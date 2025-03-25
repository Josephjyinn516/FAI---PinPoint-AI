import pandas as pd
import numpy as np
from geopy.distance import geodesic
from shapely.geometry import LineString, Point
import geopandas as gpd

class SpiderMapLayer:
    def __init__(self, lrt_file, commercial_file, max_distance_km=1):
        self.lrt_file = lrt_file
        self.commercial_file = commercial_file
        self.max_distance_km = max_distance_km
        self.df_lrt = None
        self.df_commercial = None

    def load_data(self):
        """Loads LRT and commercial hub data."""
        self.df_lrt = pd.read_csv(self.lrt_file, encoding="ISO-8859-1")
        self.df_commercial = pd.read_csv(self.commercial_file)

        self.df_lrt.rename(columns={'latitude': 'Latitude', 'longitude': 'Longitude'}, inplace=True)
        self.df_commercial.rename(columns={'Centroid_Lat': 'Latitude', 'Centroid_Lon': 'Longitude'}, inplace=True)

        print(f"[SpiderLayer DEBUG] Loaded {len(self.df_lrt)} LRT stations.")
        print(f"[SpiderLayer DEBUG] Loaded {len(self.df_commercial)} commercial hubs.")

    def generate_spider_outputs(self):
        """
        Generates:
        - Spider links (GeoDataFrame of LineStrings)
        - LRT station markers (GeoDataFrame of Points)
        :return: (GeoDataFrame, GeoDataFrame)
        """
        if self.df_lrt is None or self.df_commercial is None:
            raise ValueError("Data not loaded. Call load_data() first.")

        spider_lines = []

        print(f"[SpiderLayer DEBUG] Generating spider links with max distance {self.max_distance_km} km...")

        for _, com_row in self.df_commercial.iterrows():
            com_point = (com_row["Latitude"], com_row["Longitude"])
            found_connection = False

            for _, lrt_row in self.df_lrt.iterrows():
                lrt_point = (lrt_row["Latitude"], lrt_row["Longitude"])
                distance_km = geodesic(com_point, lrt_point).km

                if distance_km <= self.max_distance_km:
                    line = LineString([
                        (com_row["Longitude"], com_row["Latitude"]),
                        (lrt_row["Longitude"], lrt_row["Latitude"])
                    ])
                    spider_lines.append(line)
                    found_connection = True

            if not found_connection:
                print(f"[SpiderLayer DEBUG] ❌ No nearby LRT for commercial hub at {com_point}")

        print(f"[SpiderLayer DEBUG] ✅ Total spider links generated: {len(spider_lines)}")

        spider_gdf = gpd.GeoDataFrame(geometry=spider_lines, crs="EPSG:4326") if spider_lines else \
                     gpd.GeoDataFrame(columns=["geometry"], geometry=[], crs="EPSG:4326")

        # LRT station points
        lrt_points = gpd.GeoDataFrame(
            self.df_lrt.copy(),
            geometry=gpd.points_from_xy(self.df_lrt["Longitude"], self.df_lrt["Latitude"]),
            crs="EPSG:4326"
        )

        return spider_gdf, lrt_points
