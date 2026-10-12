"""
Filename:    colorbars.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: Add colorbars to figure. 
"""

import numpy as np
import matplotlib.colors as mcolors
from matplotlib.colors import ListedColormap

__all__ = ['custom_cmaps']

custom_cmaps =    {
                "mclimate_green" :{ 
                        "colors":[[1.000, 1.000, 0.898], # 75 - 90
                            [0.969, 0.988, 0.725], # 90 - 94
                            [0.851, 0.941, 0.639], # 94 - 95
                            [0.678, 0.867, 0.557], # 95 - 96
                            [0.471, 0.776, 0.475], # 96 - 97
                            [0.255, 0.671, 0.365], # 97 - 98
                            [0.137, 0.518, 0.263], # 98 - 99
                            [0.000, 0.408, 0.216], # 99 - 100
                            [0.000, 0.271, 0.161]], # 100 - 101.
                        "bounds":[75., 90., 94., 95., 96., 97., 98., 99., 100., 101.],
                        "ticks":[75., 90., 94., 95., 96., 97., 98., 99., 100.],
                        "label": 'IVT Percentile Rank (xth)',
                        },
    
                "mclimate_purple" :{
                        "colors":[
                            [0.878, 0.925, 0.957],  # 0. - 75
                            [0.749, 0.827, 0.902], # 75 - 90
                            [0.620, 0.737, 0.855], # 90 - 95
                            [0.549, 0.588, 0.776], # 95 - 97
                            [0.549, 0.420, 0.694], # 97 - 99
                            [0.533, 0.255, 0.616], # 99 - 99.5
                            [0.506, 0.059, 0.486], # 99.5 - 99.8
                            [0.302, 0.000, 0.294], # 99.8 - 99.9
                            [0.000, 0.000, 0.000]], # 99.9 - 100.
                        "bounds":[75., 90., 94., 95., 96., 97., 98., 99., 100., 101.],
                        "ticks":[75., 90., 94., 95., 96., 97., 98., 99., 100.],
                        "label": '1000 hPa Wind Percentile Rank (xth)',
                        },
            "mclimate_red" :{
                        "colors":[
                            [255,245,240],
                            [254,224,210],
                            [252,187,161],
                            [252,146,114],
                            [251,106,74],
                            [239,59,44],
                            [203,24,29],
                            [165,15,21],
                            [103,0,13]],
                        "bounds":[75., 90., 94., 95., 96., 97., 98., 99., 100., 101.],
                        "ticks":[75., 90., 94., 95., 96., 97., 98., 99., 100.],
                        "label": 'Freezing Level Percentile Rank (xth)',
                        },
            "mclimate_blue" :{
                        "colors":[
                            [247,251,255],
                            [222,235,247],
                            [198,219,239],
                            [158,202,225],
                            [107,174,214],
                            [66,146,198],
                            [33,113,181],
                            [8,81,156],
                            [8,48,107]],
                        "bounds":[75., 90., 94., 95., 96., 97., 98., 99., 100., 101.],
                        "ticks":[75., 90., 94., 95., 96., 97., 98., 99., 100.],
                        "label": 'QPF Percentile Rank (xth)',
                        },
    
            "duration" :{
                        "colors":[
                            [241,238,246],
                            [189,201,225],
                            [116,169,207],
                            [5,112,176]],
                        "bounds":[0, 24, 48, 72, 300],
                        "ticks":[0, 24, 48, 72, 300],
                        "label": 'Duration (hr) IVT > 95th percentile',
                        },
            "ar_index" :{
                        "colors":[
                            [255, 255, 255],
                            [211, 223, 231],
                            [250,244,168],
                            [245,150,61],
                            [228,35,47],
                            [120,86,159]],
                        "bounds":[0, 1, 2, 3, 4, 5, 6],
                        "ticks":[0, 1, 2, 3, 4, 5],
                        "label": 'AR Hazard Index',
                        },
}

def cmap(cbarname):
        data = np.array(custom_cmaps[cbarname]["colors"])
        data = data / np.max(data)
        cmap = ListedColormap(data, name=cbarname)
        bnds = custom_cmaps[cbarname]["bounds"]
        norm = mcolors.BoundaryNorm(bnds, cmap.N)
        cbarticks = custom_cmaps[cbarname]["ticks"]
        cbarlbl = custom_cmaps[cbarname]["label"]
        return cmap, norm, bnds, cbarticks, cbarlbl