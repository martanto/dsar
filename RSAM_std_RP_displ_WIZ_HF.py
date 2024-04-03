# -*- coding: utf-8 -*-
"""
Created on Fri Dec 20 14:41:46 2013

@author: Thomas Lecocq - Corentin Caudron
"""

import pandas as pd
import numpy as np
from obspy.core import read, Stream 
import glob
import matplotlib.pyplot as plt
import os
import datetime

def MseedFile(stats,year, jday, hour=0,format="SDS"):
    if format == "SDS":
        format = "YEAR/NET/STA/CHAN.TYPE/NET.STA.LOC.CHAN.TYPE.YEAR.JDAY"
    elif format == "IJEN":
    #### changement pr windows /  --> \
        #~ format = "YEAR/NET/STA/CHAN.TYPE/JDAY/NET.STA.LOC.CHAN.TYPE.YEAR.JDAY.HOUR"
        format = "YEAR.JDAY.HOUR_z.msd"
    elif format == "IDDSext":
        format = "YEAR/NET/STA/CHAN.TYPE/JDAY/NET.STA.LOC.CHAN.TYPE.YEAR.JDAY.HOUR.MSEED"
    elif format == "ew":
        format = "STA/STA.NET.LOC.CHAN.YEAR.JDAY"
#~ C:\Users\corentin\Documents\EOS_seismic\Taurus\2012\XX\VMCB\BHZ.D\268\XX.VMCB..BHZ.D.2012.268.05
#~ C:\Users\corentin\Documents\EOS_seismic\Taurus\2012\XX\VMCB\BHZ.D\268\XX.VMCB..BHZ.D.2012.268.05.SAC
    else:
        print("format not recognized")
        return ""
    file=format.replace('YEAR', "%04i"%year)
    file=file.replace('NET', stats.network)
    file=file.replace('STA', stats.station)
    file=file.replace('LOC', stats.location)
    file=file.replace('CHAN', stats.channel)
    file=file.replace('JDAY', "%03i"%jday)
    file=file.replace('TYPE', "D")
    file=file.replace('HOUR', "%02i"%hour)
    return file

class DFStream(Stream):
    def __init__(self):
        Stream.__init__(self)

    def toSeries(self):
        self.series = {}
        for trace in self.traces:
            t = pd.date_range(trace.stats.starttime.datetime,periods=trace.stats.npts, freq="%ims"%(trace.stats.delta*1000))
            s = pd.Series(data=trace.data, index=t, name=trace.id,dtype=trace.data.dtype)
            self.series[trace.id] = s
            del t, s

    def ssam(self,d):
        return np.median(np.abs(d))

    def ssem(self,d):
        return np.median(np.abs(d))

    def SSxM(self,rule='90S',bands=None,id=None):
        if len(self.series.keys()) > 1 and id==None:
            print("Warning, more than 1 key in Series, using first '%s' by default" % self.series.keys()[0])
            id = self.series.keys()[0]
        elif len(self.series.keys()) == 1:
            id = list(self.series.keys()[0])
        s = self.series[id]
        data = pd.DataFrame(s.resample(rule, how=self.ssam), columns=['RSAM'])
        data['RSEM'] = s.resample(rule, how=self.ssem)

        #~ for band in bands:
            #~ print "band:", band
            #~ tmp = s.copy()
        #~ print tmp
        #~ print self.traces[0].stats.sampling_rate
        #~ print band[1], band[0]
            #~ tmp.data = bandpass(tmp,band[0],band[1],self.traces[0].stats.sampling_rate,corners=4,zerophase=False)
            #~ data["SSAM: %s" % str(band)] = tmp.resample(rule, how=self.ssam)
            #~ data["SSEM: %s" % str(band)] = tmp.resample(rule, how=self.ssem)
            #~ del tmp
        del s
        return data

class Stats(object):
    pass

