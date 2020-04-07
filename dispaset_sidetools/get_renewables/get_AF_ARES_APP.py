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
import pycountry
import glob
import matplotlib.pyplot as plt
from eto import ETo, datasets
import math
import enlopy as el

# Local source tree imports
from dispaset_sidetools.common import date_range, get_country_codes, write_csv_files, commons, get_ktoe_to_mwh, make_dir
from dispaset_sidetools.get_capacities.get_Capacities_ARES_APP import get_hydro_units

sys.path.append(os.path.abspath(r'../..'))

# %% Inputs
# Folder destinations
input_folder = commons['InputFolder']
source_folder = 'ARES_Africa/'
output_folder = commons['OutputFolder']

input_file_Wind_AF = 'Wind_OnShore_AF.csv'
input_file_Solar_AF = 'Solar_PV_AF.csv'
input_file_dams = 'African_hydro_dams.xlsx'
input_file_inflows = 'AfricaDamsInFlows'
input_file_generation = 'Annual_Generation_Statistics.xlsx'
input_file_CF = 'CF_IRENA.csv'

# Other options
STO_HOURS = 5
EFFICIENCY = 0.8
YEAR_InFlow = 2015
YEAR_Generation = 2015
SOURCE = 'JRC'
SOURCE_Hydro = 'LISFLOOD'
WRITE_CSV = True

# %% Read input data from csv/xlsx files
# Solar and Wind data from csv files
solar_AF = pd.read_csv(input_folder + source_folder + input_file_Solar_AF)
wind_AF = pd.read_csv(input_folder + source_folder + input_file_Wind_AF)
# Hydro dam data and InfLows from xlsx and csv
hydro_dam_data = pd.read_excel(input_folder + source_folder + input_file_dams, int=0, header=0)
path = input_folder + source_folder + input_file_inflows  # use your path
all_files = glob.glob(path + "/*.csv")
# Annual generation per fuel type
generation = pd.read_excel(input_folder + source_folder + input_file_generation, sheet_name=0, index_col=0)
generation.fillna(0, inplace=True)
# IRENA Capacity factors for wind and PV
capacity_factors = pd.read_csv(input_folder + source_folder + input_file_CF,index_col=0, header=0)

# Select active zones
countries_EAPP = ['Burundi', 'Djibouti', 'Egypt', 'Ethiopia', 'Eritrea', 'Kenya', 'Rwanda', 'Somalia', 'Sudan',
                  'South Sudan', 'Tanzania', 'Uganda']
countries_NAPP = ['Algeria', 'Libya', 'Morocco', 'Mauritania', 'Tunisia']
countries_CAPP = ['Angola', 'Cameroon', 'Central African Republic', 'Republic of the Congo', 'Chad', 'Gabon',
                  'Equatorial Guinea', 'Democratic Republic of the Congo']

# %% Data processing
# Get ISO_2 country codes
codes = get_country_codes(list(solar_AF.columns))
codes_CEN = get_country_codes(countries_EAPP + countries_CAPP + countries_NAPP)
# Assign proper index and column names
solar_AF.rename(columns=dict(zip(solar_AF.columns, codes)), inplace=True)
wind_AF.rename(columns=dict(zip(wind_AF.columns, codes)), inplace=True)
solar_AF.drop(columns=['Unknown code'], inplace=True)
wind_AF.drop(columns=['Unknown code'], inplace=True)
solar_AF.set_index(date_range('1/1/2005', '1/1/2017', freq='H'), inplace=True)
wind_AF.set_index(date_range('1/1/2005', '1/1/2017', freq='H'), inplace=True)

# Filter wind and solar for selected zones
wind_AF = wind_AF[codes_CEN]
solar_AF = solar_AF[codes_CEN]

# Get hydro units in dispa-set format
hydro_units = get_hydro_units(hydro_dam_data)

# unit_names = list(hydro_units['Unit'])
unit_hdam = list(hydro_units['Zone'].loc[hydro_units['Technology'] == 'HDAM'].unique())
unit_hror = list(hydro_units['Zone'].loc[hydro_units['Technology'] == 'HROR'].unique())

# Read river inflows and adjust (upscale) to hourly values
river_in_flows = pd.DataFrame()
for filename in all_files:
    tmp = pd.read_csv(filename, index_col=0, header=0, parse_dates=[0])
    river_in_flows = pd.concat([river_in_flows, tmp], axis=1)
river_in_flows.columns = list(hydro_units['Unit'])
river_in_flows = river_in_flows.resample('H').interpolate(method='linear')

# Analyze inflows for specific year
start_date = str(YEAR_InFlow) + '-1-1'
end_date = str(YEAR_InFlow) + '-12-31'
tmp_flow = pd.DataFrame(river_in_flows.loc[start_date:end_date])

