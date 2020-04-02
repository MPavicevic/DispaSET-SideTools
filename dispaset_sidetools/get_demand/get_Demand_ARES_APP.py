# -*- coding: utf-8 -*-
"""
@author: Matija Pavičević
"""

from __future__ import division

import pandas as pd
import os
import sys
# Local source tree imports
from dispaset_sidetools.common import make_dir, date_range, get_country_codes

sys.path.append(os.path.abspath(r'../..'))

# %% Inputs
# Folder destinations
input_folder = '../../Inputs/'  # Standard input folder
source_folder = 'ARES_Africa/'
output_folder = '../../Outputs/'  # Standard output folder

# File names
input_file_hourly_data = 'Estimated hourly load profiles (for 2010 and 2015).xlsx'
sheet_hourly_data = 'Hourly load profiles'
input_file_annual_data = 'Anual_Demand_Statistics.xlsx'
sheet_annual_data = 'Inputs'

# Other options
WRITE_CSV = False
YEAR = 2016

# Source for demand projections
SOURCE = 'TEMBA'

# %% Data preprocessing
xls = pd.ExcelFile(input_folder + source_folder + input_file_hourly_data)
data_full = pd.read_excel(xls, sheet_name=sheet_hourly_data, header=0)
data_full.dropna(axis=1, inplace=True)

data = {}
date_2010 = date_range('1/1/2010', '1/1/2011', freq='H')
date_2015 = date_range('1/1/2015', '1/1/2016', freq='H')
data[str(2010)] = data_full.loc[data_full['Year'] == 2010]
data[str(2015)] = data_full.loc[data_full['Year'] == 2015]
data[str(2010)].set_index(date_2010, inplace=True)
data[str(2015)].set_index(date_2015, inplace=True)
data[str(2010)].drop(columns=['Year', 'Hour'], inplace=True)
data[str(2015)].drop(columns=['Year', 'Hour'], inplace=True)

country_codes = get_country_codes(list(data[str(2015)].columns))
data[str(2010)].columns = country_codes
data[str(2015)].columns = country_codes
data[str(2010)].drop(columns=['Unknown code'], inplace=True)
data[str(2015)].drop(columns=['Unknown code'], inplace=True)

# South Sudan profile scaled from Sudan
ss_anual = 391800  # MWh
data['2015']['SS'] = data['2015'].loc[:, 'SD'] / data['2015'].loc[:, 'SD'].sum() * ss_anual
data['2015']['MG'] = data['2015'].loc[:, 'MZ'] / data['2015'].loc[:, 'MZ'].sum() * 100
data['2015']['MU'] = data['2015'].loc[:, 'MZ'] / data['2015'].loc[:, 'MZ'].sum() * 100
data['2015']['NA'] = data['2015'].loc[:, 'BW'] / data['2015'].loc[:, 'BW'].sum() * 100
data['2015']['SC'] = data['2015'].loc[:, 'MZ'] / data['2015'].loc[:, 'MZ'].sum() * 100

# Annual adjustments based on external projections
data_anual = pd.read_excel(input_folder + source_folder + input_file_annual_data, sheet_annual_data)
tmp_data = data_anual.loc[(data_anual['Source'] == SOURCE) & (data_anual['Year'] == YEAR)]
tmp_data.index = tmp_data['Country']

anual_scaling_factor = data['2015'] / data['2015'].sum()
data[str(YEAR)] = anual_scaling_factor * tmp_data['Energy'] * 1e3

if WRITE_CSV is True:
    for c in data[str(2010)].columns:
        make_dir(output_folder + 'Database')
        folder = output_folder + 'Database/TotalLoadValue/'
        make_dir(folder)
        make_dir(folder + c)
        data[str(2010)][c].to_csv(folder + c + '/ARES_TotalLoadValue_2010.csv', header=False)
    for c in data[str(2015)].columns:
        make_dir(output_folder + 'Database')
        folder = output_folder + 'Database/TotalLoadValue/'
        make_dir(folder)
        make_dir(folder + c)
        data[str(2015)][c].to_csv(folder + c + '/ARES_TotalLoadValue_2015.csv', header=False)
    for c in data[str(2010)].columns:
        make_dir(output_folder + 'Database')
        folder = output_folder + 'Database/TotalLoadValue/'
        make_dir(folder)
        make_dir(folder + c)
        data[str(YEAR)][c].to_csv(folder + c + '/ARES_TotalLoadValue_' + SOURCE + '_' + str(YEAR) + '.csv',
                                  header=False)
