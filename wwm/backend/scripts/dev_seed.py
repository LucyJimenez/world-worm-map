"""Seed demo data for local development."""

from datetime import date, datetime

from sqlalchemy import func, select

from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.models import Affiliation, Sample, SampleAffiliation, SampleSpecies


def upsert_affiliation(name: str, display_name: str, db):
    item = db.execute(select(Affiliation).where(Affiliation.name == name)).scalar_one_or_none()
    if item:
        return item
    item = Affiliation(name=name, display_name=display_name)
    db.add(item)
    db.flush()
    return item


def create_sample_if_missing(
    db,
    sample_id: str,
    lat: float,
    lon: float,
    site_name: str,
    sampling_date: date,
    status: str,
    affiliations: list[str],
    species_names: list[str],
):
    sample = db.execute(select(Sample).where(Sample.external_sample_id == sample_id)).scalar_one_or_none()
    if sample:
        return

    sample = Sample(
        external_sample_id=sample_id,
        submitted_by="demo@example.org",
        site_name=site_name,
        sampling_date=sampling_date,
        status=status,
        submitted_at=datetime.utcnow(),
        notes="Seeded sample",
        latitude=lat,
        longitude=lon,
        geom=func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326),
    )
    db.add(sample)
    db.flush()

    for affiliation_name in affiliations:
        affiliation = db.execute(select(Affiliation).where(Affiliation.name == affiliation_name)).scalar_one()
        db.add(SampleAffiliation(sample_id=sample.id, affiliation_id=affiliation.id))

    for idx, species_name in enumerate(species_names):
        db.add(
            SampleSpecies(
                sample_id=sample.id,
                species_name=species_name,
                is_provisional=species_name == "unidentified",
                curated_by=None if species_name == "unidentified" else "curator",
                created_at=datetime.utcnow(),
            )
        )


def main():
    init_db()
    db = SessionLocal()
    try:
        upsert_affiliation("worm_lab", "Worm Lab", db)
        upsert_affiliation("sanger_institute", "Sanger Institute", db)

        create_sample_if_missing(
            db,
            sample_id="SEED-AFRICA-001",
            lat=-1.2921,
            lon=36.8219,
            site_name="Nairobi field station",
            sampling_date=date(2026, 1, 10),
            status="pending",
            affiliations=["worm_lab"],
            species_names=["unidentified"],
        )
        create_sample_if_missing(
            db,
            sample_id="SEED-EUROPE-001",
            lat=51.5072,
            lon=-0.1276,
            site_name="Thames riverbank",
            sampling_date=date(2026, 1, 22),
            status="validated",
            affiliations=["sanger_institute"],
            species_names=["Caenorhabditis elegans"],
        )
        create_sample_if_missing(
            db,
            sample_id="SEED-SOUTHAM-001",
            lat=-23.5505,
            lon=-46.6333,
            site_name="Sao Paulo urban garden",
            sampling_date=date(2026, 2, 2),
            status="pending",
            affiliations=["worm_lab", "sanger_institute"],
            species_names=["unidentified", "Pristionchus pacificus"],
        )

        db.commit()
        print("Seed data loaded.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
