"""
Filename:    data_loader_and_harmonizer.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: Functions for loading forecast data (WWRF or GEFS) and the associated M-Climate data
Also cleans up and aligns forecast and mclimate so they are directly comparable.
"""

import pandas as pd
import os
import xarray as xr
import numpy as np

from config import DOY_BLOCKS
from utils import globalvars
from reader import load_gefs
from reader import load_wwrf_9km

def convert_leadtime_to_integer_hours(ds):
    
    if np.issubdtype(ds.lead_time.dtype, np.timedelta64):
        ds = ds.assign_coords(
            lead_time=ds.lead_time / np.timedelta64(1, "h")
        )
    
    ds = ds.assign_coords(
        lead_time=ds.lead_time.astype(int)
    )

    return ds

def clean_datetime_attrs(ds):
    for coord in ["init_date", "valid_time"]:
        if coord in ds.coords:
            ds[coord].attrs.pop("units", None)
            ds[coord].attrs.pop("calendar", None)

    return ds

def subset_domain_wwrf(ds, domain):

    ds_yslice, ds_xslice = load_wwrf_9km.get_domain_indices(
        ds.latitude,
        ds.longitude,
        domain,
    )
    
    ds = ds.isel(
        south_north=ds_yslice,
        west_east=ds_xslice,
    )

    return ds

def subset_domain(ds, domain, model):

    if model == "wwrf":
        ds = subset_domain_wwrf(ds, domain)

    else:

        lat = ds.latitude
    
        # handle ascending vs descending latitude
        if lat[0] > lat[-1]:
            lat_slice = slice(domain["lat_max"], domain["lat_min"])
        else:
            lat_slice = slice(domain["lat_min"], domain["lat_max"])
    
        ds = ds.sel(
            longitude=slice(domain["lon_min"], domain["lon_max"]),
            latitude=lat_slice,
        ).sortby('latitude')

    return ds

def standardize_coords(ds):

    coord_map = {
        "lat": "latitude",
        "lon": "longitude",
        "step": "lead_time",
        "time": "init_date",
        "forecast_hour": "lead_time",
        "ensemble": "number",
    }

    var_map = {
        "tp": "qpf",
        "gh": "freezing_level",
        "IVT": "ivt",
        "uIVT": "ivtu",
        "vIVT": "ivtv",
        "RAIN": "qpf",
    }

    coord_rename = {
        k: v
        for k, v in coord_map.items()
        if k in ds.coords or k in ds.dims
    }

    var_rename = {
        k: v
        for k, v in var_map.items()
        if k in ds.data_vars
    }

    return ds.rename(
        coord_rename | var_rename
    )

def longitude_normalizer(ds):
    # -------------------------------------------------
    # Longitude normalization
    # -------------------------------------------------

    if "longitude" not in ds.coords:
        return ds

    lon_min = ds.longitude.min().item()
    lon_max = ds.longitude.max().item()

    # Only normalize if longitudes are in the 0-360 convention
    if lon_min >= 0 and lon_max > 180:
        ds = ds.assign_coords(
            longitude=((ds.longitude + 180) % 360) - 180
        )
        ds = ds.sortby("longitude")

    return ds

def regrid_datasets(forecast, mclimate, model):
    if model == "wwrf":
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
    
    
            mclimate = load_wwrf_9km.remap_to_forecast_grid(
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
    else:
        if (
            not forecast.latitude.equals(mclimate.latitude)
            or not forecast.longitude.equals(mclimate.longitude)
        ):
    
            forecast = forecast.interp(
                latitude=mclimate.latitude,
                longitude=mclimate.longitude,
            )

    return forecast, mclimate

def harmonize_datasets(
    forecast,
    mclimate,
    varname,
    model,
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
    mclimate = standardize_coords(mclimate)

    # -------------------------------------------------
    # 2. Convert lon from 0-360 to -180 to 180
    # -------------------------------------------------

    forecast = longitude_normalizer(forecast)
    mclimate = longitude_normalizer(mclimate)

    # -------------------------------------------------
    # 2. Spatial subset
    # -------------------------------------------------

    forecast = subset_domain(forecast, domain, model)
    mclimate = subset_domain(mclimate, domain, model)

    # -------------------------------------------------
    # 3. Ensemble mean
    # -------------------------------------------------

    if ensemble_mean and "number" in forecast.dims:
        forecast = forecast.mean("number")

    # -------------------------------------------------
    # 4. Rename vars
    # -------------------------------------------------
    mclimate = mclimate.rename({f"{varname}_percentiles": varname})


    # -------------------------------------------------
    # 5. Convert lead times to integer hours
    # -------------------------------------------------

    forecast = convert_leadtime_to_integer_hours(forecast)
    mclimate = convert_leadtime_to_integer_hours(mclimate)

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

    forecast, mclimate = regrid_datasets(forecast, mclimate, model)

    # -------------------------------------------------
    # 8. Standard dimension ordering
    # -------------------------------------------------

    preferred_order = [
        "number",
        "ensemble",
        "init_date",
        "lead_time",
        "latitude",
        "longitude",
    ]
    
    dim_order = [
        d for d in preferred_order
        if d in forecast.dims
    ]
    
    forecast = forecast.transpose(*dim_order)

    # -------------------------------------------------
    # 9. Remove time-encoding attributes 
    # -------------------------------------------------

    forecast = clean_datetime_attrs(forecast)
    mclimate = clean_datetime_attrs(mclimate)

    # -------------------------------------------------
    # 10. Convert lead_time to integer hours
    # -------------------------------------------------
    
    forecast = convert_leadtime_to_integer_hours(forecast)
    mclimate = convert_leadtime_to_integer_hours(mclimate)

    return forecast, mclimate

def prepare_forecast_and_mclimate(
    init_date,
    varname,
    domain,
    model="gefs",
    source="reforecast",
):

    if model == "gefs":
        if source == "reforecast":
            forecast = load_gefs.load_reforecast(
                init_date,
                varname,
            )
    
        elif source == "archive":
            forecast = load_gefs.load_gefs_archive(
                init_date,
                varname,
            )
    
        elif source == "realtime":
            forecast = load_gefs.load_gefs_realtime(
                init_date,
                varname,
            )
    
        else:
            raise ValueError(
                f"Unsupported forecast source: {source}"
            )
    
        mclimate = load_gefs.load_gefs_mclimate(
            init_date,
            varname,
            DOY_BLOCKS,
        )
        
    elif model == "wwrf":
        if source == "realtime":
            forecast = load_wwrf_9km.load_wwrf_nrt_forecast(init_date, varname="QPF")
    
        elif source == "archive":
            forecast = load_wwrf_9km.load_wwrf_archive_forecast(init_date, varname)
            
        mclimate = load_wwrf_9km.load_wwrf_mclimate(
            init_date,
            varname,
        )

    forecast, mclimate = harmonize_datasets(
        forecast=forecast,
        mclimate=mclimate,
        varname=varname,
        model=model,
        domain=domain,
    )

    return forecast, mclimate