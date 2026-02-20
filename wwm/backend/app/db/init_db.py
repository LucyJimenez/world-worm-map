from sqlalchemy import text

from app.db.base import Base
from app.db.session import engine
from app.models import models  # noqa: F401


def init_db() -> None:
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        connection.execute(text("ALTER TABLE IF EXISTS samples ADD COLUMN IF NOT EXISTS country VARCHAR(120)"))
    Base.metadata.create_all(bind=engine)
