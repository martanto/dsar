# Standard library imports
import os
from datetime import datetime

# Third party imports
import pandas as pd
from obspy import Stream
from typing_extensions import List, Self

# Project imports
from dsar.frequency_bands import FrequencyBands, default_bands
from dsar.sds import SDS
from dsar.utilities import trace_to_series


class DSAR:
    """Calculate Displacement Seismic Amplitude Ratio (DSAR) from SDS seismic data.

    Reads miniSEED files from an SDS archive, applies frequency band filtering and
    displacement integration, computes the ratio between two user-defined bands,
    and saves daily results to CSV.

    Attributes:
        resample (str): Default resampling interval (``"10min"``).

    Example:
        >>> dsar = DSAR(
        ...     station="OJN",
        ...     channel="EHZ",
        ...     network="VG",
        ...     location="00",
        ...     input_dir="/data/sds",
        ...     start_date="2025-01-01",
        ...     end_date="2025-01-08",
        ... )
        >>> dsar.run()
    """

    resample: str = "10min"

    def __init__(
        self,
        station: str,
        channel: str,
        network: str,
        location: str,
        input_dir: str,
        start_date: str,
        end_date: str,
        directory_structure: str = "sds",
        output_dir: str = None,
        resample: str = None,
        verbose: bool = False,
        debug: bool = False,
    ):
        """Initialize and configure the DSAR calculator.

        Args:
            station (str): Station code (e.g., ``"OJN"``).
            channel (str): Channel code (e.g., ``"EHZ"``).
            network (str): Network code (e.g., ``"VG"``).
            location (str): Location code (e.g., ``"00"``).
            input_dir (str): Path to the root SDS data directory.
            start_date (str): Start date in ``YYYY-MM-DD`` format.
            end_date (str): End date in ``YYYY-MM-DD`` format.
            directory_structure (str, optional): Type of directory structure to use.
                Defaults to ``"sds"``.
            output_dir (str, optional): Path to the output directory. Defaults to
                ``<cwd>/output/dsar``.
            resample (str, optional): Pandas offset alias for the resampling interval.
                Defaults to ``"10min"``.
            verbose (bool, optional): Enable verbose logging. Defaults to False.
            debug (bool, optional): Enable debug logging. Defaults to False.

        Raises:
            AssertionError: If ``start_date`` is after ``end_date``.
            FileNotFoundError: If ``input_dir`` does not exist.

        Example:
            >>> dsar = DSAR(
            ...     station="OJN",
            ...     channel="EHZ",
            ...     network="VG",
            ...     location="00",
            ...     input_dir="/data/sds",
            ...     start_date="2025-01-01",
            ...     end_date="2025-01-08",
            ...     resample="10min",
            ...     verbose=True,
            ... )
        """
        self.input_dir = input_dir
        self.start_date = start_date
        self.end_date = end_date
        self.directory_structure = directory_structure.lower()
        self.output_dir = output_dir
        self.resample = resample if resample is not None else self.resample
        self.station = station
        self.channel = channel
        self.network = network
        self.location = location

        self.nslc = f"{self.network}.{self.station}.{self.location}.{self.channel}"
        self.start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        self.sds = SDS(
            input_dir,
            network=self.network,
            station=self.station,
            channel=self.channel,
            location=self.location,
            verbose=verbose,
            debug=debug,
        )

        assert (
            self.start_date_obj <= self.end_date_obj
        ), f"\u274c start_date must be before end_date"

        self.dfs: dict[str, pd.DataFrame] = {}

        self._first_label: str | None = None
        self._first_bands: dict[str, List[float]] | None = None

        self._second_label: str | None = None
        self._second_bands: dict[str, List[float]] | None = None

    def __repr__(self) -> str:
        return (
            f"DSAR(input_dir={self.input_dir}, start_date={self.start_date}, "
            f"end_date={self.end_date}, directory_structure={self.directory_structure}, "
            f"resample={self.resample}, first_bands={self._first_bands}, "
            f"second_bands={self._second_bands}, bands={self.bands})"
        )

    def first_bands(
        self, name: str, first_freq: float, second_freq: float, third_freq: float
    ) -> Self:
        """Set the first frequency band (numerator of the DSAR ratio).

        Args:
            name (str): Label for the frequency band (e.g., ``"LF"``).
            first_freq (float): High-pass filter frequency in Hz applied before
                integration.
            second_freq (float): Lower corner frequency of the bandpass filter in Hz.
            third_freq (float): Upper corner frequency of the bandpass filter in Hz.

        Returns:
            Self: The current DSAR instance, enabling method chaining.

        Raises:
            AssertionError: If frequencies are not in non-decreasing order.

        Example:
            >>> dsar.first_bands(name="LF", first_freq=0.1, second_freq=4.5, third_freq=8.0)
        """
        self._first_bands = FrequencyBands(
            name, first_freq, second_freq, third_freq
        ).to_dict()
        self._first_label = name
        return self

    def second_bands(
        self, name: str, first_freq: float, second_freq: float, third_freq: float
    ) -> Self:
        """Set the second frequency band (denominator of the DSAR ratio).

        Args:
            name (str): Label for the frequency band (e.g., ``"HF"``).
            first_freq (float): High-pass filter frequency in Hz applied before
                integration.
            second_freq (float): Lower corner frequency of the bandpass filter in Hz.
            third_freq (float): Upper corner frequency of the bandpass filter in Hz.

        Returns:
            Self: The current DSAR instance, enabling method chaining.

        Raises:
            AssertionError: If frequencies are not in non-decreasing order.

        Example:
            >>> dsar.second_bands(name="HF", first_freq=0.1, second_freq=8.0, third_freq=16.0)
        """
        self._second_bands = FrequencyBands(
            name, first_freq, second_freq, third_freq
        ).to_dict()
        self._second_label = name
        return self

    @property
    def bands(self) -> dict[str, list[float]]:
        """Return the active frequency bands used for DSAR computation.

        Returns the custom bands if both :meth:`first_bands` and :meth:`second_bands`
        have been set; otherwise returns the default LF/HF bands.

        Returns:
            dict[str, list[float]]: Mapping of band name to a frequency triplet,
                e.g. ``{"LF": [0.1, 4.5, 8.0], "HF": [0.1, 8.0, 16.0]}``.
        """
        bands: dict[str, list[float]] = default_bands

        if self._first_bands is not None and self._second_bands is not None:
            bands = {}
            bands.update(self._first_bands)
            bands.update(self._second_bands)

        return bands

    @staticmethod
    def process(stream: Stream, band_frequencies: list[float]) -> Stream:
        """Process a seismic stream for a given frequency band.

        Applies demean detrending, a high-pass filter, integration to displacement,
        and bandpass filtering using the provided frequency triplet.

        Args:
            stream (Stream): ObsPy Stream to process.
            band_frequencies (list[float]): List of exactly three frequencies in Hz:
                ``[high_pass, bandpass_low, bandpass_high]``.
                Example: ``[0.1, 8.0, 16.0]``.

        Returns:
            Stream: Processed ObsPy Stream containing displacement data.

        Raises:
            AssertionError: If ``band_frequencies`` does not contain exactly 3 values.

        Example:
            >>> processed = DSAR.process(stream, [0.1, 8.0, 16.0])
        """
        assert len(band_frequencies) == 3, (
            f"\u274c band_frequencies must contain exactly 3 values. "
            f"Example: [0.1, 8.0, 16.0]"
        )
        stream.merge(fill_value=0)
        stream.detrend("demean")
        stream.filter("highpass", freq=band_frequencies[0])
        stream.integrate()
        stream.filter("highpass", freq=band_frequencies[1])
        stream.filter("lowpass", freq=band_frequencies[2])
        return stream

    def calculate(self, dfs: dict[str, pd.DataFrame]) -> Self:
        """Calculate DSAR values and rolling median smoothings.

        Computes the ratio of the first to the second frequency band amplitudes,
        then applies 6-hour and 24-hour centered rolling medians. Duplicate indices
        are removed and gaps are interpolated.

        Args:
            dfs (dict[str, pd.DataFrame]): Dictionary mapping station NSLC identifiers
                to DataFrames with columns named after each frequency band.

        Returns:
            Self: The current DSAR instance with ``self.dfs`` populated.

        Example:
            >>> dsar.calculate(dfs={"VG.OJN.00.EHZ": df})
        """
        first_label = "LF" if self._first_label is None else self._first_label
        second_label = "HF" if self._second_label is None else self._second_label

        for station, df in dfs.items():
            default_name: str = "DSAR_{}".format(self.resample)

            dfs[station][default_name] = df[first_label] / df[second_label]
            dfs[station]["DSAR_6h_median"] = (
                df[default_name].rolling("6h", center=True).median()
            )
            dfs[station]["DSAR_24h_median"] = (
                df[default_name].rolling("24h", center=True).median()
            )

            dfs[station] = dfs[station].dropna()
            dfs[station] = dfs[station].loc[~dfs[station].index.duplicated(), :]
            dfs[station] = dfs[station].interpolate("time").interpolate()

        self.dfs = dfs

        return self

    def save(self, date_str: str) -> str | None:
        """Save the daily DSAR calculation results to a CSV file.

        Args:
            date_str (str): Date string in ``YYYY-MM-DD`` format, used for log messages.

        Returns:
            str | None: Path to the saved CSV file if successful; a warning message
                string if the DataFrame is empty; or ``None`` if ``self.dfs`` is empty.

        Example:
            >>> path = dsar.save("2025-01-01")
        """
        output_directory = self.output_dir

        if output_directory is None:
            output_directory: str = os.path.join(os.getcwd(), "output", "dsar")
            os.makedirs(output_directory, exist_ok=True)

        for station, df in self.dfs.items():
            if not df.empty:
                date: str = str(df.first_valid_index()).split(" ")[0]

                csv_directory: str = os.path.join(
                    output_directory, station, self.resample
                )
                os.makedirs(csv_directory, exist_ok=True)

                csv_file: str = os.path.join(csv_directory, f"{station}_{date}.csv")

                df.to_csv(csv_file, index=True)
                print(f"\U0001F4BE {date_str} : Saved to {csv_file}")

                return csv_file

            return f"\u26a0\ufe0f {date_str} : Not saved. Not enough data for {station}"

        return None

    def run(self) -> None:
        """Run the full DSAR pipeline over the configured date range.

        Iterates day by day from ``start_date`` to ``end_date``, loading seismic
        streams from the SDS archive, processing each frequency band, computing
        DSAR ratios, and saving daily CSV files.

        Example:
            >>> dsar.run()
        """
        dates: pd.DatetimeIndex = pd.date_range(
            self.start_date, self.end_date, freq="D"
        )

        for date_obj in dates:
            dfs: dict[str, pd.DataFrame] = {}
            date_str: str = date_obj.strftime("%Y-%m-%d")

            print(f"==============================")
            print(f"\u231b {date_str} : Get stream for {date_str}")

            stream: Stream = self.sds.get(datetime.strptime(date_str, "%Y-%m-%d"))

            if stream.count() > 0:
                print(f"\u2705 {date_str} : Found {stream.count()} trace(s) in stream")
                for trace in stream:
                    dfs[trace.id]: pd.DataFrame = pd.DataFrame()

                for band_name, band_frequencies in self.bands.items():
                    for trace in self.process(stream, band_frequencies):
                        print(f"\U0001F9EE {date_str} : Calculating {trace.id} for {band_name}")
                        series = (
                            trace_to_series(trace=trace)
                            .resample(self.resample)
                            .median()
                        )
                        dfs[trace.id][
                            band_name
                        ]: pd.DataFrame = series.to_frame().sort_index()

                self.calculate(dfs=dfs).save(date_str=date_str)
            else:
                print(f"\u274c {date_str} : No trace(s) found. Skipping")
