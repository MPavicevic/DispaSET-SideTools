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

date_str = '1/1/2030'
start = pd.to_datetime(date_str)
hourly_periods = 8760
drange = pd.date_range(start, periods=hourly_periods, freq='H')

data_PHOT = pd.read_excel(input_folder + 'res_time_series_8760h.xlsx','pv',index_col = 0)
data_PHOT.rename(columns={'GB' : 'UK', 'GR' : 'EL'},inplace=True)
data_WTON = pd.read_excel(input_folder + 'res_time_series_8760h.xlsx','wind onshore',index_col = 0)
data_WTON.rename(columns={'GB' : 'UK', 'GR' : 'EL'},inplace=True)
data_WTOF = pd.read_excel(input_folder + 'res_time_series_8760h.xlsx','wind offshore',index_col = 0)
data_WTOF.rename(columns={'GB' : 'UK', 'GR' : 'EL'},inplace=True)
data_WTON_WTOF = pd.read_excel(input_folder + 'res_time_series_8760h.xlsx','wind on&off combined',index_col = 0)
data_WTON_WTOF.rename(columns={'GB' : 'UK', 'GR' : 'EL'},inplace=True)

regions = list(data_PHOT.columns.unique())
zero_df = pd.DataFrame(index=data_PHOT.index,columns=['HROR','WTON','WTOF','PHOT']).fillna(0)
small_df  = pd.DataFrame(index=data_PHOT.index,columns=['HDAM','HPHS']).fillna(0.1)


res_timeseries = {}
inflow_timeseries = {}
reservoirs_timeseries = {}
for region in regions:
    # PV
    tmp_PV = pd.DataFrame(data_PHOT[region],index=drange)
    tmp_PV.rename(columns={region : 'PHOT'},inplace=True)
    # Wind onshore
    if region in data_WTON:
        tmp_WTON = pd.DataFrame(data_WTON[region],index=drange)
        tmp_WTON.rename(columns={region : 'WTON'},inplace=True)
        print(region + ' WTON timseries created from WTON dataset')
    elif region in data_WTON_WTOF:
        tmp_WTON = pd.DataFrame(data_WTON_WTOF[region],index=drange)
        tmp_WTON.rename(columns={region : 'WTON'},inplace=True)
        print(region + ' WTON timseries created from WTON&WTOF dataset')
    else:
        print(region + ' WTON timeseries doesnt exist')
        tmp_WTON = pd.DataFrame(zero_df['WTON'],index=drange)
    # Wind ofshore
    if region in data_WTOF:
        tmp_WTOF = pd.DataFrame(data_WTOF[region],index=drange)
        tmp_WTOF.rename(columns={region : 'WTOF'},inplace=True)
        print(region + ' WTOF timseries created from WTOF dataset')        
    elif region in data_WTON_WTOF:
        tmp_WTOF = pd.DataFrame(data_WTON_WTOF[region],index=drange)
        tmp_WTOF.rename(columns={region : 'WTOF'},inplace=True)
        print(region + ' WTOF timseries created from WTON&WTOF dataset')
    else:
        print(region + ' WTOF timeseries doesnt exist')
        tmp_WTOF = pd.DataFrame(zero_df['WTOF'],index=drange)
    # Hydro run-of-river
    tmp_HROR = pd.read_csv(input_folder + 'AvailabilityFactors/' + region + '/1h/2016.csv')
    tmp_HROR = tmp_HROR.head(8760)
    if 'HROR' in tmp_HROR:
        tmp_HROR = pd.DataFrame(tmp_HROR['HROR'].values, index=drange, columns = ['HROR'])
    else:
        print(region + ' there is no HROR timeseries present in the availability factors')
        tmp_HROR = pd.DataFrame(zero_df['HROR'],index=drange)
    
    # Combine it all together
    tmp_res_timeseries = [tmp_WTON,tmp_WTOF,tmp_PV,tmp_HROR]
    res_timeseries[region] = pd.concat(tmp_res_timeseries,axis=1)

    #TODO
    # Hydro levels and inflows
    try:
        tmp_InFlows = pd.read_csv(input_folder + 'HydroData/ScaledInflows/' + region + '/1h/2016_profile_from_2012.csv')
        tmp_InFlows = tmp_InFlows.head(8760)
        if 'HDAM' in tmp_InFlows:
            tmp_HDAM = pd.DataFrame(tmp_InFlows['HDAM'].values, index=drange, columns = ['HDAM'])
        else:
            print(region + ' there is no HDAM timeseries present in the scaled inflows')
            tmp_HDAM = pd.DataFrame(small_df['HDAM'])
        if 'HPHS' in tmp_InFlows:
            tmp_HPHS = pd.DataFrame(tmp_InFlows['HPHS'].values, index=drange, columns = ['HPHS'])
        else:
            print(region + ' there is no HPHS timeseries present in the scaled inflows')
            tmp_HPHS = pd.DataFrame(small_df['HPHS'],index=drange) 
        tmp_inflow_timeseries = [tmp_HDAM,tmp_HPHS]
        inflow_timeseries[region] = pd.concat(tmp_inflow_timeseries,axis=1)
    except FileNotFoundError: 
        print(region + ' No such file. Unable to create HDAM and HPHS scaled inflows time series. Switching to IF of AT') 
        tmp_InFlows = pd.read_csv(input_folder + 'HydroData/ScaledInflows/' + 'AT' + '/1h/2016_profile_from_2012.csv')
        tmp_InFlows = tmp_InFlows.head(8760)
        tmp_HDAM = pd.DataFrame(tmp_InFlows['HDAM'].values, index=drange, columns = ['HDAM'])        
        tmp_HPHS = pd.DataFrame(tmp_InFlows['HPHS'].values, index=drange, columns = ['HPHS'])
        tmp_inflow_timeseries = [tmp_HDAM,tmp_HPHS]
        inflow_timeseries[region] = pd.concat(tmp_inflow_timeseries,axis=1)
    
    try:    
        tmp_Reservoirs = pd.read_csv(input_folder + 'HydroData/ScaledLevels/' + region + '/1h/2016.csv')
        tmp_Reservoirs = tmp_Reservoirs.head(8760)
        if region in tmp_Reservoirs:
            tmp_Levels = pd.DataFrame(tmp_Reservoirs[region].values, index=drange, columns = [region])
        else:
            print(region + ' there is no HDAM timeseries present in the scaled inflows')
            tmp_Levels = pd.DataFrame(index=drange,columns=[region]).fillna(0.1)
        reservoirs_timeseries[region] = tmp_Levels
    except FileNotFoundError: 
        print(region + ' No such file. Unable to create HDAM and HPHS scaled reservoir levels time series. Switching to RL of AT') 
        tmp_Reservoirs = pd.read_csv(input_folder + 'HydroData/ScaledLevels/' + 'AT' + '/1h/2016.csv')
        tmp_Reservoirs = tmp_Reservoirs.head(8760)
        tmp_Levels = pd.DataFrame(tmp_Reservoirs['AT'].values, index=drange, columns = [region])
        reservoirs_timeseries[region] = tmp_Levels
       
        
    

