// Wires up the region picker screen: renders Scotland's local authorities
// (real boundary data from js/scotland-geometry.js) as one SVG path per
// authority, coloured by macro-region, then makes each shape
// clickable/keyboard-activatable to navigate to the main map pre-filtered
// to that region. Hovering/focusing any shape highlights every shape
// belonging to the same region, not just the one under the pointer.

const SVG_NS = "http://www.w3.org/2000/svg";
const shapesByRegion = {};

function goToRegion(slug) {
  window.location.href = `map.html?region=${encodeURIComponent(slug)}`;
}

function setRegionHighlighted(slug, on) {
  (shapesByRegion[slug] || []).forEach((el) => el.classList.toggle("hovered", on));
}

function makeActivatable(el, slug, label) {
  const info = REGIONS[slug];
  if (!info) return;

  el.setAttribute("tabindex", "0");
  el.setAttribute("role", "button");
  el.setAttribute("aria-label", label || info.name);
  el.classList.add("region-shape");
  el.dataset.region = slug;

  const title = document.createElementNS(SVG_NS, "title");
  title.textContent = label || info.name;
  el.appendChild(title);

  el.addEventListener("click", () => goToRegion(slug));
  el.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      goToRegion(slug);
    }
  });
  el.addEventListener("mouseenter", () => setRegionHighlighted(slug, true));
  el.addEventListener("mouseleave", () => setRegionHighlighted(slug, false));
  el.addEventListener("focus", () => setRegionHighlighted(slug, true));
  el.addEventListener("blur", () => setRegionHighlighted(slug, false));

  (shapesByRegion[slug] = shapesByRegion[slug] || []).push(el);
}

function buildMap() {
  const svg = document.getElementById("scotland-map");
  svg.setAttribute("viewBox", SCOTLAND_VIEWBOX);

  SCOTLAND_LA_SHAPES.forEach((shape) => {
    const path = document.createElementNS(SVG_NS, "path");
    path.setAttribute("d", shape.d);
    path.style.fill = REGIONS[shape.region] ? REGIONS[shape.region].color : "#ccc";
    makeActivatable(path, shape.region, `${REGIONS[shape.region].name} (${shape.name})`);
    svg.appendChild(path);
  });

  const labelGroup = document.createElementNS(SVG_NS, "g");
  labelGroup.setAttribute("class", "region-labels");
  labelGroup.setAttribute("aria-hidden", "true");
  Object.entries(SCOTLAND_REGION_LABEL_POS).forEach(([slug, pos]) => {
    const info = REGIONS[slug];
    if (!info) return;
    const text = document.createElementNS(SVG_NS, "text");
    text.setAttribute("x", pos.x);
    text.setAttribute("y", pos.y);
    text.textContent = info.name;
    labelGroup.appendChild(text);
  });
  svg.appendChild(labelGroup);
}

// The hamburger menu itself is wired up by js/site-header.js (shared
// across pages).

buildMap();
