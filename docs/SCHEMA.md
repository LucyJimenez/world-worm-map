# Database Schema

## Core tables

users
affiliations
samples
sample_affiliations
sample_species
genomic_records
audit_log

## What3Words fields on samples

- `what3words`: normalized three-word address, for example `filled.count.soap`.
- `what3words_source`: source of the value, usually `kobo_manual`.
- `what3words_status`: `unvalidated`, `validated`, `validation_failed`, or `demo`.
- `what3words_language`, `what3words_map_url`, `what3words_nearest_place`, `what3words_country`, `what3words_square`, `what3words_updated_at`: optional enrichment fields populated when the What3Words API key is configured.

## Key rule

Each ingested sample automatically receives
a provisional species entry:
species_name = "unidentified"
