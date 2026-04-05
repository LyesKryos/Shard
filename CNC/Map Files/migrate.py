"""
C&C Map Migration Script
========================
Populates cnc_provinces with: id, terrain, bordering, coast, river

Usage:
    python migrate.py --svg C_C_Map.svg --dsn postgresql://user:pass@host/dbname
    python migrate.py --svg C_C_Map.svg --dsn ... --dry-run

Requirements:
    pip install shapely lxml asyncpg
    (does NOT require svg.path)
"""

import asyncio
import argparse
import re
import sys
from itertools import combinations

import asyncpg
from lxml import etree
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SVG_NS      = "http://www.w3.org/2000/svg"
INKSCAPE_NS = "http://www.inkscape.org/namespaces/inkscape"

TERRAIN_COLORS: dict[str, int] = {
    "#267f00": 0,   # Plains
    "#d3b000": 1,   # Desert
    "#0b6127": 2,   # Hills
    "#5a5b5e": 5,   # Mountain
    "#283b1b": 7,   # Swamp
    "#c1c1eb": 9,   # Arctic
}

# Translation applied to the Provinces layer in the SVG coordinate space
PROVINCE_TX = 1316.7823
PROVINCE_TY = 1432.499

# Tolerances (SVG units)
NEIGHBOR_TOLERANCE = 4.0
RIVER_BUFFER       = 4.0


# ---------------------------------------------------------------------------
# Fast SVG Path Parser
# ---------------------------------------------------------------------------
# Extracts on-curve anchor points from SVG path data without evaluating
# bezier curves. This is ~1000x faster than sampling svg.path.point()
# and produces accurate-enough polygons for neighbor/coastal/river detection.

_TOKEN_RE = re.compile(
    r'[MmLlHhVvCcSsQqTtAaZz]'
    r'|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?'
)

def svg_d_to_polygon(d: str, tx: float = 0.0, ty: float = 0.0) -> Polygon | None:
    """
    Parse an SVG path 'd' string into a Shapely Polygon by extracting
    on-curve anchor points only (skipping bezier control points).
    Applies (tx, ty) translation to bring coordinates into the global space.
    """
    tokens = _TOKEN_RE.findall(d)
    pts: list[tuple[float, float]] = []
    x = y = x0 = y0 = 0.0
    cmd = "M"
    i = 0

    while i < len(tokens):
        t = tokens[i]
        if t.isalpha():
            cmd = t
            i += 1
            continue
        try:
            if cmd == "M":
                x, y = float(tokens[i]), float(tokens[i+1]); i += 2
                x0, y0 = x, y; pts.append((x+tx, y+ty)); cmd = "L"
            elif cmd == "m":
                x += float(tokens[i]); y += float(tokens[i+1]); i += 2
                x0, y0 = x, y; pts.append((x+tx, y+ty)); cmd = "l"
            elif cmd == "L":
                x, y = float(tokens[i]), float(tokens[i+1]); i += 2
                pts.append((x+tx, y+ty))
            elif cmd == "l":
                x += float(tokens[i]); y += float(tokens[i+1]); i += 2
                pts.append((x+tx, y+ty))
            elif cmd == "H":
                x = float(tokens[i]); i += 1; pts.append((x+tx, y+ty))
            elif cmd == "h":
                x += float(tokens[i]); i += 1; pts.append((x+tx, y+ty))
            elif cmd == "V":
                y = float(tokens[i]); i += 1; pts.append((x+tx, y+ty))
            elif cmd == "v":
                y += float(tokens[i]); i += 1; pts.append((x+tx, y+ty))
            elif cmd == "C":
                i += 4  # skip two control points
                x, y = float(tokens[i]), float(tokens[i+1]); i += 2
                pts.append((x+tx, y+ty))
            elif cmd == "c":
                i += 4
                x += float(tokens[i]); y += float(tokens[i+1]); i += 2
                pts.append((x+tx, y+ty))
            elif cmd == "S":
                i += 2
                x, y = float(tokens[i]), float(tokens[i+1]); i += 2
                pts.append((x+tx, y+ty))
            elif cmd == "s":
                i += 2
                x += float(tokens[i]); y += float(tokens[i+1]); i += 2
                pts.append((x+tx, y+ty))
            elif cmd == "Q":
                i += 2
                x, y = float(tokens[i]), float(tokens[i+1]); i += 2
                pts.append((x+tx, y+ty))
            elif cmd == "q":
                i += 2
                x += float(tokens[i]); y += float(tokens[i+1]); i += 2
                pts.append((x+tx, y+ty))
            elif cmd in ("Z", "z"):
                pts.append((x0+tx, y0+ty))
                i += 0
            else:
                i += 1
        except (IndexError, ValueError):
            i += 1

    if len(pts) < 3:
        return None
    poly = Polygon(pts)
    if not poly.is_valid:
        poly = poly.buffer(0)
    return poly if (poly.is_valid and not poly.is_empty) else None


