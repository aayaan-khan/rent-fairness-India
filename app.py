import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Is My Rent Fair? — India", layout="wide")
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "processed" / "fairness_scored_listings.csv"

@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH)

df = load_data()
import joblib
import numpy as np

MODEL_DIR = BASE_DIR / "models"

@st.cache_resource
def load_model():
    model = joblib.load(MODEL_DIR / "lgb_rent_model.pkl")
    features = joblib.load(MODEL_DIR / "feature_list.pkl")
    median_err_pct = joblib.load(MODEL_DIR / "median_error_pct.pkl")
    return model, features, median_err_pct

model, lgb_features, median_err_pct = load_model()

st.title("Is My Rent Fair? — Delhi Rental Analysis")
st.write(f"Analyzing {len(df):,} rental listings across Delhi")

# ---------------- Sidebar filters ----------------
st.sidebar.header("Search Filters")

locality_options = sorted(df['locality_group'].unique())
selected_localities = st.sidebar.multiselect(
    "Locality Group", locality_options, default=[]
)
if not selected_localities:
    selected_localities = locality_options

st.sidebar.divider()

bhk_min, bhk_max = int(df['bedrooms'].min()), int(df['bedrooms'].max())
bhk_range = st.sidebar.slider("BHK Range", bhk_min, bhk_max, (bhk_min, bhk_max))

st.sidebar.divider()

col1, col2 = st.sidebar.columns(2)
with col1:
    min_price = st.number_input("Min Budget (₹)", value=int(df['actual_price'].min()), step=1000)
with col2:
    max_price = st.number_input("Max Budget (₹)", value=int(df['actual_price'].max()), step=1000)

st.sidebar.divider()

fairness_options = sorted(df['fairness_label'].unique())
selected_fairness = st.sidebar.multiselect("Fairness Label", fairness_options, default=[])
if not selected_fairness:
    selected_fairness = fairness_options

# ---------------- Apply filters ----------------
filtered_df = df[
    (df['locality_group'].isin(selected_localities)) &
    (df['bedrooms'].between(bhk_range[0], bhk_range[1])) &
    (df['actual_price'].between(min_price, max_price)) &
    (df['fairness_label'].isin(selected_fairness))
]

# ---------------- Main panel ----------------
st.write(f"**{len(filtered_df):,}** of {len(df):,} listings match your filters")

col1, col2, col3 = st.columns(3)
col1.metric("Avg Rent", f"₹{filtered_df['actual_price'].mean():,.0f}" if len(filtered_df) else "—")
col2.metric("Median Rent", f"₹{filtered_df['actual_price'].median():,.0f}" if len(filtered_df) else "—")
col3.metric(
    "Avg ₹/sqft",
    f"₹{(filtered_df['actual_price']/filtered_df['size_sq_ft']).mean():,.1f}" if len(filtered_df) else "—"
)

st.dataframe(
    filtered_df[[
        'locality_name', 'locality_group', 'bedrooms', 'size_sq_ft',
        'property_type', 'actual_price', 'predicted_price', 'pct_deviation', 'fairness_label'
    ]],
    use_container_width=True,
    hide_index=True
)
st.divider()
tab1, tab2, tab3 = st.tabs(["Browse Listings", "Check My Rent", "Locality Trends"])
with tab1:
    st.write(f"**{len(filtered_df):,}** of {len(df):,} listings match your filters")
    col1, col2, col3 = st.columns(3)
    col1.metric("Avg Rent", f"₹{filtered_df['actual_price'].mean():,.0f}" if len(filtered_df) else "—")
    col2.metric("Median Rent", f"₹{filtered_df['actual_price'].median():,.0f}" if len(filtered_df) else "—")
    col3.metric("Avg ₹/sqft", f"₹{(filtered_df['actual_price']/filtered_df['size_sq_ft']).mean():,.1f}" if len(filtered_df) else "—")
    st.dataframe(
        filtered_df[['locality_name','locality_group','bedrooms','size_sq_ft',
                     'property_type','actual_price','predicted_price','pct_deviation','fairness_label']],
        use_container_width=True, hide_index=True
    )

