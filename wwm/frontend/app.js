const API_BASE = window.location.protocol === "file:" ? "http://127.0.0.1:8000/api" : "/api";
const DEMO_DATA_URL = "demo-samples.json";

const map = L.map("map", { worldCopyJump: true }).setView([18, 0], 2);
const markerLayer = L.layerGroup().addTo(map);
const filters = document.getElementById("filters");
const speciesFilter = document.getElementById("species-filter");
const familyFilter = document.getElementById("family-filter");
const affiliationFilter = document.getElementById("affiliation-filter");
const resetBtn = document.getElementById("reset-btn");
const apiStatus = document.getElementById("apiStatus");
const statusText = apiStatus ? apiStatus.querySelector(".status-text") : null;
const emptyState = document.getElementById("emptyState");
const sampleCount = document.getElementById("sample-count");
const phRange = document.getElementById("ph-range");
const habitats = document.getElementById("habitats");
const affiliationNamesBySlug = {};
let demoSamples = null;
let useDemoData = false;

const DISPLAY_LABELS = {
  crc1211: "CRC1211",
  worm_lab: "Worm Lab",
  sanger_institute: "Sanger Institute",
  urban: "Urban / built environment",
  desert: "Desert / arid",
  freshwater_margin: "Freshwater margin (river/lake)",
  tundra: "Tundra / alpine",
};

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: "&copy; OpenStreetMap contributors",
}).addTo(map);

function setApiStatus(isOnline, label) {
  if (!apiStatus) return;
  apiStatus.classList.toggle("online", isOnline);
  apiStatus.classList.toggle("offline", !isOnline);
  if (statusText) {
    statusText.textContent = label || (isOnline ? "API reachable" : "API unreachable");
  }
}

function setEmptyState(show) {
  if (!emptyState) return;
  emptyState.classList.toggle("hidden", !show);
}

function statusColor(status) {
  if (status === "validated") return "#197278";
  if (status === "rejected") return "#9d0208";
  return "#9a6a00";
}

