# -*- coding: utf-8 -*-
"""
This script generates the PowerPlant Dispa-SET data for the JRC-EU-TIMES runs

@authors: Matija Pavičević, KU Leuven
          Sylvain Quoilin, KU Leuven
"""
from __future__ import division

import os
import sys

import pandas as pd

# Local source tree imports
from dispaset_sidetools.common import date_range, write_csv_files, commons

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
data_distance = pd.read_excel(input_folder + source_folder + 'Fuel_Prices.xlsx', 2, header=0, index_col=0)

# Other options
WRITE_CSV = True
YEAR = 2015
EFFICIENCY = 0.8

# Source for demand projections
SOURCE = 'JRC'
sensitivity = 'Avg'

# Conversion factors
Gj_to_MWh = 3.6
transport_oil = 0.001429  # EUR/MWh/km
transport_hrd = 0.009383  # EUR/MWh/km

data_costs_min = data_costs.loc[['Oil - Min', 'Gas - Min', 'Hrd - Min', 'BIO', 'PEA'], :]
data_costs_avg = data_costs.loc[['Oil - Avg', 'Gas - Avg', 'Hrd - Avg', 'BIO', 'PEA'], :]
data_costs_max = data_costs.loc[['Oil - Max', 'Gas - Max', 'Hrd - Max', 'BIO', 'PEA'], :]

fuels = ['OIL', 'GAS', 'HRD', 'BIO', 'PEA']

if sensitivity == 'Min':
    data_costs = data_costs_min.reset_index(drop=True)
elif sensitivity == 'AVG':
    data_costs = data_costs_avg.reset_index(drop=True)
else:
    data_costs = data_costs_max.reset_index(drop=True)
data_costs.index = fuels
data_costs = data_costs * Gj_to_MWh

# Data processing
# Assign prices based on fingerprints
price_oil = pd.DataFrame(
    data_fingerprints['OIL - Domestic'] * data_fingerprints['Coastal'] * data_costs.loc['OIL', 'Domestic'] +
    data_fingerprints['OIL - Domestic'] * data_fingerprints['Inland'] * data_costs.loc['OIL', 'Domestic'] +
    data_fingerprints['OIL - Import'] * data_fingerprints['Coastal'] * data_costs.loc['OIL', 'Imported'] +
    data_fingerprints['OIL - Import'] * data_fingerprints['Inland'] * (data_costs.loc['OIL', 'Imported'] +
                                                                       data_distance['OIL'] * transport_oil) +
    data_fingerprints['OIL - Pipeline'] * data_fingerprints['Inland'] * data_costs.loc['OIL', 'Pipeline'],
    columns=['OIL'])
price_gas = pd.DataFrame(
    data_fingerprints['GAS - Domestic'] * data_fingerprints['Coastal'] * data_costs.loc['GAS', 'Domestic'] +
    data_fingerprints['GAS - Domestic'] * data_fingerprints['Inland'] * data_costs.loc['GAS', 'Domestic'] +
    data_fingerprints['GAS - Import'] * data_fingerprints['Coastal'] * data_costs.loc['GAS', 'Pipeline'] +
    data_fingerprints['GAS - Import'] * data_fingerprints['Inland'] * data_costs.loc['GAS', 'Imported'] +
    data_fingerprints['GAS - Pipeline'] * data_fingerprints['Coastal'] * data_costs.loc['GAS', 'Pipeline'] +
    data_fingerprints['GAS - Pipeline'] * data_fingerprints['Inland'] * (data_costs.loc['GAS', 'Pipeline'] +
                                                                         data_distance['GAS'] * transport_oil),
    columns=['GAS'])
price_hrd = pd.DataFrame(
    data_fingerprints['HRD - Import'] * data_fingerprints['Coastal'] * data_costs.loc['HRD', 'Imported'] +
    data_fingerprints['HRD - Import'] * data_fingerprints['Inland'] * (data_costs.loc['HRD', 'Imported'] +
                                                                       data_distance['HRD'] * transport_hrd),
    columns=['HRD'])
price_bio = pd.DataFrame(
    data_fingerprints['BIO - Moderate'] * data_fingerprints['Coastal'] * data_costs.loc['BIO', 'Moderate'] +
    data_fingerprints['BIO - Moderate'] * data_fingerprints['Inland'] * data_costs.loc['BIO', 'Moderate'] +
    data_fingerprints['BIO - Scarce'] * data_fingerprints['Coastal'] * data_costs.loc['BIO', 'Scarce'] +
    data_fingerprints['BIO - Scarce'] * data_fingerprints['Inland'] * data_costs.loc['BIO', 'Scarce'], columns=['BIO'])
price_pea = pd.DataFrame(
    data_fingerprints['PEA - Moderate'] * data_fingerprints['Coastal'] * data_costs.loc['PEA', 'Moderate'] +
    data_fingerprints['PEA - Moderate'] * data_fingerprints['Inland'] * data_costs.loc['PEA', 'Moderate'] +
    data_fingerprints['PEA - Scarce'] * data_fingerprints['Coastal'] * data_costs.loc['PEA', 'Scarce'] +
    data_fingerprints['PEA - Scarce'] * data_fingerprints['Inland'] * data_costs.loc['PEA', 'Scarce'], columns=['PEA'])

# Merge all prices into one dataframe
price_all = pd.concat([price_bio, price_gas, price_hrd, price_oil, price_pea], axis=1)

# Dataframe filled with ones
ones_df = pd.DataFrame(index=date_range('1/1/' + str(YEAR), '1/1/' + str(YEAR + 1), freq='H'),
                       columns=list(price_all.index)).fillna(1)

fuel_price = {}
for fuel in list(price_all.columns):
    fuel_price[fuel] = ones_df * price_all.loc[:, fuel]

# Generate files
write_csv_files(fuel_price, 'ARES_APP', SOURCE, 'FuelPrices', str(YEAR), WRITE_CSV, 'Zonal')
