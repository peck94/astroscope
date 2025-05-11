import numpy as np

import matplotlib.pyplot as plt

from astropy.visualization import astropy_mpl_style, quantity_support

import datetime

import astropy.units as u
from astropy.time import Time
from astropy.coordinates import AltAz, EarthLocation, SkyCoord, get_sun

def get_time():
    return Time(datetime.datetime.now().astimezone(datetime.timezone.utc))

def get_midnight():
    now = datetime.datetime.now()
    midnight = datetime.datetime(now.year, now.month, now.day, 0, 0, 0).astimezone(datetime.timezone.utc)
    return Time(midnight)

def get_location(location_data):
    return EarthLocation(lat=location_data["latitude"], lon=location_data["longitude"])

def float_to_dms(altaz):
    degrees, minutes, seconds = altaz.dms

    return f"{degrees}° {minutes}' {float(seconds):.2f}\""

def get_sky_position(obj_name, location_data):
    try:
        dso = SkyCoord.from_name(obj_name)
        time = get_time()
        location = get_location(location_data)
        return dso.transform_to(AltAz(obstime=time, location=location))
    except:
        return None

def plot_visibility(obj_name, location_data):
    dso = SkyCoord.from_name(obj_name)
    time = get_time()
    location = get_location(location_data)
    obj = dso.transform_to(AltAz(obstime=time, location=location))

    midnight = get_midnight()
    delta_midnight = np.linspace(-12, 12, 1000) * u.hour
    times = midnight + delta_midnight
    frames = AltAz(obstime=times, location=get_location(location_data))
    sunaltazs = get_sun(times).transform_to(frames)

    altazs_obj = obj.transform_to(frames)

    plt.style.use(astropy_mpl_style)
    quantity_support()

    fig, ax = plt.subplots()
    sp = ax.scatter(
        delta_midnight,
        altazs_obj.alt,
        c=altazs_obj.az.value,
        lw=0,
        s=8,
        cmap="viridis",
    )
    ax.fill_between(
        delta_midnight,
        0 * u.deg,
        90 * u.deg,
        sunaltazs.alt < -0 * u.deg,
        color="0.5",
        zorder=0,
    )
    ax.fill_between(
        delta_midnight,
        0 * u.deg,
        90 * u.deg,
        sunaltazs.alt < -18 * u.deg,
        color="k",
        zorder=0,
    )
    ax.axhline(30, 0, 1, ls=":", color='red')
    ax.axhline(70, 0, 1, ls=":", color='red')
    fig.colorbar(sp).set_label("Azimuth [deg]")
    ax.set_xlim(-12 * u.hour, 12 * u.hour)
    ax.set_xticks(ticks=(np.arange(13) * 2 - 12) * u.hour, labels=(np.arange(13) * 2 + 12) % 24)
    ax.set_ylim(0 * u.deg, 90 * u.deg)
    ax.set_xlabel("Hour")
    ax.set_ylabel("Altitude [deg]")

    best_times = np.logical_and(np.logical_and(altazs_obj.alt.deg >= 30, altazs_obj.alt.deg <= 70), sunaltazs.alt.deg <= 0)
    if any(best_times):
        first, last = delta_midnight[best_times][0], delta_midnight[best_times][-1]
        return fig, (24 + int(first.value)) % 24, (24 + int(last.value)) % 24
    else:
        return fig, None, None
