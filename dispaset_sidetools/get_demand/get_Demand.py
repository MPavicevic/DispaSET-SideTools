# -*- coding: utf-8 -*-
"""
This script is used to format the raw csv data provided by Entso-e
All time series are gathered for a specific year and saved in new csv files with varying timesteps

@author: Matija Pavičević 
         Sylvain Quoilin
"""
from __future__ import division
import pandas as pd
import numpy as np
import os
from dispaset_sidetools.common import mapping,outliers,fix_na,make_dir
#import matplotlib.pyplot as plt

input_folder = '../../Inputs/'  # Standard input folder
output_folder = '../../Outputs/'# Standard output folder

data_1h = pd.read_csv(input_folder + 'OSE-Demand-2030.csv',index_col = 0)

date_str = '1/1/2030'
start = pd.to_datetime(date_str)
hourly_periods = 8760
drange = pd.date_range(start, periods=hourly_periods, freq='H')

data_1h = pd.DataFrame(data_1h,index=drange)
#TODO
# Automatization of dates, inputs should be either with dates or without, if without function calacultes it automatically
# 

def write_csv_files(file_name,demand,write_csv=None):
    '''
    Function that generates .csv files in the Output/Database/PowerPlants/ folder
    :power_plant_filename:      clustered for example (has to be a string)
    :units:                     allunits for example
    '''
    filename = file_name + '.csv'
    if write_csv == True:
        for c in demand:
            make_dir(output_folder + 'Database')
            folder = output_folder + 'Database/TotalLoadValue/'
            make_dir(folder)
            make_dir(folder + c)
            demand[c].to_csv(folder + c + '/' + filename)     
    else:
        print('[WARNING ]: '+'WRITE_CSV_FILES = False, unable to write .csv files')

write_csv_files('OSE_Demand_2030',data_1h,True)

# for c in data_1h:
#     tmp = data_1h[c]


# #%%
# '''
# 'BZN': Bidding zone
# 'CTA': Country Area
# 'CTY': Country
# '''
# AreaTypeCode = 'CTY'

# header = 'TotalLoadValue'            # name of the data column in the csv file
# folder = './entsoe/ActualTotalLoad'         # folder contining the data.
# year = 2015                          # considered year
# write_csv = True                     # Write csv database

# # Set time series index for new dataframe
# data_1h = pd.DataFrame(index=pd.date_range(start=str(year) + '-01-01', end= str(year) + '-12-31 23:00', freq='H'))
# data_15 = pd.DataFrame(index=pd.date_range(start=str(year) + '-01-01', end= str(year) + '-12-31 23:00', freq='15min'))
# data_30 = pd.DataFrame(index=pd.date_range(start=str(year) + '-01-01', end= str(year) + '-12-31 23:00', freq='30min'))

# dtypes={'year':np.int16,
#         'month':np.int16,
#         'day':np.int16}

# listdir = os.listdir(folder)
# files = [folder + '/' + f for f in listdir if f[:4] == str(year)]
# #files = ['ActualTotalLoad/2016_11_ActualTotalLoad.csv']
# #files = ['samples/ActualLoad.csv']
# outliers = outliers()

# for f in files:
#     data = pd.read_csv(f,header=0,index_col=None,encoding='utf-16',low_memory=False,error_bad_lines=False,sep='\t',dtype=dtypes)
    
#     data.index = pd.to_datetime(data.DateTime)
    
#     zones = list(data.MapCode.unique()) 
    
#     # Set time series index for new dataframe
#     dates = sorted(data['DateTime'].unique()) 
    
#     #tmp = data[(data.MapCode==u'BE')&(data.AreaTypeCode==AreaTypeCode)]
#     #test[tmp.index[:15]] = tmp[header][tmp.index[:15]]
    
#     for c in mapping['iso2entsoe']:
#         tmp = data[(data.MapCode==c)&(data.AreaTypeCode==AreaTypeCode)]
#         tmp = tmp[header]

#         index_1h = data_1h.index.join(tmp.index,how='inner')
#         index_15 = data_15.index.join(tmp.index,how='inner')
#         index_30 = data_30.index.join(tmp.index,how='inner')
#         data_1h.loc[index_1h,c] = tmp[index_1h]
#         data_15.loc[index_15,c] = tmp[index_15]
#         data_30.loc[index_30,c] = tmp[index_30]

# #%%

# for c in data_1h:
#     data_share = 1 - float(np.sum(np.isnan(data_1h[c])))/len(data_1h)
#     if data_share <0.75:
#         print('Deleting column "' + c + '" from the one hour data. There are only ' + str(data_share*100) + '% valid data points')
#         del data_1h[c]
#     else:
#         if c in outliers:
#             ranges = outliers[c]
#         else:
#             ranges=None
#         data_1h[c] = fix_na(data_1h[c],name=c,outliers=ranges)
        
# for c in data_30:
#     data_share = 1 - float(np.sum(np.isnan(data_30[c])))/len(data_30)
#     if data_share <0.75:
#         print('Deleting column "' + c + '" from the 30 min data. There are only ' + str(data_share*100) + '% valid data points')
#         del data_30[c]
#     else:
#         if c in outliers:
#             ranges = outliers[c]
#         else:
#             ranges=None
#         data_30[c] = fix_na(data_30[c],name=c,outliers=ranges)
    
# for c in data_15:
#     data_share = 1 - float(np.sum(np.isnan(data_15[c])))/len(data_15)
#     if data_share <0.75:
#         print('Deleting column "' + c + '" from the 15 min data. There are only ' + str(data_share*100) + '% valid data points')
#         del data_15[c]
#     else:
#         if c in outliers:
#             ranges = outliers[c]
#         else:
#             ranges=None
#         data_15[c] = fix_na(data_15[c],name=c,outliers=ranges)


# #%%
# # Changing country names to the dispa-set format:
# for c in mapping['dispa2entsoe']:
#     c_entsoe = mapping['dispa2entsoe'][c]
#     if c_entsoe in data_1h and c != c_entsoe:
#         data_1h.rename(columns={c_entsoe:c},inplace=True)
#     if c_entsoe in data_30 and c != c_entsoe:
#         data_30.rename(columns={c_entsoe:c},inplace=True)
#     if c_entsoe in data_15 and c != c_entsoe:
#         data_15.rename(columns={c_entsoe:c},inplace=True)
# #%%
# # Write to pickle:
# data_1h.to_pickle('demand_1h_' + str(year) + '.p')
# data_15.to_pickle('demand_15_' + str(year) + '.p')
# data_30.to_pickle('demand_30_' + str(year) + '.p')

    
# #%%
# # Write to CSV:
# if write_csv:
#     make_dir('Database')
#     folder = 'Database/'+header + '/'
#     make_dir(folder)
#     for c in data_1h:
#         make_dir(folder + c)
#         make_dir(folder + c + '/1h')
#         data_1h[c].to_csv(folder + c + '/1h/' + str(year) + '.csv')
#     for c in data_30:
#         make_dir(folder + c)
#         make_dir(folder + c + '/30min')
#         data_30[c].to_csv(folder + c + '/30min/' + str(year) + '.csv')
#     for c in data_15:
#         make_dir(folder + c)
#         make_dir(folder + c + '/15min')
#         data_15[c].to_csv(folder + c + '/15min/' + str(year) + '.csv')
              
 