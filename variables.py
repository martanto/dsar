import pandas as pd
import os
from obspy.core import UTCDateTime
from obspy import Stream
from obspy.clients.filesystem.sds import Client

# ============================================
# DEFINING VARIABLES
# List of station
stations: list[str] = [
    # 'VG.PSAG.00.EHZ',
    # 'VG.TMKS.00.EHZ',
    'VG.RUA3.00.EHZ',
]

# Named band frequencies
# Very Long Period, Long Period, and Volcano Tectonic
bands: dict[str, list[float]] = {
    'VLP': [0.02, 0.2],
    'LP': [0.5, 4.0],
    'VT': [4.0, 18.0]
}

# SDS Client
sds_directory: str = r'D:\\Data\\SDS'
client = Client(sds_directory)

# Resample parameter to use in DSAR and RSAM
resample_rule: str = '10min'

# Defining start and end datae
start_date: str = "2023-01-01"
end_date: str = "2024-04-14"


# List of date from start to end with 1-day period
def get_dates(start: str, end: str) -> pd.DatetimeIndex:
    return pd.date_range(start, end, freq="D")


# Leave it as it be
dates: list[UTCDateTime] = [UTCDateTime(date) for date in get_dates(start_date, end_date)]

# Get current directory
current_dir: str = os.getcwd()

# Get output directory and make sure it exists
output_directory: str = os.path.join(current_dir, "output")
os.makedirs(output_directory, exist_ok=True)

# Get DSAR output directory and make sure it exists
dsar_directory: str = os.path.join(output_directory, "dsar")
os.makedirs(dsar_directory, exist_ok=True)

# Get RSAM output directory and make sure it exists
rsam_directory: str = os.path.join(output_directory, "rsam")
os.makedirs(rsam_directory, exist_ok=True)

# Get RSAM figures output directory and make sure it exists
figures_directory: str = os.path.join(output_directory, "figures")
os.makedirs(figures_directory, exist_ok=True)

# Get MAGMA output directory
plot_from_magma: bool = True
magma_directory: str = os.path.join(output_directory, "magma")
os.makedirs(magma_directory, exist_ok=True)

# MAGMA CSV Event and dataframe
magma_csv: str = 'magma_RUA_2024-01-01_2024-04-14.csv'
magma_df = pd.read_csv(os.path.join(magma_directory, magma_csv),
                       index_col='date', parse_dates=True) if plot_from_magma else pd.DataFrame

# DSAR and RSAM dataframes
DSAR_dfs: dict[str, pd.DataFrame] = {}
RSAM_dfs: dict[str, pd.DataFrame] = {}

for station in stations:
    DSAR_csv_combined: str = os.path.join(dsar_directory, 'DSAR_{}.csv'.format(station))
    RSAM_csv_combined: str = os.path.join(rsam_directory, station,
                                          'combined_{}_{}.csv'.format(resample_rule, station))

    DSAR_dfs[station]: pd.DataFrame = pd.DataFrame()
    RSAM_dfs[station]: pd.DataFrame = pd.DataFrame()

    if os.path.exists(DSAR_csv_combined):
        DSAR_dfs[station]: pd.DataFrame = pd.read_csv(DSAR_csv_combined,
                              index_col='datetime', parse_dates=True)

    if os.path.exists(RSAM_csv_combined):
        RSAM_dfs[station]: pd.DataFrame = pd.read_csv(RSAM_csv_combined, index_col='datetime', parse_dates=True)

# Dict of stream with date as a key and Stream object as values. Example: streams['2017-10-01'][Stream, Stream, ...]
streams: dict[str, Stream] = {}
series: dict[str, dict[str, pd.Series]] = {}

# Dict of CSV files with station name as a key. Example: csv_files['VG.PSAG.00.EHZ'][....]
csv_files: dict[str, list[str]] = {}

# ============================================
# These variables used to Plot the RSAM result
# start date, end date of eruption
continuous_eruptions: list[list[str]] = [
    # ['2017-11-21', '2017-11-29'],
    # ['2018-06-27', '2018-07-16'],
    # ['2018-07-24', '2018-07-27'],
    ['2024-04-14', '2024-04-15'],
]
single_eruptions: list[str] = [
    '2017-11-25',
    '2017-11-26',
    '2017-11-27',
    '2017-11-29',
    '2017-12-08',
    '2017-12-09',
    '2017-12-10',
    '2017-12-11',
    '2017-12-12',
    '2017-12-23',
    '2017-12-24',
    '2017-12-26',
    '2017-12-28',
    '2018-01-01',
    '2018-01-03',
    '2018-01-11',
    '2018-01-15',
    '2018-01-17',
    '2018-01-18',
    '2018-01-19',
    '2018-01-20',
    '2018-01-22',
    '2018-01-23',
    '2018-01-24',
    '2018-02-13',
    '2018-03-11',
    '2018-03-26',
    '2018-04-06',
    '2018-04-15',
    '2018-04-30',
    '2018-05-19',
    '2018-05-29',
    '2018-06-10',
    '2018-06-13',
    '2018-06-15',
    '2018-06-27',
    '2018-07-02',
    '2018-07-03',
    '2018-07-04',
    '2018-07-05',
    '2018-07-06',
    '2018-07-08',
    '2018-07-09',
    '2018-07-11',
    '2018-07-13',
    '2018-07-15',
    '2018-07-16',
    '2018-07-21',
    '2018-07-24',
    '2018-07-25',
    '2018-07-27']
