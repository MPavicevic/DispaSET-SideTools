# -*- coding: utf-8 -*-
"""
@author: Matija Pavičević
"""

from __future__ import division

import pandas as pd
import os
import sys
# Local source tree imports
from dispaset_sidetools.common import date_range, get_country_codes, write_csv_files

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
# TEMBA, IEA, JRC, World Bank, CIA: World Fact Book, Indexmundi
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
ss_annual = 391800  # MWh
data['2015']['SS'] = data['2015'].loc[:, 'SD'] / data['2015'].loc[:, 'SD'].sum() * ss_annual

# Annual adjustments based on external projections
data_annual = pd.read_excel(input_folder + source_folder + input_file_annual_data, sheet_annual_data)
tmp_data = data_annual.loc[(data_annual['Source'] == SOURCE) & (data_annual['Year'] == YEAR)]
tmp_data.index = tmp_data['Country']

# Scaling to desired year according to source
anual_scaling_factor = data['2015'] / data['2015'].sum()
data[str(YEAR)] = anual_scaling_factor * tmp_data['Energy'] * 1e3

# Generate database
write_csv_files(data[str(YEAR)], 'ARES_APP', SOURCE, 'TotalLoadValue', str(YEAR), WRITE_CSV, 'Zonal')
