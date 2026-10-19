"""
Filename:    load_gefs.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: Functions for loading GEFS forecast data (GEFSv12 Reforecast, GEFS Archive, or GEFS operational) and the associated M-Climate data
"""

import os
import pandas as pd
import xarray as xr

from utils import globalvars
from reader import gefs_realtime

def load_reforecast(init_date, varname):

    init_date = pd.to_datetime(init_date, format="%Y%m%d%H")

    filename = os.path.join(
        globalvars.path_to_data,
        "preprocessed/GEFSv12_reforecast",
        f"{varname}_final",
        f"GEFSv12_reforecast_{varname}_{init_date:%Y%m%d}.nc",
    )

    print(filename)

    ds = xr.open_dataset(filename, decode_timedelta=True)

    return ds

def load_gefs_archive(init_date, varname):

    init_date = pd.to_datetime(init_date, format="%Y%m%d%H")

    filename = os.path.join(
        globalvars.path_to_data,
        "preprocessed/GEFS",
        f"{varname}",
        f"{init_date:%Y%m%d}_{varname}.nc",
    )

    print(filename)

    ds = xr.open_dataset(filename, decode_timedelta=True)

    return ds

def load_gefs_realtime(init_date, varname):

    if varname == "freezing_level":
        return gefs_realtime.load_realtime_freezing_level(init_date)

    elif varname == "uv":
        return gefs_realtime.load_realtime_uv(init_date)

    elif varname == "qpf":
        return gefs_realtime.load_realtime_qpf(init_date)

    elif varname == "ivt":
        return gefs_realtime.load_realtime_ivt(init_date)

    else:
        raise ValueError(f"Unsupported realtime variable: {varname}")

def load_gefs_mclimate(init_date, varname, doy_blocks, base_dir=None):
    """
    Load model climatology dataset based on init_date and DOY blocks.

    Parameters
    ----------
    init_date : str, int, or datetime-like
        Initialization date (e.g., '20000115', 20000115, or datetime)
    varname : str
        Variable name (e.g., 'ivt')
    doy_blocks : dict
        Dictionary of DOY blocks (e.g., DOY_BLOCKS)
    base_dir : str, optional
        Base data directory

    Returns
    -------
    xarray.Dataset
    """

    if base_dir is None:
        base_dir = globalvars.path_to_data

    # Convert to datetime
    init_date = pd.to_datetime(init_date, format="%Y%m%d%H")
    doy = init_date.dayofyear

    # Handle leap year edge case (optional but recommended)
    if doy == 366:
        doy = 365

    # Find matching DOY block
    block_name = None
    for block in doy_blocks.values():
        if block["doy_min"] <= doy <= block["doy_max"]:
            block_name = block["name"]
            break

    if block_name is None:
        raise ValueError(f"No DOY block found for DOY={doy}")

    # Build filename
    filename = os.path.join(
        base_dir,
        f"preprocessed/mclimate_2.0/{varname}/concat_DOY",
        f"mclimate_{varname}_{block_name}.nc"
    )

    print(f"Loading DOY={doy} → {block_name}")
    print(filename)

    ds = xr.open_dataset(filename)
    ds = ds.sel(doy=doy)

    return ds