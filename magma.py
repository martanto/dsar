#!/usr/bin/env python
# coding: utf-8

# In[69]:


import requests
import json
import pandas as pd
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


# In[70]:


url = 'https://magma.esdm.go.id/api/v1/python/magma-var/evaluasi'
token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwczpcL1wvbWFnbWEuZXNkbS5nby5pZFwvY2hhbWJlcnNcL3Rva2VuXC9nZW5lcmF0ZSIsImlhdCI6MTcxMzM2NTczNiwiZXhwIjoxNzEzNDUyMTM2LCJuYmYiOjE3MTMzNjU3MzYsImp0aSI6IkFsVFk0dEk2UlA3amFURnoiLCJzdWIiOjI1OCwicHJ2IjoiODdlMGFmMWVmOWZkMTU4MTJmZGVjOTcxNTNhMTRlMGIwNDc1NDZhYSIsInNvdXJjZSI6Ik1BR01BIEluZG9uZXNpYSIsImFwaV92ZXJzaW9uIjoidjEifQ.03FqVhJBL0BXLA4EbEo5RDl3F_I308OuuYCWp6VIUPM'


# In[71]:


start_date: str = '2017-10-01'
end_date: str = '2018-07-31'
volcano_code: str = 'AGU'
events = ['vta', 'vtb', 'lts']


# In[72]:


payload = json.dumps({
  'start_date': start_date,
  'end_date': end_date,
  'code_ga': volcano_code,
  'gempa': events
})


# In[73]:


headers = {
  'Authorization': 'Bearer '+token,
  'Content-Type': 'application/json'
}


# In[74]:


current_dir: str = os.getcwd()
output_directory: str = os.path.join(current_dir, "output", "magma")
os.makedirs(output_directory, exist_ok=True)


# In[75]:


response = requests.request("GET", url, headers=headers, data=payload)


# In[76]:


response_json = response.json()


# In[77]:


df = pd.json_normalize(response.json()['data'])


# In[78]:


df.drop(columns=[
  'availability',
  'visual.visibility',
  'visual.cuaca',
  'visual.asap.teramati',
  'visual.asap.warna',
  'visual.asap.intensitas',
  'visual.asap.tekanan',
  'visual.asap.tinggi_min',
  'visual.asap.tinggi_max',
  'visual.letusan.teramati',
  'visual.letusan.tinggi_min',
  'visual.letusan.tinggi_max',
  'visual.letusan.warna',
  'visual.awan_panas_guguran.teramati',
  'visual.awan_panas_guguran.jarak_min',
  'visual.awan_panas_guguran.jarak_max'
], inplace=True)

df.head()


# In[79]:


df.columns[df.sum()==0]


# In[80]:


df.drop(columns=df.columns[df.sum()==0], inplace=True)

df.head()


# In[81]:


df.set_index(keys='date', inplace=True)


# In[82]:


filename = os.path.join(output_directory, "magma_{}_{}-{}.csv".format(volcano_code, start_date, end_date))
df.to_csv(filename)


# In[93]:


colors = ['#5ba04f','#4e79a6','#f28e2b']

fig, axs = plt.subplots(nrows=3, ncols=1, figsize=(12, 6),
                        layout="constrained", sharex=True)

for gempa, column_name in enumerate(df.columns):
    axs[gempa].bar(df.index, df[column_name], width=0.5,label=column_name, color=colors[gempa])
    
    axs[gempa].legend(loc=1)
    axs[gempa].set_ylabel('Jumlah')
    
    axs[gempa].xaxis.set_major_locator(mdates.DayLocator(interval=14))
    
    # Rotate x label
    for label in axs[gempa].get_xticklabels(which='major'):
        label.set(rotation=30, horizontalalignment='right')


# In[86]:


single_eruptions = df[df['gempa.letusan_erupsi'] > 0]['gempa.letusan_erupsi']


# In[90]:


single_eruptions.index.tolist()


# In[ ]:




