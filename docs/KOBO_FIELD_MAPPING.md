# Kobo Field Mapping

Source form: `wwm/forms/kobo_form.xml`

This document maps Kobo fields to backend ingestion normalization and storage.

| Kobo field name | Backend column mapping | Required | Transformation / rule |
|---|---|---|---|
| `group_ih2au74/sample_id` | `samples.external_sample_id` | Yes | Preferred identifier. Fallback: `_uuid`, then `_id` if missing. |
| `group_kw39a24/site_name` | `samples.site_name` | No | Trim quotes/whitespace. Default `"Unknown site"` when empty. |
| `group_ih2au74/collector_name` | `samples.submitted_by` | Yes | Trim string. Fallback key: `collector`. |
| `group_ih2au74/sampling_date` | `samples.sampling_date` | Yes | Parse date. Fallback: `_submission_time` date component. |
| `group_kw39a24/gps_coordinates` | `samples.latitude`, `samples.longitude`, `samples.geom` | Yes | Parse geopoint from `"lat lon alt acc"` or `"lat,lon,alt,acc"`; store PostGIS Point SRID 4326. |
| `group_ih2au74/country` | `samples.country` | Yes | Stored as submitted code/value. Supports ISO-3166 dropdown values. |
| `group_jy8zq69/habitat_type` | `samples.raw_payload.habitat_type` | Yes | Stored in raw payload. |
| `group_jy8zq69/soil_type` | `samples.raw_payload.soil_type` | No | Stored in raw payload. |
| `group_jy8zq69/soil_ph` | `samples.raw_payload.soil_ph` | No | Stored in raw payload as string/decimal text. |
| `group_ga0dq77/depth_cm` | `samples.raw_payload.depth_cm` | No | Stored in raw payload as numeric text. |
| `group_ga0dq77/num_samples` | `samples.raw_payload.num_samples` | Yes | Stored in raw payload as numeric text. |
| `group_ga0dq77/tube_id` | `samples.raw_payload.tube_id` | Yes | Stored in raw payload. |
| `group_ih2au74/notes` | `samples.notes` | No | Fallback key: `additional_notes`. |
| `group_ih2au74/affiliation` | `sample_affiliations` links + `affiliations` records | Yes | Parse select_multiple from list/space/comma/semicolon; slugify values; create missing affiliations. |
| `group_ih2au74/affiliation_other` | `samples.raw_payload.affiliation_other` + `sample_affiliations` link | Conditional | If `other` selected and text provided, create/link slug from text. If affiliation list empty but text exists, create/link from text. |
| `group_jy8zq69/climate_info` | `samples.raw_payload.climate_info` | No | Stored in raw payload (read-only field in form). |
| `group_ga0dq77/photo_sample` | `samples.raw_payload.photo_sample` | No | Attachment reference captured in raw payload. |
| `start` | `samples.raw_payload.start` | Auto | Stored in raw payload. |
| `end` | `samples.raw_payload.end` | Auto | Stored in raw payload. |
| `today` | `samples.raw_payload.today` | Auto | Stored in raw payload. |
| `instance_uuid` | `samples.raw_payload.instance_uuid` | No | Stored in raw payload. |
| `meta/instanceID` | `samples.raw_payload.meta_instance_id` | Auto | Stored in raw payload. |

## Ingestion compatibility notes

- Idempotency key remains `samples.external_sample_id`.
- Every new sample creates one provisional species record: `species_name = "unidentified"`.
- Unknown or extra Kobo fields are preserved in `samples.raw_payload.kobo` for traceability.