def write_csv_files(file_name_AF,file_name_IF,file_name_RL,res_timeseries,inflow_timeseries,reservoirs_timeseries,write_csv=None):
    '''
    Function that generates .csv files in the Output/Database/PowerPlants/ folder
    :power_plant_filename:      clustered for example (has to be a string)
    :units:                     allunits for example
    '''
    filename_AF = file_name_AF + '.csv'
    filename_IF = file_name_IF + '.csv'
    filename_RL = file_name_RL + '.csv'
    if write_csv == True:
        for c in res_timeseries:
            make_dir(output_folder + 'Database')
            folder = output_folder + 'Database/AvailabilityFactors/'
            make_dir(folder)
            make_dir(folder + c)
            res_timeseries[c].to_csv(folder + c + '/' + filename_AF) 
        for c in inflow_timeseries:     
            make_dir(output_folder + 'Database')
            make_dir(output_folder + 'Database/HydroData')
            folder_1 = output_folder + 'Database/HydroData/ScaledInflows/'
            make_dir(folder_1)
            make_dir(folder_1 + c)
            inflow_timeseries[c].to_csv(folder_1 + c + '/' + filename_IF)
        for c in reservoirs_timeseries:
            folder_2 = output_folder + 'Database/HydroData/ScaledLevels/'             
            make_dir(folder_2)  
            make_dir(folder_2 + c)            
            reservoirs_timeseries[c].to_csv(folder_2 + c + '/' + filename_RL)             
    else:
        print('[WARNING ]: '+'WRITE_CSV_FILES = False, unable to write .csv files')

# write_csv_files('OSE_AvailabilityFactors_2030','OSE_IF_2030','OSE_RL_2030',res_timeseries,inflow_timeseries,reservoirs_timeseries,True)

 
 