import numpy as np
import geopandas as gpd
import folium
import pandas as pd
from sklearn.cluster import DBSCAN
from shapely.geometry import MultiPoint
from scipy.spatial.distance import cdist

class POIClustering:
    def __init__(self, eps_distance=100/111000, min_samples=3, output_csv="Clustered_POIs.csv"):
        self.eps_distance = eps_distance  # Distance threshold for clustering (~100m)
        self.min_samples = min_samples    # Minimum POIs per cluster
        self.output_csv = output_csv      # File to save cluster data

    def cluster_pois(self, gdf_poi):
        """Perform DBSCAN clustering on POIs."""
        print("🔹 Running DBSCAN Clustering...")

        poi_coords = np.array(list(zip(gdf_poi.geometry.y, gdf_poi.geometry.x)))
        dbscan = DBSCAN(eps=self.eps_distance, min_samples=self.min_samples, metric="euclidean")
        gdf_poi["cluster"] = dbscan.fit_predict(poi_coords)

        return gdf_poi

    def generate_cluster_polygons(self, gdf_poi, gdf_population):
        print("🔹 Generating Cluster Polygons...")

        cluster_polygons = gpd.GeoDataFrame(columns=["cluster", "geometry"], crs="EPSG:4326")
        cluster_info = []

        for cluster_id in set(gdf_poi["cluster"]):
            if cluster_id == -1:
                continue  # Ignore noise points

            # Extract points in the cluster
            cluster_points = gdf_poi[gdf_poi["cluster"] == cluster_id].geometry
            total_poi = len(cluster_points)

            # ✅ Ensure at least 3 POIs to form a Convex Hull
            if total_poi < 3:
                print(f"⚠️ Skipping cluster {cluster_id} (only {total_poi} POIs, cannot form a convex hull)")
                continue  # Skip this cluster

            # ✅ Generate Convex Hull for Cluster
            hull_polygon = MultiPoint(cluster_points.tolist()).convex_hull
            cluster_polygons = pd.concat([cluster_polygons, gpd.GeoDataFrame({"cluster": [cluster_id], "geometry": [hull_polygon]})])

            # ✅ Calculate Centroid
            centroid = hull_polygon.centroid

            # ✅ Find Closest Population Point for Parlimen & Dun
            population_coords = np.array(list(zip(gdf_population.geometry.y, gdf_population.geometry.x)))
            cluster_centroid_coords = np.array([[centroid.y, centroid.x]])

            closest_idx = np.argmin(cdist(cluster_centroid_coords, population_coords))
            closest_population = gdf_population.iloc[closest_idx]

            cluster_info.append({
                "Cluster_ID": cluster_id,
                "Centroid_Lat": centroid.y,
                "Centroid_Lon": centroid.x,
                "Total_POI": total_poi,
                "Parlimen": closest_population["parlimen"],
                "Dun": closest_population["dun"]
            })

        # ✅ Save Cluster Data to CSV
        df_cluster_info = pd.DataFrame(cluster_info)
        df_cluster_info.to_csv(self.output_csv, index=False)
        print(f"✅ Cluster Data Saved to {self.output_csv}")

        return cluster_polygons


    def add_cluster_layer(self, cluster_polygons, folium_map):
        """Add Cluster Polygons as a Layer to the Map."""
        print("🔹 Adding Clusters to Map...")

        cluster_layer = folium.FeatureGroup(name="POI Clusters")

        for _, row in cluster_polygons.iterrows():
            folium.GeoJson(
                row["geometry"],
                name=f"Cluster {row['cluster']}",
                style_function=lambda feature: {
                    "fillColor": "#FF5733", "color": "#FF5733",
                    "weight": 2, "fillOpacity": 0.4
                }
            ).add_to(cluster_layer)

        folium_map.add_child(cluster_layer)
        print("✅ Cluster Layer Added to Map.")
