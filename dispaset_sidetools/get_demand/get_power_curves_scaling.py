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
import sys,os

# Insert the path where DispaSET---Side-Tools is located
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
inputfile_heat_diff =  input_folder + source_folder + '/' + scenario + "/TIMES_Delta_P2H_2050-2020.csv"

#File with the demand for EV in TIMES
inputfile_ev =  input_folder + source_folder + '/' + scenario + "/TIMES_EV_Demand_2050.csv"

# File with power curves from dispaset (%s stands for the country code)
inputfile_power = input_folder + 'Default/' + "TotalLoadValue/%s/1h/2016.csv"

#File with the demand curve for EV (Currently from PyPSA, we are working to generate better curves)
inputfile_ev_curve =input_folder + "PyPSA/PyPSA_EV_Demand_Profiles.csv"

#%% Input demands

ev_demand_times = pd.read_csv(inputfile_ev, header = 0, index_col = 0) #TWh
#ev_demand_times.rename(index = {'MT':'Mt'}, inplace = True)

#PJ
el_2050 = pd.read_csv(inputfile_el2050, header = 0, index_col = 0, skiprows = 1)
el_2020 = pd.read_csv(inputfile_el2020, header = 0, index_col = 0, skiprows = 1)
heat_delta = pd.read_csv(inputfile_heat_diff, header = 0, index_col = 0, skiprows = 1)
heat_delta = heat_delta.sum( axis = 1)
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

ev_demand_ad = ev_demand/(ev_demand.sum(axis = 0)/10**6)
ev_demand_ad['UK']  = ev_demand_ad.pop('GB')

ev_demand_ad['CY']  = ev_demand_ad['EL']
ev_demand_ad['MT']  = ev_demand_ad['EL']

ev_demand_ad.drop(columns = ['BA', 'RS'], inplace = True)


ev_demand_scaled = ev_demand_ad * ev_demand_times

for h in ['00', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23']:
    ev_demand_scaled.loc['2011-02-29 ' + h + ':00:00',:] = (ev_demand_scaled.loc['2011-02-28 ' + h + ':00:00',:] + ev_demand_scaled.loc['2011-03-01 ' + h + ':00:00',:])/2
    ev_demand_scaled.sort_index(inplace = True)

temp_friday = ev_demand_scaled.loc['2011-12-31 00:00:00':'2011-12-31 23:00:00',:]
ev_demand_scaled = ev_demand_scaled.loc[:'2011-12-31', :]
ev_demand_scaled = pd.concat([temp_friday, ev_demand_scaled], axis=0, join='inner')

yr = 2016
hour = pd.date_range(start=str(yr) + '-01-01', end= str(yr) + '-12-31 23:00', freq='H')
ev_demand_scaled.set_index(hour, inplace= True)

p_curve_scaled_ev = p_curve_scaled + ev_demand_scaled
p_curve_scaled_ev.drop(columns = ['CY', 'MT'], inplace = True)


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

