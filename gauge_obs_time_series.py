import os
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from utils import haversine

# ==========================================================
# User settings
# ==========================================================

obs_file = "/home/dnash/comet_data/downloads/CZU_RainData_2020-2021.csv"

rain_gauges = {
    "Big_Basin": (37.172640, -122.222251),
    "Berry_Creek": (37.079284, -122.216055),
    "Brookdale_Lodge": (37.106800, -122.109566),
    "Green_Valley": (37.055999, -122.032146),
}

# Map model gauge names to observation names if needed
obs_name_map = {
    "Big_Basin": "Big_Basin",
    "Berry_Creek": "Berry_Creek",
    "Brookdale_Lodge": "Brookdale_Lodge",
    "Green_Valley": "Green_Valley",
}

# ==========================================================
# Read observations
# ==========================================================

obs = pd.read_csv(obs_file)

obs["DATE_TIME"] = pd.to_datetime(
    obs["DATE_TIME"],
    format="%m/%d/%Y %H:%M:%S",
)

# California local time -> UTC
obs["DATE_TIME"] = (
    obs["DATE_TIME"]
    .dt.tz_localize("America/Los_Angeles")
    .dt.tz_convert("UTC")
    .dt.tz_localize(None)
)

obs = obs.sort_values(["SITE_NAME", "DATE_TIME"])

# ==========================================================
# Hourly accumulations
# ==========================================================

obs_hourly = {}

for site, group in obs.groupby("SITE_NAME"):

    hourly = (
        group.set_index("DATE_TIME")["RAIN_MM"]
        .resample("1h")
        .sum()
    )

    obs_hourly[site] = hourly

# ==========================================================
# Plot
# ==========================================================

fig, axes = plt.subplots(
    2,
    2,
    figsize=(6, 6),
    sharex=True,
    sharey=True,
)

axes = axes.flatten()

for ax, gauge in zip(axes, rain_gauges.keys()):

    # -----------------------
    # Observations
    # -----------------------

    obs_name = obs_name_map[gauge]

    if obs_name in obs_hourly:

        hourly = obs_hourly[obs_name]

        ax.bar(
            hourly.index,
            hourly.values,
            width=1 / 24,
            align="edge",
            color="tab:blue",
            edgecolor="darkblue",
            linewidth=0.6,
            alpha=0.5,
            zorder=10,
            label="Obs",
        )

    ax.set_title(gauge.replace("_", " "))
    ax.set_ylabel("precipitation (mm h-1)")
    ax.grid(alpha=0.3)

# ==========================================================
# X-axis formatting
# ==========================================================

major_locator = mdates.HourLocator(byhour=[0, 6, 12, 18])
minor_locator = mdates.HourLocator(interval=1)

major_formatter = mdates.DateFormatter("%m/%d\n%HZ")

for ax in axes:

    ax.xaxis.set_major_locator(major_locator)
    ax.xaxis.set_minor_locator(minor_locator)
    ax.xaxis.set_major_formatter(major_formatter)

    ax.tick_params(axis="x", which="major", length=6)
    ax.tick_params(axis="x", which="minor", length=3)

    ax.set_xlim(pd.to_datetime("2021-01-26 18"), pd.to_datetime("2021-01-27 18"))
    ax.axvspan(pd.to_datetime("2021-01-27 07"), pd.to_datetime("2021-01-27 10"), color='red', alpha=0.3, label='Peak Rainfall')

handles, labels = axes[0].get_legend_handles_labels()

fig.legend(
    handles,
    labels,
    loc="upper center",
    ncol=6,
)

fig.tight_layout(rect=[0, 0, 1, 0.93])

fig.savefig( f"figs/obs_hourly_time_series.png", dpi=300, bbox_inches="tight")