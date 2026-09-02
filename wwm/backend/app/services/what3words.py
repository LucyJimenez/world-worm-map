from __future__ import annotations

from datetime import datetime
import re
from typing import Any

import requests

from app.core.config import settings

W3W_WORD = r"[\wÀ-ÖØ-öø-ÿ-]+"
W3W_PATTERN = re.compile(rf"^(?:///)?({W3W_WORD})[.\s,]+({W3W_WORD})[.\s,]+({W3W_WORD})$", re.IGNORECASE)


def normalize_what3words(value: Any) -> str | None:
    if value is None:
        return None

    text = str(value).strip().lower()
    if not text:
        return None

    text = text.removeprefix("///").strip()
    match = W3W_PATTERN.match(text)
    if not match:
        return None

    return ".".join(part.strip(". ") for part in match.groups())


def what3words_map_url(words: str | None) -> str | None:
    if not words:
        return None
    return f"https://what3words.com/{words}"


def convert_to_coordinates(words: str) -> dict[str, Any] | None:
    if not settings.what3words_api_key:
        return None

    response = requests.get(
        "https://api.what3words.com/v3/convert-to-coordinates",
        params={
            "words": words,
            "key": settings.what3words_api_key,
            "language": settings.what3words_language,
        },
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    coordinates = payload.get("coordinates") or {}
    lat = coordinates.get("lat")
    lon = coordinates.get("lng")

    if lat is None or lon is None:
        return None

    return {
        "words": normalize_what3words(payload.get("words")) or words,
        "language": payload.get("language"),
        "lat": float(lat),
        "lon": float(lon),
        "nearest_place": payload.get("nearestPlace"),
        "country": payload.get("country"),
        "map_url": what3words_map_url(normalize_what3words(payload.get("words")) or words),
        "square": payload.get("square"),
        "updated_at": datetime.utcnow(),
    }
