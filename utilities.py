import pandas as pd
import numpy as np
from obspy import Trace, Stream, UTCDateTime
from obspy.clients.filesystem.sds import Client
from datetime import timedelta


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
        if date.strftime('%Y-%m-%d') != stream[0].stats.starttime.strftime('%Y-%m-%d'):
            print("⛔ {} :: File(s) for date {} INVALID!".format(station, date.strftime('%Y-%m-%d')))
            return Stream()
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
