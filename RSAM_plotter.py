import numpy as np
from matplotlib.pyplot import *
#~ from cluster import *
import scipy
import time
import calendar
from datetime import datetime, date, timedelta
import glob, os


from matplotlib.dates import num2date
from statsmodels.tsa.filters.hp_filter import hpfilter
import matplotlib.pyplot as plt

import pandas as pd
import datetime
import seaborn as sns


sns.set_palette("bright")
sns.set_context("notebook", font_scale=1.0, rc={"lines.linewidth": 2.5})

from matplotlib.dates import date2num


def intr(start, end):
    x1 = date2num(start)
    x2 = date2num(end)
    plt.axvspan(x1, x2, color='k', zorder=0, alpha=0.4)


from matplotlib.dates import date2num


def waspada(start, end):
    x1 = date2num(start)
    x2 = date2num(end)
    plt.axvspan(x1, x2, color='r', zorder=0, alpha=0.2)


def level(start, end):
    x1 = date2num(start)
    x2 = date2num(end)
    plt.axvspan(x1, x2, color='b', zorder=0, alpha=0.2)



LF=pd.read_csv('WIZ_SSAM_0_5_1Hz.csv',header=0,index_col='Date',parse_dates=True)
HF=pd.read_csv('WIZ_SSAM_2_5Hz.csv',header=0,index_col='Date',parse_dates=True)
RSAM=pd.read_csv('WIZ_RSAM.csv',header=0,index_col='Date',parse_dates=True)


LF = LF.dropna()
LF = LF.apply(lambda col: col.drop_duplicates())
LF = LF.resample('1D').mean()
LF = LF.interpolate()



plt.subplot(311)
# plt.plot(LF.index,LF.DSAR_smoothed_730, c= 'g',label='DSAR (1 year)')
# plt.plot(LF.index,LF.DSAR_smoothed_180, c= 'r',label='DSAR (180 days)')
plt.scatter(LF.index,LF, c= 'k',alpha=0.3,s=10,label='1 day')
cycle,trend = hpfilter(LF, 1000)
plt.plot(LF.index,trend,c='darkcyan',label='Smoothed',alpha=0.8)

# cycle,trend = hpfilter(LF, 10000000)
# plt.plot(LF.index,trend,c='orange',label='WIZ smoothed',alpha=0.8)




plt.legend(loc=2)

intr(datetime.datetime(2011,8,19),datetime.datetime(2011,8,21))
waspada(datetime.datetime(2012,8,5),datetime.datetime(2013,10,11))
# level(datetime.datetime(2007,3,1),datetime.datetime(2007,9,1))

# plt.axvline(datetime.datetime(2003,3,1), lw=2.0,ls ='--', c='b')

plt.axvline(datetime.datetime(2012,8,4), lw=2.0,c='r')
#~ plt.axvline(datetime.datetime(2013,8,19), lw=2.0,c='b')
plt.axvline(datetime.datetime(2013,10,4), lw=2.0,c='r')
plt.axvline(datetime.datetime(2013,10,8), lw=2.0,c='r')
plt.axvline(datetime.datetime(2013,10,11), lw=2.0,c='r')
plt.axvline(datetime.datetime(2016,4,27), lw=2.0,c='r')
plt.xlim(datetime.datetime(2003,1,1),datetime.datetime(2020,5,1))
plt.ylabel('LF (0.5-1.0 Hz)')



RSAM = RSAM.dropna()
RSAM = RSAM.apply(lambda col: col.drop_duplicates())
RSAM = RSAM.resample('1D').mean()
RSAM = RSAM.interpolate()



plt.subplot(312)
# plt.plot(LF.index,LF.DSAR_smoothed_730, c= 'g',label='DSAR (1 year)')
# plt.plot(LF.index,LF.DSAR_smoothed_180, c= 'r',label='DSAR (180 days)')
plt.scatter(RSAM.index,RSAM, c= 'k',alpha=0.3,s=10,label='WIZ (1 day)')
cycle,trend = hpfilter(RSAM, 1000)
plt.plot(RSAM.index,trend,c='darkcyan',label='Smoothed',alpha=0.8)

# cycle,trend = hpfilter(RSAM, 10000000)
# plt.plot(RSAM.index,trend,c='orange',label='LF',alpha=0.8)




plt.legend(loc=2)

intr(datetime.datetime(2011,8,19),datetime.datetime(2011,8,21))
waspada(datetime.datetime(2012,8,5),datetime.datetime(2013,10,11))
# level(datetime.datetime(2007,3,1),datetime.datetime(2007,9,1))

# plt.axvline(datetime.datetime(2003,3,1), lw=2.0,ls ='--', c='b')

plt.axvline(datetime.datetime(2012,8,4), lw=2.0,c='r')
#~ plt.axvline(datetime.datetime(2013,8,19), lw=2.0,c='b')
plt.axvline(datetime.datetime(2013,10,4), lw=2.0,c='r')
plt.axvline(datetime.datetime(2013,10,8), lw=2.0,c='r')
plt.axvline(datetime.datetime(2013,10,11), lw=2.0,c='r')
plt.axvline(datetime.datetime(2016,4,27), lw=2.0,c='r')
plt.xlim(datetime.datetime(2003,1,1),datetime.datetime(2020,5,1))
plt.ylabel('RSAM')




LF=pd.read_csv('WIZ_SSAM_0_5_1Hz.csv',header=0,index_col='Date',parse_dates=True)
HF=pd.read_csv('WIZ_SSAM_2_5Hz.csv',header=0,index_col='Date',parse_dates=True)
RSAM=pd.read_csv('WIZ_RSAM.csv',header=0,index_col='Date',parse_dates=True)


HF = HF.dropna()
HF = HF.apply(lambda col: col.drop_duplicates())
HF = HF.resample('1D').mean()
HF = HF.interpolate()



plt.subplot(313)
# plt.plot(LF.index,LF.DSAR_smoothed_730, c= 'g',label='DSAR (1 year)')
# plt.plot(LF.index,LF.DSAR_smoothed_180, c= 'r',label='DSAR (180 days)')
plt.scatter(HF.index,HF, c= 'k',alpha=0.3,s=10,label='1 day')
cycle,trend = hpfilter(HF, 1000)
plt.plot(HF.index,trend,c='darkcyan',label='2-5 Hz',alpha=0.8)

# cycle,trend = hpfilter(HF, 10000000)
# plt.plot(HF.index,trend,c='orange',label='HF smoothed',alpha=0.8)

plt.legend(loc=2)

intr(datetime.datetime(2011,8,19),datetime.datetime(2011,8,21))
waspada(datetime.datetime(2012,8,5),datetime.datetime(2013,10,11))
# level(datetime.datetime(2007,3,1),datetime.datetime(2007,9,1))

# plt.axvline(datetime.datetime(2003,3,1), lw=2.0,ls ='--', c='b')

plt.axvline(datetime.datetime(2012,8,4), lw=2.0,c='r')
#~ plt.axvline(datetime.datetime(2013,8,19), lw=2.0,c='b')
plt.axvline(datetime.datetime(2013,10,4), lw=2.0,c='r')
plt.axvline(datetime.datetime(2013,10,8), lw=2.0,c='r')
plt.axvline(datetime.datetime(2013,10,11), lw=2.0,c='r')
plt.axvline(datetime.datetime(2016,4,27), lw=2.0,c='r')
plt.xlim(datetime.datetime(2003,1,1),datetime.datetime(2020,5,1))
# plt.ylabel('Amplitude')

plt.show()