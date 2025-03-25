# 1. hexbin_layer.py (Modified for Streamlit)

import h3
import geopandas as gpd
import numpy as np
import folium
from shapely.geometry import Polygon
from tqdm import tqdm
from sklearn.ensemble import RandomForestClassifier

class HexbinGenerator:
    def __init__(self, data_loader, rf_model, hex_resolution=7):
        self.data_loader = data_loader
        self.rf_model = rf_model
        self.hex_resolution = hex_resolution

    def generate_hexbins_with_ml(self):
        gdf_poi, gdf_population, _ = self.data_loader.load_data()

        if gdf_population is None or gdf_population.empty:
            return None

        gdf_population["hex"] = gdf_population.apply(
            lambda row: h3.latlng_to_cell(row.geometry.y, row.geometry.x, self.hex_resolution), axis=1
        )

        hex_population = gdf_population.groupby("hex").agg({
            "population_every_1km2": "sum",
            "state": "first", "parlimen": "first", "dun": "first",
            "ethnicity_proportion_bumi": "mean", "ethnicity_proportion_chinese": "mean", "ethnicity_proportion_indian": "mean",
            "age_proportion_0_14": "mean", "age_proportion_15_64": "mean", "age_proportion_18_above": "mean", "age_proportion_65_above": "mean",
            "income_avg": "mean", "expenditure_avg": "mean"
        }).reset_index()

        numeric_cols = hex_population.select_dtypes(include=[np.number]).columns
        hex_population[numeric_cols] = hex_population[numeric_cols].apply(lambda x: x.fillna(x.median()), axis=0)

        feature_columns = [
            "population_every_1km2", "income_avg", "expenditure_avg",
            "ethnicity_proportion_bumi", "ethnicity_proportion_chinese", "ethnicity_proportion_indian",
            "age_proportion_0_14", "age_proportion_15_64", "age_proportion_18_above", "age_proportion_65_above"
        ]

        X_hex = hex_population[feature_columns]
        y_hex_pred = self.rf_model.predict(X_hex)

        hex_population["suitability_pred"] = y_hex_pred
        hex_population = hex_population[hex_population["suitability_pred"] == 1]

        if hex_population.empty:
            return None

        hex_population["geometry"] = [
            Polygon([tuple(reversed(coord)) for coord in h3.cell_to_boundary(hex_id)])
            for hex_id in tqdm(hex_population["hex"], desc="Processing Hexagons")
        ]

        gdf_hex = gpd.GeoDataFrame(hex_population, geometry="geometry", crs="EPSG:4326")
        return gdf_hex

    def assign_colors_by_parlimen(self, gdf_hex):
        gdf_hex["color"] = None  # or you can skip this entirely

        for parlimen, group in gdf_hex.groupby("parlimen"):
            pop_values = group["population_every_1km2"]
            q25, q50, q75 = np.percentile(pop_values, [25, 50, 75])

            def assign_color(val):
                if val < q25:
                    return "<Q25"     # Red for values below 25th percentile
                elif val < q50:
                    return "<Q50"  # Yellow for values between 25th and 50th percentile
                elif val < q75:
                    return "<Q75"   # Green for values between 50th and 75th percentile
                else:
                    return ">Q75"   # Green for values above 75th percentile

            gdf_hex.loc[group.index, "color"] = group["population_every_1km2"].apply(assign_color)

        return gdf_hex


    # def plot_filtered_hexbin_map(self, gdf_hex):
    #     hexbin_layer = folium.FeatureGroup(name="Filtered Hexbins")

    #     folium.GeoJson(
    #         gdf_hex,
    #         style_function=lambda feature: {
    #             "fillColor": feature["properties"].get("color", "gray"),
    #             "color": "black",
    #             "weight": 0.5,
    #             "fillOpacity": 0.5
    #         },
    #         tooltip=folium.GeoJsonTooltip(
    #             fields=["state", "parlimen", "dun", "population_every_1km2", "income_avg", "expenditure_avg"],
    #             aliases=["State:", "Parlimen:", "Dun:", "Population:", "Income:", "Expenditure:"]
    #         )
    #     ).add_to(hexbin_layer)

    #     return hexbin_layer