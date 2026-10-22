import os
import yaml
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import cartopy.crs as ccrs
from pathlib import Path
from pyproj import CRS

import globalvars
from reader.io_utils import load_processed_datasets
from modules.wrf_rio import wrf_prepare_for_rio

# ==========================================================
# User settings
# ==========================================================

init_date = "2021012700"
lead_time=6

varname = 'qpf'
domain_name = 'Central_CA'
source='archive'


domain = {
    "lon_min": -125.,
    "lon_max": -110.,
    "lat_min": 25.,
    "lat_max": 50.,
}

# ---------------------------------------------------------
# Load processed datasets
# ---------------------------------------------------------

fc, final_ds = (
    load_processed_datasets(
        init_date=init_date,
        source=source,
    )
)
# ---------------------------------------------------------
# Load Burn Scar Shapefile
# ---------------------------------------------------------

fp = globalvars.path_to_data + 'downloads/calfire/California_Fire_Perimeters.shp'
polys = gpd.read_file(fp)

keep_names = ["CZU LIGHTNING COMPLEX"]
polys = polys[polys["FIRE_NAME"].isin(keep_names)]

# ---------------------------------------------------------
# Subset to Burn Scar
# ---------------------------------------------------------
field = final_ds[varname]
print(field)
print("Dataset shape:", field.shape)
print("Latitude range:",
      float(field.latitude.min()), float(field.latitude.max()))
print("Longitude range:",
      float(field.longitude.min()), float(field.longitude.max()))


from pyproj import Transformer

# Inspect the burn scar in geographic coordinates
print("\n--- Burn Scar Geographic Bounds ---")
print(polys.to_crs("EPSG:4326").geometry.bounds)

# Transform burn scar coordinates to the WRF Lambert Conformal projection
wrf_crs = CRS.from_proj4(
    "+proj=lcc +lat_1=39 +lat_2=50 +lat_0=39 +lon_0=-140 "
    "+a=6370000 +b=6370000 +units=m +no_defs"
)

polys_wrf = polys.to_crs(wrf_crs)

print("\n--- Burn Scar Bounds in WRF Projection ---")
print(polys_wrf.geometry.bounds)

# prepare for rioxarray
da = wrf_prepare_for_rio(field, x_dim="west_east", y_dim="south_north")


# Compare the actual WRF geographic coordinates with projected coordinates
from pyproj import Transformer

transformer = Transformer.from_crs(
    "EPSG:4326",
    da.rio.crs,
    always_xy=True
)

lon = field.longitude.values
lat = field.latitude.values

x_actual, y_actual = transformer.transform(lon, lat)

print("\n--- Projected WRF Grid Coordinates ---")
print("Actual projected X range:", np.nanmin(x_actual), np.nanmax(x_actual))
print("Actual projected Y range:", np.nanmin(y_actual), np.nanmax(y_actual))

print("\n--- Assigned Raster Coordinates ---")
print("Assigned X range:", float(da.west_east.min()), float(da.west_east.max()))
print("Assigned Y range:", float(da.south_north.min()), float(da.south_north.max()))

# reproject shapefile to match WRF CRS
polys = polys.to_crs(da.rio.crs)

print(f"\nVariable: {varname}")
print(f"  Raster CRS: {da.rio.crs}")
print(f"  Polygon CRS: {polys.crs}")
print(f"  Raster bounds: {da.rio.bounds()}")
print(f"  Polygon bounds: {polys.geometry.bounds}")

results = []
# --- loop through polygons ---
for _, poly in polys.iterrows():
    # Clip both datasets to polygon
    da_clip = da.rio.clip([poly.geometry], polys.crs, drop=True)
    print(da_clip)

    print("\n--- Clipped Cell Locations ---")
    print(
        da_clip[["latitude", "longitude"]]
        if False else "Grid cells:"
    )
    
    lat_clip = da_clip.latitude.values
    lon_clip = da_clip.longitude.values
    
    for j in range(lat_clip.shape[0]):
        for i in range(lat_clip.shape[1]):
            print(
                f"Row {j}, Col {i}: "
                f"lat={lat_clip[j, i]:.4f}, "
                f"lon={lon_clip[j, i]:.4f}"
            )

#     # Compute stats
#     stats = lambda da: {
#         "mean": float(da.mean().values),
#         "min": float(da.min().values),
#         "max": float(da.max().values)
#     }

#     da_stats = stats(da_clip)

#     results.append({
#         "variable": varname,
#         "burnscar": poly["Name"],
#         "mean_model": da_stats["mean"],
#         "min_model": da_stats["min"],
#         "max_model": da_stats["max"],
#     })

# df = pd.DataFrame(results)