# Gather unit specific data for further analysis
data = pd.DataFrame(hydro_dam_data['Dam height (m)']).fillna(1)
data['PowerCapacity'] = hydro_units['PowerCapacity']
data['Zone'] = hydro_dam_data['Country Code']
data['Technology'] = hydro_units['Technology']
data['Area'] = hydro_dam_data['Reservoir area (km2)']
data['Area'] = data['Area'].fillna(0)
data['FlowMax'] = data['PowerCapacity'] * 1e6 / 9.81 / 1000 / data['Dam height (m)'] / 0.8
data['FlowMin'] = data['FlowMax'] * 0.1
data.index = list(hydro_units['Unit'])

# Annual generation in MWh
generation = get_ktoe_to_mwh(generation, ['Biofuels', 'Fosil', 'Hydro', 'Geothermal', 'RES'])

# Identify annual generation per zone and share of installed capacity
for c in list(data['Zone'].unique()):
    if c in list(generation.index):
        data.loc[data['Zone'] == c, 'Share'] = data['PowerCapacity'].loc[data['Zone'] == c] / \
                                               data['PowerCapacity'].loc[data['Zone'] == c].sum()
        data.loc[data['Zone'] == c, 'Generation_Historic'] = generation['Hydro'][c]
    else:
        data.loc[data['Zone'] == c, 'Generation_Historic'] = 0
# Assign annual generation for each individual unit based on shares
data['Generation_Historic'] = data['Generation_Historic'] * data['Share']
# Compute annual generation for proposed inflows
data['Generation_From_Flows'] = tmp_flow.sum() * 9.81 / 1e6 * 1000 * data['Dam height (m)'] * 0.8
# Identify capacity factors
data['CF'] = data['Generation_Historic'] / data['PowerCapacity'] / 8760

# Initial Inflow adjustment for all units
data['Correction'] = (data['Generation_Historic'] - data['Generation_From_Flows']) / data['Generation_From_Flows']
# Assign AF for HDAM's
af_hdam = tmp_flow.loc[:, data['Technology'] == 'HDAM'] * 9.81 / 1e6 * 1000 * \
          data['Dam height (m)'].loc[data['Technology'] == 'HDAM'] * \
          (1 + data['Correction'].loc[data['Technology'] == 'HDAM']) / \
          data['PowerCapacity'].loc[data['Technology'] == 'HDAM']


# Helper functions
def get_hror_cf(data, CF, generation):
    """
    Iterative method for adjusting the annual generation based on flows
    :param data:    Unit specific input data (Generation and Technology)
    :param CF:      Initial correction factor
    :param generation:    pd.DataFrame
    :returns:       Updated capacity factor and new flows
    """
    tmp_flow_HROR = generation * (1 + CF)
    spill_HROR = tmp_flow_HROR - data['PowerCapacity'].loc[data['Technology'] == 'HROR']
    spill_HROR[spill_HROR < 0] = 0
    flow_HROR = tmp_flow_HROR - spill_HROR
    flow_HROR.fillna(4, inplace=True)
    CF = (data['Generation_Historic'].loc[data['Technology'] == 'HROR'] - flow_HROR.sum()) / flow_HROR.sum()
    CF.fillna(0, inplace=True)
    return CF, flow_HROR, tmp_flow_HROR


def get_res_cf(availability, CF, total):
    """
    Iterative method for adjusting annual generation based on RES
    :param generation:  RES timeseries
    :param CF:          Correction factor
    :param total:       Total generation with new CF
    :return:            Updated availability timeseries
    """
    tmp_res = availability * (1 + CF)
    spill_res = tmp_res - 1
    spill_res[spill_res < 0] = 0
    res = tmp_res - spill_res
    CF = (total - res.sum()) / res.sum()
    CF.fillna(0,inplace=True)
    return CF, res, tmp_res

# Initial correction factors for wind and sun
cor_res = pd.DataFrame(index = list(wind_AF.columns))
cor_res['Wind'],cor_res['PV'] = 0.5, 0.5
# Iterations
for i in range(100):
    tmp_win = get_res_cf(wind_AF,cor_res['Wind'],capacity_factors['CF_Wind']*wind_AF.count(axis=0))
    tmp_sun = get_res_cf(solar_AF, cor_res['PV'], capacity_factors['CF_PV'] * solar_AF.count(axis=0))
    cor_res['Wind'] = tmp_win[0]
    cor_res['PV'] = tmp_sun[0]
    wind_AF = tmp_win[1]
    solar_AF = tmp_sun[1]
    if i % 10 == 0:
        logging.info('iteration #' + str(i) + ' max correction for wind: ' + str(tmp_win[0].max()))
        logging.info('iteration #' + str(i) + ' max correction for solar PV: ' + str(tmp_sun[0].max()))

# Get generation for HROR units
generation = tmp_flow.loc[:, data['Technology'] == 'HROR'] * 9.81 / 1e6 * 1000 * \
             data['Dam height (m)'].loc[data['Technology'] == 'HROR'] * 0.8

# Initial inflow adjustment for HROR units
correction_factor = data['Correction'].loc[data['Technology'] == 'HROR']
# Iterations
for i in range(100):
    tmp_data = get_hror_cf(data, correction_factor, generation)
    correction_factor = tmp_data[0]
    generation = tmp_data[1]
    if i % 10 == 0:
        logging.info('iteration #' + str(i) + ' max correction: ' + str(tmp_data[0].max()))

