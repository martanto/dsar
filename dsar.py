import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import os
import glob
from obspy import Stream
from utilities import trace_to_series, plot_eruptions, get_combined_csv


class DSAR:
    """Return DSAR per date"""

    def __init__(self, stream: Stream = None, bands: dict[str, list[float]] = None, resample: str = '10m'):

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
            self.stream_processed: Stream = DSAR.processing(stream.copy(), band_values)

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

            self.dfs[station][default_name] = (df['LF'] / df['HF'])
            self.dfs[station]['DSAR_6h'] = df[default_name].rolling('6h', center=True).median()
            self.dfs[station]['DSAR_24h'] = df[default_name].rolling('24h', center=True).median()

            self.dfs[station] = self.dfs[station].dropna()
            self.dfs[station] = self.dfs[station].loc[~self.dfs[station].index.duplicated(), :]
            self.dfs[station] = self.dfs[station].interpolate('time').interpolate()

    @staticmethod
    def processing(stream: Stream, band_frequencies: list[float]) -> Stream:
        stream.merge(fill_value=0)
        stream.detrend('demean')
        stream.filter('highpass', freq=band_frequencies[0])
        stream.integrate()
        stream.filter('highpass', freq=band_frequencies[1])
        stream.filter('lowpass', freq=band_frequencies[2])
        return stream

    def save(self, output_directory: str = None) -> str:

        if output_directory is None:
            output_directory: str = os.path.join(os.getcwd(), 'output', 'dsar')
            os.makedirs(output_directory, exist_ok=True)

        for station, df in self.dfs.items():

            if df.count() > 1:
                date: str = str(df.first_valid_index()).split(' ')[0]

                csv_directory: str = os.path.join(output_directory, station, self.resample)
                os.makedirs(csv_directory, exist_ok=True)

                csv_file: str = os.path.join(csv_directory, f'{station}_{date}.csv')

                print("💾 Saving to {}".format(csv_file))
                df.to_csv(csv_file, index=True)

                return csv_file

            return f'⚠️💾 Not saved. Not enough data for {station}'

    @staticmethod
    def concatenate_csv(dsar_directory: str, station: str, resample: str) -> str:
        df_list: list = []

        csv_files: list[str] = glob.glob(os.path.join(
            dsar_directory, station, resample, "*.csv"))

        for csv in csv_files:
            df = pd.read_csv(csv)
            if not df.empty:
                df_list.append(df)

        big_df = pd.concat(df_list, ignore_index=True)
        big_df = big_df.dropna()
        big_df = big_df.sort_values(by=['datetime'])
        big_df = big_df.reset_index().drop_duplicates(keep='last')

        combined_csv_files: str = os.path.join(
            dsar_directory, station, "combined_{}_{}.csv".format(resample, station))

        columns = ['datetime', f'DSAR_{resample}', 'DSAR_6h', 'DSAR_24h']

        big_df.to_csv(combined_csv_files, index=False, columns=columns)
        print(f'✅ Saved to {combined_csv_files}')
        return combined_csv_files

    @staticmethod
    def plot_single_graph(dsar_directory: str, station: str, resample: str,
                          interval_day: int = 14, y_min: float = 0, y_max: float = 6.5, title: str = None,
                          axvspans: list[list[str]] = None, axvlines: list[str] = None) -> plt.Figure:

        fig, axs = plt.subplots(nrows=1, ncols=1, figsize=(12, 3),
                                layout="constrained")

        df = get_combined_csv(dsar_directory, station, resample)

        axs.scatter(df.index, df['DSAR_{}'.format(resample)],
                    c='k', alpha=0.3, s=10, label='10min')

        # df['std'] = df['DSAR_{}'.format(resample)].rolling('24h', center=True).mean()
        # axs.plot(df.index, df['std'], c='yellow', label='24h', alpha=1)

        axs.plot(df.index, df['DSAR_24h'], c='red', label='24h', alpha=1)
        axs.set_ylabel('DSAR')

        # axs.set_xlabel('Date')

        axs.xaxis.set_major_locator(mdates.DayLocator(interval=interval_day))
        # axs.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))

        axs.set_ylim(y_min, y_max)
        axs.set_xlim(df.first_valid_index(), df.last_valid_index())

        axs.annotate(
            text='DSAR - ' + station if title is None else title,
            xy=(0.01, 0.92),
            xycoords='axes fraction',
            fontsize='8',
            bbox=dict(facecolor='white', alpha=0.5)
        )

        # Plotting eruptions
        if (axvspans is not None) or (axvlines is not None):
            plot_eruptions(axs, axvspans, axvlines)

        # Add legend
        axs.legend(loc='upper right', fontsize='8', ncol=4)

        # Rotate x label
        for label in axs.get_xticklabels(which='major'):
            label.set(rotation=30, horizontalalignment='right')

        return fig

    @staticmethod
    def plot(dsar_directory: str, stations: list[str], resample: str,
             interval_day: int = 14, y_min: float = 0, y_max: float = 6.5, title: str = None,
             axvspans: list[list[str]] = None, axvlines: list[str] = None) -> plt.Figure:

        fig, axs = plt.subplots(nrows=len(stations), ncols=1, figsize=(12, 3 * len(stations)),
                                layout="constrained", sharex=True)

        for index_key, _station in enumerate(stations):
            df = get_combined_csv(dsar_directory, _station, resample)

            axs[index_key].scatter(df.index, df['DSAR_{}'.format(resample)],
                                   c='k', alpha=0.3, s=10, label='10min')

            axs[index_key].plot(df.index, df['DSAR_24h'], c='red', label='24h', alpha=1)
            axs[index_key].set_ylabel('DSAR')

            if index_key == (len(stations) - 1):
                axs[index_key].set_xlabel('Date')

            axs[index_key].xaxis.set_major_locator(mdates.DayLocator(interval=interval_day))
            axs[index_key].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))

            axs[index_key].set_ylim(y_min, y_max)
            axs[index_key].set_xlim(df.first_valid_index(), df.last_valid_index())

            axs[index_key].annotate(
                text='DSAR - ' + _station if title is None else title,
                xy=(0.01, 0.92),
                xycoords='axes fraction',
                fontsize='8',
                bbox=dict(facecolor='white', alpha=0.5)
            )

            # Plotting eruptions
            if (axvspans is not None) or (axvlines is not None):
                plot_eruptions(axs[index_key], axvspans, axvlines)

            # Add legend
            axs[index_key].legend(loc='upper right', fontsize='8', ncol=4)

            # Rotate x label
            for label in axs[index_key].get_xticklabels(which='major'):
                label.set(rotation=30, horizontalalignment='right')

        return fig
