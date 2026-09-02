from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from flask import Flask, jsonify, render_template, request, send_from_directory


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "wwm.sqlite3"
ENV_PATH = BASE_DIR / ".env"

app = Flask(__name__)


def load_local_env() -> None:
    if not ENV_PATH.exists():
        return
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_local_env()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def get_db() -> sqlite3.Connection:
    DATA_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS samples (
              sample_id TEXT PRIMARY KEY,
              collector_name TEXT,
              sampling_date TEXT,
              country TEXT,
              site_name TEXT,
              lat REAL,
              lon REAL,
              altitude_m REAL,
              gps_accuracy_m REAL,
              what3words TEXT,
              what3words_source TEXT,
              what3words_status TEXT,
              what3words_language TEXT,
              what3words_map_url TEXT,
              what3words_nearest_place TEXT,
              what3words_country TEXT,
              what3words_square_json TEXT,
              what3words_updated_at TEXT,
              affiliation TEXT,
              affiliation_other TEXT,
              habitat_type TEXT,
              habitat_other TEXT,
              soil_types TEXT,
              soil_type_other TEXT,
              soil_ph REAL,
              climate_info TEXT,
              depth_cm INTEGER,
              num_samples INTEGER,
              photo_sample TEXT,
              notes TEXT,
              status TEXT NOT NULL DEFAULT 'pending',
              raw_payload TEXT,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sample_taxa (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              sample_id TEXT NOT NULL REFERENCES samples(sample_id) ON DELETE CASCADE,
              scientific_name TEXT NOT NULL,
              family TEXT,
              rank TEXT NOT NULL DEFAULT 'species',
              source TEXT NOT NULL DEFAULT 'provisional',
              identification_method TEXT,
              gene_marker TEXT,
              genetic_sequence_id TEXT,
              genbank_accession TEXT,
              curator_name TEXT,
              validation_date TEXT,
              created_at TEXT NOT NULL,
              UNIQUE(sample_id, scientific_name, family, source)
            );

            CREATE INDEX IF NOT EXISTS idx_samples_location ON samples(lat, lon);
            CREATE INDEX IF NOT EXISTS idx_samples_status ON samples(status);
            CREATE INDEX IF NOT EXISTS idx_samples_environment ON samples(country, habitat_type, soil_ph);
            CREATE INDEX IF NOT EXISTS idx_taxa_name ON sample_taxa(scientific_name);
            CREATE INDEX IF NOT EXISTS idx_taxa_family ON sample_taxa(family);
            """
        )
        ensure_sample_columns(conn)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_samples_what3words ON samples(what3words)")


def ensure_sample_columns(conn: sqlite3.Connection) -> None:
    existing_columns = {
        row["name"] for row in conn.execute("PRAGMA table_info(samples)").fetchall()
    }
    required_columns = {
        "what3words": "TEXT",
        "what3words_source": "TEXT",
        "what3words_status": "TEXT",
        "what3words_language": "TEXT",
        "what3words_map_url": "TEXT",
        "what3words_nearest_place": "TEXT",
        "what3words_country": "TEXT",
        "what3words_square_json": "TEXT",
        "what3words_updated_at": "TEXT",
    }
    for column, column_type in required_columns.items():
        if column not in existing_columns:
            try:
                conn.execute(f"ALTER TABLE samples ADD COLUMN {column} {column_type}")
            except sqlite3.OperationalError as exc:
                if "duplicate column name" not in str(exc):
                    raise


def flatten_payload(value: Any, out: dict[str, Any] | None = None) -> dict[str, Any]:
    out = out or {}
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, dict):
                flatten_payload(item, out)
            else:
                out[key.split("/")[-1]] = item
    return out


def first_value(flat: dict[str, Any], *names: str, default: Any = None) -> Any:
    for name in names:
        if name in flat and flat[name] not in (None, ""):
            return flat[name]
    return default


def to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def to_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def parse_geopoint(value: Any) -> tuple[float | None, float | None, float | None, float | None]:
    if isinstance(value, dict):
        return (
            to_float(first_value(value, "lat", "latitude")),
            to_float(first_value(value, "lon", "lng", "longitude")),
            to_float(first_value(value, "alt", "altitude")),
            to_float(first_value(value, "accuracy", "precision")),
        )
    if isinstance(value, (list, tuple)):
        values = list(value) + [None, None, None, None]
        return to_float(values[0]), to_float(values[1]), to_float(values[2]), to_float(values[3])
    if isinstance(value, str):
        parts = value.replace(",", " ").split()
        values = parts + [None, None, None, None]
        return to_float(values[0]), to_float(values[1]), to_float(values[2]), to_float(values[3])
    return None, None, None, None


def normalize_multi_select(value: Any) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, list):
        values = [str(item).strip() for item in value if str(item).strip()]
    else:
        values = [item.strip() for item in str(value).replace(",", " ").split() if item.strip()]
    return ",".join(dict.fromkeys(values)) or None


def normalize_what3words(value: Any) -> str | None:
    if value in (None, ""):
        return None
    text = str(value).strip().lower()
    text = text.removeprefix("///").strip()
    text = text.replace("/", "").replace(",", ".")
    parts = [part for part in text.replace(".", " ").split() if part]
    if len(parts) == 3:
        return ".".join(parts)
    return text or None


def normalize_kobo_submission(payload: dict[str, Any]) -> dict[str, Any]:
    flat = flatten_payload(payload)
    sample_id = first_value(flat, "sample_id", "instance_uuid", "instanceID", "_uuid")
    if not sample_id:
        sample_id = f"sample-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    lat, lon, altitude_m, gps_accuracy_m = parse_geopoint(
        first_value(flat, "gps_coordinates", "location", "_geolocation")
    )
    habitat_type = first_value(flat, "habitat_type_001", "habitat_type")
    soil_types = normalize_multi_select(first_value(flat, "soil_type_001_001", "soil_type"))
    what3words = normalize_what3words(
        first_value(
            flat,
            "what3words",
            "what3words_address",
            "what3words_three_words",
            "w3w",
            "w3w_address",
            "w3w_three_words",
        )
    )

    return {
        "sample_id": str(sample_id),
        "collector_name": first_value(flat, "collector_name"),
        "sampling_date": first_value(flat, "sampling_date", "today"),
        "country": first_value(flat, "country"),
        "site_name": first_value(flat, "site_name"),
        "lat": lat,
        "lon": lon,
        "altitude_m": altitude_m,
        "gps_accuracy_m": gps_accuracy_m,
        "what3words": what3words,
        "what3words_source": "manual" if what3words else None,
        "what3words_status": "unvalidated" if what3words else None,
        "what3words_language": first_value(flat, "what3words_language", "w3w_language"),
        "what3words_map_url": first_value(flat, "what3words_map_url", "w3w_map_url"),
        "what3words_nearest_place": first_value(flat, "what3words_nearest_place", "w3w_nearest_place"),
        "what3words_country": first_value(flat, "what3words_country", "w3w_country"),
        "what3words_square_json": first_value(flat, "what3words_square_json", "w3w_square_json"),
        "what3words_updated_at": first_value(flat, "what3words_updated_at", "w3w_updated_at"),
        "affiliation": normalize_multi_select(first_value(flat, "affiliation")),
        "affiliation_other": first_value(flat, "affiliation_other"),
        "habitat_type": habitat_type,
        "habitat_other": first_value(flat, "If_Other_please_type_the_habitat_type"),
        "soil_types": soil_types,
        "soil_type_other": first_value(flat, "If_Other_please_type_the_soi"),
        "soil_ph": to_float(first_value(flat, "soil_ph")),
        "climate_info": first_value(flat, "climate_info"),
        "depth_cm": to_int(first_value(flat, "depth_cm")),
        "num_samples": to_int(first_value(flat, "num_samples")),
        "photo_sample": first_value(flat, "photo_sample"),
        "notes": first_value(flat, "notes"),
        "raw_payload": json.dumps(payload, ensure_ascii=False, sort_keys=True),
    }


def row_to_sample(row: sqlite3.Row, taxa: list[sqlite3.Row]) -> dict[str, Any]:
    species = [taxon["scientific_name"] for taxon in taxa]
    families = sorted({taxon["family"] for taxon in taxa if taxon["family"]})
    return {
        "sample_id": row["sample_id"],
        "collector_name": row["collector_name"],
        "sampling_date": row["sampling_date"],
        "country": row["country"],
        "site_name": row["site_name"],
        "lat": row["lat"],
        "lon": row["lon"],
        "altitude_m": row["altitude_m"],
        "gps_accuracy_m": row["gps_accuracy_m"],
        "what3words": row["what3words"],
        "what3words_source": row["what3words_source"],
        "what3words_status": row["what3words_status"],
        "what3words_language": row["what3words_language"],
        "what3words_map_url": row["what3words_map_url"],
        "what3words_nearest_place": row["what3words_nearest_place"],
        "what3words_country": row["what3words_country"],
        "affiliation": split_csv(row["affiliation"]),
        "affiliation_other": row["affiliation_other"],
        "habitat_type": row["habitat_type"],
        "habitat_other": row["habitat_other"],
        "soil_types": split_csv(row["soil_types"]),
        "soil_type_other": row["soil_type_other"],
        "soil_ph": row["soil_ph"],
        "climate_info": row["climate_info"],
        "depth_cm": row["depth_cm"],
        "num_samples": row["num_samples"],
        "photo_sample": row["photo_sample"],
        "notes": row["notes"],
        "status": row["status"],
        "species": species,
        "families": families,
        "taxa": [dict(taxon) for taxon in taxa],
        "has_genomic_links": any(taxon["genbank_accession"] for taxon in taxa),
    }


def split_csv(value: str | None) -> list[str]:
    return [item for item in (value or "").split(",") if item]


def what3words_config() -> dict[str, str | None]:
    return {
        "api_key": os.environ.get("WHAT3WORDS_API_KEY"),
        "language": os.environ.get("WHAT3WORDS_LANGUAGE", "en"),
    }


def fetch_what3words(lat: float, lon: float) -> dict[str, Any]:
    config = what3words_config()
    if not config["api_key"]:
        raise RuntimeError("Missing WHAT3WORDS_API_KEY")

    response = requests.get(
        "https://api.what3words.com/v3/convert-to-3wa",
        params={
            "coordinates": f"{lat},{lon}",
            "language": config["language"],
            "format": "json",
            "key": config["api_key"],
        },
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def fetch_what3words_coordinates(words: str) -> dict[str, Any]:
    config = what3words_config()
    if not config["api_key"]:
        raise RuntimeError("Missing WHAT3WORDS_API_KEY")

    response = requests.get(
        "https://api.what3words.com/v3/convert-to-coordinates",
        params={
            "words": words,
            "format": "json",
            "key": config["api_key"],
        },
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def apply_what3words_result(sample: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    sample["what3words"] = result.get("words")
    sample["what3words_source"] = sample.get("what3words_source") or "derived"
    sample["what3words_status"] = "validated"
    sample["what3words_language"] = result.get("language")
    sample["what3words_map_url"] = result.get("map")
    sample["what3words_nearest_place"] = result.get("nearestPlace")
    sample["what3words_country"] = result.get("country")
    sample["what3words_square_json"] = json.dumps(result.get("square"), sort_keys=True)
    sample["what3words_updated_at"] = utc_now()
    return sample


def apply_what3words_coordinates_result(sample: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    coordinates = result.get("coordinates") or {}
    sample["what3words"] = result.get("words") or sample.get("what3words")
    sample["what3words_source"] = sample.get("what3words_source") or "manual"
    sample["what3words_status"] = "validated"
    sample["what3words_language"] = result.get("language")
    sample["what3words_map_url"] = result.get("map")
    sample["what3words_nearest_place"] = result.get("nearestPlace")
    sample["what3words_country"] = result.get("country")
    sample["what3words_square_json"] = json.dumps(result.get("square"), sort_keys=True)
    sample["what3words_updated_at"] = utc_now()
    if sample.get("lat") is None:
        sample["lat"] = to_float(coordinates.get("lat"))
    if sample.get("lon") is None:
        sample["lon"] = to_float(coordinates.get("lng"))
    return sample


def enrich_sample_with_what3words(sample: dict[str, Any]) -> dict[str, Any]:
    if not what3words_config()["api_key"]:
        return sample
    try:
        if sample.get("what3words"):
            return apply_what3words_coordinates_result(
                sample, fetch_what3words_coordinates(sample["what3words"])
            )
        if sample.get("lat") is None or sample.get("lon") is None:
            return sample
        return apply_what3words_result(sample, fetch_what3words(sample["lat"], sample["lon"]))
    except requests.RequestException:
        return sample


def enrich_existing_samples_with_what3words(limit: int = 100) -> dict[str, Any]:
    if not what3words_config()["api_key"]:
        raise RuntimeError("Missing WHAT3WORDS_API_KEY")

    updated = 0
    skipped = 0
    errors: list[dict[str, str]] = []
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT sample_id, lat, lon
            FROM samples
            WHERE lat IS NOT NULL
              AND lon IS NOT NULL
              AND (what3words IS NULL OR what3words = '')
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        for row in rows:
            try:
                result = fetch_what3words(row["lat"], row["lon"])
                conn.execute(
                    """
                    UPDATE samples
                    SET what3words = ?,
                        what3words_language = ?,
                        what3words_map_url = ?,
                        what3words_nearest_place = ?,
                        what3words_country = ?,
                        what3words_square_json = ?,
                        what3words_updated_at = ?
                    WHERE sample_id = ?
                    """,
                    (
                        result.get("words"),
                        result.get("language"),
                        result.get("map"),
                        result.get("nearestPlace"),
                        result.get("country"),
                        json.dumps(result.get("square"), sort_keys=True),
                        utc_now(),
                        row["sample_id"],
                    ),
                )
                updated += 1
            except requests.RequestException as exc:
                skipped += 1
                errors.append({"sample_id": row["sample_id"], "error": str(exc)})
    return {"updated": updated, "skipped": skipped, "errors": errors[:10]}


def validate_existing_manual_what3words(limit: int = 100) -> dict[str, Any]:
    if not what3words_config()["api_key"]:
        raise RuntimeError("Missing WHAT3WORDS_API_KEY")

    validated = 0
    skipped = 0
    errors: list[dict[str, str]] = []
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT sample_id, what3words
            FROM samples
            WHERE what3words IS NOT NULL
              AND what3words != ''
              AND COALESCE(what3words_status, 'unvalidated') != 'validated'
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        for row in rows:
            try:
                result = fetch_what3words_coordinates(row["what3words"])
                coordinates = result.get("coordinates") or {}
                conn.execute(
                    """
                    UPDATE samples
                    SET lat = COALESCE(lat, ?),
                        lon = COALESCE(lon, ?),
                        what3words = ?,
                        what3words_source = 'manual',
                        what3words_status = 'validated',
                        what3words_language = ?,
                        what3words_map_url = ?,
                        what3words_nearest_place = ?,
                        what3words_country = ?,
                        what3words_square_json = ?,
                        what3words_updated_at = ?
                    WHERE sample_id = ?
                    """,
                    (
                        to_float(coordinates.get("lat")),
                        to_float(coordinates.get("lng")),
                        result.get("words") or row["what3words"],
                        result.get("language"),
                        result.get("map"),
                        result.get("nearestPlace"),
                        result.get("country"),
                        json.dumps(result.get("square"), sort_keys=True),
                        utc_now(),
                        row["sample_id"],
                    ),
                )
                validated += 1
            except requests.RequestException as exc:
                skipped += 1
                errors.append({"sample_id": row["sample_id"], "error": str(exc)})
    return {"validated": validated, "skipped": skipped, "errors": errors[:10]}


def upsert_sample(sample: dict[str, Any]) -> tuple[str, bool]:
    sample = enrich_sample_with_what3words(sample)
    now = utc_now()
    fields = [
        "sample_id",
        "collector_name",
        "sampling_date",
        "country",
        "site_name",
        "lat",
        "lon",
        "altitude_m",
        "gps_accuracy_m",
        "what3words",
        "what3words_source",
        "what3words_status",
        "what3words_language",
        "what3words_map_url",
        "what3words_nearest_place",
        "what3words_country",
        "what3words_square_json",
        "what3words_updated_at",
        "affiliation",
        "affiliation_other",
        "habitat_type",
        "habitat_other",
        "soil_types",
        "soil_type_other",
        "soil_ph",
        "climate_info",
        "depth_cm",
        "num_samples",
        "photo_sample",
        "notes",
        "raw_payload",
    ]
    with get_db() as conn:
        existing = conn.execute(
            "SELECT sample_id FROM samples WHERE sample_id = ?", (sample["sample_id"],)
        ).fetchone()
        conn.execute(
            f"""
            INSERT INTO samples ({", ".join(fields)}, created_at, updated_at)
            VALUES ({", ".join(["?"] * len(fields))}, ?, ?)
            ON CONFLICT(sample_id) DO UPDATE SET
              collector_name=excluded.collector_name,
              sampling_date=excluded.sampling_date,
              country=excluded.country,
              site_name=excluded.site_name,
              lat=excluded.lat,
              lon=excluded.lon,
              altitude_m=excluded.altitude_m,
              gps_accuracy_m=excluded.gps_accuracy_m,
              what3words=COALESCE(excluded.what3words, samples.what3words),
              what3words_source=COALESCE(excluded.what3words_source, samples.what3words_source),
              what3words_status=COALESCE(excluded.what3words_status, samples.what3words_status),
              what3words_language=COALESCE(excluded.what3words_language, samples.what3words_language),
              what3words_map_url=COALESCE(excluded.what3words_map_url, samples.what3words_map_url),
              what3words_nearest_place=COALESCE(excluded.what3words_nearest_place, samples.what3words_nearest_place),
              what3words_country=COALESCE(excluded.what3words_country, samples.what3words_country),
              what3words_square_json=COALESCE(excluded.what3words_square_json, samples.what3words_square_json),
              what3words_updated_at=COALESCE(excluded.what3words_updated_at, samples.what3words_updated_at),
              affiliation=excluded.affiliation,
              affiliation_other=excluded.affiliation_other,
              habitat_type=excluded.habitat_type,
              habitat_other=excluded.habitat_other,
              soil_types=excluded.soil_types,
              soil_type_other=excluded.soil_type_other,
              soil_ph=excluded.soil_ph,
              climate_info=excluded.climate_info,
              depth_cm=excluded.depth_cm,
              num_samples=excluded.num_samples,
              photo_sample=excluded.photo_sample,
              notes=excluded.notes,
              raw_payload=excluded.raw_payload,
              updated_at=excluded.updated_at
            """,
            [sample.get(field) for field in fields] + [now, now],
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO sample_taxa
              (sample_id, scientific_name, family, rank, source, created_at)
            VALUES (?, 'unidentified', NULL, 'unknown', 'provisional', ?)
            """,
            (sample["sample_id"], now),
        )
    return sample["sample_id"], existing is None


