"""
Generates a static detail page for every school in data/schools.json, at
schools/<local-authority-slug>/<school-slug>.html (paths already computed by
build_schools_json.py and stored as each school's `pageUrl`).

Every fact shown is pulled directly from data/schools.json -- no invented
narrative, no fields we don't actually have data for (see the "Explicitly
excluded from v1" list agreed before building this: star ratings, founded
year, capacity, attendance %, placing requests, catchment area, "Living
nearby", FAQs, "People also viewed", photos).

Run with: python3 scripts/build_school_pages.py
(requires data/schools.json to already be built -- run build_schools_json.py
first if source data has changed)
"""
import heapq
import json
import math
import os
from html import escape

from region_mapping import REGION_NAMES, region_slug_for_la

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHOOLS_JSON = os.path.join(ROOT, "data", "schools.json")
OUT_ROOT = ROOT
SITE_BASE_URL = "https://www.scotlandschoolmap.co.uk"

NEARBY_COUNT = 4

GRADE_LABELS = {
    6: "Excellent",
    5: "Very Good",
    4: "Good",
    3: "Satisfactory",
    2: "Weak",
    1: "Unsatisfactory",
}

QI_LABELS = {
    "1.1": "Self-evaluation for self-improvement",
    "1.3": "Leadership of change",
    "2.1": "Curriculum",
    "2.3": "Learning, teaching and assessment",
    "3.1": "Ensuring wellbeing, equality and inclusion",
    "3.2": "Raising attainment and achievement",
    "5.1": "The curriculum",
    "5.3": "Meeting learning needs",
    "5.9": "Improvement through self-evaluation",
}

GRADIENT_STOPS = [
    (0.0, (215, 48, 39)),
    (0.5, (254, 224, 139)),
    (1.0, (26, 152, 80)),
]
NO_DATA_COLOR = "#9e9e9e"


def color_for_score(score, has_data):
    if not has_data or score is None:
        return NO_DATA_COLOR
    clamped = max(0.0, min(1.0, score))
    lower, upper = GRADIENT_STOPS[0], GRADIENT_STOPS[-1]
    for i in range(len(GRADIENT_STOPS) - 1):
        if GRADIENT_STOPS[i][0] <= clamped <= GRADIENT_STOPS[i + 1][0]:
            lower, upper = GRADIENT_STOPS[i], GRADIENT_STOPS[i + 1]
            break
    span = upper[0] - lower[0]
    t = 0 if span == 0 else (clamped - lower[0]) / span
    rgb = tuple(round(lower[1][c] + t * (upper[1][c] - lower[1][c])) for c in range(3))
    return f"rgb({rgb[0]}, {rgb[1]}, {rgb[2]})"