if __name__ == "__main__":

    # Definition of the Bands for the SSxM
    bands = [[0.1,20.0],[2.0,15.0],[2.0,6.0]]
    #~ bands = [[0.1,25.0]]

    # Compute the SSxM for windows of 5 minutes
    # (see http://pandas.pydata.org/pandas-docs/stable/timeseries.html#offset-aliases)
    rule = '10T'

    # Define an output directory (create it before running!)
    #~ out = "F:\Ijen_RP\New_work_2016\SSAM\RP_0_5_4_5Hz_displ"
    #~ out = "F:\Ijen_RP\New_work_2016\SSAM\TUVZ_8_16Hz_displ"
    #~ out = "F:\Ijen_RP\New_work_2016\SSAM\WIZ_4_5_8Hz_displ_cek"
    #~ out = "G:\Ijen_RP\New_work_2016\SSAM\WSRZ_4_5_8Hz_displ"

    out = r"C:\Users\caudroco\Documents\Papers_2020\WI\DSAR\WSRZ_8_16Hz_displ"


    # Should we re-process already processed files ?
    # force = True
    force = False

    # Should we plot after processing ?
    # dry = True
    dry = False

    # Define the root of the archive containing the data

    # source = r"C:\Users\caudroco\Documents\Papers_2019\WI\Dec2019\WI\*\NZ\WIZ*"
    source = r"F:\NZ_volcanoes\data_NZ_volcanoes\CONV\*\NZ\WSRZ"
    # Define the structure of the archive
    archive_struc = "IDDSext"

    # Define some stats to find the files
    stats = Stats()


    paths = sorted(glob.glob(r'%s\HHZ.D\*'%source))


    start = datetime.datetime(2000,1,1)
    end = datetime.datetime(2020,1,1)

    # Loop over the dates and find files to analyse:
    files = []
    current = start
    i = 0
    while current <= end:
        # Creates f, the filename for station "stats.station" in the archive, probleme if hr ajout?
        # et si pas linux \ /?
        try:
            f = paths[i]
            i+=1
        except:
            pass
        #~ print 'la',f
        path = f

        print('ici',path)
        if os.path.isfile(path):
            #~ print 'yeah'
                files.append(path)
        #### probleme si hr ?
        current += datetime.timedelta(days=1)
            #~ current += datetime.timedelta(hours=1)

        # Process files and output data to CSV in "out" directory:
    first = True
    for file in files:
        filename = os.path.split(file)[1]
        if os.path.isfile(os.path.join(out,filename)) and not force:
            print("%s: Exists !" %filename)
            iSSxM = pd.read_csv(os.path.join(out,filename),parse_dates=True,index_col=0)
        else:
            print("Processing:", file)
            st = read(file)
            print(st)
                # Merge the traces with unique IDs and fill gaps with NaNs\
            try:
                # st = st.select(channel="HHZ")
            #~ st = st.select(channel="EHZ")
                st = st.select(channel="HHZ")
            except:
                pass
            st.merge(fill_value=0)
                # Detrend and filter to remove DC offset and very long period signal
            #~ st.merge(fill_value=np.NaN)
            try:
             st.detrend('demean')
            except:
                pass

            st.filter("highpass", freq=0.1)
            st.integrate()
            st.filter("highpass", freq=8.0)
            #~ st.filter("highpass", freq=4.5)
            st.filter("lowpass", freq=16.0)
            stream = DFStream()
            stream+=st
            st=stream
            t = pd.date_range(
                st[0].stats.starttime.datetime,periods=st[0].stats.npts,
                freq="%ims"%(st[0].stats.delta*1000)
            )
            s = pd.Series(data=np.abs(st[0].data), index=t, name=st[0].id,dtype=st[0].data.dtype)
            print(s)
            iSSxM = s.resample('10T').median()
                # Export to CSV

            ##### pr virer le sac
            #~ filename = filename[:-4]

            iSSxM.to_csv(os.path.join(out,filename))
            del st

            if not dry:
                # if plotting is desired:
                if first:
                    SSxM = iSSxM
                    first = False
                else:
                    SSxM = pd.concat((SSxM,iSSxM))
            del iSSxM

    # Select a band to plot:
    t = SSxM['SSEM: [1.0, 20.0]']

    t = t.resample('5T')
    filename = 'Ijen_2012_2013_total'
    #~ SSxM['SSAM: [1.0, 15.0]'].to_csv(os.path.join(out,filename))
    SSxM.to_csv(os.path.join(out,filename))

    # Plot all points
    #~ plt.plot(t)
    #~ plt.show()
    #~ t = t.cumsum()
    t.plot()
    #~ plt.title('%s_1.0_15.0 Hz'%(station))

    # Then apply a rolling median and plot it too:
    #~ t = rolling_median(t,20*24,10)
    #~ t.plot(c='r',lw=2)
    #~ t.plot()

    # customize Axes and Show:
    plt.ylim(0,200)
    plt.show()


#END

