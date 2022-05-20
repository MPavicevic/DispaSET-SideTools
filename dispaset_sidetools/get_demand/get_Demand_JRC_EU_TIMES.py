# -*- coding: utf-8 -*-
"""
Created on Mon Dec 23 19:00:19 2019

@author: Andrea Mangipinto
"""
from __future__ import division

#%%
'''
Script to scale the power curve from 2016 to the levels of TIMES, considering
the variation in heat demand 2016-TIMES year. Then adds the EV load curves, 
considering the variation in EV demand 2016-TIMES year
'''

#%% Import files 

import pandas as pd 
import numpy as np
import sys,os

# %% INPUT DATA
COP = {'COP_01' : 1, 'COP_02' : 3, 'COP_03': 3, 'COP_04': 3.3, 'COP_05' : 3.8, 'COP_07': 4}
#COP_01 electric boilers
#COP_02 Heat pump air-to-air
#COP_03 Air heat pump electric
#COP_04 Heat pump air-to-water
#COP_05 Heat pump air-to-water
#COP_07 Heat pump ground

# %% Insert the path where DispaSET---Side-Tools is located
dispaset_sidetools_path = r'../..'

sys.path.append(os.path.abspath(dispaset_sidetools_path))
os.chdir(dispaset_sidetools_path)

from dispaset_sidetools.common import make_dir

WRITE_CSV_FILES = True  # Write csv database

#Output File name
scenario = 'ProRes1'
year = '2050'

filename = 'TotalLoadValue_%s_%s' %(scenario, year)

#%% Files to be loaded 

input_folder = 'Inputs/'  # Standard input folder
source_folder = 'JRC_EU_TIMES'
output_folder = 'Outputs/'  # Standard output folder

#File with the electric generation from TIMES in year to be modelled 
inputfile_el2050 = input_folder + source_folder + '/' + scenario + "/TIMES_Electricity_generation_2050.csv"

#File with the electric generation from TIMES in 2020 
inputfile_el2020 =  input_folder + source_folder + '/' + scenario + "/TIMES_Electricity_generation_2020.csv"

#File with the variation in heat generation from TIMES in year to be modelled - 2020 
inputfile_heat_diff =  input_folder + source_folder + '/' + scenario + "/TIMES_Delta_P2H_2050_2020.xlsx"

#File with the demand for EV in TIMES
inputfile_ev =  input_folder + source_folder + '/' + scenario + "/TIMES_EV_Demand_2050.csv"

# File with power curves from dispaset (%s stands for the country code)
inputfile_power = input_folder + 'Default/' + "TotalLoadValue/%s/1h/2016.csv"

#File with the demand curve for EV 
inputfile_ev_curve = input_folder + "RAMP-mobility/RAMP-mobility_EV_Demand_Profiles.csv"

#%% Input demands

ev_demand_times = pd.read_csv(inputfile_ev, header = 0, index_col = 0) #TWh
#ev_demand_times.rename(index = {'MT':'Mt'}, inplace = True)

#PJ
el_2050 = pd.read_csv(inputfile_el2050, header = 0, index_col = 0, skiprows = 1)
el_2020 = pd.read_csv(inputfile_el2020, header = 0, index_col = 0, skiprows = 1)
heat_delta_init =  pd.read_excel(inputfile_heat_diff, header=0, index_col = 0, skiprows = 2)
heat_delta_header = pd.read_excel(inputfile_heat_diff, header=None, index_col = 0, skiprows = 1, nrows=1)

for count,i in enumerate(heat_delta_header.iloc[0,:]):
    if '2050' in str(i):
        col_2050_start = count
        break
        
#%% Pre-processing of p2h curve (substraction + division by COP)
#for h in heat_delta.columns: 
# first substract
heat_delta_init.fillna(0, inplace=True)
heat_delta_final = pd.DataFrame(columns = ["ELC01_20","ELC01_50","ELC02_20","ELC02_50",
                                 "ELC03_20","ELC03_50","ELC04_20","ELC04_50",
                                 "ELC05_20","ELC05_50", "ELC07_20","ELC07_50"],
                                 index=heat_delta_init.index)
heat_delta_final.fillna(0,inplace=True)
        
