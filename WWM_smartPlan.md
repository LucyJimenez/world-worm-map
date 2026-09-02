---
title: WWM

---

# World Worm Map (WWM) — SMART Implementation Plan

## North Star (Vision)

**World Worm Map (WWM)** will be an open-science, globally accessible platform where users can submit nematode sampling records, visualize them on a world map, filter by species, and progressively enrich samples with lab/genomics metadata (including accession numbers and links). The platform will also support overlaying environmental layers (soil/climate/elevation) with clearly cited data sources.


## Phase 1  — Public MVP + daily ingestion
**SMART Goal:** deliver a working WWM MVP that can be embedded into **worm-lab.eu**, displays global sampling points ingested from KoboToolbox once per day, and supports species filtering with pending records visible in a lighter style.

### Specific

* FastAPI backend with scheduled ingestion (Option A)
* PostgreSQL + PostGIS persistence
* Automatic provisional species entry (“unidentified”)
* Store affiliations and free-text affiliations
* Default status = pending
* Leaflet world map visualization
* Species filtering + affiliation filtering
* iframe/embed deployment strategy

### Measurable

* ≥ 50 samples visible
* ≥ 5 species filter options
* ingestion runs ≥ 3 consecutive days
* ingestion idempotent (no duplicates)

## Phase 2 — Governance + curation + versioning

**SMART Goal:** implement collaboration governance: user roles, affiliation ownership, PI/delegated approvals, curated species updates, and accession validation with clear “verified vs unverified” display.

### Specific

* Implement user roles:
  * **Contributor**: submit/view
  * **PI/Validator**: approve + edit for affiliated groups
  * **Curator/Admin**: global management
* Approval workflow:
  * `pending` records are visible but clearly labeled
  * PI (or delegated validator) can approve → `validated`
* Versioning/audit trail:
  * track who changed what and when (sample edits, species edits, accession edits)
* Curation UI (web form):
  * add multiple species per sample
  * species dropdown + “Other” free text
  * analysis status fields (e.g., “sequenced”, “assembly available”)
  * accession number input with API-based validation and auto-link generation when valid
  * show clear difference between **verified** (link generated) vs **unverified** (no link + warning)

### Measurable

* ≥ 10 registered users
* ≥ 3 affiliations with a PI/validator assigned
* ≥ 30 samples approved by PI/validator
* ≥ 20 curated species entries added
* ≥ 10 accessions validated (linked) and ≥ 10 flagged unverified (visibly distinct)

### Tasks?

* auth + roles + affiliation membership model
* PI approval interface + pending/validated pipeline
* curation workflow + species “Other” + accession validation
* versioning/audit + stabilization

---

## Phase 3 — Environmental overlays + scientific UX + open API

**SMART Goal:** ship the research-grade beta: environmental overlays (soil/climate/elevation), advanced filtering, public read-only API endpoints for open science, and complete dataset/source documentation.

### Specific

* Add environmental overlay toggles (at least three):

  * soil layer(s)
  * climate layer(s)
  * elevation/topography layer(s)
* Improve UX:

  * combined filters (species × affiliation × status)
  * sample detail panel showing multi-species and genomic links
* Provide public read-only API endpoints:

  * `GET /api/samples` (with filters)
  * `GET /api/species`
  * `GET /api/affiliations`
* Documentation:

  * README includes **data sources and licenses** for each environmental layer
  * API usage examples

### Measurable

* ≥ 3 environmental overlay layers working
* ≥ 500 samples stored (or an agreed realistic target for beta)
* ≥ 100 samples with at least 1 identified species
* ≥ 50 samples with genomic links/accession metadata

### Tasks?

* overlay integration + source/license documentation
* advanced filtering + sample detail panel
* public API endpoints + docs
* beta demo + release freeze

---

# Development mode decision

* Start **local-first** development
* Backend: **FastAPI**
* Ingestion: **Option A (scheduled daily)**
* Later: embed into **worm-lab.eu** (likely via iframe/widget)



---

# 1) Architecture (local-first, cloud-ready)

### High-level components

* **KoboToolbox (source of truth for Stage 1 field submissions)**
* **WWM Backend API (FastAPI)**
  * daily scheduled ingestion job (Option A, 1x/day)
  * REST API for map + filters + curation + approvals
