"""
Build the 6 macro-area pages under /areas/.
Each page covers one of Scotland's six regions with:
  - Hero photo + CTA to the interactive map
  - Top 10 primary schools (by inspection score)
  - Top 10 secondary schools (by SQA Higher pass rate)
  - Property prices (averaged across the region's LAs)
  - Crime breakdown (Overall, Violent, Housebreaking, Car crime, Anti-social)
  - Local authority cards
"""

import csv, json, math, os, re
from html import escape

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Region definitions ────────────────────────────────────────────────────────

REGIONS = {
    "glasgow-strathclyde": {
        "name": "Glasgow and Strathclyde",
        "tagline": "Scotland's largest city region, full of culture and opportunities.",
        "photo": "https://images.unsplash.com/photo-1704322624412-84ca3103ecfa?auto=format&fit=crop&w=1600&q=80",
        "localAuthorities": [
            "Glasgow City", "East Ayrshire", "East Dunbartonshire",
            "East Renfrewshire", "Inverclyde", "North Ayrshire",
            "North Lanarkshire", "Renfrewshire", "South Ayrshire",
            "South Lanarkshire", "West Dunbartonshire",
        ],
        "intro": [
            "Glasgow and Strathclyde is Scotland's largest and most diverse region, stretching from the city of Glasgow to the Ayrshire coast and the shores of Loch Lomond. The region covers Glasgow City, North and South Lanarkshire, East and West Dunbartonshire, Renfrewshire, East Renfrewshire, Inverclyde, and the three Ayrshire councils.",
            "Explore school performance, compare local house prices and crime data, and discover the communities that best match your family's needs.",
        ],
        "why_families": {
            "eyebrow": "WHY FAMILIES CHOOSE",
            "heading": "Glasgow and Strathclyde",
            "intro": "From Scotland's most exciting city to coastal towns and countryside, Glasgow and Strathclyde offers families an extraordinary range of places to live, learn and grow.",
            "items": [
                {
                    "icon": "school",
                    "title": "Excellent Schools",
                    "body": "A wide range of primary and secondary schools across eleven local authorities, with many achieving strong inspection results.",
                    "photo": "https://images.unsplash.com/photo-1588072432836-e10032774350?auto=format&fit=crop&w=800&q=80",
                    "photo_alt": "Children sitting at desks in a classroom",
                },
                {
                    "icon": "home",
                    "title": "Vibrant City Living",
                    "body": "From Glasgow's dynamic city centre and West End to quieter suburban communities across the region, there's a neighbourhood for every family.",
                    "photo": "https://images.unsplash.com/photo-1531152369337-1d0b0b9ef20d?auto=format&fit=crop&w=800&q=80",
                    "photo_alt": "People walking in Glasgow city centre",
                },
                {
                    "icon": "train",
                    "title": "Excellent Connections",
                    "body": "One of the best-connected regions in Scotland, with an extensive rail network, the Subway and easy road links across central Scotland.",
                    "photo": "https://images.unsplash.com/photo-1598476959236-fd5b8e15e64c?auto=format&fit=crop&w=800&q=80",
                    "photo_alt": "Glasgow Subway station with distinctive orange columns",
                },
                {
                    "icon": "tree",
                    "title": "Outdoor Adventures",
                    "body": "Loch Lomond, the Trossachs and the Ayrshire coast are all within easy reach — perfect for families who love the outdoors.",
                    "photo": "https://images.unsplash.com/photo-1607602274042-161d6cba839a?auto=format&fit=crop&w=800&q=80",
                    "photo_alt": "Green mountains beside a Scottish loch",
                },
                {
                    "icon": "briefcase",
                    "title": "Strong Economy",
                    "body": "Glasgow is Scotland's commercial capital, with a thriving job market across finance, tech, creative industries and the public sector.",
                    "photo": "https://images.unsplash.com/photo-1706606992443-538c5271ae41?auto=format&fit=crop&w=800&q=80",
                    "photo_alt": "Glasgow city street with tall buildings",
                },
                {
                    "icon": "heart",
                    "title": "Thriving Culture",
                    "body": "World-class museums, festivals, sports and a famously welcoming community make Glasgow and Strathclyde a great place to raise a family.",
                    "photo": "https://images.unsplash.com/photo-1779447789640-2d78161a9ff3?auto=format&fit=crop&w=800&q=80",
                    "photo_alt": "Riverside Museum Glasgow reflecting the Tall Ship and cloudy sky",
                },
            ],
        },
    },
    "edinburgh-lothians": {
        "name": "Edinburgh and Lothians",
        "tagline": "Scotland's capital region with excellent schools and amenities.",
        "photo": "https://images.unsplash.com/photo-1751922090004-6386496669c8?auto=format&fit=crop&w=1600&q=80",
        "localAuthorities": [
            "City of Edinburgh", "East Lothian", "Midlothian", "West Lothian",
        ],
        "intro": [
            "Edinburgh and the Lothians is one of Scotland's most desirable regions for families, offering excellent schools, strong transport links and a wide choice of communities. The region covers the City of Edinburgh, East Lothian, Midlothian and West Lothian.",
            "Explore school performance, compare local house prices and crime data, and discover the areas that best match your family's needs.",
        ],
        "why_families": {
            "eyebrow": "WHY FAMILIES CHOOSE",
            "heading": "Edinburgh and the Lothians",
            "intro": "From outstanding schools to beautiful places to live, Edinburgh and the Lothians offers families the perfect balance of opportunity, lifestyle and community.",
            "items": [
                {
                    "icon": "school",
                    "title": "Excellent Schools",
                    "body": "A wide choice of highly rated schools with strong academic results and supportive communities.",
                    "photo": "https://images.unsplash.com/photo-1636202339022-7d67f7447e3a?auto=format&fit=crop&w=800&q=80",
                    "photo_alt": "Children sitting at desks in a classroom",
                },
                {
                    "icon": "home",
                    "title": "Great Places to Live",
                    "body": "From vibrant city neighbourhoods to countryside and coastal towns, there's a place for every family.",
                    "photo": "https://images.unsplash.com/photo-1780618612142-bfd83659b659?auto=format&fit=crop&w=800&q=80",
                    "photo_alt": "Historic Edinburgh city street with red bus",
                },
                {
                    "icon": "train",
                    "title": "Excellent Connections",
                    "body": "Great transport links by road, rail and air make commuting and travelling easy.",
                    "photo": "https://images.unsplash.com/photo-1525943421222-633f69ca9078?auto=format&fit=crop&w=800&q=80",
                    "photo_alt": "Timelapse of Edinburgh street traffic",
                },
                {
                    "icon": "tree",
                    "title": "Outdoor Lifestyle",
                    "body": "Beautiful parks, beaches and countryside right on your doorstep for weekend adventures.",
                    "photo": "https://images.unsplash.com/photo-1610890690772-3f7fed4d7c80?auto=format&fit=crop&w=800&q=80",
                    "photo_alt": "Green Scottish coastline and sea",
                },
                {
                    "icon": "briefcase",
                    "title": "Strong Economy",
                    "body": "A diverse job market and thriving industries provide excellent career opportunities.",
                    "photo": "https://images.unsplash.com/photo-1668509549273-14abf4067904?auto=format&fit=crop&w=800&q=80",
                    "photo_alt": "Edinburgh city skyline at sunset",
                },
                {
                    "icon": "heart",
                    "title": "Thriving Communities",
                    "body": "Friendly communities, local events and family activities all year round.",
                    "photo": "https://images.unsplash.com/photo-1544176617-dc09515e2179?auto=format&fit=crop&w=800&q=80",
                    "photo_alt": "Edinburgh Christmas market at night",
                },
            ],
        },
    },
    "tayside-central-fife": {
        "name": "Tayside, Central and Fife",
        "tagline": "Great connections, historic towns and beautiful countryside.",
        "photo": "https://images.unsplash.com/photo-1692876292380-d9ad8c0f2f84?auto=format&fit=crop&w=1600&q=80",
        "localAuthorities": [
            "Angus", "Clackmannanshire", "Dundee City", "Falkirk",
            "Fife", "Perth and Kinross", "Stirling",
        ],
        "intro": [
            "Tayside, Central and Fife is a diverse region stretching from the Fife coastline to the heart of Scotland, taking in historic cities, market towns and scenic countryside. The region covers Dundee City, Angus, Perth and Kinross, Fife, Stirling, Falkirk and Clackmannanshire — connected by strong road and rail links to both Edinburgh and Glasgow.",
            "Explore school performance, compare local house prices and crime data, and discover the communities that best match your family's needs.",
        ],
        "why_families": {
            "eyebrow": "WHY FAMILIES CHOOSE",
            "heading": "Tayside, Central and Fife",
            "intro": "From Dundee's waterfront to the hills of Perthshire and the coast of Fife, this region offers families a remarkable range of places to live, with great schools, strong connections and beautiful landscapes.",
            "items": [
                {
                    "icon": "school",
                    "title": "Strong Schools",
                    "body": "A broad choice of primary and secondary schools across seven local authorities, from well-regarded city schools to thriving community schools in market towns.",
                    "photo": "https://images.unsplash.com/photo-1636202339022-7d67f7447e3a?auto=format&fit=crop&w=800&q=80",
                    "photo_alt": "Children sitting at desks in a classroom",
                },
                {
                    "icon": "home",
                    "title": "Great Places to Live",
                    "body": "From Dundee's regenerated waterfront to the historic towns of Stirling and St Andrews, there's a community to suit every family.",
                    "photo": "https://images.unsplash.com/photo-1605558162119-2de4d9ff8130?auto=format&fit=crop&w=800&q=80",
                    "photo_alt": "Dundee waterfront and V&A Museum",
                },
                {
                    "icon": "train",
                    "title": "Excellent Connections",
                    "body": "Well placed between Edinburgh and Glasgow, with strong rail and road links making the whole of central Scotland easily accessible.",
                    "photo": "https://images.unsplash.com/photo-1685702149672-af779c937876?auto=format&fit=crop&w=800&q=80",
                    "photo_alt": "Train at a station platform",
                },
                {
                    "icon": "tree",
                    "title": "Beautiful Countryside",
                    "body": "Perthshire's glens, the Lomond Hills and the Fife coastal path offer endless outdoor adventures right on your doorstep.",
                    "photo": "https://images.unsplash.com/photo-1680936613337-fc829882b375?auto=format&fit=crop&w=800&q=80",
                    "photo_alt": "Rolling green hills in Perthshire",
                },
                {
                    "icon": "briefcase",
                    "title": "Diverse Economy",
                    "body": "A growing tech and creative sector in Dundee, alongside traditional industries, tourism and a strong university presence across the region.",
                    "photo": "https://images.unsplash.com/photo-1648674136198-86bab411a319?auto=format&fit=crop&w=800&q=80",
                    "photo_alt": "Dundee city waterfront at dusk",
                },
                {
                    "icon": "heart",
                    "title": "Welcoming Communities",
                    "body": "Close-knit towns and villages with a strong sense of community, local events and family-friendly activities throughout the year.",
                    "photo": "https://images.unsplash.com/photo-1688713658343-68b132822277?auto=format&fit=crop&w=800&q=80",
                    "photo_alt": "Family walking together outdoors",
                },
            ],
        },
    },
    "highland-islands": {
        "name": "Highlands and Islands",
        "tagline": "Remote beauty, vibrant communities and a slower pace of life.",
        "photo": "https://images.unsplash.com/photo-1611422111224-bde09221f95b?auto=format&fit=crop&w=1600&q=80",
        "localAuthorities": [
            "Highland", "Argyll and Bute", "Na h-Eileanan an Iar",
            "Orkney Islands", "Shetland Islands",
        ],
        "intro": [
            "The Highlands and Islands is Scotland's most expansive region, covering a vast and varied landscape that stretches from Argyll and Bute in the south to Shetland in the far north. The region includes Highland, Argyll and Bute, Na h-Eileanan an Iar, Orkney Islands and Shetland Islands — each with its own distinct character, culture and community.",
            "Explore school performance, compare local house prices and crime data, and discover the communities that best match your family's needs.",
        ],
        "why_families": {
            "eyebrow": "WHY FAMILIES CHOOSE",
            "heading": "Highlands and Islands",
            "intro": "From Inverness to Skye and the Northern Isles, the Highlands and Islands offers a remarkable quality of life — outstanding scenery, close-knit communities and a pace of living that's hard to find anywhere else in Britain.",
            "items": [
                {
                    "icon": "school",
                    "title": "Committed Schools",
                    "body": "From large secondaries in Inverness to small rural primaries serving island communities, schools here are known for their strong community values and dedicated staff.",
                    "photo": "https://images.unsplash.com/photo-1519226135464-df5a9dbcd2a5?auto=format&fit=crop&w=800&q=80",
                    "photo_alt": "Boy holding on a swing outdoors",
                },
                {
                    "icon": "home",
                    "title": "Unique Places to Live",
                    "body": "Whether it's a Highland town, a coastal village or one of Scotland's remote islands, every community here has its own distinct identity.",
                    "photo": "https://images.unsplash.com/photo-1625265328763-06198810074c?auto=format&fit=crop&w=800&q=80",
                    "photo_alt": "Inverness city centre with the River Ness",
                },
                {
                    "icon": "train",
                    "title": "Scenic Connections",
                    "body": "Some of Britain's most scenic rail routes, ferry links to the islands and improving road connections keep communities well connected.",
                    "photo": "https://images.unsplash.com/photo-1733336650115-65565c0adae6?auto=format&fit=crop&w=800&q=80",
                    "photo_alt": "Ferry crossing a Scottish sea loch",
                },
                {
                    "icon": "tree",
                    "title": "Unmatched Outdoors",
                    "body": "Ben Nevis, Skye's Cuillin, Loch Ness and the white-sand beaches of the Outer Hebrides — the natural environment here is simply extraordinary.",
                    "photo": "https://images.unsplash.com/photo-1546706872-9c90b8d0c94f?auto=format&fit=crop&w=800&q=80",
                    "photo_alt": "Isle of Skye dramatic landscape",
                },
                {
                    "icon": "briefcase",
                    "title": "Growing Opportunities",
                    "body": "Tourism, renewables and the food and drink sector are all expanding, providing real career opportunities across the Highlands and Islands.",
                    "photo": "https://images.unsplash.com/photo-1667926650784-226b0c73de79?auto=format&fit=crop&w=800&q=80",
                    "photo_alt": "Wind turbines in a Scottish forest",
                },
                {
                    "icon": "heart",
                    "title": "Close-knit Communities",
                    "body": "Strong community spirit, Gaelic culture, local festivals and a genuine sense of belonging make the Highlands and Islands a special place to raise a family.",
                    "photo": "https://images.unsplash.com/photo-1670375845014-4f523beb786f?auto=format&fit=crop&w=800&q=80",
                    "photo_alt": "Group of people gathered in a field",
                },
            ],
        },
    },
    "aberdeen-north-east": {
        "name": "Aberdeen and North East",
        "tagline": "Dynamic cities and coastal towns with strong communities.",
        "photo": "https://images.unsplash.com/photo-1579723251184-cb96c6bcac33?auto=format&fit=crop&w=1600&q=80",
        "localAuthorities": ["Aberdeen City", "Aberdeenshire", "Moray"],
        "intro": [
            "Aberdeen and the North East is a region of contrasts — from the energy and ambition of Aberdeen City to the quiet fishing villages of Moray and the rolling farmland of Aberdeenshire. The region covers three local authorities, each offering a different pace of life while sharing a strong sense of community and a proud local identity.",
            "Explore school performance, compare local house prices and crime data, and discover the communities that best match your family's needs.",
        ],
        "why_families": {
            "eyebrow": "WHY FAMILIES CHOOSE",
            "heading": "Aberdeen and the North East",
            "intro": "From Aberdeen's vibrant harbour city to the Aberdeenshire countryside and the dramatic Moray coast, the North East of Scotland offers families an exceptional quality of life with strong schools and a resilient local economy.",
            "items": [
                {
                    "icon": "school",
                    "title": "Strong Schools",
                    "body": "A well-regarded collection of primary and secondary schools across Aberdeen City, Aberdeenshire and Moray, with many consistently achieving strong results.",
                    "photo": "https://images.unsplash.com/photo-1636202339022-7d67f7447e3a?auto=format&fit=crop&w=800&q=80",
                    "photo_alt": "Children sitting at desks in a classroom",
                },
                {
                    "icon": "home",
                    "title": "Great Places to Live",
                    "body": "From Aberdeen's granite city centre to Aberdeenshire market towns and Moray's coastal villages, there's a community to suit every family.",
                    "photo": "https://images.unsplash.com/photo-1628946578676-e1ee0a952c35?auto=format&fit=crop&w=800&q=80",
                    "photo_alt": "Aberdeen harbour with colourful buildings",
                },
                {
                    "icon": "train",
                    "title": "Good Connections",
                    "body": "Rail links to Edinburgh and Glasgow, Aberdeen International Airport and well-maintained roads connect the North East to the rest of Scotland and beyond.",
                    "photo": "https://images.unsplash.com/photo-1685702149672-af779c937876?auto=format&fit=crop&w=800&q=80",
                    "photo_alt": "Train at a station platform",
                },
                {
                    "icon": "tree",
                    "title": "Coast and Countryside",
                    "body": "Miles of dramatic coastline, the Cairngorms National Park and the Castle Trail make the North East a brilliant base for outdoor families.",
                    "photo": "https://images.unsplash.com/photo-1610890690772-3f7fed4d7c80?auto=format&fit=crop&w=800&q=80",
                    "photo_alt": "Green Scottish coastline",
                },
                {
                    "icon": "briefcase",
                    "title": "Resilient Economy",
                    "body": "Traditionally strong in energy and agriculture, Aberdeen's economy is increasingly diversified across life sciences, tech and the creative industries.",
                    "photo": "https://images.unsplash.com/photo-1589490047559-a1c13ec25b87?auto=format&fit=crop&w=800&q=80",
                    "photo_alt": "Glencoe bridge and Scottish landscape",
                },
                {
                    "icon": "heart",
                    "title": "Proud Communities",
                    "body": "A strong sense of local identity, warm communities and a rich cultural heritage make Aberdeen and the North East a great place to put down roots.",
                    "photo": "https://images.unsplash.com/photo-1688713658343-68b132822277?auto=format&fit=crop&w=800&q=80",
                    "photo_alt": "Family walking together outdoors",
                },
            ],
        },
    },
    "scotland-south": {
        "name": "Scotland South",
        "tagline": "Coastal living, market towns and access to England.",
        "photo": "https://images.unsplash.com/photo-1729495761596-ace93589a8e7?auto=format&fit=crop&w=1600&q=80",
        "localAuthorities": ["Dumfries and Galloway", "Scottish Borders"],
        "intro": [
            "Scotland South is a largely rural region covering two of Scotland's most scenic council areas — Dumfries and Galloway in the west and the Scottish Borders in the east. The region stretches from the Solway Firth to the Cheviot Hills, taking in market towns, coastal communities and wide open countryside.",
            "Explore school performance, compare local house prices and crime data, and discover the communities that best match your family's needs.",
        ],
        "why_families": {
            "eyebrow": "WHY FAMILIES CHOOSE",
            "heading": "Scotland South",
            "intro": "From the Solway coast to the rolling hills of the Scottish Borders, Scotland South offers families space, affordability and a quieter way of life — without sacrificing community, culture or connections.",
            "items": [
                {
                    "icon": "school",
                    "title": "Community Schools",
                    "body": "Schools here are deeply rooted in their local communities, offering a personal and supportive learning environment in both Dumfries and Galloway and the Scottish Borders.",
                    "photo": "https://images.unsplash.com/photo-1636202339022-7d67f7447e3a?auto=format&fit=crop&w=800&q=80",
                    "photo_alt": "Children sitting at desks in a classroom",
                },
                {
                    "icon": "home",
                    "title": "Affordable Living",
                    "body": "Among the most affordable areas in Scotland, with characterful market towns, coastal villages and rural properties offering exceptional value.",
                    "photo": "https://images.unsplash.com/photo-1779922413860-c7254a46e133?auto=format&fit=crop&w=800&q=80",
                    "photo_alt": "Traditional Scottish stone wall and rural scenery",
                },
                {
                    "icon": "train",
                    "title": "Border Connections",
                    "body": "Good road links to Edinburgh and northern England, with the Borders Railway connecting Tweedbank to Edinburgh Waverley in under an hour.",
                    "photo": "https://images.unsplash.com/photo-1685702149672-af779c937876?auto=format&fit=crop&w=800&q=80",
                    "photo_alt": "Train at a station platform",
                },
                {
                    "icon": "tree",
                    "title": "Outstanding Scenery",
                    "body": "The Southern Uplands, Galloway Forest Park and the dramatic Borders hills offer families some of Scotland's most beautiful and unspoilt landscapes.",
                    "photo": "https://images.unsplash.com/photo-1767370568577-0ebe99e2273d?auto=format&fit=crop&w=800&q=80",
                    "photo_alt": "Rolling hills in southern Scotland",
                },
                {
                    "icon": "briefcase",
                    "title": "Rural Economy",
                    "body": "Agriculture, textiles, tourism and a growing creative sector provide employment across the region, with remote working opening up new opportunities.",
                    "photo": "https://images.unsplash.com/photo-1609674750700-33895b9b7ce1?auto=format&fit=crop&w=800&q=80",
                    "photo_alt": "Green mountains and valley in southern Scotland",
                },
                {
                    "icon": "heart",
                    "title": "Close-knit Communities",
                    "body": "Strong local identity, festivals, walking and cycling events and a genuine community spirit make Scotland South a wonderful place to raise a family.",
                    "photo": "https://images.unsplash.com/photo-1688713658343-68b132822277?auto=format&fit=crop&w=800&q=80",
                    "photo_alt": "Family walking together outdoors",
                },
            ],
        },
    },
}

