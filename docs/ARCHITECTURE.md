# Architecture

## Components

- KoboToolbox — submission data source
- FastAPI backend — ingestion, API, lightweight governance endpoints, and static frontend serving for local runs
- PostgreSQL + PostGIS — relational persistence plus point geometry for sample coordinates
- Leaflet frontend — global map, sidebar filters, popups, and summary view
- APScheduler — daily in-process Kobo ingestion job in local/container deployment
- GitHub Pages — static public MVP deployment
- GitHub Actions — scheduled public Kobo export plus Pages deployment

## Data Flow

### Local/API-backed flow

1. Kobo submission is created through the active KoboToolbox form.
2. Manual or scheduled ingestion fetches Kobo EU submissions.
3. Records are normalized and inserted into PostgreSQL/PostGIS.
4. Each newly ingested Kobo sample receives a provisional `unidentified` species entry.
5. Curators can update status, add species entries, and attach genomic accessions through API endpoints.
6. The Leaflet frontend fetches `/api/samples`, `/api/species`, `/api/families`, `/api/affiliations`, and `/api/environment-summary`.
7. The map renders sample markers and filterable environmental/taxonomic metadata.

### Public GitHub Pages flow

1. GitHub Actions runs `scripts/export_kobo_static.py`.
2. The script fetches Kobo EU submissions using repository variables/secrets.
3. The script writes a sanitized `wwm/frontend/demo-samples.json`.
4. Beta reference samples from `wwm/frontend/reference-samples.json` are appended to demonstrate species, family, and status filters.
5. GitHub Pages serves the static frontend and JSON dataset.

## Deployment Model

Local dev:

```bash
docker compose up --build
```

Public beta:

```text
GitHub Actions -> GitHub Pages
https://lucyjimenez.github.io/world-worm-map/
```

Production backend deployment is planned but not implemented in this beta.