* **Database (PostgreSQL + PostGIS)**
* **WWM Frontend (Leaflet map)**
  * reads from the backend API
  * displays markers with status styling
  * species filter + affiliation filter
* **Admin/Curator UI**
  * lightweight web pages served by backend (Jinja templates) OR separate minimal frontend
  * used for approvals and curation

### Data flow

1. **Daily ingestion job**
* Backend calls KoboToolbox API once per day
* Normalizes fields → inserts into DB
* Creates **provisional species entry** per sample: `unidentified`
* Marks samples as `pending`

2. **Curation & governance**
* PI/Validator approves samples (`pending` → `validated`)
* Curator adds species entries and accession numbers
* Backend validates accession via NCBI and generates links where possible

3. **Map visualization**
* Frontend fetches `/api/samples` with filters
* Markers:
  * `pending` = lighter style
  * `validated` = solid
  * samples with accession links = extra icon/badge

### Deployment-ready packaging

* Local dev: `docker compose up` (FastAPI + Postgres/PostGIS)
* Later: same compose can run on a server; only environment variables change

---

# 2) Minimal DB schema (Postgres + PostGIS)

## Tables

### `users`
* `id` (uuid, pk)
* `email` (text, unique)
* `display_name` (text)
* `role` (text: `contributor|validator|curator|admin`)
* `created_at` (timestamp)

### `affiliations`
* `id` (uuid, pk)
* `slug` (text, unique) — e.g. `worm_lab`
* `name` (text) — e.g. `Worm~Lab`
* `created_at` (timestamp)

### `user_affiliations` (many-to-many)
* `user_id` (uuid, fk users)
* `affiliation_id` (uuid, fk affiliations)
* `is_pi` (bool default false) — PI/lead for that affiliation
* `is_validator` (bool default false) — delegated validator
* composite pk (`user_id`, `affiliation_id`)

### `samples`
* `id` (uuid, pk)
* `sample_id` (text, unique) — from Kobo or generated
* `collector_name` (text)
* `sampling_date` (date)
* `site_name` (text)
* `geom` (geometry(Point, 4326)) — lat/lon
* `country` (text)
* `habitat_type` (text)
* `soil_type` (text)
* `soil_ph` (numeric)
* `depth_cm` (int)
* `num_samples` (int)
* `tube_id` (text)
* `notes` (text)
* `status` (text: `pending|validated|rejected`)
* `created_by_user_id` (uuid, nullable)
* `created_at` (timestamp)
* `updated_at` (timestamp)

### `sample_affiliations` (many-to-many)

* `sample_id` (uuid, fk samples)
* `affiliation_id` (uuid, fk affiliations)
* composite pk (`sample_id`, `affiliation_id`)
* (optional) store free-text `affiliation_other` separately (see below)

### `sample_species`
* `id` (uuid, pk)
* `sample_id` (uuid, fk samples)
* `species_name` (text) — default `unidentified`
* `species_source` (text: `provisional|curated`)
* `created_by_user_id` (uuid, nullable)
* `created_at` (timestamp)

### `genomic_records`
(one per species entry, can expand later)
* `id` (uuid, pk)
* `sample_species_id` (uuid, fk sample_species)
* `data_type` (text: `genome|transcriptome|marker|other`)
* `accession` (text, nullable)
* `accession_validated` (bool default false)
* `resolved_url` (text, nullable)
* `provider` (text: `NCBI|ENA|other`, nullable)
* `created_at` (timestamp)

### `audit_log`
* `id` (uuid, pk)
* `entity_type` (text: `sample|species|genomic`)
* `entity_id` (uuid)
* `action` (text: `create|update|approve|reject`)
* `diff_json` (jsonb)
* `actor_user_id` (uuid)
* `created_at` (timestamp)

**Key rule (your decision):**
* On ingestion, always create `sample_species` with `species_name="unidentified"`.

---

# 3) API contract (endpoints + payloads)

Base path: `/api`

## Public (read-only)

### `GET /api/samples`

Query params:

* `species` (optional, string)
* `status` (optional: `pending|validated`)
* `affiliation` (optional: affiliation slug)
  Returns: list of samples with species summary + coordinates.

Response (example):

```json
[
  {
    "sample_id": "COL-2025-001",
    "status": "pending",
    "site_name": "San Pedro plot",
    "sampling_date": "2025-10-20",
    "lat": 4.711,
    "lon": -74.072,
    "affiliations": ["worm_lab", "sanger_institute"],
    "species": ["unidentified", "Pratylenchus penetrans"],
    "has_genomic_links": true
  }
]
```

