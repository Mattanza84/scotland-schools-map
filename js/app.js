// Map initialisation, layer wiring, and filter controls.
//
// Checkbox changes only update the live "Showing X of Y" count (cheap, no
// map mutation) so the panel stays responsive while you're picking filters.
// The map's markers are only added/removed when "Apply filters" is clicked,
// which also avoids touching up to ~2,300 Leaflet markers on every single
// checkbox click.

function getSelectedRegion() {
  const slug = new URLSearchParams(window.location.search).get("region");
  return slug && typeof REGIONS !== "undefined" && REGIONS[slug]
    ? { slug, ...REGIONS[slug] }
    : null;
}

const selectedRegion = getSelectedRegion();
const regionBounds =
  selectedRegion && typeof SCOTLAND_REGION_BOUNDS !== "undefined"
    ? SCOTLAND_REGION_BOUNDS[selectedRegion.slug]
    : null;

const map = L.map("map");
if (regionBounds) {
  map.fitBounds(regionBounds, { padding: [20, 20] });
} else {
  map.setView([55.86, -4.25], 10);
}

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
}).addTo(map);

const activeSectors = new Set(["primary", "secondary"]);
const activeLocalAuthorities = new Set();
const activeRatings = new Set();
let markerRecords = [];

// Best to worst, matching the labels build_schools_json.py assigns to averageScore 6..1.
const RATING_ORDER = ["Excellent", "Very Good", "Good", "Satisfactory", "Weak", "Unsatisfactory"];
const NO_DATA_LABEL = "No inspection data";

function ratingKeyForSchool(school) {
  return school.rating.hasData ? school.rating.label : NO_DATA_LABEL;
}

function scoreForRatingLabel(label) {
  const grade = 6 - RATING_ORDER.indexOf(label);
  return (grade - 1) / (6 - 1);
}

function createMarkerForSchool(school) {
  const colorHex = colorForScore(school.rating.score, school.rating.hasData);
  const icon = buildIcon(school.sector, colorHex);
  const marker = L.marker([school.lat, school.lng], { icon });
  marker.bindPopup(buildPopupHtml(school));
  return marker;
}

function isVisible(school) {
  return (
    activeSectors.has(school.sector) &&
    activeLocalAuthorities.has(school.localAuthority) &&
    activeRatings.has(ratingKeyForSchool(school))
  );
}

function updateCountLine() {
  const visibleCount = markerRecords.filter(({ school }) => isVisible(school)).length;
  document.getElementById("school-count").textContent =
    `Showing ${visibleCount} of ${markerRecords.length} schools`;
}

function showFilterActions() {
  document.getElementById("filter-actions").hidden = false;
}

function hideFilterActions() {
  document.getElementById("filter-actions").hidden = true;
}

// Called by every checkbox's change handler: updates the live count preview
// and reveals the Apply/Reset buttons (hidden again once Apply or Reset
// actually runs).
function onFilterChanged() {
  updateCountLine();
  showFilterActions();
}

function applyMarkerVisibility() {
  markerRecords.forEach(({ school, marker }) => {
    const shouldShow = isVisible(school);
    const onMap = map.hasLayer(marker);
    if (shouldShow && !onMap) {
      marker.addTo(map);
    } else if (!shouldShow && onMap) {
      map.removeLayer(marker);
    }
  });
  updateCountLine();
  hideFilterActions();
}

function buildLocalAuthorityCheckboxes(schools, region) {
  const schoolCountByLA = {};
  schools.forEach((s) => {
    schoolCountByLA[s.localAuthority] = (schoolCountByLA[s.localAuthority] || 0) + 1;
  });

  // With a region selected, list exactly that region's local authorities
  // (even ones with no schools in the dataset yet) so the panel stays
  // relevant to the chosen area instead of showing whatever happens to be
  // loaded. Without a region, fall back to whatever local authorities are
  // actually present in the dataset.
  const localAuthorities = region
    ? [...region.localAuthorities].sort()
    : Array.from(new Set(schools.map((s) => s.localAuthority))).sort();

  const container = document.getElementById("la-checkboxes");

  localAuthorities.forEach((la) => {
    const count = schoolCountByLA[la] || 0;
    const hasData = count > 0;
    const checked = hasData;
    if (checked) activeLocalAuthorities.add(la);

    const label = document.createElement("label");
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = checked;
    checkbox.disabled = !hasData;
    checkbox.dataset.la = la;
    checkbox.addEventListener("change", (e) => {
      if (e.target.checked) {
        activeLocalAuthorities.add(la);
      } else {
        activeLocalAuthorities.delete(la);
      }
      onFilterChanged();
    });
    label.appendChild(checkbox);
    label.appendChild(document.createTextNode(la));
    if (!hasData) {
      const note = document.createElement("span");
      note.className = "no-data-note";
      note.textContent = "(no data yet)";
      label.appendChild(note);
      label.classList.add("la-no-data");
    }
    container.appendChild(label);
  });
}

