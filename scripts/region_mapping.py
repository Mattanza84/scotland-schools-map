"""
Shared macro-region definitions for the Python build scripts (mirrors
js/regions-data.js). Local authority names here match the canonical spelling
used throughout the app (data/schools.json's `localAuthority` field), which
is also what js/regions-data.js uses.

Used by:
  - build_regions_geometry.py (via LA_NAME_ALIASES, since ONS spells the
    Outer Hebrides council differently)
  - build_school_pages.py (region name + slug for breadcrumbs and the
    "view on interactive map" link)
"""

REGION_NAMES = {
    "highland-islands": "Highland and Islands",
    "aberdeen-north-east": "Aberdeen and North East",
    "tayside-central-fife": "Tayside, Central and Fife",
    "edinburgh-lothians": "Edinburgh and Lothians",
    "glasgow-strathclyde": "Glasgow and Strathclyde",
    "scotland-south": "Scotland South",
}

LA_TO_REGION = {
    "Highland": "highland-islands",
    "Argyll and Bute": "highland-islands",
    "Na h-Eileanan an Iar": "highland-islands",
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

# ONS LAD23NM -> canonical name used above. ONS spells the Outer Hebrides
# council "Na h-Eileanan Siar"; everywhere else in this project (schools
# dataset, js/regions-data.js) uses "Na h-Eileanan an Iar" for the same area.
LA_NAME_ALIASES = {
    "Na h-Eileanan Siar": "Na h-Eileanan an Iar",
}


def region_slug_for_la(la_name):
    """la_name in canonical spelling (as in data/schools.json)."""
    return LA_TO_REGION.get(la_name)
