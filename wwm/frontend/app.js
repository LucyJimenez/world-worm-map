const API_BASE = "http://localhost:8000/api";

const map = L.map("map").setView([20, 0], 2);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: "&copy; OpenStreetMap contributors",
}).addTo(map);

const markerLayer = L.layerGroup().addTo(map);
const speciesFilter = document.getElementById("species-filter");
const statusFilter = document.getElementById("status-filter");
const affiliationFilter = document.getElementById("affiliation-filter");
const refreshBtn = document.getElementById("refresh-btn");
const apiStatus = document.getElementById("apiStatus");
const statusText = apiStatus ? apiStatus.querySelector(".status-text") : null;
const emptyState = document.getElementById("emptyState");
const affiliationNamesBySlug = {};

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

function styleForStatus(status) {
  if (status === "validated") {
    return { radius: 7, color: "#1e8e3e", fillColor: "#1e8e3e", fillOpacity: 0.95, weight: 2 };
  }
  if (status === "rejected") {
    return { radius: 7, color: "#c62828", fillColor: "#c62828", fillOpacity: 0.95, weight: 2 };
  }
  return { radius: 7, color: "#ef6c00", fillColor: "#ef6c00", fillOpacity: 0.9, weight: 2 };
}

async function getJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Request failed: ${url} (${response.status})`);
  }
  return response.json();
}

function buildSampleQuery() {
  const params = new URLSearchParams();
  if (speciesFilter.value) params.set("species", speciesFilter.value);
  if (statusFilter.value) params.set("status", statusFilter.value);
  if (affiliationFilter.value) params.set("affiliation", affiliationFilter.value);
  const query = params.toString();
  return query ? `?${query}` : "";
}

function getLatLon(sample) {
  const lat = Number(sample.lat);
  const lon = Number(sample.lon);
  if (Number.isFinite(lat) && Number.isFinite(lon)) {
    return [lat, lon];
  }
  if (
    sample.geometry &&
    Array.isArray(sample.geometry.coordinates) &&
    sample.geometry.coordinates.length >= 2
  ) {
    return [sample.geometry.coordinates[1], sample.geometry.coordinates[0]];
  }
  return null;
}

function renderMarkers(samples) {
  markerLayer.clearLayers();

  samples.forEach((sample) => {
    const coords = getLatLon(sample);
    if (!coords) {
      return;
    }

    const affiliations = Array.isArray(sample.affiliations)
      ? sample.affiliations
          .map((slug) => affiliationNamesBySlug[slug] || slug)
          .join(", ")
      : "n/a";
    const affiliationOther = sample.affiliation_other ? ` (${sample.affiliation_other})` : "";
    const species = Array.isArray(sample.species) ? sample.species.join(", ") : "n/a";

    const marker = L.circleMarker(coords, styleForStatus(sample.status));
    marker.bindPopup(
      `<strong>sample_id:</strong> ${sample.sample_id || "n/a"}<br>` +
        `<strong>status:</strong> ${sample.status || "n/a"}<br>` +
        `<strong>site_name:</strong> ${sample.site_name || "n/a"}<br>` +
        `<strong>sampling_date:</strong> ${sample.sampling_date || "n/a"}<br>` +
        `<strong>collector_name:</strong> ${sample.collector_name || "n/a"}<br>` +
        `<strong>tube_id:</strong> ${sample.tube_id || "n/a"}<br>` +
        `<strong>affiliations:</strong> ${affiliations}${affiliationOther}<br>` +
        `<strong>species:</strong> ${species}`
    );
    markerLayer.addLayer(marker);
  });
}

async function loadFilters() {
  try {
    const [speciesList, affiliationsList] = await Promise.all([
      getJson(`${API_BASE}/species`),
      getJson(`${API_BASE}/affiliations`),
    ]);
    setApiStatus(true);

    speciesList.forEach((item) => {
      const option = document.createElement("option");
      option.value = item.species_name;
      option.textContent = `${item.species_name} (${item.sample_count})`;
      speciesFilter.appendChild(option);
    });

    affiliationsList.forEach((item) => {
      const option = document.createElement("option");
      option.value = item.slug;
      option.textContent = item.name || item.slug;
      affiliationNamesBySlug[item.slug] = item.name || item.slug;
      affiliationFilter.appendChild(option);
    });
  } catch (error) {
    setApiStatus(false);
    console.warn("Could not load filters from API.", error);
  }
}

async function loadSamples() {
  try {
    const samples = await getJson(`${API_BASE}/samples${buildSampleQuery()}`);
    const list = Array.isArray(samples) ? samples : [];
    setApiStatus(true);
    renderMarkers(list);
    setEmptyState(list.length === 0);
  } catch (error) {
    setApiStatus(false);
    renderMarkers([]);
    setEmptyState(false);
    console.warn("Could not load samples from API.", error);
  }
}

refreshBtn.addEventListener("click", loadSamples);
speciesFilter.addEventListener("change", loadSamples);
statusFilter.addEventListener("change", loadSamples);
affiliationFilter.addEventListener("change", loadSamples);

setApiStatus(false);
setEmptyState(false);
loadFilters();
loadSamples();

setTimeout(() => map.invalidateSize(), 0);
