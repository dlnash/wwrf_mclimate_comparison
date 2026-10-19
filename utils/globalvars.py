"""
Filename:    globalvars.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: Global variables and server-specific paths.
"""

import numpy as np


# --------------------------------------------------
# Server-specific configurations
# --------------------------------------------------

SERVER_CONFIGS = {

    "local": {
        "path_to_data": "/home/dnash/comet_data/",
        "path_to_repo": "/home/dnash/repos/wwrf_mclimate_comparison/",
        "GEFS_REALTIME_DIR": (
            "/data/projects/external_datasets/GEFS/processed"
        ),
        "GEFS_REALTIME_IVT_DIR": (
            "/data/projects/derived_products/GEFS_IVT/data"
        ),
    },
}


# --------------------------------------------------
# Default/static settings
# --------------------------------------------------

leads = np.arange(6, 169, 6)
qpf_leads = np.arange(3, 169, 3)


# --------------------------------------------------
# Active paths
# --------------------------------------------------

path_to_data = None
path_to_repo = None
GEFS_REALTIME_DIR = None
GEFS_REALTIME_INDEX_DIR = None
GEFS_REALTIME_IVT_DIR = None


def configure(server):
    """
    Configure paths for the selected server.

    Parameters
    ----------
    server : str
        Server configuration name, e.g. 'aware' or 'merced'.
    """

    global path_to_data
    global path_to_repo
    global GEFS_REALTIME_DIR
    global GEFS_REALTIME_INDEX_DIR
    global GEFS_REALTIME_IVT_DIR

    if server not in SERVER_CONFIGS:
        valid_servers = ", ".join(SERVER_CONFIGS)
        raise ValueError(
            f"Unknown server '{server}'. "
            f"Valid options are: {valid_servers}"
        )

    config = SERVER_CONFIGS[server]

    path_to_data = config["path_to_data"]
    path_to_repo = config["path_to_repo"]
    GEFS_REALTIME_DIR = config["GEFS_REALTIME_DIR"]
    GEFS_REALTIME_IVT_DIR = config["GEFS_REALTIME_IVT_DIR"]

    GEFS_REALTIME_INDEX_DIR = (
        f"{path_to_repo}data/cfgrib_index_files"
    )