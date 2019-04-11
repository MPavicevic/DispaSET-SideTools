# -*- coding: utf-8 -*-
"""
Created on Sun Apr  7 18:53:45 2019

@author: Matija Pavičević 
"""

import pickle
import pandas as pd
from common import mapping,outliers_vre,fix_na,make_dir,entsoe_types,commons

# Load data
year = 2016
pickle_off = open('../GetCapacities/pp_capacities.p','rb')
allunits = pickle.load(pickle_off)
demand = pd.read_csv('Nondimensional_heat_demand_Aarhus.csv')

# Help functions
dates = pd.DataFrame(pd.date_range(start=str(year) + '-01-01', end= str(year) + '-12-31 23:00', freq='H'),columns=['dates'])
demand = demand.merge(dates, how='outer', left_index=True, right_index=True)
demand.set_index('dates',drop=True,inplace=True)
demand.ffill(inplace=True)
available_countries = list(demand)

# Identify units that need CHP demand
# heat_demand = pd.DataFrame()
h_dem={}
for c in allunits:
    heat_demand = pd.DataFrame()
    # c = 'HR'
    chp_heat = pd.DataFrame()
    tmp_demand = pd.DataFrame()
    tmp_units = allunits[c]
    if c in available_countries:
        tmp_demand = demand[c]
        print('Country '+ c + ': Heat demand created')
    else:
        tmp_demand = demand['EU']
        print('Country '+ c + ': No loacl time series generic heat demand created')
    # heat_capacity = tmp_units['Unit'].loc[] 
    chp_units = tmp_units[tmp_units['Unit'].str.contains("CHP")==True]
    chp_heat['HeatCapacity'] = chp_units['PowerCapacity']/chp_units['CHPPowerToHeat']*chp_units['Nunits']
    chp_heat = chp_heat.T
    # print(chp_heat)
    if chp_heat.empty == True:
        print('Country '+ c + ': DataFrame is empty, no heat demand created')
    else:
        
        for u in chp_heat:
            tmp_cap = chp_heat[u]
            tmp_dem = tmp_cap['HeatCapacity']*tmp_demand
            tmp_dem = pd.DataFrame({u:tmp_dem.values})
            heat_demand = heat_demand.merge(tmp_dem, how='outer', left_index=True, right_index=True) 
        heat_demand.set_index(demand.index,inplace=True)        
        h_dem[c] = heat_demand

#%% Write csv file:
'''    
inputs (heat demand file name as a string)
:filename:        clustered for example
:units:           allunits for example
'''
def write_csv_files(dem_filename,heat_demand):
    filename = dem_filename + '.csv'
    allunits = heat_demand
    for c in allunits:
        make_dir('Database')
        folder = 'Database/Heat_demand/'
        make_dir(folder)
        make_dir(folder + c)
        allunits[c].to_csv(folder + c + '/' + filename)     

write_csv_files(str(year),h_dem)


