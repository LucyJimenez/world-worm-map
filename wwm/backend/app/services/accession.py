from dataclasses import dataclass

import requests

from app.core.config import settings


@dataclass
class AccessionValidationResult:
    accession_validated: bool
    resolved_url: str | None


def validate_accession(accession: str) -> AccessionValidationResult:
    """Validate accession against NCBI when enabled, otherwise keep records unverified."""
    accession = accession.strip()
    if not accession:
        return AccessionValidationResult(False, None)

    fallback_url = f"https://www.ncbi.nlm.nih.gov/nuccore/{accession}"

    if not settings.enable_real_ncbi_validation:
        return AccessionValidationResult(False, fallback_url)

    params = {
        "db": "nucleotide",
        "term": accession,
        "retmode": "json",
    }

    try:
        response = requests.get(settings.ncbi_api_base, params=params, timeout=10)
        response.raise_for_status()
        payload = response.json()
        id_list = payload.get("esearchresult", {}).get("idlist", [])
        is_valid = len(id_list) > 0
        return AccessionValidationResult(is_valid, fallback_url if is_valid else None)
    except requests.RequestException:
        return AccessionValidationResult(False, None)
