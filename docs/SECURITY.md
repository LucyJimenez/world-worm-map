# Security

- `wwm/.env` must never be committed. It is ignored by Git and stores local secrets such as `KOBO_TOKEN` and optional `WHAT3WORDS_API_KEY`.
- GitHub Pages uses the repository secret `KOBO_TOKEN` to generate a sanitized static dataset during deployment.
- The public static dataset excludes What3Words values, collector names, notes, raw Kobo payloads, original Kobo sample IDs, `kobo_uuid`, and `kobo_id`.
- Current API-key authentication is development-only. `API_KEY_ADMIN` and `API_KEY_CURATOR` are placeholders and must be replaced before production backend deployment.
- Admin ingestion endpoints must be protected outside development.
- What3Words is treated as internal sampling metadata. GPS/PostGIS coordinates remain the canonical map location.
- Future production versions need explicit data governance for location precision, contributor attribution, public/private fields, and curator roles.
