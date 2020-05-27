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
input_file_CF = 'CF_IRENA.csv'

# Local files
# Typical units
typical_units = pd.read_csv(input_folder + source_folder + 'Typical_Units_ARES.csv')
# Historical power plants
pp_data = pd.read_excel(input_folder + source_folder + 'Power plants Africa.xlsx', int=0, header=1)
# Annual generation per fuel type
generation = pd.read_excel(input_folder + source_folder + input_file_generation, sheet_name=0, index_col=0)
generation.fillna(0, inplace=True)
# Capacity factor for CSP
capacity_factors = pd.read_csv(input_folder + source_folder + input_file_CF, index_col=0, header=0)

# Other options
WRITE_CSV = True
YEAR = 2055
EFFICIENCY = 0.8

# Source for demand projections
SOURCE = 'TEMBA'
scenario = '2.0deg'

if SOURCE == 'TEMBA':
    import pickle
    with open(input_folder + source_folder + 'TEMBA_capacities_' + scenario + '_' + str(YEAR) + '.p', 'rb') as handle:
        allunits = pickle.load(handle)

# Input data preprocessing
pp_data['Country'] = pp_data['Country'].str.title()
pp_data['Plant'] = pp_data['Plant'].str.title()
pp_data = pp_data[~pp_data['Country'].isin(["Ascension Island", 'Tristan Da Cunha', 'St Helena'])]
pp_data = pp_data[pp_data['Status'].str.contains("OPR")]
pp_data = pp_data[~pp_data['Fuel'].str.contains("WAT")]
pp_data = pp_data[~pp_data['Fuel'].str.contains("WSTH")]

# Convert Fuels and Technologies to Dispa-SET readable format
fuels = {'AGAS': 'GAS', 'BGAS': 'GAS', 'CGAS': 'GAS', 'CSGAS': 'GAS', 'DGAS': 'GAS', 'FGAS': 'GAS', 'LGAS': 'GAS',
         'LNG': 'GAS', 'LPG': 'GAS', 'REFGAS': 'GAS', 'WOODGAS': 'GAS',
         'BAG': 'BIO', 'BIOMASS': 'BIO', 'BL': 'BIO', 'WOOD': 'BIO',
         'COAL': 'HRD',
         'KERO': 'OIL', 'LIQ': 'OIL', 'SHALE': 'OIL',
         'NAP': 'OIL',
         'PEAT': 'PEA',
         'REF': 'WST', 'UNK': 'OTH',
         'UR': 'NUC',
         'WIND': 'WIN'}

technologies = {'CC/D': 'COMC', 'CC': 'COMC', 'CCSS': 'COMC', 'GT/C': 'COMC', 'GT/CP': 'COMC',
                'GT': 'GTUR', 'GT/D': 'GTUR', 'GT/H': 'GTUR', 'GT/S': 'GTUR', 'ORC': 'GTUR',
                'IC': 'ICEN', 'IC/CD': 'ICEN', 'IC/CP': 'ICEN', 'IC/H': 'ICEN',
                'RSE': 'STUR', 'ST': 'STUR', 'ST/D': 'STUR', 'ST/S': 'STUR', 'ST/G': 'STUR',
                'PV': 'PHOT',
                'WTG': 'WTON', 'WTG/O': 'WTOF'}

pp_data['Fuel'] = pp_data['Fuel'].replace(fuels)
pp_data['Technology'] = pp_data['Technology'].replace(technologies)

# Look-up countries from the database and convert to ISO_2 code
capitals = list(pp_data['Country'])
codes = get_country_codes(capitals)

# Assign data to Dispa-SET readable format
data = pd.DataFrame(columns=commons['ColumnNames'])
data['Unit'] = pp_data['Plant']
data['Zone'] = codes
data['Fuel'] = pp_data['Fuel']
data['Technology'] = pp_data['Technology']
data['PowerCapacity'] = pp_data['Capacity']

# Historic units assign only 1 per unit
data['Nunits'] = 1

# Assign missing data from typical units
cols = ['Efficiency', 'MinUpTime', 'MinDownTime', 'RampUpRate', 'RampDownRate', 'StartUpCost_pu', 'NoLoadCost_pu',
        'RampingCost', 'PartLoadMin', 'MinEfficiency', 'StartUpTime', 'CO2Intensity', 'COP', 'Tnominal', 'coef_COP_a',
        'coef_COP_b', 'STOCapacity', 'STOSelfDischarge', 'STOMaxChargingPower', 'STOChargingEfficiency']

for fuel in commons['Fuels']:
    for technology in commons['Technologies']:
        if data.loc[(data['Technology'] == technology) & (data['Fuel'] == fuel)].empty:
            # logging.info(fuel + ' and ' + technology + ' combination not present in this database.')
            continue
        else:
            data.loc[(data['Technology'] == technology) & (data['Fuel'] == fuel), cols] = \
                typical_units.loc[
                    (typical_units['Technology'] == technology) & (typical_units['Fuel'] == fuel), cols].values
            logging.info('Typical units assigned to: ' + fuel + ' and ' + technology + ' combination.')

# Annual generation in MWh
generation = get_ktoe_to_mwh(generation, ['Biofuels', 'Fosil', 'Hydro', 'Geothermal', 'RES'])

# Identify specific units for outages
if SOURCE == 'TEMBA':
    aa = pd.concat(allunits, ignore_index=True)
    bio_units = list(aa.loc[aa['Fuel'] == 'BIO']['Unit'])
    bio_data = aa.loc[aa['Fuel'] == 'BIO']