async function getJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Request failed: ${url} (${response.status})`);
  }
  return response.json();
}

async function getDemoSamples() {
  if (!demoSamples) {
    demoSamples = await getJson(DEMO_DATA_URL);
  }
  return demoSamples;
}

function htmlList(values) {
  return values && values.length ? values.join(", ") : "Not recorded";
}

function niceLabel(value) {
  if (DISPLAY_LABELS[value]) return DISPLAY_LABELS[value];
  return String(value || "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function paramsFromForm() {
  const params = new URLSearchParams();
  new FormData(filters).forEach((value, key) => {
    const cleaned = String(value).trim();
    if (cleaned) params.set(key, cleaned);
  });
  return params;
}

function popupHtml(sample) {
  const habitat = sample.habitat_other || sample.habitat_label || niceLabel(sample.habitat_type) || "Not recorded";
  const soil = sample.soil_type_other || htmlList(sample.soil_labels || sample.soil_types);
  const affiliation = htmlList((sample.affiliations || []).map(niceLabel));
  const statusLine = sample.status ? `<span>Status: ${sample.status}</span><br>` : "";
  const subsamplesLine =
    sample.num_samples !== undefined && sample.num_samples !== null
      ? `<br><span>Sub-samples: ${sample.num_samples}</span>`
      : "";

  return `
    <strong>${sample.sample_id || "n/a"}</strong><br>
    ${sample.site_name || "Unnamed site"} ${sample.country ? `(${sample.country})` : ""}<br>
    ${statusLine}
    <span>Affiliation: ${affiliation}</span><br>
    <span>Species: ${htmlList(sample.species)}</span><br>
    <span>Families: ${htmlList(sample.families)}</span><br>
    <hr>
    <span>Coordinates: ${Number(sample.lat).toFixed(5)}, ${Number(sample.lon).toFixed(5)}</span><br>
    <span>Habitat: ${habitat}</span><br>
    <span>Soil: ${soil}</span><br>
    <span>pH: ${sample.soil_ph ?? "Not recorded"}</span><br>
    <span>Depth: ${sample.depth_cm ?? "Not recorded"} cm</span>${subsamplesLine}
  `;
}

function renderMarkers(samples) {
  markerLayer.clearLayers();
  const bounds = [];

  samples.forEach((sample) => {
    const lat = Number(sample.lat);
    const lon = Number(sample.lon);
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) return;

    const marker = L.circleMarker([lat, lon], {
      radius: sample.status === "validated" ? 7 : 6,
      color: statusColor(sample.status),
      fillColor: statusColor(sample.status),
      fillOpacity: sample.status === "pending" ? 0.45 : 0.78,
      weight: 2,
    });
    marker.bindPopup(popupHtml(sample));
    marker.addTo(markerLayer);
    bounds.push([lat, lon]);
  });

  if (bounds.length) {
    map.fitBounds(bounds, { maxZoom: 8, padding: [24, 24] });
  }
}

function updateSummary(summary) {
  sampleCount.textContent = summary.sample_count ?? 0;
  phRange.textContent = summary.ph_min === null ? "-" : `${summary.ph_min} - ${summary.ph_max}`;
  habitats.textContent = summary.habitats && summary.habitats.length ? summary.habitats.join(", ") : "-";
}

function optionFor(value, label) {
  const option = document.createElement("option");
  option.value = value;
  option.textContent = label;
  return option;
}

function deriveDemoOptions(samples) {
  const speciesCounts = new Map();
  const families = new Set();
  const affiliations = new Set();

  samples.forEach((sample) => {
    (sample.species || []).forEach((name) => {
      speciesCounts.set(name, (speciesCounts.get(name) || 0) + 1);
    });
    (sample.families || []).forEach((family) => families.add(family));
    (sample.affiliations || []).forEach((affiliation) => affiliations.add(affiliation));
  });

  return {
    speciesList: Array.from(speciesCounts.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([species_name, sample_count]) => ({ species_name, sample_count })),
    familiesList: Array.from(families).sort(),
    affiliationsList: Array.from(affiliations)
      .sort()
      .map((slug) => ({ slug, name: niceLabel(slug) })),
  };
}

function addOptions({ speciesList, familiesList, affiliationsList }) {
  speciesList.forEach((item) => {
    speciesFilter.appendChild(optionFor(item.species_name, `${item.species_name} (${item.sample_count})`));
  });

  familiesList.forEach((family) => {
    familyFilter.appendChild(optionFor(family, family));
  });

  affiliationsList.forEach((item) => {
    affiliationNamesBySlug[item.slug] = item.name || item.slug;
    affiliationFilter.appendChild(optionFor(item.slug, item.name || item.slug));
  });
}

async function loadOptions() {
  try {
    const [speciesList, familiesList, affiliationsList] = await Promise.all([
      getJson(`${API_BASE}/species`),
      getJson(`${API_BASE}/families`),
      getJson(`${API_BASE}/affiliations`),
    ]);
    addOptions({ speciesList, familiesList, affiliationsList });
  } catch (error) {
    useDemoData = true;
    const samples = await getDemoSamples();
    addOptions(deriveDemoOptions(samples));
    setApiStatus(true, "Demo dataset");
    console.warn("Using static demo data.", error);
  }
}

function matchesFilter(sample, key, value) {
  if (!value) return true;
  if (key === "species") return (sample.species || []).includes(value);
  if (key === "family") return (sample.families || []).includes(value);
  if (key === "status") return sample.status === value;
  if (key === "affiliation") return (sample.affiliations || []).includes(value);
  if (key === "country") return String(sample.country || "").toLowerCase() === value.toLowerCase();
  if (key === "habitat") return sample.habitat_type === value;
  if (key === "soil_type") return (sample.soil_types || []).includes(value);
  if (key === "ph_min") return Number(sample.soil_ph) >= Number(value);
  if (key === "ph_max") return Number(sample.soil_ph) <= Number(value);
  return true;
}

function filterDemoSamples(samples) {
  const entries = Array.from(new FormData(filters).entries());
  return samples.filter((sample) => entries.every(([key, value]) => matchesFilter(sample, key, String(value).trim())));
}

function summarizeSamples(samples) {
  const phValues = samples.map((sample) => Number(sample.soil_ph)).filter(Number.isFinite);
  const habitatValues = Array.from(
    new Set(samples.map((sample) => sample.habitat_label || niceLabel(sample.habitat_type)).filter(Boolean))
  ).sort();
  return {
    sample_count: samples.length,
    ph_min: phValues.length ? Math.min(...phValues) : null,
    ph_max: phValues.length ? Math.max(...phValues) : null,
    habitats: habitatValues,
  };
}

async function loadDemoSamples() {
  const samples = filterDemoSamples(await getDemoSamples());
  setApiStatus(true, "Demo dataset");
  renderMarkers(samples);
  updateSummary(summarizeSamples(samples));
  setEmptyState(samples.length === 0);
}

async function loadSamples() {
  if (useDemoData) {
    await loadDemoSamples();
    return;
  }

  const params = paramsFromForm();
  const query = params.toString();
  const suffix = query ? `?${query}` : "";
  let samples;
  let summary;

  try {
    [samples, summary] = await Promise.all([
      getJson(`${API_BASE}/samples${suffix}`),
      getJson(`${API_BASE}/environment-summary${suffix}`),
    ]);
  } catch (error) {
    useDemoData = true;
    console.warn("Could not load samples from API; using static demo data.", error);
    await loadDemoSamples();
    return;
  }

  const list = Array.isArray(samples) ? samples : [];
  setApiStatus(true);
  renderMarkers(list);
  updateSummary(summary);
  setEmptyState(list.length === 0);
}

filters.addEventListener("submit", (event) => {
  event.preventDefault();
  loadSamples().catch((error) => {
    setApiStatus(false);
    setEmptyState(false);
    console.warn("Could not load samples from API.", error);
  });
});

resetBtn.addEventListener("click", () => {
  filters.reset();
  loadSamples().catch((error) => {
    setApiStatus(false);
    console.warn("Could not load samples from API.", error);
  });
});

setApiStatus(false);
setEmptyState(false);
loadOptions()
  .then(loadSamples)
  .catch((error) => {
    setApiStatus(false);
    console.warn("Could not initialize WWM map.", error);
  });

setTimeout(() => map.invalidateSize(), 0);
