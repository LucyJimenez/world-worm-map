# KoboToolbox Field Contract

This document defines the ingestion contract between KoboToolbox
and the WWM ingestion pipeline.

## Required fields

gps_coordinates
site_name
sampling_date
affiliation
affiliation_other
species_name (optional)

## Notes

- affiliation may contain multiple values
- affiliation_other is used when "Other" is selected
- missing species entries create "unidentified" provisional species
- country should be modeled as an ISO-3166 select list (recommended alpha-2 codes)

Last synchronized: 2026-02-20
Kobo Asset UID: a8Rvu5KasYeAfsa2GfFppG

