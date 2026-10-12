"""
Filename:    maps.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: Function for adding the maps to the figure axes.
"""
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import matplotlib.patches as mpatches
import cartopy.feature as cfeature
import matplotlib.ticker as mticker
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from matplotlib.colorbar import Colorbar # different way to handle colorbar
import itertools
import geopandas as gpd
from cartopy.feature import ShapelyFeature

from plotting.configs import PLOT_CONFIG, kw_ticklabels, kw_clabels
from plotting.labels import get_summary_extent
import plotting.colorbars as ccmap
import globalvars
path_to_data = globalvars.path_to_data

def plot_fire_perimeters(ax):

    fp = globalvars.path_to_data + 'downloads/calfire/California_Fire_Perimeters.shp'
    polys = gpd.read_file(fp)

    keep_names = ["CZU LIGHTNING COMPLEX","CARMEL", "DOLAN"]
    polys = polys[polys["FIRE_NAME"].isin(keep_names)]
    polys = polys.to_crs(epsg=4326)

    # add to plot
    polys.crs = 'epsg:4326'
    for idx, (i, poly) in enumerate(polys.iterrows()):
        feature = ShapelyFeature([poly.geometry], ccrs.PlateCarree(),
                             edgecolor="red", facecolor='none', linewidth=1.)
        ax.add_feature(feature, zorder=200)

def plot_bbox(ax, bbox_ext, datacrs):
    ax.add_patch(mpatches.Rectangle(xy=[bbox_ext[0], bbox_ext[2]], width=bbox_ext[1]-bbox_ext[0], height=bbox_ext[3]-bbox_ext[2],
                                fill=False,
                                edgecolor='k',
                                linewidth=0.75,
                                transform=datacrs,
                                zorder=199))
    
def draw_basemap(ax, datacrs=ccrs.PlateCarree(), extent=None, xticks=None, yticks=None, grid=False, left_lats=True, right_lats=False, bottom_lons=True, mask_ocean=False, coastline=True):
    """
    Creates and returns a background map on which to plot data. 
    
    Map features include continents and country borders.
    Option to set lat/lon tickmarks and draw gridlines.
    
    Parameters
    ----------
    ax : 
        plot Axes on which to draw the basemap
    
    datacrs : 
        crs that the data comes in (usually ccrs.PlateCarree())
        
    extent : float
        Set map extent to [lonmin, lonmax, latmin, latmax] 
        Default: None (uses global extent)
        
    grid : bool
        Whether to draw grid lines. Default: False
        
    xticks : float
        array of xtick locations (longitude tick marks)
    
    yticks : float
        array of ytick locations (latitude tick marks)
        
    left_lats : bool
        Whether to add latitude labels on the left side. Default: True
        
    right_lats : bool
        Whether to add latitude labels on the right side. Default: False
        
    Returns
    -------
    ax :
        plot Axes with Basemap
    
    Notes
    -----
    - Grayscale colors can be set using 0 (black) to 1 (white)
    - Alpha sets transparency (0 is transparent, 1 is solid)
    
    """
    ## some style dictionaries
    kw_ticklabels = {'size': 10, 'color': 'dimgray', 'weight': 'light'}
    kw_grid = {'linewidth': .5, 'color': 'k', 'linestyle': '--', 'alpha': 0.4}
    kw_ticks = {'length': 4, 'width': 0.5, 'pad': 2, 'color': 'black',
                         'labelsize': 10, 'labelcolor': 'dimgray'}

    # Use map projection (CRS) of the given Axes
    mapcrs = ax.projection    
    
    # Add map features (continents and country borders)
    ax.add_feature(cfeature.LAND, facecolor='0.9')      
    ax.add_feature(cfeature.BORDERS, edgecolor='0.4', linewidth=0.8)
    ax.add_feature(cfeature.STATES, edgecolor='0.4', linewidth=0.5)
    if coastline == True:
        ax.add_feature(cfeature.COASTLINE, edgecolor='0.4', linewidth=0.8)
    if mask_ocean == True:
        ax.add_feature(cfeature.OCEAN, edgecolor='0.4', zorder=12, facecolor='white') # mask ocean
        
    ## Tickmarks/Labels
    ## Add in meridian and parallels
    if mapcrs == ccrs.NorthPolarStereo():
        gl = ax.gridlines(draw_labels=False,
                      linewidth=.5, color='black', alpha=0.5, linestyle='--')
    elif mapcrs == ccrs.SouthPolarStereo():
        gl = ax.gridlines(draw_labels=False,
                      linewidth=.5, color='black', alpha=0.5, linestyle='--')
        
    else:
        gl = ax.gridlines(crs=datacrs, draw_labels=True, **kw_grid)
        gl.top_labels = False
        gl.left_labels = left_lats
        gl.right_labels = right_lats
        gl.bottom_labels = bottom_lons
        gl.xlocator = mticker.FixedLocator(xticks)
        gl.ylocator = mticker.FixedLocator(yticks)
        gl.xformatter = LONGITUDE_FORMATTER
        gl.yformatter = LATITUDE_FORMATTER
        gl.xlabel_style = kw_ticklabels
        gl.ylabel_style = kw_ticklabels
    
    ## Gridlines
    # Draw gridlines if requested
    if (grid == True):
        gl.xlines = True
        gl.ylines = True
    if (grid == False):
        gl.xlines = False
        gl.ylines = False
            

    # apply tick parameters
    ax.set_xticks(xticks, crs=datacrs)
    ax.set_yticks(yticks, crs=datacrs)
    plt.yticks(color='w', size=1) # hack: make the ytick labels white so the ticks show up but not the labels
    plt.xticks(color='w', size=1) # hack: make the ytick labels white so the ticks show up but not the labels
    ax.ticklabel_format(axis='both', style='plain')

    ## Map Extent
    # If no extent is given, use global extent
    if extent is None:        
        ax.set_global()
        extent = [-180., 180., -90., 90.]
    # If extent is given, set map extent to lat/lon bounding box
    else:
        ax.set_extent(extent, crs=datacrs)
    
    return ax
    
