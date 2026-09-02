# GitHub release checklist

## Before pushing

- Confirm `.env` is not committed.
- Confirm `wwm_app/data/` is not committed.
- Confirm `.venv/` is not committed.
- Keep the repository private while Kobo data and deployment details are still being reviewed.

## Suggested commands

```bash
git init
git add README.md GITHUB_RELEASE_CHECKLIST.md WWM_boss_update_what3words_deployment.md WWM_kobo_what3words_field.md render.yaml .gitignore wwm_app
git status
git commit -m "Prepare WWM prototype with Kobo and What3Words support"
git branch -M main
git remote add origin git@github.com:YOUR_ORG_OR_USER/world-worm-map.git
git push -u origin main
```

## Render deployment

1. Open Render.
2. Create a new Blueprint from the GitHub repository.
3. Confirm it detects `render.yaml`.
4. Add secret environment variables:
   - `KOBO_ASSET_UID`
   - `KOBO_TOKEN`
   - `WHAT3WORDS_API_KEY`
5. Deploy.
6. Open the deployed app URL.
7. Open `/admin`.
8. Click `Import Kobo samples`.
9. Click `Validate entered W3W` after users have submitted What3Words values in Kobo.

## Kobo form update

Add the optional field described in `WWM_kobo_what3words_field.md`.
