# -*- coding: utf-8 -*-
"""
Created on Tue Mar  3 14:46:07 2020

@author: Andrea Mangipinto
"""
from __future__ import division

#%%
'''
Script to obtain the NTCs according to TYNDP 2014 (until 2030), and then using the
e-Highway project to find the NTCs in 2050.
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
scenario = 'NearZeroCarbon'
year = '2050'
filename = 'AF_%s_%s' %(scenario, year)

#%% Import NTC forecasts Excel data 

input_folder = 'Inputs/'  # Standard input folder
source_folder = 'Default/'
output_folder = 'Outputs/'  # Standard output folder
source_folder = 'JRC_EU_TIMES'

#File with NTC raw data
inputfile_ntc = input_folder + source_folder + "NTC Forecasts.xlsx"

sys.path.append(os.path.abspath(r'../..'))

ntc = {}

ntc['2020_16'] = pd.read_excel(inputfile_ntc, sheet_name='2020 - TYNDP16')
ntc['2020_18'] = pd.read_excel(inputfile_ntc, sheet_name='2020 - TYNDP18')
ntc['2030_14'] = pd.read_excel(inputfile_ntc, sheet_name='2030 - TYNDP14')
ntc['2030_16'] = pd.read_excel(inputfile_ntc, sheet_name='2030 - TYNDP16')
ntc['2030_eH'] = pd.read_excel(inputfile_ntc, sheet_name='2030 - eH')
ntc['2040_eH_add'] = pd.read_excel(inputfile_ntc, sheet_name='2040 - eH')
ntc['2040_18'] = pd.read_excel(inputfile_ntc, sheet_name='2040 - TYNDP18')
ntc['2050_eH_add'] = pd.read_excel(inputfile_ntc, sheet_name='2050 - eH')

#%% Changing zone names (from a to b), filtering the internal transmissions and adding values of same borders

def clean_ntc_db(db_name, a = None, b = None):
    
    '''Slices the c1 (country 1) and c2 (country 2) columns from a to b and capitalizes it
    Creates the border name (e.g. C1 -> C2)
    Then filters the values where C1 == C2 and groups and sums the same borders'''
    
    db_name['c1'] = db_name['c1'].str.slice(a, b)
    db_name['c1'] = db_name['c1'].str.upper()
    
    db_name['c2'] = db_name['c2'].str.slice(a, b)
    db_name['c2'] = db_name['c2'].str.upper()
    
    db_name = db_name[db_name['c1'] != 'NS']
    db_name = db_name[db_name['c2'] != 'NS']   
    
    db_name['Links'] = db_name['c1'] + ' -> ' + db_name['c2']
    db_name = db_name[db_name['c1'] != db_name['c2']]
    
    db_name = db_name.groupby(['Links']).sum()
    return db_name

# Apllying the function to all the databases, with different parameters 

ntc['2020_16'] = clean_ntc_db(ntc['2020_16'], 0, 2)
ntc['2020_18'] = clean_ntc_db(ntc['2020_18'], 0, 2)
ntc['2030_14'] = clean_ntc_db(ntc['2030_14'], 0, 2)
ntc['2030_16'] = clean_ntc_db(ntc['2030_16'], 0, 2)
ntc['2030_eH'] = clean_ntc_db(ntc['2030_eH'],-2)
ntc['2040_18'] = clean_ntc_db(ntc['2040_18'], 0, 2)
ntc['2040_eH_add'] = clean_ntc_db(ntc['2040_eH_add'],-2)
ntc['2050_eH_add'] = clean_ntc_db(ntc['2050_eH_add'],-2)

# Dividing the 2040 in common (50%) and extended (70%) scenario

ntc['2040_eH_add_c'] = pd.DataFrame(ntc['2040_eH_add']['Common grid'])
ntc['2040_eH_add_e'] = pd.DataFrame(ntc['2040_eH_add']['Extended grid'])

# Extend the databases to give them the same columns of 2030_eH (5 scenarios)

for column in ntc['2050_eH_add'].columns:
    ntc['2040_eH_add_c'][column] = ntc['2040_eH_add']['Common grid']
ntc['2040_eH_add_c'] = ntc['2040_eH_add_c'].drop(['Common grid'], axis=1)

for column in ntc['2050_eH_add'].columns:
    ntc['2040_eH_add_e'][column] = ntc['2040_eH_add']['Extended grid']
ntc['2040_eH_add_e'] = ntc['2040_eH_add_e'].drop(['Extended grid'], axis=1)

for column in ntc['2050_eH_add'].columns:
    ntc['2030_16'][column] = ntc['2030_16']['NTC']
ntc['2030_16'] = ntc['2030_16'].drop(['NTC'], axis=1)

for column in ntc['2050_eH_add'].columns:
    ntc['2030_14'][column] = ntc['2030_14']['NTC']
ntc['2030_14'] = ntc['2030_14'].drop(['NTC'], axis=1)

# Sum the additional transimissions to obtain the total NTC in 2040 (C & E) and 2050
ntc['2040_eH_c'] = ntc['2030_eH'].add(ntc['2040_eH_add_c'], fill_value=0)
ntc['2040_eH_e'] = ntc['2030_eH'].add(ntc['2040_eH_add_e'], fill_value=0)
ntc['2050_eH'] = ntc['2030_eH'].add(ntc['2050_eH_add'], fill_value=0)
ntc['2050_mix_14'] = ntc['2030_14'].add(ntc['2050_eH_add'], fill_value=0)   # 2030 data from TYNDP 16 + Additional in 2050 from eH
ntc['2050_mix_16'] = ntc['2030_16'].add(ntc['2050_eH_add'], fill_value=0)   # 2030 data from TYNDP 16 + Additional in 2050 from eH

# Transpose all the databases
for name in ['2020_16', '2020_18', '2030_eH', '2030_16','2030_14', '2040_18', '2040_eH_c', '2040_eH_e', '2050_eH', '2050_mix_14', '2050_mix_16']:
    ntc[name] = ntc[name].transpose()

# Drop the keys not useful anymore
for name in ['2040_eH_add', '2040_eH_add_c', '2040_eH_add_e','2050_eH_add']:
    del ntc[name]

#%% Extend the needed db to all the year 
    # Here was done for the 2050 one, but can be changed

ntc_2050_14 = pd.DataFrame(ntc['2050_mix_14'].loc['100% RES']).transpose()

year = 2016
ntc_2050_14 = pd.DataFrame(ntc_2050_14,index=pd.date_range(start=str(year) + '-01-01', end= str(year) + '-12-31 23:00', freq='H'))
ntc_2050_14 = ntc_2050_14.fillna(1)

ntc_2050_14 = pd.DataFrame(ntc_2050_14.values*ntc['2050_mix_14'].loc['100% RES'].values, columns=ntc_2050_14.columns, index=ntc_2050_14.index)

#%% Save to csv

def write_csv_files(filename, variable, write_csv=None):
    """
    Function that generates .csv files in the Output/Database/DayAheadNTC/1h/ folder
    :filename:      has to be a string)
    :variable:      ntc_2050_14 for example
    """
    filename = filename + '.csv'
    variable = variable
    if write_csv is True:
        make_dir((output_folder))
        make_dir(output_folder + '/'+ source_folder + '/Database')
        folder = output_folder + source_folder + '/Database/' + scenario + '/DayAheadNTC/'
        make_dir(folder)
        folder = folder + '/1h'
        make_dir(folder)
        variable.to_csv(folder + '/' + filename)
    else:
        print('[WARNING ]: ' + 'WRITE_CSV_FILES = False, unable to write .csv files')


write_csv_files(filename, ntc_2050_14, WRITE_CSV_FILES)

