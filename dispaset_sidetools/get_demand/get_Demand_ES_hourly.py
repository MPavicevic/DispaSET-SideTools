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
from dispaset_sidetools.search import * #from_excel_to_dataFrame,search_YearBalance
from dispaset_sidetools.constants import *

input_folder = '../../Inputs/EnergyScope/'
output_folder = '../../Outputs/EnergyScope/'
sidetools_folder = '../'


######################################################################################################
#Enter the starting date
start = pd.to_datetime(date_str)
drange = pd.date_range(start, periods=hourly_periods, freq='H')

#input file
#TotalLoadValue = pd.read_csv(input_folder + 'EUD_ELEC.txt',delimiter = '\t' ,index_col = 0) #EUD Load
TotalLoadValue = from_excel_to_dataFrame(input_folder + 'DATA_preprocessing_BE.xlsx', 'EUD_elec')
TotalLoadValue.set_index(drange, inplace=True)
TotalLoadValue.columns = countries


tech_country = list()
for Country in countries:
    for y in elec_mobi_tech:
        elec = search_YearBalance(y, 'ELECTRICITY') #TO CHECK
        if elec!=0 :
            tech_country.append(Country + '_' + y)




TotalLoadValue_ESinput = pd.DataFrame(index=range(0,8760), columns=tech_country)

ElecLayers = pd.read_csv(input_folder + 'ElecLayers.txt',delimiter='\t')
TD_DF = pd.read_csv(input_folder + 'TD_file.csv')

for x in range(0,len(countries)):
    for day in range(1,366):
        for h in range(1,25):
            thistd = get_TD(TD_DF,(day-1)*24+h,n_TD)
            for y in elec_mobi_tech:
                name = countries[x] + '_' + y
                TotalLoadValue_ESinput.at[(day-1)*24+h-1, name] = search_ElecLayers(ElecLayers,thistd,h,y) * 1000 #TO CHECK


TotalLoadValue_ESinput['Sum'] = -TotalLoadValue_ESinput.sum(axis=1)
TotalLoadValue_ESinput = TotalLoadValue_ESinput.set_index(drange)
for x in countries:
    TotalLoadValue[x] = TotalLoadValue[x] + TotalLoadValue_ESinput['Sum'] # TO BE MODIFIED FOR SEVERAL COUNTRIES !!!!!!!!!!!


######################################################################################################

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

write_csv_files('2015_hourly',TotalLoadValue,True)
#TotalLoadValue.to_csv(output_folder + 'TotalLoadValue.csv', index=True)
