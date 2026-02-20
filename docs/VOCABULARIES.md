# Controlled Vocabularies

This document defines controlled vocabularies used by the WWM Kobo form.

## habitat_type_list

- `agricultural_field`: Agricultural field
- `forest`: Forest
- `grassland`: Grassland
- `wetland`: Wetland
- `urban`: Urban / built environment
- `desert`: Desert / arid
- `freshwater_margin`: Freshwater margin (river/lake)
- `coastal`: Coastal
- `tundra`: Tundra / alpine
- `other`: Other

## soil_type_list

- `sandy`: Sandy
- `clay`: Clay
- `silt`: Silt
- `loam`: Loam
- `peat`: Peat / organic-rich
- `chalk`: Chalky / calcareous
- `volcanic`: Volcanic
- `mixed`: Mixed / unknown
- `other`: Other

## Rationale

Controlled vocabularies reduce ambiguity in field submissions, improve query/filter reliability, and simplify downstream analytics by enforcing stable machine-readable codes.

## Country field

The `country` question uses `select_one country_list` with ISO-3166 alpha-2 codes.

- Choice `name` values are ISO alpha-2 codes (for example `DE`, `CH`, `CO`).
- Choice labels are English country names.
- Full list exported to `wwm/forms/country_list_iso3166.csv`.
