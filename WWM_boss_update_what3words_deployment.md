# WWM update: What3Words markers and deployable demo

Hi,

Yes, we can integrate What3Words as an additional user-entered geographical marker for WWM sampling sites.

The implementation keeps KoboToolbox as the main data-entry workflow. Contributors enter the three-word address in an additional Kobo field, while latitude and longitude remain the canonical scientific coordinates whenever GPS is available.

## What the prototype now supports

- Import sampling sites from KoboToolbox.
- Store sampling coordinates, country, habitat, soil type, pH, depth and number of sub-samples.
- Display points on a Leaflet map.
- Filter records by species, family, status, country, habitat, soil type and pH range.
- Import a user-entered What3Words field from KoboToolbox.
- Validate the What3Words address when a `WHAT3WORDS_API_KEY` is configured.
- Use validated What3Words to recover coordinates only if GPS is missing.
- Show the What3Words address in each map popup, with a direct link to the What3Words map.

## Why this is useful

For scientific analysis, WWM will still prioritize GPS coordinates. For humans in the field, What3Words gives a compact marker such as:

```text
///word.word.word
```

This can make it easier to communicate or revisit a sampling site, especially when site names are ambiguous.

## Deployment plan

The project can be shared through a private GitHub repository and deployed as a small Python web service.

Recommended demo deployment:

- GitHub private repository for code review and collaboration.
- Render, Railway or Fly.io for a live web URL.
- Environment variables configured securely in the hosting dashboard:
  - `KOBO_BASE_URL`
  - `KOBO_ASSET_UID`
  - `KOBO_TOKEN`
  - `WHAT3WORDS_API_KEY`
  - `WHAT3WORDS_LANGUAGE`

Tokens and local data are excluded from GitHub.

## Important note

What3Words is a proprietary service and requires an API key for validation. It should be treated as a convenience layer, not as a replacement for open coordinate data.
