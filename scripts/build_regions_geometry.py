"""
Builds js/scotland-geometry.js from the real ONS local authority boundary
data in data/raw/scotland_la_boundaries.geojson (British National Grid,
EPSG:27700). Converts each of Scotland's 32 local authority polygons into an
SVG path (flipping northing -> SVG y, scaling to fit a chosen viewBox) and
tags each with its macro-region slug, so index.html can render an
accurate, real-shaped map instead of hand-drawn approximations.

Run with: python3 scripts/build_regions_geometry.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_PATH = os.path.join(ROOT, "data", "raw", "scotland_la_boundaries.geojson")
RAW_WGS84_PATH = os.path.join(ROOT, "data", "raw", "scotland_la_boundaries_wgs84.geojson")
OUT_PATH = os.path.join(ROOT, "js", "scotland-geometry.js")

VIEWBOX_WIDTH = 520
MARGIN = 8

# ONS LAD23NM -> region slug. Names must match data/raw feature properties
# exactly. Note ONS spells the Outer Hebrides "Na h-Eileanan Siar", while the
# schools dataset (and js/regions-data.js) uses "Na h-Eileanan an Iar" for
# the same council area -- handled by LA_NAME_ALIASES below.
LA_TO_REGION = {
    "Highland": "highland-islands",
    "Argyll and Bute": "highland-islands",
    "Na h-Eileanan Siar": "highland-islands",
    "Orkney Islands": "highland-islands",
    "Shetland Islands": "highland-islands",
    "Aberdeen City": "aberdeen-north-east",
    "Aberdeenshire": "aberdeen-north-east",
    "Moray": "aberdeen-north-east",
    "Angus": "tayside-central-fife",
    "Clackmannanshire": "tayside-central-fife",
    "Dundee City": "tayside-central-fife",
    "Falkirk": "tayside-central-fife",
    "Fife": "tayside-central-fife",
    "Perth and Kinross": "tayside-central-fife",
    "Stirling": "tayside-central-fife",
    "City of Edinburgh": "edinburgh-lothians",
    "East Lothian": "edinburgh-lothians",
    "Midlothian": "edinburgh-lothians",
    "West Lothian": "edinburgh-lothians",
    "Glasgow City": "glasgow-strathclyde",
    "East Ayrshire": "glasgow-strathclyde",
    "East Dunbartonshire": "glasgow-strathclyde",
    "East Renfrewshire": "glasgow-strathclyde",
    "Inverclyde": "glasgow-strathclyde",
    "North Ayrshire": "glasgow-strathclyde",
    "North Lanarkshire": "glasgow-strathclyde",
    "Renfrewshire": "glasgow-strathclyde",
    "South Ayrshire": "glasgow-strathclyde",
    "South Lanarkshire": "glasgow-strathclyde",
    "West Dunbartonshire": "glasgow-strathclyde",
    "Dumfries and Galloway": "scotland-south",
    "Scottish Borders": "scotland-south",
}

# Canonical name to use in output (matches js/regions-data.js / schools.json).
LA_NAME_ALIASES = {
    "Na h-Eileanan Siar": "Na h-Eileanan an Iar",
}


def rings_of(geometry):
    if geometry["type"] == "Polygon":
        return geometry["coordinates"]
    return [ring for polygon in geometry["coordinates"] for ring in polygon]


def ring_area_and_centroid(points):
    """Shoelace-formula signed area and centroid of a closed ring of (x, y) points."""
    area = 0.0
    cx = 0.0
    cy = 0.0
    n = len(points)
    for i in range(n):
        x0, y0 = points[i]
        x1, y1 = points[(i + 1) % n]
        cross = x0 * y1 - x1 * y0
        area += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    area /= 2.0
    if area == 0:
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        return 0.0, (sum(xs) / n, sum(ys) / n)
    cx /= 6 * area
    cy /= 6 * area
    return abs(area), (cx, cy)


def compute_region_bounds():
    """Leaflet-style [[south, west], [north, east]] bounds per region, from the
    real WGS84 boundary data (independent of the SVG projection above)."""
    data = json.load(open(RAW_WGS84_PATH))
    region_bounds = {}
    missing = []
    for feature in data["features"]:
        raw_name = feature["properties"]["LAD23NM"]
        region = LA_TO_REGION.get(raw_name)
        if region is None:
            missing.append(raw_name)
            continue
        lons = [pt[0] for ring in rings_of(feature["geometry"]) for pt in ring]
        lats = [pt[1] for ring in rings_of(feature["geometry"]) for pt in ring]
        south, north = min(lats), max(lats)
        west, east = min(lons), max(lons)
        if region not in region_bounds:
            region_bounds[region] = [south, west, north, east]
        else:
            b = region_bounds[region]
            region_bounds[region] = [
                min(b[0], south), min(b[1], west), max(b[2], north), max(b[3], east)
            ]

    if missing:
        raise SystemExit(f"No region mapping for (WGS84 pass): {missing}")

    return {
        slug: [[round(s, 5), round(w, 5)], [round(n, 5), round(e, 5)]]
        for slug, (s, w, n, e) in region_bounds.items()
    }


def main():
    data = json.load(open(RAW_PATH))
    features = data["features"]

    all_x = [pt[0] for f in features for ring in rings_of(f["geometry"]) for pt in ring]
    all_y = [pt[1] for f in features for ring in rings_of(f["geometry"]) for pt in ring]
    min_e, max_e = min(all_x), max(all_x)
    min_n, max_n = min(all_y), max(all_y)

    scale = (VIEWBOX_WIDTH - 2 * MARGIN) / (max_e - min_e)
    height = (max_n - min_n) * scale + 2 * MARGIN

    def to_svg(easting, northing):
        x = (easting - min_e) * scale + MARGIN
        y = (max_n - northing) * scale + MARGIN
        return round(x, 1), round(y, 1)

    entries = []
    missing = []
    region_biggest = {}  # slug -> (area, centroid) of its largest ring seen so far

    for feature in features:
        raw_name = feature["properties"]["LAD23NM"]
        name = LA_NAME_ALIASES.get(raw_name, raw_name)
        region = LA_TO_REGION.get(raw_name)
        if region is None:
            missing.append(raw_name)
            continue

        subpaths = []
        for ring in rings_of(feature["geometry"]):
            points = [to_svg(e, n) for e, n in ring]
            d = "M" + " L".join(f"{x},{y}" for x, y in points) + " Z"
            subpaths.append(d)

            area, centroid = ring_area_and_centroid(points)
            if area > region_biggest.get(region, (0, None))[0]:
                region_biggest[region] = (area, centroid)

        entries.append({"name": name, "region": region, "d": " ".join(subpaths)})

    if missing:
        raise SystemExit(f"No region mapping for: {missing}")

    entries.sort(key=lambda e: (e["region"], e["name"]))

    # Label anchor per region = centroid of that region's single largest landmass
    # (its biggest local authority's biggest ring), so labels land on solid land
    # rather than being dragged toward small island fragments.
    labels = {
        slug: {"x": round(centroid[0], 1), "y": round(centroid[1], 1)}
        for slug, (area, centroid) in region_biggest.items()
    }

    region_bounds = compute_region_bounds()

    with open(OUT_PATH, "w") as f:
        f.write(
            "// Generated by scripts/build_regions_geometry.py from real ONS local\n"
            "// authority boundary data (British National Grid for SVG shapes, WGS84\n"
            "// for map bounds). Do not hand-edit -- rerun the script instead.\n\n"
        )
        f.write(f"const SCOTLAND_VIEWBOX = \"0 0 {VIEWBOX_WIDTH} {round(height, 1)}\";\n\n")
        f.write("const SCOTLAND_LA_SHAPES = ")
        f.write(json.dumps(entries, indent=2))
        f.write(";\n\nconst SCOTLAND_REGION_LABEL_POS = ")
        f.write(json.dumps(labels, indent=2))
        f.write(
            ";\n\n// Leaflet-style [[south, west], [north, east]] bounds per region,\n"
            "// for map.fitBounds() on the main schools map.\n"
        )
        f.write("const SCOTLAND_REGION_BOUNDS = ")
        f.write(json.dumps(region_bounds, indent=2))
        f.write(";\n")

    print(f"Wrote {len(entries)} local authority shapes to {OUT_PATH}")
    print(f"viewBox: 0 0 {VIEWBOX_WIDTH} {round(height, 1)}")


if __name__ == "__main__":
    main()