def haversine_km(lat1, lng1, lat2, lng2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def nearest_schools(school, all_schools, n=NEARBY_COUNT):
    candidates = (s for s in all_schools if s is not school)
    scored = (
        (haversine_km(school["lat"], school["lng"], s["lat"], s["lng"]), s)
        for s in candidates
    )
    return heapq.nsmallest(n, scored, key=lambda pair: pair[0])


def region_link(school):
    slug = region_slug_for_la(school["localAuthority"])
    if slug is None:
        return None
    return slug, REGION_NAMES[slug]


def build_breadcrumb(school):
    parts = ['<a href="/">Home</a>']
    region = region_link(school)
    if region:
        slug, name = region
        parts.append(f'<a href="/map.html?region={escape(slug)}">{escape(name)}</a>')
    parts.append(f"<span>{escape(school['localAuthority'])}</span>")
    parts.append(f"<span>{escape(school['name'])}</span>")
    return '<nav class="breadcrumb" aria-label="Breadcrumb">' + " &rsaquo; ".join(parts) + "</nav>"


def build_summary_sentence(school):
    sector_word = "primary" if school["sector"] == "primary" else "secondary"
    denom = school["denomination"]
    denom_phrase = f"{denom.lower()} " if denom and denom != "Not specified" else ""
    sentence = (
        f"{school['name']} is a {denom_phrase}{sector_word} school in the "
        f"{school['localAuthority']} local authority area."
    )

    rating = school["rating"]
    if rating["hasData"] and rating["metric"] == "inspection":
        sentence += (
            f" According to its most recent Education Scotland inspection "
            f"({rating['inspectionDate']}), it was rated {rating['label'].lower()} "
            f"on the quality indicators graded at that visit."
        )
    elif rating["hasData"] and rating["metric"] == "attainment":
        sentence += (
            f" In {rating['year']}, {rating['percent']}% of its leaver cohort "
            f"attained 5 or more qualifications at Higher level or above."
        )

    if school.get("pupilRoll"):
        sentence += f" The school has a pupil roll of {school['pupilRoll']:,}."

    return sentence


def build_quick_facts(school):
    facts = [
        ("School type", school["sector"].capitalize()),
        ("Local authority", school["localAuthority"]),
        ("Denomination", school["denomination"]),
    ]
    if school["rating"]["hasData"]:
        facts.append(("Rating", school["rating"]["label"]))
    if school.get("pupilRoll"):
        facts.append(("Pupil roll", f"{school['pupilRoll']:,}"))
    if school.get("pupilRoll") and school.get("fteTeachers"):
        ratio = school["pupilRoll"] / school["fteTeachers"]
        facts.append(("Pupil:teacher ratio", f"{ratio:.1f}:1"))
    return facts


def build_quick_facts_html(school):
    cards = "".join(
        f'<div class="fact-card"><span class="fact-label">{escape(label)}</span>'
        f'<span class="fact-value">{escape(str(value))}</span></div>'
        for label, value in build_quick_facts(school)
    )
    return f'<div class="quick-facts-grid">{cards}</div>'


def build_rating_section_html(school):
    rating = school["rating"]
    if not rating["hasData"]:
        return '<p class="no-rating">No rating data is available for this school.</p>'

    if rating["metric"] == "inspection":
        cards = "".join(
            f'''<div class="rating-card" style="border-top-color: {color_for_score((val - 1) / 5, True)}">
              <span class="rating-card-label">{escape(QI_LABELS.get(qi, f"Quality indicator {qi}"))}</span>
              <span class="rating-card-value">{escape(GRADE_LABELS.get(val, val))}</span>
            </div>'''
            for qi, val in rating["qiScores"].items()
        )
        return f'''
          <p class="rating-source">Inspected {escape(rating['inspectionDate'])} by Education Scotland.
            Rating is an illustrative average of the quality indicators graded at that inspection,
            not an official single overall grade.</p>
          <div class="rating-cards">{cards}</div>'''

    color = color_for_score(rating["score"], True)
    return f'''
      <div class="rating-cards">
        <div class="rating-card" style="border-top-color: {color}">
          <span class="rating-card-label">5+ Higher passes</span>
          <span class="rating-card-value">{escape(str(rating['percent']))}%</span>
        </div>
      </div>
      <p class="rating-source">SQA attainment, {escape(rating['year'])} &mdash; Scottish Government
        (statistics.gov.scot, "Breadth and Depth of Qualifications"). This is a raw attainment
        figure, not adjusted for pupils' backgrounds &mdash; the official methodology recommends
        comparing a school to its "virtual comparator" for a fairer read, which this page does
        not show.</p>'''


def build_contact_html(school):
    rows = [f'<div class="contact-row"><span>Address</span><span>{escape(school["address"])}</span></div>']
    if school.get("phone"):
        rows.append(
            f'<div class="contact-row"><span>Phone</span>'
            f'<span><a href="tel:{escape(school["phone"])}">{escape(school["phone"])}</a></span></div>'
        )
    if school.get("email"):
        rows.append(
            f'<div class="contact-row"><span>Email</span>'
            f'<span><a href="mailto:{escape(school["email"])}">{escape(school["email"])}</a></span></div>'
        )
    if school.get("website"):
        rows.append(
            f'<div class="contact-row"><span>Website</span>'
            f'<span><a href="{escape(school["website"])}" rel="noopener" target="_blank">'
            f'{escape(school["website"])}</a></span></div>'
        )
    return '<div class="contact-list">' + "".join(rows) + "</div>"


def build_nearby_html(nearest):
    cards = []
    for dist_km, s in nearest:
        rating = s["rating"]
        rating_badge = (
            f'<span class="nearby-rating" style="background: {color_for_score(rating["score"], True)}">'
            f'{escape(rating["label"])}</span>'
            if rating["hasData"]
            else '<span class="nearby-rating nearby-rating--none">No data</span>'
        )
        cards.append(f'''
          <a class="nearby-card" href="/{escape(s['pageUrl'])}">
            <div class="nearby-card-top">
              <span class="nearby-sector">{escape(s['sector'].capitalize())}</span>
              <span class="nearby-distance">{dist_km:.1f} km</span>
            </div>
            <div class="nearby-name">{escape(s['name'])}</div>
            <div class="nearby-la">{escape(s['localAuthority'])}</div>
            {rating_badge}
          </a>''')
    return '<div class="nearby-grid">' + "".join(cards) + "</div>"


def render_school_page(school, nearest):
    region = region_link(school)
    region_slug = region[0] if region else ""
    rating = school["rating"]
    color = color_for_score(rating.get("score"), rating["hasData"])
    rating_summary = (
        f'{escape(rating["label"])}' if rating["hasData"] else "No rating data"
    )
    icon_shape = "circle" if school["sector"] == "primary" else "triangle"

    map_link = f"/map.html?region={escape(region_slug)}&school={school['seedCode']}"

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(school['name'])} &mdash; {escape(school['localAuthority'])} | Scotland Schools Map</title>
<meta name="description" content="{escape(build_summary_sentence(school))}">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
  integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin="" />
