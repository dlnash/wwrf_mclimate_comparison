"""
Filename:    grib_helper.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: wrapper to use in-memory index to read .grb files for multiple variables
"""

import os
import sys
import xarray as xr
import numpy as np
import pickle
import cfgrib.xarray_plugin as xarray_plugin
from cfgrib.dataset import open_fileindex
from cfgrib.messages import FileStream, FileIndex
from cfgrib.dataset import build_dataset_components
from cfgrib.dataset import Dataset as CfgribDataset
import time

from utils import globalvars

class SimpleDataStore:
    """
    lightweight object that provides the lock and cfgrib Dataset
    """
    
    def __init__(self, ds):
        self.ds = ds
        self.lock = xarray_plugin.ECCODES_LOCK

    def open_store_variable(self, var):
        if isinstance(var.data, np.ndarray):
            data = var.data
        else:
            wrapped_array = xarray_plugin.CfGribArrayWrapper(
    self, var.data
)
            data = xr.core.indexing.LazilyIndexedArray(wrapped_array)

        encoding = self.ds.encoding.copy()
        encoding["original_shape"] = var.data.shape

        return xr.Variable(
            var.dimensions,
            data,
            var.attributes,
            encoding,
        )

    def get_variables(self):
        return xr.core.utils.FrozenDict(
            (k, self.open_store_variable(v))
            for k, v in self.ds.variables.items()
        )

    def get_attrs(self):
        return xr.core.utils.Frozen(self.ds.attributes)

    def get_dimensions(self):
        return xr.core.utils.Frozen(self.ds.dimensions)


def build_index_and_save(fname, indexpath):
    
    index_keys = [
        "centre",
        "centreDescription",
        "dataDate",
        "dataTime",
        "dataType",
        "directionNumber",
        "edition",
        "endStep",
        "frequencyNumber",
        "gridType",
        "level:float",
        "md5GridSection",
        "number",
        "numberOfPoints",
        "paramId",
        "shortName",
        "step",
        "stepType",
        "stepUnits",
        "subCentre",
        "time",
        "typeOfLevel",
        "uvRelativeToGrid",
    ]

    stream = FileStream(fname)

    index = open_fileindex(
        stream,
        indexpath="",
        index_keys=index_keys,
        filter_by_keys={},
    )

    with open(indexpath, "wb") as f:
        pickle.dump(index, f)

    return index

def build_and_save_index_files(F, init_date):
        
    fname = os.path.join(
        globalvars.GEFS_REALTIME_DIR,
        init_date,
        f"gefs_{init_date}_F{F:03d}.grb2",
    )

    indexpath = os.path.join(globalvars.GEFS_REALTIME_INDEX_DIR,
                             f"gefs_{init_date}_F{F:03d}.idx",
                            )

    print(f"Starting F{F:03d}")
    t0 = time.perf_counter()
    
    index = build_index_and_save(fname, indexpath)

    elapsed = time.perf_counter() - t0
    print(f"Finished F{F:03d}: {elapsed:.2f} s")

    return F, elapsed

def load_index(indexpath):
    return FileIndex.from_indexpath(indexpath)

def dataset_from_subindex(subindex):

    dimensions, variables, attributes, encoding = build_dataset_components(
        subindex,
        errors="warn",
        encode_cf=("parameter", "time", "geography", "vertical"),
    )
    
    # Build the cfgrib Dataset container
    cf_ds = CfgribDataset(
        dimensions,
        variables,
        attributes,
        encoding,
    )
    
    # Wrap it for xarray
    store = SimpleDataStore(cf_ds)
    
    # Construct actual xarray Dataset
    xr_ds = xr.Dataset(
        store.get_variables(),
        attrs=store.get_attrs(),
    )

    for coord in ["time", "step", "valid_time"]:
        if coord in xr_ds:
            xr_ds = xr_ds.set_coords(coord)

    # Decode GRIB Unix timestamps
    for coord in ["time", "valid_time"]:
        if coord in xr_ds:
            xr_ds[coord] = xr_ds[coord].astype("datetime64[ns]")

    return xr_ds
