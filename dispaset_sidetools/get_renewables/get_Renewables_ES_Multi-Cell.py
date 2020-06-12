# -*- coding: utf-8 -*-
"""
This script generates the country RES time series for Dispa-SET
Input : EnergyScope database
Output :    - Database/HydroData/ScaledLevels/##/... .csv
            - Database/HydroData/ScaledInflows/##/... .csv
            - Database/AvailabilityFactors/##/... .csv
@authors: Matija Pavičević, KU Leuven
          Sylvain Quoilin, KU Leuven
          Damon Coates, UCLouvain
          Guillaume Percy, UCLouvain
"""
from __future__ import division

import sys, os
sys.path.append(os.path.abspath(r'../..'))


from dispaset_sidetools import *
import numpy as np
import pandas as pd
import math

from dispaset_sidetools.common import *
from dispaset_sidetools.search import *
from dispaset_sidetools.constants import *


#Enter studied year
start = pd.to_datetime(date_str)
drange = pd.date_range(start, periods=hourly_periods, freq='H')

#Create data structures
res_timeseries = {}
inflow_timeseries = {}
scaledlevels_timeseries = {}


for x in countries:

    #input files
    Storage = pd.read_csv(input_folder + x + '/' + 'Distri_E_stored.txt', delimiter = '\t' ,index_col = 0)
    Storage.set_index(drange, inplace=True)
    AF_ES_df = from_excel_to_dataFrame(input_folder + x + '/' + 'DATA_preprocessing.xlsx', 'AvailabilityFactors')
    AF_ES_df.set_index(drange, inplace=True)

    #Availability Factors
    AvailFactors_DS = [' ']
    for i in AF_ES_df:
        if i[3:] in mapping['TECH']:
            DS_AF = mapping['TECH'][i[3:]]
            AvailFactors_DS.append(mapping['TECH'][i[3:]])
        elif 'Wind' in i or 'wind' in i or 'WIND' in i:
            AvailFactors_DS.append('WTON')
    AF_DS_df = AF_ES_df.set_axis(AvailFactors_DS, axis=1, inplace=False)
    for i in AvailFactors_DS:
        AF_DS_df.loc[AF_DS_df[i] < 0,i] = 0
        AF_DS_df.loc[AF_DS_df[i] > 1,i] = 1
    res_timeseries[x] = AF_DS_df.drop(AF_DS_df.columns[0], axis=1)

    #Scaled Inflows
    Inflows = pd.DataFrame(index=drange)
    for i in AvailFactors_DS:
        if i == 'HDAM' or i == 'HPHS':
            Inflows[i] = res_timeseries[x][i]
    inflow_timeseries[x] = Inflows


    #ScaledLevels:
    Levels = pd.DataFrame(index=drange)
    for i in AvailFactors_DS:
        if i == 'HDAM':
            Levels[i] = Storage['DAM_STORAGE'].div(float(search_assets(x,'DAM_STORAGE','f')))
        elif i == 'HPHS':
            Levels[i] = Storage['PHS'].div(float(search_assets(x,'PHS','f')))
    scaledlevels_timeseries[x] = Levels



def write_csv_files(file_name_AF,file_name_IF,file_name_RL,res_timeseries,inflow_timeseries,scaledlevels_timeseries,write_csv=None):

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
    else:
        print('[WARNING ]: '+'WRITE_CSV_FILES = False, unable to write .csv files')

write_csv_files('2015_ES','2015_ES','2015_ES',res_timeseries,inflow_timeseries,scaledlevels_timeseries,True)