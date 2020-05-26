# -*- coding: utf-8 -*-
"""
Created on Sat Dec 28 11:22:01 2019

@author: Andrea Mangipinto
"""
from __future__ import division

#%%
'''
Script to control that the power capacity given by times * the AF in Dispa-SET 
provide a value close to the Energy production by unit given in TIMES
'''
#%% Import files 

import pandas as pd 
import sys,os

# Insert the path where DispaSET---Side-Tools is located
dispaset_sidetools_path = r'../..'

sys.path.append(os.path.abspath(dispaset_sidetools_path))
os.chdir(dispaset_sidetools_path)

from dispaset_sidetools.common import make_dir

WRITE_CSV_FILES = False  # Write csv database

#Output File name
scenario = 'ProRes1'
year = '2050'
filename = 'AF_%s_%s' %(scenario, year)

#%% Files to be loaded 

input_folder = 'Inputs/'  # Standard input folder
source_folder = 'Default/'
output_folder = 'Outputs/'  # Standard output folder

# Provide the path to the folder with the starting availability factors
inputfolder_af = input_folder + source_folder + "AvailabilityFactors"

#Provide the path for the TIMES Capacities divided by technology
inputfile_cap = input_folder + "/JRC_EU_TIMES/" + scenario + "/TIMES_Capacities_technology_2050.csv"

#Provide the path for the TIMES Energy production for the HROR units
inputfile_en_hror = input_folder + "/JRC_EU_TIMES/" + scenario + "/TIMES_Energy_HROR.xlsx"

#Provide the path for the TIMES Energy production for the SUN units
inputfile_en_sun = input_folder + "/JRC_EU_TIMES/" + scenario + "/TIMES_Energy_SUN.xlsx"

#File with the BEVS AF 
inputfile_ev_af_curve = input_folder + "RAMP-mobility\RAMP-mobility_AF.csv"

#%% ################### AF #######################

#Loading the availability factors from Dispa-SET

import pandas as pd
countries = ['AT', 'BE', 'BG', 'CZ', 'DE','DK', 'EE', 'IE', 'EL', 'ES', 'FR', 
             'HR', 'IT', 'LV', 'LT', 'LU', 'HU', 'NL', 'PL', 'PT', 'RO', 'SI',
             'SK', 'FI', 'SE', 'UK', 'NO', 'CH', 'CY', 'MT']

af = {}
#year = 2050
#hour = pd.date_range(start=str(year) + '-01-01', end= str(year) + '-12-31 23:00', freq='H')

for c in countries: 
    af[c] = pd.read_csv(inputfolder_af + r"/" + c + r"\1h\2016.csv", index_col = 0, header = 0)
#    af[c].set_index(hour, inplace= True)

#%% Fix missing columns 
    
af['CY']['HROR'] = af['EL']['HROR']
af['MT']['HROR'] = af['EL']['HROR']
af['HU']['HROR'] = af['SK']['HROR']
af['NL']['HROR'] = af['BE']['HROR']

af['BG']['WTOF'] = af['FR']['WTOF']
af['CY']['WTOF'] = af['FR']['WTOF']
af['EE']['WTOF'] = af['FI']['WTOF']
af['EL']['WTOF'] = af['FR']['WTOF']
af['ES']['WTOF'] = af['FR']['WTOF']
af['HR']['WTOF'] = af['FR']['WTOF']
af['IT']['WTOF'] = af['FR']['WTOF']
af['LT']['WTOF'] = af['EE']['WTOF']
af['LV']['WTOF'] = af['EE']['WTOF']
af['MT']['WTOF'] = af['FR']['WTOF']
af['MT']['WTON'] = af['IT']['WTON']
af['PL']['WTOF'] = af['DE']['WTOF']
af['PT']['WTOF'] = af['FR']['WTOF']
af['RO']['WTOF'] = af['FR']['WTOF']
af['SI']['WTOF'] = af['FR']['WTOF']

#%% ############### Cf for HROR units ####################

#Calculate the capacity factor for the HROR Units 

cf_hror = pd.DataFrame(index = [0])

for c in countries: 
    cf_hror[c] = af[c]['HROR'].mean()

