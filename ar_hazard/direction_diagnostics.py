"""
Filename:    direction_diagnostics.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: functions to compute direction of IVT and UV, compare to aspect
"""

import xarray as xr
import numpy as np

from utils import globalvars
from reader.data_loader_and_harmonizer import standardize_coords

def load_slope_aspect(init_date=None, server="aware"):

    if server == "aware":
        # filename = (
        #     f"/dev/shm/GEFSv12_slope_aspect_{init_date}.nc"
        # )
        filename = (f"{globalvars.path_to_data}preprocessed/GEFSv12_reforecast/GEFSv12_slope_aspect.nc"
        )

    else:
        filename = (
            "/data/projects/operations/"
            "GEFS_Mclimate/data/"
            "GEFSv12_slope_aspect.nc"
        )

    aspect = xr.open_dataset(filename, decode_timedelta=True)
    aspect = standardize_coords(aspect)
    
    return aspect

def compute_flow_directions(fc):
    """
    Compute meteorological flow directions from vector components.
    """

    # -----------------------------------------
    # IVT direction
    # -----------------------------------------

    if {"ivtu", "ivtv"}.issubset(fc.data_vars):

        fc["ivtdir_from"] = (
            270
            - np.degrees(
                np.arctan2(
                    fc["ivtv"],
                    fc["ivtu"],
                )
            )
        ) % 360

        fc["ivtdir_to"] = (fc["ivtdir_from"] + 180) % 360

    # -----------------------------------------
    # Low-level wind direction
    # -----------------------------------------

    if {"u", "v"}.issubset(fc.data_vars):

        fc["uvdir_from"] = (
            270
            - np.degrees(
                np.arctan2(
                    fc["v"],
                    fc["u"],
                )
            )
        ) % 360

        fc["uvdir_to"] = (fc["uvdir_from"] + 180) % 360

    return fc
    
def angular_difference(dir1, dir2):
    return np.abs((dir1 - dir2 + 180) % 360 - 180)
    
def compute_terrain_relative_flow(
    fc,
    final_ds,
    aspect,
):
    """
    Compute flow direction relative to terrain aspect.
    Compute upslope component -1 to 1
    """

        # Upslope component: +1 = directly upslope,
#                     0 = perpendicular,
#                    -1 = directly downslope

    if "ivtdir_to" in fc:
        ivtdir_diff = angular_difference(fc["ivtdir_to"], aspect["aspect"])
        final_ds["ivt_upslope_component"] = -np.cos(np.deg2rad(ivtdir_diff))

    if "uvdir_to" in fc:
        uvdir_diff = angular_difference(fc["uvdir_to"], aspect["aspect"])
        final_ds["uv_upslope_component"] = -np.cos(np.deg2rad(uvdir_diff))

    return final_ds

def compute_direction_diagnostics(
    fc,
    final_ds,
    init_date,
    server="aware",
):
    """
    Compute terrain-relative flow diagnostics.
    """

    # Compute directions
    fc = compute_flow_directions(fc)

    # Load aspect
    aspect = load_slope_aspect(
        init_date=init_date,
        server=server,
    )

    # Match grids if needed
    aspect = aspect.interp(
        latitude=fc.latitude,
        longitude=fc.longitude,
    )

    # Compute terrain-relative flow
    final_ds = compute_terrain_relative_flow(
        fc,
        final_ds,
        aspect,
    )

    aspect.close()

    return fc, final_ds