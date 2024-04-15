import pandas as pd
import os
import glob
from obspy import Trace, Stream
from utilities import trace_to_series


class DSAR:
    """Return DSAR per date"""

    def __init__(self, stream: Stream = None, bands: dict[str, list[float]] = None,
                 resample: str = '10m', filters: list[float] = None, corners=4):

        if bands is None:
            bands: dict[str, list[float]] = {
                'LF': [0.1, 4.5, 8.0],
                'HF': [0.1, 8.0, 16.0],
            }

        self.stream: Stream = stream
        self.stream_processed: Stream = Stream()
        self.resample = resample
        self.bands: dict[str, list[float]] = bands
        self.series: dict[str, dict[str, pd.Series]] = {}
        self.dfs: dict[str, pd.DataFrame] = {}

        for trace in self.stream:
            self.series[trace.id]: dict[str, pd.Series] = {}
            self.dfs[trace.id]: pd.DataFrame = pd.DataFrame()

        for band_id, band_values in bands.items():
            print(f'⌚ Processing {band_id} band')
            """Returned stream_processed['HF'] and stream_processed['LF']'"""
            self.stream_processed: Stream = self.processing(stream.copy(), band_values)

            """Returned series[nslc]['HF'] and series[nslc]['LF']"""
            for trace in self.stream_processed:
                series = trace_to_series(trace).resample(resample).median()
                self.series[trace.id][band_id] = series
                self.dfs[trace.id][band_id]: pd.DataFrame = series.to_frame().sort_index()

        self.calculate()

    def calculate(self, dfs: dict[str, pd.DataFrame] = None) -> None:

        if dfs is None:
            dfs: dict[str, pd.DataFrame] = self.dfs

        for station, df in dfs.items():
            default_name: str = 'DSAR_{}'.format(self.resample)

            self.dfs[station][default_name] = (df['LF']/df['HF'])
            self.dfs[station]['DSAR_6h'] = df[default_name].rolling('6h', center=True).median()
            self.dfs[station]['DSAR_24h'] = df[default_name].rolling('24h', center=True).median()

            self.dfs[station] = self.dfs[station].dropna()
            self.dfs[station] = self.dfs[station].loc[~self.dfs[station].index.duplicated(), :]
            self.dfs[station] = self.dfs[station].interpolate('time').interpolate()

    def processing(self, stream: Stream, band_frequencies: list[float]) -> Stream:
        stream.merge(fill_value=0)
        stream.detrend('demean')
        stream.filter('highpass', freq=band_frequencies[0])
        stream.integrate()
        stream.filter('highpass', freq=band_frequencies[1])
        stream.filter('lowpass', freq=band_frequencies[2])
        return stream

    def save(self, output_directory: str = None):

        if output_directory is None:
            output_directory: str = os.path.join(os.getcwd(), 'output', 'dsar')
            os.makedirs(output_directory, exist_ok=True)

        for station, df in self.dfs.items():
            date: str = str(df.first_valid_index()).split(' ')[0]

            csv_directory: str = os.path.join(output_directory, station, self.resample)
            os.makedirs(csv_directory, exist_ok=True)

            csv_file: str = os.path.join(csv_directory, f'{date}_{station}.csv')

            print("💾 Saving to {}".format(csv_file))
            df.to_csv(csv_file, index=True)

    @staticmethod
    def concatenate_csv(dsar_directory: str, station: str, resample: str) -> str:
        df_list: list = []

        csv_files: list[str] = glob.glob(os.path.join(
            dsar_directory, station, resample, "*.csv"))

        for csv in csv_files:
            df = pd.read_csv(csv)
            df_list.append(df)

        big_df = pd.concat(df_list, ignore_index=True)
        big_df = big_df.dropna()
        big_df = big_df.sort_values(by=['datetime'])
        big_df = big_df.reset_index().drop_duplicates(keep='last')

        combined_csv_files: str = os.path.join(
            dsar_directory, station, "combined_{}_{}.csv".format(resample, station))

        columns = ['datetime', f'DSAR_{resample}', 'DSAR_6h', 'DSAR_24h']

        big_df.to_csv(combined_csv_files, index=False, columns=columns)
        return combined_csv_files


