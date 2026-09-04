"""Seed demo data for local development."""

from datetime import date, datetime

from sqlalchemy import delete, func, select

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
    what3words: str | None = None,
    country: str | None = None,
    raw_payload: dict | None = None,
):
    sample = db.execute(select(Sample).where(Sample.external_sample_id == sample_id)).scalar_one_or_none()
    if not sample:
        sample = Sample(external_sample_id=sample_id, submitted_at=datetime.utcnow())
        db.add(sample)
    else:
        db.execute(delete(SampleAffiliation).where(SampleAffiliation.sample_id == sample.id))
        db.execute(delete(SampleSpecies).where(SampleSpecies.sample_id == sample.id))

    sample.submitted_by = "demo@example.org"
    sample.data_source = "seed"
    sample.what3words = what3words
    sample.what3words_source = "seed" if what3words else None
    sample.what3words_status = "demo" if what3words else None
    sample.what3words_map_url = f"https://what3words.com/{what3words}" if what3words else None
    sample.site_name = site_name
    sample.country = country or (raw_payload or {}).get("country")
    sample.sampling_date = sampling_date
    sample.status = status
    sample.notes = "Seeded sample"
    sample.raw_payload = raw_payload or {}
    sample.latitude = lat
    sample.longitude = lon
    sample.geom = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
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
        upsert_affiliation("crc1211", "CRC1211", db)
        upsert_affiliation("swedish_museum_of_natural_history", "Swedish Museum of Natural History", db)

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
            what3words="filled.count.soap",
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
            what3words="index.home.raft",
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
            what3words="pays.vibes.daring",
        )
        create_sample_if_missing(
            db,
            sample_id="SEED-BETA-CH-001",
            lat=47.5596,
            lon=7.5886,
            site_name="Basel grassland edge",
            sampling_date=date(2026, 5, 4),
            status="validated",
            country="CH",
            affiliations=["worm_lab", "sanger_institute"],
            species_names=["Heterodera schachtii"],
            raw_payload={
                "habitat_type": "grassland",
                "soil_type": "loam,sandy",
                "soil_ph": 7.1,
                "depth_cm": 20,
                "num_samples": 3,
                "taxonomic_entries": [{"family": "Heteroderidae", "species": "Heterodera schachtii"}],
            },
        )
        create_sample_if_missing(
            db,
            sample_id="SEED-BETA-CO-001",
            lat=4.711,
            lon=-74.072,
            site_name="Bogota highland agricultural plot",
            sampling_date=date(2026, 5, 1),
            status="pending",
            country="CO",
            affiliations=["worm_lab"],
            species_names=["Pratylenchus penetrans", "Meloidogyne incognita"],
            raw_payload={
                "habitat_type": "agricultural_field",
                "soil_type": "loam,clay",
                "soil_ph": 6.4,
                "depth_cm": 15,
                "num_samples": 2,
                "taxonomic_entries": [
                    {"family": "Pratylenchidae", "species": "Pratylenchus penetrans"},
                    {"family": "Meloidogynidae", "species": "Meloidogyne incognita"},
                ],
            },
        )
        create_sample_if_missing(
            db,
            sample_id="SEED-BETA-KE-001",
            lat=-1.2864,
            lon=36.8172,
            site_name="Nairobi urban garden",
            sampling_date=date(2026, 5, 8),
            status="validated",
            country="KE",
            affiliations=["crc1211"],
            species_names=["Caenorhabditis elegans"],
            raw_payload={
                "habitat_type": "urban",
                "soil_type": "mixed",
                "soil_ph": 6.8,
                "depth_cm": 10,
                "num_samples": 4,
                "taxonomic_entries": [{"family": "Rhabditidae", "species": "Caenorhabditis elegans"}],
            },
        )
        create_sample_if_missing(
            db,
            sample_id="SEED-BETA-JP-001",
            lat=35.6762,
            lon=139.6503,
            site_name="Honshu forest soil",
            sampling_date=date(2026, 5, 11),
            status="pending",
            country="JP",
            affiliations=["sanger_institute"],
            species_names=["Aphelenchoides fragariae"],
            raw_payload={
                "habitat_type": "forest",
                "soil_type": "volcanic,loam",
                "soil_ph": 5.6,
                "depth_cm": 18,
                "num_samples": 1,
                "taxonomic_entries": [{"family": "Aphelenchoididae", "species": "Aphelenchoides fragariae"}],
            },
        )
        create_sample_if_missing(
            db,
            sample_id="SEED-BETA-ZA-001",
            lat=-33.9249,
            lon=18.4241,
            site_name="Cape coastal dune",
            sampling_date=date(2026, 5, 16),
            status="rejected",
            country="ZA",
            affiliations=["worm_lab"],
            species_names=["Panagrolaimus sp."],
            raw_payload={
                "habitat_type": "coastal",
                "soil_type": "sandy",
                "soil_ph": 8.0,
                "depth_cm": 12,
                "num_samples": 1,
                "taxonomic_entries": [{"family": "Panagrolaimidae", "species": "Panagrolaimus sp."}],
            },
        )
        create_sample_if_missing(
            db,
            sample_id="SEED-BETA-CL-001",
            lat=-22.322429,
            lon=-69.474276,
            site_name="Atacama Desert sampling site",
            sampling_date=date(2025, 3, 26),
            status="pending",
            country="CL",
            affiliations=["worm_lab"],
            species_names=["Pristionchus pacificus"],
            raw_payload={
                "habitat_type": "desert",
                "soil_type": "sandy",
                "soil_ph": 6.8,
                "depth_cm": 35,
                "num_samples": 2,
                "taxonomic_entries": [{"family": "Diplogastridae", "species": "Pristionchus pacificus"}],
            },
        )

        db.commit()
        print("Seed data loaded.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
