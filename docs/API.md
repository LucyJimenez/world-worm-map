# API Contract

Base path: /api

## Public

GET /api/samples
GET /api/species
GET /api/affiliations

## Admin

POST /api/admin/ingest/kobo

## Governance

POST /api/samples/{sample_id}/approve
POST /api/samples/{sample_id}/species
POST /api/species/{sample_species_id}/genomics

