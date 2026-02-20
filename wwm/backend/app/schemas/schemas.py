from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class SpeciesCreate(BaseModel):
    species_name: str = Field(min_length=2, max_length=255)


class ApprovalRequest(BaseModel):
    status: Literal["validated", "rejected"]


class GenomicsCreate(BaseModel):
    accession: str = Field(min_length=2, max_length=255)


class AffiliationOut(BaseModel):
    id: int
    name: str
    display_name: str

    model_config = {"from_attributes": True}


class SpeciesOut(BaseModel):
    id: int
    sample_id: int
    species_name: str
    is_provisional: bool
    curated_by: Optional[str]

    model_config = {"from_attributes": True}


class SampleOut(BaseModel):
    id: int
    external_sample_id: str
    submitted_by: Optional[str]
    status: str
    submitted_at: datetime
    latitude: float
    longitude: float
    notes: Optional[str]
    affiliations: list[str]
    species: list[str]


class GenomicRecordOut(BaseModel):
    id: int
    sample_species_id: int
    accession: str
    accession_validated: bool
    resolved_url: Optional[str]

    model_config = {"from_attributes": True}
