import numpy as np

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # km

    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)
    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))

    return R * c

def get_season_day(timestamp):
    """
    Return climatological season day.

    Dec 1 = 1
    ...
    Mar 31 = 121

    Feb 29 is assigned the same season day as Feb 28.
    """

    month = timestamp.month
    day = timestamp.day

    if month == 12:
        return day

    if month == 1:
        return 31 + day

    if month == 2:
        if day == 29:
            day = 28
        return 62 + day

    if month == 3:
        if calendar.isleap(timestamp.year):
            return 90 + (day - 1)
        else:
            return 90 + day

    raise ValueError("Date outside Dec-Mar")