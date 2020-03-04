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
from search import search_assets
input_folder = '../../Inputs/'  # Standard input folder
output_folder = '../../Outputs/'# Standard output folder

#Enter studied year
date_str = '1/1/2015'
start = pd.to_datetime(date_str)
hourly_periods = 8760
drange = pd.date_range(start, periods=hourly_periods, freq='H')

#input files
Storage = pd.read_csv(input_folder + 'Distri_E_stored.txt', delimiter = '\t' ,index_col = 0)
Storage.set_index(drange, inplace=True)
AvailFactors_ES = pd.read_csv(input_folder + 'AvailibilityFactors.txt',delimiter = '\t' ,index_col = 0)
AvailFactors_ES.set_index(drange, inplace=True)

#Enter countries studied
countries = list(['BE'])

#Create AvailibilityFactors
AvailFactors = ['WTON','WTOF','PHOT','HROR']
Inflows = ['HDAM','HPHS']
ReservoirLevels = ['HPHS']

#Create data structures
res_timeseries = {}
inflow_timeseries = {}
scaledlevels_timeseries = {}




for x in countries:

    tmp_WTON = pd.DataFrame(index=drange)
    tmp_WTOF = pd.DataFrame(index=drange)
    tmp_PV = pd.DataFrame(index=drange)
    tmp_HROR = pd.DataFrame(index=drange)
    #Availibility Factors
    AF_countr = [ x+'_PV', x+'_WIND_ONSHORE',x+'_WIND_OFFSHORE',x+'_HYDRO_RIVER']
    AF = ['PHOT','WTON','WTOF','HROR']
    tmp_WTON[x]= AvailFactors_ES[AF_countr[1]]
    tmp_WTOF[x]= AvailFactors_ES[AF_countr[2]]
    tmp_PV[x]= AvailFactors_ES[AF_countr[0]]
    tmp_HROR[x]= AvailFactors_ES[AF_countr[3]]

    # Combine it all together
    tmp_res_timeseries = [tmp_PV[x],tmp_WTON[x],tmp_WTOF[x],tmp_HROR[x]]
    res_timeseries[x] = pd.concat(tmp_res_timeseries,axis=1)
    res_timeseries[x].columns = AF

    res_timeseries[x].loc[res_timeseries[x]['PHOT'] < 0,'PHOT'] = 0
    res_timeseries[x].loc[res_timeseries[x]['PHOT'] > 1,'PHOT'] = 1
    res_timeseries[x].loc[res_timeseries[x]['WTON'] < 0,'WTON'] = 0
    res_timeseries[x].loc[res_timeseries[x]['WTON'] > 1,'WTON'] = 1
    res_timeseries[x].loc[res_timeseries[x]['WTOF'] < 0,'WTOF'] = 0
    res_timeseries[x].loc[res_timeseries[x]['WTOF'] > 1,'WTOF'] = 1
    res_timeseries[x].loc[res_timeseries[x]['HROR'] < 0,'HROR'] = 0
    res_timeseries[x].loc[res_timeseries[x]['HROR'] > 1,'HROR'] = 1

    tmp_HDAM = pd.DataFrame(index=drange)
    tmp_HPHS = pd.DataFrame(index=drange)
#    tmp_BATS = pd.DataFrame(index=drange)
    #Scaled Inflows
    tmp_HDAM[x] = AvailFactors_ES[AF_countr[3]]
    tmp_HPHS[x] = AvailFactors_ES[AF_countr[3]]
#    inst_capa_bats = float(search_assets('BATT_LI', 'f'))
#    tmp_BATS[x] = Storage['BATT_LI_in']
#    tmp_inflow_timeseries = [tmp_HDAM[x], tmp_HPHS[x],abs(tmp_BATS[x]).div(inst_capa_bats)]
    tmp_inflow_timeseries = [tmp_HDAM[x], tmp_HPHS[x]]
    inflow_timeseries[x] = pd.concat(tmp_inflow_timeseries, axis=1)
    inflow_timeseries[x].columns = Inflows


#    tmp_BATT_LI = pd.DataFrame(index=drange)
    tmp_scaledlevels_timeseries = pd.DataFrame(index=drange)
    #ScaledLevels
#    tmp_BATT_LI[x] = Storage['BATT_LI']
#    inst_capa_1 = float(search_assets('BATT_LI', 'f'))
    tmp_HPHS[x] = Storage['PHS']
    inst_capa_2 = float(search_assets('PHS','f'))
#    tmp_scaledlevels_timeseries = [tmp_BATT_LI[x].div(inst_capa_1), tmp_HPHS[x].div(inst_capa_2)]
    tmp_scaledlevels_timeseries = [tmp_HPHS[x].div(inst_capa_2)]
    scaledlevels_timeseries[x] = pd.concat(tmp_scaledlevels_timeseries, axis = 1)
    Levels_countr = [x + '_BATT_LI' , x + '_PHS']
    scaledlevels_timeseries[x].columns = ReservoirLevels

'''
    tmp_Levels = pd.DataFrame(index=drange)
    #reservoirs
    tmp_Levels[x] = Storage['DAM_STORAGE']
    inst_capa = float(search_assets('HYDRO_DAM', 'f'))
    reservoirs_timeseries[x] = (tmp_Levels[x].div(1000))
'''

def write_csv_files(file_name_AF,file_name_IF,file_name_RL,res_timeseries,inflow_timeseries,scaledlevels_timeseries,write_csv=None):
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
        for c in scaledlevels_timeseries:
            folder_2 = output_folder + 'Database/HydroData/ScaledLevels/'
            make_dir(folder_2)
            make_dir(folder_2 + c)
            scaledlevels_timeseries[c].to_csv(folder_2 + c + '/' + filename_RL)

#        for c in reservoirs_timeseries:
#            folder_2 = output_folder + 'Database/HydroData/ReservoirLevel/'
#            make_dir(folder_2)
#            make_dir(folder_2 + c)
#            reservoirs_timeseries[c].to_csv(folder_2 + c + '/' + filename_RL)

    else:
        print('[WARNING ]: '+'WRITE_CSV_FILES = False, unable to write .csv files')

write_csv_files('1h','1h','1h',res_timeseries,inflow_timeseries,scaledlevels_timeseries,True)