# Name mappings between datasets
CRIME_LA_MAP = {
    "Na h-Eileanan an Iar": "Na h-Eileanan Siar",
}

HPI_LA_MAP = {
    "Aberdeen City":       "City of Aberdeen",
    "Dundee City":         "City of Dundee",
    "Glasgow City":        "City of Glasgow",
    "Na h-Eileanan an Iar": "Na h-Eileanan Siar",
}

CRIME_YEAR = "2024/2025"

CRIME_CATEGORIES = [
    ("Overall crime",        ["All Crimes"]),
    ("Violent crime",        ["All Group 1: Non-sexual crimes of violence"]),
    ("Housebreaking",        ["Crimes: Group 3: Housebreaking"]),
    ("Car crime",            ["Crimes: Group 3: Theft from a motor vehicle",
                              "Crimes: Group 3: Theft of a motor vehicle"]),
    ("Anti-social behaviour",["All Group 6: Antisocial offences"]),
]

PROPERTY_DATE = "2026-03-01"

PROPERTY_TYPES = [
    ("Detached",      "Detached_Average_Price"),
    ("Semi-detached", "Semi_Detached_Average_Price"),
    ("Terraced",      "Terraced_Average_Price"),
    ("Flat",          "Flat_Average_Price"),
]

RATING_ORDER = ["Excellent", "Very Good", "Good", "Satisfactory", "Weak", "Unsatisfactory"]


