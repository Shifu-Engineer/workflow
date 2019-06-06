import h5py
import matplotlib
matplotlib.use('agg')  #Workaround for missing tkinter
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import urllib
import time
import datetime
import timeit
import requests
import optparse

# optparse is outstanding, handling many types and
# generating a --help very easily.  Typical Python module with named, optional arguments
# For instance:
### Make a parser
parser = optparse.OptionParser("usage: %prog [options] <input file.ROOT> \n")
### Add options
parser.add_option ('-v', dest='debug', action="store_true", default=False,
                   help="Turn on verbose debugging.")
parser.add_option ('--days', dest='days', action="store_true", default=0,
                   help="Days before start time to request data? Default zero.")
parser.add_option ('--hours', dest='hours', action="store_true", default=0,
                   help="Hours before start time to request data? Default zero.")
parser.add_option ('--minutes', dest='minutes', action="store_true", default=0,
                   help="Minutes before start time to request data? Default zero.")
parser.add_option ('--seconds', dest='seconds', action="store_true", default=0,
                   help="Seconds before start time to request data? Default zero.")
### Get the options and argument values from the parser....
options, args = parser.parse_args()
### ...and assign them to variables. (No declaration needed, just like bash!)
debug   = options.debug
days    = options.days    
hours   = options.hours   
minutes = options.minutes 
seconds = options.seconds 

# If no time interval set, default to 1 second
if days == 0 and hours == 0 and minutes == 0 and seconds == 0: seconds = 1

if debug:
    print ("Time interval: days = "+str(days)+
           ", hours = "  +str(hours  )+
           ", minutes = "+str(minutes)+
           ", seconds = "+str(seconds)+".")

def read_URL_to_file (URL, filename):
    with urllib.request.urlopen(URL) as url_returns:
        data = url_returns.read().decode('utf-8').split('\n')
        with open(filename, 'w') as f:
            for datum in data:
                f.write("%s\n" % datum)
                
    return 
interval = datetime.timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)

now = datetime.datetime.now()
starttime = '{0:%Y-%m-%d+%H:%M:%S}'.format(now - interval)
stopptime = '{0:%Y-%m-%d+%H:%M:%S}'.format(now )

##starttime = '{0:%Y-%m-%d}'.format(now - one_day)
##stopptime = '{0:%Y-%m-%d}'.format(now )
##
# logger_get ACL command documentation: https://www-bd.fnal.gov/issues/wiki/ACLCommandLogger_get
URL = "http://www-ad.fnal.gov/cgi-bin/acl.pl?acl=logger_get/date_format='utc_seconds'/ignore_db_format/start=\""+starttime+"\"/end=\""+stopptime+"\"/node="

D43DataLoggerNode = 'MLrn'
URL = URL + D43DataLoggerNode + '+'
deviceNames = ['B:VIMIN', 'B_VIMIN', 'B:VIMAX', 'B_VIMAX', 'B:IMINER', 'B:NGMPS', 'B:VINHBT', 'B:GMPSFF', 'B:GMPSBT',
               'B:IMINST', 'B:IPHSTC', 'B:IMINXG', 'B:IMINXO', 'B:IMAXXG', 'B:IMAXXO', 'B_VINHBT', 'B_GMPSFF', 'B_GMPSBT',
               'B_IMINST', 'B_IPHSTC', 'B_IMINXG', 'B_IMINXO', 'B_IMAXXG', 'B_IMAXXO',
               'B:ACMNPG', 'B:ACMNIG', 'B:ACMXPG', 'B:ACMXIG', 'B:DCPG' , 'B:DCIG', 'B:VIPHAS',
               'B_ACMNPG', 'B_ACMNIG', 'B_ACMXPG', 'B_ACMXIG', 'B_DCPG' , 'B_DCIG', 'B_VIPHAS',
               'B:PS1VGP', 'B:PS1VGM', 'B:GMPS1V', 'B:PS2VGP', 'B:PS2VGM', 'B:GMPS2V', 'B:PS3VGP', 'B:PS3VGM', 'B:GMPS3V', 'B:PS4VGP', 'B:PS4VGM', 'B:GMPS4V']


tempfilename = 'temp_file.txt'
timestamps = np.zeros(shape=(1,1))

dfdict = {} #Need a place to keep each dataframe
for deviceName in deviceNames:
    tempfilename = 'tempfile'+deviceName+'.txt'
    tempURL = URL + deviceName
    if debug: print (tempURL)

    # Download device data to local ASCII file
    with open(tempfilename, "wb") as file:
        # Column headers
        headers = 'utc_seconds'+deviceName+' \t '+deviceName+'\n'
        # Write headers encoded
        file.write(headers.encode('utf-8'))
        # Get request
        response = requests.get(tempURL)
        if str(response.content).count('logger_get') > 0:
            print (response.content) #Should go to a log file. 
            exit()
        # Write data to file
        file.write(response.content)
    # Dump the file into a pandas DataFrame 
    columns = ('utc_seconds'+deviceName, deviceName) # Will get these set up higher.
    dfdict[deviceName] = pd.read_csv(tempfilename, delim_whitespace=True, names=columns, skiprows=1)
    timestamps_thisdevice = dfdict[deviceName]['utc_seconds'+deviceName].values
    if debug: print (dfdict[deviceName])

if debug: print (dfdict.values())
df = pd.concat(dfdict.values(), axis=1)
h5key = 'x' #str(time.time())
#Fun with hdf5
df.to_hdf('moardata.h5', key=h5key, mode='w')
