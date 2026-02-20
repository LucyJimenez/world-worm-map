# Deployment Guide

## Layout

Repo root contains Docker Compose and docs. Application code lives under `wwm/`.

## Local deployment

From repo root:

```bash
cp wwm/.env.example wwm/.env
# fill in KOBO_TOKEN and other overrides
docker compose up --build -d
```

Services:
- Backend: `http://localhost:8000`
- Database: PostGIS `postgis/postgis:15-3.3`

## Environment configuration

Use only `wwm/.env` for backend configuration/secrets.

Important keys:
- `DATABASE_URL=postgresql+psycopg2://wwm:wwm@db:5432/wwm`
- `KOBO_BASE_URL`
- `KOBO_ASSET_UID`
- `KOBO_TOKEN`
- `INGEST_HOUR`
- `INGEST_MINUTE`
- `CORS_ORIGINS`

## Kobo ingestion

Manual trigger:

```bash
curl -X POST http://localhost:8000/api/admin/ingest/kobo
```

Response shape:

```json
{"ingested": 0, "duplicates": 0, "errors": 0}
```

## Scheduler behavior

APScheduler runs inside FastAPI for local dev (no external cron required).
- Daily ingestion at `INGEST_HOUR:INGEST_MINUTE` UTC.
- Startup logs include next scheduled run time.

## Frontend local static run

```bash
cd wwm/frontend
python -m http.server 8080
```

CORS is configured to allow `http://localhost:8080`.

## Validation checks

```bash
curl http://localhost:8000/api/samples
curl http://localhost:8000/api/species
curl http://localhost:8000/api/affiliations
```
