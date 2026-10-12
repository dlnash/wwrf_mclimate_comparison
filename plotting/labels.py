"""
Filename:    labels.py
Author:      Deanna Nash, dnash@ucsd.edu
Description: Functions for labeling the figure
"""

import os
import textwrap
import pandas as pd
from datetime import timedelta
import string
from plotting.configs import kw_ticklabels

def panel_label(i):
    return f"({string.ascii_lowercase[i]})"

def add_panel_label(
    ax,
    label,
    x=-1.25,
    y=1.025,
    fontsize=12,
):
    ax.text(
        x,
        y,
        label,
        ha="left",
        va="top",
        transform=ax.transAxes,
        fontsize=fontsize,
        bbox={
            "facecolor": "white",
            "edgecolor": "none",
            "alpha": 0.9,
            "pad": 2,
        },
        zorder=101,
    )

def get_summary_extent(domain_cfg):
    """
    Return highlight_box extent if available,
    otherwise domain extent.
    """
    highlight_box = domain_cfg.get("highlight_box")

    if highlight_box is not None:
        highlight_extent = highlight_box.get("extent")
        if highlight_extent is not None:
            return highlight_extent

    return domain_cfg.get("extent")

def add_annotation_text(
    fig,
    gs_loc,
    txt,
    wrap_length=35,
    xy=(0, 0),
    xytext=(0, 0),
    ha="left",
    va="bottom",
    text_kwargs=None,
):
    """
    Add annotation text inside a GridSpec location.
    """

    if text_kwargs is None:
        text_kwargs = {}

    ann_ax = fig.add_subplot(gs_loc)
    ann_ax.axis("off")

    ann_ax.annotate(
        textwrap.fill(txt, wrap_length),
        xy,
        textcoords="offset points",
        xytext=xytext,
        ha=ha,
        va=va,
        **kw_ticklabels,
        **text_kwargs,
    )

    return ann_ax
        
def format_lat(lat):
    hemi = "N" if lat >= 0 else "S"
    return f"{abs(lat):.0f}°{hemi}"


def format_lon(lon):
    hemi = "E" if lon >= 0 else "W"
    return f"{abs(lon):.0f}°{hemi}"


def format_forecast_titles(domain_cfg, init_date, lead_time):
    ts = pd.to_datetime(init_date, format="%Y%m%d%H")

    init_time = ts.strftime("%HZ %d %b %Y")
    valid_time = (ts + timedelta(hours=int(lead_time))).strftime("%HZ %d %b %Y")

    start_date = (ts - timedelta(days=10)).strftime("%d-%b")
    end_date = (ts + timedelta(days=10)).strftime("%d-%b")

    extent = get_summary_extent(domain_cfg)
    domain = (
        f"{format_lat(extent[2])} to {format_lat(extent[3])}, "
        f"{format_lon(extent[0])} to {format_lon(extent[1])}"
    )

    return {
        "left": f"Initialized: {init_time}",
        "right": f"F{int(lead_time):03d} | Valid: {valid_time}",
        "heatmap": f"Maximum percentile rank within {domain}",
        "arhazard": (
            f"Relative to all GEFSv12 reforecasts (2000–2019) "
            f"initialized between {start_date} and {end_date} "
            f"at F{int(lead_time):03d}"
        ),
    }