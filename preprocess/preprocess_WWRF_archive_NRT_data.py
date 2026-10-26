import os
import glob
import xarray as xr
import pandas as pd

def normalize_time(ds):
    # Convert WRF Times (bytes) to datetime
    # 2021-01-27_00:00:00
    times = pd.to_datetime(ds['Times'].astype(str), format='%Y-%m-%d_%H:%M:%S')

    # Round to nearest hour (or use .floor('H') if you prefer)
    times = times.round('H')

    # Assign back
    ds = ds.assign_coords(time=("Time", times))
    ds = ds.swap_dims({"Time": "time"})
    ds = ds.drop_vars("Times")

    return ds
    
def get_ensemble_paths(base_path):
    """
    Returns dict: {ensemble_name: path_to_files}
    """
    ens_paths = {}

    for subdir in ["wrfprd", "wrfprd2"]:
        full_path = os.path.join(base_path, subdir)
        if not os.path.exists(full_path):
            continue

        for ens in sorted(os.listdir(full_path)):
            ens_dir = os.path.join(full_path, ens)
            if os.path.isdir(ens_dir):
                ens_paths[ens] = ens_dir

    return ens_paths

def process_member(path_to_member, keep_vars=["RAIN"]):
    files = sorted(glob.glob(os.path.join(path_to_member, "hourly_d01_*")))

    ds_lst = []
    for file in files:
        ds = xr.open_dataset(file, engine="netcdf4")

        # normalize time
        ds = normalize_time(ds)

        # compute rain
        ds["RAIN"] = ds["RAINC"] + ds["RAINNC"]

        # keep only needed vars
        ds = ds[[v for v in keep_vars if v in ds]]

        ds_lst.append(ds)

    if not ds_lst:
        return None

    return xr.concat(ds_lst, dim="time")


WY = '2020-2021'
init_date = '2021012200'

base_path = f'/data/projects/WWRF-NRT/{WY}/Full_Output/ens/COMET/cw3eprod/{init_date}'

ens_paths = get_ensemble_paths(base_path)

ens_datasets = []

for ens_name, ens_path in ens_paths.items():
    print(f"Processing {ens_name}")

    ds = process_member(ens_path)

    if ds is None:
        continue

    # assign ensemble coordinate
    ds = ds.expand_dims({"ensemble": [ens_name]})

    ens_datasets.append(ds)

## Ensure time alignment across members
ref_time = ens_datasets[0].time

for ds in ens_datasets:
    if not ds.time.equals(ref_time):
        print("Time mismatch:", ds.ensemble.values)
        
# concat across ensemble
final_ds = xr.concat(ens_datasets, dim="ensemble")

# --- Save to NetCDF ---
path_to_out = "/home/dnash/comet_data/preprocessed/NRT_WWRF/"
out_file = os.path.join(path_to_out, f"wwrf_qpf_{init_date}.nc")
print(f"Writing QPF for {init_date} to {out_file}")
final_ds.to_netcdf(out_file, mode="w", format="NETCDF4")