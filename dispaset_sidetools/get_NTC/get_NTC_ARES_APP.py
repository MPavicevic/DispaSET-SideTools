# -*- coding: utf-8 -*-
"""
@author: Matija Pavičević
"""

from __future__ import division

import pandas as pd
import os
import sys
# Local source tree imports
from dispaset_sidetools.common import date_range, get_country_codes, write_csv_files, commons

sys.path.append(os.path.abspath(r'../..'))

# %% Inputs
# Folder destinations
input_folder = commons['InputFolder']
source_folder = 'ARES_Africa/'
output_folder = commons['OutputFolder']

# Input file
input_file = 'NTCs.xlsx'
sheet_name = '2025'
SOURCE = 'JRC'

# Other options
WRITE_CSV = True
YEAR = 2025

# %% Model
# Load data
xls = pd.ExcelFile(input_folder + source_folder + input_file)
data = pd.read_excel(xls, sheet_name=sheet_name, header=2, index_col=2)
data = data.loc[:, ~data.columns.str.contains('^Unnamed')]

# Process data
countries = list(data.index)
tmp = {}
for home in countries:
    for away in countries:
        tmp[home + ' -> ' + away] = data.loc[home, away]
ntcs = pd.DataFrame(tmp, index=date_range('1/1/' + str(YEAR), '1/1/' + str(YEAR + 1), freq='H'))
ntcs.dropna(axis=1, inplace=True)

write_csv_files(ntcs, 'ARES_APP', SOURCE, 'DayAheadNTC', str(YEAR), WRITE_CSV, 'Aggregated')
