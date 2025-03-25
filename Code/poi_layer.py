import h3
import folium
import geopandas as gpd

class POIProcessor:
    def __init__(self, hex_resolution=7):
        self.hex_resolution = hex_resolution
        self.brand_icons = {
            "7Cafe": "https://www.ekocherasmall.com/images/uploads/20221229162220_7%20Cafe%20logo_color%20only.jpg",
            "7Eleven": "https://1000logos.net/wp-content/uploads/2020/09/7-Eleven-Logo-1968.png",
            "99 Speedmart": "https://rnggt.com/wp-content/uploads/2024/03/99-Speed-Mart.png",
            "Chagee": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTpi_h7I_Iuxl4lK7hDnUoVsgfpyGS-N1ndXQ&s",
            "CU": "https://upload.wikimedia.org/wikipedia/commons/1/1a/CU_BI_%282017%29.svg",
            "Domino's": "https://cdn.iconscout.com/icon/free/png-256/free-dominos-pizza-logo-icon-download-in-svg-png-gif-file-formats--food-italian-slice-logos-pack-icons-1581234.png?f=webp&w=256",
            "Eco-shop": "https://play-lh.googleusercontent.com/JvfAjmCsDEVMR0pMiWSEXyPmCX6_gYbSAO0I49YTEqmXXEmcvhM9bGSyxKXuZZ6OB6s",
            "FamilyMart": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS2-0_8Fp1xFO0bpxjBAIpuyQcw3p8o3_CyrQ&s",
            "Kenangan Coffee": "https://www.sunwaypyramid.com/static/shops/67e55cf747dc260c37581f09d24a023e/w768.png",
            "KFC": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRXtFRQ9HZaFj-rhvF_W7H-nDP6dSiY2Cgieg&s",
            "Marrybrown": "https://play-lh.googleusercontent.com/8JGXUb9ppE7Oc-DL8c9fNx4PAOQWV_GRnayhfzQFnoQdS3YVw2--RCxRUC36kCnRRQM=w240-h480-rw",
            "McDonalds": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTQBWFv2jTgUqSrAblgeB1Aj1eJ-FmuQvlKGw&s",
            "MR DIY": "https://vectorise.net/logo/wp-content/uploads/2018/01/Mr-DIY.png",
            "myNEWS": "https://is1-ssl.mzstatic.com/image/thumb/Purple221/v4/50/ca/7b/50ca7ba1-1ebd-9c65-9ee5-894c6ba9cb06/mynews_AppIcon-0-0-1x_U007emarketing-0-8-0-0-85-220.png/1200x600wa.png",
            "Starbucks": "https://i.pinimg.com/736x/51/b9/23/51b923f0f86c47b7ccb3dd01e927a5ef.jpg",
            "The Coffee Bean": "https://play-lh.googleusercontent.com/rkLArKsUOBieVg20jJieqOycVnRaBGTcd71A6ExS_4HU81_A8byQhWsdX6ov1BKr94w",
            "Watson": "https://e7.pngegg.com/pngimages/595/266/png-clipart-logo-retail-watsons-marketing-a-s-watson-group-w-text-retail-thumbnail.png",
            "Pizza Hut": "https://cdn.iconscout.com/icon/free/png-256/free-pizza-hut-logo-icon-download-in-svg-png-gif-file-formats--food-slice-fast-italian-brand-pack-logos-icons-2822954.png",
            "ZUS Coffee": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRHalYO5hzDg0neHd2e46OhN3uJKtBjvE7Jxg&sg"
        }
        self.DEFAULT_ICON_URL = "https://upload.wikimedia.org/wikipedia/commons/8/88/Map_marker.svg"

    def filter_pois(self, gdf_poi, gdf_selected_states):
        """Filter POIs within the selected states."""
        return gdf_poi[gdf_poi.within(gdf_selected_states.unary_union)]

    def assign_poi_to_hex(self, gdf_poi):
        """Assign POIs to hexagons based on their latitude/longitude."""
        gdf_poi["hex"] = gdf_poi.apply(lambda row: h3.latlng_to_cell(row.geometry.y, row.geometry.x, self.hex_resolution), axis=1)
        return gdf_poi

    def add_poi_layer(self, gdf_poi, folium_map):
        """Add POI markers with brand-specific icons to the map."""
        print("🔹 Adding POI Layer to Map...")

        poi_layer = folium.FeatureGroup(name="Points of Interest (POI)")

        # Ensure "Brand" column exists
        if "Brand" not in gdf_poi.columns:
            gdf_poi["Brand"] = "Unknown"

        for _, row in gdf_poi.iterrows():
            brand = row["Brand"]
            icon_url = self.brand_icons.get(brand, self.DEFAULT_ICON_URL)  # Get brand-specific icon or default

            # Create a custom icon for the POI
            icon = folium.CustomIcon(
                icon_url,
                icon_size=(25, 25)  # Adjust the size of the logo
            )

            # Add POI marker to the POI layer
            folium.Marker(
                location=[row.geometry.y, row.geometry.x],
                icon=icon,
                tooltip=f"{brand}"  # Display brand name when hovered
            ).add_to(poi_layer)

        folium_map.add_child(poi_layer)
        print("✅ POI Layer Added to Map.")
