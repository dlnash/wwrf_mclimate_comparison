"""
Filename:    wrf_rio.py
Author:      Deanna Nash, dlnash@ucsb.edu
Description: Function for aligning shapefile and netCDF.

"""
import sys, os
import xarray as xr
import numpy as np
import rioxarray
from pyproj import CRS, Transformer
import globalvars
path_to_data = globalvars.path_to_data

import rioxarray  # for spatial clipping

def wrf_prepare_for_rio(da, x_dim="x", y_dim="y"):
    """
    Prepare a WRF DataArray for rioxarray spatial operations.

    Parameters
    ----------
    da : xarray.DataArray
        WRF DataArray with dims (y_dim, x_dim) and 2D lat/lon coordinates.
    x_dim : str, optional
        Name of the x dimension in da (default "x").
    y_dim : str, optional
        Name of the y dimension in da (default "y").

    Returns
    -------
    da_rio : xarray.DataArray
        Same DataArray with:
        - x/y coordinates in meters
        - rioxarray spatial dims set
        - Lambert Conformal CRS applied
    """
    # --- check dimensions ---
    if x_dim not in da.dims or y_dim not in da.dims:
        raise ValueError(f"DataArray must have '{x_dim}' and '{y_dim}' dimensions")
    
    nx = da.sizes[x_dim]
    ny = da.sizes[y_dim]

    # --- get WRF projection attributes ---
    attrs = da.attrs
    dx = attrs.get("DX", 9000.0)
    dy = attrs.get("DY", 9000.0)
    cen_lat = attrs.get("CEN_LAT", 39.0)
    cen_lon = attrs.get("CEN_LON", -135.0)
    truelat1 = attrs.get("TRUELAT1", 39.0)
    truelat2 = attrs.get("TRUELAT2", 50.0)
    map_proj = attrs.get("MAP_PROJ", 1)

    # --- build CRS for Lambert Conformal ---
    if map_proj == 1:
        crs = CRS.from_proj4(
            f"+proj=lcc +lat_1={truelat1} +lat_2={truelat2} "
            f"+lat_0={cen_lat} +lon_0={cen_lon} "
            f"+a=6370000 +b=6370000 +units=m +no_defs"
        )
    elif map_proj == 6:
        crs = CRS.from_epsg(4326)
    else:
        raise NotImplementedError(f"MAP_PROJ={map_proj} not supported")
    
    # --- project actual 2D latitude/longitude coordinates ---
    if map_proj == 1:
        transformer = Transformer.from_crs(
            "EPSG:4326", crs, always_xy=True
        )
    
        lon2d = da.longitude.values
        lat2d = da.latitude.values
    
        x2d, y2d = transformer.transform(lon2d, lat2d)
    
        # Verify the grid can be represented by 1D x/y coordinates.
        x = np.nanmean(x2d, axis=0)
        y = np.nanmean(y2d, axis=1)
    
        da = da.assign_coords({x_dim: x, y_dim: y})
    else:
        raise NotImplementedError(
            "This coordinate assignment currently supports Lambert Conformal only."
        )

    # --- set spatial dims for rioxarray ---
    da = da.rio.set_spatial_dims(x_dim=x_dim, y_dim=y_dim, inplace=False)

    # --- build CRS for Lambert Conformal ---
    if map_proj == 1:  # Lambert Conformal
        crs = CRS.from_proj4(
            f"+proj=lcc +lat_1={truelat1} +lat_2={truelat2} "
            f"+lat_0={cen_lat} +lon_0={cen_lon} +a=6370000 +b=6370000 +units=m +no_defs"
        )
    elif map_proj == 6:  # Lat/Lon
        crs = CRS.from_epsg(4326)
    else:
        raise NotImplementedError(f"MAP_PROJ={map_proj} not supported")

    # --- write CRS ---
    da.rio.write_crs(crs.to_wkt(), inplace=True)

    return da
