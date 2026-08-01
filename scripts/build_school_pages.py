"""
Generates a static detail page for every school in data/schools.json, at
schools/<local-authority-slug>/<school-slug>.html (paths already computed by
build_schools_json.py and stored as each school's `pageUrl`).

Run with: python3 scripts/build_school_pages.py
(requires data/schools.json to already be built -- run build_schools_json.py
first if source data has changed)
"""
import csv
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

NO_DATA_COLOR = "#9e9e9e"

GAUGE_COLORS = ["#EA580C", "#FACC15", "#4ADE80", "#22C55E", "#16A34A"]

RATING_COLORS = {
    "Excellent": "#16A34A",
    "Very Good": "#22C55E",
    "Good": "#4ADE80",
    "Satisfactory": "#A3E635",
    "Weak": "#FACC15",
    "Unsatisfactory": "#EA580C",
}

GAUGE_POSITIONS = {
    "Excellent": 0.9,
    "Very Good": 0.7,
    "Good": 0.5,
    "Satisfactory": 0.35,
    "Weak": 0.25,
    "Unsatisfactory": 0.1,
}

CRIME_CONFIG = {
    "Low": {
        "color": "#16a34a",
        "bar_pct": 25,
        "desc": "Crime rate in this area is lower than the Scotland average.",
    },
    "Medium": {
        "color": "#d97706",
        "bar_pct": 55,
        "desc": "Crime rate in this area is around the Scotland average.",
    },
    "High": {
        "color": "#dc2626",
        "bar_pct": 82,
        "desc": "Crime rate in this area is higher than the Scotland average.",
    },
}

# ---------------------------------------------------------------------------
# Inline SVG icons (Lucide-style, 20x20 for stat cards, 18x18 for contact)
# ---------------------------------------------------------------------------

STAT_ICON_COLORS = ["#6A4C93", "#17C3B2", "#FFCA3A", "#EF476F"]

ICON_SHIELD = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" '
    'fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>'
)
ICON_BUILDING = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" '
    'fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M3 21h18"/><path d="M5 21V7l8-4v18"/><path d="M19 21V11l-6-4"/>'
    '<path d="M9 9h1"/><path d="M9 13h1"/><path d="M9 17h1"/></svg>'
)
ICON_USERS = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" '
    'fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>'
    '<path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>'
)
ICON_BAR_CHART = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" '
    'fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/>'
    '<line x1="6" y1="20" x2="6" y2="14"/></svg>'
)
ICON_MAP_PIN = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" '
    'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>'
)
ICON_PHONE = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" '
    'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 '
    '19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 '
    '2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 '
    '2.81.7A2 2 0 0 1 22 16.92z"/></svg>'
)
ICON_GLOBE = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" '
    'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/>'
    '<path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10A15.3 15.3 0 0 1 12 2z"/></svg>'
)
ICON_MAIL = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" '
    'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>'
)
ICON_INFO = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" '
    'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>'
)


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def color_for_label(label, has_data):
    if not has_data or not label:
        return NO_DATA_COLOR
    return RATING_COLORS.get(label, NO_DATA_COLOR)


