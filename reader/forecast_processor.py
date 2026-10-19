"""
Filename:    forecast_processor.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: multi-variable pipeline to process all variables for forecast and compare to mclimate
"""

import xarray as xr
from reader.data_loader_and_harmonizer import prepare_forecast_and_mclimate

from ar_hazard.compare_mclimate import compare_mclimate_to_forecast
from ar_hazard.direction_diagnostics import compute_direction_diagnostics

def process_variable(
    init_date,
    varname,
    domain,
    model="gefs",
    source="reforecast",
):
    """
    Load, harmonize, and compare one variable.
    """

    forecast, mclimate = prepare_forecast_and_mclimate(
        init_date=init_date,
        varname=varname,
        domain=domain,
        model=model,
        source=source,
    )

    comparison = compare_mclimate_to_forecast(
        forecast,
        mclimate,
        varname,
    )

    return forecast, comparison

def process_all_variables(
    init_date,
    var_lst,
    domain,
    model="gefs",
    source="reforecast",
    server="aware",
    derived_diagnostics=True,
):
    """
    Process all variables and merge outputs.
    """

    forecast_datasets = []
    comparison_datasets = []

    for varname in var_lst:

        print(
            f"Processing {varname} "
            f"for {init_date} ({source})"
        )

        forecast, comparison = process_variable(
            init_date=init_date,
            varname=varname,
            domain=domain,
            model=model,
            source=source,
        )

        forecast_datasets.append(forecast)
        comparison_datasets.append(comparison)

    fc = xr.merge(
        forecast_datasets,
        compat="override",
    )

    final_ds = xr.merge(
        comparison_datasets,
        compat="override",
    )

    # -----------------------------------------
    # Derived diagnostics
    # -----------------------------------------
    if derived_diagnostics == True:
        
        fc, final_ds = compute_direction_diagnostics(
            fc,
            final_ds,
            init_date,
            server=server
        )

    return fc, final_ds