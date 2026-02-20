"""Manual Kobo ingestion trigger script for local testing."""

from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.services.kobo_ingest import ingest_kobo_submissions


def main():
    init_db()
    db = SessionLocal()
    try:
        result = ingest_kobo_submissions(db, actor="manual_script")
        print(result)
    finally:
        db.close()


if __name__ == "__main__":
    main()