# ── Data loaders ──────────────────────────────────────────────────────────────

def load_schools():
    with open(os.path.join(BASE, "data", "schools.json")) as f:
        return json.load(f)


def load_crime():
    """Returns {la_name: {category: count}} for CRIME_YEAR."""
    data = {}
    with open(os.path.join(BASE, "data", "raw", "recorded-crime-scotland.csv")) as f:
        for row in csv.DictReader(f):
            if row["FeatureType"] != "Council Area":
                continue
            if row["DateCode"] != CRIME_YEAR:
                continue
            la = row["FeatureName"]
            cat = row["Crime or Offence"]
            try:
                val = int(row["Value"])
            except (ValueError, TypeError):
                continue
            data.setdefault(la, {})[cat] = val

    # Scotland total
    scot = {}
    with open(os.path.join(BASE, "data", "raw", "recorded-crime-scotland.csv")) as f:
        for row in csv.DictReader(f):
            if row["FeatureName"] != "Scotland":
                continue
            if row["DateCode"] != CRIME_YEAR:
                continue
            try:
                scot[row["Crime or Offence"]] = int(row["Value"])
            except (ValueError, TypeError):
                pass
    return data, scot


def load_hpi():
    """Returns {la_name: {col: value}} for PROPERTY_DATE."""
    data = {}
    scot = {}
    with open(os.path.join(BASE, "data", "raw", "uk-hpi-property-type.csv")) as f:
        for row in csv.DictReader(f):
            if row["Date"] != PROPERTY_DATE:
                continue
            name = row["Region_Name"]
            if name == "Scotland":
                scot = row
            elif row["Area_Code"].startswith("S"):
                data[name] = row
    return data, scot


