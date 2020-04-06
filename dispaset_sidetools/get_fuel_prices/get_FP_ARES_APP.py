# -*- coding: utf-8 -*-
"""
This script generates the PowerPlant Dispa-SET data for the JRC-EU-TIMES runs

@authors: Matija Pavičević, KU Leuven
          Sylvain Quoilin, KU Leuven
"""
from __future__ import division

import pandas as pd
import logging
import os
import sys
# Local source tree imports
from dispaset_sidetools.common import date_range, get_country_codes, write_csv_files, commons, get_ktoe_to_mwh

sys.path.append(os.path.abspath(r'../..'))

# %% Inputs
# Folder destinations
input_folder = commons['InputFolder']
source_folder = 'ARES_Africa/'
output_folder = commons['OutputFolder']
input_file_generation = 'Annual_Generation_Statistics.xlsx'

# Local files
data_costs = pd.read_excel(input_folder + source_folder + 'Fuel_Prices.xlsx', 0, header=0, index_col=0)
data_fingerprints = pd.read_excel(input_folder + source_folder + 'Fuel_Prices.xlsx', 1, header=0, index_col=0)

# Other options
WRITE_CSV = True
YEAR = 2015
EFFICIENCY = 0.8

# Source for demand projections
SOURCE = 'JRC'

# Data processing
# Assign prices based on fingerprints
price_oil = pd.DataFrame(
    data_fingerprints['OIL - Domestic'] * data_fingerprints['Coastal'] * data_costs.loc['OIL', 'Coastal'] + \
    data_fingerprints['OIL - Domestic'] * data_fingerprints['Inland'] * data_costs.loc['OIL', 'Inland'] + \
    data_fingerprints['OIL - Import'] * data_fingerprints['Coastal'] * data_costs.loc['OIL', 'Coastal'] + \
    data_fingerprints['OIL - Import'] * data_fingerprints['Inland'] * data_costs.loc['OIL', 'Inland'], columns=['OIL'])
price_gas = pd.DataFrame(
    data_fingerprints['GAS - Domestic'] * data_fingerprints['Coastal'] * data_costs.loc['GAS', 'Domestic'] + \
    data_fingerprints['GAS - Domestic'] * data_fingerprints['Inland'] * data_costs.loc['GAS', 'Domestic'] + \
    data_fingerprints['GAS - Pipeline'] * data_fingerprints['Coastal'] * data_costs.loc['GAS', 'Pipeline'] + \
    data_fingerprints['GAS - Pipeline'] * data_fingerprints['Inland'] * data_costs.loc['GAS', 'Pipeline'] + \
    data_fingerprints['GAS - Import'] * data_fingerprints['Coastal'] * data_costs.loc['GAS', 'Pipeline'] + \
    data_fingerprints['GAS - Import'] * data_fingerprints['Inland'] * data_costs.loc['GAS', 'Imported'],
    columns=['GAS'])
price_hrd = pd.DataFrame(
    data_fingerprints['HRD - Domestic'] * data_fingerprints['Coastal'] * data_costs.loc['GAS', 'Domestic'] + \
    data_fingerprints['HRD - Domestic'] * data_fingerprints['Inland'] * data_costs.loc['GAS', 'Domestic'] + \
    data_fingerprints['HRD - Import'] * data_fingerprints['Coastal'] * data_costs.loc['GAS', 'Imported'] + \
    data_fingerprints['HRD - Import'] * data_fingerprints['Inland'] * data_costs.loc['GAS', 'Imported'],
    columns=['HRD'])
price_lig = pd.DataFrame(
    data_fingerprints['LIG - Import'] * data_fingerprints['Coastal'] * data_costs.loc['LIG', 'Imported'] * 0.87 + \
    data_fingerprints['LIG - Import'] * data_fingerprints['Inland'] * data_costs.loc['LIG', 'Imported'],
    columns=['LIG'])
price_bio = pd.DataFrame(
    data_fingerprints['BIO - Moderate'] * data_fingerprints['Coastal'] * data_costs.loc['BIO', 'Moderate'] + \
    data_fingerprints['BIO - Moderate'] * data_fingerprints['Inland'] * data_costs.loc['BIO', 'Moderate'] + \
    data_fingerprints['BIO - Scarce'] * data_fingerprints['Coastal'] * data_costs.loc['BIO', 'Scarce'] * 0.87 + \
    data_fingerprints['BIO - Scarce'] * data_fingerprints['Inland'] * data_costs.loc['BIO', 'Scarce'], columns=['BIO'])
price_pea = pd.DataFrame(
    data_fingerprints['PEA - Moderate'] * data_fingerprints['Coastal'] * data_costs.loc['PEA', 'Moderate'] + \
    data_fingerprints['PEA - Moderate'] * data_fingerprints['Inland'] * data_costs.loc['PEA', 'Moderate'] + \
    data_fingerprints['PEA - Scarce'] * data_fingerprints['Coastal'] * data_costs.loc['PEA', 'Scarce'] * 0.87 + \
    data_fingerprints['PEA - Scarce'] * data_fingerprints['Inland'] * data_costs.loc['PEA', 'Scarce'], columns=['PEA'])

# Merge all prices into one dataframe
price_all = pd.concat([price_bio, price_gas, price_hrd, price_lig, price_oil, price_pea], axis=1)

# Dataframe filled with ones
ones_df = pd.DataFrame(index=date_range('1/1/' + str(YEAR), '1/1/' + str(YEAR + 1), freq='H'),
                       columns=list(price_all.index)).fillna(1)

fuel_price = {}
for fuel in list(price_all.columns):
    fuel_price[fuel] = ones_df * price_all.loc[:, fuel]

# Generate files
write_csv_files(fuel_price, 'ARES_APP', SOURCE, 'FuelPrices', str(YEAR), WRITE_CSV, 'Zonal')