### `GET /api/species`

Returns unique species names (for filter dropdown):

```json
["unidentified", "Pratylenchus penetrans", "Meloidogyne incognita"]
```

### `GET /api/affiliations`

Returns:

```json
[
  {"slug":"worm_lab","name":"Worm~Lab"},
  {"slug":"sanger_institute","name":"Sanger Institute"}
]
```

## Authenticated (curation/governance)

### `POST /api/samples/{sample_id}/approve`

Body:

```json
{"status":"validated"}
```

### `POST /api/samples/{sample_id}/species`

Adds species to a sample.
Body:

```json
{"species_name":"Heterodera schachtii","species_source":"curated"}
```

### `POST /api/species/{sample_species_id}/genomics`

Adds/updates genomic record.
Body:

```json
{
  "data_type":"genome",
  "provider":"NCBI",
  "accession":"GCA_000001405.28"
}
```

Server will:

* attempt validation via NCBI
* set `accession_validated`
* set `resolved_url` if valid

## Admin (ingestion)

### `POST /api/admin/ingest/kobo`

Triggers ingestion manually (for testing). No body.
Returns:

```json
{"ingested": 25, "skipped_duplicates": 10}
```

---

# 4) Repo structure (GitHub-ready, Docker-ready)

```
wwm/
├── README.md
├── DEPLOYMENT.md
├── .env.example
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml  (or requirements.txt)
│   ├── app/
│   │   ├── main.py              # FastAPI entrypoint
│   │   ├── config.py            # env settings
│   │   ├── db.py                # DB session + engine
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── crud.py              # DB operations
│   │   ├── api/
│   │   │   ├── routes_public.py
│   │   │   ├── routes_curation.py
│   │   │   ├── routes_admin.py
│   │   ├── services/
│   │   │   ├── kobo_ingest.py    # scheduled ingestion
│   │   │   ├── ncbi_validate.py  # accession validation
│   │   ├── templates/            # (optional) curation UI
│   │   └── static/
│   └── tests/
├── frontend/
│   ├── index.html               # Leaflet map MVP
│   ├── app.js                   # fetch API + render markers + filters
│   └── style.css
└── scripts/
    ├── run_ingest_local.sh
    └── dev_seed.py              # seed affiliations/species
```

**docker-compose** runs:

* `backend` (FastAPI)
* `db` (Postgres/PostGIS)


# Project Progress Dashboard

## Overall progress

```
Phase 1 ████████████░░░░░ 70%
Phase 2 ░░░░░░░░░░░░░░░░░ 0%
Phase 3 ░░░░░░░░░░░░░░░░░ 0%
```

---

## Phase 1 — MVP ingestion + map

### Backend ingestion

* [x] KoboToolbox connection
* [x] Scheduled ingestion
* [x] Duplicate-safe ingestion
* [x] Provisional species creation
* [ ] ingestion monitoring endpoint
* [ ] ingestion logging dashboard

### Database

* [x] Postgres + PostGIS running
* [x] Samples persisted
* [ ] affiliation normalization table linking
* [ ] ingestion health metrics table

### Frontend map

* [x] Leaflet world map
* [x] Sample markers
* [x] Species filter
* [x] Affiliation filter
* [ ] status-based marker styling refinement
* [ ] popup enrichment (multi-species display)

### Deployment readiness

* [x] Docker compose environment
* [x] Local dev running
* [ ] worm-lab.eu embed integration
* [ ] staging deployment

---

## Phase 2 — Governance & curation

* [ ] authentication system
* [ ] roles (contributor / validator / curator / admin)
* [ ] affiliation ownership model
* [ ] approval workflow
* [ ] species curation UI
* [ ] accession validation service
* [ ] audit/versioning system

---

## Phase 3 — Scientific platform beta

* [ ] environmental overlays (soil)
* [ ] environmental overlays (climate)
* [ ] environmental overlays (elevation)
* [ ] advanced filtering
* [ ] public open API documentation
* [ ] dataset source citation registry

---

## Current milestone status

**Milestone:** Live ingestion + map visualization
**Status:** Achieved
**Next milestone:** ingestion stabilization + embed into worm-lab.eu

---


