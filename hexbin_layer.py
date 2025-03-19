import h3
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Polygon
from tqdm import tqdm
import folium

class HexbinGenerator:
    def __init__(self, hex_resolution=7):
        self.hex_resolution = hex_resolution

    def generate_hexbins_with_pois(self, gdf_population, gdf_poi):
        print("🔹 Generating Hexbins (Containing POIs Only)...")

        # ✅ Ensure POI data is valid
        if gdf_poi is None or gdf_poi.empty:
            print("⚠️ No valid POI data found! Skipping hexbin generation.")
            return None

        # ✅ Remove empty geometries
        gdf_poi = gdf_poi[~gdf_poi.geometry.is_empty]

        # ✅ Assign POIs to Hexagons
        gdf_poi["hex"] = gdf_poi.apply(
            lambda row: h3.latlng_to_cell(row.geometry.y, row.geometry.x, self.hex_resolution), axis=1
        )

        # ✅ Get Unique Hexagons That Contain POIs
        hex_with_poi = set(gdf_poi["hex"])

        # ✅ Assign Population Points to Hexagons
        gdf_population["hex"] = gdf_population.apply(
            lambda row: h3.latlng_to_cell(row.geometry.y, row.geometry.x, self.hex_resolution), axis=1
        )

        # ✅ Filter Population Data to Only Hexagons with POIs
        gdf_population = gdf_population[gdf_population["hex"].isin(hex_with_poi)]

        if gdf_population.empty:
            print("⚠️ No hexagons found with POIs. Skipping hexbin generation.")
            return None

        # ✅ Aggregate Population Data Per Hexbin
        hex_population = gdf_population.groupby("hex").agg({
            "population_every_1km2": "sum",
            "state": "first", "parlimen": "first", "dun": "first",
            "ethnicity_proportion_bumi": "mean", "ethnicity_proportion_chinese": "mean", "ethnicity_proportion_indian": "mean",
            "age_proportion_0_14": "mean", "age_proportion_15_64": "mean", "age_proportion_18_above": "mean", "age_proportion_65_above": "mean",
            "income_avg": "mean", "expenditure_avg": "mean"
        }).reset_index()

        # ✅ Convert Hex IDs to Polygons
        hex_population["geometry"] = [
            Polygon([tuple(reversed(coord)) for coord in h3.cell_to_boundary(hex_id)]) 
            for hex_id in tqdm(hex_population["hex"], desc="Processing Hexagons")
        ]

        # ✅ Convert to GeoDataFrame
        gdf_hex = gpd.GeoDataFrame(hex_population, geometry="geometry", crs="EPSG:4326")

        print(f"✅ Hexbins Generated: {len(gdf_hex)} (Containing POIs Only)")
        return gdf_hex


    def assign_colors(self, gdf_hex):
        """
        Assigns colors to hexbins based on population density.
        """
        print("🔹 Assigning Colors to Hexbins...")

        # Normalize population density for color mapping
        gdf_hex["population_scaled"] = (
            gdf_hex["population_every_1km2"] - gdf_hex["population_every_1km2"].min()
        ) / (gdf_hex["population_every_1km2"].max() - gdf_hex["population_every_1km2"].min())

        gdf_hex["color"] = "gray"  # Default color

        for parlimen, group in gdf_hex.groupby("parlimen"):
            q25, q50, q75 = np.percentile(group["population_every_1km2"], [25, 50, 75])

            def assign_color(value):
                if value >= q75:
                    return "green"  # 🔴 Highest 25%
                elif value >= q25:
                    return "yellow"  # 🟡 Middle 50%
                else:
                    return "red"  # 🟢 Lowest 25%

            gdf_hex.loc[group.index, "color"] = group["population_every_1km2"].apply(assign_color)

        print("✅ Colors Assigned.")
        return gdf_hex

    def create_hexbin_layer(self, gdf_hex):
        """
        Creates a Folium GeoJson layer for the hexbins.
        """
        print("🔹 Creating Hexbin Layer...")

        hexbin_layer = folium.FeatureGroup(name="Hexbin Population Density (POI-Based)")

        folium.GeoJson(
            gdf_hex,
            name="Hexbin Layer",
            style_function=lambda feature: {
                "fillColor": feature["properties"]["color"],
                "color": "black",
                "weight": 0.5,
                "fillOpacity": 0.5
            },
            tooltip=folium.GeoJsonTooltip(
                fields=["state", "parlimen", "dun", "population_every_1km2",
                        "ethnicity_proportion_bumi", "ethnicity_proportion_chinese", "ethnicity_proportion_indian",
                        "age_proportion_0_14", "age_proportion_15_64", "age_proportion_18_above", "age_proportion_65_above",
                        "income_avg", "expenditure_avg"],
                aliases=["State:", "Parlimen:", "Dun:", "Population:",
                         "Bumi Putera:", "Chinese:", "Indian:",
                         "Age 0-14:", "Age 15-64:", "Age 18+:", "Age 65+:",
                         "Average Income:", "Average Expenditure:"],
                localize=True
            )
        ).add_to(hexbin_layer)

        print(f"✅ Hexbin Layer Created.")
        return hexbin_layer
