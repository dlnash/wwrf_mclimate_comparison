import os
import yaml
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import cartopy.crs as ccrs
from pathlib import Path
from pyproj import CRS, Transformer

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

# prepare for rioxarray
da = wrf_prepare_for_rio(field, x_dim="west_east", y_dim="south_north")

# reproject shapefile to match WRF CRS
polys = polys.to_crs(da.rio.crs)

# print("\n--- Burn Scar Bounds in WRF Projection ---")
# print(polys.geometry.bounds)

# print(f"\nVariable: {varname}")
# print(f"  Raster CRS: {da.rio.crs}")
# print(f"  Polygon CRS: {polys.crs}")
# print(f"  Raster bounds: {da.rio.bounds()}")
# print(f"  Polygon bounds: {polys.geometry.bounds}")

# --- loop through polygons ---
for _, poly in polys.iterrows():
    # Clip both datasets to polygon
    da_clip = da.rio.clip([poly.geometry], polys.crs, drop=True)
    
    # Calculate statistics across the two spatial dimensions
    spatial_dims = ("south_north", "west_east")
    
    qpf_min = da_clip.min(dim=spatial_dims, skipna=True)
    qpf_max = da_clip.max(dim=spatial_dims, skipna=True)
    qpf_mean = da_clip.mean(dim=spatial_dims, skipna=True)
    
    print("Minimum shape:", qpf_min.shape)
    print("Maximum shape:", qpf_max.shape)
    print("Mean shape:", qpf_mean.shape)
    
    qpf_mean.to_netcdf('test_ensemble_clip_burnscar.nc')