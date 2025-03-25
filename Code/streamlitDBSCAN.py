import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import MultiPoint
from sklearn.cluster import DBSCAN
from scipy.spatial.distance import cdist

class POIClustering:
    def __init__(self, eps_distance=100 / 111000, min_samples=3, output_csv="Clustered_POIs.csv"):
        self.eps_distance = eps_distance  # ~100 meters in degrees
        self.min_samples = min_samples
        self.output_csv = output_csv

    def cluster_pois(self, gdf_poi):
        """Apply DBSCAN clustering to POI point data."""
        print("🔹 Running DBSCAN Clustering...")

        poi_coords = np.array(list(zip(gdf_poi.geometry.y, gdf_poi.geometry.x)))
        dbscan = DBSCAN(eps=self.eps_distance, min_samples=self.min_samples, metric="euclidean")
        gdf_poi["cluster"] = dbscan.fit_predict(poi_coords)

        print(f"✅ DBSCAN completed. Total clusters (excluding noise): {len(set(gdf_poi['cluster'])) - (1 if -1 in gdf_poi['cluster'] else 0)}")
        return gdf_poi

    def generate_cluster_polygons(self, gdf_poi, gdf_population):
        """Generate convex hull polygons for each DBSCAN cluster."""
        print("🔹 Generating Cluster Polygons...")

        cluster_polygons = []
        cluster_info = []

        for cluster_id in sorted(set(gdf_poi["cluster"])):
            if cluster_id == -1:
                continue  # Skip noise

            cluster_points = gdf_poi[gdf_poi["cluster"] == cluster_id].geometry
            total_poi = len(cluster_points)

            if total_poi < 3:
                print(f"⚠️ Skipping cluster {cluster_id} (only {total_poi} POIs)")
                continue

            hull = MultiPoint(cluster_points.tolist()).convex_hull
            centroid = hull.centroid

            # Find closest population centroid
            population_coords = np.array(list(zip(gdf_population.geometry.y, gdf_population.geometry.x)))
            cluster_centroid_coords = np.array([[centroid.y, centroid.x]])

            closest_idx = np.argmin(cdist(cluster_centroid_coords, population_coords))
            closest_population = gdf_population.iloc[closest_idx]

            cluster_polygons.append({
                "Cluster_ID": cluster_id,
                "Centroid_Lat": centroid.y,
                "Centroid_Lon": centroid.x,
                "Total_POI": total_poi,
                "Parlimen": closest_population["parlimen"],
                "Dun": closest_population["dun"],
                "geometry": hull
            })

            cluster_info.append({
                "Cluster_ID": cluster_id,
                "Centroid_Lat": centroid.y,
                "Centroid_Lon": centroid.x,
                "Total_POI": total_poi,
                "Parlimen": closest_population["parlimen"],
                "Dun": closest_population["dun"]
            })

        # Save CSV
        df_cluster_info = pd.DataFrame(cluster_info)
        df_cluster_info.to_csv(self.output_csv, index=False)
        print(f"✅ Cluster info saved to {self.output_csv}")

        # Return GeoDataFrame
        cluster_gdf = gpd.GeoDataFrame(cluster_polygons, crs="EPSG:4326")
        return cluster_gdf
