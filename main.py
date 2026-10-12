"""
Main driver for AR hazard processing.
Compute + save
→ comparison to mclimate for given var(s)
→ save nc
"""

import argparse
import yaml
import pandas as pd

from forecast_processor import process_all_variables
from io_utils import save_processed_datasets

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
    default="CA",
)

parser.add_argument(
    "--source",
    default="wwrf",
)

parser.add_argument(
    "--server",
    default="merced",
)

args = parser.parse_args()

init_date = args.init_date
domain_name = args.domain
source = args.source
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
    source=source,
    server=server,
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
