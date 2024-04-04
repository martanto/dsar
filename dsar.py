#!/usr/bin/env python
# coding: utf-8

# In[35]:


import pandas as pd
import os
import matplotlib.pyplot as plt
from statsmodels.tsa.filters.hp_filter import hpfilter


# In[48]:


network = "VG"
station = "PSAG"
location = "00"
channel = "EHZ"

nslc = "{}.{}.{}.{}".format(network, station, location, channel)


# In[47]:


current_dir: str = os.getcwd()
output_directory: str = os.path.join(current_dir, "output", "dsar")
os.makedirs(output_directory, exist_ok=True)

combined_HF_csv: str = r'D:\Projects\dsar\output\HF\combined_0.1-8.0-16.0Hz_VG.PSAG.00.EHZ.csv'
combined_LF_csv: str = r'D:\Projects\dsar\output\LF\combined_0.1-4.5-8.0Hz_VG.PSAG.00.EHZ.csv'


# In[37]:


HF = pd.read_csv(combined_HF_csv, names=["datetime", "values"], 
                 index_col='datetime', parse_dates=True)
LF = pd.read_csv(combined_LF_csv, names=["datetime", "values"], 
                 index_col='datetime', parse_dates=True)


# In[38]:


HF


# In[39]:


LF


# In[40]:


df = pd.DataFrame()


# In[41]:


df['LF'] = LF['values']
df['HF'] = HF['values']
df['DSAR'] = (LF['values']/HF['values'])


# In[42]:


df


# In[43]:


df = df.dropna()


# In[44]:


df = df.apply(lambda col: col.drop_duplicates())


# In[45]:


df = df.interpolate('time').interpolate()


# In[46]:


df


# In[49]:


filename = os.path.join(output_directory, "DSAR_{}.csv".format(nslc))
df.to_csv(filename)


# In[50]:


plt.subplot(111)


# In[61]:


plt.scatter(df.index, df.DSAR, c= 'k', alpha=0.3, s=10, label='{} (10 minutes)'.format(nslc))

# HP filter documentation https://www.statsmodels.org/stable/generated/statsmodels.tsa.filters.hp_filter.hpfilter.html
_,trend = hpfilter(df.DSAR, 1600)
plt.plot(df.index, trend, c='lightseagreen', label='{} smoothed (HP Filter)'.format(nslc), alpha=0.8)

plt.legend(loc=2)
plt.ylabel('DSAR')
plt.ylim(1,5)


# In[ ]:




