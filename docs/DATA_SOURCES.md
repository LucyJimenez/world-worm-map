# Data Sources

This document lists data sources and external layers used in the current WWM beta.

## Implemented

- KoboToolbox EU: active source for new sampling submissions.
- OpenStreetMap tile layer: basemap used by the Leaflet frontend.
- Beta reference samples: small static fixture in `wwm/frontend/reference-samples.json` used to demonstrate species, family, and status filters.

## Planned / not implemented

- Environmental raster/vector overlays are not implemented in the beta.
- Climate and soil enrichment from external datasets is not implemented in the beta.
- Darwin Core or other biodiversity-standard exports are not implemented in the beta.

Any future environmental layer should document source name, license, citation, URL, spatial/temporal resolution, transformation method, and whether values are observed or derived.
