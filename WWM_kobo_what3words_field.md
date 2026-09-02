# KoboToolbox field: What3Words

Add this optional field to the WWM KoboToolbox form.

| type | name | label | hint | required |
|---|---|---|---|---|
| text | what3words | What3Words location reference | Optional. Enter the three words for the sampling site, for example filled.count.soap. Do not include personal addresses. | no |

Recommended placement: immediately after the GPS/geopoint field.

WWM will import this field as a manual location reference. If `WHAT3WORDS_API_KEY` is configured, WWM can validate the three-word address and, if GPS is missing, use it to fill approximate coordinates.

Important: GPS latitude/longitude should still be collected whenever possible because it remains the canonical scientific coordinate for GIS and environmental analyses.

