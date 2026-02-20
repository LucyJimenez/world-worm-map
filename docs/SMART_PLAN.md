# World Worm Map (WWM) — SMART Implementation Plan

## Vision
WWM is an open-science global platform enabling submission, visualization,
curation, and enrichment of nematode sampling records with genomic metadata.

## Phase 1 — MVP ingestion + map
Goal: Global map with daily Kobo ingestion and filtering.

Status: COMPLETED
Completion date: 2026-02-20

Deliverables:
- Scheduled ingestion (daily)
- PostGIS persistence
- Leaflet world map
- Species + affiliation filters
- Pending vs validated styling

Success metrics:
- ≥50 samples visible
- ≥5 species options
- ingestion idempotent
- ingestion stable ≥3 days

## Phase 2 — Governance & curation
Goal: role-based collaboration and curation.

Deliverables:
- user roles
- PI validation workflow
- audit trail
- accession validation

## Phase 3 — Scientific beta
Goal: research-grade platform.

Deliverables:
- environmental overlays
- public open API
- dataset citation registry
- advanced filtering

