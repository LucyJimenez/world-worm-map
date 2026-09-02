const API_BASE = window.location.protocol === "file:" ? "http://127.0.0.1:8000/api" : "/api";

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

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: "&copy; OpenStreetMap contributors",
}).addTo(map);

function setApiStatus(isOnline) {
  if (!apiStatus) return;
  apiStatus.classList.toggle("online", isOnline);
  apiStatus.classList.toggle("offline", !isOnline);
  if (statusText) {
    statusText.textContent = isOnline ? "API reachable" : "API unreachable";
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

function htmlList(values) {
  return values && values.length ? values.join(", ") : "Not recorded";
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
  const habitat = sample.habitat_other || sample.habitat_type || "Not recorded";
  const soil = sample.soil_type_other || htmlList(sample.soil_types);
  const w3wHref = sample.what3words_map_url || `https://what3words.com/${sample.what3words || ""}`;
  const what3words = sample.what3words
    ? `<a href="${w3wHref}" target="_blank" rel="noreferrer">///${sample.what3words}</a>`
    : "Not entered";
  const w3wMeta = sample.what3words
    ? `${sample.what3words_source || "manual"}, ${sample.what3words_status || "unvalidated"}`
    : "Not recorded";

  return `
    <strong>${sample.sample_id || "n/a"}</strong><br>
    ${sample.site_name || "Unnamed site"} ${sample.country ? `(${sample.country})` : ""}<br>
    <span>Status: ${sample.status || "n/a"}</span><br>
    <span>Species: ${htmlList(sample.species)}</span><br>
    <span>Families: ${htmlList(sample.families)}</span><br>
    <hr>
    <span>What3Words: ${what3words}</span><br>
    <span>W3W status: ${w3wMeta}</span><br>
    <span>Nearest place: ${sample.what3words_nearest_place || "Not recorded"}</span><br>
    <span>Coordinates: ${Number(sample.lat).toFixed(5)}, ${Number(sample.lon).toFixed(5)}</span><br>
    <hr>
    <span>Habitat: ${habitat}</span><br>
    <span>Soil: ${soil}</span><br>
    <span>pH: ${sample.soil_ph ?? "Not recorded"}</span><br>
    <span>Depth: ${sample.depth_cm ?? "Not recorded"} cm</span><br>
    <span>Sub-samples: ${sample.num_samples ?? "Not recorded"}</span>
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

async function loadOptions() {
  const [speciesList, familiesList, affiliationsList] = await Promise.all([
    getJson(`${API_BASE}/species`),
    getJson(`${API_BASE}/families`),
    getJson(`${API_BASE}/affiliations`),
  ]);

  speciesList.forEach((item) => {
    const option = document.createElement("option");
    option.value = item.species_name;
    option.textContent = `${item.species_name} (${item.sample_count})`;
    speciesFilter.appendChild(option);
  });

  familiesList.forEach((family) => {
    const option = document.createElement("option");
    option.value = family;
    option.textContent = family;
    familyFilter.appendChild(option);
  });

  affiliationsList.forEach((item) => {
    const option = document.createElement("option");
    option.value = item.slug;
    option.textContent = item.name || item.slug;
    affiliationNamesBySlug[item.slug] = item.name || item.slug;
    affiliationFilter.appendChild(option);
  });
}

async function loadSamples() {
  const params = paramsFromForm();
  const query = params.toString();
  const suffix = query ? `?${query}` : "";
  const [samples, summary] = await Promise.all([
    getJson(`${API_BASE}/samples${suffix}`),
    getJson(`${API_BASE}/environment-summary${suffix}`),
  ]);

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
