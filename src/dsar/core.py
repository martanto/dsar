# Standard library imports
import os
import logging
import warnings
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Third party imports
import pandas as pd
from obspy import Stream
from typing_extensions import Self

from dsar.sds import SDS
from dsar.utilities import trace_to_series

# Project imports
from dsar.frequency_bands import FrequencyBands, default


logger = logging.getLogger(__name__)


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
        output_dir: str | None = None,
        resample: str | None = None,
        n_jobs: int = 1,
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
            output_dir (str, optional): Path to the output directory. Defaults to
                ``<cwd>/output/dsar``.
            resample (str, optional): Pandas offset alias for the resampling interval.
                Defaults to ``"10min"``.
            n_jobs (int, optional): Number of worker threads for parallel date
                processing. Defaults to ``1`` (sequential). Values greater than
                ``1`` use a :class:`~concurrent.futures.ThreadPoolExecutor`.
            verbose (bool, optional): Enable verbose logging. Defaults to False.
            debug (bool, optional): Enable debug logging. Defaults to False.

        Raises:
            ValueError: If ``start_date`` is after ``end_date`` or ``n_jobs`` is invalid.
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
            ...     n_jobs=4,
            ...     verbose=True,
            ... )
        """
        logging.basicConfig(
            level=logging.DEBUG if debug else (logging.INFO if verbose else logging.WARNING)
        )

        self.input_dir = input_dir
        self.start_date = start_date
        self.end_date = end_date
        self.output_dir = output_dir
        self.resample = resample if resample is not None else self.resample
        self.station = station.upper()
        self.channel = channel.upper()
        self.network = network.upper()
        self.location = location.upper()

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

        if self.start_date_obj > self.end_date_obj:
            raise ValueError("start_date must be before or equal to end_date")
        if n_jobs < 1:
            raise ValueError("n_jobs must be greater than or equal to 1")

        self.n_jobs = n_jobs
        self.dfs: dict[str, pd.DataFrame] = {}

        self._lower_label: str | None = None
        self._lower_bands: dict[str, list[float]] | None = None

        self._upper_label: str | None = None
        self._upper_bands: dict[str, list[float]] | None = None

    def __repr__(self) -> str:
        return (
            f"DSAR(input_dir={self.input_dir}, start_date={self.start_date}, "
            f"end_date={self.end_date}, resample={self.resample},"
            f"lower_bands={self._lower_bands}, upper_bands={self._upper_bands}"
            f", bands={self.bands})"
        )

    def lower_bands(
        self, name: str, first_freq: float, second_freq: float, third_freq: float
    ) -> Self:
        """Set the lower frequency band (numerator of the DSAR ratio).

        Args:
            name (str): Label for the frequency band (e.g., ``"LF"``).
            first_freq (float): High-pass filter frequency in Hz applied before
                integration.
            second_freq (float): Lower corner frequency of the bandpass filter in Hz.
            third_freq (float): Upper corner frequency of the bandpass filter in Hz.

        Returns:
            Self: The current DSAR instance, enabling method chaining.

        Raises:
            ValueError: If frequencies are not in non-decreasing order.

        Example:
            >>> dsar.lower_bands(name="LF", first_freq=0.1, second_freq=4.5, third_freq=8.0)
        """
        self._lower_bands = FrequencyBands(
            name, first_freq, second_freq, third_freq
        ).to_dict()
        self._lower_label = name
        return self

    def upper_bands(
        self, name: str, first_freq: float, second_freq: float, third_freq: float
    ) -> Self:
        """Set the upper frequency band (denominator of the DSAR ratio).

        Args:
            name (str): Label for the frequency band (e.g., ``"HF"``).
            first_freq (float): High-pass filter frequency in Hz applied before
                integration.
            second_freq (float): Lower corner frequency of the bandpass filter in Hz.
            third_freq (float): Upper corner frequency of the bandpass filter in Hz.

        Returns:
            Self: The current DSAR instance, enabling method chaining.

        Raises:
            ValueError: If frequencies are not in non-decreasing order.

        Example:
            >>> dsar.upper_bands(name="HF", first_freq=0.1, second_freq=8.0, third_freq=16.0)
        """
        self._upper_bands = FrequencyBands(
            name, first_freq, second_freq, third_freq
        ).to_dict()
        self._upper_label = name
        return self

    def first_bands(
        self, name: str, first_freq: float, second_freq: float, third_freq: float
    ) -> Self:
        """Deprecated alias for :meth:`lower_bands`."""
        warnings.warn(
            "first_bands() is deprecated and will be removed in a future release; "
            "use lower_bands() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.lower_bands(name, first_freq, second_freq, third_freq)

    def second_bands(
        self, name: str, first_freq: float, second_freq: float, third_freq: float
    ) -> Self:
        """Deprecated alias for :meth:`upper_bands`."""
        warnings.warn(
            "second_bands() is deprecated and will be removed in a future release; "
            "use upper_bands() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.upper_bands(name, first_freq, second_freq, third_freq)

    @property
    def bands(self) -> dict[str, list[float]]:
        """Return the active frequency bands used for DSAR computation.

        Returns the custom bands if both :meth:`lower_bands` and :meth:`upper_bands`
        have been set; otherwise returns the default LF/HF bands.

        Returns:
            dict[str, list[float]]: Mapping of band name to a frequency triplet,
                e.g. ``{"LF": [0.1, 4.5, 8.0], "HF": [0.1, 8.0, 16.0]}``.
        """
        if self._lower_bands is not None and self._upper_bands is not None:
            return {**self._lower_bands, **self._upper_bands}

        return dict(default)

    @staticmethod
    def process(stream: Stream, band_frequencies: list[float]) -> Stream:
        """Process a seismic stream for a given frequency band.

        Applies demean detrending, a high-pass filter, integration to displacement,
        and bandpass filtering using the provided frequency triplet.

        Args:
            stream (Stream): ObsPy Stream to process.
            band_frequencies (list[float]): list of exactly three frequencies in Hz:
                ``[high_pass, bandpass_low, bandpass_high]``.
                Example: ``[0.1, 8.0, 16.0]``.

        Returns:
            Stream: Processed ObsPy Stream containing displacement data.

        Raises:
            ValueError: If ``band_frequencies`` does not contain exactly 3 values.

        Example:
            >>> processed = DSAR.process(stream, [0.1, 8.0, 16.0])
        """
        if len(band_frequencies) != 3:
            raise ValueError(
                "band_frequencies must contain exactly 3 values. "
                "Example: [0.1, 8.0, 16.0]"
            )
        stream.merge(fill_value="interpolate")
        stream.detrend("demean")
        stream.filter("highpass", freq=band_frequencies[0])
        stream.integrate()
        stream.filter("highpass", freq=band_frequencies[1])
        stream.filter("lowpass", freq=band_frequencies[2])
        return stream

    def _labels(self) -> tuple[str, str]:
        first_label = "LF" if self._lower_label is None else self._lower_label
        second_label = "HF" if self._upper_label is None else self._upper_label
        return first_label, second_label

    def _calculate_results(self, dfs: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
        first_label, second_label = self._labels()
        result: dict[str, pd.DataFrame] = {}

        for station, df in dfs.items():
            if first_label not in df.columns or second_label not in df.columns:
                raise KeyError(
                    f"Missing expected band columns in {station}: "
                    f"{first_label}, {second_label}"
                )

            station_df = df.copy()
            ratio_name = f"DSAR_{self.resample}"

            station_df[ratio_name] = station_df[first_label] / station_df[second_label]
            station_df["DSAR_6h_median"] = station_df[ratio_name].rolling(
                "6h", center=True
            ).median()
            station_df["DSAR_24h_median"] = station_df[ratio_name].rolling(
                "24h", center=True
            ).median()

            station_df = station_df.dropna()
            station_df = station_df.loc[~station_df.index.duplicated(), :]
            station_df = station_df.interpolate("time").interpolate()

            result[station] = station_df

        return result

    def _save_results(
        self, dfs: dict[str, pd.DataFrame], date_str: str, output_directory: str
    ) -> str | None:
        if not dfs:
            logger.warning("%s :: Nothing to save: no station data", date_str)
            return None

        last_saved: str | None = None
        for station, df in dfs.items():
            if df.empty:
                logger.warning("%s :: Not saved. Not enough data for %s", date_str, station)
                continue

            date: str = str(df.first_valid_index()).split(" ")[0]
            csv_directory = os.path.join(output_directory, station, self.resample)
            os.makedirs(csv_directory, exist_ok=True)

            csv_file = os.path.join(csv_directory, f"{station}_{date}.csv")
            df.to_csv(csv_file, index=True)
            logger.info("%s :: Saved to %s", date_str, csv_file)
            last_saved = csv_file

        return last_saved

    def _output_directory(self) -> str:
        return (
            os.path.join(os.getcwd(), "output", "dsar")
            if self.output_dir is None
            else self.output_dir
        )

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
        self.dfs = self._calculate_results(dfs)
        return self

    def save(self, date_str: str) -> str | None:
        """Save the daily DSAR calculation results to a CSV file.

        Args:
            date_str (str): Date string in ``YYYY-MM-DD`` format, used for log messages.

        Returns:
            str | None: Path to the last saved CSV file if successful, or ``None``
                if ``self.dfs`` is empty or all DataFrames are empty.

        Example:
            >>> path = dsar.save("2025-01-01")
        """
        output_directory = self._output_directory()
        os.makedirs(output_directory, exist_ok=True)
        return self._save_results(self.dfs, date_str, output_directory)

    def _process_date(self, date_obj) -> str | None:
        """Process a single date: load stream, compute DSAR, and save CSV.

        This method is designed to be called concurrently from :meth:`run`. It
        operates entirely on local state — it does not read or write ``self.dfs`` —
        so it is safe to run in parallel across multiple dates.

        Args:
            date_obj: A pandas ``Timestamp`` representing the date to process.

        Returns:
            str | None: Path to the saved CSV file, or ``None`` if no data was found
                or the result was empty.
        """
        dfs: dict[str, pd.DataFrame] = {}
        date_str: str = date_obj.strftime("%Y-%m-%d")

        logger.info("==============================")
        logger.info("%s :: Getting stream", date_str)

        stream: Stream = self.sds.get(datetime.strptime(date_str, "%Y-%m-%d"))

        if stream.count() == 0:
            logger.info("%s :: No trace(s) found. Skipping", date_str)
            return None

        logger.info("%s :: Found %s trace(s) in stream", date_str, stream.count())
        for trace in stream:
            dfs[trace.id] = pd.DataFrame()

        for band_name, band_frequencies in self.bands.items():
            for trace in self.process(stream.copy(), band_frequencies):
                logger.debug(
                    "%s :: Calculating %s for band %s", date_str, trace.id, band_name
                )
                series = trace_to_series(trace=trace).resample(self.resample).median()
                dfs[trace.id][band_name] = series.to_frame().sort_index()

        result = self._calculate_results(dfs)
        output_directory = self._output_directory()
        os.makedirs(output_directory, exist_ok=True)
        return self._save_results(result, date_str, output_directory)

    def run(self) -> None:
        """Run the full DSAR pipeline over the configured date range.

        When ``n_jobs=1`` (the default), dates are processed sequentially.
        When ``n_jobs > 1``, dates are dispatched to a
        :class:`~concurrent.futures.ThreadPoolExecutor` for parallel processing.

        Example:
            >>> dsar.run()
        """
        dates: pd.DatetimeIndex = pd.date_range(
            self.start_date, self.end_date, freq="D"
        )

        if self.n_jobs == 1:
            for date_obj in dates:
                self._process_date(date_obj)
        else:
            with ThreadPoolExecutor(max_workers=self.n_jobs) as executor:
                executor.map(self._process_date, dates)
