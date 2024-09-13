from .frequency_bands import FrequencyBands, default_bands
from .utilities import trace_to_series
from datetime import datetime
from magma_converter.search import Search
from obspy import read, Stream
from typing_extensions import List, Self

import pandas as pd
import os


class DSAR:
    resample: str = '10min'

    def __init__(self,
                 input_dir: str,
                 start_date: str,
                 end_date: str,
                 directory_structure: str = 'sds',
                 output_dir: str = None,
                 station: str = None,
                 channel: str = None,
                 network: str = None,
                 location: str = None,
                 resample: str = None,):
        self.input_dir = input_dir
        self.start_date = start_date
        self.end_date = end_date
        self.directory_structure = directory_structure.lower()
        self.output_dir = output_dir
        self.resample = resample if resample is not None else self.resample
        self.station = '*' if station is None else station
        self.channel = '*' if channel is None else channel
        self.network = '*' if network is None else network
        self.location = '*' if location is None else location

        self.nslc = f"{self.network}.{self.station}.{self.location}.{self.channel}"
        self.start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        self.end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')

        assert self.start_date_obj <= self.end_date_obj, f"❌ start_date must before end_date"

        self.dfs: dict[str, pd.DataFrame] = {}

        self._first_label: str | None = None
        self._first_bands: dict[str, List[float]] | None = None

        self._second_label: str | None = None
        self._second_bands: dict[str, List[float]] | None = None

    def __repr__(self):
        return (f"DSAR(input_dir={self.input_dir}, start_date={self.start_date}, end_date={self.end_date}, "
                f"directory_structure={self.directory_structure}, resample={self.resample}, "
                f"first_bands={self._first_bands}, second_bands={self._second_bands}, bands={self.bands}")

    def first_bands(self,
                    name: str,
                    first_freq: float,
                    second_freq: float,
                    third_freq: float) -> Self:
        """Set first_bands

        Args:
            name (str): name of band
            first_freq (float): first frequency
            second_freq (float): second frequency
            third_freq (float): third frequency

        Returns:
            Self
        """
        self._first_bands = FrequencyBands(name, first_freq, second_freq, third_freq).to_dict()
        self._first_label = name
        return self

    def second_bands(self,
                     name: str,
                     first_freq: float,
                     second_freq: float,
                     third_freq: float) -> Self:
        """Set second_bands

        Args:
            name (str): name of band
            first_freq (float): first frequency
            second_freq (float): second frequency
            third_freq (float): third frequency

        Returns:
            Self
        """
        self._second_bands = FrequencyBands(name, first_freq, second_freq, third_freq).to_dict()
        self._second_label = name
        return self

    @property
    def bands(self) -> dict[str, list[float]]:
        """Bands of frequencies

        Returns:
            dict[str, list[float]]: band name, and list of frequencies in float. Example {'HF': [0.1, 8.0, 16.0]}
        """
        bands: dict[str, list[float]] = default_bands

        if self._first_bands is not None and self._second_bands is not None:
            bands = {}
            bands.update(self._first_bands)
            bands.update(self._second_bands)

        return bands

    @staticmethod
    def process(stream: Stream, band_frequencies: list[float]) -> Stream:
        """Stream processing based on band frequencies

        Args:
            stream (Stream): Stream to process
            band_frequencies (list[float]): Band frequencies

        Returns:
            Stream: Stream with filtered band frequencies
        """
        assert len(band_frequencies) == 3, (f"❌ Length of band_frequencies must equal 3. "
                                            f"Example [0.1, 8.0, 16.0]")
        stream.merge(fill_value=0)
        stream.detrend('demean')
        stream.filter('highpass', freq=band_frequencies[0])
        stream.integrate()
        stream.filter('highpass', freq=band_frequencies[1])
        stream.filter('lowpass', freq=band_frequencies[2])
        return stream

    def calculate(self, dfs: dict[str, pd.DataFrame]) -> Self:
        """Calculate DSAR

        Args:
            dfs (dict[str, pd.DataFrame]) : Dict of DataFrames(s) with station and band name.

        Returns:
            Self: DSAR object
        """
        first_label = 'LF' if self._first_label is None else self._first_label
        second_label = 'HF' if self._second_label is None else self._second_label

        for station, df in dfs.items():
            default_name: str = 'DSAR_{}'.format(self.resample)

            dfs[station][default_name] = (df[first_label] / df[second_label])
            dfs[station]['DSAR_6h_median'] = df[default_name].rolling('6h', center=True).median()
            dfs[station]['DSAR_24h_median'] = df[default_name].rolling('24h', center=True).median()

            dfs[station] = dfs[station].dropna()
            dfs[station] = dfs[station].loc[~dfs[station].index.duplicated(), :]
            dfs[station] = dfs[station].interpolate('time').interpolate()

        self.dfs = dfs

        return self

    def save(self, date_str: str) ->str:
        """Save DSAR daily calculated

        Args:
            date_str: Date string in yyyy-mm-dd format

        Returns:
            str: CSV file location
        """
        output_directory = self.output_dir

        if output_directory is None:
            output_directory: str = os.path.join(os.getcwd(), 'output', 'dsar')
            os.makedirs(output_directory, exist_ok=True)

        for station, df in self.dfs.items():
            if not df.empty:
                date: str = str(df.first_valid_index()).split(' ')[0]

                csv_directory: str = os.path.join(output_directory, station, self.resample)
                os.makedirs(csv_directory, exist_ok=True)

                csv_file: str = os.path.join(csv_directory, f'{station}_{date}.csv')

                df.to_csv(csv_file, index=True)
                print(f"💾 {date_str} : Saved to {csv_file}")

                return csv_file

            return f'⚠️ {date_str} : Not saved. Not enough data for {station}'

    def run(self) -> None:
        """Run DSAR"""
        dates: pd.DatetimeIndex = pd.date_range(self.start_date, self.end_date, freq='D')

        for date_obj in dates:
            dfs: dict[str, pd.DataFrame] = {}
            date_str: str = date_obj.strftime('%Y-%m-%d')

            print(f'==============================')
            print(f'⌛ {date_str} : Get stream for {date_str}')

            stream: Stream = Search(
                input_dir=self.input_dir,
                directory_structure=self.directory_structure,
                network=self.network,
                station=self.station,
                channel=self.channel,
                location=self.location,
            ).search(date_str=date_str)

            if stream.count() > 0:
                print(f'✅ {date_str} : Found {stream.count()} trace(s) in stream')
                for trace in stream:
                    dfs[trace.id]: pd.DataFrame  = pd.DataFrame()

                for band_name, band_frequencies in self.bands.items():
                    for trace in self.process(stream, band_frequencies):
                        print(f'🧮 {date_str} : Calculating {trace.id} for {band_name}')
                        series = trace_to_series(trace=trace).resample(self.resample).median()
                        dfs[trace.id][band_name]: pd.DataFrame = series.to_frame().sort_index()

                self.calculate(dfs=dfs).save(date_str=date_str)
            else:
                print(f'❌ {date_str} : No trace(s) found. Skip')
