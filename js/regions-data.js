// Shared macro-region definitions, used by both index.html (the picker
// screen) and map.html (to pre-filter local authorities when arriving via
// a region link). Local authority names must match `localAuthority` exactly
// as it appears in data/schools.json.

const REGIONS = {
  "highland-islands": {
    name: "Highland and Islands",
    color: "#c0392b",
    localAuthorities: [
      "Highland",
      "Argyll and Bute",
      "Na h-Eileanan an Iar",
      "Orkney Islands",
      "Shetland Islands",
    ],
  },
  "aberdeen-north-east": {
    name: "Aberdeen and North East",
    color: "#f1c40f",
    localAuthorities: ["Aberdeen City", "Aberdeenshire", "Moray"],
  },
  "tayside-central-fife": {
    name: "Tayside, Central and Fife",
    color: "#27ae60",
    localAuthorities: [
      "Angus",
      "Clackmannanshire",
      "Dundee City",
      "Falkirk",
      "Fife",
      "Perth and Kinross",
      "Stirling",
    ],
  },
  "edinburgh-lothians": {
    name: "Edinburgh and Lothians",
    color: "#e84393",
    localAuthorities: ["City of Edinburgh", "East Lothian", "Midlothian", "West Lothian"],
  },
  "glasgow-strathclyde": {
    name: "Glasgow and Strathclyde",
    color: "#2980b9",
    localAuthorities: [
      "Glasgow City",
      "East Ayrshire",
      "East Dunbartonshire",
      "East Renfrewshire",
      "Inverclyde",
      "North Ayrshire",
      "North Lanarkshire",
      "Renfrewshire",
      "South Ayrshire",
      "South Lanarkshire",
      "West Dunbartonshire",
    ],
  },
  "scotland-south": {
    name: "Scotland South",
    color: "#8e44ad",
    localAuthorities: ["Dumfries and Galloway", "Scottish Borders"],
  },
};
