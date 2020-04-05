# -*- coding: utf-8 -*-
"""
This script is used to format the raw csv data provided by EnergyScope
All time series are gathered for a specific year and saved in new csv files with varying timesteps

@author:
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


input_folder = '../../Inputs/EnergyScope/'
output_folder = '../../Outputs/EnergyScope/'

#input file
#TotalLoadValue = pd.read_csv(input_folder + 'EUD_ELEC.txt',delimiter = '\t' ,index_col = 0)
TotalLoadValue = from_excel_to_dataFrame(input_folder + 'DATA_preprocessing_BE.xlsx', 'EUD_elec')


#Enter the starting date
start = pd.to_datetime(date_str)
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
