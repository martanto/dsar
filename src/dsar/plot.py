# Standard library imports
import os
from datetime import datetime
from glob import glob

# Third party imports
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


class PlotDsar:
    """Visualization class for DSAR time-series data.

    Loads daily CSV outputs produced by :class:`DSAR`, combines them into a single
    DataFrame, and renders scatter plots with rolling median overlays.

    Example:
        >>> plot = PlotDsar(
        ...     start_date="2024-01-01",
        ...     end_date="2024-04-22",
        ...     station="RUA3",
        ...     channel="EHZ",
        ... )
        >>> plot.plot(interval_day=7, save=True, file_type="jpg")
    """

    def __init__(
        self,
        start_date: str,
        end_date: str,
        station: str,
        channel: str,
        dsar_dir: str = None,
        figures_dir: str = None,
        network: str = "VG",
        location: str = "00",
        resample: str = "10min",
    ):
        """Initialize the DSAR plotter.

        Args:
            start_date (str): Start date of the plot range in ``YYYY-MM-DD`` format.
            end_date (str): End date of the plot range in ``YYYY-MM-DD`` format.
            station (str): Station code (e.g., ``"RUA3"``).
            channel (str): Channel code (e.g., ``"EHZ"``).
            dsar_dir (str, optional): Directory containing calculated DSAR CSV files.
                Defaults to ``<cwd>/output/dsar``.
            figures_dir (str, optional): Directory for saving figures.
                Defaults to ``<cwd>/output/figures/dsar``.
            network (str, optional): Network code. Defaults to ``"VG"``.
            location (str, optional): Location code. Defaults to ``"00"``.
            resample (str, optional): Pandas offset alias matching the DSAR calculation
                interval. Defaults to ``"10min"``.

        Raises:
            AssertionError: If ``start_date`` is after ``end_date``.
        """
        self.start_date = start_date
        self.end_date = end_date
        self.station = station
        self.channel = channel
        self.network = network
        self.location = location
        self.resample = resample

        self.nslc = f"{network}.{station}.{location}.{channel}"

        self.start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")

        assert (
            self.start_date_obj <= self.end_date_obj
        ), f"\u274c start_date must be before end_date"

        self.dsar_dir = dsar_dir
        if dsar_dir is None:
            self.dsar_dir: str = os.path.join(os.getcwd(), "output", "dsar")

        if figures_dir is None:
            figures_dir: str = os.path.join(os.getcwd(), "output", "figures", "dsar")
        self.figures_dir = figures_dir

        self.y_min = None
        self.y_max = None

    @property
    def df(self) -> pd.DataFrame:
        """Load, combine, and return all daily DSAR CSV files as a single DataFrame.

        Reads all ``*.csv`` files from the DSAR output directory for the configured
        NSLC and resample interval, concatenates them, removes duplicates, sorts by
        datetime, and saves a combined CSV file to disk.

        Returns:
            pd.DataFrame: Combined and sorted DataFrame with a ``datetime`` index
                containing DSAR values and rolling median columns.

        Raises:
            AssertionError: If no CSV files are found in the expected directory.

        Example:
            >>> df = plot.df
        """
        df_list: list = []

        csv_path = os.path.join(self.dsar_dir, self.nslc, self.resample)

        csv_files: list[str] = glob(os.path.join(csv_path, "*.csv"))

        assert len(csv_files) > 0, f"\u274c No CSV files found in {csv_path}."

        for csv in csv_files:
            df = pd.read_csv(csv)
            if not df.empty:
                df_list.append(df)

        big_df = pd.concat(df_list, ignore_index=True)
        big_df = big_df.dropna()
        big_df = big_df.sort_values(by=["datetime"])
        big_df = big_df.drop_duplicates(keep="last")
        big_df = big_df.set_index("datetime")
        big_df.index = pd.to_datetime(big_df.index)

        combined_csv_file: str = os.path.join(
            self.dsar_dir,
            self.nslc,
            "combined_{}_{}.csv".format(self.resample, self.nslc),
        )

        big_df.to_csv(combined_csv_file, index=True)
        print(f"\u2705 Combined CSV saved to: {combined_csv_file}")
        return big_df

    def save(self, figure: plt.Figure, file_type: str = "png") -> bool:
        """Save a matplotlib figure to disk.

        Args:
            figure (plt.Figure): Matplotlib Figure object to save.
            file_type (str, optional): Output file extension (e.g., ``"png"``,
                ``"jpg"``). Defaults to ``"png"``.

        Returns:
            bool: ``True`` if the figure was saved successfully, ``False`` otherwise.

        Example:
            >>> plot.save(fig, file_type="jpg")
        """
        save_path: str = os.path.join(self.figures_dir, self.nslc)
        os.makedirs(save_path, exist_ok=True)

        filename: str = (
            f"{self.nslc}_{self.resample}_{self.start_date}-{self.end_date}.{file_type}"
        )
        save_file = os.path.join(save_path, filename)
        try:
            figure.savefig(save_file, dpi=300)
            print(f"\U0001F4F7 Figure saved to: {save_file}")
            return True
        except Exception as e:
            print(e)
            return False

    def plot(
        self,
        interval_day: int = 3,
        title: str = None,
        y_min: float = None,
        y_max: float = None,
        save: bool = True,
        file_type: str = "png",
    ) -> plt.Figure:
        """Generate a DSAR time-series plot.

        Creates a scatter plot of DSAR values with a 24-hour rolling median overlay
        and optional fixed y-axis limits.

        Args:
            interval_day (int, optional): X-axis major tick interval in days.
                Defaults to 3.
            title (str, optional): Plot title. Defaults to ``"DSAR - {NSLC}"``.
            y_min (float, optional): Minimum y-axis value. Defaults to None
                (auto-scaled).
            y_max (float, optional): Maximum y-axis value. Defaults to None
                (auto-scaled).
            save (bool, optional): Whether to save the figure to disk.
                Defaults to True.
            file_type (str, optional): File format for saving (e.g., ``"png"``,
                ``"jpg"``). Defaults to ``"png"``.

        Returns:
            plt.Figure: The generated matplotlib Figure.

        Raises:
            AssertionError: If the combined DataFrame is empty.

        Example:
            >>> fig = plot.plot(
            ...     interval_day=7, y_min=85, y_max=225, save=True, file_type="jpg"
            ... )
        """
        df = self.df

        assert not df.empty, f"\u274c DataFrame is empty"

        fig, axs = plt.subplots(nrows=1, ncols=1, figsize=(12, 3), layout="constrained")

        axs.scatter(
            df.index,
            df["DSAR_{}".format(self.resample)],
            c="k",
            alpha=0.3,
            s=10,
            label="10min",
        )

        axs.plot(
            df.index, df["DSAR_24h_median"], c="orange", label="24h_median", alpha=1
        )
        axs.set_ylabel("DSAR")

        axs.xaxis.set_major_locator(mdates.DayLocator(interval=interval_day))

        axs.set_xlim(df.first_valid_index(), df.last_valid_index())

        if (y_min is not None) and (y_max is not None):
            axs.set_ylim(y_min, y_max)

        axs.annotate(
            text="DSAR - " + self.nslc if title is None else title,
            xy=(0.01, 0.92),
            xycoords="axes fraction",
            fontsize="8",
            bbox=dict(facecolor="white", alpha=0.5),
        )

        axs.legend(loc="upper right", fontsize="8", ncol=4)

        for label in axs.get_xticklabels(which="major"):
            label.set(rotation=30, horizontalalignment="right")

        if save:
            self.save(fig, file_type)

        return fig
