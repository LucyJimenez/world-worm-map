# Installation Guide

This document is intended for the technical person who will install, run, or continue implementation of World Worm Map.

## Requirements

- Git
- Docker Desktop or Docker Engine with Docker Compose
- Access to the public GitHub repository
- KoboToolbox asset UID and API token
- Optional: What3Words API key for validation/enrichment

## Clone the Repository

```bash
git clone https://github.com/LucyJimenez/world-worm-map.git
cd world-worm-map
```

## Configure Environment Variables

Create the runtime environment file:

```bash
cp wwm/.env.example wwm/.env
```

Edit `wwm/.env` and provide at least:

```bash
KOBO_BASE_URL=https://eu.kobotoolbox.org
KOBO_ASSET_UID=<kobo_asset_uid>
KOBO_TOKEN=<kobo_api_token>
```

Optional What3Words validation:

```bash
WHAT3WORDS_API_KEY=<what3words_api_key>
WHAT3WORDS_LANGUAGE=en
```

Do not commit `wwm/.env`. It contains secrets and is ignored by Git.

## Start the MVP

From the repository root:

```bash
docker compose up --build
```

The backend and frontend are served at:

```text
http://localhost:8000
```

The API base path is:

```text
http://localhost:8000/api
```

## Load Local Seed Data

If the local database is empty, load seed records:

```bash
docker compose exec backend python -m scripts.dev_seed
```

Then open:

```text
http://localhost:8000
```

The seeded records include beta examples for species, family, and status filters, plus example What3Words values for backend validation and ingestion testing. What3Words values are treated as internal metadata and are not shown in the public map popup.

## Import KoboToolbox Submissions

New samples should be entered in KoboToolbox:

```text
https://ee-eu.kobotoolbox.org/x/HcREEDBq
```

This is the active field-user submission link. The administrative KoboToolbox project remains associated with asset UID `a8Rvu5KasYeAfsa2GfFppG`.

Trigger manual ingestion:

```bash
curl -X POST http://localhost:8000/api/admin/ingest/kobo
```

For configured admin protection:

```bash
curl -X POST -H "x-api-key: admin-key" http://localhost:8000/api/admin/ingest/kobo
```

Verify sync state:

```bash
curl -H "x-api-key: admin-key" http://localhost:8000/api/admin/verify/kobo-sync
```

Refresh Kobo-derived records while keeping seed examples:

```bash
curl -X POST -H "x-api-key: admin-key" http://localhost:8000/api/admin/kobo/refresh
```

## Refresh GitHub Pages from KoboToolbox

The public GitHub Pages map is static:

```text
https://lucyjimenez.github.io/world-worm-map/
```

During deployment, the GitHub Actions workflow exports a sanitized public dataset from KoboToolbox to `wwm/frontend/demo-samples.json` and appends the beta reference records from `wwm/frontend/reference-samples.json`. The public dataset includes only coordinates, country, sampling site name, affiliation, date, habitat, soil, pH, depth, taxonomy, and beta curation status where available. It excludes What3Words, collector names, notes, raw Kobo payloads, original sample IDs, and internal Kobo identifiers.

Configure this repository secret in GitHub:

```text
KOBO_TOKEN=<kobotoolbox_api_token>
```

Optional repository variables:

```text
KOBO_BASE_URL=https://eu.kobotoolbox.org
KOBO_ASSET_UID=a8Rvu5KasYeAfsa2GfFppG
```

The workflow runs once per hour and can also be started manually from GitHub Actions.

## Validate What3Words Values

When `WHAT3WORDS_API_KEY` is configured:

```bash
curl -X POST -H "x-api-key: admin-key" http://localhost:8000/api/admin/what3words/validate
```

Expected response:

```json
{
  "checked": 0,
  "validated": 0,
  "failed": 0
}
```

## Useful API Checks

Health check:

```bash
curl http://localhost:8000/api/health
```

List samples:

```bash
curl http://localhost:8000/api/samples
```

List species:

```bash
curl http://localhost:8000/api/species
```

List affiliations:

```bash
curl http://localhost:8000/api/affiliations
```

## Stop Services

```bash
docker compose down
```

To remove the local database volume during development:

```bash
docker compose down -v
```

Use volume removal carefully because it deletes local PostgreSQL data.

## Troubleshooting

If the backend cannot connect to the database, rebuild cleanly:

```bash
docker compose down
docker compose up --build
```

If the API is reachable but no samples appear, load seed data or verify Kobo credentials.

If What3Words values appear as `unvalidated`, that is expected when `WHAT3WORDS_API_KEY` is not configured. The field is still stored as internal sampling metadata and is not shown in the public map popup.
