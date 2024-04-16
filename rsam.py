import pandas as pd
import os
import numpy as np
import glob
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from obspy import Stream
from utilities import trace_to_series, calculate_per_band, plot_eruptions, get_combined_csv


class RSAM:
    def __init__(self, stream: Stream = None, resample: str = '10m', filters: list[float] = None,
                 bands: dict[str, list[float]] = None, corners=4):

        if bands is None:
            bands: dict[str, list[float]] = {
                'VLP': [0.02, 0.2],
                'LP': [0.5, 4.0],
                'VT': [4.0, 18.0]
            }

        self.resample = resample
        self.bands: dict[str, list[float]] = bands
        self.metrics: list[str] = ['min', 'max', 'mean', 'median', 'rms']
        self.dataframes: dict[str, pd.DataFrame] = {}

        for tr in stream:
            date_string = tr.stats.starttime.strftime('%Y-%m-%d')
            print("⌚ Processing {} for {}".format(date_string, tr.id))
            df = pd.DataFrame()
            tr = tr.detrend(type='demean')

            if filters is not None:
                tr = tr.filter('bandpass', freqmin=filters[0],
                               freqmax=filters[1], corners=corners)

            series = trace_to_series(tr).resample(resample)
            df['min'] = series.min()
            df['mean'] = series.mean()
            df['max'] = series.max()
            df['median'] = series.median()
            df['rms'] = series.std()

            if bands:
                for band in bands:
                    df[band] = calculate_per_band(
                        bands[band], tr, corners=corners).resample(resample).mean()

                if 'LP' in bands and 'VT' in bands:
                    df['f_ratio'] = np.log2(df['VT'] / df['LP'])

            self.dataframes[tr.id] = df

    def save(self, csv_location: str = None) -> str:
        for station, df in self.dataframes.items():
            date = str(df.first_valid_index()).split(' ')[0]

            csv_dir: str = os.path.join(csv_location, station, self.resample)
            os.makedirs(csv_dir, exist_ok=True)

            csv_location = os.path.join(csv_dir, '{}_{}.csv'.format(station, date))

            # Saving to CSV
            print("💾 Saving to {}".format(csv_location))
            df.to_csv(csv_location)

            # Return CSV location
            return csv_location

    @staticmethod
    def concatenate_csv(rsam_directory: str, station: str, resample_rule: str) -> str:
        df_list: list = []

        csv_files: list[str] = glob.glob(os.path.join(
            rsam_directory, station, resample_rule, "*.csv"))

        for csv in csv_files:
            df = pd.read_csv(csv)
            df_list.append(df)

        big_df = pd.concat(df_list, ignore_index=True)
        big_df = big_df.dropna()
        big_df = big_df.sort_values(by=['datetime'])
        big_df = big_df.reset_index().drop_duplicates(keep='last')

        combined_csv_files: str = os.path.join(
            rsam_directory, station, "combined_{}_{}.csv".format(resample_rule, station))

        columns = ['datetime', 'min', 'mean', 'max',
                   'median', 'rms', 'VLP', 'LP', 'VT', 'f_ratio']

        big_df.to_csv(combined_csv_files, index=False, columns=columns)
        return combined_csv_files

    @staticmethod
    def plot(rsam_directory: str, stations: list[str], resample: str,
             axvspans: list[list[str]] = None, axvlines: list[str] = None,
             interval_day: int = 14, title: str = None) -> plt.Figure:

        fig, axs = plt.subplots(nrows=len(stations), ncols=1, figsize=(12, 3 * len(stations)),
                                layout="constrained", sharex=True)

        for index_key, _station in enumerate(stations):
            df = get_combined_csv(rsam_directory, _station, resample)

            df['VT_24h'] = df['VT'].rolling('24h', center=True).median()

            axs[index_key].scatter(df.index, df.VT, c='k', alpha=0.3, s=10, label='10 minutes')
            axs[index_key].plot(df.index, df.VT_24h, c='red', label='24h', alpha=1)

            axs[index_key].set_ylabel('Amplitude (count)')

            # Plot label only for the last subplot
            if index_key == (len(stations) - 1):
                axs[index_key].set_xlabel('Date')

            axs[index_key].xaxis.set_major_locator(mdates.DayLocator(interval=interval_day))
            axs[index_key].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            axs[index_key].set_ylim(0, 0.002)
            axs[index_key].set_xlim(df.first_valid_index(), df.last_valid_index())

            axs[index_key].annotate(
                text='RSAM '+_station if title is None else title,
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

    @staticmethod
    def get_dataframe_from_rsam_csv(rsam_directory: str, station: str, resample_rule: str) -> pd.DataFrame:
        rsam_csv_combined = os.path.join(rsam_directory, station, 'combined_{}_{}.csv'.format(resample_rule, station))
        return pd.read_csv(rsam_csv_combined, index_col='datetime', parse_dates=True)
