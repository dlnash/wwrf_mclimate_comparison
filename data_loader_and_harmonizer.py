"""
Filename:    data_loader_and_harmonizer.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: Functions for loading forecast data (GEFSv12 Reforecast, GEFS Archive, or GEFS operational) and the associated M-Climate data
Also cleans up and aligns forecast and mclimate so they are directly comparable.
"""

import pandas as pd
import os
import xarray as xr
import numpy as np
from pathlib import Path
import re

from utils import get_season_day
import globalvars

path_to_data = globalvars.path_to_data

from scipy.spatial import cKDTree


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

def standardize_coords(ds):

    coord_map = {
        "lat": "latitude",
        "lon": "longitude",
        "step": "lead_time",
        "time": "valid_time",
    }

    var_map = {
        "RAIN": "qpf",
    }

    coord_rename = {
        k: v for k, v in coord_map.items()
        if k in ds.coords or k in ds.dims
    }

    var_rename = {
        k: v for k, v in var_map.items()
        if k in ds.data_vars
    }

    ds = ds.rename(coord_rename)
    ds = ds.rename(var_rename)

    return ds

def harmonize_datasets(
    forecast,
    mclimate,
    varname,
    ensemble_mean=True,
    domain=None,
):
    """
    Harmonize forecast and mclimate datasets
    so they are directly comparable.
    """
    print('Harmonizing forecast and mclimate datasets')
    # -------------------------------------------------
    # 1. Rename coordinates
    # -------------------------------------------------

    forecast = standardize_coords(forecast)
    # print(forecast)
    mclimate = standardize_coords(mclimate)
    # print(mclimate)
    
    # -------------------------------------------------
    # 2. Spatial subset
    # -------------------------------------------------

    forecast_yslice, forecast_xslice = get_domain_indices(
        forecast.latitude,
        forecast.longitude,
        domain,
    )
    
    forecast = forecast.isel(
        south_north=forecast_yslice,
        west_east=forecast_xslice,
    )
    
    
    mclimate_yslice, mclimate_xslice = get_domain_indices(
        mclimate.latitude,
        mclimate.longitude,
        domain,
    )
    
    mclimate = mclimate.isel(
        south_north=mclimate_yslice,
        west_east=mclimate_xslice,
    )

    print("Forecast latitude max/min")
    print(forecast.latitude.min().values,
          forecast.latitude.max().values)
    print("Mclimate latitude max/min")
    print(mclimate.latitude.min().values,
          mclimate.latitude.max().values)
    print("Forecast longitude max/min")
    print(forecast.longitude.min().values,
          forecast.longitude.max().values)
    print("Mclimate longitude max/min")
    print(mclimate.longitude.min().values,
          mclimate.longitude.max().values)

    # Check to see if mclimate and forecast are the same size
    print("Forecast shape")
    print(forecast.latitude.shape)
    print("Mclimate shape")
    print(mclimate.latitude.shape)

    print("Forecast grid size")
    print(
        np.nanmean(
            np.sqrt(
                (np.diff(forecast.latitude.values, axis=0)**2)
                +
                (np.diff(forecast.longitude.values, axis=0)**2)
            )
        )
    )
    print("Mclimate grid size")
    print(
        np.nanmean(
            np.sqrt(
                (np.diff(mclimate.latitude.values, axis=0)**2)
                +
                (np.diff(mclimate.longitude.values, axis=0)**2)
            )
        )
    )

    # -------------------------------------------------
    # 3. Ensemble mean
    # -------------------------------------------------

    if ensemble_mean and "ensemble" in forecast.dims:
        forecast = forecast.mean("ensemble")

    # -------------------------------------------------
    # 4. Rename vars
    # -------------------------------------------------
    mclimate = mclimate.rename({f"{varname}_percentile": varname})


    # -------------------------------------------------
    # 5. Convert lead times to integer hours
    # -------------------------------------------------
    if np.issubdtype(forecast.lead_time.dtype, np.timedelta64):

        lead_hours = (
            forecast.lead_time.values
            / np.timedelta64(1, "h")
        ).astype(int)

        forecast = forecast.assign_coords(
            lead_time=lead_hours
        )

    if np.issubdtype(mclimate.lead_time.dtype, np.timedelta64):

        lead_hours = (
            mclimate.lead_time.values
            / np.timedelta64(1, "h")
        ).astype(int)

        mclimate = mclimate.assign_coords(
            lead_time=lead_hours
        )

    # -------------------------------------------------
    # 6. Match lead times
    # -------------------------------------------------
    common_leads = np.intersect1d(
        forecast.lead_time,
        mclimate.lead_time,
    )

    forecast = forecast.sel(lead_time=common_leads)
    mclimate = mclimate.sel(lead_time=common_leads)

    # -------------------------------------------------
    # 7. Regrid if needed
    # -------------------------------------------------

    same_grid = (
        forecast.latitude.shape == mclimate.latitude.shape
        and np.allclose(
            forecast.latitude,
            mclimate.latitude,
            atol=1e-3,
        )
        and np.allclose(
            forecast.longitude,
            mclimate.longitude,
            atol=1e-3,
        )
    )

    if same_grid != True:

        print("Grid mismatch: remapping mclimate")


        mclimate = remap_to_forecast_grid(
            mclimate,
            forecast,
        )
    print("Difference in latitude grid after remap")
    print(
        np.nanmax(
            np.abs(
                forecast.latitude.values -
                mclimate.latitude.values
            )
        )
    )

    print("Difference in longitude grid after remap")
    print(
        np.nanmax(
            np.abs(
                forecast.longitude.values -
                mclimate.longitude.values
            )
        )
    )

    # -------------------------------------------------
    # 8. Standard dimension ordering
    # -------------------------------------------------

    # dim_order = [
    #     d for d in [
    #         "lead_time",
    #         "latitude",
    #         "longitude",
    #     ]
    #     if d in forecast.dims
    # ]

    # forecast = forecast.transpose(*dim_order)
    # mclimate = mclimate.transpose(*dim_order)

    return forecast, mclimate

