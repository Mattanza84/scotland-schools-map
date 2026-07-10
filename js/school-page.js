// Initialises the small single-marker map on each school detail page.

function initSchoolMap() {
  const el = document.getElementById("school-map");
  if (!el) return;

  const lat = parseFloat(el.dataset.lat);
  const lng = parseFloat(el.dataset.lng);
  const shape = el.dataset.shape;
  const color = el.dataset.color;
  const name = el.dataset.name;

  const map = L.map(el, {
    zoomControl: true,
    scrollWheelZoom: false,
  }).setView([lat, lng], 14);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map);

  const svg =
    shape === "triangle"
      ? `<svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" viewBox="0 0 24 24">
           <polygon points="12,2 22,20 2,20" fill="${color}" stroke="#333" stroke-width="1.5" stroke-linejoin="round"/>
         </svg>`
      : `<svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" viewBox="0 0 24 24">
           <circle cx="12" cy="12" r="9" fill="${color}" stroke="#333" stroke-width="1.5"/>
         </svg>`;

  const icon = L.divIcon({
    html: svg,
    className: "school-marker",
    iconSize: [26, 26],
    iconAnchor: [13, 13],
  });

  L.marker([lat, lng], { icon }).addTo(map).bindTooltip(name, { permanent: false });
}

initSchoolMap();
