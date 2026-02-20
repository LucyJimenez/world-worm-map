from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.core.config import settings
from app.models import Affiliation, GenomicRecord, Sample, SampleAffiliation, SampleSpecies
from app.schemas.schemas import ApprovalRequest, GenomicRecordOut, GenomicsCreate, SpeciesCreate
from app.services.accession import validate_accession
from app.services.audit import write_audit
from app.services.auth import require_role
from app.services.kobo_ingest import get_kobo_fields_debug, ingest_kobo_submissions
from app.services.scheduler import scheduler

router = APIRouter(prefix="/api", tags=["wwm"])


@router.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "database": "connected",
        "scheduler": "running" if scheduler.running else "stopped",
    }


@router.get("/samples")
def list_samples(
    species: str | None = Query(default=None),
    status: str | None = Query(default=None),
    affiliation: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    stmt = select(Sample).options(
        selectinload(Sample.affiliations).selectinload(SampleAffiliation.affiliation),
        selectinload(Sample.species_entries).selectinload(SampleSpecies.genomic_records),
    )

    if status:
        stmt = stmt.where(Sample.status == status)

    if species:
        stmt = stmt.join(SampleSpecies, SampleSpecies.sample_id == Sample.id).where(
            func.lower(SampleSpecies.species_name) == species.lower()
        )

    if affiliation:
        stmt = (
            stmt.join(SampleAffiliation, SampleAffiliation.sample_id == Sample.id)
            .join(Affiliation, Affiliation.id == SampleAffiliation.affiliation_id)
            .where(func.lower(Affiliation.name) == affiliation.lower())
        )

    stmt = stmt.order_by(Sample.submitted_at.desc())
    samples = db.execute(stmt).scalars().unique().all()

    return [
        {
            "sample_id": sample.external_sample_id,
            "status": sample.status,
            "site_name": sample.site_name or "Unknown site",
            "sampling_date": sample.sampling_date.isoformat()
            if sample.sampling_date
            else sample.submitted_at.date().isoformat(),
            "collector_name": sample.submitted_by
            or (sample.raw_payload or {}).get("collector_name")
            or (sample.raw_payload or {}).get("collector"),
            "tube_id": (sample.raw_payload or {}).get("tube_id"),
            "soil_ph": (sample.raw_payload or {}).get("soil_ph"),
            "depth_cm": (sample.raw_payload or {}).get("depth_cm"),
            "lat": sample.latitude,
            "lon": sample.longitude,
            "affiliations": [sa.affiliation.name for sa in sample.affiliations],
            "affiliation_other": (sample.raw_payload or {}).get("affiliation_other"),
            "species": [sp.species_name for sp in sample.species_entries],
            "has_genomic_links": any(sp.genomic_records for sp in sample.species_entries),
        }
        for sample in samples
    ]


@router.get("/species")
def list_species(db: Session = Depends(get_db)):
    rows = db.execute(
        select(SampleSpecies.species_name, func.count(SampleSpecies.id).label("sample_count"))
        .group_by(SampleSpecies.species_name)
        .order_by(SampleSpecies.species_name.asc())
    ).all()
    return [{"species_name": row.species_name, "sample_count": row.sample_count} for row in rows]


@router.get("/affiliations")
def list_affiliations(db: Session = Depends(get_db)):
    rows = db.execute(select(Affiliation).order_by(Affiliation.name.asc())).scalars().all()
    return [{"slug": row.name, "name": row.display_name} for row in rows]


@router.post("/samples/{sample_id}/approve")
def approve_sample(
    sample_id: int,
    payload: ApprovalRequest,
    _: str = Depends(require_role("curator")),
    db: Session = Depends(get_db),
):
    sample = db.get(Sample, sample_id)
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")

    sample.status = payload.status
    write_audit(
        db,
        actor="curator",
        action="approve_sample",
        entity_type="sample",
        entity_id=str(sample.id),
        detail={"status": payload.status},
    )
    db.commit()
    db.refresh(sample)
    return {"id": sample.id, "status": sample.status}


@router.post("/samples/{sample_id}/species")
def add_curated_species(
    sample_id: int,
    payload: SpeciesCreate,
    _: str = Depends(require_role("curator")),
    db: Session = Depends(get_db),
):
    sample = db.get(Sample, sample_id)
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")

    species = SampleSpecies(
        sample_id=sample_id,
        species_name=payload.species_name.strip(),
        is_provisional=False,
        curated_by="curator",
    )
    db.add(species)
    write_audit(
        db,
        actor="curator",
        action="add_species",
        entity_type="sample_species",
        entity_id="pending",
        detail={"sample_id": sample_id, "species_name": species.species_name},
    )
    db.commit()
    db.refresh(species)
    return {
        "id": species.id,
        "sample_id": species.sample_id,
        "species_name": species.species_name,
        "is_provisional": species.is_provisional,
    }


@router.post("/species/{sample_species_id}/genomics", response_model=GenomicRecordOut)
def add_genomics_record(
    sample_species_id: int,
    payload: GenomicsCreate,
    _: str = Depends(require_role("curator")),
    db: Session = Depends(get_db),
):
    species_entry = db.get(SampleSpecies, sample_species_id)
    if not species_entry:
        raise HTTPException(status_code=404, detail="Sample species entry not found")

    validation = validate_accession(payload.accession)
    record = GenomicRecord(
        sample_species_id=sample_species_id,
        accession=payload.accession.strip(),
        accession_validated=validation.accession_validated,
        resolved_url=validation.resolved_url,
    )
    db.add(record)

    write_audit(
        db,
        actor="curator",
        action="add_genomic_record",
        entity_type="genomic_record",
        entity_id="pending",
        detail={
            "sample_species_id": sample_species_id,
            "accession": payload.accession,
            "validated": validation.accession_validated,
        },
    )

    db.commit()
    db.refresh(record)
    return record


@router.post("/admin/ingest/kobo")
def trigger_kobo_ingest(
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    if settings.environment != "development":
        require_role("admin")(x_api_key=x_api_key)
    elif x_api_key and x_api_key != settings.api_key_admin:
        raise HTTPException(status_code=403, detail="Invalid admin API key")

    result = ingest_kobo_submissions(db, actor="admin")
    return result


@router.get("/admin/kobo/fields")
def debug_kobo_fields(_: str = Depends(require_role("admin"))):
    return get_kobo_fields_debug()