def kobo_config() -> dict[str, str | None]:
    return {
        "base_url": os.environ.get("KOBO_BASE_URL", "https://kf.kobotoolbox.org").rstrip("/"),
        "asset_uid": os.environ.get("KOBO_ASSET_UID"),
        "token": os.environ.get("KOBO_TOKEN") or os.environ.get("KOBOTOOLBOX_TOKEN"),
        "page_size": os.environ.get("KOBO_PAGE_SIZE", "1000"),
    }


def fetch_kobo_submissions() -> list[dict[str, Any]]:
    config = kobo_config()
    if not config["asset_uid"]:
        raise RuntimeError("Missing KOBO_ASSET_UID")

    url = (
        f"{config['base_url']}/api/v2/assets/{config['asset_uid']}/data/"
        f"?format=json&page_size={config['page_size']}"
    )
    headers = {}
    if config["token"]:
        headers["Authorization"] = f"Token {config['token']}"

    submissions: list[dict[str, Any]] = []
    while url:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, list):
            submissions.extend(item for item in payload if isinstance(item, dict))
            url = None
        else:
            results = payload.get("results", [])
            submissions.extend(item for item in results if isinstance(item, dict))
            url = payload.get("next")
    return submissions


def ingest_kobo_submissions() -> dict[str, Any]:
    submissions = fetch_kobo_submissions()
    created = 0
    updated = 0
    skipped = 0
    errors: list[dict[str, str]] = []
    for submission in submissions:
        try:
            sample = normalize_kobo_submission(submission)
            _, was_created = upsert_sample(sample)
            created += int(was_created)
            updated += int(not was_created)
        except Exception as exc:  # Keep one bad submission from blocking the ingest.
            skipped += 1
            errors.append({"error": str(exc), "submission": str(submission.get("_id") or submission.get("sample_id"))})
    return {
        "fetched": len(submissions),
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "errors": errors[:10],
    }