def plot_variable_panel(fig, gs_loc, domain_cfg, lats_lbl, ds, fc, lead_time, config_key, cax, labels):
    print(f"Plotting M-Climate map for {config_key}")
    ticks = domain_cfg.get("ticks")
    dx = ticks.get("lon")
    dy = ticks.get("lat")
    ext = domain_cfg.get("extent")
    cfg = PLOT_CONFIG[config_key]
    cmap_name = cfg["cmap"]

    # Set up projection
    mapcrs = ccrs.PlateCarree()
    datacrs = ccrs.PlateCarree()

    ax = fig.add_subplot(gs_loc, projection=mapcrs)

    ax = draw_basemap(ax, extent=ext, xticks=dx, yticks=dy, left_lats=lats_lbl, right_lats=False, bottom_lons=True)

    # Contour Filled (mclimate values)
    scale = 100. if config_key != "ar_index" else 1
    data = ds.sel(lead_time=lead_time)[config_key]*scale
    cmap, norm, bnds, cbarticks, cbarlbl = ccmap.cmap(cmap_name)
    cf = ax.pcolormesh(ds.longitude, ds.latitude, data, transform=datacrs,
                       cmap=cmap, norm=norm, alpha=0.9)

    if config_key != "ar_index":
        # Contour Lines (forecast values)
        forecast = fc[config_key].sel(lead_time=lead_time)     
        cs = ax.contour(fc.longitude, fc.latitude, forecast, transform=datacrs,
                         levels=cfg["contours"], colors='k',
                         linewidths=0.75, linestyles='solid')
        plt.clabel(cs, **kw_clabels)

    ## Plot Normalized Vectors
    kw_quiver = {'headlength': 6, 'headaxislength': 4.5, 'headwidth': 4.5}
    if config_key == 'ivt':
        forecast = fc.sel(lead_time=lead_time) 
        fc_mask = forecast.where((forecast.ivt > 250.))
        
        fcu = fc_mask['ivtu'] / fc_mask['ivt']
        fcv = fc_mask['ivtv'] / fc_mask['ivt']

        q = ax.quiver(fc.longitude, fc.latitude, fcu, fcv, color='k', regrid_shape=20,
                      capstyle='round', units='width', **kw_quiver)

    if config_key == 'uv':
        forecast = fc.sel(lead_time=lead_time) 
        fc_mask = forecast.where((forecast.uv > 20.))
        
        fcu = fc_mask['u'] / fc_mask['uv']
        fcv = fc_mask['v'] / fc_mask['uv']

        q = ax.quiver(fc.longitude, fc.latitude, fcu, fcv, color='0.7', regrid_shape=20,
                      capstyle='round', units='width', **kw_quiver)

    ## add box to map
    plot_bbox(ax, get_summary_extent(domain_cfg), datacrs)

    ## add colorbar
    cbax = plt.subplot(cax) # colorbar axis
    cbarticks = list(itertools.compress(bnds, cbarticks)) ## this labels the cbarticks based on the cmap dictionary
    cb = Colorbar(ax = cbax, mappable = cf, orientation = 'horizontal', 
                  ticklocation = 'bottom', ticks=cbarticks)
    cb.set_label(cbarlbl)

    ## add titles
    ax.set_title(labels["left"], loc="left", fontsize=10)
    ax.set_title(labels["right"], loc="right", fontsize=10)

    return ax
    
    
def plot_ar_index_panel():
    ax = draw_basemap(ax, extent=ext, xticks=dx, yticks=dy, left_lats=True, right_lats=False, bottom_lons=True)
    # Contour Filled (mclimate values)
    data = ds.sel(step=step)['AR_index'].values
    cmap, norm, bnds, cbarticks, cbarlbl = ccmap.cmap('ar_index')
    cf = ax.pcolormesh(lons, lats, data, transform=datacrs,
                       cmap=cmap, norm=norm, alpha=0.9)

    ## add box to map
    ax = add_bbox(ext)


    