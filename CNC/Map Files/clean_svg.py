import sys
from lxml import etree
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
from svgpathtools import parse_path

SVG_NS = "http://www.w3.org/2000/svg"
NSMAP = {"svg": SVG_NS}


def path_to_polygons(path_obj, samples=200):
    polygons = []

    try:
        subpaths = path_obj.continuous_subpaths()
    except Exception:
        subpaths = [path_obj]

    for subpath in subpaths:
        points = []

        for i in range(samples):
            t = i / (samples - 1)
            pt = subpath.point(t)
            points.append((pt.real, pt.imag))

        if points and points[0] != points[-1]:
            points.append(points[0])

        try:
            poly = Polygon(points)
            if poly.is_valid and not poly.is_empty:
                polygons.append(poly)
        except Exception:
            continue

    return polygons


def polygons_to_path_d(geom):
    """
    Convert Polygon or MultiPolygon into SVG path string,
    preserving ALL parts (including islands).
    """
    paths = []

    if isinstance(geom, Polygon):
        geom = [geom]
    elif isinstance(geom, MultiPolygon):
        geom = list(geom.geoms)
    else:
        return ""

    for poly in geom:
        exterior = list(poly.exterior.coords)

        d = f"M {exterior[0][0]},{exterior[0][1]} "
        for x, y in exterior[1:]:
            d += f"L {x},{y} "
        d += "Z"
        paths.append(d)

    return " ".join(paths)


def clean_svg(input_file, output_file):
    parser = etree.XMLParser(huge_tree=True)
    tree = etree.parse(input_file, parser)
    root = tree.getroot()

    paths = root.findall(".//svg:path", namespaces=NSMAP)

    print(f"Found {len(paths)} paths")

    for i, elem in enumerate(paths):
        pid = elem.get("id")
        d = elem.get("d")

        if not d:
            continue

        try:
            svg_path = parse_path(d)

            polys = path_to_polygons(svg_path)

            if not polys:
                continue

            # 🔥 Union but KEEP ALL resulting geometry
            cleaned = unary_union(polys)

            if cleaned.is_empty:
                continue

            # ✅ Preserve all pieces (no island loss)
            new_d = polygons_to_path_d(cleaned)
            elem.set("d", new_d)

            if i % 100 == 0:
                print(f"Processed {i} paths...")

        except Exception as e:
            print(f"Skipping {pid}: {e}")
            continue

    tree.write(output_file)
    print(f"Saved cleaned SVG to {output_file}")


input_svg = r"C:\Users\jaedo\OneDrive\Documents\Coding Projects\Shard\Command and Conquest (C&C)\Maps\C&C Map.svg"
output_svg = r"C:\Users\jaedo\OneDrive\Documents\Coding Projects\Shard\Command and Conquest (C&C)\Maps\C&C Map (Clean).svg"

clean_svg(input_svg, output_svg)