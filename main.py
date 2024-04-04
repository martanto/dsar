#!/usr/bin/env python
# coding: utf-8

# In[14]:


import pandas as pd
import os
import numpy as np
import glob
from obspy import Stream
from obspy.core import UTCDateTime
from obspy.clients.filesystem.sds import Client
from datetime import timedelta


# Initiate station variables

# In[34]:


network = "VG"
station = "PSAG"
location = "00"
channel = "EHZ"

nslc = "{}.{}.{}.{}".format(network, station, location, channel)


# Initiate directories variables.   
# The `sds_directory` based on Seiscomp Data Structure (https://www.seiscomp.de/seiscomp3/doc/applications/slarchive/SDS.html)  
# The example of the SDS Directory can be found inside `input` directory

# In[3]:


current_dir: str = os.getcwd()
sds_directory: str = r"D:\Projects\dsar\input"
client = Client(sds_directory)

output_directory: str = os.path.join(current_dir, "output")
os.makedirs(output_directory, exist_ok=True)


# Add start_date and end_date parameters

# In[4]:


start_date: str = "2017-12-01"
end_date: str = "2017-12-03"


# In[5]:


bands: dict[str, list[float]] = {
    'HF' : [0.1, 8.0, 16.0],
    'LF' : [0.1, 4.5, 8.0],
}

resample_rule: str = '10min'


# A method to generate list of date between two date periods. Returning `pd.DatetimeIndex`

# In[6]:


def get_dates(start: str, end: str) -> pd.DatetimeIndex:
    return pd.date_range(start, end, freq="D")


# Stream processing to get `dsar` values

# In[7]:


def stream_processing(
        daily_mseed: Stream,
        first_highpass: float = 0.1,
        second_highpass: float = 8.0,
        low_pass: float = 16.0
    ) -> Stream:
    stream = daily_mseed
    stream.merge(fill_value=0)
    stream.detrend('demean')
    stream.filter('highpass', freq=first_highpass)
    stream.integrate()
    stream.filter('highpass', freq=second_highpass)
    stream.filter('lowpass', freq=low_pass)
    return stream


# Convert calculated `dsar` value into `pd.Series`

# In[8]:


def convert_stream_to_series(stream: Stream) -> pd.Series:
    index_time = pd.date_range(
        start = stream[0].stats.starttime.datetime,
        periods = stream[0].stats.npts,
        freq = "{}ms".format(stream[0].stats.delta*1000)
    )
    
    _series = pd.Series(
        data=np.abs(stream[0].data),
        index=index_time,
        name=stream[0].id,
        dtype=stream[0].data.dtype)
    
    return _series.resample(resample_rule).median()


# Filling `streams` list variable

# In[9]:


def fill_streams(date: UTCDateTime, band_values=None)-> Stream:
    if band_values is None:
        band_values = [0.1, 8.0, 16, 0]
        
    stream = client.get_waveforms(
        network = network,
        station = station,
        location = location,
        channel = channel,
        starttime = date,
        endtime= date + timedelta(days=1)
    )
    
    # Check if stream is not empty (files not found)
    # Return empty Stream if files are not found
    if stream.count():
        date_string = date.strftime('%Y-%m-%d')
        print("⌚ Processing {} for {}".format(date_string, stream[0].id))

        # You can change the freq filter here
        stream = stream_processing(
            stream,
            first_highpass = band_values[0],
            second_highpass = band_values[1],
            low_pass = band_values[2]
        )
        
        return stream
    else:
        print("⚠️ {} :: File(s) not found!".format(date.strftime('%Y-%m-%d')))
        return Stream()


# Filling `series` variable and save it to csv 

# In[10]:


def fill_series_and_save_to_csv(stream: Stream, band, band_values=None)-> pd.Series:
    if band_values is None:
        band_values = [0.1, 8.0, 16, 0]
    date_string: str = stream[0].stats.starttime.datetime.strftime('%Y-%m-%d')
    
    filename: str = "{}Hz_{}_{}".format(
        '-'.join(map(str,band_values)),
        date_string,
        stream[0].id
    )
    
    csv_output = os.path.join(output_directory, band,"{}.csv".format(filename))
    
    print("↔️ Convert stream {} to series".format(filename))
    values = convert_stream_to_series(stream)
    
    print("💾 Saving to {}".format(csv_output))
    values.to_csv(os.path.join(output_directory,csv_output), header=False)
    
    return values


# Combining CSV files per band and station

# In[49]:


def concatenate_csv(band: str, station=None)-> str:
    if station is None:
        station = nslc
        
    df_list: list = []
    
    wildcard: str = '-'.join(map(str,bands[band]))
    csv_files: list[str] = glob.glob(os.path.join(
        output_directory, band, "{}Hz_*_{}.csv".format(wildcard, station)))

    for csv in csv_files:
        df = pd.read_csv(csv, header=None)
        df_list.append(df)
        
    big_df = pd.concat(df_list, ignore_index=True)
    
    combined_csv_files: str = os.path.join(
        output_directory, band,"combined_{}Hz_{}.csv".format(wildcard, station))
    
    big_df.to_csv(
        combined_csv_files,
        index=False, header=False)
    return combined_csv_files


# In[12]:


dates: list[UTCDateTime] = [UTCDateTime(date) for date in get_dates(start_date, end_date)]
streams: dict[str, Stream] = {}
series: dict[str, dict[str, pd.Series]] = {}


# In[51]:


# We can optimize this using parallel computation
for band in bands.keys():
    # Create output directory per band
    os.makedirs(os.path.join(output_directory, band), exist_ok=True)
    
    # Get band values
    band_values: list[float] = bands[band]
    
    # Initiate series per band with empty dict
    series[band]: dict[str, pd.Series] = {}
    print("=====================================")
    print("🏃‍♀️ Using {} band with values {}".format(band, band_values))
    print("======================================")
    
    # Looping through date
    for date in dates:
        date_string = date.strftime('%Y-%m-%d')
        
        # Add stream value to streams variable
        streams[date_string]: Stream = fill_streams(date, band_values)
        
        # Check if stream per date is empty or not
        # Skip converting if data is not found
        if streams[date_string].count():
            # Converting stream value to series and save it as CSV
            series[band][date_string]: pd.Series = fill_series_and_save_to_csv(streams[date_string], band, band_values)
    
    # Combining CSV files
    combined_csv_file = concatenate_csv(band)
    print("⌚ Combined CSV files saved into: {}".format(combined_csv_file))
    print("")
print("✅Finish!")

