# Database Schema

## Core tables

- `users`: user identity and role placeholder table.
- `affiliations`: normalized institutional/research group slugs and display names.
- `samples`: core sampling record, location, status, provenance, raw payload, and optional What3Words metadata.
- `sample_affiliations`: many-to-many link between samples and affiliations.
- `sample_species`: provisional or curated species annotations for each sample.
- `genomic_records`: accession records attached to sample-species annotations.
- `audit_log`: audit trail for ingestion and curator/admin actions.

`samples.geom` is a PostGIS `POINT` with SRID 4326 and is generated from longitude/latitude.

There are no Alembic migrations in the beta. Tables are created with SQLAlchemy metadata during FastAPI startup, and compatibility columns/indexes are added in `app/db/init_db.py`.

## What3Words fields on samples

- `what3words`: normalized three-word address, for example `filled.count.soap`.
- `what3words_source`: source of the value, usually `kobo_manual`.
- `what3words_status`: `unvalidated`, `validated`, `validation_failed`, or `demo`.
- `what3words_language`, `what3words_map_url`, `what3words_nearest_place`, `what3words_country`, `what3words_square`, `what3words_updated_at`: optional enrichment fields populated when the What3Words API key is configured.

## Key rule

Each ingested sample automatically receives
a provisional species entry:
species_name = "unidentified"
