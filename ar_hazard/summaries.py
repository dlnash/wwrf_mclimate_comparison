"""
Filename:    summaries.py
Author:      Deanna Nash, dnash@ucsd.edu

Description:
Utilities for generating regional forecast summaries,
heatmap tables, and CSV exports from percentile datasets.
"""

import os
import pandas as pd
import xarray as xr

# ---------------------------------------------------------
# Spatial subsetting
# ---------------------------------------------------------

def subset_domain(ds, extent):
    """
    Spatially subset dataset using extent:
    [lon_min, lon_max, lat_min, lat_max]
    """

    lon_min, lon_max, lat_min, lat_max = extent

    # Handle latitude ordering
    lat_slice = (
        slice(lat_max, lat_min)
        if ds.latitude[0] > ds.latitude[-1]
        else slice(lat_min, lat_max)
    )

    return ds.sel(
        longitude=slice(lon_min, lon_max),
        latitude=lat_slice,
    )


# ---------------------------------------------------------
# Spatial summary statistics
# ---------------------------------------------------------

def compute_spatial_summary(
    ds,
    extent,
    mode="max",
):
    """
    Compute regional summary statistics.

    Parameters
    ----------
    ds : xr.Dataset
        Input dataset

    extent : list
        [lon_min, lon_max, lat_min, lat_max]

    mode : str
        Spatial summary type:
            - "max"
            - "90th"

    Returns
    -------
    xr.Dataset
    """

    ds_sub = subset_domain(ds, extent)

    spatial_dims = ["latitude", "longitude"]

    if mode == "max":

        summary = ds_sub.max(
            dim=spatial_dims,
            skipna=True,
        )

    elif mode == "90th":

        summary = ds_sub.quantile(
            0.9,
            dim=spatial_dims,
            skipna=True,
        )

    else:
        raise ValueError(
            f"Unsupported summary mode: {mode}"
        )

    return summary.fillna(0)


# ---------------------------------------------------------
# DataFrame creation
# ---------------------------------------------------------

def create_summary_dataframe(
    ds,
    extent,
    mode="max",
):
    """
    Create formatted summary dataframe.
    """

    summary = compute_spatial_summary(
        ds,
        extent,
        mode=mode,
    )

    df = summary.to_dataframe()

    # Drop unnecessary coords
    drop_cols = [
        c for c in [
            "init_date",
            "quantile",
            "surface",
            "doy",
            "isobaricInhPa",
            "number"
        ]
        if c in df.columns
    ]

    if drop_cols:
        df = df.drop(columns=drop_cols)

    return df


# ---------------------------------------------------------
# Optional formatting
# ---------------------------------------------------------

def format_summary_dataframe(df):
    """
    Format dataframe for output/visualization.
    """

    # Convert percentile values to %
    percentile_vars = [
        "ivt",
        "freezing_level",
        "uv",
        "qpf",
    ]

    for var in percentile_vars:
        if var in df.columns:
            df[var] *= 100

    return df


# ---------------------------------------------------------
# CSV export
# ---------------------------------------------------------

def get_summary_csv_path(out_root, domain_name, mode, init_date):
    return os.path.join(
        out_root,
        domain_name,
        mode,
        f"mclimate_summary_{init_date}.csv",
    )

def export_summary_csv(
    ds,
    domain_name,
    domain_cfg,
    init_date,
    mode="max",
    out_root="output/csv",
):
    """
    Export regional summary CSV.
    """

    # -----------------------------------------
    # Output directory / fname
    # -----------------------------------------
    
    out_dir = os.path.join(
        out_root,
        domain_name,
        mode,
    )
    
    os.makedirs(out_dir, exist_ok=True)

    # -----------------------------------------
    # Determine summary extent
    # -----------------------------------------

    extent = domain_cfg["extent"]

    bbox_cfg = domain_cfg.get("highlight_box")

    if bbox_cfg:
        extent = bbox_cfg["extent"]

    # -----------------------------------------
    # Create dataframe
    # -----------------------------------------

    df = create_summary_dataframe(
        ds,
        extent,
        mode=mode,
    )

    df = format_summary_dataframe(df)

    # -----------------------------------------
    # Output filename
    # -----------------------------------------

    csv_fname = os.path.join(
    out_dir,
    f"mclimate_summary_{init_date}.csv",
)

    print(f"Writing CSV: {csv_fname}")

    df.to_csv(csv_fname)

    return df

def load_summary_csv(
    domain_name,
    init_date,
    mode="max",
    out_root="output/csv",
):
    """
    Load regional summary CSV.
    """

    csv_fname = os.path.join(
        out_root,
        domain_name,
        mode,
        f"mclimate_summary_{init_date}.csv",
    )

    if not os.path.exists(csv_fname):
        raise FileNotFoundError(f"CSV not found: {csv_fname}")

    keep_cols = [
        "lead_time",
        "ivt",
        "qpf",
        "uv",
        "freezing_level",
        "duration",
        "valid_time",
    ]

    df = pd.read_csv(csv_fname)

    # Keep only columns that exist
    existing_cols = [c for c in keep_cols if c in df.columns]
    df = df[existing_cols]

    # Parse datetime
    if "valid_time" in df.columns:
        df["valid_time"] = pd.to_datetime(df["valid_time"])

    return df