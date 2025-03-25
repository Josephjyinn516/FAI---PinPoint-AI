import pandas as pd
import geopandas as gpd
import chardet

class DataLoader:
    def __init__(self, state_geojson, poi_csv=None, population_csv=None):
        self.state_geojson = state_geojson
        self.poi_csv = poi_csv
        self.population_csv = population_csv

    def detect_encoding(self, file_path):
        if file_path is None:
            return None  # Skip if no file
        with open(file_path, "rb") as f:
            result = chardet.detect(f.read(100000))
            return result["encoding"]

    def load_data(self):
        print("🔹 Loading Datasets...")

        gdf_states = gpd.read_file(self.state_geojson).to_crs("EPSG:4326")

        gdf_poi = None
        if self.poi_csv:
            encoding = self.detect_encoding(self.poi_csv)
            df_poi = pd.read_csv(self.poi_csv, encoding=encoding)
            gdf_poi = gpd.GeoDataFrame(df_poi, geometry=gpd.points_from_xy(df_poi["Longitude"], df_poi["Latitude"]), crs="EPSG:4326")

        gdf_population = None
        if self.population_csv:
            df_population = pd.read_csv(self.population_csv)
            gdf_population = gpd.GeoDataFrame(df_population, geometry=gpd.points_from_xy(df_population["Lon"], df_population["Lat"]), crs="EPSG:4326")

        return gdf_poi, gdf_population, gdf_states
