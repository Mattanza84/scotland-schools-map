# Data sources

## School locations, sector, denomination, address

- **Source**: "Schools_Scotland__2022" ArcGIS FeatureServer layer, published by the Scottish
  Government (derived from the "School contact details" and "School level summary statistics"
  publications on gov.scot).
- **URL**: `https://services-eu1.arcgis.com/ELpYE44CpoxrJqcU/ArcGIS/rest/services/Schools_Scotland__2022/FeatureServer/0`
- **Fetched**: 2026-07-07
- **License**: Open Government Licence v3.0
- **Raw files**: `data/raw/schools_scotland_page1.geojson`, `data/raw/schools_scotland_page2.geojson`
  (2 pages of up to 2000 records each, `outSR=4326` for WGS84 lat/lng).
- **Notes**: covers all ~2,495 schools in Scotland; filtered at build time to primary/secondary
  sectors only (special schools excluded), giving 2,360 schools across all 32 local authorities.

## Inspection ratings (quality indicator grades)

- **Source**: Scottish Government FOI response FOI-202000044014, Annex A spreadsheet.
- **URL**: `https://www.gov.scot/publications/foi-202000044014/` (spreadsheet linked from that page)
- **Fetched**: 2026-07-07
- **Raw file**: `data/raw/foi_inspection_annex_a.xlsx`
- **Coverage**: inspections from April 2008 to June 2020, across three inspection framework
  periods each grading a different set of quality indicators (QIs) on a 1 (weakest) to 6
  (strongest) scale:
  - 2008-2016: QI 1.1, 2.1, 5.3, 5.1, 5.9
  - 2016-2020: QI 1.3, 2.3, 3.2, 3.1
  - 2017-2020: QI 1.1, 2.3, 3.2
- **Known limitation**: no confirmed bulk source was found for inspections after June 2020.
  Scotland's inspection model is light-touch (only a fraction of schools inspected in any given
  period), so schools with no rating in the map may simply not have been inspected recently, and
  schools that do have a rating may be reflecting an inspection from as far back as 2008. The
  `inspectionDate` shown in each popup is the actual date of the most recent inspection Annex A
  contains for that school (deduplicated by SEED code, keeping the latest date where a school
  appears in more than one framework period) — always check it rather than assuming the rating
  is current.
- **What "rating" means here**: Education Scotland does not publish a single official overall
  grade per school (unlike Ofsted's England-only "Outstanding/Good/..." scale). The `label` and
  `averageScore` fields in `data/schools.json` are an illustrative average computed across
  whichever quality indicators were graded at that school's inspection — not an official
  Education Scotland score.

## Region-picker boundary shapes (index.html)

- **Source**: ONS Open Geography Portal, "Local Authority Districts (December 2023) Boundaries
  UK BUC" (Ultra Generalised, 500m — the lightest-weight ONS boundary product, intended for
  small-scale thematic maps like this one).
- **URL**: `https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Local_Authority_Districts_December_2023_Boundaries_UK_BUC/FeatureServer/0`
- **Fetched**: 2026-07-09, filtered to Scotland (`LAD23CD LIKE 'S12%'`), projected in British
  National Grid (EPSG:27700).
- **Raw file**: `data/raw/scotland_la_boundaries.geojson` (all 32 Scottish local authorities).
- **License**: Open Government Licence v3.0 / © Crown copyright and database right, ONS.
- **Notes**: ONS spells the Outer Hebrides council "Na h-Eileanan Siar"; the schools dataset
  (and `js/regions-data.js`) uses "Na h-Eileanan an Iar" for the same area — both refer to the
  same local authority, reconciled in `scripts/build_regions_geometry.py`.

## Refreshing the data

Re-run `python3 scripts/build_schools_json.py` after replacing the files in `data/raw/` with
newer downloads from the same sources (or newer equivalents) to regenerate `data/schools.json`.
Re-run `python3 scripts/build_regions_geometry.py` after replacing
`data/raw/scotland_la_boundaries.geojson` to regenerate `js/scotland-geometry.js`.
