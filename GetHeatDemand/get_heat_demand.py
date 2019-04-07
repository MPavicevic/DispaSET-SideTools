# -*- coding: utf-8 -*-
"""
Created on Sun Apr  7 18:53:45 2019

@author: Matija Pavičević 
"""

import pickle
import pandas as pd
import os
from common import mapping,outliers_vre,fix_na,make_dir,entsoe_types,commons

# Load data
year = 2016
pickle_off = open('../GetCapacities/pp_capacities.p','rb')
allunits = pickle.load(pickle_off)

demand = pd.read_csv('Nondimensional_heat_demand.csv')

available_countries = list(demand)

# Identify units that need CHP demand
heat_demand = pd.DataFrame()
for c in allunits:
    # c = 'EE'
    chp_heat = pd.DataFrame()
    tmp_demand = pd.DataFrame()
    tmp_units = allunits[c]
    if c in available_countries:
        tmp_demand = demand[c]
        # print('Country '+ c + ': Heat demand created')
    else:
        tmp_demand = demand['EU']
        print('Country '+ c + ': No loacl time series generic heat demand created')
    # heat_capacity = tmp_units['Unit'].loc[] 
    chp_units = tmp_units[tmp_units['Unit'].str.contains("CHP")==True]
    chp_heat['HeatCapacity'] = chp_units['PowerCapacity']/chp_units['CHPPowerToHeat']*chp_units['Nunits']
    chp_heat = chp_heat.T
    # print(chp_heat)
    for u in chp_heat:
        tmp_cap = chp_heat[u]
        tmp_dem = tmp_cap['HeatCapacity']*tmp_demand
        tmp_dem = pd.DataFrame({u:tmp_dem.values})
        heat_demand = heat_demand.merge(tmp_dem, how='outer', left_index=True, right_index=True) 

#%% Write csv file:
'''    
inputs (power plant file name as a string)
:pp_filename:     clustered for example
:units:           allunits for example
'''
filename =  str(year) + '.csv'
make_dir('Database')
folder = 'Database/Heat_demand/'
make_dir(folder)
heat_demand.to_csv(folder + filename)     