def load_population():
    """Rough LA populations from schools.json school counts as proxy for weighting."""
    with open(os.path.join(BASE, "data", "schools.json")) as f:
        schools = json.load(f)
    counts = {}
    for s in schools:
        la = s["localAuthority"]
        counts[la] = counts.get(la, 0) + 1
    return counts


# ── Helpers ───────────────────────────────────────────────────────────────────

def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def fmt_price(v):
    try:
        return f"£{int(float(v)):,}"
    except (ValueError, TypeError):
        return "N/A"


def fmt_int(v):
    try:
        return f"{int(v):,}"
    except (ValueError, TypeError):
        return "—"


def pill_class(label):
    slug = label.lower().replace(" ", "-")
    return f"rpill rpill--{slug}"


def rating_sort_key(label):
    try:
        return RATING_ORDER.index(label)
    except ValueError:
        return 99


def region_crime(las, crime_data):
    """Sum crime counts for all LAs in the region."""
    totals = {}
    for la in las:
        crime_la = CRIME_LA_MAP.get(la, la)
        la_data = crime_data.get(crime_la, {})
        for label, cats in CRIME_CATEGORIES:
            for cat in cats:
                totals[label] = totals.get(label, 0) + la_data.get(cat, 0)
    return totals


def region_prices(las, hpi_data):
    """Average prices across LAs in the region (simple mean of available LAs)."""
    result = {}
    for ptype, col in PROPERTY_TYPES:
        vals = []
        for la in las:
            hpi_la = HPI_LA_MAP.get(la, la)
            row = hpi_data.get(hpi_la, {})
            try:
                v = float(row[col])
                if v > 0:
                    vals.append(v)
            except (KeyError, ValueError, TypeError):
                pass
        result[ptype] = int(sum(vals) / len(vals)) if vals else None
    return result


