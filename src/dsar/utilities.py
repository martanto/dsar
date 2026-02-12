# Standard library imports
from datetime import datetime, timedelta

# Third party imports
import numpy as np
import pandas as pd
from obspy import Stream, Trace, UTCDateTime
from obspy.clients.filesystem.sds import Client


def fill_streams(client: Client, station: str, date: UTCDateTime) -> Stream:
    """Load a seismic stream from an SDS client for a given station and date.

    Validates that the loaded stream matches the requested date. Returns an empty
    Stream if no files are found or the returned data does not match the requested date.

    Args:
        client (Client): ObsPy SDS filesystem client.
        station (str): NSLC identifier in ``"Network.Station.Location.Channel"`` format
            (e.g., ``"VG.OJN.00.EHZ"``).
        date (UTCDateTime): Start date of the data to retrieve.

    Returns:
        Stream: ObsPy Stream containing the waveform data, or an empty Stream if
            no data is found or the date does not match.

    Example:
        >>> from obspy.clients.filesystem.sds import Client
        >>> from obspy import UTCDateTime
        >>> client = Client("/data/sds")
        >>> stream = fill_streams(client, "VG.OJN.00.EHZ", UTCDateTime("2025-01-01"))
    """
    _network, _station, _location, _channel = station.split(".")

    stream = client.get_waveforms(
        network=_network,
        station=_station,
        location=_location,
        channel=_channel,
        starttime=date,
        endtime=date + timedelta(days=1),
    )

    if stream.count():
        stream_date: str = stream[0].stats.starttime.strftime("%Y-%m-%d")
        if date.strftime("%Y-%m-%d") != stream_date:
            print(
                "\u26a0\ufe0f {} :: File(s) for date {} vs {} INVALID!".format(
                    station, date.strftime("%Y-%m-%d"), stream_date
                )
            )
            return stream
        print(
            "\u2139\ufe0f {} :: File(s) for date {} OK!".format(
                station, date.strftime("%Y-%m-%d")
            )
        )
        return stream
    else:
        print(
            "\u26a0\ufe0f {} :: File(s) for date {} not found!".format(
                station, date.strftime("%Y-%m-%d")
            )
        )
        return Stream()


def trace_to_series(trace: Trace) -> pd.Series:
    """Convert an ObsPy Trace to a pandas Series of absolute amplitude values.

    The resulting Series uses a DatetimeIndex derived from the trace start time
    and sample interval, and contains the absolute values of the raw waveform data.

    Args:
        trace (Trace): ObsPy Trace object to convert.

    Returns:
        pd.Series: Series of absolute amplitude values with a ``"datetime"``-named
            DatetimeIndex and name ``"values"``.

    Example:
        >>> series = trace_to_series(trace)
        >>> series.resample("10min").median()
    """
    index_time = pd.date_range(
        start=trace.stats.starttime.datetime,
        periods=trace.stats.npts,
        freq="{}ms".format(trace.stats.delta * 1000),
    )

    _series = pd.Series(
        data=np.abs(trace.data), index=index_time, name="values", dtype=trace.data.dtype
    )

    _series.index.name = "datetime"

    return _series


def trace_to_dataframe(trace: Trace) -> pd.DataFrame:
    """Convert an ObsPy Trace to a single-column pandas DataFrame.

    Wraps :func:`trace_to_series` and promotes the result to a DataFrame.

    Args:
        trace (Trace): ObsPy Trace object to convert.

    Returns:
        pd.DataFrame: Single-column DataFrame with a ``"datetime"``-named index
            and a ``"values"`` column of absolute amplitude values.

    Example:
        >>> df = trace_to_dataframe(trace)
    """
    return trace_to_series(trace).to_frame()


def calculate_per_band(frequencies: list[float], trace: Trace, corners: int = 4) -> pd.Series:
    """Apply a bandpass filter to a trace and return amplitude as a Series.

    Filters the trace between the first and last values in ``frequencies`` using a
    Butterworth bandpass filter, then converts to a pandas Series of absolute amplitude
    values via :func:`trace_to_series`.

    Args:
        frequencies (list[float]): List of at least two frequencies in Hz. The first
            element is used as ``freqmin`` and the last as ``freqmax``.
        trace (Trace): ObsPy Trace object to filter.
        corners (int, optional): Number of filter corners (filter order). Defaults to 4.

    Returns:
        pd.Series: Absolute amplitude values of the filtered trace as a pandas Series.

    Example:
        >>> series = calculate_per_band([0.1, 8.0], trace)
    """
    trace = trace.filter(
        "bandpass", freqmin=frequencies[0], freqmax=frequencies[-1], corners=corners
    )
    return trace_to_series(trace)


