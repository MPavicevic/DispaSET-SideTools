# -*- coding: utf-8 -*-
"""
Created on Sat Dec 28 18:38:32 2019

@author: Andrea
"""
from __future__ import division

#%%
'''
Script to control that the power capacity given by times * the Scaled Inflows in 
Dispa-SET provide a value close to the Energy production by unit given in TIMES
'''

#%% Import files 

import pandas as pd 
import sys,os
import numpy as np 

# Insert the path where DispaSET---Side-Tools is located
dispaset_sidetools_path = r'C:\Users\Andrea\GitHub\DispaSET---Side-Tools'

sys.path.append(os.path.abspath(dispaset_sidetools_path))
os.chdir(dispaset_sidetools_path)

from dispaset_sidetools.common import make_dir

WRITE_CSV_FILES = True  # Write csv database

#Output File name
scenario = 'ProRes1'
year = '2050'

filename = 'ScaledInflows_%s_%s' %(scenario, year)

#%% Files to be loaded 

input_folder = 'Inputs/'  # Standard input folder
source_folder = 'Default/'
output_folder = 'Outputs/'  # Standard output folder

#Input files for the Scaled Inflows from Dispa-SET
inputfile_inflows = input_folder + source_folder + "HydroData/ScaledInflows/%s/1h/2016_profile_from_2012.csv"
inputfolder_inflows = input_folder + source_folder + "HydroData\ScaledInflows"

#Provide the path for the TIMES Capacities divided by technology
inputfile_cap = input_folder + "/JRC_EU_TIMES/TIMES_Capacities_technology_2050.csv"

#Provide the path for the TIMES Energy production for the HROR units
inputfile_en_hdam = input_folder + "/JRC_EU_TIMES/TIMES_Energy_HDAM.xlsx"

#%% Scaled Inflows

#Loading the Scaled Inflows from Dispa-SET

countries = ['AT', 'BE', 'BG', 'CZ', 'DE','DK', 'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'LV', 'LT', 'LU', 'HU', 'NL', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI', 'SE', 'UK', 'NO', 'CH', 'CY', 'MT']
available_countries = os.listdir(inputfolder_inflows)

scaled_inflows = {}

#%% Cf for HDAM units 

#Calculate the capacity factor for the HDAM Units 

cf_hdam = pd.DataFrame(index = [0])

for c in countries: 
    if c in available_countries:
        scaled_inflows[c] = pd.read_csv(inputfile_inflows %c, index_col = 0, header = 0)
        cf_hdam[c] = scaled_inflows[c]['HDAM'].mean()

pmax = pd.read_csv(inputfile_cap, header = 0, index_col = 0)
pmax_hdam = pmax["WAT_HDAM"] #MW

en_times_hdam = pd.read_excel(inputfile_en_hdam, index_col = 0, skiprows = 3) #PJ
en_times_hdam = en_times_hdam.sum(axis = 1)/3.6*1000 #GWh

en_cf_hdam = (pmax_hdam * cf_hdam *8784/1000).T #GWh
cf_times_hdam = en_times_hdam*1000/(pmax_hdam*8784)

#Calculates the updated AF in order to meet the target of energy production 
af_multiplier_hdam = en_times_hdam / en_cf_hdam.iloc[:,0]

af_multiplier_hdam.replace([np.inf, -np.inf], np.nan, inplace = True)
af_multiplier_hdam.fillna(1, inplace = True)

scaled_inflows_scaled = {}

#Extend the values for HDAM also to HPHS

for c in countries: 
    if c in available_countries:
        scaled_inflows_scaled[c] = pd.DataFrame(columns = ['HDAM', 'HPHS'])
        scaled_inflows_scaled[c]['HDAM'] = scaled_inflows[c]['HDAM']*af_multiplier_hdam[c]
        scaled_inflows_scaled[c]['HPHS'] = scaled_inflows_scaled[c]['HDAM']
        
#%% Export the scaled ScaledInflows

def write_csv_files(filename, variable, write_csv=None):
    """
    Function that generates .csv files in the Output/Database/HydroData/ScaledInflows folder
    :filename:      has to be a string
    :variable:      af_scaled for example
    """
    filename = filename + '.csv'
    variable = variable
    if write_csv is True:
        for c in available_countries: 
            make_dir((output_folder))
            make_dir(output_folder +  'Database')
            folder = output_folder +  'Database/HydroData/'
            make_dir(folder)
            folder = output_folder +  'Database/HydroData/ScaledInflows/'
            make_dir(folder)
            folder = folder + c
            make_dir(folder)
            folder = folder + '/1h'
            make_dir(folder)
            variable[c].to_csv(folder + '/' + filename)
    else:
        print('[WARNING ]: ' + 'WRITE_CSV_FILES = False, unable to write .csv files')

write_csv_files(filename, scaled_inflows_scaled, WRITE_CSV_FILES)

