# World Worm Map (WWM)

## Project Attribution

World Worm Map (WWM) is an open-science infrastructure project designed and developed by **Lucy Jimenez**.

The platform was created for and in collaboration with **Worm Lab**:
https://worm-lab.eu/

WWM supports the Worm Lab mission of advancing nematode biodiversity research through reproducible, data-driven, and collaborative genomic workflows.

WWM contains:
- FastAPI backend (`wwm/backend`)
- PostGIS database (via Docker Compose)
- Leaflet frontend (`wwm/frontend`)

## Documentation

- [`docs/SMART_PLAN.md`](docs/SMART_PLAN.md)
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- [`docs/API.md`](docs/API.md)
- [`docs/SCHEMA.md`](docs/SCHEMA.md)
- [`docs/KOBO_SCHEMA.md`](docs/KOBO_SCHEMA.md)
- [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md)
- [`docs/SECURITY.md`](docs/SECURITY.md)
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)
- [`docs/KOBO_FIELD_MAPPING.md`](docs/KOBO_FIELD_MAPPING.md)
- [`docs/README_DOCS.md`](docs/README_DOCS.md)

## Local run (from repo root)

1. Create the runtime env file:
   ```bash
   cp wwm/.env.example wwm/.env
   ```
2. Add your Kobo token in `wwm/.env`:
   - `KOBO_TOKEN=...`
3. Start services:
   ```bash
   docker compose up --build
   ```

Backend will be available at [http://localhost:8000](http://localhost:8000).

## Environment source of truth

Only `wwm/.env` is used for backend runtime secrets/config in local Docker.

Required keys in `wwm/.env`:
- `DATABASE_URL`
- `KOBO_BASE_URL`
- `KOBO_ASSET_UID`
- `KOBO_TOKEN`
- `INGEST_HOUR`
- `CORS_ORIGINS`

## Verify API and sample loading

Check samples:

```bash
curl http://localhost:8000/api/samples
```

If empty, seed demo data:

```bash
docker compose exec backend python -m scripts.dev_seed
curl http://localhost:8000/api/samples
```

## Manual Kobo ingestion trigger

```bash
curl -X POST http://localhost:8000/api/admin/ingest/kobo
```

Expected response:

```json
{"ingested": 0, "duplicates": 0, "errors": 0}
```

## Refresh Kobo data without losing seed examples

Verify Kobo/database sync state:

```bash
curl -H "x-api-key: admin-key" http://localhost:8000/api/admin/verify/kobo-sync
```

Refresh Kobo-derived data only (keeps `data_source='seed'` samples):

```bash
curl -X POST -H "x-api-key: admin-key" http://localhost:8000/api/admin/kobo/refresh
```

## Scheduler

Ingestion runs daily inside the FastAPI process using APScheduler:
- Hour: `INGEST_HOUR` (UTC)
- Minute: `INGEST_MINUTE` (UTC, default `0`)

## Frontend

Serve frontend separately for local dev testing (optional):

```bash
cd wwm/frontend
python -m http.server 8080
```

Then open [http://localhost:8080](http://localhost:8080). Frontend calls `http://localhost:8000/api`.

## Troubleshooting

If backend cannot connect to the database during startup, reset local containers/volumes and rebuild:

```bash
docker compose down -v
docker compose up --build
```

## Credits

Project Lead & Architecture:
Lucy Jimenez

Developed for:
Worm Lab — https://worm-lab.eu/

Technology stack:
FastAPI, PostgreSQL/PostGIS, Leaflet, KoboToolbox
