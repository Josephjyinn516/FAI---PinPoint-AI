import pandas as pd
import folium
from geopy.distance import geodesic

# Load LRT Hub Data
lrt_file = r"C:\Users\User\OneDrive - Asia Pacific University\DEGREE (AI)\DEGREE YEAR 3 (FINAL YEAR)\Y3S1\Assignment\Further Artificial Intelligence\Dataset\lrt-malaysia.csv"
df_lrt = pd.read_csv(lrt_file)

# Load Commercial Hub Data
commercial_file = r"C:\Users\User\OneDrive - Asia Pacific University\DEGREE (AI)\DEGREE YEAR 3 (FINAL YEAR)\Y3S1\Assignment\Further Artificial Intelligence\Code\Clustered_POIs.csv"
df_commercial = pd.read_csv(commercial_file)

# Rename columns for consistency
df_lrt.rename(columns={'latitude': 'Latitude', 'longitude': 'Longitude'}, inplace=True)
df_commercial.rename(columns={'Centroid_Lat': 'Latitude', 'Centroid_Lon': 'Longitude'}, inplace=True)

# Define maximum distance for linking (5 km)
max_distance_km = 1

# Create Folium Map (Centered around LRT Hubs)
map_center = [df_lrt["Latitude"].mean(), df_lrt["Longitude"].mean()]
lrt_map = folium.Map(location=map_center, zoom_start=9)

# Add LRT Hub Circles (Blue)
for _, row in df_lrt.iterrows():
    folium.CircleMarker(
        location=[row["Latitude"], row["Longitude"]],
        radius=5,  # Size of the circle
        color="blue",
        fill=True,
        fill_color="blue",
        fill_opacity=0.7,
        popup=row.get("station_name", "LRT Hub")
    ).add_to(lrt_map)

# Add Commercial Hub Circles (Red)
for _, row in df_commercial.iterrows():
    folium.CircleMarker(
        location=[row["Latitude"], row["Longitude"]],
        radius=7,  # Slightly larger for commercial hubs
        color="red",
        fill=True,
        fill_color="red",
        fill_opacity=0.7,
        popup=f"Cluster ID: {row.get('Cluster_ID', 'Commercial Hub')}"
    ).add_to(lrt_map)

# Link LRT hubs to commercial hubs within 5km radius
for _, lrt_row in df_lrt.iterrows():
    lrt_location = (lrt_row["Latitude"], lrt_row["Longitude"])

    for _, com_row in df_commercial.iterrows():
        com_location = (com_row["Latitude"], com_row["Longitude"])
        distance = geodesic(lrt_location, com_location).km

        if distance <= max_distance_km:  # Only link if within 5km
            folium.PolyLine(
                locations=[lrt_location, com_location],
                color="green",
                weight=2,
                opacity=0.7
            ).add_to(lrt_map)

# Save and display the map
lrt_map.save("lrt_commercial_5km_links.html")
lrt_map
