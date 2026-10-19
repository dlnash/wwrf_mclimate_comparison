"""
Day-of-year (DOY) block definitions.

Blocks are 10-day windows:
  DOY_001_010, DOY_011_020, ..., DOY_361_365
"""

def make_doy_blocks(step=10, doy_start=1, doy_end=365):
    """
    Generate DOY blocks.

    Parameters
    ----------
    step : int
        Size of each DOY block (default 10 days)
    doy_start : int
        First DOY (default 1)
    doy_end : int
        Last DOY (default 365)

    Returns
    -------
    dict
        Dictionary of DOY blocks keyed by index
    """
    return {
        i: dict(
            name=f"DOY_{start:03d}_{end:03d}",
            doy_min=start,
            doy_max=end,
        )
        for i, (start, end) in enumerate(
            [
                (d, min(d + step - 1, doy_end))
                for d in range(doy_start, doy_end + 1, step)
            ]
        )
    }


# Default 10-day DOY blocks
DOY_BLOCKS = make_doy_blocks()


__all__ = ["DOY_BLOCKS", "make_doy_blocks"]
