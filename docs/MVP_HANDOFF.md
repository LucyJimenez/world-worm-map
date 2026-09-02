# MVP Handoff, Roadmap, and Implementation Notes

This document summarizes the current MVP state and the recommended next implementation steps.

## Current MVP State

The current system is ready as a demonstrable MVP. It provides a working end-to-end path from field data collection to spatial visualization:

1. KoboToolbox collects sample metadata.
2. The backend imports and normalizes submissions.
3. PostgreSQL/PostGIS stores sample records and geometry.
4. The API exposes samples, species, affiliations, curation endpoints, and admin ingestion utilities.
5. The frontend displays sampling sites on an interactive global map.

The What3Words integration has been implemented and deployed as an additional optional Kobo field. This preserves KoboToolbox as the data-entry source of truth and avoids introducing a second submission workflow at the MVP stage.

## Scientific Data Model Priorities

WWM should continue to treat sampling records as research objects with provenance. The original Kobo payload is preserved, while normalized fields are extracted for analysis and visualization.

Priority data dimensions:

- Taxonomy: family, genus, species, provisional identification, curator identity.
- Geography: country, latitude, longitude, PostGIS geometry, optional What3Words address.
- Environment: habitat type, soil type, soil pH, sampling depth, climate descriptors.
- Sampling protocol: sample ID, tube ID, sampling date, number of subsamples, collector.
- Provenance: Kobo ID, Kobo UUID, submission timestamp, data source, raw payload.
- Genomics: accession IDs, validation state, resolved URLs.

## Immediate To-Do List

- Add the production Kobo asset UID and token to `wwm/.env` or the deployment secret manager.
- Add a What3Words API key only if validation/enrichment is required.
- Run Kobo ingestion and confirm the new field appears in `/api/samples`.
- Confirm that the map popup shows `///three.word.address` for imported records.
- Decide whether seed demo samples should remain in production or only in staging/demo.

## Recommended Technical Improvements

- Add database migrations with Alembic instead of relying on startup `ALTER TABLE` statements.
- Add automated tests for Kobo normalization, What3Words validation, and API sample serialization.
- Replace development API-key authentication with production-grade authentication.
- Add role-specific frontend views for admin, curator, and public users.
- Add structured environmental tables when the environmental schema stabilizes.
- Add family/genus/species filtering separately instead of relying only on free-text species names.
- Add data export endpoints for CSV, GeoJSON, and Darwin Core-compatible occurrence records.
- Add audit views for curator actions.
- Add error reporting for scheduled Kobo ingestion.
- Add deployment-specific environment configuration for staging and production.

## Recommended Scientific Improvements

- Define controlled vocabularies for habitat type, soil texture, sampling protocol, and life stage.
- Align occurrence metadata with biodiversity standards such as Darwin Core where practical.
- Add quality-control flags for coordinate precision, missing environmental fields, and taxonomic uncertainty.
- Separate observed field metadata from derived/enriched variables such as climate overlays.
- Add citation and dataset versioning for public data releases.
- Define minimal required metadata for a record to become public.

## What3Words Implementation Notes

Current behavior:

- The field is collected through KoboToolbox as `what3words`.
- Accepted user formats include `filled.count.soap`, `///filled.count.soap`, and `filled count soap`.
- The backend normalizes the address to `filled.count.soap`.
- If no What3Words API key is configured, the value is stored with status `unvalidated`.
- If an API key is configured, the value can be validated and enriched.
- GPS coordinates remain the canonical map location when available.

Recommended next step:

Keep What3Words as a supplementary human-readable location reference. Use GPS/PostGIS geometry as the analytical coordinate source unless a sampling protocol explicitly approves W3W-derived coordinates as a fallback.

## Production Readiness Notes

The MVP is appropriate for internal demonstration and controlled pilot testing. Before public release, the project should add migrations, production authentication, automated tests, deployment monitoring, and a clear data governance policy.

For the official handoff, the recommended presentation is:

- Explain the scientific objective and data model.
- Demonstrate the map with seeded examples.
- Demonstrate Kobo ingestion with a test submission.
- Show the What3Words value in the map popup.
- Walk through the roadmap from MVP to scientific beta.