for nb in [1,2,3,4,5,7]:
    for count,h in enumerate(heat_delta_init.columns):
        if 'ELC0'+str(nb) in h:
            if count > col_2050_start:
                heat_delta_final.loc[:,'ELC0'+str(nb)+'_50'] += heat_delta_init.loc[:,h]  
            else:
                heat_delta_final.loc[:,'ELC0'+str(nb)+'_20'] += heat_delta_init.loc[:,h]
            
for count,h in enumerate(heat_delta_init.columns):
    if 'ELC0' in h:
        continue
    elif count > col_2050_start:
        heat_delta_final.loc[:,'ELC0'+str(1)+'_50'] += heat_delta_init.loc[:,h]
        heat_delta_init.drop(columns=[h], inplace=True)
    else:
        heat_delta_final.loc[:,'ELC0'+str(1)+'_20'] += heat_delta_init.loc[:,h]
        heat_delta_init.drop(columns=[h], inplace=True)
    
for nb in [1,2,3,4,5,7]:
    heat_delta_final.loc[:,'ELC0'+str(nb)+'_50'] -=  heat_delta_final.loc[:,'ELC0'+str(nb)+'_20']
    heat_delta_final.drop(columns = 'ELC0'+str(nb)+'_20', inplace = True )
    heat_delta_final.loc[:,'ELC0'+str(nb)+'_50'] /= COP['COP_0' + str(nb)] # divide by COP
    
heat_delta = heat_delta_final.sum(axis=1)

if 'IS' in heat_delta.index:
    heat_delta.drop('IS',inplace=True)
    
#TWh
el_2050 = el_2050.iloc[:,0]/3.6
if 'IS' in el_2050.index:
    el_2050.drop('IS',inplace=True)
el_2020 = el_2020.iloc[:,0]/3.6
if 'IS' in el_2020.index:
    el_2020.drop('IS',inplace=True)
heat_delta = heat_delta/3.6
ev_demand_times = ev_demand_times.iloc[:,0]
if 'IS' in ev_demand_times.index:
    ev_demand_times.drop('IS',inplace=True)
    
#- ev_demand_times
country_coeff = (el_2050 - heat_delta - ev_demand_times)/el_2020
country_coeff.drop(index = ['CY','MT'], inplace = True)
if 'Mt' in country_coeff.index:
    country_coeff.drop('Mt', inplace = True)


#%% Import the power curves from dispaset
countries = list(country_coeff.index)

#import power curves from dispaset database
p_curve_dict = {}
for c in countries: 
    p_curve_dict[c] = pd.read_csv(inputfile_power %c, header = None, index_col = 0)
    p_curve_dict[c] = p_curve_dict[c].iloc[:,0]

#create dataframe from 
p_curve = pd.DataFrame.from_dict(p_curve_dict)

p_curve_scaled = p_curve * country_coeff.T

#%% Add EV demand 

ev_demand = pd.read_csv(inputfile_ev_curve, header = 0, index_col = 0)

ev_demand_ad = ev_demand/ev_demand.sum(axis = 0) # [W/Wh] 

ev_demand_scaled = ev_demand_ad * (ev_demand_times * 1e6) # Scaled demand in MW

yr = 2016
hour = pd.date_range(start=str(yr) + '-01-01', end= str(yr) + '-12-31 23:00', freq='H')
ev_demand_scaled.set_index(hour, inplace= True)

p_curve_scaled_ev = p_curve_scaled + ev_demand_scaled

#%% Export scaled power curves
    
def write_csv_files(filename, variable, write_csv=None):
    """
    Function that generates .csv files in the Output/Database/TotalLoadValue folder
    :filename:      has to be a string
    :variable:      p_curve_scaled_ev for example
    """
    filename = filename + '.csv'
    variable = variable
    if write_csv is True:
        for c in p_curve_scaled_ev.columns: 
            make_dir((output_folder))
            make_dir(output_folder + source_folder + '/Database')
            folder = output_folder + source_folder + '/Database/' + scenario + '/TotalLoadValue/'
            make_dir(folder)
            folder = folder + c
            make_dir(folder)
            folder = folder + '/1h'
            make_dir(folder)
            variable[c].to_csv(folder + '/' + filename, header = False)
    else:
        print('[WARNING ]: ' + 'WRITE_CSV_FILES = False, unable to write .csv files')

write_csv_files(filename, p_curve_scaled_ev, WRITE_CSV_FILES)

