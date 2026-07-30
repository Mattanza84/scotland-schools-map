// Search page: name search, postcode search (via postcodes.io), popular schools.

const RATING_COLORS = {
  "Excellent": "#16A34A",
  "Very Good": "#22C55E",
  "Good": "#4ADE80",
  "Satisfactory": "#A3E635",
  "Weak": "#FACC15",
  "Unsatisfactory": "#EA580C",
};

const POPULAR_PRIMARY = [
  "Jordanhill School",
  "Sciennes Primary School",
  "South Morningside Primary School",
  "Bearsden Primary School",
  "Cramond Primary School",
];
const POPULAR_SECONDARY = [
  "Jordanhill School",
  "St Ninian's High School",
  "Mearns Castle High School",
  "Williamwood High School",
  "Bearsden Academy",
];

const POSTCODE_RE = /^[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}$/i;

let allSchools = [];
let lastPostcodeCoords = null;
let lastPostcodeQuery = "";

function haversineKm(lat1, lng1, lat2, lng2) {
  const R = 6371;
  const p1 = lat1 * Math.PI / 180;
  const p2 = lat2 * Math.PI / 180;
  const dp = (lat2 - lat1) * Math.PI / 180;
  const dl = (lng2 - lng1) * Math.PI / 180;
  const a = Math.sin(dp / 2) ** 2 + Math.cos(p1) * Math.cos(p2) * Math.sin(dl / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}

function buildCardHtml(school, distKm) {
  const r = school.rating;
  let badgeHtml;
  if (r.hasData) {
    const color = RATING_COLORS[r.label] || "#9e9e9e";
    badgeHtml = `<span class="school-card-badge" style="background:${color}">${escapeHtml(r.label)}</span>`;
  } else {
    badgeHtml = `<span class="school-card-badge school-card-badge--none">No data</span>`;
  }
  const sectorLabel = school.sector.charAt(0).toUpperCase() + school.sector.slice(1);
  const distLine = distKm != null
    ? `<p class="school-card-distance">${distKm.toFixed(1)} km away</p>`
    : "";
  const arrow = `<span class="school-card-arrow"><svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg></span>`;
  return (
    `<a class="school-card" href="/${escapeHtml(school.pageUrl)}">` +
    `<div>` +
    `<p class="school-card-name">${escapeHtml(school.name)}</p>` +
    `<p class="school-card-la">${escapeHtml(school.localAuthority)}</p>` +
    `<p class="school-card-sector">${sectorLabel}</p>` +
    distLine +
    `</div>` +
    badgeHtml +
    arrow +
    `</a>`
  );
}

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, function (c) {
    return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
  });
}

function showSection(id) {
  document.getElementById("popular-section").hidden = id !== "popular-section";
  document.getElementById("search-results").hidden = id !== "search-results";
  document.getElementById("no-results").hidden = id !== "no-results";
}

function renderCards(container, schools, withDistance) {
  container.innerHTML = schools
    .map(function (item) {
      var s = item.school || item;
      var d = withDistance ? item.dist : null;
      return buildCardHtml(s, d);
    })
    .join("");
}

function renderPopular() {
  var priContainer = document.getElementById("popular-primary");
  var secContainer = document.getElementById("popular-secondary");
  var pri = POPULAR_PRIMARY.map(function (name) {
    return allSchools.find(function (s) {
      return s.name === name && s.sector === "primary";
    });
  }).filter(Boolean);
  var sec = POPULAR_SECONDARY.map(function (name) {
    return allSchools.find(function (s) {
      return s.name === name && s.sector === "secondary";
    });
  }).filter(Boolean);
  renderCards(priContainer, pri, false);
  renderCards(secContainer, sec, false);
}

