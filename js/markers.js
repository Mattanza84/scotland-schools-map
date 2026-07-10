// Icon, colour, and popup construction for school markers.

const NO_DATA_COLOR = "#9e9e9e";

// Red -> yellow -> green, matching the rating-panel swatch colours.
const GRADIENT_STOPS = [
  { stop: 0.0, rgb: [215, 48, 39] },   // #d73027
  { stop: 0.5, rgb: [254, 224, 139] }, // #fee08b
  { stop: 1.0, rgb: [26, 152, 80] },   // #1a9850
];

function colorForScore(score, hasData) {
  if (!hasData || score === null || score === undefined) {
    return NO_DATA_COLOR;
  }
  const clamped = Math.max(0, Math.min(1, score));

  let lower = GRADIENT_STOPS[0];
  let upper = GRADIENT_STOPS[GRADIENT_STOPS.length - 1];
  for (let i = 0; i < GRADIENT_STOPS.length - 1; i++) {
    if (clamped >= GRADIENT_STOPS[i].stop && clamped <= GRADIENT_STOPS[i + 1].stop) {
      lower = GRADIENT_STOPS[i];
      upper = GRADIENT_STOPS[i + 1];
      break;
    }
  }

  const range = upper.stop - lower.stop;
  const t = range === 0 ? 0 : (clamped - lower.stop) / range;
  const rgb = lower.rgb.map((channel, i) => Math.round(channel + t * (upper.rgb[i] - channel)));
  return `rgb(${rgb[0]}, ${rgb[1]}, ${rgb[2]})`;
}

function buildIcon(sector, colorHex) {
  const stroke = "#333";
  let svg;
  if (sector === "secondary") {
    svg = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
      <polygon points="12,2 22,20 2,20" fill="${colorHex}" stroke="${stroke}" stroke-width="1.5" stroke-linejoin="round"/>
    </svg>`;
  } else {
    svg = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="9" fill="${colorHex}" stroke="${stroke}" stroke-width="1.5"/>
    </svg>`;
  }

  return L.divIcon({
    html: svg,
    className: "school-marker",
    iconSize: [24, 24],
    iconAnchor: [12, 12],
    popupAnchor: [0, -12],
  });
}

const QI_LABELS = {
  "1.1": "Self-evaluation for self-improvement",
  "1.3": "Leadership of change",
  "2.1": "Curriculum",
  "2.3": "Learning, teaching and assessment",
  "3.1": "Ensuring wellbeing, equality and inclusion",
  "3.2": "Raising attainment and achievement",
  "5.1": "The curriculum",
  "5.3": "Meeting learning needs",
  "5.9": "Improvement through self-evaluation",
};

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[c]));
}

function buildPopupHtml(school) {
  const sectorLabel = school.sector.charAt(0).toUpperCase() + school.sector.slice(1);
  let ratingBlock;

  if (school.rating.hasData && school.rating.metric === "attainment") {
    const colorHex = colorForScore(school.rating.score, true);
    ratingBlock = `
      <div class="popup-rating" style="border-left: 4px solid ${colorHex}">
        <strong>${escapeHtml(school.rating.label)}</strong> &mdash; ${escapeHtml(school.rating.percent)}% of the leaver cohort attained 5+ awards at Higher level or above
        <div class="popup-source">SQA attainment, ${escapeHtml(school.rating.year)} &mdash; Scottish Government (statistics.gov.scot, "Breadth and Depth of Qualifications"). This is a raw attainment figure, not adjusted for pupils' backgrounds &mdash; the official methodology recommends comparing a school to its "virtual comparator" for a fairer read, which this map does not show.</div>
      </div>`;
  } else if (school.rating.hasData) {
    const colorHex = colorForScore(school.rating.score, true);
    const qiItems = Object.entries(school.rating.qiScores)
      .map(([qi, val]) => {
        const label = QI_LABELS[qi] || `Quality indicator ${qi}`;
        return `<li>${escapeHtml(label)} (QI ${escapeHtml(qi)}): ${escapeHtml(val)}/6</li>`;
      })
      .join("");

    ratingBlock = `
      <div class="popup-rating" style="border-left: 4px solid ${colorHex}">
        <strong>${escapeHtml(school.rating.label)}</strong> &mdash; average score ${escapeHtml(school.rating.averageScore)}/6
        <ul class="qi-list">${qiItems}</ul>
        <div class="popup-source">Inspected ${escapeHtml(school.rating.inspectionDate)} &mdash; Education Scotland. Rating is an illustrative average of the quality indicators graded at that inspection, not an official single overall grade.</div>
      </div>`;
  } else {
    ratingBlock = `<div class="popup-rating popup-rating--none">No rating data available for this school.</div>`;
  }

  const profileLink = school.pageUrl
    ? `<a class="popup-profile-link" href="/${escapeHtml(school.pageUrl)}">View full profile &rarr;</a>`
    : "";

  return `
    <div class="school-popup">
      <h3>${escapeHtml(school.name)}</h3>
      <div class="popup-meta">${escapeHtml(sectorLabel)} school &middot; ${escapeHtml(school.localAuthority)}</div>
      <div class="popup-address">${escapeHtml(school.address)}</div>
      <hr>
      ${ratingBlock}
      ${profileLink}
    </div>`;
}
