# World Worm Map

World Worm Map is a prototype for collecting and displaying nematode sampling records.

Current workflow:

1. Contributors submit sampling records through KoboToolbox.
2. WWM imports Kobo submissions into the web app.
3. WWM displays sites on a map with taxon, habitat, soil and pH filters.
4. Users can optionally enter a What3Words address in Kobo as an additional site reference.
5. WWM can validate entered What3Words addresses when a `WHAT3WORDS_API_KEY` is configured.

The application code is in `wwm_app/`.

## Local app

See `wwm_app/README.md`.

## Deployment

This repository includes `render.yaml` for a Render Blueprint deployment.

Secrets must be configured in the hosting dashboard, not committed to GitHub:

- `KOBO_ASSET_UID`
- `KOBO_TOKEN`
- `WHAT3WORDS_API_KEY`

## Important

Do not commit:

- `.env`
- Kobo tokens
- What3Words API keys
- local SQLite databases
- `.venv`

