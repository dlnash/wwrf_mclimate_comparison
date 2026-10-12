""" 
Filename: configs.py Author: Deanna Nash, dnash@ucsd.edu 
Description: Plot configuration, colormap configuration, etc. """ 

import numpy as np

# contour labels 
kw_clabels = {'inline': True, 'inline_spacing': 7, 'fmt': '%i', 'rightside_up': True, 'use_clabeltext': True} 
kw_ticklabels = {'color': 'dimgray', 'weight': 'light'} 

PLOT_CONFIG = {
    "ivt": 
    { 
        "cmap": "mclimate_green", 
        "contours": np.arange(250, 2100, 250), 
        "vector": True, 
        "vector_u": "ivtu", 
        "vector_v": "ivtv", 
        "vector_threshold": 250, 
        "label": "IVT", 
    }, 
    
    "uv": 
    { 
        "cmap": "mclimate_purple", 
        "contours": np.arange(0, 55, 5), 
        "vector": True, 
        "vector_u": "u", 
        "vector_v": "v", 
        "vector_threshold": 20, 
        "label": "UV", 
    }, 
    
    "freezing_level": 
    { 
        "cmap": "mclimate_red", 
        "contours": np.arange(0, 60000, 2000), 
        "convert_to_feet": True, #fc[var]*3.281 # convert to feet 
        "vector": False, 
        "label": "Z0", 
    }, 
    
    "qpf": 
    { 
        "cmap": "mclimate_blue", 
        "contours": [0.1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100], 
        "vector": False, 
        "label": "QPF", 
    }, 
    
    "duration" : 
    { 
        "cmap" : "duration", 
        "label" : 'DUR' 
    }, 

}