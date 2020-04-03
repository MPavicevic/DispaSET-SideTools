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
from dispaset_sidetools.common import date_range, get_country_codes, write_csv_files, commons

sys.path.append(os.path.abspath(r'../..'))

# %% Inputs
# Folder destinations
input_folder = commons['InputFolder']
source_folder = 'ARES_Africa/'
output_folder = commons['OutputFolder']

# Local files
# Typical units
typical_units = pd.read_csv(input_folder + source_folder + 'Typical_Units_ARES.csv')
# Historical power plants
pp_data = pd.read_excel(input_folder + source_folder + 'Power plants Africa.xlsx', int=0, header=1)
# Historic hydro units
data_hydro = pd.read_excel(input_folder + source_folder + 'African_hydro_dams.xlsx', int=0, header=0)

# Other options
WRITE_CSV = True
YEAR = 2018
EFFICIENCY = 0.8

# Source for demand projections
SOURCE = 'JRC'

# Input data preprocessing
pp_data['Country'] = pp_data['Country'].str.title()
pp_data['Plant'] = pp_data['Plant'].str.title()
pp_data = pp_data[~pp_data['Country'].isin(["Ascension Island", 'Tristan Da Cunha', 'St Helena'])]
pp_data = pp_data[pp_data['Status'].str.contains("OPR")]
pp_data = pp_data[~pp_data['Fuel'].str.contains("WAT")]
pp_data = pp_data[~pp_data['Fuel'].str.contains("WSTH")]

# Convert Fuels and Technologies to Dispa-SET readable format
fuels = {'AGAS': 'GAS', 'BAG': 'BIO', 'BGAS': 'GAS', 'BIOMASS': 'BIO', 'BL': 'BIO', 'CGAS': 'GAS', 'COAL': 'HRD',
         'CSGAS': 'GAS',
         'DGAS': 'GAS', 'FGAS': 'GAS', 'KERO': 'OIL', 'LGAS': 'GAS', 'LIQ': 'OIL', 'LNG': 'GAS', 'LPG': 'GAS',
         'NAP': 'OIL',
         'PEAT': 'PEA', 'REF': 'WST', 'REFGAS': 'GAS', 'SHALE': 'OIL', 'UNK': 'OTH', 'UR': 'NUC', 'WIND': 'WIN',
         'WOOD': 'BIO',
         'WOODGAS': 'GAS'}
technologies = {'CC': 'COMC', 'CCSS': 'COMC',
                'GT': 'GTUR', 'GT/C': 'GTUR', 'GT/CP': 'GTUR', 'GT/D': 'GTUR', 'GT/H': 'GTUR', 'GT/S': 'GTUR',
                'IC': 'ICEN', 'IC/CD': 'ICEN', 'IC/CP': 'ICEN', 'IC/H': 'ICEN',
                'ORC': 'GTUR',
                'PV': 'PHOT',
                'RSE': 'STUR', 'ST': 'STUR', 'ST/D': 'STUR', 'ST/S': 'STUR', 'ST/G': 'STUR',
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
            logging.info(fuel + ' and ' + technology + ' combination not present in this database.')
        else:
            data.loc[(data['Technology'] == technology) & (data['Fuel'] == fuel), cols] = \
                typical_units.loc[(typical_units['Technology'] == technology) & (typical_units['Fuel'] == fuel), cols].values
            logging.info('Typical units assigned to: ' + fuel + ' and ' + technology + ' combination.')

# Preprocess historic hydro units
# Identify and assign ISO_2 country code
countries_with_hydro = list(data_hydro['Country'])
codes_hydro = get_country_codes(countries_with_hydro)
data_hydro['Country Code'] = codes_hydro
# Create Dispa-SET readable power plant database format
hydro_units = pd.DataFrame(columns=commons['ColumnNames'])
# Assign correct names
hydro_units['Unit'] = data_hydro['Name of dam']
# Identify installed power
hydro_units['PowerCapacity'] = data_hydro['Hydroelectricity (MW)']
# Set all values that are equal to 1
for key in ['Nunits']:
    hydro_units[key] = 1
# Set all values that are equal to 0
for key in ['MinUpTime','MinDownTime','StartUpCost_pu','NoLoadCost_pu', 'RampingCost', 'PartLoadMin','StartUpTime', 'CO2Intensity']:
    hydro_units[key] = 0
# Set all values that are equal to efficiency
for key in ['Efficiency', 'MinEfficiency']:
    hydro_units[key] = EFFICIENCY
# Set all values that are equal to 0.066667
for key in ['RampUpRate', 'RampDownRate']:
    hydro_units[key] = 0.066667
# Assign strings
hydro_units['Fuel'] = 'WAT'
hydro_units['Zone'] = data_hydro['Country Code']
# Calculate storage data
data_hydro['STOCapacity'] = 9.81 * 1000 * data_hydro['Reservoir capacity (million m3)'] * \
                             data_hydro['Dam height (m)'] * EFFICIENCY / 3.6 / 1e3
# Assign technology based on minimum number of storage hours
hydro_units.loc[data_hydro['STOCapacity'] / hydro_units['PowerCapacity'] >= 5, 'Technology'] = 'HDAM'
hydro_units['Technology'].fillna('HROR', inplace=True)
hydro_units.loc[data_hydro['STOCapacity'] / hydro_units['PowerCapacity'] >= 5, 'STOCapacity'] = data_hydro['STOCapacity']
# HROR efficiency is 1
hydro_units.loc[hydro_units['Technology'] == 'HROR', 'Efficiency'] = 1

# Merge two series
data = data.append(hydro_units, ignore_index=True)
data['PowerCapacity'] = data['PowerCapacity'].astype(float)

# Countries used in the analysis
countries_EAPP = ['Burundi', 'Djibouti', 'Egypt', 'Ethiopia', 'Eritrea', 'Kenya', 'Rwanda', 'Somalia', 'Sudan',
                  'South Sudan', 'Tanzania', 'Uganda']
countries_NAPP = ['Algeria', 'Libya', 'Morocco', 'Mauritania', 'Tunisia']
countries_CAPP = ['Angola', 'Cameroon', 'Central African Republic', 'Republic of the Congo', 'Chad', 'Gabon',
                  'Equatorial Guinea', 'Democratic Republic of the Congo']

used = set()
countries = countries_EAPP + countries_CAPP + countries_NAPP
countries = [x for x in countries if x not in used and (used.add(x) or True)]
countries = get_country_codes(countries)

# Generation of allunits
allunits = {}
for c in countries:
    allunits[c] = data.loc[data['Zone'] == c]

write_csv_files(allunits, 'ARES_APP', SOURCE, 'PowerPlants', str(YEAR), WRITE_CSV, 'Zonal')