def top_schools(schools, las, sector, n=10):
    subset = [s for s in schools if s["localAuthority"] in las
              and s["sector"] == sector and s["rating"]["hasData"]]
    if sector == "primary":
        subset.sort(key=lambda s: -s["rating"].get("averageScore", 0))
    else:
        subset.sort(key=lambda s: (-s["rating"].get("percent", 0),
                                   rating_sort_key(s["rating"].get("label", ""))))
    return subset[:n]


# ── Why-families icons (Feather-style inline SVG) ────────────────────────────

ICONS = {
    "school": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg>',
    "home": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
    "train": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="3" width="16" height="16" rx="2"/><path d="M4 11h16"/><path d="M12 3v8"/><path d="M8 19l-2 3"/><path d="M18 22l-2-3"/></svg>',
    "tree": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 8C8 10 5.9 16.17 3.82 20.54"/><path d="M9.09 9.91C7 12 3.82 20.54 3.82 20.54"/><path d="M10.9 7.1A9 9 0 0 0 4.28 3a9 9 0 0 0 .72 9"/><path d="M13.5 4A9 9 0 0 1 21 8a9 9 0 0 1-5.27 8.16"/></svg>',
    "briefcase": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>',
    "heart": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>',
}


def why_families_html(data):
    if not data:
        return ""
    cards = ""
    for item in data["items"]:
        icon = ICONS.get(item["icon"], "")
        cards += f"""<div class="why-card">
    <div class="why-card-top">
      <div class="why-icon">{icon}</div>
      <h3>{escape(item['title'])}</h3>
      <p>{escape(item['body'])}</p>
    </div>
    <div class="why-card-photo">
      <img src="{escape(item['photo'])}" alt="{escape(item['photo_alt'])}" loading="lazy">
    </div>
  </div>"""
    return f"""<section class="why-families">
  <div class="why-families-inner">
    <p class="why-eyebrow">{escape(data['eyebrow'])} {escape(data['heading'])}</p>
    <p class="why-intro">{escape(data['intro'])}</p>
    <div class="why-grid">{cards}</div>
  </div>
</section>"""


