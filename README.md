# Is My Rent Fair? — India

A data science project that predicts fair market rent for residential properties and flags listings that are significantly over- or under-priced relative to comparable units in the same locality.

🔗 **Live demo:** https://rent-fairness-india.streamlit.app/

<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/5f389590-75d2-4ea6-ac3e-3887ffcfe449" />

<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/33953271-d005-4088-a2e1-92dd365f2d87" />

---

## Table of Contents
Results at a Glance
Overview
What It Does
Methodology
Data
Data Engineering
Data Cleaning
Modeling
Key Findings
Known Limitations
Tech Stack
Project Structure
Running Locally
Next Steps
Acknowledgments
License
Contact

## Results at a Glance
	Baseline (Linear Regression)	Final Model (LightGBM)
R² (log scale)	0.728	0.861
MAE	₹7,512 (35.8% of median price)	₹4,989 (23.8% of median price)
Median % error	—	12.7%

~40% reduction in typical prediction error over baseline. Clears the project's original success criteria (R² 0.65–0.80).

Read honestly: a 23.8% MAE means a fairness verdict is directional, not a precise appraisal — e.g. a ₹30,000/month listing could reasonably fall anywhere in a ~₹23,000–37,000 "fair" band. The app states this explicitly rather than implying false precision (see Known Limitations).

## Overview

Current scope: Delhi (17,322 listings after cleaning), sourced from a public Kaggle rental dataset. Noida and Ghaziabad are the next planned expansion — deliberately deferred rather than rushed, since the major real-estate portals (99acres, MagicBricks, Housing.com) prohibit scraping in their Terms of Service, and no free, compliant developer API exists for individual/student use. Rather than circumvent that, this project sources data through public/compliant channels only, and is scoped honestly around that constraint.

Business question: given a property's locality, size, bedroom count, property type, and proximity to key landmarks, what should it rent for — and how far off is a given asking price from that estimate?

## What It Does
Predicts fair rent using a LightGBM regression model trained on locality, size, bedrooms, property type, and distance to metro/airport/AIIMS/New Delhi Railway Station.
Flags listings as Fair / Somewhat / Significantly over- or under-priced, using confidence bands derived from the model's own measured error (median absolute % error) rather than an arbitrary round-number cutoff.
Explains individual predictions with SHAP, so the tool can say not just "this is overpriced" but why — which features pushed the estimate up or down, and by how much.
Interactive dashboard (Streamlit): search/filter listings by locality, BHK, and budget; enter your own listing's details to check its fairness; browse locality-level price trends.

## Methodology
Data
Source: Kaggle "New Delhi Rental Listings" (2020), ~17,890 raw rows, Delhi city only.
A small personally-collected sample of live listings was gathered as a private sanity-check during scoping, but was not included in the training/production dataset — it informed judgment calls only, to keep data provenance auditable and honest.

