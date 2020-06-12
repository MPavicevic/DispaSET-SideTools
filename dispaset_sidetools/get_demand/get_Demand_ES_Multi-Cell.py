# -*- coding: utf-8 -*-
"""
This script generates the country Electricity End-use Demand time series for Dispa-SET
Input : EnergyScope database
Output : Database/TotalLoadValue/##/... .csv

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

######################################################################################################

#Enter the starting date
start = pd.to_datetime(date_str)
drange = pd.date_range(start, periods=hourly_periods, freq='H')

# Create final dataframe
EUD_elec = pd.DataFrame(index = drange, columns = countries)

for x in countries:

    grid_losses = grid_losses_list[countries.index(x)]

    #input file
    TotalLoadValue = from_excel_to_dataFrame(input_folder + x + '/' + 'DATA_preprocessing.xlsx', 'EUD_elec')
    TotalLoadValue.set_index(drange, inplace=True)

    extra_elec_demand = 0
    extra_demand_tech = list()
    for y in (elec_mobi_tech ):
        elec = search_YearBalance(x, y, 'ELECTRICITY') #TO CHECK
        if elec!=0 :
            extra_demand_tech.append(y)
            extra_elec_demand = extra_elec_demand - elec #[GWh]

    factor = (search_YearBalance(x,'END_USES_DEMAND', 'ELECTRICITY')-extra_elec_demand*grid_losses)/((TotalLoadValue[x].sum()/1000))

    TotalLoadValue = TotalLoadValue.multiply(factor)
    TotalLoadValue_ESinput = pd.DataFrame(index=range(0,8760), columns=extra_demand_tech)

    ElecLayers = pd.read_csv(input_folder + x + '/' + 'ElecLayers.txt',delimiter='\t')
    TD_DF = pd.read_csv(input_folder + x + '/' + 'TD_file.csv')

    for day in range(1,366):
        for h in range(1,25):
            thistd = get_TD(TD_DF,(day-1)*24+h,n_TD)
            for y in extra_demand_tech:
                TotalLoadValue_ESinput.at[(day-1)*24+h-1, y] = search_ElecLayers(ElecLayers,thistd,h,y) * 1000 #TO CHECK


    TotalLoadValue_ESinput['Sum'] = -TotalLoadValue_ESinput.sum(axis=1)
    TotalLoadValue_ESinput = TotalLoadValue_ESinput.set_index(drange)
    EUD_elec[x] = TotalLoadValue[x] + TotalLoadValue_ESinput['Sum'].multiply(1+grid_losses)

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

write_csv_files('2015_ES',EUD_elec,True)

