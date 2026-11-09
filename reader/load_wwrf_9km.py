"""
Filename:    load_wwrf_9km.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: Functions for loading 9-km WWRF forecast data (WWRF NRT or WWRF Archive) and the associated M-Climate data
"""
import os
import xarray as xr
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from utils import globalvars

path_to_data = "/cw3e/mead/projects/cwp226/data/"

def get_season_day(timestamp):
    """
    Return climatological season day.

    Dec 1 = 1
    ...
    Mar 31 = 121

    Feb 29 is assigned the same season day as Feb 28.
    """

    month = timestamp.month
    day = timestamp.day

    if month == 12:
        return day

    if month == 1:
        return 31 + day

    if month == 2:
        if day == 29:
            day = 28
        return 62 + day

    if month == 3:
        if calendar.isleap(timestamp.year):
            return 90 + (day - 1)
        else:
            return 90 + day

    raise ValueError("Date outside Dec-Mar")
    
def remap_to_forecast_grid(mclimate, forecast):

    print("Remapping mclimate to forecast grid")

    # Source grid
    src_lat = mclimate.latitude.values
    src_lon = mclimate.longitude.values

    # Target grid
    dst_lat = forecast.latitude.values
    dst_lon = forecast.longitude.values

    src_points = np.column_stack(
        (
            src_lat.ravel(),
            src_lon.ravel(),
        )
    )

    dst_points = np.column_stack(
        (
            dst_lat.ravel(),
            dst_lon.ravel(),
        )
    )

    tree = cKDTree(src_points)

    _, indices = tree.query(dst_points)

    iy, ix = np.unravel_index(
        indices,
        src_lat.shape,
    )

    mclimate = mclimate.isel(
        south_north=xr.DataArray(
            iy.reshape(dst_lat.shape),
            dims=("south_north", "west_east"),
        ),
        west_east=xr.DataArray(
            ix.reshape(dst_lat.shape),
            dims=("south_north", "west_east"),
        ),
    )

    # assign forecast coordinates
    mclimate = mclimate.assign_coords(
        {
            "latitude": forecast.latitude,
            "longitude": forecast.longitude,
        }
    )

    return mclimate

def get_domain_indices(lat, lon, domain):

    mask = (
        (lat >= domain["lat_min"]) &
        (lat <= domain["lat_max"]) &
        (lon >= domain["lon_min"]) &
        (lon <= domain["lon_max"])
    )

    iy, ix = np.where(mask)

    return (
        slice(iy.min(), iy.max() + 1),
        slice(ix.min(), ix.max() + 1),
    )

def load_wwrf_archive_forecast(init_date, varname):
    """
    Loads preprocessed NRT WWRF forecast using lazy Dask arrays.
    Computes 3-hour accumulated precipitation from hourly accumulated QPF.
    """

    print("Loading NRT WWRF Archive Forecast...")

    init_date = pd.to_datetime(init_date, format="%Y%m%d%H")

    filename = os.path.join(
        path_to_data,
        "preprocessed/NRT_WWRF",
        f"wwrf_{varname}_{init_date:%Y%m%d%H}.nc",
    )

    print(filename)

    # Open lazily using Dask
    ds = xr.open_dataset(
        filename,
        chunks="auto",
        decode_timedelta=True,
    )

    # Extract geographic coordinates (small 2D arrays)
    lat2d = ds["XLAT"].isel(ensemble=0, time=0).compute()
    lon2d = ds["XLONG"].isel(ensemble=0, time=0).compute()

    # Work exclusively with precipitation
    rain = ds["RAIN"]

    # Calculate hourly precipitation from accumulated precipitation
    qpf = rain.diff("time")

    # Aggregate hourly precipitation into 3-hour totals
    qpf_3h = qpf.resample(time="3h").sum()

    # Calculate lead time
    lead_hours = (
        (qpf_3h.time - np.datetime64(init_date))
        / np.timedelta64(1, "h")
    ).astype("int32")

    # Build a new, smaller dataset
    out = qpf_3h.to_dataset(name="qpf")

    out = out.assign_coords(
        lat=(("south_north", "west_east"), lat2d.data),
        lon=(("south_north", "west_east"), lon2d.data),
        lead_time=("time", lead_hours.data),
        init_date=np.datetime64(init_date),
    )

    # Rename time dimension and use lead time as dimension
    out = (
        out.rename({"time": "valid_time"})
           .swap_dims({"valid_time": "lead_time"})
    )

    out = out.compute()

    return out


def load_wwrf_nrt_forecast(init_date, varname="QPF"):
    """
    Load a WWRF ensemble forecast and standardize it to the
    format expected by the WWRF model climatology.

    Returns
    -------
    xr.Dataset
    """
    init_date = pd.to_datetime(init_date, format="%Y%m%d%H")
    filename = os.path.join(
        "/data/projects/WWRF-NRT/2025-2026/WWRF_QPF",
        f"{init_date:%Y%m%d%H}/Ensemble",
        f"QPF_WWRF_{init_date:%Y%m%d%H}.nc",
    )

    ds = xr.open_dataset(filename)
    ds = ds.drop_vars(["SNOW"])

    # ---------------------------------------------------------
    # Rename dimensions
    # ---------------------------------------------------------

    rename = {}

    if "ensembles" in ds.dims:
        rename["ensembles"] = "ensemble"

    if "forecast_hour" in ds.dims:
        rename["forecast_hour"] = "lead_time"

    if "lat" in ds.dims:
        rename["lat"] = "south_north"

    if "lon" in ds.dims:
        rename["lon"] = "west_east"

    ds = ds.rename(rename)

    # ---------------------------------------------------------
    # Rename variable
    # ---------------------------------------------------------

    ds = ds.rename(
        {
            varname: "qpf",
            "lat2d": "lat",
            "lon2d": "lon",
        }
    )

    # Promote latitude/longitude to coordinates
    ds = ds.set_coords(["lat", "lon"])

    # ---------------------------------------------------------
    # Build lead_time coordinate
    # ---------------------------------------------------------

    lead_hours = np.arange(
        0,
        3 * (ds.sizes["lead_time"]),
        3,
    )
    print(lead_hours)

    ds = ds.assign_coords(
        lead_time=pd.to_timedelta(
            lead_hours,
            unit="h",
        )
    )

    # ---------------------------------------------------------
    # Add initialization time
    # ---------------------------------------------------------

    ds = ds.assign_coords(
        init_date=init_date
    )

    # ---------------------------------------------------------
    # Compute precipitation rate (mm 3-h) from accumulated QPF
    # ---------------------------------------------------------
    qpf = ds["qpf"].diff("lead_time")
    ds = ds.isel(lead_time=slice(1, None))
    ds["qpf"] = qpf

    return ds

def load_wwrf_mclimate(init_date, varname, base_dir=None):
    """
    Load model climatology dataset based on init_date.

    Parameters
    ----------
    init_date : str
        Initialization date (e.g., '2000011500')
    varname : str
        Variable name (e.g., 'ivt')
    base_dir : str, optional
        Base data directory

    Returns
    -------
    xarray.Dataset
    """
    print("Loading WWRF M-Climate...")
    if base_dir is None:
        base_dir = path_to_data

    # Convert to datetime
    init_date = pd.to_datetime(init_date, format="%Y%m%d%H")
    sd = get_season_day(init_date)

    # Build filename
    filename = os.path.join(
        base_dir,
        f"preprocessed/wwrf_mclimate/{varname}_by_season_day",
        f"mclimate_qpf_season_day_{sd:03d}.nc"
    )

    print(f"Loading Season Day={sd}")
    print(filename)

    ds = xr.open_dataset(filename)

    return ds