## Data Engineering
Normalized relational schema in SQLite: separate listings, localities, and an intentionally-empty amenities table (placeholder — this dataset has no amenity data; the schema is ready to populate once a richer source is added).
Two-tier locality structure: locality_name (750 raw, street/block-level names — median of just 2 listings each) paired with a coarser locality_group (~12 reliable groups, derived from the dataset's suburb field) for statistically meaningful aggregation. A sparsity flag (is_sparse, <5 listings) marks fine-grained localities too thin to trust individually.
Analytical SQL used in EDA: window functions (PARTITION BY, NTILE) for within-group price ranking, CTEs for group-level summary stats.

## Data Cleaning

(fully logged — see docs/data_quality_report.md)

Percentile-based outlier trimming (1st–99th percentile) on price and size: 502 rows dropped (2.8%).
Two additional data artifacts found through model error diagnostics, not upfront EDA: a capped size_sq_ft placeholder value (exactly 4500, spanning ₹55,000–215,000 in price — clearly a form-field cap, not a real measurement; 60 rows dropped) and unrealistic bedroom-density rows (sqft/bedroom < 150; 6 rows dropped). Called out deliberately here because catching data issues via model behavior, not just univariate EDA, reflects a more mature workflow.
Modeling
Target: log(price), chosen after EDA showed a right-skewed price distribution.
Split: stratified random split by locality_group (80/20) — a deliberate middle ground between a naive random split (risks the model "memorizing" a seen locality) and a full group-holdout split (too aggressive given only ~12 reliable groups).
Baseline — Linear Regression: R² 0.728 (log scale), MAE ₹7,512 (35.8% of median price).
Final model — LightGBM: R² 0.861 (log scale), MAE ₹4,989 (23.8% of median price), median % error 12.7%.
Train/test R² gap (0.913 vs. 0.861) checked and judged an acceptable, mild degree of overfitting for a 500-tree gradient-boosted model.
Explainability: SHAP TreeExplainer used both globally (feature importance) and per-listing (individual prediction breakdown). Notably, SHAP surfaced that distance to AIIMS and New Delhi Railway Station carry more predictive weight than raw metro distance — a nonlinear interaction effect the simple linear-correlation analysis in EDA didn't fully capture.
Fairness score: predicted-vs-actual deviation, bucketed using confidence bands set at 1× and 2× the model's own median error — a data-driven threshold rather than a round-number guess, explicitly checked against the resulting bucket distribution before being finalized.

## Key Findings
Size is the strongest single price driver, both by raw correlation (r = 0.76) and by SHAP importance — consistent across both analytical approaches.
Metro proximity is not a universal price driver. Citywide correlation between metro distance and price is nearly zero (r = 0.013), but this masks a locality-specific effect: within some locality groups (Delhi South, Delhi North, Rohini) proximity to the metro does predict higher price as expected; in others (Delhi West, South West Delhi) the relationship reverses. This is a confounding effect — locality group captures most of what metro proximity would otherwise explain.
Apartments and independent houses/floors price differently at scale. Apartments get cheaper per sqft as bedroom count increases (a "bulk space discount," ~₹23/sqft for 1BHK down to ~₹17/sqft for 4BHK) — but large Independent Houses/Floors (5–6BHK) spike back up to ₹34–42/sqft, consistent with these being low-supply, luxury-tier private properties commanding a premium rather than a bulk discount. This is a genuine interaction effect, not something either feature explains independently.
Model diagnostics caught data quality issues invisible to standard outlier filtering — including one likely data-entry error (a listing priced at ₹180,000 against a peer-group mean of ₹23,417 for effectively identical properties), found by tracing an anomalously large SHAP prediction error back to its comparable listings.
## Known Limitations
No furnishing, amenities, or floor-level data in the current source — a real gap, not glossed over. The amenities table exists in the schema specifically so this can be populated without a redesign once available.
Dataset is from 2020; absolute rent estimates should be read as directionally indicative rather than current-market-precise. A future iteration would apply a locality-level inflation/drift correction.
Currently Delhi-only. Noida and Ghaziabad are the explicit next milestone, pending a compliant data source for those cities.
Coarse geographic resolution. Only ~12 reliable locality groups exist after accounting for data sparsity — fairness verdicts are meaningful at that resolution, not at the street/block level the raw locality_name field suggests.
~24% typical error margin. This is a directional signal, not a precise appraisal — see the callout in Results at a Glance. The live app surfaces this alongside every prediction.
Correlation/SHAP analysis presented here is based on this specific feature set — a richer feature set (amenities, condition, floor) would likely shift some of these findings.
Tech Stack

Python · pandas · SQLite (window functions, CTEs) · scikit-learn · LightGBM · SHAP · Streamlit · joblib

## Project Structure
rent-fairness-india/
├── app.py                  # Streamlit dashboard
├── src/build_db.py         # Data cleaning + SQLite schema build
├── notebooks/              # EDA, SQL analysis, modeling notebooks
├── db/rentals.db           # SQLite database
├── models/                 # Saved LightGBM model + supporting artifacts
├── data/processed/         # Fairness-scored listings (dashboard input)
└── docs/                   # Data quality report, EDA findings, charts

## Running Locally
bash
git clone https://github.com/aayaan-khan/rent-fairness-india.git
cd rent-fairness-india
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
streamlit run app.py

## Next Steps
Add Noida/Ghaziabad data and re-validate the model across a genuinely multi-city scope.
Source or collect furnishing/amenities/floor data to close the current biggest feature gap.
Apply a temporal price-drift correction to account for the 2020 dataset's age.
Calibrate fairness-band thresholds against real user feedback rather than statistical convention alone.
Replace Delhi-specific landmark distances (AIIMS, New Delhi Railway) with generalizable, city-agnostic features (distance to nearest transit hub, distance to CBD, city-tier) ahead of geographic expansion.

## Acknowledgments

Dataset: "New Delhi Rental Listings" via Kaggle (2020).

## License

MIT — or specify your preferred license.

## Contact

Built by _Aayaan Khan_ as an independent data science portfolio project. GitHub (https://github.com/aayaan-khan) · LinkedIn(https://www.linkedin.com/in/aayaan-khan-170b9a276/) · Email (khanaayaan422@gmail.com)
