# -*- coding: utf-8 -*-
"""
Created on Tue Feb 25 14:25:42 2020

@author: Eva Joskin
"""
import pickle
import pandas as pd
from dispaset_sidetools.common import make_dir

# %% Adjustable inputs that should be modified
# Scenario definition
WRITE_CSV_FILES = True  # Write csv database
SCENARIO = 'NearZeroCarbon'  # Scenario name, used for naming csv files
CASE = 'ALLFLEX'  # Case name, used for naming csv files
SOURCE = 'JRC_EU_TIMES_'  # Source name, used for naming csv files

# %% Inputs
# Folder destinations
input_folder = '../../Inputs/'  # Standard input folder
source_folder = 'JRC_EU_TIMES/'
output_folder = '../../Outputs/'  # Standard output folder
scenario = SCENARIO + '/'

# %% Load data
h2_total_demand_raw_h= pd.read_excel(
    input_folder + source_folder + scenario + 'TIMES_H2_Demand_2050.xlsx', 
    header=None, nrows = 1, skiprows = 1, index_col = 0)
h2_total_demand_raw = pd.read_excel(
    input_folder + source_folder + scenario + 'TIMES_H2_Demand_2050.xlsx', 
    header=None, index_col = 0, skiprows = 2)

# %% First solution: create a flat demand over the year
h2_total_demand=pd.DataFrame(h2_total_demand_raw.sum(axis=1),index=h2_total_demand_raw.index)
dates = pd.date_range(start='1/1/2050', end='31/12/2050 23:00:00', freq='H')

h2_demand_time_series = pd.DataFrame(0,index=dates, columns = h2_total_demand_raw.index)

for c in h2_total_demand_raw.index:
    h2_demand_time_series.loc[:,c] = h2_total_demand.loc[c,0]/(len(dates)*3.6e-6) # flat demand [MWh]
    
# %% Write csv file:
def write_csv_files(h2_TimeSeries, write_csv=None):
    """
    Function that generates .csv files in the Output/Database/h2_demand/ folder
    :h2_TimeSeries:  DataFrame with H2 demand at each hour for each zone
    """
    if write_csv is True:
        for c in h2_TimeSeries.columns:
            filename = 'H2_Demand'  +'_' + c + '_' + '2050' + '.csv'
            make_dir((output_folder))
            make_dir(output_folder + source_folder + 'Database')
            folder = output_folder + source_folder + 'Database/' + scenario + 'H2_demand/'
            make_dir(folder)
            make_dir(folder + c)
            h2_TimeSeries[c].to_csv(folder + c + '/' + filename)
    else:
        print('[WARNING ]: ' + 'WRITE_CSV_FILES = False, unable to write .csv files')


write_csv_files(h2_demand_time_series, WRITE_CSV_FILES) 
