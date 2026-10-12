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

path_to_model = "/home/dnash/comet_data/preprocessed/NRT_WWRF/"
obs_file = "/home/dnash/comet_data/downloads/CZU_RainData_2020-2021.csv"

init_date = "2021012400"

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
# Read WWRF forecast
# ==========================================================

fname = os.path.join(path_to_model, f"wwrf_qpf_{init_date}.nc")
ds = xr.open_dataset(fname)

lat2d = ds["XLAT"].isel(ensemble=0, time=0)
lon2d = ds["XLONG"].isel(ensemble=0, time=0)

ds = ds.assign_coords(
    lat=(("south_north", "west_east"), lat2d.data),
    lon=(("south_north", "west_east"), lon2d.data),
)

ds = ds.drop_vars(["XLAT", "XLONG"])

# ==========================================================
# Subset domain
# ==========================================================

extent = [35, 40, -125, -120]

mask = (
    (ds.lat >= extent[0])
    & (ds.lat <= extent[1])
    & (ds.lon >= extent[2])
    & (ds.lon <= extent[3])
).compute()

y, x = np.where(mask)

ds = ds.isel(
    south_north=slice(y.min(), y.max() + 1),
    west_east=slice(x.min(), x.max() + 1),
)

# ds = ds.chunk({"time": 10, "ensemble": 5})

# ==========================================================
# Compute hourly precipitation
# ==========================================================

rain_rate = ds["RAIN"].diff("time")
rain_rate["time"] = ds.time.isel(time=slice(1, None))
rain_rate = rain_rate.persist()

# ==========================================================
# Find nearest WRF grid cells
# ==========================================================

def nearest_grid(ds, lat0, lon0, method="haversine"):
    if method == "haversine":
        dist = haversine(lat0, lon0, ds.lat.values, ds.lon.values)
    else:
        dist = (ds.lat.values - lat0) ** 2 + (ds.lon.values - lon0) ** 2

    iy, ix = np.unravel_index(np.argmin(dist), dist.shape)

    return iy, ix


gauge_timeseries = {}

for gauge, (lat, lon) in rain_gauges.items():

    iy, ix = nearest_grid(ds, lat, lon)

    gauge_timeseries[gauge] = rain_rate.isel(
        south_north=iy,
        west_east=ix,
    )

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
    figsize=(14, 8),
    sharex=True,
    sharey=True,
)

axes = axes.flatten()

for ax, gauge in zip(axes, rain_gauges.keys()):

    da = gauge_timeseries[gauge].transpose("time", "ensemble")

    times = pd.to_datetime(da.time.values)

    values = da.values

    ens_min = np.nanmin(values, axis=1)
    ens_max = np.nanmax(values, axis=1)
    q25 = np.nanpercentile(values, 25, axis=1)
    median = np.nanpercentile(values, 50, axis=1)
    q75 = np.nanpercentile(values, 75, axis=1)

    ax.fill_between(
        times,
        q25,
        q75,
        alpha=0.3,
        label="25-75%",
    )

    ax.plot(times, ens_min, "--", lw=1, label="Min")
    ax.plot(times, ens_max, "--", lw=1, label="Max")
    ax.plot(times, median, lw=2, label="Median")

    # -----------------------
    # Observations
    # -----------------------

    obs_name = obs_name_map[gauge]

    if obs_name in obs_hourly:

        hourly = obs_hourly[obs_name]

        hourly = hourly[
            (hourly.index >= times.min())
            & (hourly.index <= times.max())
        ]

        ax.scatter(
            hourly.index,
            hourly.values,
            color="k",
            s=18,
            zorder=10,
            label="Obs",
        )

    ax.set_title(gauge.replace("_", " "))
    ax.set_ylabel("Hourly precipitation (mm)")
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

    ax.set_xlim(pd.to_datetime("2021-01-27 00"), pd.to_datetime("2021-01-29 00"))
    ax.axvspan(pd.to_datetime("2021-01-27 07"), pd.to_datetime("2021-01-27 10"), color='red', alpha=0.3, label='Peak Rainfall')

handles, labels = axes[0].get_legend_handles_labels()

fig.legend(
    handles,
    labels,
    loc="upper center",
    ncol=6,
)

fig.tight_layout(rect=[0, 0, 1, 0.93])

fig.savefig( f"figs/ensemble_spread_time_series_{init_date}.png", dpi=300, bbox_inches="tight")