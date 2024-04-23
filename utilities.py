import pandas as pd
import numpy as np
import os
from obspy import Trace, Stream, UTCDateTime
from obspy.clients.filesystem.sds import Client
from datetime import timedelta
from datetime import datetime


def fill_streams(client: Client, station: str, date: UTCDateTime) -> Stream:
    """Return stream from SDS Directory based on network, station, location and channel"""
    _network, _station, _location, _channel = station.split('.')

    stream = client.get_waveforms(
        network=_network,
        station=_station,
        location=_location,
        channel=_channel,
        starttime=date,
        endtime=date + timedelta(days=1)
    )

    # Check if stream is not empty (files not found)
    # Return empty Stream if files are not found
    if stream.count():
        stream_date: str = stream[0].stats.starttime.strftime('%Y-%m-%d')
        if date.strftime('%Y-%m-%d') != stream_date:
            print("⚠️ {} :: File(s) for date {} vs {} INVALID!".format(station, date.strftime('%Y-%m-%d'), stream_date))
            return stream
        print('ℹ️ {} :: File(s) for date {} OK!'.format(station, date.strftime('%Y-%m-%d')))
        return stream
    else:
        print("⚠️ {} :: File(s) for date {} not found!".format(station, date.strftime('%Y-%m-%d')))
        return Stream()


def trace_to_series(trace: Trace) -> pd.Series:
    index_time = pd.date_range(
        start=trace.stats.starttime.datetime,
        periods=trace.stats.npts,
        freq="{}ms".format(trace.stats.delta * 1000)
    )

    _series = pd.Series(
        data=np.abs(trace.data),
        index=index_time,
        name='values',
        dtype=trace.data.dtype)

    _series.index.name = 'datetime'

    return _series


def trace_to_dataframe(trace: Trace) -> pd.DataFrame:
    return trace_to_series(trace).to_frame()


def calculate_per_band(frequencies: list[float], trace: Trace, corners=4) -> pd.Series:
    trace = trace.filter('bandpass', freqmin=frequencies[0],
                         freqmax=frequencies[-1], corners=corners)
    return trace_to_series(trace)


def plot_continuous_eruption(axes, axvspans: list[list[str]]):
    for key, continuous in enumerate(axvspans):
        # continuous[0] = start date of eruption
        # continuous[1] = end date of eruption
        axes.axvspan(continuous[0], continuous[1], alpha=0.4,
                     color='orange', label="_" * key + 'Continuous Eruption')

    return axes


def plot_single_eruption(axes, axvlines: list[str]):
    for key, date in enumerate(axvlines):
        axes.axvline(datetime.strptime(date, '%Y-%m-%d'),
                    color='red', label="_" * key + 'Single Eruption')
    return axes


def plot_eruptions(axes, axvspans: list[list[str]] = None, axvlines: list[str] = None):
    if axvspans is not None:
        plot_continuous_eruption(axes, axvspans)

    if axvlines is not None:
        plot_single_eruption(axes, axvlines)

    return axes


def get_combined_csv(directory: str, station: str, resample: str) -> pd.DataFrame:
    df = pd.read_csv(os.path.join(
        directory, station, 'combined_{}_{}.csv'.format(resample, station)),
        index_col='datetime', parse_dates=True, date_format = '%Y-%m-%d %H:%M:%S')

    return df
