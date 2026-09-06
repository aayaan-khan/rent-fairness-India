# Data Quality Report

## Source
Kaggle "New Delhi Rental Listings" (June 2020), 17,890 raw rows, Delhi city only.

## Cleaning steps
1. Outlier removal: price and size trimmed to 1st-99th percentile
   - Price outlier filter: 290 rows dropped
   - Size outlier filter: 303 rows dropped
   - Combined (both filters): 91 rows dropped in both
   - Total: 502 rows dropped (2.8%)
   - Justification: [your reasoning from Step 3a]

## Locality structure
- 750 unique raw locality names (street/block-level granularity, not casing noise)
- Median listings per locality: 2; 63% of localities have <5 listings
- Two-tier design: locality_name (fine-grained) + locality_group (suburbName, ~10-12 reliable groups)
- is_sparse flag (< 5 listings) added to localities table

## Known limitations
- No furnishing, amenities, or floor data in this source
- Data is from 2020 — temporal drift vs. current rents not yet corrected
- Scope currently Delhi only; Noida/Ghaziabad pending additional data source