# New AF for HROR units
af_hror = tmp_data[1] / data['PowerCapacity'].loc[data['Technology'] == 'HROR']
# Merger of HDAM and HROR AF/Scaled InFlows
tmp_af = pd.concat([af_hdam, af_hror], axis=1, sort=False)

hdam_timeseries = {}
res_timeseries = {}

# Predefined all 0 DataFrame. Used to fill missing AF and Hydro data
zero_df = pd.DataFrame(index=solar_AF.index, columns=['HROR', 'PHOT', 'WTON', 'WTOF', 'HDAM']).fillna(0)

for region in codes_CEN:
    # Solar PV
    if region in solar_AF:
        tmp_PV = pd.DataFrame(solar_AF[region].loc[start_date:end_date])
        tmp_PV.rename(columns={region: 'PHOT'}, inplace=True)
        logging.info(region + ' PHOT timseries created from PHOT dataset')
    else:
        logging.warning(region + ' PHOT timeseries doesnt exist')
        tmp_PV = pd.DataFrame(zero_df['PHOT'].loc[start_date:end_date])
    # Wind onshore
    if region in wind_AF:
        tmp_WTON = pd.DataFrame(wind_AF[region].loc[start_date:end_date])
        tmp_WTON.rename(columns={region: 'WTON'}, inplace=True)
        logging.info(region + ' WTON timseries created from WTON dataset')
    else:
        logging.warning(region + ' WTON timeseries doesnt exist')
        tmp_WTON = pd.DataFrame(zero_df['WTON'].loc[start_date:end_date])
    # Wind offshore
    if region in wind_AF:
        tmp_WTOF = pd.DataFrame(wind_AF[region].loc[start_date:end_date])
        tmp_WTOF.rename(columns={region: 'WTOF'}, inplace=True)
        logging.info(region + ' WTOF timseries created from WTON dataset')
    else:
        logging.warning(region + ' WTOF timeseries doesnt exist')
        tmp_WTOF = pd.DataFrame(zero_df['WTOF'].loc[start_date:end_date])
    # Hydro run-of-river
    tmp_HROR = zero_df
    if region in unit_hror:
        tmp_HROR = tmp_af.loc[:, list(hydro_units['Unit'].loc[(hydro_units['Zone'] == region) &
                                                              (hydro_units['Technology'] == 'HROR')])]
    else:
        logging.warning(region + ' there is no HROR timeseries present in the availability factors')
        tmp_HROR = pd.DataFrame(zero_df['HROR'].loc[start_date:end_date])
    # Hydro dam
    tmp_HDAM = zero_df
    if region in unit_hdam:
        tmp_HDAM = tmp_af.loc[:, list(hydro_units['Unit'].loc[(hydro_units['Zone'] == region) &
                                                              (hydro_units['Technology'] == 'HDAM')])]
    else:
        logging.warning(region + ' there is no HDAM timeseries present in the availability factors')
        tmp_HDAM = pd.DataFrame(zero_df['HDAM'].loc[start_date:end_date])

    # Combine it all together
    tmp_res_timeseries = [tmp_WTON, tmp_WTOF, tmp_PV, tmp_HROR]
    res_timeseries[region] = pd.concat(tmp_res_timeseries, axis=1)
    # Separate HDAM's
    hdam_timeseries[region] = tmp_HDAM.copy()

write_csv_files(res_timeseries, 'ARES_APP', SOURCE, 'AvailabilityFactors', str(YEAR_InFlow), WRITE_CSV, 'Zonal')


def write_csv_hydro(file_name_IF=None, inflow_timeseries=None, write_csv=None):
    """
    Specific function for hydro inflows
    :param file_name_IF:
    :param inflow_timeseries:
    :param write_csv:
    :return:
    """
    if write_csv is True:
        if isinstance(inflow_timeseries, dict):
            filename_IF = file_name_IF + '.csv'
            for c in inflow_timeseries:
                make_dir('../../Outputs/')
                make_dir('../../Outputs/' + 'ARES_APP')
                make_dir('../../Outputs/' + 'ARES_APP' + '/Database/')
                make_dir('../../Outputs/' + 'ARES_APP' + '/Database/' + 'HydroData/')
                folder_1 = '../../Outputs/' + 'ARES_APP' + '/Database/' + 'HydroData/' + 'ScaledInflows/'
                make_dir(folder_1)
                make_dir(folder_1 + c)
                inflow_timeseries[c].to_csv(folder_1 + c + '/' + filename_IF)
                logging.info('ScaledInFlows' + ' database was created for zone: ' + c + '.')
    else:
        logging.warning('[WARNING ]: ' + 'WRITE_CSV_FILES = False, unable to write .csv files')


write_csv_hydro('IF_' + SOURCE_Hydro + '_' + str(YEAR_InFlow), hdam_timeseries, WRITE_CSV)

el.plot_percentiles(river_in_flows['Erraguene'], x='dayofyear', zz='year', color='green')
plt.show()