def haversine_km(lat1, lng1, lat2, lng2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def nearest_schools(school, all_schools, n=NEARBY_COUNT):
    candidates = (
        s for s in all_schools
        if s is not school and s["sector"] == school["sector"]
    )
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


def compute_averages(schools):
    sec_by_la, sec_all = {}, []
    pri_by_la, pri_all = {}, []
    ratio_all = []

    for s in schools:
        if s.get("pupilRoll") and s.get("fteTeachers") and s["fteTeachers"] > 0:
            ratio_all.append(s["pupilRoll"] / s["fteTeachers"])

        rating = s["rating"]
        if not rating["hasData"]:
            continue
        if rating["metric"] == "attainment":
            pct = rating["percent"]
            sec_by_la.setdefault(s["localAuthority"], []).append(pct)
            sec_all.append(pct)
        elif rating["metric"] == "inspection":
            avg = rating["averageScore"]
            pri_by_la.setdefault(s["localAuthority"], []).append(avg)
            pri_all.append(avg)

    def mean(lst):
        return sum(lst) / len(lst) if lst else None

    return {
        "secondary": {
            "national": mean(sec_all),
            "by_la": {la: mean(v) for la, v in sec_by_la.items()},
        },
        "primary": {
            "national": mean(pri_all),
            "by_la": {la: mean(v) for la, v in pri_by_la.items()},
        },
        "ratio_national": mean(ratio_all),
    }


HPI_CSV = os.path.join(ROOT, "data", "raw", "uk-hpi-property-type.csv")
CRIME_CSV = os.path.join(ROOT, "data", "raw", "recorded-crime-scotland.csv")

HPI_NAME_MAP = {
    "City of Aberdeen": "Aberdeen City",
    "City of Dundee": "Dundee City",
    "City of Glasgow": "Glasgow City",
}
CRIME_NAME_MAP = {
    "Na h-Eileanan Siar": "Na h-Eileanan an Iar",
}


PROPERTY_TYPES = [
    ("Detached", "Detached_Average_Price"),
    ("Semi-detached", "Semi_Detached_Average_Price"),
    ("Terraced", "Terraced_Average_Price"),
    ("Flats", "Flat_Average_Price"),
]


def load_property_prices():
    """Load latest UK HPI average prices by property type for Scottish LAs.

    Returns (la_prices, scotland_avg) where scotland_avg is the mean of all
    LA prices per property type.
    """
    latest = {}
    with open(HPI_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            code = row["Area_Code"]
            if not code.startswith("S12"):
                continue
            name = HPI_NAME_MAP.get(row["Region_Name"], row["Region_Name"])
            date = row["Date"]
            if name not in latest or date > latest[name]["date"]:
                prices = []
                for ptype, col in PROPERTY_TYPES:
                    val = row[col].strip()
                    if val:
                        prices.append((ptype, round(float(val))))
                latest[name] = {"date": date, "prices": prices}
    la_prices = {la: d["prices"] for la, d in latest.items()}

    sums = {}
    counts = {}
    for prices in la_prices.values():
        for ptype, price in prices:
            sums[ptype] = sums.get(ptype, 0) + price
            counts[ptype] = counts.get(ptype, 0) + 1
    scotland_avg = {
        ptype: round(sums[ptype] / counts[ptype]) for ptype in sums
    }
    return la_prices, scotland_avg


def load_crime_rates():
    """Load 2024/25 recorded crime rates per 10,000 population for Scottish LAs."""
    rates = {}
    scotland_rate = None
    with open(CRIME_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["DateCode"] != "2024/2025":
                continue
            if row["Measurement"] != "Ratio":
                continue
            if row["Crime or Offence"] != "All Crimes":
                continue
            code = row["FeatureCode"]
            name = row["FeatureName"]
            val = float(row["Value"])
            if code == "S92000003":
                scotland_rate = val
            elif code.startswith("S12"):
                name = CRIME_NAME_MAP.get(name, name)
                rates[name] = val
    return rates, scotland_rate


# ---------------------------------------------------------------------------
# HTML builders
# ---------------------------------------------------------------------------

def build_breadcrumb(school):
    parts = ['<a href="/">Home</a>']
    region = region_link(school)
    if region:
        slug, name = region
        parts.append(f'<a href="/map.html?region={escape(slug)}">{escape(name)}</a>')
    parts.append(f"<span>{escape(school['localAuthority'])}</span>")
    parts.append(f"<span>{escape(school['name'])}</span>")
    return '<nav class="breadcrumb" aria-label="Breadcrumb">' + " &rsaquo; ".join(parts) + "</nav>"


def stat_icon_html(icon_svg, color):
    return (
        f'<div class="stat-icon-circle" style="background:{color}">'
        f'{icon_svg}</div>'
    )


def build_stat_cards(school, averages):
    rating = school["rating"]
    cards = []

    # Card 1: School Rating
    if rating["hasData"]:
        color = color_for_label(rating["label"], True)
        value = rating["label"]
        if rating["metric"] == "inspection":
            sub = f'Inspected {rating["inspectionDate"]}'
        else:
            sub = f'SQA {rating["year"]}'
    else:
        color = NO_DATA_COLOR
        value = "No data"
        sub = ""

    cards.append(
        f'<div class="stat-card">'
        f'{stat_icon_html(ICON_SHIELD, STAT_ICON_COLORS[0])}'
        f'<div class="stat-label">School Rating</div>'
        f'<div class="stat-value" style="color:{color}">{escape(value)}</div>'
        + (f'<div class="stat-sub">{escape(sub)}</div>' if sub else "")
        + "</div>"
    )

    # Card 2: Denomination
    cards.append(
        f'<div class="stat-card">'
        f'{stat_icon_html(ICON_BUILDING, STAT_ICON_COLORS[1])}'
        f'<div class="stat-label">Denomination</div>'
        f'<div class="stat-value">{escape(school["denomination"])}</div>'
        f"</div>"
    )

    # Card 3: Pupil Roll
    roll = school.get("pupilRoll")
    cards.append(
        f'<div class="stat-card">'
        f'{stat_icon_html(ICON_USERS, STAT_ICON_COLORS[2])}'
        f'<div class="stat-label">Pupil Roll</div>'
        f'<div class="stat-value">{f"{roll:,}" if roll else "N/A"}</div>'
        f"</div>"
    )

    # Card 4: Pupil:Teacher Ratio
    fte = school.get("fteTeachers")
    if roll and fte and fte > 0:
        ratio = roll / fte
        ratio_str = f"{ratio:.1f}:1"
        nat = averages.get("ratio_national")
        sub2 = f"Scotland avg: {nat:.1f}:1" if nat else ""
    else:
        ratio_str = "N/A"
        sub2 = ""

    cards.append(
        f'<div class="stat-card">'
        f'{stat_icon_html(ICON_BAR_CHART, STAT_ICON_COLORS[3])}'
        f'<div class="stat-label">Pupil:Teacher Ratio</div>'
        f'<div class="stat-value">{escape(ratio_str)}</div>'
        + (f'<div class="stat-sub">{escape(sub2)}</div>' if sub2 else "")
        + "</div>"
    )

    return '<div class="stat-cards">' + "".join(cards) + "</div>"


def build_gauge_svg(label, has_data):
    if not has_data:
        return '<div class="gauge-no-data">No rating data available</div>'

    cx, cy, r = 100, 95, 75
    sw = 18

    bg_x1 = cx + r * math.cos(math.pi)
    bg_y1 = cy - r * math.sin(math.pi)
    bg_x2 = cx + r * math.cos(0)
    bg_y2 = cy - r * math.sin(0)
    bg_arc = (
        f'<path d="M {bg_x1:.1f} {bg_y1:.1f} A {r} {r} 0 1 1 {bg_x2:.1f} {bg_y2:.1f}" '
        f'fill="none" stroke="#EFF6FF" stroke-width="{sw}" stroke-linecap="round"/>'
    )

    pos = GAUGE_POSITIONS.get(label, 0.5)
    fill_angle = math.pi * (1 - pos)
    fx = cx + r * math.cos(fill_angle)
    fy = cy - r * math.sin(fill_angle)
    fill_color = RATING_COLORS.get(label, GAUGE_COLORS[2])
    fill_arc = (
        f'<path d="M {bg_x1:.1f} {bg_y1:.1f} A {r} {r} 0 0 1 {fx:.1f} {fy:.1f}" '
        f'fill="none" stroke="{fill_color}" stroke-width="{sw}" stroke-linecap="round"/>'
    )

    return (
        f'<svg class="rating-gauge" viewBox="0 0 200 125" xmlns="http://www.w3.org/2000/svg">'
        f'{bg_arc}{fill_arc}'
        f'<text x="{cx}" y="{cy + 22}" text-anchor="middle" '
        f'font-family="-apple-system, BlinkMacSystemFont, sans-serif" '
        f'font-size="14" font-weight="700" fill="{fill_color}">{escape(label)}</text>'
        f"</svg>"
    )


def build_comparison_bars(school, averages):
    rating = school["rating"]
    if not rating["hasData"]:
        return ""

    la = school["localAuthority"]

    if rating["metric"] == "attainment":
        school_val = rating["percent"]
        la_avg = averages["secondary"]["by_la"].get(la)
        nat_avg = averages["secondary"]["national"]

        def bar_width(v):
            return max(2, v)

        def fmt(v):
            return f"{v:.0f}%"

        title = "Attainment: 5+ Higher Pass Rate"
    else:
        school_val = rating["averageScore"]
        la_avg = averages["primary"]["by_la"].get(la)
        nat_avg = averages["primary"]["national"]

        def bar_width(v):
            return max(2, (v - 1) / 5 * 100)

        def fmt(v):
            return f"{v:.1f} / 6"

        title = "Average Inspection Score"

    school_color = color_for_label(rating["label"], True)
    avg_color = "#94a3b8"

    bars = [(school["name"], school_val, school_color, bar_width(school_val))]
    if la_avg is not None:
        bars.append((f"{la} avg", la_avg, avg_color, bar_width(la_avg)))
    if nat_avg is not None:
        bars.append(("Scotland avg", nat_avg, avg_color, bar_width(nat_avg)))

    rows = "".join(
        f'<div class="bar-row">'
        f'<span class="bar-label" title="{escape(name)}">{escape(name)}</span>'
        f'<div class="bar-track"><div class="bar-fill" style="width:{width:.1f}%;background:{color}"></div></div>'
        f'<span class="bar-value">{fmt(val)}</span>'
        f"</div>"
        for name, val, color, width in bars
    )

    return (
        f'<h3 class="comparison-title">{escape(title)}</h3>'
        f'<div class="comparison-bars">{rows}</div>'
    )


def build_performance_section(school, averages):
    rating = school["rating"]
    gauge = build_gauge_svg(rating.get("label", ""), rating["hasData"])
    bars = build_comparison_bars(school, averages)

    if rating["hasData"] and rating["metric"] == "inspection":
        source_text = (
            f"Inspected {escape(rating['inspectionDate'])} by Education Scotland. "
            f"Rating is an illustrative average of the quality indicators graded at that inspection, "
            f"not an official single overall grade."
        )
    elif rating["hasData"] and rating["metric"] == "attainment":
        source_text = (
            f"SQA attainment, {escape(rating['year'])} &mdash; Scottish Government "
            f"(statistics.gov.scot). Raw attainment figure, not adjusted for pupils' backgrounds."
        )
    else:
        source_text = ""

    info_tooltip = ""
    if source_text:
        info_tooltip = (
            f'<div class="info-tooltip">'
            f'<span class="info-icon" tabindex="0" aria-label="Data source information">{ICON_INFO}</span>'
            f'<div class="info-tooltip-content"><p>{source_text}</p></div>'
            f"</div>"
        )

    return (
        f'<section class="content-card">'
        f'<div class="card-header">'
        f"<h2>Rating &amp; Performance</h2>"
        f"{info_tooltip}"
        f"</div>"
        f'<div class="gauge-container">{gauge}</div>'
        f"{bars}"
        f"</section>"
    )


def build_hero_contact(school):
    rows = [
        f'<div class="contact-row">'
        f'<span class="contact-icon">{ICON_MAP_PIN}</span>'
        f"<span>{escape(school['address'])}</span>"
        f"</div>"
    ]

    if school.get("phone"):
        rows.append(
            f'<div class="contact-row">'
            f'<span class="contact-icon">{ICON_PHONE}</span>'
            f'<a href="tel:{escape(school["phone"])}">{escape(school["phone"])}</a>'
            f"</div>"
        )
    if school.get("website"):
        rows.append(
            f'<div class="contact-row">'
            f'<span class="contact-icon">{ICON_GLOBE}</span>'
            f'<a href="{escape(school["website"])}" rel="noopener" target="_blank">Visit website</a>'
            f"</div>"
        )
    if school.get("email"):
        rows.append(
            f'<div class="contact-row">'
            f'<span class="contact-icon">{ICON_MAIL}</span>'
            f'<a href="mailto:{escape(school["email"])}">Email the school</a>'
            f"</div>"
        )

    return f'<div class="hero-contact">{"".join(rows)}</div>'


def build_nearby_html(school, nearest):
    sector_label = "Primary" if school["sector"] == "primary" else "Secondary"
    items = []
    for dist_km, s in nearest:
        rating = s["rating"]
        if rating["hasData"]:
            badge_slug = rating["label"].lower().replace(" ", "-")
            badge = (
                f'<span class="nearby-badge nearby-badge--{badge_slug}">'
                f"{escape(rating['label'])}</span>"
            )
        else:
            badge = '<span class="nearby-badge nearby-badge--none">No data</span>'

        items.append(
            f'<a class="nearby-item" href="/{escape(s["pageUrl"])}">'
            f'<div class="nearby-info">'
            f'<div class="nearby-name">{escape(s["name"])}</div>'
            f'<div class="nearby-detail">{dist_km:.1f} km &middot; {escape(s["localAuthority"])}</div>'
            f"</div>"
            f"{badge}"
            f"</a>"
        )

    return (
        f'<section class="content-card">'
        f"<h2>Nearby {escape(sector_label)} Schools</h2>"
        f'<div class="nearby-list-inner">{"".join(items)}</div>'
        f"</section>"
    )


def build_property_section(la_name, all_prices, scotland_avg):
    prices = all_prices.get(la_name)
    if not prices:
        return ""
    rows = []
    for ptype, price in prices:
        nat = scotland_avg.get(ptype)
        if nat and price < nat * 0.97:
            diff_color = "#16a34a"
        elif nat and price > nat * 1.03:
            diff_color = "#dc2626"
        else:
            diff_color = "#888"
        nat_str = f"&pound;{nat:,}" if nat else "N/A"
        rows.append(
            f'<div class="price-row">'
            f'<span class="price-type">{escape(ptype)}</span>'
            f'<span class="price-values">'
            f'<span class="price-value">&pound;{price:,}</span>'
            f'<span class="price-nat" style="color:{diff_color}">{nat_str}</span>'
            f'</span>'
            f"</div>"
        )
    return (
        f'<div class="area-card">'
        f"<h3>Average Property Prices</h3>"
        f'<p class="area-subtitle">{escape(la_name)}</p>'
        f'<div class="price-header">'
        f'<span class="price-type">Type</span>'
        f'<span class="price-header-right">'
        f'<span>Local</span><span>Scotland avg</span>'
        f'</span>'
        f'</div>'
        f'<div class="price-list">{"".join(rows)}</div>'
        f'<p class="source-note">UK House Price Index, March 2026. '
        f"Council-area averages &mdash; prices vary within each authority.</p>"
        f"</div>"
    )


def build_crime_section(la_name, all_crime_rates, scotland_rate):
    rate = all_crime_rates.get(la_name)
    if rate is None or scotland_rate is None:
        return ""
    if rate < scotland_rate * 0.7:
        level = "Low"
    elif rate < scotland_rate * 1.15:
        level = "Medium"
    else:
        level = "High"
    cfg = CRIME_CONFIG[level]
    max_rate = max(all_crime_rates.values())
    bar_pct = max(2, min(98, rate / max_rate * 100))
    return (
        f'<div class="area-card">'
        f"<h3>Crime Rate</h3>"
        f'<p class="area-subtitle">{escape(la_name)}</p>'
        f'<div class="crime-display">'
        f'<span class="crime-dot" style="background:{cfg["color"]}"></span>'
        f'<span class="crime-label" style="color:{cfg["color"]}">{escape(level)}</span>'
        f"</div>"
        f'<p class="crime-desc">{round(rate)} crimes per 10,000 people '
        f"(Scotland average: {round(scotland_rate)}).</p>"
        f'<div class="crime-bar-track">'
        f'<div class="crime-bar-fill" style="left:{bar_pct:.0f}%;background:{cfg["color"]}"></div>'
        f"</div>"
        f'<div class="crime-bar-labels"><span>Low</span><span>High</span></div>'
        f'<p class="source-note">Recorded Crime in Scotland 2024&ndash;25, '
        f"Scottish Government. All recorded crimes per 10,000 population.</p>"
        f"</div>"
    )


# ---------------------------------------------------------------------------
# Page renderer
# ---------------------------------------------------------------------------

def render_school_page(school, nearest, averages, all_prices, scotland_avg_prices, all_crime_rates, scotland_crime_rate):
    region = region_link(school)
    region_slug = region[0] if region else ""
    rating = school["rating"]
    color = color_for_label(rating.get("label"), rating["hasData"])
    icon_shape = "circle" if school["sector"] == "primary" else "triangle"
    map_link = f"/map.html?region={escape(region_slug)}&school={school['seedCode']}"

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(school['name'])} &mdash; {escape(school['localAuthority'])} | Scotland Schools Map</title>
<meta name="description" content="{escape(school['name'])} is a {escape(school['sector'])} school in {escape(school['localAuthority'])}.">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
  integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin="" />
<link rel="stylesheet" href="/css/site-header.css?v=10">
<link rel="stylesheet" href="/css/site-footer.css?v=1">
<link rel="stylesheet" href="/css/school-page.css?v=3">
</head>
<body>

<header id="site-header">
  <div style="display: flex; align-items: center;">
    <a href="/" class="site-logo">
      <img src="/assets/logo.svg" alt="Scotland Schools Map logo">
    </a>
    <a href="/" class="site-title" style="color: inherit; text-decoration: none;">Scotland Schools Map</a>
  </div>
  <nav id="site-menu">
    <a href="/search.html" class="site-menu-item">Find a school</a>
    <a href="/explore.html" class="site-menu-item">Explore areas</a>
  </nav>
</header>

<main id="school-page">
  {build_breadcrumb(school)}

  <div class="school-hero">
    <div class="hero-info">
      <span class="sector-badge">{escape(school['sector'].capitalize())} school</span>
      <h1>{escape(school['name'])}</h1>
      <p class="hero-la">{escape(school['localAuthority'])}</p>
      {build_hero_contact(school)}
    </div>
    <div class="hero-map-wrap">
      <div id="school-map" data-lat="{school['lat']}" data-lng="{school['lng']}"
           data-name="{escape(school['name'])}" data-shape="{icon_shape}" data-color="{color}"></div>
      <a class="map-expand-link" href="{map_link}">View on the interactive map &rarr;</a>
    </div>
  </div>

  {build_stat_cards(school, averages)}

  <div class="section-grid">
    {build_performance_section(school, averages)}
    {build_nearby_html(school, nearest)}
  </div>

  <section class="page-section">
    <h2>Local Area Insights</h2>
    <p class="section-sub">Key information about the area surrounding this school.</p>
    <div class="area-grid">
      {build_property_section(school['localAuthority'], all_prices, scotland_avg_prices)}
      {build_crime_section(school['localAuthority'], all_crime_rates, scotland_crime_rate)}
    </div>
  </section>
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
    averages = compute_averages(schools)
    all_prices, scotland_avg_prices = load_property_prices()
    all_crime_rates, scotland_crime_rate = load_crime_rates()

    written = 0
    for school in schools:
        nearest = nearest_schools(school, schools)
        html = render_school_page(school, nearest, averages, all_prices, scotland_avg_prices, all_crime_rates, scotland_crime_rate)
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
