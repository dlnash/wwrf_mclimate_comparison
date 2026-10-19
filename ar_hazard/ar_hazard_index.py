"""
Filename:    ar_hazard_index.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: function to compute AR Hazard Index
"""

import xarray as xr

def compute_AR_duration(ds):
    
    # -----------------------------------------
    # Compute AR duration
    # -----------------------------------------
    
    AR = ds.ivt >= 0.95
    
    # lead time spacing in hours
    nhrs = int(
        ds.lead_time.isel(lead_time=1)
        - ds.lead_time.isel(lead_time=0)
    )
    
    # cumulative AR duration
    tmp = (
        AR.cumsum(dim="lead_time")
        - AR.cumsum(dim="lead_time")
            .where(~AR)
            .ffill(dim="lead_time")
            .fillna(0)
            .astype(int)
    )
    
    duration = (
        tmp * nhrs
    ).rename("duration")
    
    ds["duration"] = duration

    return ds
    
def compute_AR_hazard_index(ds):

    # -----------------------------------------
    # IVT magnitude
    # -----------------------------------------
    ## +0.5 Index Point for IVT >= 95th percentile
    AR1 = xr.where(ds.ivt >= 0.95, 0.5, 0.0)
    ARIVT = xr.where(ds.ivt >= 0.98, 0.5, 0.0)

    # -----------------------------------------
    # Freezing level
    # -----------------------------------------
    ## check if init date is between Oct 15 and May 1
    ## if yes, then a point can be assigned
    da = ds.init_date
    cold_season = (
        (da.dt.month > 10)
        | ((da.dt.month == 10) & (da.dt.day > 15))
        | (da.dt.month < 5)
    )

    AR2 = xr.where(
                    cold_season & (ds.freezing_level >= 0.95),
                    1.0,
                    0.0,
                )

    # -----------------------------------------
    # Wind diagnostics
    # -----------------------------------------
    ## +0.5 Index Point for uv >= 95th percentile
    AR3 = xr.where(ds.uv >= 0.95, 0.5, 0.0)

    ## +0.5 Index Point for IVT upslope flow
    dir1 = ((ds.ivt_upslope_component >= 0.8) & (ds.ivt >= 0.95))
    AR6 = xr.where(dir1, 0.5, 0.0)
    
    ## +0.5 Index Point for UV upslope flow
    dir2 = ((ds.uv_upslope_component >= 0.8) & (ds.uv >= 0.95))
    AR7 = xr.where(dir2, 0.5, 0.0)

    # -----------------------------------------
    # Duration
    # -----------------------------------------
    ## calculate duration
    ds = compute_AR_duration(ds)
    
    ## +0.5 Index Point for duration >= 24
    AR4 = xr.where(ds.duration >= 24, 0.5, 0.0)
    
    ## +0.5 Index Point for duration >= 48
    AR5 = xr.where(ds.duration >= 48, 0.5, 0.0)
    

    # -----------------------------------------
    # Precipitation
    # -----------------------------------------

    ## +0.5 Index Point for QPF >= 95th percentile
    AR8 = xr.where(ds.qpf >= 0.95, 0.5, 0.0)

    ## +0.5 Index Point for QPF >= 98th percentile
    AR9 = xr.where(ds.qpf >= 0.98, 0.5, 0.0)

    # -----------------------------------------
    # Final Computation
    # -----------------------------------------
    
    # AR_index = AR1 + AR2 + AR3 + AR4 + AR5
    AR_index = AR1 + AR2 + AR3 + AR4 + AR5 + AR6 + AR7 + AR8 + AR9 + ARIVT
    
    ds["ar_index"] = AR_index

    ds["ar_index"].attrs = {
    "long_name": "Atmospheric River Hazard Index",
    "description": (
        "Composite index based on IVT, duration, "
        "freezing level, terrain-relative flow, "
        "winds, and precipitation"
    ),
}

    return ds