def plot_continuous_eruption(axes, axvspans: list[list[str]]):
    """Overlay shaded spans on a matplotlib axes to mark continuous eruption periods.

    Args:
        axes (matplotlib.axes.Axes): The axes on which to draw the spans.
        axvspans (list[list[str]]): List of ``[start_date, end_date]`` pairs in
            YYYY-MM-DD format defining each eruption interval.

    Returns:
        matplotlib.axes.Axes: The modified axes with eruption spans added.

    Example:
        >>> plot_continuous_eruption(ax, [["2024-01-10", "2024-01-15"]])
    """
    for key, continuous in enumerate(axvspans):
        axes.axvspan(
            continuous[0],
            continuous[1],
            alpha=0.4,
            color="orange",
            label="_" * key + "Continuous Eruption",
        )

    return axes


def plot_single_eruption(axes, axvlines: list[str]):
    """Overlay vertical lines on a matplotlib axes to mark discrete eruption events.

    Args:
        axes (matplotlib.axes.Axes): The axes on which to draw the lines.
        axvlines (list[str]): List of date strings in YYYY-MM-DD format, one per event.

    Returns:
        matplotlib.axes.Axes: The modified axes with eruption lines added.

    Example:
        >>> plot_single_eruption(ax, ["2024-02-01", "2024-03-15"])
    """
    for key, date in enumerate(axvlines):
        axes.axvline(
            datetime.strptime(date, "%Y-%m-%d"),
            color="red",
            label="_" * key + "Single Eruption",
        )
    return axes


def plot_eruptions(axes, axvspans: list[list[str]] = None, axvlines: list[str] = None):
    """Overlay eruption markers on a matplotlib axes.

    Combines :func:`plot_continuous_eruption` and :func:`plot_single_eruption` into a
    single convenience function. Either or both arguments can be provided.

    Args:
        axes (matplotlib.axes.Axes): The axes on which to draw the markers.
        axvspans (list[list[str]], optional): List of ``[start_date, end_date]`` pairs
            for continuous eruption intervals. Defaults to None.
        axvlines (list[str], optional): List of date strings in YYYY-MM-DD format for
            discrete eruption events. Defaults to None.

    Returns:
        matplotlib.axes.Axes: The modified axes with eruption markers added.

    Example:
        >>> plot_eruptions(
        ...     ax,
        ...     axvspans=[["2024-01-10", "2024-01-15"]],
        ...     axvlines=["2024-02-01"],
        ... )
    """
    if axvspans is not None:
        plot_continuous_eruption(axes, axvspans)

    if axvlines is not None:
        plot_single_eruption(axes, axvlines)

    return axes


def get_combined_csv(directory: str, station: str, resample: str) -> pd.DataFrame:
    """Load a pre-combined DSAR CSV file into a DataFrame.

    Reads the combined CSV produced by :meth:`PlotDsar.df` and parses the
    ``datetime`` column as the index.

    Args:
        directory (str): Path to the DSAR output directory containing the combined CSV.
        station (str): NSLC identifier (e.g., ``"VG.RUA3.00.EHZ"``).
        resample (str): Resampling interval used during DSAR calculation
            (e.g., ``"10min"``).

    Returns:
        pd.DataFrame: DataFrame with a parsed ``datetime`` index.

    Raises:
        FileNotFoundError: If the combined CSV file does not exist at the expected path.

    Example:
        >>> df = get_combined_csv("output/dsar", "VG.RUA3.00.EHZ", "10min")
    """
    import os

    df = pd.read_csv(
        os.path.join(
            directory, station, "combined_{}_{}.csv".format(resample, station)
        ),
        index_col="datetime",
        parse_dates=True,
        date_format="%Y-%m-%d %H:%M:%S",
    )

    return df