function buildRatingCheckboxes(schools) {
  const presentLabels = new Set(
    schools.filter((s) => s.rating.hasData).map((s) => s.rating.label)
  );
  const hasUnrated = schools.some((s) => !s.rating.hasData);

  const orderedKeys = RATING_ORDER.filter((label) => presentLabels.has(label));
  if (hasUnrated) orderedKeys.push(NO_DATA_LABEL);

  const container = document.getElementById("rating-checkboxes");

  orderedKeys.forEach((key) => {
    activeRatings.add(key);
    const swatchColor = key === NO_DATA_LABEL ? colorForScore(null, false) : colorForScore(scoreForRatingLabel(key), true);

    const label = document.createElement("label");
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = true;
    checkbox.dataset.rating = key;
    checkbox.addEventListener("change", (e) => {
      if (e.target.checked) {
        activeRatings.add(key);
      } else {
        activeRatings.delete(key);
      }
      onFilterChanged();
    });
    const swatch = document.createElement("span");
    swatch.className = "colour-swatch";
    swatch.style.background = swatchColor;

    label.appendChild(checkbox);
    label.appendChild(swatch);
    label.appendChild(document.createTextNode(key));
    container.appendChild(label);
  });
}

function initAccordion() {
  const items = document.querySelectorAll(".accordion-item");
  items.forEach((item) => {
    const header = item.querySelector(".accordion-header");
    header.addEventListener("click", () => {
      const isOpen = item.classList.contains("open");
      items.forEach((i) => i.classList.remove("open"));
      if (!isOpen) item.classList.add("open");
    });
  });
}

function resetFilters() {
  activeSectors.clear();
  activeSectors.add("primary");
  activeSectors.add("secondary");
  document.getElementById("toggle-primary").checked = true;
  document.getElementById("toggle-secondary").checked = true;

  activeLocalAuthorities.clear();
  document.querySelectorAll("#la-checkboxes input[type=checkbox]").forEach((cb) => {
    if (!cb.disabled) {
      cb.checked = true;
      activeLocalAuthorities.add(cb.dataset.la);
    }
  });

  activeRatings.clear();
  document.querySelectorAll("#rating-checkboxes input[type=checkbox]").forEach((cb) => {
    cb.checked = true;
    activeRatings.add(cb.dataset.rating);
  });

  applyMarkerVisibility();
}

async function init() {
  let schools;
  try {
    schools = await loadSchools();
  } catch (err) {
    document.getElementById("school-count").textContent =
      "Could not load school data. See browser console for details.";
    console.error(err);
    return;
  }

  if (selectedRegion) {
    document.getElementById("page-title").textContent = `${selectedRegion.name} Schools Map`;
    document.getElementById("page-subtitle").textContent =
      `Primary and secondary schools in ${selectedRegion.name}. Colours reflect an illustrative ` +
      "average of published Education Scotland inspection quality indicators — coverage is " +
      "partial and some inspections are old, so always check the date shown in each popup.";
  }
  buildLocalAuthorityCheckboxes(schools, selectedRegion);
  buildRatingCheckboxes(schools);
  initAccordion();

  markerRecords = schools.map((school) => ({
    school,
    marker: createMarkerForSchool(school).addTo(map),
  }));

  applyMarkerVisibility();

  document.getElementById("toggle-primary").addEventListener("change", (e) => {
    if (e.target.checked) {
      activeSectors.add("primary");
    } else {
      activeSectors.delete("primary");
    }
    onFilterChanged();
  });

  document.getElementById("toggle-secondary").addEventListener("change", (e) => {
    if (e.target.checked) {
      activeSectors.add("secondary");
    } else {
      activeSectors.delete("secondary");
    }
    onFilterChanged();
  });

  document.getElementById("apply-filters-btn").addEventListener("click", () => {
    applyMarkerVisibility();
    document.querySelectorAll(".accordion-item").forEach((item) => item.classList.remove("open"));
  });

  document.getElementById("reset-filters-btn").addEventListener("click", resetFilters);
}

init();