# ---------------------------------------------------------------------------
# SVG Layer Helpers
# ---------------------------------------------------------------------------

def get_layer(root: etree._Element, label: str) -> etree._Element | None:
    for g in root.findall(f".//{{{SVG_NS}}}g"):
        if (g.get(f"{{{INKSCAPE_NS}}}groupmode") == "layer"
                and g.get(f"{{{INKSCAPE_NS}}}label") == label):
            return g
    return None


def parse_fill(style: str) -> str:
    for part in style.split(";"):
        part = part.strip()
        if part.startswith("fill:"):
            return part[5:].strip().lower()
    return ""


def should_skip(pid: str, fill: str) -> bool:
    return (
        fill in ("#252525", "none", "")
        or pid.startswith("impassable_terrain_")
        or "LAKE" in pid.upper()
    )


def river_group_to_geometry(group: etree._Element):
    """Union all segments of a river group into one buffered geometry."""
    geoms = []
    for p in group.findall(f".//{{{SVG_NS}}}path"):
        d = p.get("d", "")
        if not d:
            continue
        poly = svg_d_to_polygon(d)
        if poly:
            geoms.append(poly.buffer(RIVER_BUFFER))
        else:
            # Fallback for open paths: treat as linestring
            tokens = _TOKEN_RE.findall(d)
            pts, x, y, cmd = [], 0.0, 0.0, "M"
            i = 0
            while i < len(tokens):
                t = tokens[i]
                if t.isalpha(): cmd = t; i += 1; continue
                try:
                    if cmd in ("M", "L"):
                        x, y = float(tokens[i]), float(tokens[i+1]); i += 2
                        pts.append((x, y)); cmd = "L"
                    elif cmd in ("m", "l"):
                        x += float(tokens[i]); y += float(tokens[i+1]); i += 2
                        pts.append((x, y)); cmd = "l"
                    elif cmd == "C":
                        i += 4; x, y = float(tokens[i]), float(tokens[i+1]); i += 2
                        pts.append((x, y))
                    elif cmd == "c":
                        i += 4; x += float(tokens[i]); y += float(tokens[i+1]); i += 2
                        pts.append((x, y))
                    else:
                        i += 1
                except (IndexError, ValueError):
                    i += 1
            if len(pts) >= 2:
                geoms.append(LineString(pts).buffer(RIVER_BUFFER))
    return unary_union(geoms) if geoms else None


def detect_coastal(polygons: dict) -> set[str]:
    """
    A province is coastal if its boundary touches the exterior outline of the
    landmass — i.e. it faces open water rather than other provinces.

    Uses the exterior rings of the landmass union only, ignoring internal
    province borders. This correctly identifies coastal provinces without
    needing the ocean layer at all.

    Note: will produce false positives around lake holes in the landmass.
    Correct these manually in the DB after migration.
    """
    from shapely.geometry import MultiLineString

    print("  Building landmass union (this may take a moment)...")
    all_land = unary_union(list(polygons.values()))

    # Extract only the exterior outlines — not internal province borders
    if all_land.geom_type == "Polygon":
        exterior = all_land.exterior
    elif all_land.geom_type == "MultiPolygon":
        exterior = MultiLineString([g.exterior for g in all_land.geoms])
    else:
        exterior = all_land.boundary  # fallback

    coastal = set()
    for pid, poly in polygons.items():
        try:
            if poly.boundary.intersects(exterior):
                coastal.add(pid)
        except Exception:
            continue

    return coastal


# ---------------------------------------------------------------------------
# Migration
# ---------------------------------------------------------------------------