def build_sample_query(args: dict[str, str]) -> tuple[str, list[Any]]:
    joins = ""
    where = ["s.lat IS NOT NULL", "s.lon IS NOT NULL"]
    params: list[Any] = []

    if args.get("species") or args.get("family"):
        joins = "JOIN sample_taxa t ON t.sample_id = s.sample_id"
    if species := args.get("species"):
        where.append("LOWER(t.scientific_name) = LOWER(?)")
        params.append(species)
    if family := args.get("family"):
        where.append("LOWER(t.family) = LOWER(?)")
        params.append(family)
    if status := args.get("status"):
        where.append("s.status = ?")
        params.append(status)
    if affiliation := args.get("affiliation"):
        where.append("((',' || COALESCE(s.affiliation, '') || ',') LIKE ? OR LOWER(s.affiliation_other) LIKE LOWER(?))")
        params.extend([f"%,{affiliation},%", f"%{affiliation}%"])
    if country := args.get("country"):
        where.append("LOWER(s.country) = LOWER(?)")
        params.append(country)
    if habitat := args.get("habitat"):
        where.append("(s.habitat_type = ? OR LOWER(s.habitat_other) LIKE LOWER(?))")
        params.extend([habitat, f"%{habitat}%"])
    if soil_type := args.get("soil_type"):
        where.append("((',' || COALESCE(s.soil_types, '') || ',') LIKE ? OR LOWER(s.soil_type_other) LIKE LOWER(?))")
        params.extend([f"%,{soil_type},%", f"%{soil_type}%"])
    if ph_min := args.get("ph_min"):
        where.append("s.soil_ph >= ?")
        params.append(to_float(ph_min))
    if ph_max := args.get("ph_max"):
        where.append("s.soil_ph <= ?")
        params.append(to_float(ph_max))

    query = f"""
        SELECT DISTINCT s.*
        FROM samples s
        {joins}
        WHERE {" AND ".join(where)}
        ORDER BY s.sampling_date DESC, s.updated_at DESC
    """
    return query, params


