"""
Filename:    forecast_processor.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: multi-variable pipeline to process all variables for forecast and compare to mclimate
"""

import xarray as xr
from data_loader_and_harmonizer import prepare_forecast_and_mclimate
from compare_mclimate import compare_mclimate_to_forecast

def process_variable(
    init_date,
    varname,
    domain,
    source="wwrf",
):
    """
    Load, harmonize, and compare one variable.
    """

    forecast, mclimate = prepare_forecast_and_mclimate(
        init_date=init_date,
        varname=varname,
        domain=domain,
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
    source="wwrf",
    server="merced",
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


    return fc, final_ds