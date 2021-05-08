# -*- coding: utf-8 -*-
"""
This script generates the country H2 Demand time series for Dispa-SET
Input : EnergyScope database
Output : Database/H2Demand/##/... .csv

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
from dispaset_sidetools.search import * #from_excel_to_dataFrame,search_YearBalance
from dispaset_sidetools.constants import *

Zone = None

ES_folder = '../../../EnergyScope/'
DATA = 'Data/'
STEP_1 = 'STEP_1_TD_selection/'
STEP_2 = 'STEP_2_Energy_Model/'

# folder with the common.py and various Dictionaries
sidetools_folder = '../'
# to access DATA - DATA_preprocessing_BE & Typical_Units (to find installed power f [GW or GWh for storage])
hourly_data = ES_folder + STEP_2 + 'output/hourly_data/'

######################################################################################################
#Enter the starting date
start = pd.to_datetime(date_str)
drange = pd.date_range(start, periods=hourly_periods, freq='H')

columns_countries = [c + '_H2_ELECTROLYSIS' for c in countries]
H2_EUD = pd.DataFrame(index = drange, columns=columns_countries)


for x in countries:
    #input file
    H2Layers = pd.read_csv(input_folder + x + '/' + 'H2Layers.txt',delimiter='\t')
    TD_DF = pd.read_csv(input_folder + x + '/' +'TD_file.csv')

    #Create the dataframe which ill take values or all countries
    tech_country = []
    for y in H2_tech_elec:
        elec = search_YearBalance(x ,y ,'H2') #TO CHECK
        if elec!=0 :
            tech_country.append(x + '_' + y)
    H2_ESinput = pd.DataFrame(index=range(0,8760), columns=tech_country)


    #Fill in vaue of H2 Demand in H2_ESinput
    for day in range(1,366):
        for h in range(1,25):
            thistd = get_TD(TD_DF,(day-1)*24+h,n_TD)
            for y in H2_tech_elec:
                name = x + '_' + y
                H2_ESinput.at[(day-1)*24+h-1, name] = search_H2Layers(H2Layers,thistd,h,y) * 1000 #H2 demand in GWh in ES - put in MWh ? - TO CHECK

    H2_ESinput['Sum'] = H2_ESinput.sum(axis=1) #Why do a sum ? There is only H2_ELECTROLYSIS ?
    H2_ESinput = H2_ESinput.set_index(drange)
    H2_EUD[x+ '_H2_ELECTROLYSIS'] = H2_ESinput['Sum']

######################################################################################################

# write_csv_files('2015_ES',H2_EUD, '2015_ES', index=True, write_csv=True)