# ── HTML builders ─────────────────────────────────────────────────────────────

def header_html(region_name):
    return f"""<header id="site-header">
  <div style="display:flex;align-items:center;">
    <a href="/index.html" class="site-logo">
      <img src="/assets/logo.svg" alt="Scotland Schools Map logo">
    </a>
    <a href="/index.html" class="site-title" style="color:inherit;text-decoration:none;">Scotland Schools Map</a>
  </div>
  <nav id="site-menu">
    <a href="/search.html" class="site-menu-item">Find a school</a>
    <a href="/explore.html" class="site-menu-item">Explore areas</a>
  </nav>
</header>"""


def hero_html(region):
    return f"""<section class="area-hero" style="background-image:url('{region['photo']}')">
  <div class="area-hero-inner">
    <h1>{escape(region['name'])}</h1>
    <p>{escape(region['tagline'])}</p>
    <a href="/map.html?region={escape(region['slug'])}" class="area-hero-cta">
      View schools on map &#8594;
    </a>
  </div>
</section>"""


MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}


def schools_table_html(schools_list, sector):
    if not schools_list:
        return "<p style='color:#888;font-size:0.85rem;'>No data available.</p>"
    rows = ""
    for i, s in enumerate(schools_list, 1):
        label = s["rating"].get("label", "")
        pill = f'<span class="{pill_class(label)}">{escape(label)}</span>'
        if sector == "secondary":
            metric = f"{s['rating'].get('percent', '—')}%"
        else:
            score = s["rating"].get("averageScore")
            metric = f"{score:.1f}/6" if score else "—"
        url = "/" + s.get("pageUrl", "#")
        if i in MEDALS:
            rank_cell = f'<td class="rank-num"><span class="medal">{MEDALS[i]}</span></td>'
        else:
            rank_cell = f'<td class="rank-num">{i}</td>'
        rows += f"""<tr>
          {rank_cell}
          <td>
            <a class="school-link" href="{escape(url)}">{escape(s['name'])}</a>
            <div class="school-la">{escape(s['localAuthority'])}</div>
          </td>
          <td>{pill}</td>
          <td>{metric}</td>
        </tr>"""
    metric_head = "Pass rate" if sector == "secondary" else "Score"
    return f"""<table class="schools-table">
  <thead><tr>
    <th style="width:2rem">#</th>
    <th>School</th>
    <th>Rating</th>
    <th>{metric_head}</th>
  </tr></thead>
  <tbody>{rows}</tbody>
</table>"""


