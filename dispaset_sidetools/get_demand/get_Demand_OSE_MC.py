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