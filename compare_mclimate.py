"""
Filename:    compare_mclimate.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: Compare forecast to mclimate percentiles
"""

import xarray as xr
import numpy as np


def compare_mclimate_to_forecast(fc, mclimate, varname):
    """
    Compare forecast values to mclimate quantile thresholds.

    Parameters
    ----------
    fc : xr.Dataset
        Forecast dataset
    mclimate : xr.Dataset
        Mclimate dataset containing quantiles
    varname : str
        Variable name

    Returns
    -------
    xr.Dataset
        Dataset containing exceeded quantile values
    """

    forecast = fc[varname]
    climatology = mclimate[varname]

    quantiles = mclimate["quantile"].values

    # initialize output with NaNs
    # result = xr.full_like(forecast, np.nan, dtype=float)
    result = xr.full_like(forecast, quantiles[0], dtype=float) # use this depending on plotting needs

    # progressively overwrite with highest exceeded quantile
    for i, q in enumerate(quantiles):

        threshold = climatology.isel(quantile=i)

        result = xr.where(
            forecast >= threshold,
            q,
            result,
        )

    # package into dataset
    ds = result.to_dataset(name=varname)

    # preserve init date if available
    if "init_date" in fc.coords:
        ds = ds.assign_coords(init_date=fc.init_date)

    return ds