def prices_html(prices, scot_row):
    rows = ""
    for ptype, col in PROPERTY_TYPES:
        val = prices.get(ptype)
        scot_val = scot_row.get(col)
        try:
            scot_int = int(float(scot_val))
        except (TypeError, ValueError):
            scot_int = None
        rows += f"""<div class="price-row">
      <span class="price-type">{escape(ptype)}</span>
      <span class="price-val">{fmt_price(val)}</span>
    </div>"""
    scot_overall = fmt_price(scot_row.get("Detached_Average_Price")) if scot_row else "N/A"
    return f"""<div class="price-rows">{rows}</div>
  <p class="price-vs-scot">Scotland average (detached): {scot_overall} &middot; Source: UK HPI, March 2026</p>"""


def crime_html(region_totals, scot_crime):
    rows = ""
    for label, cats in CRIME_CATEGORIES:
        count = region_totals.get(label, 0)
        scot_count = sum(scot_crime.get(c, 0) for c in cats)
        rows += f"""<div class="crime-row">
      <span class="crime-label">{escape(label)}</span>
      <div class="crime-figures">
        <div class="crime-count">{fmt_int(count)}</div>
        <div class="crime-rate">Scotland: {fmt_int(scot_count)}</div>
      </div>
    </div>"""
    return f"""<div class="crime-rows">{rows}</div>
  <p class="crime-source">Recorded Crime in Scotland {CRIME_YEAR}, Scottish Government</p>"""