else:
    bio_units = list(data.loc[data['Fuel'] == 'BIO']['Unit'])
    bio_data = data.loc[data['Fuel'] == 'BIO']
# Identify annual generation per zone and share of installed capacity
for c in list(bio_data['Zone'].unique()):
    if c in list(generation.index):
        bio_data.loc[bio_data['Zone'] == c, 'Share'] = bio_data['PowerCapacity'].loc[bio_data['Zone'] == c] / \
                                                       bio_data['PowerCapacity'].loc[bio_data['Zone'] == c].sum()
        bio_data.loc[bio_data['Zone'] == c, 'Generation_Historic'] = generation['Biofuels'][c]
    else:
        bio_data.loc[bio_data['Zone'] == c, 'Generation_Historic'] = 0
# Assign annual generation for each individual unit based on shares
bio_data['Generation_Historic'] = bio_data['Generation_Historic'] * bio_data['Share']
# Identify capacity factors
bio_data['CF'] = bio_data['Generation_Historic'] / bio_data['PowerCapacity'] / 8760
bio_data.set_index('Unit', inplace=True)

ones_df_bio = pd.DataFrame(index=date_range('1/1/' + str(YEAR), '1/1/' + str(YEAR + 1), freq='H'),
                           columns=bio_units).fillna(1)
if SOURCE == 'TEMBA':
    bio_outage = ones_df_bio - ones_df_bio * 0.8
else:
    bio_outage = ones_df_bio - ones_df_bio * bio_data['CF']

if SOURCE == 'TEMBA':
    geo_units = list(aa.loc[aa['Fuel'] == 'GEO']['Unit'])
    geo_data = aa.loc[aa['Fuel'] == 'GEO']
else:
    geo_units = list(data.loc[data['Fuel'] == 'GEO']['Unit'])
    geo_data = data.loc[data['Fuel'] == 'GEO']
# Identify annual generation per zone and share of installed capacity
for c in list(geo_data['Zone'].unique()):
    if c in list(generation.index):
        geo_data.loc[geo_data['Zone'] == c, 'Share'] = geo_data['PowerCapacity'].loc[geo_data['Zone'] == c] / \
                                                       geo_data['PowerCapacity'].loc[geo_data['Zone'] == c].sum()
        geo_data.loc[geo_data['Zone'] == c, 'Generation_Historic'] = generation['Geothermal'][c]
    else:
        geo_data.loc[geo_data['Zone'] == c, 'Generation_Historic'] = 0
# Assign annual generation for each individual unit based on shares
geo_data['Generation_Historic'] = geo_data['Generation_Historic'] * geo_data['Share']
# Identify capacity factors
geo_data['CF'] = geo_data['Generation_Historic'] / geo_data['PowerCapacity'] / 8760
geo_data.set_index('Unit', inplace=True)

ones_df_geo = pd.DataFrame(index=date_range('1/1/' + str(YEAR), '1/1/' + str(YEAR + 1), freq='H'),
                           columns=geo_units).fillna(1)
if SOURCE == 'TEMBA':
    geo_outage = ones_df_geo - ones_df_geo * 0.65
else:
    geo_outage = ones_df_geo - ones_df_geo * geo_data['CF']

# Identify zones where units are selected
if SOURCE == 'TEMBA':
    csp_units = list(aa.loc[(aa['Fuel'] == 'SUN') & (aa['Technology'] == 'STUR')]['Unit'])
    csp_data = aa.loc[(aa['Fuel'] == 'SUN') & (aa['Technology'] == 'STUR')]
else:
    csp_units = list(data.loc[(data['Fuel'] == 'SUN') & (data['Technology'] == 'STUR')]['Unit'])
    csp_data = data.loc[(data['Fuel'] == 'SUN') & (data['Technology'] == 'STUR')]
# Asign CF for each unit
for c in list(csp_data['Zone'].unique()):
    if c in list(generation.index):
        csp_data.loc[csp_data['Zone'] == c, 'CF'] = capacity_factors.loc[c]['CF_CSP']
    else:
        csp_data.loc[csp_data['Zone'] == c, 'CF'] = 0
csp_data.set_index('Unit', inplace=True)
ones_df_csp = pd.DataFrame(index=date_range('1/1/' + str(YEAR), '1/1/' + str(YEAR + 1), freq='H'),
                           columns=csp_units).fillna(1)

csp_outage = ones_df_csp - ones_df_csp * csp_data['CF']

outage = pd.concat([bio_outage, geo_outage, csp_outage], axis=1, sort=False, join='inner')
units_with_outage = pd.concat([bio_data, geo_data, csp_data], axis=0, sort=False)
units_with_outage = units_with_outage.loc[units_with_outage['Zone'].isin(list(generation.index))]

tmp_out = {}
for c in list(units_with_outage['Zone'].unique()):
    units = units_with_outage.loc[units_with_outage['Zone'] == c].index
    tmp_out[c] = outage.loc[:, units]

if SOURCE == 'TEMBA':
    write_csv_files(tmp_out, 'ARES_APP', SOURCE + '_' + scenario, 'OutageFactors', str(YEAR), WRITE_CSV, 'Zonal')
else:
    write_csv_files(tmp_out, 'ARES_APP', SOURCE, 'OutageFactors', str(YEAR), WRITE_CSV, 'Zonal')