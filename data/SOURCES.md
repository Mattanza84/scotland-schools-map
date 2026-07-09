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

## Primary school ratings (inspection quality indicator grades)

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
- **Usage**: this is the sole rating source for primary schools, and the fallback for any
  secondary school with no attainment data available (see below).

## Secondary school ratings (SQA attainment)

- **Source**: Scottish Government, "Schools - Breadth and Depth of Qualifications",
  statistics.gov.scot (a linked-data cube, OGL v3.0 licensed).
- **URL**: `https://statistics.gov.scot/data/breadth-and-depth`, queried via its SPARQL endpoint
  at `http://statistics.gov.scot/sparql`.
- **Fetched**: 2026-07-09, filtered to: `numberOfAwards = 5-and-above`, `scqfLevel = 6-and-above`
  (SCQF level 6 = Higher), `courses = all-courses`, `comparator = real-establishment`, for
  reference periods 2023-08-01/P1Y (academic year 2023-24) and 2024-08-01/P1Y (2024-25).
- **Raw files**: `data/raw/breadth_and_depth_2023-24.json`, `data/raw/breadth_and_depth_2024-25.json`
  (raw SPARQL JSON results).
- **Metric**: % of the school-leaver cohort attaining 5 or more qualifications at Higher level
  (SCQF 6) or above. This is a genuinely school-level, annually-updated official statistic —
  unlike primary attainment (ACEL), which Scottish Government only publishes aggregated at
  local-authority level, so no equivalent exists for primary schools here.
- **Join key**: each establishment entity's `foi:code` in this dataset is the same SEED code used
  throughout the rest of this project — confirmed by cross-checking real schools (e.g. SEED
  5102030 = "Thurso High School" in both this dataset and the ArcGIS schools layer).
- **Suppression**: cells marked `*` (small-cohort disclosure control) or `#` (not applicable) in
  the raw data are treated as no data for that year; 2024-25 is preferred where both years have a
  usable value, otherwise 2023-24 is used.
- **Banding**: `data/schools.json` reuses the same six labels as the primary inspection scale
  (Excellent/Very Good/Good/Satisfactory/Weak/Unsatisfactory) so the existing "School rating"
  filter needs no changes, banding the raw percentage at 60/45/35/25/15/0. These thresholds are
  illustrative (chosen from the actual national distribution, not an official scale) — Scottish
  Government does not publish rating bands for this metric.
- **Known limitation**: this is a raw attainment figure, not adjusted for pupils' socioeconomic
  background or prior attainment. The official methodology recommends comparing a school against
  its own "virtual comparator" (a matched sample with similar pupil characteristics) for a fairer
  read — this map does not show that comparison, only the raw percentage, and the popup discloses
  this. ~16 of 360 secondary schools have no usable value in either year (suppressed in both, or
  absent from the dataset) and fall back to inspection-based ratings where available.

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

To pull a newer year of secondary attainment data, query the SPARQL endpoint with the reference
period updated to the new year (e.g. `2025-08-01T00:00:00/P1Y` for 2025-26), and save the result
as `data/raw/breadth_and_depth_<year>.json`:

```
curl -sS -G "http://statistics.gov.scot/sparql" \
  --data-urlencode 'query=PREFIX qb: <http://purl.org/linked-data/cube#>
PREFIX sdmxd: <http://purl.org/linked-data/sdmx/2009/dimension#>
PREFIX foi: <http://publishmydata.com/def/ontology/foi/>
PREFIX edu: <http://statistics.gov.scot/def/education/>
PREFIX dim: <http://statistics.gov.scot/def/dimension/>
PREFIX measure: <http://statistics.gov.scot/def/measure-properties/>
SELECT ?seedCode ?schoolName ?refPeriod ?percent WHERE {
  ?obs qb:dataSet <http://statistics.gov.scot/data/breadth-and-depth> ;
       sdmxd:refPeriod ?refPeriod ;
       edu:refEstablishment ?est ;
       dim:numberOfAwards <http://statistics.gov.scot/def/concept/number-of-awards/5-and-above> ;
       dim:scqfLevel <http://statistics.gov.scot/def/concept/scqf-level/6-and-above> ;
       dim:courses <http://statistics.gov.scot/def/concept/courses/all-courses> ;
       dim:comparator <http://statistics.gov.scot/def/concept/comparator/real-establishment> ;
       measure:percent ?percent .
  ?est foi:memberOf <http://statistics.gov.scot/def/foi/collection/education-establishments> ;
       foi:code ?seedCode ;
       foi:displayName ?schoolName .
  FILTER(?refPeriod = <http://reference.data.gov.uk/id/gregorian-interval/YYYY-08-01T00:00:00/P1Y>)
}' \
  -H "Accept: application/sparql-results+json" -o data/raw/breadth_and_depth_YYYY-YY.json
```

Then update the `sources` list at the top of `load_attainment()` in `scripts/build_schools_json.py`
to include the new filename (most recent year first).
