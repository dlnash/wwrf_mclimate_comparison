"""
Filename:    gefs_realtime.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: reads GEFS .grb files and extracts variables
"""

import os
import numpy as np
import pandas as pd
import xarray as xr
import time

from utils import globalvars
from reader import grib_helper

filters = {
    "qpf": {
        "dataType": "pf",
        "typeOfLevel": "surface",
        "level:float": 0.0,
        "paramId": 228228,
        "shortName": "tp",
    },
    "u": {
        "dataType": "pf",
        "typeOfLevel": "isobaricInhPa",
        "shortName": "u",
        "level:float": 1000.0,
    },
    "v": {
        "dataType": "pf",
        "typeOfLevel": "isobaricInhPa",
        "shortName": "v",
        "level:float": 1000.0,
    },
    "freezing_level": {
        "dataType": "pf",
        "typeOfLevel": "isothermZero",
        "level:float": 0.0,
        "shortName": "gh",
    },
}

def load_xarray_object_from_grb_using_index(F, varname, init_date): 

    filter_keys = filters[varname]

    indexpath = os.path.join(globalvars.GEFS_REALTIME_INDEX_DIR,
                             f"gefs_{init_date}_F{F:03d}.idx",
                            )

    index = grib_helper.load_index(indexpath)

    subindex = index.subindex(filter_keys)

    xr_ds = grib_helper.dataset_from_subindex(subindex)

    return xr_ds

def load_realtime_ivt(init_date, leads=None):

    init_date = pd.to_datetime(init_date, format="%Y%m%d%H")
    
    filename = os.path.join(
        globalvars.GEFS_REALTIME_IVT_DIR,
        f"GEFS_IVT_{init_date:%Y%m%d%H}.nc",
    )

    ds = xr.open_dataset(filename, decode_timedelta=True)

    return ds

def load_realtime_freezing_level(init_date, leads=None):
    """
    Load GEFS realtime freezing level directly from GRIB2 files.

    Returns
    -------
    xarray.Dataset
        Dataset containing freezing_level with dimensions:
        number, lead_time, latitude, longitude
    """
    t00 = time.perf_counter()
    init_date = pd.to_datetime(init_date, format="%Y%m%d%H")

    if leads is None:
        leads = globalvars.leads

    fdate = init_date.strftime("%Y%m%d%H")

    ds_lst = []

    for F in leads:

        print(f"Reading freezing level: F{F:03d}")

        ds = load_xarray_object_from_grb_using_index(
            F=F, 
            varname="freezing_level", 
            init_date=fdate,
        )

        ds_lst.append(ds)

    ds = xr.concat(ds_lst, dim="step")
    ds = ds.drop_vars("isothermZero")

    print(f"\nTotal time to read freezing level: {time.perf_counter() - t00:.2f} s")

    return ds

def load_realtime_uv(
    init_date,
    leads=None,
):
    """
    Load GEFS realtime wind magnitude at specified hPa level
    directly from GRIB2 files.

    Returns
    -------
    xarray.Dataset
        Dataset containing uv at specified level, with dimensions:
        number, lead_time, latitude, longitude
    """
    t00 = time.perf_counter()
    init_date = pd.to_datetime(init_date, format="%Y%m%d%H")

    if leads is None:
        leads = globalvars.leads

    fdate = init_date.strftime("%Y%m%d%H")

    ds_lst = []

    for F in leads:

        print(f"Reading UV: F{F:03d}")

        u_ds = load_xarray_object_from_grb_using_index(
            F=F, 
            varname="u", 
            init_date=fdate,
        )

        u = u_ds["u"].load()
        u_ds.close()

        v_ds = load_xarray_object_from_grb_using_index(
            F=F, 
            varname="v", 
            init_date=fdate,
        )

        v = v_ds["v"].load()
        v_ds.close()

        ds = xr.merge([u,v,], compat="no_conflicts")

        ds_lst.append(ds)

    # ds = xr.concat(ds_lst, dim="step", coords="minimal",)
    ds = xr.concat(
        ds_lst,
        dim="step",
        coords=["step", "valid_time"],
    )

    # -------------------------------------------------
    # Compute wind magnitude
    # -------------------------------------------------

    ds["uv"] = np.sqrt(
        ds["u"]**2 + ds["v"]**2
    )

    print(f"\nTotal time to read uv: {time.perf_counter() - t00:.2f} s")

    return ds

def fix_accum_qpf(ds):

    tp = ds.tp

    # 3-hour accumulated precipitation:
    # 3, 9, 15, ... h
    prec_3hr = tp.isel(step=slice(0, None, 2))

    # Difference consecutive accumulated fields.
    # These differences give the 6-hour precipitation:
    # 6, 12, 18, ... h
    tp2 = tp.diff(dim="step")

    prec_6hr = tp2.isel(step=slice(0, None, 2))
    prec_6hr = prec_6hr.assign_coords(
        step=tp.step.isel(step=slice(1, None, 2))
    )

    new_prec = prec_3hr.combine_first(prec_6hr)

    ds = ds.drop_vars("tp")
    ds = xr.merge([ds, new_prec])

    return ds
    
def load_realtime_qpf(init_date, leads=None):

    t00 = time.perf_counter()
    init_date = pd.to_datetime(init_date, format="%Y%m%d%H")

    if leads is None:
        leads = globalvars.qpf_leads

    fdate = init_date.strftime("%Y%m%d%H")

    ds_lst = []

    for F in leads:
        print(f"Reading QPF: F{F:03d}")

        ds = load_xarray_object_from_grb_using_index(
            F=F, 
            varname="qpf", 
            init_date=fdate,
        )
    
        ds.load()
        ds.close()

        ds_lst.append(ds)

    ds = xr.concat(ds_lst, dim="step", coords=["valid_time"])

    ds = fix_accum_qpf(ds)
    ds = ds.drop_vars("surface")

    print(f"\nTotal time to read qpf: {time.perf_counter() - t00:.2f} s")

    return ds