"""
Main driver for AR hazard processing.
Compute + save
→ comparison to mclimate for given var(s)
→ save nc
"""

import argparse
import yaml
import pandas as pd

import sys
from pathlib import Path

# Path to the parent repos directory
repos_dir = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(repos_dir))

from reader.forecast_processor import process_all_variables
from reader.io_utils import save_processed_datasets

# ---------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------

parser = argparse.ArgumentParser()

parser.add_argument(
    "--init-date",
    required=True,
    help="Initialization date YYYYMMDDHH",
)

parser.add_argument(
    "--domain",
    default="DEFAULT",
)

parser.add_argument(
    "--source",
    default="archive",
    help="reforecast, archive, realtime",
)

parser.add_argument(
    "--model",
    default="wwrf",
    help="gefs, wwrf",
)

parser.add_argument(
    "--server",
    default="local",
)

args = parser.parse_args()

init_date = args.init_date
domain_name = args.domain
source = args.source
model = args.model
server = args.server


# ---------------------------------------------------------
# Config
# ---------------------------------------------------------

var_lst = [
    "qpf",
]

# ---------------------------------------------------------
# Load domain config
# ---------------------------------------------------------

with open("config/domain.yaml", "r") as f:
    config = yaml.safe_load(f)

domain_cfg = config["domains"][domain_name]

domain = {
    "lon_min": -125.,
    "lon_max": -110.,
    "lat_min": 25.,
    "lat_max": 50.,
}



# ---------------------------------------------------------
# Process variables
# ---------------------------------------------------------
fc, final_ds = process_all_variables(
    init_date=init_date,
    var_lst=var_lst,
    domain=domain,
    ensemble_mean=False,
    model=model,
    source=source,
    server=server,
    derived_diagnostics=False,
)


# ---------------------------------------------------------
# Export netCDFs
# ---------------------------------------------------------
save_processed_datasets(
    fc,
    final_ds,
    init_date,
    source,
)
