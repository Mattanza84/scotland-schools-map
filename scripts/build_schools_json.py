"""
Builds data/schools.json from the raw source files in data/raw/.

Sources (see data/SOURCES.md for full provenance):
  - data/raw/schools_scotland_page{1,2}.geojson
      School locations, sector, denomination, address. Fetched from the
      "Schools_Scotland__2022" ArcGIS FeatureServer layer (WGS84).
  - data/raw/foi_inspection_annex_a.xlsx
      Education Scotland inspection quality-indicator (QI) grades, 1 (weakest)
      to 6 (strongest), covering inspections from April 2008 to June 2020.
      Response to FOI-202000044014.

Run with: python3 scripts/build_schools_json.py
"""
import json
import os
from datetime import date

import openpyxl

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
OUT_PATH = os.path.join(ROOT, "data", "schools.json")

SECTOR_MAP = {
    "Primary": "primary",
    "Secondary": "secondary",
}

# Education Scotland's own wording for the 1-6 scale, used to label the
# averaged score. This is an illustrative average across whichever quality
# indicators a given inspection graded, not an official single overall grade
# (Education Scotland does not publish one).
GRADE_LABELS = {
    6: "Excellent",
    5: "Very Good",
    4: "Good",
    3: "Satisfactory",
    2: "Weak",
    1: "Unsatisfactory",
}


def load_locations():
    features = []
    for fname in ("schools_scotland_page1.geojson", "schools_scotland_page2.geojson"):
        with open(os.path.join(RAW, fname)) as f:
            features.extend(json.load(f)["features"])

    schools = {}
    skipped_no_sector = 0
    for feat in features:
        p = feat["properties"]
        sector = SECTOR_MAP.get(p["SchoolType"])
        if sector is None:
            # "Special" schools and any other non primary/secondary type are
            # out of scope per the plan.
            skipped_no_sector += 1
            continue
        lat, lng = p.get("Latitude"), p.get("Longitude")
        if lat is None or lng is None:
            continue
        seed = int(p["SeedCode"])
        address_parts = [
            p.get("AddressLin"),
            p.get("AddressL_1"),
            p.get("AddressL_2"),
        ]
        address = ", ".join(
            part for part in address_parts if part and part.strip() and part.strip() != "0"
        )
        if p.get("PostCode"):
            address = f"{address}, {p['PostCode']}" if address else p["PostCode"]

        schools[p["SchUID"]] = {
            "id": p["SchUID"],
            "seedCode": seed,
            "name": p["SchoolName"],
            "sector": sector,
            "denomination": p.get("Denominati") or "Not specified",
            "localAuthority": p["LAName"],
            "address": address,
            "lat": lat,
            "lng": lng,
            "rating": {"hasData": False},
        }
    return schools


def read_inspection_sheet(ws, header_name="Seed No."):
    header_row_idx = None
    header = None
    for i, row in enumerate(ws.iter_rows(min_row=1, max_row=5, values_only=True), start=1):
        if row and row[0] == header_name:
            header_row_idx = i
            header = row
            break
    if header_row_idx is None:
        raise ValueError(f"Could not find header row in sheet {ws.title}")

    qi_columns = [
        (idx, name)
        for idx, name in enumerate(header)
        if name and str(name).startswith("QI")
    ]

    records = []
    for row in ws.iter_rows(min_row=header_row_idx + 1, values_only=True):
        seed_raw = row[0]
        if not isinstance(seed_raw, (int, float)):
            continue
        seed = int(seed_raw)
        inspection_date = row[2]
        qi_scores = {}
        for idx, qi_name in qi_columns:
            val = row[idx]
            if isinstance(val, (int, float)):
                qi_number = qi_name.replace("QI", "").strip()
                qi_scores[qi_number] = val
        if not qi_scores:
            continue
        records.append(
            {
                "seedCode": seed,
                "inspectionDate": inspection_date,
                "qiScores": qi_scores,
            }
        )
    return records


def load_ratings():
    wb = openpyxl.load_workbook(
        os.path.join(RAW, "foi_inspection_annex_a.xlsx"), data_only=True
    )
    all_records = []
    for sheet_name in wb.sheetnames:
        if sheet_name == "QI definitions":
            continue
        all_records.extend(read_inspection_sheet(wb[sheet_name]))

    # A school can appear in more than one sheet if it was inspected more than
    # once (e.g. once under an older framework, again under a newer one).
    # Keep only the most recent inspection per SEED code.
    latest_by_seed = {}
    for rec in all_records:
        existing = latest_by_seed.get(rec["seedCode"])
        if existing is None or rec["inspectionDate"] > existing["inspectionDate"]:
            latest_by_seed[rec["seedCode"]] = rec
    return latest_by_seed


def apply_ratings(schools, ratings_by_seed):
    matched = 0
    for school in schools.values():
        rec = ratings_by_seed.get(school["seedCode"])
        if rec is None:
            continue
        qi_scores = rec["qiScores"]
        average = sum(qi_scores.values()) / len(qi_scores)
        score = (average - 1) / (6 - 1)
        label = GRADE_LABELS[round(average)]
        inspection_date = rec["inspectionDate"]
        school["rating"] = {
            "hasData": True,
            "inspectionDate": inspection_date.date().isoformat()
            if hasattr(inspection_date, "date")
            else str(inspection_date),
            "qiScores": qi_scores,
            "averageScore": round(average, 2),
            "score": round(score, 3),
            "label": label,
        }
        matched += 1
    return matched


def main():
    schools = load_locations()
    ratings_by_seed = load_ratings()
    matched = apply_ratings(schools, ratings_by_seed)

    out = sorted(schools.values(), key=lambda s: (s["localAuthority"], s["name"]))

    with open(OUT_PATH, "w") as f:
        json.dump(out, f, indent=2)

    by_sector = {}
    for s in out:
        by_sector[s["sector"]] = by_sector.get(s["sector"], 0) + 1

    print(f"Wrote {len(out)} schools to {OUT_PATH}")
    print(f"  by sector: {by_sector}")
    print(f"  with rating data: {matched} ({matched / len(out):.0%})")
    print(f"  generated: {date.today().isoformat()}")


if __name__ == "__main__":
    main()
