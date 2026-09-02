# World Worm Map prototype

WWM is a small Flask prototype for mapping nematode sampling records from KoboToolbox. It stores normalized sampling records locally, displays them on a Leaflet map, and supports filtering by species, family, status, country, habitat, soil type and pH range.

## Current integrations

- KoboToolbox import via API v2.
- User-entered What3Words location reference from KoboToolbox.
- Optional What3Words validation and coordinate lookup when an API key is configured.
- Manual curation page for species, family and molecular metadata.

## Local run

```bash
cd wwm_app
python -m venv .venv
./.venv/bin/pip install -r requirements.txt
cp .env.example .env
./.venv/bin/python seed_demo_data.py
./.venv/bin/python app.py
```

Open:

```text
http://127.0.0.1:5050
```

## Environment variables

```bash
KOBO_BASE_URL=https://eu.kobotoolbox.org
KOBO_ASSET_UID=your_kobo_asset_uid
KOBO_TOKEN=your_private_project_token
KOBO_PAGE_SIZE=1000
WHAT3WORDS_API_KEY=your_what3words_api_key
WHAT3WORDS_LANGUAGE=en
```

Do not commit `.env`, Kobo tokens, What3Words keys or local SQLite data.

## Deploy from GitHub

Recommended quick demo path:

1. Push this project to a private GitHub repository.
2. In Render, create a new Blueprint from the repository. The root `render.yaml` already defines the service.
3. Add the secret environment variables when Render asks for them:
   - `KOBO_ASSET_UID`
   - `KOBO_TOKEN`
   - `WHAT3WORDS_API_KEY`

Manual Render setup also works:

1. Create a Python web service.
2. Set the service root directory to `wwm_app`.
3. Use build command:

```bash
pip install -r requirements.txt
```

4. Use start command:

```bash
gunicorn app:app
```

5. Add environment variables in the host dashboard.
6. Open `/admin` on the deployed URL and use:
   - `Import Kobo samples`
   - `Validate entered W3W`

## Scientific note

KoboToolbox remains the data-entry workflow. What3Words is stored as an additional user-entered location reference for human-readable site communication. WWM keeps latitude/longitude as the canonical scientific coordinate whenever GPS is available. If GPS is missing, a validated What3Words address can be used to recover approximate coordinates.

## KoboToolbox field to add

Add this optional field to the Kobo form:

```text
type: text
name: what3words
label: What3Words location reference
hint: Optional. Enter the three words for the sampling site, for example filled.count.soap. Do not include personal addresses.
required: no
```