async def migrate(svg_path: str, dsn: str, dry_run: bool = False):
    print(f"Parsing {svg_path}...")
    root = etree.parse(svg_path).getroot()

    province_layer = get_layer(root, "Provinces")
    river_layer    = get_layer(root, "Rivers")

    if province_layer is None:
        print("ERROR: 'Provinces' layer not found.", file=sys.stderr)
        sys.exit(1)
    if river_layer is None:
        print("WARNING: 'Rivers' layer not found — river=False for all.")

    # ------------------------------------------------------------------
    # Parse provinces
    # ------------------------------------------------------------------
    print("Parsing province polygons...")
    polygons: dict[str, Polygon] = {}
    terrain:  dict[str, int]     = {}
    skipped = 0

    for elem in province_layer.findall(f"{{{SVG_NS}}}path"):
        pid  = elem.get("id", "")
        fill = parse_fill(elem.get("style", ""))
        d    = elem.get("d", "")

        if should_skip(pid, fill):
            skipped += 1
            continue

        tid = TERRAIN_COLORS.get(fill)
        if tid is None:
            print(f"  WARNING: Unknown fill '{fill}' on '{pid}' — skipping.")
            skipped += 1
            continue

        poly = svg_d_to_polygon(d, PROVINCE_TX, PROVINCE_TY)
        if poly is None:
            print(f"  WARNING: Could not build polygon for '{pid}' — skipping.")
            skipped += 1
            continue

        polygons[pid] = poly
        terrain[pid]  = tid

    print(f"  Valid: {len(polygons)}  |  Skipped: {skipped}")

    # ------------------------------------------------------------------
    # Neighbor detection — STRtree spatial index to avoid O(n²) brute force
    # ------------------------------------------------------------------
    print("Detecting neighbors...")
    bordering: dict[str, list[str]] = {pid: [] for pid in polygons}
    ids      = list(polygons.keys())
    polys    = [polygons[pid] for pid in ids]

    # Buffer each polygon by half the tolerance for intersection testing
    buffered = [p.buffer(NEIGHBOR_TOLERANCE / 2) for p in polys]
    tree     = STRtree(buffered)

    checked = 0
    for i, pid_a in enumerate(ids):
        candidates = tree.query(buffered[i])
        for j in candidates:
            if j <= i:
                continue
            pid_b = ids[j]
            try:
                if polygons[pid_a].distance(polygons[pid_b]) < NEIGHBOR_TOLERANCE:
                    bordering[pid_a].append(pid_b)
                    bordering[pid_b].append(pid_a)
                    checked += 1
            except Exception:
                continue

    print(f"  Neighbor pairs: {checked}")

    # ------------------------------------------------------------------
    # Coastal detection — boundary-based, no ocean layer needed
    # ------------------------------------------------------------------
    print("Detecting coastal provinces...")
    coastal_ids = detect_coastal(polygons)
    coast: dict[str, bool] = {pid: (pid in coastal_ids) for pid in polygons}
    print(f"  Coastal: {sum(coast.values())}")
    print(f"  NOTE: Provinces bordering lakes may be false positives —")
    print(f"        correct these manually with: UPDATE cnc_provinces SET coast = false WHERE id IN (...)")

    # ------------------------------------------------------------------
    # River detection
    # ------------------------------------------------------------------
    river: dict[str, bool] = {pid: False for pid in polygons}
    if river_layer is not None:
        print("Detecting river adjacency...")
        province_tree = STRtree(polys)
        groups = [c for c in river_layer if c.tag == f"{{{SVG_NS}}}g"]
        for group in groups:
            rid       = group.get("id", "unnamed")
            river_geom = river_group_to_geometry(group)
            if river_geom is None:
                print(f"  WARNING: No geometry for '{rid}'")
                continue
            candidates = province_tree.query(river_geom)
            touched = 0
            for j in candidates:
                pid = ids[j]
                try:
                    if not river[pid] and river_geom.intersects(polys[j]):
                        river[pid] = True
                        touched += 1
                except Exception:
                    continue
            print(f"  {rid}: {touched} provinces")
        print(f"  Provinces with river: {sum(river.values())}")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("\n=== SUMMARY ===")
    print(f"  Provinces  : {len(polygons)}")
    print(f"  Neighbors  : {checked} pairs")
    print(f"  Coastal    : {sum(coast.values())}")
    print(f"  River      : {sum(river.values())}")

    if dry_run:
        print("\nDry run — no DB writes.")
        return

    # ------------------------------------------------------------------
    # Write to DB
    # ------------------------------------------------------------------
    print(f"\nConnecting to database...")
    db = await asyncpg.connect(dsn)
    try:
        print("Writing to cnc_provinces...")
        rows = [
            (
                pid,
                terrain[pid],
                bordering[pid],
                coast[pid],
                river[pid],
            )
            for pid in polygons
        ]

        await db.executemany("""
            INSERT INTO cnc_provinces (id, terrain, bordering, coast, river)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (id) DO UPDATE SET
                terrain   = EXCLUDED.terrain,
                bordering = EXCLUDED.bordering,
                coast     = EXCLUDED.coast,
                river     = EXCLUDED.river
        """, rows)

        print(f"  Done — {len(rows)} rows written.")
        print("\nMigration complete.")

    finally:
        await db.close()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Migrate C&C Map SVG into cnc_provinces."
    )
    parser.add_argument("--svg",     required=True, help="Path to C_C_Map.svg")
    parser.add_argument("--dsn",     required=True, help="PostgreSQL DSN")
    parser.add_argument("--dry-run", action="store_true",
                        help="Parse and summarise without writing to DB")
    args = parser.parse_args()
    asyncio.run(migrate(args.svg, args.dsn, dry_run=args.dry_run))


if __name__ == "__main__":
    main()