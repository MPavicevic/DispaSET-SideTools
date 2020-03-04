# -*- coding: utf-8 -*-
"""
This script is used to format the raw csv data provided by EnergyScope
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

#input file
TotalLoadValue = pd.read_csv(input_folder + 'EUD_ELEC.txt',delimiter = '\t' ,index_col = 0)

#Enter Studied Countries
countries = ['BE']

#Enter the starting date
date_str = '1/1/2015'
start = pd.to_datetime(date_str)
hourly_periods = 8760
drange = pd.date_range(start, periods=hourly_periods, freq='H')

TotalLoadValue.set_index(drange, inplace=True)
TotalLoadValue.columns = countries


def write_csv_files(file_name,demand,write_csv=None):

    filename = file_name + '.csv'
    if write_csv == True:
        for c in demand:
            make_dir(output_folder + 'Database')
            folder = output_folder + 'Database/TotalLoadValue/'
            make_dir(folder)
            make_dir(folder + c)
            demand[c].to_csv(folder + c + '/' + filename, header=False)
    else:
        print('[WARNING ]: '+'WRITE_CSV_FILES = False, unable to write .csv files')

write_csv_files('2015',TotalLoadValue,True)