@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/admin")
def admin_page():
    return render_template("admin.html")


@app.route("/webhook", methods=["POST"])
def receive_kobo_data():
    if not request.is_json:
        return jsonify({"status": "error", "message": "Expected JSON payload"}), 400
    sample = normalize_kobo_submission(request.get_json() or {})
    sample_id, created = upsert_sample(sample)
    return jsonify(
        {
            "status": "success",
            "sample_id": sample_id,
            "created": created,
            "message": "Data received and normalized",
        }
    )


@app.route("/api/samples")
def api_samples():
    query, params = build_sample_query(request.args)
    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        sample_ids = [row["sample_id"] for row in rows]
        taxa_by_sample: dict[str, list[sqlite3.Row]] = {sample_id: [] for sample_id in sample_ids}
        if sample_ids:
            placeholders = ",".join(["?"] * len(sample_ids))
            taxa_rows = conn.execute(
                f"SELECT * FROM sample_taxa WHERE sample_id IN ({placeholders}) ORDER BY source, scientific_name",
                sample_ids,
            ).fetchall()
            for taxon in taxa_rows:
                taxa_by_sample[taxon["sample_id"]].append(taxon)
    return jsonify([row_to_sample(row, taxa_by_sample[row["sample_id"]]) for row in rows])


@app.route("/api/species")
def api_species():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT DISTINCT scientific_name FROM sample_taxa ORDER BY scientific_name"
        ).fetchall()
    return jsonify([row["scientific_name"] for row in rows])


