from __future__ import annotations

from datetime import date, datetime
import json
import os
from pathlib import Path
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


OUTPUT_PATH = Path("wwm/frontend/demo-samples.json")

HABITAT_VALUES = {
    "agricultural_field": "Agricultural field",
    "forest": "Forest",
    "grassland": "Grassland",
    "wetland": "Wetland",
    "urban": "Urban / built environment",
    "desert": "Desert / arid",
    "freshwater_margin": "Freshwater margin (river/lake)",
    "coastal": "Coastal",
    "tundra": "Tundra / alpine",
    "other": "Other",
}

SOIL_VALUES = {
    "sandy": "Sandy",
    "clay": "Clay",
    "silt": "Silt",
    "loam": "Loam",
    "peat": "Peat",
    "chalk": "Chalk",
    "volcanic": "Volcanic",
    "mixed": "Mixed",
    "other": "Other",
}

AFFILIATION_VALUES = {
    "worm_lab": "Worm Lab",
    "sanger_institute": "Sanger Institute",
    "crc1211": "CRC1211",
}


def is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    if isinstance(value, (list, tuple, dict)) and len(value) == 0:
        return True
    return False


def get_first(submission: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        value = submission.get(key)
        if not is_empty(value):
            return value

        if "/" not in key and not key.startswith("_"):
            suffix = f"/{key}"
            for submission_key, submission_value in submission.items():
                if submission_key.endswith(suffix) and not is_empty(submission_value):
                    return submission_value
    return default


def clean_string(value: Any) -> str | None:
    if is_empty(value):
        return None
    text = str(value).strip()
    if len(text) >= 2 and ((text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'"))):
        text = text[1:-1].strip()
    return text or None


def parse_date(value: Any) -> str:
    if is_empty(value):
        return date.today().isoformat()
    raw = str(value).strip().replace("Z", "")
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y/%m/%d"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    return date.today().isoformat()


def parse_geopoint(value: Any) -> tuple[float, float] | None:
    if value is None:
        return None
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        try:
            return float(value[0]), float(value[1])
        except (TypeError, ValueError):
            return None
    if isinstance(value, str):
        parts = [part for part in value.strip().replace(",", " ").split() if part]
        if len(parts) >= 2:
            try:
                return float(parts[0]), float(parts[1])
            except ValueError:
                return None
    return None


def parse_multi_value(value: Any) -> list[str]:
    if is_empty(value):
        return []
    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
    else:
        items = [item.strip() for item in re.split(r"[\s,;]+", str(value)) if item.strip()]
    return list(dict.fromkeys(items))


def slugify(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")


def normalize_choice(value: Any, mapping: dict[str, str]) -> str | None:
    text = clean_string(value)
    if not text:
        return None
    if re.fullmatch(r"option_\d+", text):
        return None

    if text in mapping:
        return text

    slug = slugify(text)
    if slug in mapping:
        return slug

    for key, label in mapping.items():
        if slugify(label) == slug:
            return key
    return text


def clean_country(value: Any) -> str | None:
    text = clean_string(value)
    if not text or re.fullmatch(r"option_\d+", text):
        return None
    return text


def normalize_choices(value: Any, mapping: dict[str, str]) -> list[str]:
    normalized: list[str] = []
    for item in parse_multi_value(value):
        choice = normalize_choice(item, mapping)
        if choice and choice not in normalized:
            normalized.append(choice)
    return normalized


def labels_for(values: list[str], mapping: dict[str, str]) -> list[str]:
    return [mapping.get(value, value) for value in values]


def extract_submissions(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("results"), list):
        return [item for item in payload["results"] if isinstance(item, dict)]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def fetch_kobo_submissions() -> list[dict[str, Any]]:
    base_url = os.environ.get("KOBO_BASE_URL", "https://eu.kobotoolbox.org").rstrip("/")
    asset_uid = os.environ.get("KOBO_ASSET_UID", "a8Rvu5KasYeAfsa2GfFppG").strip()
    token = os.environ.get("KOBO_TOKEN", "").strip()

    if not asset_uid or not token:
        raise RuntimeError("KOBO_ASSET_UID and KOBO_TOKEN are required for live Kobo export.")

    url = f"{base_url}/api/v2/assets/{asset_uid}/data/?{urlencode({'format': 'json'})}"
    request = Request(url, headers={"Authorization": f"Token {token}", "Accept": "application/json"})
    with urlopen(request, timeout=30) as response:
        return extract_submissions(json.loads(response.read().decode("utf-8")))


def to_public_sample(submission: dict[str, Any], index: int) -> dict[str, Any] | None:
    geopoint = parse_geopoint(get_first(submission, "gps_coordinates", "_geolocation"))
    if not geopoint:
        return None

    species = parse_multi_value(get_first(submission, "species", "species_name", default=[]))
    family = parse_multi_value(get_first(submission, "family", "families", default=[]))
    habitat_type = normalize_choice(
        get_first(submission, "habitat_type", "habitat_type_001"),
        HABITAT_VALUES,
    )
    habitat_other = clean_string(get_first(submission, "habitat_other", "If_Other_please_type_the_habitat_type"))
    soil_types = normalize_choices(get_first(submission, "soil_type", "soil_type_001_001"), SOIL_VALUES)
    affiliation_slugs = normalize_choices(get_first(submission, "affiliation", default=[]), AFFILIATION_VALUES)
    affiliation_other = clean_string(get_first(submission, "affiliation_other"))
    affiliations = labels_for([item for item in affiliation_slugs if item != "other"], AFFILIATION_VALUES)
    if "other" in affiliation_slugs and affiliation_other:
        affiliations.append(affiliation_other)

    return {
        "sample_id": f"public-kobo-{index:04d}",
        "site_name": clean_string(get_first(submission, "site_name")) or "Unnamed sampling site",
        "sampling_date": parse_date(get_first(submission, "sampling_date", "_submission_time")),
        "country": clean_country(get_first(submission, "country")),
        "habitat_type": habitat_type,
        "habitat_label": habitat_other if habitat_type == "other" and habitat_other else HABITAT_VALUES.get(habitat_type, habitat_type),
        "soil_type": ",".join(soil_types) if soil_types else None,
        "soil_types": soil_types,
        "soil_labels": labels_for(soil_types, SOIL_VALUES),
        "soil_ph": clean_string(get_first(submission, "soil_ph")),
        "depth_cm": clean_string(get_first(submission, "depth_cm")),
        "lat": geopoint[0],
        "lon": geopoint[1],
        "affiliations": affiliations,
        "species": species or ["unidentified"],
        "families": family,
    }


def main() -> int:
    try:
        submissions = fetch_kobo_submissions()
        public_samples = [sample for index, item in enumerate(submissions, start=1) if (sample := to_public_sample(item, index))]
    except (HTTPError, URLError, RuntimeError) as exc:
        print(f"Kobo export skipped: {exc}")
        return 0

    if not public_samples:
        print("Kobo export produced no mappable samples; keeping existing demo-samples.json.")
        return 0

    OUTPUT_PATH.write_text(json.dumps(public_samples, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(public_samples)} public Kobo samples to {OUTPUT_PATH}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
