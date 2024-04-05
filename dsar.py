#!/usr/bin/env python
# coding: utf-8

# In[137]:


import pandas as pd
import os
import matplotlib.pyplot as plt
from statsmodels.tsa.filters.hp_filter import hpfilter
from datetime import datetime


# In[138]:


network = "VG"
station = "TMKS"
location = "00"
channel = "EHZ"

nslc = "{}.{}.{}.{}".format(network, station, location, channel)


# In[139]:


bands: dict[str, list[float]] = {
    'HF' : [0.1, 8.0, 16.0],
    'LF' : [0.1, 4.5, 8.0],
}


# In[143]:


current_dir: str = os.getcwd()
input_directory: str = os.path.join(current_dir, "output")
output_directory: str = os.path.join(current_dir, "output", "dsar")
os.makedirs(output_directory, exist_ok=True)

combined_HF_csv: str = os.path.join(input_directory, "HF", 'combined_{}Hz_{}.csv'.format('-'.join(map(str,bands['HF'])), nslc))
combined_LF_csv: str = os.path.join(input_directory, "LF", 'combined_{}Hz_{}.csv'.format('-'.join(map(str,bands['LF'])), nslc))


# In[144]:


HF = pd.read_csv(combined_HF_csv, names=["datetime", "values"], 
                 index_col='datetime', parse_dates=True)
LF = pd.read_csv(combined_LF_csv, names=["datetime", "values"], 
                 index_col='datetime', parse_dates=True)


# In[145]:


HF


# In[146]:


LF


# In[147]:


df = pd.DataFrame()


# In[148]:


df['LF'] = LF['values']
df['HF'] = HF['values']
df['DSAR'] = (LF['values']/HF['values'])
df['DSAR_365'] = (LF['values']/HF['values']).rolling(6).median()


# In[149]:


df


# In[150]:


df = df.dropna()


# In[151]:


df.loc[~df.index.duplicated(), :]


# In[152]:


# df = df.apply(lambda col: col.drop_duplicates())


# In[153]:


df = df.interpolate('time').interpolate()


# In[154]:


df


# In[155]:


filename = os.path.join(output_directory, "DSAR_{}.csv".format(nslc))
df.to_csv(filename)


# In[157]:


import matplotlib.dates as mdates

# HP filter documentation https://www.statsmodels.org/stable/generated/statsmodels.tsa.filters.hp_filter.hpfilter.html
cycle,trend = hpfilter(df.DSAR, 1000000)

fig, axs = plt.subplots(figsize=(12, 5), layout="constrained")
scatter = axs.scatter(df.index, df.DSAR, c= 'k', alpha=0.3, s=10, label='{} (10 minutes)'.format(nslc))
smoothed_using_HP_filter = axs.plot(df.index, trend, c='red', label='{} smoothed (HP Filter)'.format(nslc), alpha=1)

axs.legend(loc=2)
axs.set_ylabel('DSAR')
axs.set_xlabel('Date')
axs.xaxis.set_major_locator(mdates.DayLocator(interval=7))
axs.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
axs.set_ylim(0,6.5)

# Agung Eruption
continous_eruptions = [
    ['2017-11-21', '2017-11-29'],
    ['2018-06-27', '2018-07-16'],
    ['2018-07-24', '2018-07-27'],
]

for continous in continous_eruptions:
    axs.axvspan(continous[0], continous[1], alpha=0.4, color='orange')

single_eruptions = [
    '2018-05-29',
    '2018-06-10',
    '2018-06-13',
    '2018-06-15',
    '2018-07-21',
    '2018-07-24',
]

for date in single_eruptions:
    axs.axvline(datetime.strptime(date, '%Y-%m-%d'), alpha=0.4, color='orange')

for label in axs.get_xticklabels(which='major'):
    label.set(rotation=30, horizontalalignment='right')


# In[ ]:




