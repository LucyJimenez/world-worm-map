from sqlalchemy import text

from app.db.base import Base
from app.db.session import engine
from app.models import models  # noqa: F401


def init_db() -> None:
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        connection.execute(text("ALTER TABLE IF EXISTS samples ADD COLUMN IF NOT EXISTS country VARCHAR(120)"))
        connection.execute(
            text("ALTER TABLE IF EXISTS samples ADD COLUMN IF NOT EXISTS data_source VARCHAR(20) NOT NULL DEFAULT 'kobo'")
        )
        connection.execute(text("ALTER TABLE IF EXISTS samples ADD COLUMN IF NOT EXISTS kobo_uuid VARCHAR(255)"))
        connection.execute(text("ALTER TABLE IF EXISTS samples ADD COLUMN IF NOT EXISTS kobo_id VARCHAR(255)"))
        connection.execute(text("ALTER TABLE IF EXISTS samples ADD COLUMN IF NOT EXISTS kobo_submission_time TIMESTAMP"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_samples_data_source ON samples (data_source)"))
        connection.execute(
            text(
                "UPDATE samples SET data_source = 'seed' "
                "WHERE data_source = 'kobo' "
                "AND (external_sample_id LIKE 'SEED-%' OR submitted_by = 'demo@example.org')"
            )
        )
    Base.metadata.create_all(bind=engine)
