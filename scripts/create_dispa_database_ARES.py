# -*- coding: utf-8 -*-
"""
Minimalist example file showing how to access the Dispa-SET-sidetools api to read input files and
create a database folder which can be directly used in the Dispa-SET model

@author: Matija Pavičević
"""

# Add the root folder of Dispa-SET-sidetools to the path so that the library can be loaded:
import sys, os
import pickle

sys.path.append(os.path.abspath('..'))

# Import Dispa-SET
import dispaset_sidetools as ds
import pandas as pd
import glob

# %% Inputs
# Folder destinations
# input_folder = ds.commons['InputFolder']
input_folder = '../Inputs/'
source_folder = 'ARES_Africa/'
output_folder = '../Outputs/'

# Other options
WRITE_CSV = False
YEAR = 2045
EFFICIENCY = 0.8
scenario = 'Reference'  # Reference, 1.5deg, 2.0deg

# Source for demand projections
SOURCE = 'TEMBA'

if SOURCE == 'TEMBA':
    TEMBA = True
else:
    TEMBA = False

#%% Local files
# Typical units
typical_units = pd.read_csv(input_folder + source_folder + 'Typical_Units_ARES.csv')
# Typical cooling systems
typical_cooling = pd.read_csv(input_folder + source_folder + 'Typical_Cooling.csv')
# Historical power plants
pp_data = pd.read_excel(input_folder + source_folder + 'Power plants Africa.xlsx', int=0, header=1)
# Historic hydro units
hydro_data = pd.read_excel(input_folder + source_folder + 'African_hydro_dams.xlsx', int=0, header=0)
# TEMBA Projections
temba_inputs = pd.read_csv(input_folder + source_folder + 'TEMBA_Results.csv', header=0, index_col=0)
# Hourly demand profiles
xls = pd.ExcelFile(input_folder + source_folder + 'Estimated hourly load profiles (for 2010 and 2015).xlsx')
data_full = pd.read_excel(xls, sheet_name='Hourly load profiles', header=0)
# Annual demands from various sources
data_annual = pd.read_excel(input_folder + source_folder + 'Annual_Demand_Statistics.xlsx', 'Inputs')
# Fuel data
xls_fuel = pd.ExcelFile(input_folder + source_folder + 'Fuel_Prices.xlsx')
data_costs = pd.read_excel(xls_fuel, 0, header=0, index_col=0)
data_fingerprints = pd.read_excel(xls_fuel, 1, header=0, index_col=0)
data_distance = pd.read_excel(xls_fuel, 2, header=0, index_col=0)
# NTC data
xls = pd.ExcelFile(input_folder + source_folder + 'NTCs.xlsx')
ntc_data = pd.read_excel(xls, sheet_name=str(ds.round_down(YEAR, 10)), header=2, index_col=2)
ntc_data = ntc_data.loc[:, ~ntc_data.columns.str.contains('^Unnamed')]
# Annual generation per fuel type
generation = pd.read_excel(input_folder + source_folder + 'Annual_Generation_Statistics.xlsx', sheet_name=0, index_col=0)
generation.fillna(0, inplace=True)
# Capacity factor for CSP
capacity_factors = pd.read_csv(input_folder + source_folder + 'CF_IRENA.csv', index_col=0, header=0)
# Renewables data
solar_AF = pd.read_csv(input_folder + source_folder + 'Solar_PV_AF.csv')
wind_AF = pd.read_csv(input_folder + source_folder + 'Wind_OnShore_AF.csv')
# Hydro dam data and InfLows from xlsx and csv
hydro_dam_data = pd.read_excel(input_folder + source_folder + 'African_hydro_dams.xlsx', int=0, header=0)
path = input_folder + source_folder + 'AfricaDamsInFlows'  # use your path

# Other options
STO_HOURS = 5
EFFICIENCY = 0.8
YEAR_InFlow = 2015
YEAR_Generation = 2015
SOURCE_Hydro = 'LISFLOOD'


#%% Countries used in the analysis
countries_EAPP = ['Burundi', 'Djibouti', 'Egypt', 'Ethiopia', 'Eritrea', 'Kenya', 'Rwanda', 'Somalia', 'Sudan',
                  'South Sudan', 'Tanzania', 'Uganda']
countries_NAPP = ['Algeria', 'Libya', 'Morocco', 'Mauritania', 'Tunisia']
countries_CAPP = ['Angola', 'Cameroon', 'Central African Republic', 'Republic of the Congo', 'Chad', 'Gabon',
                  'Equatorial Guinea', 'Democratic Republic of the Congo']

used = set()
countries = countries_EAPP + countries_CAPP + countries_NAPP
countries = [x for x in countries if x not in used and (used.add(x) or True)]
countries = ds.get_country_codes(countries)

allunits = ds.create_powerplants(temba_inputs, pp_data, hydro_data, typical_units, typical_cooling, countries,
                                         YEAR, EFFICIENCY, TEMBA, scenario)

# Source for demand projections
SOURCE = 'TEMBA' # TEMBA, IEA, JRC, World Bank, CIA: World Fact Book, Indexmundi

demand = ds.create_demand(data_full, data_annual,YEAR, SOURCE=SOURCE)

fuel_price = ds.create_fuel_prices(data_costs, data_fingerprints, data_distance, YEAR, SOURCE = 'JRC')

ntcs = ds.create_ntcs(ntc_data,YEAR,'JRC')

outages = ds.create_outages(allunits, generation, capacity_factors, SOURCE, scenario, YEAR)

ds.create_renewables(countries, solar_AF, wind_AF, hydro_dam_data, EFFICIENCY, path, YEAR_InFlow, generation, capacity_factors)
