# WWM implementation plan - 2026-05-27

## Goal

Build the first usable WWM app where a user can search by nematode species or family and see:

- where those nematodes have been sampled;
- which environmental, geographic, habitat and soil conditions are associated with those locations;
- which records are provisional, curated or validated.

The design follows the Edaphobase lesson: WWM should model observations and taxa separately from physical samples, and every occurrence should remain linked to site, method, source and environmental metadata.

## Current form mapping

Current Kobo XML: `kobotoolbox__form_27052026.xml`.

Primary fields available now:

- collector and source: `collector_name`, `affiliation`, `affiliation_other`
- sample identity: `sample_id`, `instance_uuid`
- date and location: `sampling_date`, `country`, `gps_coordinates`, `site_name`
- habitat and soil: `habitat_type_001`, `If_Other_please_type_the_habitat_type`, `soil_type_001_001`, `If_Other_please_type_the_soi`, `soil_ph`
- future enrichment placeholder: `climate_info`
- sampling method details: `depth_cm`, `num_samples`, `photo_sample`, `notes`

## Phase 0 - Local scientific MVP

Purpose: replace the demo map with a real local app that can ingest Kobo submissions and support taxon/environment filtering.

Implementation choices:

- Keep Flask for now because the existing app is Flask and this avoids a framework migration before the data model is stable.
- Use SQLite locally instead of JSON files. This is not the final warehouse database, but it gives idempotent ingestion, query filters and a cleaner migration path to PostgreSQL/PostGIS.
- Normalize Kobo payloads into stable API fields while preserving the raw payload for audit/debugging.
- Create provisional `unidentified` taxon records on ingestion.
- Let curation add species and family records per sample.

Deliverables:

- `POST /webhook`: accepts Kobo JSON, parses nested or flat payloads, upserts by `sample_id`.
- `GET /api/samples`: filters by species, family, status, affiliation, country, habitat, soil type and pH range.
- `GET /api/species` and `GET /api/families`: distinct curated/provisional taxon filters.
- `GET /api/environment-summary`: quick ranges and counts for the active query.
- Leaflet frontend reads `/api/samples` instead of hardcoded demo data.
- Curation form supports species, family, identification method and genomic accession metadata.

## Phase 1 - Production data foundation

After the local MVP works:

- migrate SQLite schema to PostgreSQL + PostGIS;
- split `samples`, `sites`, `sampling_events`, `occurrences`, `taxa`, `environmental_measurements`, `genomic_records`;
- add migrations and tests;
- add Kobo scheduled ingestion and ingestion health logs;
- add authentication only after the data model and curation workflow are stable.

## Phase 2 - Environmental enrichment

Add an enrichment job that uses coordinates to populate derived environmental values with source metadata:

- soil: SoilGrids / ISRIC;
- climate: WorldClim or CHELSA;
- elevation/topography: Copernicus DEM or SRTM;
- land cover: ESA WorldCover or equivalent.

Every derived value should store source, variable, resolution, value, unit and extraction date.

## Phase 3 - Research UX

Build the species/family view:

- map of occurrences;
- environmental distributions: pH, elevation, precipitation, temperature, soil texture;
- downloadable filtered table;
- source and license/citation panel;
- warnings for provisional or environmentally incomplete records.

