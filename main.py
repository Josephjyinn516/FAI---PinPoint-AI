import geopandas as gpd  # ✅ Import GeoPandas
from data_loader import DataLoader
from hexbin_layer import HexbinGenerator
from poi_layer import POIProcessor  # ✅ Import POI Layer
from cluster_layer import POIClustering  # ✅ Import Clustering Layer
import folium

# 🔹 File Paths
state_geojson = r"C:\Users\User\OneDrive - Asia Pacific University\DEGREE (AI)\DEGREE YEAR 3 (FINAL YEAR)\Y3S1\Assignment\Further Artificial Intelligence\Dataset\Malaysia GEOJSON\administrative_1_state.geojson"
poi_csv = r"C:\Users\User\OneDrive - Asia Pacific University\DEGREE (AI)\DEGREE YEAR 3 (FINAL YEAR)\Y3S1\Assignment\Further Artificial Intelligence\Dataset\FullPOI_with_KLV.csv"
population_csv = r"C:\Users\User\OneDrive - Asia Pacific University\DEGREE (AI)\DEGREE YEAR 3 (FINAL YEAR)\Y3S1\Assignment\Further Artificial Intelligence\Dataset\State_1km_pop_data (Cleaned).csv"
output_map = "PinPoint AI.html"

# 🔹 Load Data
print("🔹 Loading Data...")
loader = DataLoader(state_geojson, poi_csv, population_csv)
gdf_poi, gdf_population, gdf_states = loader.load_data()

# ✅ Ensure POI Data has Geometry
if gdf_poi is not None:
    print(f"🔹 Initial POI Count: {len(gdf_poi)}")

    # ✅ Drop rows where longitude or latitude is missing
    gdf_poi = gdf_poi.dropna(subset=["Longitude", "Latitude"])

    # ✅ Convert to GeoDataFrame
    gdf_poi = gpd.GeoDataFrame(
        gdf_poi, geometry=gpd.points_from_xy(gdf_poi["Longitude"], gdf_poi["Latitude"]), crs="EPSG:4326"
    )

    # ✅ Drop Empty Geometries
    gdf_poi = gdf_poi[~gdf_poi.geometry.is_empty]

    print(f"✅ Cleaned POI Count: {len(gdf_poi)}")
else:
    print("⚠️ Warning: No POI data found!")

# 🔹 Filter Data for Selected States
target_states = ["Selangor", "W.P. Kuala Lumpur", "W.P. Putrajaya"]
gdf_selected_states = gdf_states[gdf_states["state"].isin(target_states)]

# 🔹 Generate Hexbins (Only for POI Areas)
print("🔹 Generating Hexbins (Containing POIs Only)...")
hex_generator = HexbinGenerator()
gdf_hex = hex_generator.generate_hexbins_with_pois(gdf_population, gdf_poi)

# ✅ Check if Hexbins were generated
if gdf_hex is None or gdf_hex.empty:
    print("⚠️ No valid hexbins generated. Exiting.")
    exit()

# 🔹 Assign Colors to Hexbins
gdf_hex_colored = hex_generator.assign_colors(gdf_hex)

# 🔹 Create Map
map_object = folium.Map(location=[3.139, 101.6869], zoom_start=9)  # Initialize map

# 🔹 Create Layers
hexbin_layer = hex_generator.create_hexbin_layer(gdf_hex_colored)  # ✅ Hexbin Layer
poi_layer = folium.FeatureGroup(name="Points of Interest (POI)")   # ✅ POI Layer (empty, will be filled later)
cluster_layer = folium.FeatureGroup(name="POI Clusters")          # ✅ Cluster Layer (empty, will be filled later)

# ✅ Add Hexbin Layer to Map
map_object.add_child(hexbin_layer)

# 🔹 Process POIs and Add POI Layer
print("🔹 Processing POI Data...")
poi_processor = POIProcessor(hex_resolution=7)
gdf_poi = poi_processor.filter_pois(gdf_poi, gdf_selected_states)
gdf_poi = poi_processor.assign_poi_to_hex(gdf_poi)
poi_processor.add_poi_layer(gdf_poi, poi_layer)  # ✅ Add POI markers to POI Layer

# ✅ Add POI Layer to Map
map_object.add_child(poi_layer)

# 🔹 Perform Clustering on POIs
print("🔹 Running Clustering on POIs...")
clustering = POIClustering()
gdf_poi = clustering.cluster_pois(gdf_poi)
cluster_polygons = clustering.generate_cluster_polygons(gdf_poi, gdf_population)
clustering.add_cluster_layer(cluster_polygons, cluster_layer)  # ✅ Add clusters to Cluster Layer

# ✅ Add Cluster Layer to Map
map_object.add_child(cluster_layer)

# 🔹 Add Layer Control to Enable/Disable Layers
folium.LayerControl().add_to(map_object)

# 🔹 Save Map
print("🔹 Saving Hexbin + POI + Clustering Map...")
map_object.save(output_map)
print(f"✅ Map with Hexbin + POI + Clustering Layer saved successfully as {output_map}")