function doNameSearch(query) {
  var q = query.toLowerCase().trim();
  var results = allSchools.filter(function (s) {
    return s.name.toLowerCase().indexOf(q) !== -1;
  });
  if (results.length === 0) {
    showSection("no-results");
    return;
  }
  results.sort(function (a, b) {
    var aStart = a.name.toLowerCase().indexOf(q) === 0 ? 0 : 1;
    var bStart = b.name.toLowerCase().indexOf(q) === 0 ? 0 : 1;
    if (aStart !== bStart) return aStart - bStart;
    return a.name.localeCompare(b.name);
  });
  document.getElementById("results-count").textContent =
    results.length + " school" + (results.length !== 1 ? "s" : "") + " found";
  document.getElementById("radius-controls").hidden = true;
  renderCards(document.getElementById("results-cards"), results, false);
  showSection("search-results");
}

function doPostcodeSearch(query, radiusKm) {
  var clean = query.replace(/\s+/g, "").toUpperCase();

  function runWithCoords(lat, lng) {
    lastPostcodeCoords = { lat: lat, lng: lng };
    lastPostcodeQuery = query;
    filterByRadius(lat, lng, radiusKm);
  }

  if (lastPostcodeCoords && query.trim().toLowerCase() === lastPostcodeQuery.trim().toLowerCase()) {
    runWithCoords(lastPostcodeCoords.lat, lastPostcodeCoords.lng);
    return;
  }

  fetch("https://api.postcodes.io/postcodes/" + encodeURIComponent(clean))
    .then(function (res) { return res.json(); })
    .then(function (data) {
      if (data.status !== 200 || !data.result) {
        showSection("no-results");
        return;
      }
      runWithCoords(data.result.latitude, data.result.longitude);
    })
    .catch(function () {
      showSection("no-results");
    });
}

function filterByRadius(lat, lng, radiusKm) {
  var results = [];
  allSchools.forEach(function (s) {
    var d = haversineKm(lat, lng, s.lat, s.lng);
    if (d <= radiusKm) {
      results.push({ school: s, dist: d });
    }
  });
  results.sort(function (a, b) { return a.dist - b.dist; });

  if (results.length === 0) {
    showSection("no-results");
    return;
  }

  document.getElementById("results-count").textContent =
    results.length + " school" + (results.length !== 1 ? "s" : "") + " found within " + radiusKm + " km";
  document.getElementById("radius-controls").hidden = false;

  document.querySelectorAll(".radius-btn").forEach(function (btn) {
    btn.classList.toggle("active", parseInt(btn.dataset.km) === radiusKm);
  });

  renderCards(document.getElementById("results-cards"), results, true);
  showSection("search-results");
}

function doSearch() {
  var query = document.getElementById("search-input").value.trim();
  if (!query) {
    showSection("popular-section");
    return;
  }
  if (POSTCODE_RE.test(query)) {
    doPostcodeSearch(query, 1);
  } else {
    doNameSearch(query);
  }
}

function init() {
  fetch("/data/schools.json")
    .then(function (res) { return res.json(); })
    .then(function (schools) {
      allSchools = schools;
      renderPopular();

      document.getElementById("search-btn").addEventListener("click", doSearch);
      document.getElementById("search-input").addEventListener("keydown", function (e) {
        if (e.key === "Enter") doSearch();
      });
      document.getElementById("search-input").addEventListener("input", function () {
        if (!this.value.trim()) showSection("popular-section");
      });

      document.querySelectorAll(".tab-btn").forEach(function (btn) {
        btn.addEventListener("click", function () {
          document.querySelectorAll(".tab-btn").forEach(function (b) { b.classList.remove("active"); });
          btn.classList.add("active");
          var tab = btn.dataset.tab;
          document.getElementById("popular-primary").hidden = tab !== "primary";
          document.getElementById("popular-secondary").hidden = tab !== "secondary";
        });
      });

      document.querySelectorAll(".radius-btn").forEach(function (btn) {
        btn.addEventListener("click", function () {
          if (!lastPostcodeCoords) return;
          var km = parseInt(btn.dataset.km);
          filterByRadius(lastPostcodeCoords.lat, lastPostcodeCoords.lng, km);
        });
      });

      var urlQuery = new URLSearchParams(window.location.search).get("q");
      if (urlQuery) {
        document.getElementById("search-input").value = urlQuery;
        doSearch();
      }
    });
}

init();
