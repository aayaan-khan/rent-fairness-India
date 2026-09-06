from pathlib import Path
import sqlite3
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "raw" / "June_8_data_metro_closest_stations.csv"
DB_PATH = BASE_DIR / "db" / "rentals.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_PATH)

price_low, price_high = df["price"].quantile([0.01, 0.99])
size_low, size_high = df["size_sq_ft"].quantile([0.01, 0.99])
price_mask = df["price"].between(price_low, price_high)
size_mask = df["size_sq_ft"].between(size_low, size_high)
df_clean = df[price_mask & size_mask].copy()
df_clean["localityGroup"] = df_clean["suburbName"].str.strip()
print(f"After percentile outlier filter: {len(df_clean)} rows")

n_before = len(df_clean)
df_clean = df_clean[df_clean["size_sq_ft"] != 4500].copy()
print(f"Dropped {n_before - len(df_clean)} rows with capped size_sq_ft==4500")

n_before = len(df_clean)
df_clean = df_clean[df_clean["size_sq_ft"] / df_clean["bedrooms"] >= 150].copy()
print(f"Dropped {n_before - len(df_clean)} rows with unrealistic sqft/bedroom ratio")
print(f"Final cleaned row count: {len(df_clean)}")

conn = sqlite3.connect(DB_PATH)
localities = (
    df_clean.groupby("localityName")
    .agg(
        locality_group=("localityGroup", "first"),
        latitude=("latitude", "mean"),
        longitude=("longitude", "mean"),
        listing_count=("localityName", "count"),
    )
    .reset_index()
    .rename(columns={"localityName": "locality_name"})
)
localities["is_sparse"] = localities["listing_count"] < 5
localities["locality_id"] = range(1, len(localities) + 1)
localities.to_sql("localities", conn, if_exists="replace", index=False)
print(f"localities table: {len(localities)} rows")

locality_map = dict(zip(localities["locality_name"], localities["locality_id"]))
listings = df_clean.copy()
listings["locality_id"] = listings["localityName"].map(locality_map)
assert listings["locality_id"].isnull().sum() == 0, "Some rows failed to map to a locality_id!"

listings = listings.rename(columns={
    "propertyType": "property_type",
    "companyName": "company_name",
    "closest_mtero_station_km": "closest_metro_km",
    "AP_dist_km": "airport_dist_km",
    "Aiims_dist_km": "aiims_dist_km",
    "NDRLW_dist_km": "ndrlw_dist_km",
})
listings["listing_id"] = range(1, len(listings) + 1)
listings_final = listings[[
    "listing_id", "locality_id", "size_sq_ft", "property_type", "bedrooms",
    "price", "company_name", "closest_metro_km", "airport_dist_km",
    "aiims_dist_km", "ndrlw_dist_km"
]]
listings_final.to_sql("listings", conn, if_exists="replace", index=False)
print(f"listings table: {len(listings_final)} rows")

amenities = pd.DataFrame(columns=["amenity_id", "listing_id", "amenity_name"])
amenities.to_sql("amenities", conn, if_exists="replace", index=False)

with conn:
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_locality_id ON localities(locality_id);")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_listing_id ON listings(listing_id);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_listing_locality ON listings(locality_id);")

conn.close()
print("Database build complete.")