pmax = pd.read_csv(inputfile_cap, header = 0, index_col = 0)
pmax_hror = pmax["WAT_HROR"] #MW

en_times_hror = pd.read_excel(inputfile_en_hror, index_col = 0, skiprows = 1) #PJ
en_times_hror = en_times_hror/3.6*1000 #GWh
en_times_hror = en_times_hror.rename(columns = {'2050' : "0"})

en_cf_hror = (pmax_hror * cf_hror *8784/1000).T #GWh

#Calculates the updated AF in order to meet the target of energy production 
af_multiplier_hror = en_times_hror.iloc[:,0] / en_cf_hror.iloc[:,0]
af_multiplier_hror.fillna(1, inplace = True)
af_multiplier_hror['EE'] = 1

af_scaled = {}

for c in countries: 
    af_scaled[c] = pd.DataFrame(columns = ['PHOT', 'HROR', 'WTOF', 'WTON', 'BEVS'])
    af_scaled[c]['HROR'] = af[c]['HROR']*af_multiplier_hror[c]
    
#%% Cf for Photovoltaic
    
#Same for PHOT
    
import numpy as np

cf_sun = pd.DataFrame(index = [0])

for c in countries: 
    cf_sun[c] = af[c]['PHOT'].mean()

pmax_sun = pmax["SUN_SCSP"] + pmax["SUN_PHOT"]  #MW
pmax_phot = pmax["SUN_PHOT"]  #MW

en_times_sun = pd.read_excel(inputfile_en_sun, index_col = 0, skiprows = 3, header = 0) #PJ
en_times_phot = en_times_sun.loc[:,en_times_sun.columns.str.contains('PV')]

en_times_sun = en_times_sun.sum(axis = 1)/3.6*1000 #GWh

en_times_phot = en_times_phot.sum(axis = 1)/3.6*1000 #GWh

en_cf_sun = (pmax_sun * cf_sun *8784/1000).T #GWh
en_cf_phot = (pmax_phot * cf_sun *8784/1000).T #GWh

delta_sun = en_times_sun - en_cf_sun.iloc[:,0]
delta_phot = en_times_phot - en_cf_phot.iloc[:,0]

cf_times_sun = 1000*en_cf_sun[0]/(pmax_sun*8784)
cf_times_phot = 1000*en_cf_phot[0]/(pmax_phot*8784)

af_multiplier_sun = en_times_sun / en_cf_sun.iloc[:,0]
af_multiplier_phot = en_times_phot / en_cf_phot.iloc[:,0]

af_multiplier_sun.replace([np.inf, -np.inf], np.nan, inplace = True)

af_multiplier_sun.fillna(1, inplace = True)

for c in countries: 
    af_scaled[c]['PHOT'] = af[c]['PHOT']*af_multiplier_sun[c]

#%% Fix af_scaled for BEVS
    
af_ev = pd.read_csv(inputfile_ev_af_curve, index_col = 0)

af_ev['CY'] = af_ev['EL']
af_ev['MT'] = af_ev['EL']

for c in countries: 
    af_scaled[c]['BEVS'] = af_ev[c].values
    af_scaled[c]['WTON'] = af[c]['WTON']
    af_scaled[c]['WTOF'] = af[c]['WTOF']
    
#%% Save to csv

def write_csv_files(filename, variable, write_csv=None):
    """
    Function that generates .csv files in the Output/Database/AvailabilityFactors folder
    :filename:      has to be a string
    :variable:      af_scaled for example
    """
    filename = filename + '.csv'
    variable = variable
    if write_csv is True:
        for c in countries: 
            make_dir((output_folder))
            make_dir(output_folder + 'JRC_EU_TIMES/' + 'Database')
            folder = output_folder + 'JRC_EU_TIMES/' + 'Database/' + scenario + '/AvailabilityFactors/'
            make_dir(folder)
            folder = folder + c
            make_dir(folder)
            folder = folder + '/1h'
            make_dir(folder)
            variable[c].to_csv(folder + '/' + filename)
    else:
        print('[WARNING ]: ' + 'WRITE_CSV_FILES = False, unable to write .csv files')

write_csv_files(filename, af_scaled, WRITE_CSV_FILES)

