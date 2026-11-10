import os
import argparse
import geopandas as gpd
import numpy as np
import cartopy.crs as ccrs
from pathlib import Path
# from pyproj import CRS, Transformer
import xarray as xr
from shapely.geometry import Point
from rioxarray.exceptions import NoDataInBounds


import globalvars
from reader.io_utils import load_processed_datasets
from modules.wrf_rio import wrf_prepare_for_rio

# ---------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------

parser = argparse.ArgumentParser()

parser.add_argument(
    "--init-date",
    required=True,
    help="Initialization date YYYYMMDDHH",
)

args = parser.parse_args()
init_date = args.init_date

# ==========================================================
# User settings
# ==========================================================

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

keep_names = ["CZU LIGHTNING COMPLEX", "CARMEL", "DOLAN"]
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
burnscar_datasets = []
for _, poly in polys.iterrows():
    print(poly["FIRE_NAME"])
    # ---------------------------------------------------------
    # Clip to burn scar, with fallback for small polygons
    # ---------------------------------------------------------

    spatial_dims = ("south_north", "west_east")

    try:
        da_clip = da.rio.clip(
            [poly.geometry],
            polys.crs,
            drop=True
        )

        print("Using polygon-based clipping")
        print(f"Grid cells selected: {da_clip.sizes['south_north'] * da_clip.sizes['west_east']}")

    except NoDataInBounds:

        print("No grid cells inside polygon. Using 9-km proximity mask.")

        # WRF grid-cell coordinates
        xx, yy = np.meshgrid(
            da["west_east"].values,
            da["south_north"].values
        )

        # Distance from each grid-cell center to the polygon
        distances = np.array([
            poly.geometry.distance(Point(xi, yi))
            for xi, yi in zip(xx.ravel(), yy.ravel())
        ]).reshape(xx.shape)

        # Select cells within 9 km of the polygon
        distance_mask = xr.DataArray(
            distances <= 9000,
            dims=spatial_dims,
            coords={
                "south_north": da["south_north"],
                "west_east": da["west_east"]
            }
        )

        da_clip = da.where(distance_mask, drop=True)

        print("Selected grid cells:", int(distance_mask.sum()))

    # Calculate spatial statistics
    qpf_min = da_clip.min(dim=spatial_dims, skipna=True)
    qpf_max = da_clip.max(dim=spatial_dims, skipna=True)
    qpf_mean = da_clip.mean(dim=spatial_dims, skipna=True)
    
    
    # After calculating qpf_min, qpf_max, and qpf_mean
    fire_name = poly["FIRE_NAME"].replace(" ", "_")
    
    fire_ds = xr.Dataset({
        "qpf_min": qpf_min,
        "qpf_max": qpf_max,
        "qpf_mean": qpf_mean
    })
    
    fire_ds = fire_ds.expand_dims(burnscar=[fire_name])
    burnscar_datasets.append(fire_ds)
    
# Combine all burn scars
combined_ds = xr.concat(burnscar_datasets, dim="burnscar")

# Save
output_fname = f"output/processed/burnscar_clips/ensemble_clip_{init_date}.nc"
combined_ds.to_netcdf(output_fname)