<link rel="stylesheet" href="/css/site-header.css?v=10">
<link rel="stylesheet" href="/css/site-footer.css?v=1">
<link rel="stylesheet" href="/css/school-page.css?v=2">
</head>
<body>

<header id="site-header">
  <a class="site-title" href="/" style="color:inherit;text-decoration:none;">Scotland Schools Map</a>
  <button id="menu-toggle" aria-label="Open menu" aria-expanded="false" aria-controls="site-menu">
    <span></span><span></span><span></span>
  </button>
  <nav id="site-menu" hidden>
    <p class="site-menu-placeholder">More sections coming soon.</p>
  </nav>
</header>

<main id="school-page">
  {build_breadcrumb(school)}

  <div class="school-hero">
    <div>
      <span class="sector-badge sector-badge--{school['sector']}">{escape(school['sector'].capitalize())} school</span>
      <h1>{escape(school['name'])}</h1>
      <div class="hero-rating">
        <span class="rating-dot" style="background:{color}"></span>
        <strong>{rating_summary}</strong>
      </div>
      <p class="summary-text">{escape(build_summary_sentence(school))}</p>
      <a class="view-map-link" href="{map_link}">View on interactive map &rarr;</a>
    </div>
    <div id="school-map" data-lat="{school['lat']}" data-lng="{school['lng']}"
         data-name="{escape(school['name'])}" data-shape="{icon_shape}" data-color="{color}"></div>
  </div>

  <section>
    <h2>Overview</h2>
    {build_quick_facts_html(school)}
  </section>

  <section>
    <h2>Rating detail</h2>
    {build_rating_section_html(school)}
  </section>

  <div class="two-col">
    <section>
      <h2>Contact details</h2>
      {build_contact_html(school)}
    </section>

    <section>
      <h2>Nearby schools</h2>
      {build_nearby_html(nearest)}
    </section>
  </div>
</main>

<footer id="site-footer">
  <p>&copy; 2026 Scotland Schools Map. All rights reserved.</p>
  <nav class="footer-links">
    <a href="#">About</a>
    <a href="#">Privacy</a>
    <a href="#">Contact</a>
    <a href="/data/SOURCES.md">Data sources</a>
  </nav>
</footer>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
  integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
<script src="/js/site-header.js?v=10"></script>
<script src="/js/school-page.js?v=1"></script>
</body>
</html>
'''


def build_sitemap(schools):
    urls = [f"{SITE_BASE_URL}/", f"{SITE_BASE_URL}/map.html"]
    urls += [f"{SITE_BASE_URL}/{s['pageUrl']}" for s in schools]
    entries = "\n".join(f"  <url><loc>{escape(u)}</loc></url>" for u in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{entries}\n</urlset>\n'


def main():
    schools = json.load(open(SCHOOLS_JSON))

    written = 0
    for school in schools:
        nearest = nearest_schools(school, schools)
        html = render_school_page(school, nearest)
        out_path = os.path.join(OUT_ROOT, school["pageUrl"])
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w") as f:
            f.write(html)
        written += 1

    sitemap_path = os.path.join(OUT_ROOT, "sitemap.xml")
    with open(sitemap_path, "w") as f:
        f.write(build_sitemap(schools))

    print(f"Wrote {written} school pages under {OUT_ROOT}/schools/")
    print(f"Wrote sitemap with {len(schools) + 2} URLs to {sitemap_path}")


if __name__ == "__main__":
    main()
