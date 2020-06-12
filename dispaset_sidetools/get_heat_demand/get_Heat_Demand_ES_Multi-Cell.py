"""
This script generates the country Heat End-use Demand time series for Dispa-SET
Input : EnergyScope database
Output : Database/Heat_demand/##/... .csv

@authors: Matija Pavičević, KU Leuven
          Sylvain Quoilin, KU Leuven
          Damon Coates, UCLouvain
          Guillaume Percy, UCLouvain
"""


import sys, os
sys.path.append(os.path.abspath(r'../..'))


from dispaset_sidetools import *
import numpy as np
import pandas as pd
import math

from dispaset_sidetools.common import *
from dispaset_sidetools.search import *
from dispaset_sidetools.constants import *



#Enter the starting date
start = pd.to_datetime(date_str)
drange = pd.date_range(start, periods=hourly_periods, freq='H')

EUD_heat = {}

for x in countries:
    perc_dhn = perc_dhn_list[countries.index(x)]
    DHN_Sto_losses = DHN_Sto_losses_list[countries.index(x)]

    #Input file
    heat_ESinput = from_excel_to_dataFrame(input_folder + x + '/' + 'DATA_preprocessing.xlsx', 'EUD_heat')
    Distri_TS = pd.read_csv(input_folder + x + '/' + 'Distri_TS.txt', delimiter='\t')

    #Compute ratio_dhn_prod_losses
    dhn_sto_losses = Distri_TS['TS_DHN_SEASONAL'].sum() * DHN_Sto_losses
    prod_dhn = 0
    for i in dhn_tech:
        prod_dhn = prod_dhn + search_YearBalance(x,i,'HEAT_LOW_T_DHN')
    demand_dhn = heat_ESinput[x+'_LT'].sum() * perc_dhn /1000
    ratio_dhn_prod_losses = 1+(prod_dhn-dhn_sto_losses-demand_dhn)/(prod_dhn-dhn_sto_losses)

    heat_ESinput[x+'_DEC'] = heat_ESinput[x+'_LT'].multiply(1-perc_dhn)
    heat_ESinput[x+'_DHN'] = heat_ESinput[x+'_LT'].multiply(perc_dhn)*ratio_dhn_prod_losses
    heat_ESinput = heat_ESinput.drop([x+'_LT'], axis=1)
    heat_ESinput[x+'_IND'] = heat_ESinput[x+'_HT']
    heat_ESinput = heat_ESinput.drop([x+'_HT'], axis=1)
    heat_ESinput = heat_ESinput.set_index(drange)

    EUD_heat[x] = heat_ESinput


def write_csv_files(dem_filename, heat_demand,WRITE_CSV_FILES):
    filename = dem_filename + '.csv'
    if WRITE_CSV_FILES is True:
        for c in heat_demand:
            make_dir(output_folder + 'Database')
            folder = output_folder + 'Database/Heat_demand/'
            make_dir(folder)
            make_dir(folder + c)
            heat_demand[c].to_csv(folder + c +  '/' + filename)
    else:
        print('[WARNING ]: ' + 'WRITE_CSV_FILES = False, unable to write .csv files')

write_csv_files('2015_ES_th', EUD_heat,True)

