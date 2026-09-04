# Deployment

## Local

```bash
docker compose up --build
```

Local app and API:

```text
http://localhost:8000
```

## Public beta

The public beta frontend is deployed with GitHub Actions and GitHub Pages:

```text
https://lucyjimenez.github.io/world-worm-map/
```

The workflow `.github/workflows/pages.yml` runs on pushes to `main`, hourly, and manually through `workflow_dispatch`.

The public deployment is static. It exports sanitized Kobo samples into `wwm/frontend/demo-samples.json` and appends beta reference samples from `wwm/frontend/reference-samples.json`.

## Production

- Configure environment variables
- Deploy containers
- Enable scheduled ingestion

Production backend hosting is planned but not implemented in the beta.
