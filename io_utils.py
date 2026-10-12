import os
import xarray as xr

def get_processed_paths(
    init_date,
    source,
    out_dir="output/processed",
):

    base = os.path.join(
        out_dir,
        source,
        init_date,
    )

    os.makedirs(base, exist_ok=True)

    return {
        "forecast": os.path.join(
            base,
            "forecast.nc",
        ),
        "diagnostics": os.path.join(
            base,
            "diagnostics.nc",
        ),
    }


def save_processed_datasets(
    fc,
    ds,
    init_date,
    source,
):

    paths = get_processed_paths(
        init_date,
        source,
    )

    fc.to_netcdf(paths["forecast"])

    ds.to_netcdf(paths["diagnostics"])

    print("Saved:")
    print(paths["forecast"])
    print(paths["diagnostics"])


def load_processed_datasets(
    init_date,
    source,
):

    paths = get_processed_paths(
        init_date,
        source,
    )

    fc = xr.open_dataset(
        paths["forecast"]
    )

    ds = xr.open_dataset(
        paths["diagnostics"]
    )

    return fc, ds