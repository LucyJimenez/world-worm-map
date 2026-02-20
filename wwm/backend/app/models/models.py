from datetime import date, datetime
from typing import Optional

from geoalchemy2 import Geometry
from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="viewer")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Affiliation(Base):
    __tablename__ = "affiliations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)


class Sample(Base):
    __tablename__ = "samples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_sample_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    submitted_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    site_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sampling_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    geom: Mapped[str] = mapped_column(Geometry(geometry_type="POINT", srid=4326), nullable=False)

    affiliations: Mapped[list["SampleAffiliation"]] = relationship(back_populates="sample", cascade="all, delete-orphan")
    species_entries: Mapped[list["SampleSpecies"]] = relationship(back_populates="sample", cascade="all, delete-orphan")


class SampleAffiliation(Base):
    __tablename__ = "sample_affiliations"
    __table_args__ = (UniqueConstraint("sample_id", "affiliation_id", name="uq_sample_affiliation"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sample_id: Mapped[int] = mapped_column(ForeignKey("samples.id", ondelete="CASCADE"), nullable=False)
    affiliation_id: Mapped[int] = mapped_column(ForeignKey("affiliations.id", ondelete="CASCADE"), nullable=False)

    sample: Mapped[Sample] = relationship(back_populates="affiliations")
    affiliation: Mapped[Affiliation] = relationship()


class SampleSpecies(Base):
    __tablename__ = "sample_species"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sample_id: Mapped[int] = mapped_column(ForeignKey("samples.id", ondelete="CASCADE"), nullable=False)
    species_name: Mapped[str] = mapped_column(String(255), nullable=False, default="unidentified")
    is_provisional: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    curated_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    sample: Mapped[Sample] = relationship(back_populates="species_entries")
    genomic_records: Mapped[list["GenomicRecord"]] = relationship(back_populates="sample_species", cascade="all, delete-orphan")


class GenomicRecord(Base):
    __tablename__ = "genomic_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sample_species_id: Mapped[int] = mapped_column(ForeignKey("sample_species.id", ondelete="CASCADE"), nullable=False)
    accession: Mapped[str] = mapped_column(String(255), nullable=False)
    accession_validated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    resolved_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    sample_species: Mapped[SampleSpecies] = relationship(back_populates="genomic_records")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(120), nullable=False)
    detail: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