@app.route("/api/families")
def api_families():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT DISTINCT family FROM sample_taxa WHERE family IS NOT NULL AND family != '' ORDER BY family"
        ).fetchall()
    return jsonify([row["family"] for row in rows])


@app.route("/api/environment-summary")
def api_environment_summary():
    query, params = build_sample_query(request.args)
    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
    ph_values = [row["soil_ph"] for row in rows if row["soil_ph"] is not None]
    habitats = sorted({row["habitat_type"] for row in rows if row["habitat_type"]})
    countries = sorted({row["country"] for row in rows if row["country"]})
    soil_types = sorted({soil for row in rows for soil in split_csv(row["soil_types"])})
    return jsonify(
        {
            "sample_count": len(rows),
            "ph_min": min(ph_values) if ph_values else None,
            "ph_max": max(ph_values) if ph_values else None,
            "habitats": habitats,
            "countries": countries,
            "soil_types": soil_types,
        }
    )


@app.route("/api/admin/ingest/kobo", methods=["GET", "POST"])
def api_ingest_kobo():
    config = kobo_config()
    if not config["asset_uid"]:
        return (
            jsonify(
                {
                    "status": "missing_config",
                    "message": "Set KOBO_ASSET_UID and, if the project is private, KOBO_TOKEN.",
                    "base_url": config["base_url"],
                }
            ),
            400,
        )
    try:
        result = ingest_kobo_submissions()
    except requests.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else 502
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Kobo API request failed",
                    "status_code": status_code,
                    "detail": str(exc),
                }
            ),
            502,
        )
    except requests.RequestException as exc:
        return jsonify({"status": "error", "message": "Could not reach Kobo API", "detail": str(exc)}), 502
    except RuntimeError as exc:
        return jsonify({"status": "missing_config", "message": str(exc)}), 400
    return jsonify({"status": "success", **result})


