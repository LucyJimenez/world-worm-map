# API Contract

Base path: `/api`

## Public

### `GET /api/health`

Returns backend/database/scheduler status.

### `GET /api/samples`

Returns mappable sample records. Supported query parameters:

- `species`
- `family`
- `status`
- `affiliation`
- `country`
- `habitat`
- `soil_type`
- `ph_min`
- `ph_max`

The local API response includes internal-development fields such as `data_source`, `collector_name`, and `has_genomic_links`. The GitHub Pages public dataset is generated separately by `scripts/export_kobo_static.py` and intentionally excludes collector names, raw Kobo payloads, original Kobo IDs, notes, and What3Words values.

### `GET /api/species`

Returns species names and sample counts from `sample_species`.

### `GET /api/families`

Returns family names extracted from `samples.raw_payload.taxonomic_entries`.

### `GET /api/affiliations`

Returns affiliation slugs and display names.

### `GET /api/environment-summary`

Returns count, pH range, and habitat list for the current filter set. It accepts the same filter query parameters as `/api/samples`.

## Admin

### `POST /api/admin/ingest/kobo`

Fetches KoboToolbox submissions and inserts new samples. In `development`, the endpoint can run without an admin key unless an invalid key is supplied. In non-development environments it requires the admin API key.

### `GET /api/admin/kobo/fields`

Admin-only debugging endpoint that returns latest Kobo field keys and selected normalized values.

### `GET /api/admin/verify/kobo-sync`

Admin-only endpoint that compares Kobo sample IDs with records currently stored as `data_source = "kobo"`.

### `POST /api/admin/kobo/refresh`

Admin-only endpoint that deletes existing Kobo-derived records and reingests current Kobo submissions while preserving seed/reference records.

### `POST /api/admin/what3words/validate`

Admin-only endpoint that validates/enriches stored What3Words values when `WHAT3WORDS_API_KEY` is configured.

## Governance

### `POST /api/samples/{sample_id}/approve`

Curator-only endpoint. Body:

```json
{"status": "validated"}
```

Allowed status values are `validated` and `rejected`.

### `POST /api/samples/{sample_id}/species`

Curator-only endpoint. Adds a curated species entry to a sample.

```json
{"species_name": "Caenorhabditis elegans"}
```

### `POST /api/species/{sample_species_id}/genomics`

Curator-only endpoint. Adds a genomic accession record to a species entry.

```json
{"accession": "ACCESSION_ID"}
```
