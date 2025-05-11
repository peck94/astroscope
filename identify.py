import pandas as pd

import utils

import numpy as np

from pyongc import data

from tqdm import tqdm

import astropy.units as u
from astropy.coordinates import AltAz, EarthLocation, SkyCoord, get_sun

location = EarthLocation(lat=51.053822, lon=3.722270)
time = utils.get_time()
midnight = utils.get_midnight()

delta_midnight = np.linspace(-12, 12, 24) * u.hour
times = midnight + delta_midnight
frames = AltAz(obstime=times, location=location)
sunaltazs = get_sun(times).transform_to(frames)

dataframe = data.all()
results = []
for _, row in tqdm(list(dataframe.iterrows())):
    obj_name = row["name"]
    if row["vmag"] is None:
        continue

    try:
        dso = SkyCoord.from_name(obj_name)
    except:
        continue
    altazs_obj = dso.transform_to(frames)
    best_times = np.logical_and(np.logical_and(altazs_obj.alt.deg >= 30, altazs_obj.alt.deg <= 70), sunaltazs.alt.deg <= 0)
    if sum(best_times):
        first, last = delta_midnight[best_times][0], delta_midnight[best_times][-1]
        duration = round((last - first).value, 2)
        if duration >= 1:
            first, last = (24 + int(first.value)) % 24, (24 + int(last.value)) % 24
            results.append({
                'Name': obj_name,
                'Type': row["type"],
                'Constellation': row["const"],
                'Rise': first,
                'Set': last,
                'Duration': duration,
                'Magnitude': row["vmag"]
            })

df = pd.DataFrame(results).sort_values(by='Magnitude')
df.to_csv('objects.csv')
