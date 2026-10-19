def make_lead_time_blocks(max_lt=168, step=6, block_size=3):
    """
    Generate lead-time blocks.

    Parameters
    ----------
    max_lt : int
        Maximum lead time (hours)
    step : int
        Lead time spacing (hours)
    block_size : int
        Number of lead times per block

    Returns
    -------
    dict
    """
    blocks = {}
    lt = list(range(step, max_lt + step, step))

    for i in range(0, len(lt), block_size):
        block = lt[i:i + block_size]
        name = "LT_" + "_".join(f"{x:03d}" for x in block)
        blocks[i // block_size] = dict(
            name=name,
            lead_times=block,
        )

    return blocks


# If you want a ready-to-use constant:
LEAD_TIME_BLOCKS = make_lead_time_blocks()

__all__ = ["LEAD_TIME_BLOCKS", "make_lead_time_blocks"]