with tab2:
    st.subheader("Enter your listing details")

    c1, c2 = st.columns(2)
    with c1:
        input_locality = st.selectbox("Locality Group", sorted(df['locality_group'].unique()))
        input_bedrooms = st.number_input("Bedrooms (BHK)", min_value=1, max_value=8, value=2)
        input_size = st.number_input("Size (sqft)", min_value=100, max_value=5000, value=800)
        input_property = st.selectbox("Property Type", sorted(df['property_type'].unique()))
    with c2:
        input_metro = st.number_input("Distance to nearest Metro (km)", min_value=0.0, value=2.0, step=0.1)
        input_airport = st.number_input("Distance to Airport (km)", min_value=0.0, value=15.0, step=0.5)
        input_aiims = st.number_input("Distance to AIIMS (km)", min_value=0.0, value=10.0, step=0.5)
        input_ndrlw = st.number_input("Distance to New Delhi Railway (km)", min_value=0.0, value=10.0, step=0.5)

    input_rent = st.number_input("Your actual/asking monthly rent (₹)", min_value=0, value=20000, step=500)

    if st.button("Check Fairness", type="primary"):
        input_row = pd.DataFrame([{
            'size_sq_ft': input_size,
            'bedrooms': input_bedrooms,
            'closest_metro_km': input_metro,
            'airport_dist_km': input_airport,
            'aiims_dist_km': input_aiims,
            'ndrlw_dist_km': input_ndrlw,
            'locality_group': input_locality,
            'property_type': input_property,
        }])
        for col in ['locality_group', 'property_type']:
            input_row[col] = input_row[col].astype('category')

        pred_log = model.predict(input_row[lgb_features])
        pred_price = np.exp(pred_log)[0]

        pct_dev = (input_rent - pred_price) / pred_price * 100

        st.metric("Estimated Fair Rent", f"₹{pred_price:,.0f}")
        st.metric("Your Rent vs Estimate", f"{pct_dev:+.1f}%")

        if pct_dev > 2 * median_err_pct:
            st.error(f"⚠️ Significantly overpriced — about {pct_dev:.0f}% above the estimated fair rent for a comparable listing.")
        elif pct_dev > median_err_pct:
            st.warning(f"Somewhat overpriced — about {pct_dev:.0f}% above estimate.")
        elif pct_dev < -2 * median_err_pct:
            st.info(f"This looks like a great deal — about {abs(pct_dev):.0f}% below the estimated fair rent.")
        elif pct_dev < -median_err_pct:
            st.info(f"Somewhat underpriced — about {abs(pct_dev):.0f}% below estimate.")
        else:
            st.success("This looks like a fair price for comparable listings.")

with tab3:
    st.subheader("Price Comparison by Locality Group")

    group_stats = df.groupby('locality_group').agg(
        avg_price=('actual_price', 'mean'),
        median_price=('actual_price', 'median'),
        avg_price_per_sqft=('actual_price', lambda x: (x / df.loc[x.index, 'size_sq_ft']).mean()),
        listing_count=('actual_price', 'count')
    ).reset_index().sort_values('avg_price_per_sqft', ascending=False)

    st.bar_chart(group_stats.set_index('locality_group')['avg_price_per_sqft'])

    st.dataframe(
        group_stats.rename(columns={
            'locality_group': 'Locality Group',
            'avg_price': 'Avg Rent (₹)',
            'median_price': 'Median Rent (₹)',
            'avg_price_per_sqft': 'Avg ₹/sqft',
            'listing_count': 'Listings'
        }),
        use_container_width=True, hide_index=True
    )

    st.divider()
    st.subheader("Fairness Distribution by Locality Group")
    fairness_by_group = pd.crosstab(df['locality_group'], df['fairness_label'])
    st.bar_chart(fairness_by_group)