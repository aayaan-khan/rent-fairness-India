# EDA Findings — Phase 3

## 1. Price distribution & modeling implication
- Price distribution is right-skewed (see `docs/eda_distributions.png`).
- Implication: model `log(price)` rather than raw price in Phase 4, since a skewed
  target violates linear-model assumptions and trains less stably even for
  tree-based models.

## 2. What correlates with price (citywide)
| Feature | Correlation with price |
|---|---|
| size_sq_ft | 0.760 |
| bedrooms | 0.584 |
| price_per_sqft | 0.537 |
| aiims_dist_km | -0.111 |
| airport_dist_km | -0.024 |
| ndrlw_dist_km | -0.017 |
| closest_metro_km | 0.013 |

- `size_sq_ft` shows the strongest linear correlation with price citywide.
  (Note: correlation ≠ trained feature importance — a gradient-boosted model in
  Phase 4 may weight features differently once interactions are captured.)
- Distance features show weak-to-negligible citywide linear correlation with
  price — but see Finding 4 below, this is misleading in isolation.

## 3. Locality-group price-per-sqft ranking (non-sparse groups only)
| Locality group | Mean price/sqft | Listings |
|---|---|---|
| Delhi West | 39.4 | 260 |
| Delhi North | 31.2 | 161 |
| Delhi South | 29.8 | 3,609 |
| South West Delhi | 27.7 | 67 |
| Delhi Central | 26.6 | 2,643 |
| North Delhi | 26.2 | 1,215 |
| North West Delhi | 25.3 | **6 — too small to trust, flagged as group-sparse** |
| Rohini | 24.6 | 261 |
| Other | 24.3 | 1,994 |
| West Delhi | 21.7 | 2,159 |
| Delhi East | 21.3 | 1,829 |
| Dwarka | 18.7 | 2,360 |

- Added a group-level sparsity flag (`count < 30`) separate from the existing
  locality_name-level `is_sparse` flag, since a locality_group can be
  statistically unreliable even when built from many well-populated individual
  localities is not the case here — North West Delhi (n=6) is the one clear
  exception and should be excluded from any ranked comparison.

## 4. Metro distance vs. price is confounded by locality group — key non-obvious finding
Citywide, distance to metro shows almost no linear correlation with price
(r = 0.013). But when checked **within** each locality group, the relationship
is inconsistent and sometimes reverses:

| Locality group | Corr(price, metro distance) within group |
|---|---|
| North West Delhi* | +0.783 |
| Delhi West | +0.431 |
| South West Delhi | +0.346 |
| Delhi East | +0.162 |
| Delhi Central | +0.068 |
| West Delhi | +0.085 |
| Dwarka | +0.006 |
| Other | -0.041 |
| North Delhi | -0.065 |
| Rohini | -0.206 |
| Delhi North | -0.225 |
| Delhi South | -0.263 |

*North West Delhi n=6, unreliable — noted, not used to draw conclusions.

**Interpretation:** in some groups (Delhi South, Delhi North, Rohini) closer
proximity to a metro station is associated with higher price, as expected.
In others (Delhi West, South West Delhi) the relationship reverses — farther
listings are pricier. In Dwarka, metro distance has essentially no relationship
with price at all.

This means metro distance is **not a universal price driver** — its apparent
citywide weak correlation is masking locality-specific effects that partly
cancel out. This is a case of confounding: locality already captures most of
whatever metro proximity would otherwise explain, and where it doesn't, other
factors (property type mix, size mix within that group) may dominate instead.
This argues for keeping locality features and metro distance both in the
model, and letting a tree-based model capture the interaction, rather than
treating metro distance as an independent, always-positive price driver.

## 5. Property type × bedroom count interaction with price-per-sqft
| Bedrooms | Apartment | Independent Floor | Independent House | Villa |
|---|---|---|---|---|
| 1 | 23.3 | 22.5 | 23.0 | 28.3 |
| 2 | 20.6 | 23.0 | 21.3 | 22.0 |
| 3 | 18.3 | 25.3 | 23.7 | 22.2 |
| 4 | 17.4 | 30.6 | 20.0 | 21.1 |
| 5 | 22.1 | 20.6 | 41.7 | 34.7 |
| 6 | 22.4 | 33.8 | 34.3 | — |

**Interpretation:** Apartments get *cheaper* per sqft as bedroom count rises
(1BHK ~23.3 → 4BHK ~17.4) — consistent with a "bulk space discount" typical of
standardized apartment inventory. Independent Houses and Independent Floors
show the opposite pattern at the high end (5-6 BHK spiking to 34-42/sqft),
consistent with these being large, low-supply luxury/private properties
commanding a premium rather than a bulk discount.

This is a real interaction effect (property_type × bedrooms), not something
captured by either feature independently — a tree-based model should be able
to learn this split naturally, whereas a plain linear model would need this
interaction engineered explicitly.

## 6. Citywide property profile (fill in after running unfiltered describe())
- Total listings analyzed: [[ ]]
- Property type breakdown: [[ ]]
- Average size: [[ ]] sq ft
- Average bedrooms: [[ ]]
- Size range: [[ ]] – [[ ]] sq ft

## Known caveats carried into Phase 4
- Correlation figures here are linear (Pearson) only — nonlinear relationships
  may exist that these don't capture; that's part of the case for a
  gradient-boosted model over plain linear regression.
- North West Delhi group (n=6) excluded from all group-level interpretive
  claims due to sample size.
- Dwarka's low price-per-sqft was checked against size/bedroom/property-type
  mix and does not appear to be explained by unit-size differences alone —
  worth flagging as unexplained/needing more investigation rather than
  asserting a cause.
  