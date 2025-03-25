import streamlit as st
import pandas as pd
import geopandas as gpd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from streamlit_keplergl import keplergl_static
from keplergl import KeplerGl

from data_loader import DataLoader
from streamlitHexbin import HexbinGenerator
from streamlitDBSCAN import POIClustering
from poi_layer import POIProcessor
from streamlitSpider import SpiderMapLayer
import os

st.set_page_config(page_title="PinPoint AI with Kepler.gl", layout="wide")
st.title("📍 PinPoint AI: Interactive Map with Kepler.gl")

st.sidebar.header("Adjust Parameters")
percentile = st.sidebar.slider("Population Percentile Threshold", 30, 95, 75, step=5)
eps_slider = st.sidebar.slider("Clustering Radius (meters)", 50, 500, 100, step=10)
spider_km = st.sidebar.slider("LRT ↔ Commercial Hub Max Distance (km)", 0.1, 2.0, 0.5, step=0.1)
# ----------------------------
# 🔹 File Paths
# ----------------------------
import os
import streamlit as st

def get_file_path(filename):
    base_path = "Dataset" # Assuming the datasets are stored in a folder called 'datasets'
    return os.path.join(base_path, filename)

# Define the paths using relative paths
state_geojson = get_file_path("administrative_1_state.geojson")
poi_csv = get_file_path("FullPOI_with_KLV.csv")
population_csv = get_file_path("State_1km_pop_data (Cleaned).csv")
lrt_file = get_file_path("lrt-malaysia.csv")
commercial_file = get_file_path("Clustered_POIs.csv")


# ----------------------------
# 🔹 Cached Loaders
# ----------------------------
@st.cache_data
def load_data():
    loader = DataLoader(state_geojson, poi_csv, population_csv)
    return loader, *loader.load_data()

@st.cache_data
def train_model(_gdf_population, feature_columns, threshold):
    y_train = (_gdf_population["population_every_1km2"] > threshold).astype(int)
    model = RandomForestClassifier(n_estimators=200, random_state=42)
    model.fit(_gdf_population[feature_columns], y_train)
    return model


loader, gdf_poi, gdf_population, gdf_states = load_data()

# ----------------------------
# 🔹 Preprocessing & Model
# ----------------------------
feature_columns = [
    "population_every_1km2", "income_avg", "expenditure_avg",
    "ethnicity_proportion_bumi", "ethnicity_proportion_chinese", "ethnicity_proportion_indian",
    "age_proportion_0_14", "age_proportion_15_64", "age_proportion_18_above", "age_proportion_65_above"
]
gdf_population[feature_columns] = gdf_population[feature_columns].fillna(gdf_population[feature_columns].median())
threshold = np.percentile(gdf_population["population_every_1km2"], percentile)
rf_model = train_model(gdf_population, feature_columns, threshold)

# ----------------------------
# 🔹 Generate Hexbins
# ----------------------------
hexgen = HexbinGenerator(loader, rf_model)
gdf_hex = hexgen.generate_hexbins_with_ml()

gdf_hex = gdf_hex.set_geometry("geometry")
if gdf_hex.crs is None:
    gdf_hex.set_crs(epsg=4326, inplace=True)
else:
    gdf_hex = gdf_hex.to_crs(epsg=4326)

gdf_hex["type"] = "Hexbin"

gdf_hex = hexgen.assign_colors_by_parlimen(gdf_hex)

# ----------------------------
# 🔹 POI Filtering
# ----------------------------
poi_processor = POIProcessor()
target_states = ["Selangor", "W.P. Kuala Lumpur", "W.P. Putrajaya"]
gdf_selected_states = gdf_states[gdf_states["state"].isin(target_states)]
gdf_poi = poi_processor.filter_pois(gdf_poi, gdf_selected_states)
gdf_poi = poi_processor.assign_poi_to_hex(gdf_poi)

# ----------------------------
# 🔹 Reactive Rerun Detection
# ----------------------------
if "prev_eps_slider" not in st.session_state:
    st.session_state.prev_eps_slider = eps_slider
if "prev_spider_km" not in st.session_state:
    st.session_state.prev_spider_km = spider_km

rerun_cluster = eps_slider != st.session_state.prev_eps_slider
rerun_spider = spider_km != st.session_state.prev_spider_km

st.session_state.prev_eps_slider = eps_slider
st.session_state.prev_spider_km = spider_km

# ----------------------------
# 🔹 Clustering (If Needed)
# ----------------------------
if rerun_cluster or "cluster_polygons" not in st.session_state:
    eps_degrees = eps_slider / 111000
    clustering = POIClustering(eps_distance=eps_degrees)
    gdf_poi = clustering.cluster_pois(gdf_poi)
    cluster_polygons = clustering.generate_cluster_polygons(gdf_poi, gdf_population)
    if cluster_polygons is not None and not cluster_polygons.empty:
        cluster_polygons = cluster_polygons.set_geometry("geometry")
        cluster_polygons.set_crs(epsg=4326, inplace=True)
    st.session_state.cluster_polygons = cluster_polygons
    st.session_state.gdf_poi = gdf_poi
else:
    cluster_polygons = st.session_state.cluster_polygons
    gdf_poi = st.session_state.gdf_poi

# ----------------------------
# 🔹 Spider Layer (If Needed)
# ----------------------------
if rerun_spider or "spider_gdf" not in st.session_state:
    spider_layer = SpiderMapLayer(lrt_file, commercial_file, max_distance_km=spider_km)
    spider_layer.load_data()
    spider_gdf, lrt_points_gdf = spider_layer.generate_spider_outputs()
    st.session_state.spider_gdf = spider_gdf
    st.session_state.lrt_points_gdf = lrt_points_gdf
else:
    spider_gdf = st.session_state.spider_gdf
    lrt_points_gdf = st.session_state.lrt_points_gdf

# ----------------------------
# 🔹 Kepler.gl Display
# ----------------------------
kepler_map = KeplerGl(height=1000, width="100%", data={"Hexbins": gdf_hex})
kepler_map.add_data(data=gdf_hex, name="Hexbins")
if not gdf_poi.empty:
    kepler_map.add_data(data=gdf_poi, name="POIs")
if cluster_polygons is not None and not cluster_polygons.empty:
    kepler_map.add_data(data=cluster_polygons, name="Clusters")
if not spider_gdf.empty:
    kepler_map.add_data(data=spider_gdf, name="LRT Links")
if not lrt_points_gdf.empty:
    kepler_map.add_data(data=lrt_points_gdf, name="LRT Stations")

st.subheader("🗺️ PinPoint AI Map")
keplergl_static(kepler_map, center_map=True, height=800)
