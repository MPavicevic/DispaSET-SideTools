# -*- coding: utf-8 -*-
"""
Created on Tue Mar 22 08:58:50 2016

Times are in UTC

CTA: Control Area
BZN: Bidding zone
CTY: Country (Not present in this data)


@author: S. Quoilin
"""

from __future__ import division
import pandas as pd
import numpy as np
import os
import pickle
from dispaset_sidetools.common import mapping,outliers_vre,fix_na,make_dir


AreaTypeCode = 'CTA'

header = 'ForecastTransferCapacity'     # name of the data column in the csv file
folder = './entsoe/DayAheadNTC'         # folder contining the data.
year = 2016                          # considered year
write_csv = True                     # Write csv database

outliers = None

dtypes={'year':np.int16,
        'month':np.int16,
        'day':np.int16}

listdir = os.listdir(folder)
files = [folder + '/' + f for f in listdir if f[:4] == str(year)]

data ={}
for f in files:
    data[f] = pd.read_csv(f,header=0,index_col=None,encoding='utf-16',low_memory=False,error_bad_lines=False,sep='\t',dtype=dtypes)

# Several lists are created
Year = pd.concat([data[f] for f in data])
N = len(Year)
Year.index = range(N)



#%%

# First saving the special case of north ireland:
NorthIreland_out = Year[Year['MapCodeOut']=='NIE']
NorthIreland_in = Year[Year['MapCodeIn']=='NIE']

# Selecting only the country-to-country data (not bidding zone):
Year = Year[Year['AreaOutTypeCode']==AreaTypeCode]


tuples = []
strings = []

for idx in Year.index:
    tuples.append((Year['MapCodeOut'][idx],Year['MapCodeIn'][idx]))
    #strings.append(Year['MapCodeOut'] + ' -> ' + Year['MapCodeIn'])

# Finding the unique values:
cols = {tup:tup for tup in tuples}
cols = cols.values()


#%%
# Changing strings into datetime (Time consuming!!!):
indexes = pd.DatetimeIndex(Year.DateTime)

Year.DateTime = indexes

#%%
data = pd.DataFrame(index=pd.date_range(start=str(year) + '-01-01', end= str(year) + '-12-31 23:00', freq='H'),columns = cols)

for col in cols:
    temp = Year[(Year['MapCodeOut'] == col[0]) * (Year['MapCodeIn']==col[1])]
    temp.index = temp.DateTime
    # removing wrong values (eg not hourly)
    index_ok = data.index.intersection(temp.index)
    # Removing duplicates:
    temp = temp.drop_duplicates(subset='DateTime',keep='first')
    data.loc[index_ok,col] = temp.ForecastTransferCapacity[index_ok]
    print('Processed column "' + str(col) + '"')

#data.fillna(value=0,inplace=True)
data.fillna(method='ffill',inplace=True)
data.fillna(method='bfill',inplace=True)

cols_str = [str(col[0]) + ' -> ' + str(col[1]) for col in data.columns]
data.columns=cols_str


#%%
# Aggregating/correcting data:
data2 = pd.DataFrame(index=data.index)
for col in data.columns:
    if col[:2] == 'DE':
        col2 = 'DE -> ' + col[-2:]
    elif '-> DE' in col:
        col2 = col[:2] + ' -> DE'
    else:
        col2 = col
    if col2 in data2.columns:
        data2[col2] = data2[col2] + data[col]
    else:
        data2[col2] = data[col]

if 'na -> DE' in data2:
    del data2['na -> DE']
if 'DE -> an' in data2:
    del data2['DE -> an']

# Changing GR into EL:
columns2 = [x.replace('GR','EL') for x in data2.columns]
data2.columns = columns2
# Changing GB into UK:
columns2 = [x.replace('GB','UK') for x in data2.columns]
data2.columns = columns2

# Manual fix for the interconnection AT/DE:

data2['AT -> DE'] = pd.Series(2000,index=data2.index)
data2['DE -> AT'] = pd.Series(4000,index=data2.index)

#%% 
# Adding northern ireland to the ireland zone:
IE_in = NorthIreland_in['ForecastTransferCapacity']
IE_in.index = pd.DatetimeIndex(NorthIreland_in.DateTime)
IE_in = IE_in.reindex(data.index,fill_value=0)

IE_out = NorthIreland_out['ForecastTransferCapacity']
IE_out.index = pd.DatetimeIndex(NorthIreland_out.DateTime)
IE_out = IE_out.reindex(data.index,fill_value=0)

data2['UK -> IE'] = data2['UK -> IE'] + IE_in
data2['IE -> UK'] = data2['IE -> UK'] + IE_out

data2.fillna(method='ffill',inplace=True)
data2.fillna(method='bfill',inplace=True)


#%%
# Try to load the historical flows if they were already computed.

try:
    flows = pd.read_pickle('historical_flows_' + str(year) + '.p')
except:
    print('Could not laod the historical flows (they will thus not be considered). Try running the get_HistoricalFlows.py script first')

data3 = data2.copy()
maxflows = flows.max()
maxntc = data2.max()

for i in maxflows.index:
    if i in data2:
        print('Connection ' + i + '. Maximum historical flow: ' + str(maxflows[i]) + '. Maximum NTC: ' + str(maxntc[i]))
    else:
        print('Connection ' + i + '. No NTC was found for this connection')
        data3[i] = maxflows[i]

#%%

if write_csv:
    make_dir('Database')
    make_dir('Database/DayAheadNTC')
    make_dir('Database/DayAheadNTC/1h')
    #data2.to_csv('Database/DayAheadNTC/1h/'+str(year)+'.csv')
    data3.to_csv('Database/DayAheadNTC/1h/'+str(year)+'.csv')