def la_cards_html(las, school_counts):
    cards = ""
    for la in sorted(las):
        slug = slugify(la)
        count = school_counts.get(la, 0)
        cards += f"""<a class="la-card" href="/areas/la/{slug}.html">
      <span class="la-card-name">{escape(la)}</span>
      <span class="la-card-count">{count} school{"s" if count != 1 else ""}</span>
      <span class="la-card-arrow">Explore &#8594;</span>
    </a>"""
    return f'<div class="la-grid">{cards}</div>'


def build_page(slug, region, schools, crime_data, scot_crime, hpi_data, scot_hpi, school_counts):
    region = {**region, "slug": slug}
    las = region["localAuthorities"]
    las_set = set(las)

    top_primary   = top_schools(schools, las_set, "primary")
    top_secondary = top_schools(schools, las_set, "secondary")
    prices        = region_prices(las, hpi_data)
    crime_totals  = region_crime(las, crime_data)

    intro_paras = "".join(
        f"<p>{escape(p)}</p>" for p in region.get("intro", [])
    )
    intro_section = (
        f'<div class="area-intro"><div class="area-intro-inner">{intro_paras}</div></div>'
        if intro_paras else ""
    )
    why_section = why_families_html(region.get("why_families"))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(region['name'])} | Scotland Schools Map</title>
<meta name="description" content="Explore schools, house prices and local insights for {escape(region['name'])}.">
<link rel="stylesheet" href="/css/site-header.css?v=11">
<link rel="stylesheet" href="/css/site-footer.css?v=1">
<link rel="stylesheet" href="/css/area-page.css?v=1">
</head>
<body>

{header_html(region['name'])}

{hero_html(region)}

{intro_section}

{why_section}

<div class="area-page">

  <p class="area-section-eyebrow">
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg>
    TOP SCHOOLS
  </p>

  <div class="schools-row">
    <section class="content-card">
      <h2>Top 10 Primary Schools</h2>
      {schools_table_html(top_primary, "primary")}
    </section>
    <section class="content-card">
      <h2>Top 10 Secondary Schools</h2>
      {schools_table_html(top_secondary, "secondary")}
    </section>
  </div>

  <div class="data-row">
    <section class="content-card">
      <h2>Property Prices</h2>
      {prices_html(prices, scot_hpi)}
    </section>
    <section class="content-card">
      <h2>Crime Overview</h2>
      {crime_html(crime_totals, scot_crime)}
    </section>
  </div>

  <section class="content-card">
    <h2>Local Authorities</h2>
    {la_cards_html(las, school_counts)}
  </section>

</div>

<footer id="site-footer">
  <p>&copy; 2026 Scotland Schools Map. All rights reserved.</p>
  <nav class="footer-links">
    <a href="#">About</a>
    <a href="#">Privacy</a>
    <a href="#">Contact</a>
    <a href="/data/SOURCES.md">Data sources</a>
  </nav>
</footer>

</body>
</html>"""


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    schools      = load_schools()
    crime_data, scot_crime = load_crime()
    hpi_data, scot_hpi     = load_hpi()

    school_counts = {}
    for s in schools:
        la = s["localAuthority"]
        school_counts[la] = school_counts.get(la, 0) + 1

    out_dir = os.path.join(BASE, "areas")
    os.makedirs(out_dir, exist_ok=True)

    for slug, region in REGIONS.items():
        html = build_page(slug, region, schools, crime_data, scot_crime,
                          hpi_data, scot_hpi, school_counts)
        path = os.path.join(out_dir, f"{slug}.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  Wrote {path}")

    print(f"\nDone — {len(REGIONS)} area pages written to {out_dir}/")


if __name__ == "__main__":
    main()