def load_forecast(init_date, varname):
    """
    Loads preprocessed NRT WWRF forecast (works for WY2020-21)
    """
    init_date = pd.to_datetime(init_date, format="%Y%m%d%H")

    filename = os.path.join(
        path_to_data,
        "preprocessed/NRT_WWRF",
        f"wwrf_{varname}_{init_date:%Y%m%d%H}.nc",
    )

    print(filename)

    ds = xr.open_dataset(filename)

    lat2d = ds["XLAT"].isel(ensemble=0, time=0)
    lon2d = ds["XLONG"].isel(ensemble=0, time=0)
    
    # Add geographic coordinates
    ds = ds.assign_coords(
        lat=(("south_north", "west_east"), lat2d.data),
        lon=(("south_north", "west_east"), lon2d.data),
    )

    # ---------------------------------------------------------
    # Compute precipitation rate (mm 1-h) from accumulated QPF
    # ---------------------------------------------------------
    qpf = ds["RAIN"].diff("time")
    ds = ds.isel(time=slice(1, None))
    ds["RAIN"] = qpf

    
    # resample from hourly to 3-h to match mclimate
    ds = ds.resample(time='3h').sum()
    
    # Compute lead time from timestamps
    lead_hours = (
        (ds.time - np.datetime64(init_date))
        / np.timedelta64(1, "h")
    ).astype(int)
    
    # Rename time -> valid_time and make lead_time the dimension
    ds = (
        ds.rename({"time": "valid_time",
                  "RAIN": "qpf"})
          .assign_coords(lead_time=("valid_time", lead_hours.data))
          .swap_dims({"valid_time": "lead_time"})
    )
    
    # Store initialization time
    ds = ds.assign_coords(init_date=init_date)

    return ds


def load_wwrf_forecast(init_date, varname="QPF"):
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

def load_mclimate(init_date, varname, base_dir=None):
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


def prepare_forecast_and_mclimate(init_date, varname, domain, source="wwrf"):

    if source == "wwrf":
        forecast = load_wwrf_forecast(init_date, varname="QPF")

    elif source == "wwrf-preprocessed":
        forecast = load_forecast(init_date, varname)
        
    mclimate = load_mclimate(
        init_date,
        varname,
    )
    
    forecast, mclimate = harmonize_datasets(
        forecast=forecast,
        mclimate=mclimate,
        varname=varname,
        domain=domain,
    )

    return forecast, mclimate