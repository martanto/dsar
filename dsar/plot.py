import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
from datetime import datetime
from glob import glob


class PlotDsar:
    def __init__(self,
                 start_date: str,
                 end_date: str,
                 station: str,
                 channel: str,
                 dsar_dir: str = None,
                 figures_dir: str = None,
                 network: str = 'VG',
                 location: str = '00',
                 resample: str = '10min', ):
        """Plot DSAR

        Args:
            start_date (str): start date of plot
            end_date (str): end date of plot
            station (str): station name
            channel (str): channel name
            dsar_dir (str): Output for calculated DSAR
            figures_dir (str): Output for plotting figures
            network (str): Network name. Default VG
            location (str): Location name. Default 00
            resample (str): Resampling interval. Default 10min

        Returns:
            None
        """
        self.start_date = start_date
        self.end_date = end_date
        self.station = station
        self.channel = channel
        self.network = network
        self.location = location
        self.resample = resample

        self.nslc = f"{network}.{station}.{location}.{channel}"

        self.start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        self.end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')

        assert self.start_date_obj <= self.end_date_obj, f"❌ start_date must before end_date"

        self.dsar_dir = dsar_dir
        if dsar_dir is None:
            self.dsar_dir: str = os.path.join(os.getcwd(), 'output', 'dsar')

        if figures_dir is None:
            figures_dir: str = os.path.join(os.getcwd(), 'output', 'figures', 'dsar')
        os.makedirs(figures_dir, exist_ok=True)
        self.figures_dir = figures_dir

        self.y_min = None
        self.y_max = None

    @property
    def df(self) -> pd.DataFrame:
        """Get dataframe from csv file

        Returns:
            pd.DataFrame
        """
        df_list: list = []

        csv_files: list[str] = glob(os.path.join(
            self.dsar_dir, self.nslc, self.resample, "*.csv"))

        for csv in csv_files:
            df = pd.read_csv(csv)
            if not df.empty:
                df_list.append(df)

        big_df = pd.concat(df_list, ignore_index=True)
        big_df = big_df.dropna()
        big_df = big_df.sort_values(by=['datetime'])
        big_df = big_df.drop_duplicates(keep='last')
        big_df = big_df.set_index('datetime')
        big_df.index = pd.to_datetime(big_df.index)

        combined_csv_files: str = os.path.join(
            self.dsar_dir, self.nslc, "combined_{}_{}.csv".format(self.resample, self.nslc))

        big_df.to_csv(combined_csv_files, index=True)
        print(f'✅ Saved to {combined_csv_files}')
        return big_df

    def plot(self,
             interval_day: int = 3,
             title: str = None,
             y_min: float = None,
             y_max: float = None,) -> plt.Figure:
        """Plot DSAR

        Args:
            interval_day: Interval days. Default 3
            title (str): Plot title
            y_min (float): Minimum value. Default None
            y_max (float): Maximum value. Default None

        Returns:
            plt.Figure
        """
        df = self.df

        assert not df.empty, f"❌ self.df is empty"

        fig, axs = plt.subplots(nrows=1, ncols=1, figsize=(12, 3),
                                layout="constrained")

        axs.scatter(df.index, df['DSAR_{}'.format(self.resample)],
                    c='k', alpha=0.3, s=10, label='10min')

        axs.plot(df.index, df['DSAR_24h_median'], c='orange', label='24h_median', alpha=1)
        axs.set_ylabel('DSAR')

        axs.xaxis.set_major_locator(mdates.DayLocator(interval=interval_day))

        axs.set_xlim(df.first_valid_index(), df.last_valid_index())

        if (y_min is not None) and (y_max is not None):
            axs.set_ylim(y_min, y_max)

        axs.annotate(
            text='DSAR - ' + self.nslc if title is None else title,
            xy=(0.01, 0.92),
            xycoords='axes fraction',
            fontsize='8',
            bbox=dict(facecolor='white', alpha=0.5)
        )

        axs.legend(loc='upper right', fontsize='8', ncol=4)

        # Rotate x label
        for label in axs.get_xticklabels(which='major'):
            label.set(rotation=30, horizontalalignment='right')

        return fig