@app.route("/api/admin/enrich/what3words", methods=["GET", "POST"])
def api_enrich_what3words():
    limit = to_int(request.args.get("limit")) or 100
    try:
        result = enrich_existing_samples_with_what3words(limit=limit)
    except RuntimeError as exc:
        return (
            jsonify(
                {
                    "status": "missing_config",
                    "message": str(exc),
                    "hint": "Add WHAT3WORDS_API_KEY to the deployment environment.",
                }
            ),
            400,
        )
    except requests.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else 502
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "What3Words API request failed",
                    "status_code": status_code,
                    "detail": str(exc),
                }
            ),
            502,
        )
    return jsonify({"status": "success", **result})


@app.route("/api/admin/validate/what3words", methods=["GET", "POST"])
def api_validate_what3words():
    limit = to_int(request.args.get("limit")) or 100
    try:
        result = validate_existing_manual_what3words(limit=limit)
    except RuntimeError as exc:
        return (
            jsonify(
                {
                    "status": "missing_config",
                    "message": str(exc),
                    "hint": "Add WHAT3WORDS_API_KEY to validate user-entered 3-word addresses.",
                }
            ),
            400,
        )
    except requests.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else 502
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "What3Words API request failed",
                    "status_code": status_code,
                    "detail": str(exc),
                }
            ),
            502,
        )
    return jsonify({"status": "success", **result})


