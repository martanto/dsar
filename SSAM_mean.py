import numpy as np
from matplotlib.pyplot import *
#~ from cluster import *
import scipy
import time
import calendar
from datetime import datetime, date, timedelta
import glob, os
from obspy import read
#~ from obspy.signal import cornFreq2Paz, cosTaper, freqattributes,konnoOhmachiSmoothing

from mpl_toolkits.axes_grid1 import host_subplot
import mpl_toolkits.axisartist as AA

from matplotlib.dates import num2date
import matplotlib.pyplot as plt
#~ from obspy.signal.freqattributes import mper
 
### PANDAS	
import pandas as pd
import datetime 

DATE = []
fig = plt.figure(figsize=(20,16))

paths = sorted(glob.glob(r'C:\Users\caudroco\Documents\Papers_2020\WI\DSAR\WSRZ_8_16Hz_displ\*'))
#~ paths=paths[0:10]
DATE = []
AZ = []
#~ RS = []
#~ RS2 = []
#~ count = 0
for i,path in enumerate(paths):
	print(path)
	try:
		date= np.loadtxt(path,usecols = (0,),dtype = np.str, delimiter = ',',skiprows = 1)
		az= np.loadtxt(path,usecols = (1,),dtype = np.float, delimiter = ',',skiprows = 1)
		#~ rs= np.loadtxt(path,usecols = (1,),dtype = np.float, delimiter = ',',skiprows = 1)
		#~ rs2= np.loadtxt(path,usecols = (5,),dtype = np.float, delimiter = ',',skiprows = 1)
		#~ print az,rs,rs2
		tmp = datetime.datetime.strptime(date[1], "%Y-%m-%d %H:%M:%S")
		DATE.append(tmp)
		AZ.append(np.median(az))
		#~ RS.append(np.median(rs))
		#~ RS2.append(np.median(rs2))
	except:
		pass
#~ print AZ
plt.subplot(111)
plt.plot(DATE,AZ)
#~ plt.subplot(312)
#~ plt.plot(DATE,RS)
#~ plt.subplot(313)
#~ plt.plot(DATE,RS2)
plt.show()

test = pd.DataFrame({'SSAM_HF':AZ}, index=DATE)
test.to_csv('WSRZ_8_16Hz_displ.csv')

