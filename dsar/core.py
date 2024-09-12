from .frequency_bands import FrequencyBands, default_bands
from .utilities import trace_to_series
from datetime import datetime
from magma_converter.search import Search
from obspy import read, Stream
from typing_extensions import Dict, List, Self

import pandas as pd


class DSAR:
    resample: str = '10min'

    def __init__(self,
                 input_dir: str,
                 start_date: str,
                 end_date: str,
                 directory_structure: str = 'sds',
                 station: str = None,
                 channel: str = None,
                 network: str = None,
                 location: str = None,
                 resample: str = None,):
        self.input_dir = input_dir
        self.start_date = start_date
        self.end_date = end_date
        self.directory_structure = directory_structure.lower()
        self.resample = resample if resample is not None else self.resample
        self.station = '*' if station is None else station
        self.channel = '*' if channel is None else channel
        self.network = '*' if network is None else network
        self.location = '*' if location is None else location

        self.nslc = f"{self.network}.{self.station}.{self.location}.{self.channel}"
        self.start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        self.end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')

        assert self.start_date_obj <= self.end_date_obj, f"❌ start_date must before end_date"

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
        self._first_bands = FrequencyBands(name, first_freq, second_freq, third_freq).to_dict()
        self._first_label = name
        return self

    def second_bands(self,
                     name: str,
                     first_freq: float,
                     second_freq: float,
                     third_freq: float):
        self._second_bands = FrequencyBands(name, first_freq, second_freq, third_freq).to_dict()
        self._second_label = name
        return self

    @property
    def bands(self) -> dict[str, list[float]]:
        bands: dict[str, list[float]] = default_bands

        if self._first_bands is not None and self._second_bands is not None:
            bands = {}
            bands.update(self._first_bands)
            bands.update(self._second_bands)

        return bands

    @staticmethod
    def process(stream: Stream, band_frequencies: list[float]) -> Stream:
        assert len(band_frequencies) == 3, (f"❌ Length of band_frequencies must equal 3. "
                                            f"Example [0.1, 8.0, 16.0]")
        stream.merge(fill_value=0)
        stream.detrend('demean')
        stream.filter('highpass', freq=band_frequencies[0])
        stream.integrate()
        stream.filter('highpass', freq=band_frequencies[1])
        stream.filter('lowpass', freq=band_frequencies[2])
        return stream

    def calculate(self, dfs: dict[str, pd.DataFrame]) -> None:
        for station, df in dfs.items():
            default_name: str = 'DSAR_{}'.format(self.resample)

            dfs[station][default_name] = (df['LF'] / df['HF'])
            dfs[station]['DSAR_6h'] = df[default_name].rolling('6h', center=True).median()
            dfs[station]['DSAR_24h'] = df[default_name].rolling('24h', center=True).median()

            dfs[station] = dfs[station].dropna()
            dfs[station] = dfs[station].loc[dfs[station].index.duplicated(), :]
            dfs[station] = dfs[station].interpolate('time').interpolate()

    def run(self):
        dates: pd.DatetimeIndex = pd.date_range(self.start_date, self.end_date, freq='D')

        for date_obj in dates:
            dfs: dict[str, pd.DataFrame] = {}
            date_str: str = date_obj.strftime('%Y-%m-%d')
            stream: Stream = Search(
                input_dir=self.input_dir,
                directory_structure=self.directory_structure,
                network=self.network,
                station=self.station,
                channel=self.channel,
                location=self.location,
            ).search(date_str=date_str)

            if stream.count() > 0:
                for trace in stream:
                    dfs[trace.id]: pd.DataFrame  = pd.DataFrame()

                for band_name, band_frequencies in self.bands.items():
                    for trace in self.process(stream, band_frequencies):
                        series = trace_to_series(trace=trace).resample(self.resample).median()
                        dfs[trace.id][band_name]: pd.DataFrame = series.to_frame().sort_index()

                self.calculate(dfs=dfs)