@app.route("/curation")
def curation_form():
    with get_db() as conn:
        sample_ids = [
            row["sample_id"]
            for row in conn.execute("SELECT sample_id FROM samples ORDER BY updated_at DESC").fetchall()
        ]
    return render_template("curation.html", sample_ids=sample_ids)


@app.route("/submit_curation", methods=["POST"])
def submit_curation():
    sample_id = request.form.get("sample_id")
    scientific_name = (request.form.get("scientific_name") or "").strip()
    if not sample_id or not scientific_name:
        return jsonify({"status": "error", "message": "sample_id and scientific_name are required"}), 400

    entry = {
        "sample_id": sample_id,
        "scientific_name": scientific_name,
        "family": (request.form.get("family") or "").strip() or None,
        "rank": request.form.get("rank") or "species",
        "source": "curated",
        "identification_method": request.form.get("identification_method"),
        "gene_marker": request.form.get("gene_marker"),
        "genetic_sequence_id": request.form.get("genetic_sequence_id"),
        "genbank_accession": request.form.get("genbank_accession"),
        "curator_name": request.form.get("curator_name"),
        "validation_date": datetime.now(timezone.utc).date().isoformat(),
        "created_at": utc_now(),
    }
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO sample_taxa
              (sample_id, scientific_name, family, rank, source, identification_method,
               gene_marker, genetic_sequence_id, genbank_accession, curator_name,
               validation_date, created_at)
            VALUES
              (:sample_id, :scientific_name, :family, :rank, :source, :identification_method,
               :gene_marker, :genetic_sequence_id, :genbank_accession, :curator_name,
               :validation_date, :created_at)
            ON CONFLICT(sample_id, scientific_name, family, source) DO UPDATE SET
              rank=excluded.rank,
              identification_method=excluded.identification_method,
              gene_marker=excluded.gene_marker,
              genetic_sequence_id=excluded.genetic_sequence_id,
              genbank_accession=excluded.genbank_accession,
              curator_name=excluded.curator_name,
              validation_date=excluded.validation_date
            """,
            entry,
        )
    return render_template("success.html", entry=entry)


@app.route("/api/samples/<sample_id>/status", methods=["POST"])
def update_sample_status(sample_id: str):
    status = (request.get_json(silent=True) or {}).get("status")
    if status not in {"pending", "validated", "rejected"}:
        return jsonify({"status": "error", "message": "Invalid status"}), 400
    with get_db() as conn:
        conn.execute(
            "UPDATE samples SET status = ?, updated_at = ? WHERE sample_id = ?",
            (status, utc_now(), sample_id),
        )
    return jsonify({"status": "success", "sample_id": sample_id, "sample_status": status})


init_db()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5050"))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1", use_reloader=False)
