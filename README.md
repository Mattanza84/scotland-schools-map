# Scotland Schools Map

Interactive map of primary and secondary schools across all 32 Scottish local authorities,
colour-coded by rating: primary schools by an illustrative average of published Education
Scotland inspection quality indicators, secondary schools by recent SQA Highers attainment
(% of leavers with 5+ Higher passes). The homepage is the area picker (`index.html`) — pick one
of 6 macro regions to jump into the filtered map (`map.html`).

## Running locally

Browsers block `fetch()` of local JSON files opened directly from disk (`file://`), so serve the
folder with a simple static server instead of double-clicking `index.html`:

```
python3 -m http.server 8000
```

Then open `http://localhost:8000/` in a browser to start from the area picker.

## Area picker (`index.html`)

A stylized, clickable map of Scotland split into 6 macro regions (Highland and Islands, Aberdeen
and North East, Tayside/Central/Fife, Edinburgh and Lothians, Glasgow and Strathclyde, Scotland
South — see `js/regions-data.js` for the exact local-authority membership of each). Clicking a
region opens `map.html?region=<slug>`, which pre-checks only that region's local authorities and
fits the map view to that region's real geographic bounds.

## What the map shows

- **Icon shape**: circle = primary school, triangle = secondary school.
- **Colour**: red (weaker) → yellow → green (stronger). For primary schools this reflects
  Education Scotland inspection quality indicators; for secondary schools it reflects the % of
  leavers attaining 5+ Higher passes. Grey = no rating data available for that school.
- **Click a marker** to see the school's name, sector, local authority, address, and rating
  detail (or a note that no rating data is available).
- **Checkboxes** (filter panel) toggle primary/secondary schools, local authorities, and rating
  bands on/off.

## Data and its limitations

See [`data/SOURCES.md`](data/SOURCES.md) for full provenance. In short:
- School names/locations/sectors are real, sourced from a Scottish Government open dataset.
- **Primary** ratings are real inspection outcomes, but coverage is partial (Scotland does
  light-touch inspection) and the underlying source only covers inspections up to June 2020 —
  some ratings shown may be over a decade old. Always check the inspection date shown in the
  popup. The rating is an illustrative average of the graded quality indicators, not an official
  single overall grade — Education Scotland doesn't publish one.
- **Secondary** ratings are real, current (2023-25) SQA attainment figures from
  statistics.gov.scot, banded into the same illustrative scale. This is a raw percentage, not
  adjusted for pupils' backgrounds — see the popup and `data/SOURCES.md` for the "virtual
  comparator" caveat.

## Regenerating the data

```
pip3 install openpyxl
python3 scripts/build_schools_json.py
```

This reads the files in `data/raw/` and rewrites `data/schools.json`. To refresh with newer
source data, replace the files in `data/raw/` first (see `data/SOURCES.md` for where they came
from, including the SPARQL query used for the secondary attainment data).

## File structure

```
index.html                     Homepage: area picker (clickable map of Scotland's 6 macro regions)
css/regions.css                Area picker styling
js/regions-page.js             Area picker: renders the map, click/hover/keyboard wiring
js/regions-data.js             Shared region -> local authority definitions
js/scotland-geometry.js        Generated: real local authority boundary shapes (see below)
scripts/build_regions_geometry.py  Rebuilds js/scotland-geometry.js from data/raw/scotland_la_boundaries.geojson
map.html                       Main schools map
css/style.css                  Main map styling
js/app.js                      Map init, layer toggling, region-param handling
js/markers.js                  Icon/colour/popup builders
js/data-loader.js              Fetches data/schools.json
data/schools.json              Final dataset used by the app
data/raw/                      Downloaded source files (provenance)
data/SOURCES.md                Source URLs, fetch dates, known limitations
scripts/build_schools_json.py  Rebuilds data/schools.json from data/raw/
```
