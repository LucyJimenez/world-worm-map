# Architecture

## Components

- KoboToolbox — submission data source
- FastAPI backend — ingestion, API, governance
- PostgreSQL + PostGIS — persistence
- Frontend Leaflet client — visualization
- Scheduler — daily ingestion job

## Data Flow

1. Kobo submission created
2. Scheduled ingestion fetches submissions
3. Records normalized and stored
4. Default species entry created ("unidentified")
5. Frontend fetches API → renders markers
6. Curators update species / genomic records

## Deployment Model

Local dev:
docker compose up

Production:
same containers deployed to server or cloud infrastructure

