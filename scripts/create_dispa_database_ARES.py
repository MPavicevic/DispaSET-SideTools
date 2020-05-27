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
TEMBA = True
scenario = 'Reference'  # Reference, 1.5deg, 2.0deg

# Source for demand projections
SOURCE = 'TEMBA'

# Local files
# Typical units
typical_units = pd.read_csv(input_folder + source_folder + 'Typical_Units_ARES.csv')
# Typical cooling
typical_cooling = pd.read_csv(input_folder + source_folder + 'Typical_Cooling.csv')
# Historical power plants
pp_data = pd.read_excel(input_folder + source_folder + 'Power plants Africa.xlsx', int=0, header=1)
# Historic hydro units
data_hydro = pd.read_excel(input_folder + source_folder + 'African_hydro_dams.xlsx', int=0, header=0)
# TEMBA Projections
temba_inputs = pd.read_csv(input_folder + source_folder + 'TEMBA_Results.csv', header=0, index_col=0)

# Countries used in the analysis
countries_EAPP = ['Burundi', 'Djibouti', 'Egypt', 'Ethiopia', 'Eritrea', 'Kenya', 'Rwanda', 'Somalia', 'Sudan',
                  'South Sudan', 'Tanzania', 'Uganda']
countries_NAPP = ['Algeria', 'Libya', 'Morocco', 'Mauritania', 'Tunisia']
countries_CAPP = ['Angola', 'Cameroon', 'Central African Republic', 'Republic of the Congo', 'Chad', 'Gabon',
                  'Equatorial Guinea', 'Democratic Republic of the Congo']

used = set()
countries = countries_EAPP + countries_CAPP + countries_NAPP
countries = [x for x in countries if x not in used and (used.add(x) or True)]
countries = ds.get_country_codes(countries)

allunits = ds.get_allunits(
    ds.get_temba_plants(temba_inputs,
                        ds.assign_typical_units(ds.powerplant_data_preprocessing(pp_data),
                                                typical_units,
                                                typical_cooling),
                        ds.get_hydro_units(data_hydro, EFFICIENCY),
                        typical_units,
                        typical_cooling,
                        YEAR,
                        TEMBA=TEMBA,
                        scenario=scenario),
    countries)

if SOURCE == 'TEMBA':
    ds.write_csv_files(allunits, 'ARES_APP', SOURCE + '_' + scenario, 'PowerPlants', str(YEAR), WRITE_CSV, 'Zonal')
    with open(input_folder + source_folder + 'TEMBA_capacities_' + scenario + '_' + str(YEAR) + '.p', 'wb') as handle:
        pickle.dump(allunits, handle, protocol=pickle.HIGHEST_PROTOCOL)
    # with open(input_folder + source_folder + 'Units_from_get_Capacities.p', 'rb') as handle:
    #     allunits = pickle.load(handle)
else:
    ds.write_csv_files(allunits, 'ARES_APP', SOURCE, 'PowerPlants', str(YEAR), WRITE_CSV, 'Zonal')


tmp = {}
aa = ds.get_temba_plants(temba_inputs,
                        ds.assign_typical_units(ds.powerplant_data_preprocessing(pp_data),
                                                typical_units,
                                                typical_cooling),
                        ds.get_hydro_units(data_hydro, EFFICIENCY),
                        typical_units,
                        typical_cooling,
                        YEAR,
                        TEMBA=TEMBA,
                        scenario=scenario)
tmp = {}
for p in ['NAPP', 'EAPP', 'CAPP']:
    if p == 'NAPP':
        zones = ds.get_country_codes(countries_NAPP)
    elif p == 'CAPP':
        zones = ds.get_country_codes(countries_CAPP)
    else:
        zones = ds.get_country_codes(countries_EAPP)
    bb = {}
    for fuel in aa['Fuel'].unique():
        bb[fuel] = aa.loc[(aa['Zone'].isin(zones)) & (aa['Fuel'] == fuel)]['PowerCapacity'].sum()
    tmp[p] = bb

bb = pd.DataFrame.from_dict(tmp)

bb.to_csv('Ares_capacites' + str(YEAR) + '.csv')