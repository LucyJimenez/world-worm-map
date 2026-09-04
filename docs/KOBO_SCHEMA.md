# KoboToolbox Field Contract

This document defines the ingestion contract between KoboToolbox
and the WWM ingestion pipeline.

## Core fields used by the current beta

- `gps_coordinates`
- `site_name`
- `sample_id`
- `sampling_date`
- `country`
- `affiliation`
- `affiliation_other`
- `habitat_type`
- `soil_type`
- `soil_ph`
- `depth_cm`
- `num_samples`
- `tube_id`
- `what3words` (optional internal location reference)

Taxonomic species and family values are not treated as required Kobo inputs in the current beta ingestion path. Newly ingested Kobo records receive a provisional `unidentified` species entry and can be curated later through API endpoints or future curator tooling.

## Notes

- affiliation may contain multiple values
- affiliation_other is used when "Other" is selected
- missing species entries create "unidentified" provisional species
- country should be modeled as an ISO-3166 select list (recommended alpha-2 codes)
- provenance fields on `samples`:
  - `data_source` (`kobo`, `seed`, `manual`)
  - `kobo_uuid`
  - `kobo_id`
  - `kobo_submission_time`

Last synchronized: 2026-09-04
Kobo Asset UID: a8Rvu5KasYeAfsa2GfFppG
