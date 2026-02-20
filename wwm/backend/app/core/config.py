from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("/app/.env", "wwm/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "World Worm Map"
    environment: str = "development"
    database_url: str = "postgresql+psycopg2://wwm:wwm@db:5432/wwm"

    api_key_admin: str = "admin-key"
    api_key_curator: str = "curator-key"

    kobo_base_url: str = "https://eu.kobotoolbox.org"
    kobo_asset_uid: str = "a8Rvu5KasYeAfsa2GfFppG"
    kobo_token: str = ""

    enable_real_ncbi_validation: bool = False
    ncbi_api_base: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

    ingest_hour: int = 2
    ingest_minute: int = 0
    cors_origins: str = "http://localhost:8080,http://127.0.0.1:8080,http://localhost:8000"


settings = Settings()
