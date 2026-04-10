"""
Anchor Point Migration
======================
Populates fort_cords, capital_cords, army_cords in cnc_provinces.

Usage:
    python migrate_anchors.py --svg C_C_Map.svg --dsn postgresql://user:pass@host/dbname
"""

import asyncio
import argparse
import re
import sys
import math
import asyncpg
from lxml import etree
from shapely.geometry import Polygon, Point

SVG_NS      = "http://www.w3.org/2000/svg"
INKSCAPE_NS = "http://www.inkscape.org/namespaces/inkscape"

PROVINCE_TX = 1316.7823
PROVINCE_TY = 1432.499

TERRAIN_COLORS = {"#267f00", "#d3b000", "#0b6127", "#5a5b5e", "#283b1b", "#c1c1eb"}

_TOKEN_RE = re.compile(
    r'[MmLlHhVvCcSsQqTtAaZz]'
    r'|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?'
)


def svg_d_to_polygon(d: str, tx: float = 0.0, ty: float = 0.0) -> Polygon | None:
    tokens = _TOKEN_RE.findall(d)
    pts, x, y, x0, y0, cmd = [], 0.0, 0.0, 0.0, 0.0, "M"
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t.isalpha(): cmd = t; i += 1; continue
        try:
            if cmd == "M": x,y=float(tokens[i]),float(tokens[i+1]); i+=2; x0,y0=x,y; pts.append((x+tx,y+ty)); cmd="L"
            elif cmd == "m": x+=float(tokens[i]); y+=float(tokens[i+1]); i+=2; x0,y0=x,y; pts.append((x+tx,y+ty)); cmd="l"
            elif cmd == "L": x,y=float(tokens[i]),float(tokens[i+1]); i+=2; pts.append((x+tx,y+ty))
            elif cmd == "l": x+=float(tokens[i]); y+=float(tokens[i+1]); i+=2; pts.append((x+tx,y+ty))
            elif cmd == "H": x=float(tokens[i]); i+=1; pts.append((x+tx,y+ty))
            elif cmd == "h": x+=float(tokens[i]); i+=1; pts.append((x+tx,y+ty))
            elif cmd == "V": y=float(tokens[i]); i+=1; pts.append((x+tx,y+ty))
            elif cmd == "v": y+=float(tokens[i]); i+=1; pts.append((x+tx,y+ty))
            elif cmd == "C": i+=4; x,y=float(tokens[i]),float(tokens[i+1]); i+=2; pts.append((x+tx,y+ty))
            elif cmd == "c": i+=4; x+=float(tokens[i]); y+=float(tokens[i+1]); i+=2; pts.append((x+tx,y+ty))
            elif cmd == "S": i+=2; x,y=float(tokens[i]),float(tokens[i+1]); i+=2; pts.append((x+tx,y+ty))
            elif cmd == "s": i+=2; x+=float(tokens[i]); y+=float(tokens[i+1]); i+=2; pts.append((x+tx,y+ty))
            elif cmd == "Q": i+=2; x,y=float(tokens[i]),float(tokens[i+1]); i+=2; pts.append((x+tx,y+ty))
            elif cmd == "q": i+=2; x+=float(tokens[i]); y+=float(tokens[i+1]); i+=2; pts.append((x+tx,y+ty))
            elif cmd in ("Z","z"): pts.append((x0+tx,y0+ty))
            else: i+=1
        except (IndexError, ValueError): i+=1
    if len(pts) < 3: return None
    poly = Polygon(pts)
    if not poly.is_valid: poly = poly.buffer(0)
    return poly if (poly.is_valid and not poly.is_empty) else None


def compute_icon_anchors(polygon: Polygon) -> dict[str, tuple[float, float]]:
    center = polygon.representative_point()
    cx, cy = center.x, center.y
    offset = min(max(math.sqrt(polygon.area) * 0.15, 8), 30)
    candidates = {
        "capital": (cx,          cy),
        "fort":    (cx - offset, cy + offset),
        "army":    (cx + offset, cy + offset),
    }
    return {
        slot: (x, y) if polygon.contains(Point(x, y)) else (cx, cy)
        for slot, (x, y) in candidates.items()
    }


def should_skip(pid: str, fill: str) -> bool:
    return (
        fill in ("#252525", "none", "")
        or fill not in TERRAIN_COLORS
        or pid.startswith("impassable_terrain_")
        or "LAKE" in pid.upper()
    )


def parse_fill(style: str) -> str:
    for part in style.split(";"):
        if part.strip().startswith("fill:"):
            return part.split(":")[1].strip().lower()
    return ""


def get_layer(root, label):
    for g in root.findall(f".//{{{SVG_NS}}}g"):
        if (g.get(f"{{{INKSCAPE_NS}}}groupmode") == "layer"
                and g.get(f"{{{INKSCAPE_NS}}}label") == label):
            return g
    return None


async def migrate(svg_path: str, dsn: str, dry_run: bool = False):
    print(f"Parsing {svg_path}...")
    root = etree.parse(svg_path).getroot()

    province_layer = get_layer(root, "Provinces")
    if province_layer is None:
        print("ERROR: 'Provinces' layer not found.", file=sys.stderr)
        sys.exit(1)

    print("Computing anchor points...")
    rows = []
    skipped = 0

    for elem in province_layer.findall(f"{{{SVG_NS}}}path"):
        pid  = elem.get("id", "")
        fill = parse_fill(elem.get("style", ""))
        d    = elem.get("d", "")

        if should_skip(pid, fill):
            skipped += 1
            continue

        poly = svg_d_to_polygon(d, PROVINCE_TX, PROVINCE_TY)
        if poly is None:
            print(f"  WARNING: Could not build polygon for '{pid}' — skipping.")
            skipped += 1
            continue

        a = compute_icon_anchors(poly)
        rows.append((
            pid,
            (a["capital"][0], a["capital"][1]),
            (a["fort"][0],    a["fort"][1]),
            (a["army"][0],    a["army"][1]),
        ))

    print(f"  Computed: {len(rows)}  |  Skipped: {skipped}")

    if dry_run:
        print("\nDry run — no DB writes.")
        return

    print("Connecting to database...")
    db = await asyncpg.connect(dsn)
    try:
        print("Writing anchor points...")
        await db.executemany("""
            UPDATE cnc_provinces
            SET capital_cords = $2,
                fort_cords    = $3,
                army_cords    = $4
            WHERE id = $1
        """, rows)
        print(f"  Done — {len(rows)} rows updated.")
    finally:
        await db.close()


def main():
    parser = argparse.ArgumentParser(description="Populate icon anchor points in cnc_provinces.")
    parser.add_argument("--svg",     required=True, help="Path to C_C_Map.svg")
    parser.add_argument("--dsn",     required=True, help="PostgreSQL DSN")
    parser.add_argument("--dry-run", action="store_true", help="No DB writes")
    args = parser.parse_args()
    asyncio.run(migrate(args.svg, args.dsn, dry_run=args.dry_run))

if __name__ == "__main__":
    main()