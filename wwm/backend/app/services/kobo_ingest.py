from __future__ import annotations

from datetime import date, datetime
import logging
import re
from typing import Any

import requests
from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Affiliation, Sample, SampleAffiliation, SampleSpecies
from app.services.audit import write_audit

logger = logging.getLogger(__name__)


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    if isinstance(value, (list, tuple, dict)) and len(value) == 0:
        return True
    return False


def get_first(submission: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Return first non-empty value among given keys from a Kobo submission."""
    for key in keys:
        value = submission.get(key)
        if not _is_empty(value):
            return value

        # Kobo group fields are often namespaced (for example group_xxx/sample_id).
        if "/" not in key and not key.startswith("_"):
            suffix = f"/{key}"
            for submission_key, submission_value in submission.items():
                if submission_key.endswith(suffix) and not _is_empty(submission_value):
                    return submission_value
    return default


def _slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower())
    return value.strip("_")


def _humanize(value: str) -> str:
    return value.replace("_", " ").replace("-", " ").strip().title()


def _clean_string(value: Any) -> str | None:
    if _is_empty(value):
        return None
    text = str(value).strip()
    if len(text) >= 2 and ((text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'"))):
        text = text[1:-1].strip()
    return text or None


def _parse_date(value: Any) -> date | None:
    if _is_empty(value):
        return None
    raw = str(value).strip().replace("Z", "")
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y/%m/%d"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def _parse_geopoint(value: Any) -> tuple[float, float] | None:
    if value is None:
        return None

    if isinstance(value, (list, tuple)) and len(value) >= 2:
        try:
            return float(value[0]), float(value[1])
        except (TypeError, ValueError):
            return None

    if isinstance(value, str):
        raw = value.strip().replace(",", " ")
        parts = [part for part in raw.split() if part]
        if len(parts) >= 2:
            try:
                return float(parts[0]), float(parts[1])
            except ValueError:
                return None
    return None


def _extract_submissions(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("results"), list):
        return [item for item in payload["results"] if isinstance(item, dict)]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def _fetch_kobo_submissions() -> list[dict[str, Any]]:
    if not settings.kobo_asset_uid or not settings.kobo_token:
        return []

    base_url = settings.kobo_base_url.rstrip("/")
    url = f"{base_url}/api/v2/assets/{settings.kobo_asset_uid}/data/"
    headers = {
        "Authorization": f"Token {settings.kobo_token}",
        "Accept": "application/json",
    }

    response = requests.get(url, headers=headers, params={"format": "json"}, timeout=30)
    response.raise_for_status()
    return _extract_submissions(response.json())


def _parse_affiliation_values(value: Any) -> list[str]:
    if _is_empty(value):
        return []
    if isinstance(value, list):
        raw_items = [str(item).strip() for item in value if str(item).strip()]
    else:
        raw_items = [item.strip() for item in re.split(r"[\s,;]+", str(value)) if item.strip()]

    normalized: list[str] = []
    for item in raw_items:
        slug = _slugify(item)
        if slug and slug not in normalized:
            normalized.append(slug)
    return normalized


def _get_or_create_affiliation(db: Session, slug: str, display_name: str | None = None) -> Affiliation:
    if not slug:
        raise ValueError("Affiliation slug cannot be empty.")

    affiliation = db.execute(select(Affiliation).where(Affiliation.name == slug)).scalar_one_or_none()
    if affiliation:
        return affiliation

    label = display_name.strip() if display_name and display_name.strip() else _humanize(slug)
    affiliation = Affiliation(name=slug, display_name=label)
    db.add(affiliation)
    db.flush()
    return affiliation


def _attach_affiliations(db: Session, sample: Sample, normalized: dict[str, Any]) -> None:
    affiliation_slugs = normalized.get("affiliation_slugs", [])
    affiliation_other = normalized.get("affiliation_other")

    linked_slugs: set[str] = set()
    for slug in affiliation_slugs:
        if slug == "other":
            continue
        affiliation = _get_or_create_affiliation(db, slug)
        if affiliation.name not in linked_slugs:
            db.add(SampleAffiliation(sample_id=sample.id, affiliation_id=affiliation.id))
            linked_slugs.add(affiliation.name)

    if "other" in affiliation_slugs and affiliation_other:
        other_slug = _slugify(affiliation_other)
        if other_slug:
            affiliation = _get_or_create_affiliation(db, other_slug, display_name=affiliation_other)
            if affiliation.name not in linked_slugs:
                db.add(SampleAffiliation(sample_id=sample.id, affiliation_id=affiliation.id))
                linked_slugs.add(affiliation.name)

    if not affiliation_slugs and affiliation_other:
        other_slug = _slugify(affiliation_other)
        if other_slug:
            affiliation = _get_or_create_affiliation(db, other_slug, display_name=affiliation_other)
            if affiliation.name not in linked_slugs:
                db.add(SampleAffiliation(sample_id=sample.id, affiliation_id=affiliation.id))


def _normalize_submission(submission: dict[str, Any]) -> dict[str, Any] | None:
    preferred_sample_id = get_first(submission, "sample_id")
    fallback_sample_id = get_first(submission, "_uuid", "_id")
    sample_id_value = preferred_sample_id or fallback_sample_id

    if _is_empty(sample_id_value):
        return None

    if _is_empty(preferred_sample_id):
        logger.warning("Kobo submission missing sample_id; falling back to _uuid/_id: %s", sample_id_value)

    site_name = _clean_string(get_first(submission, "site_name")) or "Unknown site"
    collector_name = _clean_string(get_first(submission, "collector_name", "collector"))
    sampling_date = _parse_date(get_first(submission, "sampling_date", "_submission_time")) or date.today()
    gps_raw = get_first(submission, "gps_coordinates", "_geolocation")
    geopoint = _parse_geopoint(gps_raw)
    if geopoint is None:
        return None

    affiliation_raw = get_first(submission, "affiliation", default=[])
    affiliation_slugs = _parse_affiliation_values(affiliation_raw)
    affiliation_other = _clean_string(get_first(submission, "affiliation_other"))
    country_value = _clean_string(get_first(submission, "country"))

    return {
        "sample_id": str(sample_id_value).strip(),
        "site_name": site_name,
        "collector_name": collector_name,
        "sampling_date": sampling_date,
        "gps_coordinates_raw": gps_raw,
        "lat": geopoint[0],
        "lon": geopoint[1],
        "country": country_value,
        "habitat_type": _clean_string(get_first(submission, "habitat_type")),
        "soil_type": _clean_string(get_first(submission, "soil_type")),
        "soil_ph": _clean_string(get_first(submission, "soil_ph")),
        "depth_cm": _clean_string(get_first(submission, "depth_cm")),
        "num_samples": _clean_string(get_first(submission, "num_samples")),
        "tube_id": _clean_string(get_first(submission, "tube_id")),
        "notes": _clean_string(get_first(submission, "notes", "additional_notes")),
        "climate_info": _clean_string(get_first(submission, "climate_info")),
        "photo_sample": get_first(submission, "photo_sample"),
        "start": _clean_string(get_first(submission, "start")),
        "end": _clean_string(get_first(submission, "end")),
        "today": _clean_string(get_first(submission, "today")),
        "instance_uuid": _clean_string(get_first(submission, "instance_uuid")),
        "meta_instance_id": _clean_string(get_first(submission, "meta/instanceID")),
        "affiliation_raw": affiliation_raw,
        "affiliation_slugs": affiliation_slugs,
        "affiliation_other": affiliation_other,
        "raw": submission,
    }


def get_kobo_fields_debug() -> dict[str, Any]:
    submissions = _fetch_kobo_submissions()
    if not submissions:
        return {"count": 0, "keys": [], "mapped": {}}

    latest = submissions[0]
    normalized = _normalize_submission(latest)
    mapped = {
        "sample_id": normalized.get("sample_id") if normalized else None,
        "site_name": normalized.get("site_name") if normalized else None,
        "collector_name": normalized.get("collector_name") if normalized else None,
        "sampling_date": normalized.get("sampling_date").isoformat() if normalized else None,
        "gps_coordinates": normalized.get("gps_coordinates_raw") if normalized else None,
        "affiliation": normalized.get("affiliation_raw") if normalized else None,
        "affiliation_other": normalized.get("affiliation_other") if normalized else None,
        "affiliation_slugs": normalized.get("affiliation_slugs") if normalized else [],
    }
    return {"count": len(submissions), "keys": sorted(latest.keys()), "mapped": mapped}


def ingest_kobo_submissions(db: Session, actor: str = "system") -> dict[str, int]:
    submissions = _fetch_kobo_submissions()
    ingested = 0
    duplicates = 0
    errors = 0
    debug_logged = 0

    for raw_item in submissions:
        try:
            with db.begin_nested():
                normalized = _normalize_submission(raw_item)
                if not normalized:
                    errors += 1
                    continue

                ext_id = normalized["sample_id"]
                already_exists = db.execute(select(exists().where(Sample.external_sample_id == ext_id))).scalar()
                if already_exists:
                    duplicates += 1
                    continue

                if settings.environment == "development" and debug_logged < 3:
                    logger.info(
                        "Kobo mapped record: sample_id=%s site_name=%s gps=%s affiliation_raw=%s",
                        normalized["sample_id"],
                        normalized["site_name"],
                        normalized["gps_coordinates_raw"],
                        normalized["affiliation_raw"],
                    )
                    debug_logged += 1

                sample = Sample(
                    external_sample_id=ext_id,
                    submitted_by=normalized.get("collector_name"),
                    country=normalized.get("country"),
                    site_name=normalized.get("site_name"),
                    sampling_date=normalized.get("sampling_date"),
                    status="pending",
                    notes=str(normalized.get("notes")) if normalized.get("notes") is not None else None,
                    raw_payload={
                        "kobo": normalized.get("raw"),
                        "collector_name": normalized.get("collector_name"),
                        "country": normalized.get("country"),
                        "habitat_type": normalized.get("habitat_type"),
                        "soil_type": normalized.get("soil_type"),
                        "soil_ph": normalized.get("soil_ph"),
                        "depth_cm": normalized.get("depth_cm"),
                        "num_samples": normalized.get("num_samples"),
                        "tube_id": normalized.get("tube_id"),
                        "climate_info": normalized.get("climate_info"),
                        "photo_sample": normalized.get("photo_sample"),
                        "start": normalized.get("start"),
                        "end": normalized.get("end"),
                        "today": normalized.get("today"),
                        "instance_uuid": normalized.get("instance_uuid"),
                        "meta_instance_id": normalized.get("meta_instance_id"),
                        "affiliation_other": normalized.get("affiliation_other"),
                    },
                    submitted_at=datetime.utcnow(),
                    latitude=normalized["lat"],
                    longitude=normalized["lon"],
                    geom=func.ST_SetSRID(func.ST_MakePoint(normalized["lon"], normalized["lat"]), 4326),
                )
                db.add(sample)
                db.flush()

                _attach_affiliations(db, sample, normalized)

                db.add(
                    SampleSpecies(
                        sample_id=sample.id,
                        species_name="unidentified",
                        is_provisional=True,
                        curated_by=None,
                    )
                )

                write_audit(
                    db,
                    actor=actor,
                    action="ingest_sample",
                    entity_type="sample",
                    entity_id=str(sample.id),
                    detail={"external_sample_id": ext_id, "source": "kobo"},
                )
                ingested += 1
        except Exception:
            logger.exception("Failed to ingest Kobo submission")
            errors += 1

    db.commit()
    return {
        "ingested": ingested,
        "duplicates": duplicates,
        "errors": errors,
    }
