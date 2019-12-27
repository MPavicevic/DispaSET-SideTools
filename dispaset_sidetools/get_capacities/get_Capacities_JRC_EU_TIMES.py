# -*- coding: utf-8 -*-
"""
This script generates the PowerPlant Dispa-SET data for the JRC-EU-TIMES run

@authors: Matija Pavičević, KU Leuven
          Sylvain Quoilin, KU Leuven
"""
# System imports
from __future__ import division

import pickle
import sys

import numpy as np
import pandas as pd

# Third-party imports
# Local source tree imports
# from .common import mapping,outliers_vre,fix_na,make_dir,entsoe_types,commons
from dispaset_sidetools.common import make_dir

# %% Adjustable inputs that should be modified
YEAR = 2050  # considered year
WRITE_CSV_FILES = False  # Write csv database
TECHNOLOGY_THRESHOLD = 0  # threshold (%) below which a technology is considered negligible and no unit is created
TES_CAPACITY = 24  # No of storage hours in TES
CSP_TES_CAPACITY = 7.5  # No of storage hours in CSP units (usually 7.5 hours)
CHP_TYPE = 'back-pressure'  # Define CHP type: None, back-pressure or Extraction
BIOGAS = 'GAS'  # Define what biogas fuel equals to (BIO or GAS)
OCEAN = 'WAT'  # Define what ocean fuel equals to (WAT or OTH)
CCS = False  # Turn Carbon capture and sotrage on/off
CSP = False
HYDRO_CLUSTERING = 'OFF' # Define type of hydro clustering (OFF, HPHS, HROR)

input_folder = '../../Inputs/'  # Standard input folder
output_folder = '../../Outputs/'  # Standard output folder
# %% Inputs
# Load typical units
'''Get typical units:'''


def get_typical_units(typical_units, chp_type=None):
    """
    Function that:
        - loads typical units from the Inputs/Typical_Units.csv file
        - assigns CHP units based on type: Extraction, back-pressure or None (no CHP units)
    """
    if CCS is False:
        indexNames = typical_units[typical_units['Year'] == 2050].index
        typical_units.drop(indexNames, inplace=True)

    if chp_type == 'Extraction':
        typical_units = typical_units.copy()
    elif chp_type == 'back-pressure':
        typical_units = typical_units.copy()
        typical_units['CHPPowerLossFactor'].values[typical_units['CHPPowerLossFactor'] > 0] = 0
        typical_units['CHPType'].replace(to_replace='Extraction', value='back-pressure', inplace=True)
    elif chp_type is None:
        typical_units = typical_units.copy()
        typical_units['CHPType'], typical_units['CHPPowerLossFactor'], typical_units[
            'CHPPowerToHeat'] = np.nan, np.nan, np.nan
    else:
        print('[CRITICAL ]: chp_type is of wrong string (should be set to None, Extraction or back-pressure)')
    return typical_units


typical = get_typical_units(typical_units=pd.read_csv(input_folder + 'Typical_Units.csv'))
typical_chp = get_typical_units(typical_units=pd.read_csv(input_folder + 'Typical_Units.csv'), chp_type=CHP_TYPE)

#
'''Get capacities:'''
fuel_types = ['BIO', 'GAS', 'GEO', 'HRD', 'HYD', 'LIG', 'NUC', 'OIL', 'PEA', 'SUN', 'WAT', 'WIN', 'WST']
capacities = pd.read_csv(input_folder + 'TIMES_Capacities_fuel_2050.csv', index_col=0)
capacities[BIOGAS] = capacities[BIOGAS] + capacities['Biogas']
capacities.drop(columns=['Biogas'], inplace=True)
capacities[OCEAN] = capacities[OCEAN] + capacities['Ocean']
capacities.drop(columns=['Ocean'], inplace=True)
capacities = pd.DataFrame(capacities, columns=fuel_types).fillna(0)


# if capacities.where(capacities < 0).count() > 0:
#     print('There are ' + capacities.where(capacities < 0).count() + ' is negative')


# TODO
def get_typical_capacities(capacities, year=None):
    typical_capacities = capacities.copy()
    return typical_capacities


# %% Load reservoir capacities from entso-e (maximum value of the provided time series)
# TODO
def get_reservoir_capacities():
    reservoirs = pd.read_csv(input_folder + 'Hydro_Reservoirs.csv', index_col=0, header=None)
    reservoirs = reservoirs[1]
    return reservoirs


reservoirs = get_reservoir_capacities()

# %% BATS and BEVS data
countries = list(capacities.index)
batteries = pd.read_excel(input_folder + 'TIMES_EV_Capacities.xlsx', index_col=0)
bevs_cap = pd.DataFrame()
bevs_cap['BEVS'] = batteries[str(YEAR)] * 1000

# %% CHP Data
chp_fuel_types = ['BIO_COMC', 'BIO_STUR', 'BIO_GTUR', 'BIO_ICEN',
                  'GAS_COMC', 'GAS_STUR', 'GAS_GTUR', 'GAS_ICEN',
                  'Biogas_COMC', 'Biogas_STUR', 'Biogas_GTUR', 'Biogas_ICEN',
                  'HRD_COMC', 'HRD_STUR', 'HRD_GTUR', 'HRD_ICEN',
                  'LIG_COMC', 'LIG_STUR', 'LIG_GTUR', 'LIG_ICEN',
                  'OIL_COMC', 'OIL_STUR', 'OIL_GTUR', 'OIL_ICEN']
chp_capacities = pd.read_csv(input_folder + 'TIMES_CHP_Capacities_2050.csv', index_col=0)
chp_capacities = pd.DataFrame(chp_capacities, columns=chp_fuel_types).fillna(0)
chp_bio = pd.DataFrame([chp_capacities['BIO_COMC'], chp_capacities['BIO_STUR'],
                        chp_capacities['BIO_ICEN'], chp_capacities['BIO_GTUR']]).T
chp_bio.columns = chp_bio.columns.str[4:]
chp_gas = pd.DataFrame([chp_capacities['GAS_COMC'], chp_capacities['GAS_STUR'],
                        chp_capacities['GAS_ICEN'], chp_capacities['GAS_GTUR']]).T
chp_gas.columns = chp_gas.columns.str[4:]
chp_hrd = pd.DataFrame([chp_capacities['HRD_COMC'], chp_capacities['HRD_STUR'],
                        chp_capacities['HRD_ICEN'], chp_capacities['HRD_GTUR']]).T
chp_hrd.columns = chp_hrd.columns.str[4:]
chp_lig = pd.DataFrame([chp_capacities['LIG_COMC'], chp_capacities['LIG_STUR'],
                        chp_capacities['LIG_ICEN'], chp_capacities['LIG_GTUR']]).T
chp_lig.columns = chp_lig.columns.str[4:]
chp_oil = pd.DataFrame([chp_capacities['OIL_COMC'], chp_capacities['OIL_STUR'],
                        chp_capacities['OIL_ICEN'], chp_capacities['OIL_GTUR']]).T
chp_oil.columns = chp_oil.columns.str[4:]
if BIOGAS == 'GAS':
    chp_gas['ICEN'] = chp_gas['ICEN'] + chp_capacities['Biogas_ICEN']
    chp_gas['COMC'] = chp_gas['COMC'] + chp_capacities['Biogas_COMC']
    chp_gas['GTUR'] = chp_gas['GTUR'] + chp_capacities['Biogas_GTUR']
    chp_gas['STUR'] = chp_gas['STUR'] + chp_capacities['Biogas_STUR']
elif BIOGAS == 'BIO':
    chp_bio['ICEN'] = chp_bio['ICEN'] + chp_capacities['Biogas_ICEN']
    chp_bio['COMC'] = chp_bio['COMC'] + chp_capacities['Biogas_COMC']
    chp_bio['GTUR'] = chp_bio['GTUR'] + chp_capacities['Biogas_GTUR']
    chp_bio['STUR'] = chp_bio['STUR'] + chp_capacities['Biogas_STUR']

# TODO
data_CHP_heat_capacity = pd.read_csv(input_folder + 'Heat_Capacities.csv', index_col=0)

# %% Generate capacities for each country
no_countries = len(countries)
# TODO


# %% Generate Typical_tech dataframes
typical_tech_input = pd.read_csv(input_folder + 'TIMES_Capacities_technology_2050.csv', index_col=0)
if CCS is False:
    typical_tech_input['GAS_COMC'] = typical_tech_input['GAS_COMC'] + typical_tech_input['GAS_COMC_CCS']
    typical_tech_input['BIO_COMC'] = typical_tech_input['BIO_COMC'] + typical_tech_input['BIO_COMC_CCS']
    typical_tech_input['BIO_STUR'] = typical_tech_input['BIO_STUR'] + typical_tech_input['BIO_STUR_CCS']
    typical_tech_input['HRD_COMC'] = typical_tech_input['HRD_COMC'] + typical_tech_input['HRD_COMC_CCS']
    typical_tech_input.drop(columns=['BIO_COMC_CCS', 'BIO_STUR_CCS', 'GAS_COMC_CCS', 'HRD_COMC_CCS'], inplace=True)

if BIOGAS == 'GAS':
    typical_tech_input['GAS_ICEN'] = typical_tech_input['GAS_ICEN'] + typical_tech_input['Biogas_ICEN']
    typical_tech_input.drop(columns=['Biogas_ICEN'], inplace=True)
elif BIOGAS == 'BIO':
    typical_tech_input['BIO_ICEN'] = typical_tech_input['BIO_ICEN'] + typical_tech_input['Biogas_ICEN']
    typical_tech_input.drop(columns=['Biogas_ICEN'], inplace=True)

if OCEAN == 'WAT':
    typical_tech_input['WAT_HROR'] = typical_tech_input['WAT_HROR'] + typical_tech_input['Ocean_TIDAL']
    typical_tech_input['WAT_HROR'] = typical_tech_input['WAT_HROR'] + typical_tech_input['Ocean_WAVE']
    typical_tech_input.drop(columns=['Ocean_WAVE', 'Ocean_TIDAL'], inplace=True)

if CSP is False:
    typical_tech_input['SUN_PHOT'] = typical_tech_input['SUN_PHOT'] + typical_tech_input['SUN_STUR']
    typical_tech_input['SUN_STUR'] = 0
    typical_tech_sun = pd.DataFrame([typical_tech_input['SUN_PHOT'], typical_tech_input['SUN_STUR']],
                                    index=['PHOT', 'STUR']).T
else:
    typical_tech_sun = pd.DataFrame([typical_tech_input['SUN_PHOT'], typical_tech_input['SUN_STUR']],
                                    index=['PHOT', 'STUR']).T

typical_tech_gas = pd.DataFrame([typical_tech_input['GAS_COMC'], typical_tech_input['GAS_GTUR'],
                                 typical_tech_input['GAS_ICEN'], typical_tech_input['GAS_STUR']],
                                index=['COMC', 'GTUR', 'ICEN', 'STUR']).T
typical_tech_bio = pd.DataFrame([typical_tech_input['BIO_COMC'], typical_tech_input['BIO_GTUR'],
                                 typical_tech_input['BIO_ICEN'], typical_tech_input['BIO_STUR']],
                                index=['COMC', 'GTUR', 'ICEN', 'STUR']).T
typical_tech_hrd = pd.DataFrame([typical_tech_input['HRD_COMC'], typical_tech_input['HRD_STUR']],
                                index=['COMC', 'STUR']).T
typical_tech_oil = pd.DataFrame([typical_tech_input['OIL_COMC'], typical_tech_input['BIO_GTUR'],
                                 typical_tech_input['OIL_STUR']], index=['COMC', 'GTUR', 'STUR']).T

typical_tech_input.drop(columns=['GAS_Autoproducers', 'OIL_Autoproducers'], inplace=True)
technology_types = ['HDAM', 'HROR', 'HPHS', 'PHOT', 'WTOF', 'WTON', 'CAES', 'BATS', 'BEVS', 'THMS']
typical_tech = pd.DataFrame([typical_tech_input['WAT_HDAM'], typical_tech_input['WAT_HPHS'],
                             typical_tech_input['WAT_HROR'],
                             typical_tech_input['WIN_WTOF'], typical_tech_input['WIN_WTON']]).T
typical_tech.columns = typical_tech.columns.str[4:]
typical_tech = typical_tech.assign(CAES=1, BATS=1, BEVS=1, THMS=1)

typical_stur = pd.DataFrame(np.ones(no_countries), index=countries, columns=['STUR'])

## %% Generate Typical_FUEL dataframes
# %% WIND
typical_win = pd.DataFrame([typical_tech['WTON'], typical_tech['WTOF']]).T
typical_win['sum'] = typical_win.sum(axis=1)
typical_win = (typical_win.loc[:, 'WTON':'WTOF'].div(typical_win['sum'], axis=0))
typical_win['WTON'].fillna(1, inplace=True)
typical_win.fillna(0, inplace=True)

# %% GAS
typical_gas = pd.DataFrame([typical_tech_gas['COMC'], typical_tech_gas['GTUR'],
                            typical_tech_gas['ICEN'], typical_tech_gas['STUR']]).T
typical_gas['sum'] = typical_gas.sum(axis=1)
typical_gas = (typical_gas.loc[:, 'COMC':'STUR'].div(typical_gas['sum'], axis=0))
typical_gas['COMC'].fillna(1, inplace=True)
typical_gas.fillna(0, inplace=True)

# %% BIO
typical_bio = pd.DataFrame([typical_tech_bio['COMC'], typical_tech_bio['GTUR'],
                            typical_tech_bio['ICEN'], typical_tech_bio['STUR']]).T
typical_bio['sum'] = typical_bio.sum(axis=1)
typical_bio = (typical_bio.loc[:, 'COMC':'STUR'].div(typical_bio['sum'], axis=0))
typical_bio['STUR'].fillna(1, inplace=True)
typical_bio.fillna(0, inplace=True)

# %% HRD
typical_hrd = pd.DataFrame([typical_tech_hrd['COMC'], typical_tech_hrd['STUR']]).T
typical_hrd['sum'] = typical_hrd.sum(axis=1)
typical_hrd = (typical_hrd.loc[:, 'COMC':'STUR'].div(typical_hrd['sum'], axis=0))
typical_hrd['STUR'].fillna(1, inplace=True)
typical_hrd.fillna(0, inplace=True)

# %% HRD
typical_oil = pd.DataFrame([typical_tech_oil['COMC'], typical_tech_oil['GTUR'], typical_tech_oil['STUR']]).T
typical_oil['sum'] = typical_oil.sum(axis=1)
typical_oil = (typical_oil.loc[:, 'COMC':'STUR'].div(typical_oil['sum'], axis=0))
typical_oil['STUR'].fillna(1, inplace=True)
typical_oil.fillna(0, inplace=True)

# %% SUN
typical_sun = pd.DataFrame([typical_tech_sun['PHOT'], typical_tech_sun['STUR']]).T
typical_sun['sum'] = typical_sun.sum(axis=1)
typical_sun = (typical_sun.loc[:, 'PHOT':'STUR'].div(typical_sun['sum'], axis=0))
typical_sun['PHOT'].fillna(1, inplace=True)
typical_sun.fillna(0, inplace=True)


# %% HYDRO
# TODO
# Make a function with three statements, hydro can either HROR only, HDAM+HPHS, or each technology individually
def get_typical_hydro(typical_hydro, clustering=None):
    """
    Function that loads typical hydro units from the typical_tech and assigns one of several clustering options:
        - HROR only
        - HROR & HPHS (HPHS + HDAM)
        - HROR, HPHS & HDAM individually
    """
    if clustering == 'HPHS':
        typical_wat = typical_hydro.copy()
        typical_wat['cluster'], typical_wat['sum'] = typical_wat['HDAM'] + typical_wat['HPHS'], typical_wat.sum(
            axis=1)
        typical_wat.drop(['HDAM', 'HPHS'], axis=1, inplace=True)
        typical_wat = (typical_wat.loc[:, 'HROR':'cluster'].div(typical_wat['sum'], axis=0))
        typical_wat = typical_wat[typical_wat.replace([np.inf, -np.inf], np.nan).notnull().all(axis=1)].fillna(0)
        typical_wat.rename(columns={'cluster': 'HPHS'}, inplace=True)
    elif clustering == 'HROR':
        typical_wat = typical_hydro.copy()
        typical_wat['HROR'] = typical_wat['HDAM'] + typical_wat['HPHS'] + typical_wat['HROR']
        typical_wat.drop(['HDAM', 'HPHS'], axis=1, inplace=True)
        typical_wat.fillna(0,inplace=True)
    elif clustering == 'OFF':
        typical_wat = typical_hydro.copy()
        typical_wat['sum'] = typical_wat.sum(axis=1)
        typical_wat = (typical_wat.loc[:, 'HDAM':'HPHS'].div(typical_wat['sum'], axis=0))
        typical_wat = typical_wat[typical_wat.replace([np.inf, -np.inf], np.nan).notnull().all(axis=1)].fillna(0)
    return typical_wat


typical_wat = get_typical_hydro(typical_hydro=pd.DataFrame([typical_tech['HDAM'], typical_tech['HROR'],
                                                            typical_tech['HPHS']]).T, clustering=HYDRO_CLUSTERING)

# %% SOLAR
# typical_sun = pd.DataFrame(typical_tech['PHOT'])


# %% CHP and NON-CHP total power capacities
fuels = ['BIO', 'GAS', 'HRD', 'LIG', 'PEA', 'WST', 'OIL', 'GEO']
chp_power_capacities = pd.DataFrame(columns=fuels)
chp_power_capacities['GAS'] = chp_gas.sum(axis=1)
chp_power_capacities['BIO'] = chp_bio.sum(axis=1)
chp_power_capacities['HRD'] = chp_hrd.sum(axis=1)
chp_power_capacities['LIG'] = chp_lig.sum(axis=1)
chp_power_capacities['OIL'] = chp_oil.sum(axis=1)
chp_power_capacities.fillna(0, inplace=True)
no_chp_capacities = capacities.sub(chp_power_capacities, fill_value=0)
no_chp_capacities.fillna(0, inplace=True)
no_chp_capacities = no_chp_capacities.transpose()
chp_power_capacities = chp_power_capacities.T

# %% Non CHP units
cap = {}
cap_chp = {}
for c in countries:
    tmp_cap = pd.DataFrame(no_chp_capacities[c]).transpose()
    tmp_SUN = pd.DataFrame(typical_sun.loc[c]) * tmp_cap['SUN']
    tmp_SUN.rename(columns={c: 'SUN'}, inplace=True)
    tmp_WAT = pd.DataFrame(typical_wat.loc[c]) * tmp_cap['WAT']
    tmp_WAT.rename(columns={c: 'WAT'}, inplace=True)
    tmp_WIN = pd.DataFrame(typical_win.loc[c]) * tmp_cap['WIN']
    tmp_WIN.rename(columns={c: 'WIN'}, inplace=True)
    tmp_GAS = pd.DataFrame(typical_gas.loc[c]) * tmp_cap['GAS']
    tmp_GAS.rename(columns={c: 'GAS'}, inplace=True)
    tmp_BIO = pd.DataFrame(typical_bio.loc[c]) * tmp_cap['BIO']
    tmp_BIO.rename(columns={c: 'BIO'}, inplace=True)
    tmp_HRD = pd.DataFrame(typical_hrd.loc[c]) * tmp_cap['HRD']
    tmp_HRD.rename(columns={c: 'HRD'}, inplace=True)
    tmp_OIL = pd.DataFrame(typical_oil.loc[c]) * tmp_cap['OIL']
    tmp_OIL.rename(columns={c: 'OIL'}, inplace=True)
    tmp_BEV = pd.DataFrame(bevs_cap.loc[c])
    tmp_BEV.rename(columns={c: 'OTH'}, inplace=True)
    tmp_other = pd.DataFrame([tmp_cap['GEO'], tmp_cap['LIG'], tmp_cap['NUC'], tmp_cap['PEA'], tmp_cap['WST']]).T
    tmp_other.rename(index={c: 'STUR'}, inplace=True)
    df_merged = tmp_other.merge(tmp_GAS, how='outer', left_index=True, right_index=True)
    df_merged = df_merged.merge(tmp_BIO, how='outer', left_index=True, right_index=True)
    df_merged = df_merged.merge(tmp_HRD, how='outer', left_index=True, right_index=True)
    df_merged = df_merged.merge(tmp_OIL, how='outer', left_index=True, right_index=True)
    df_merged = df_merged.merge(tmp_WAT, how='outer', left_index=True, right_index=True)
    df_merged = df_merged.merge(tmp_WIN, how='outer', left_index=True, right_index=True)
    df_merged = df_merged.merge(tmp_SUN, how='outer', left_index=True, right_index=True)
    total_cap = df_merged.sum().sum()
    min_cap = total_cap * TECHNOLOGY_THRESHOLD
    df_merged[df_merged < min_cap] = 0
    df_merged = df_merged.merge(tmp_BEV, how='outer', left_index=True, right_index=True)
    cap[c] = df_merged
    cap[c].fillna(0, inplace=True)
    # CHP
    tmp_cap_chp = pd.DataFrame(chp_power_capacities[c]).transpose()
    tmp_GAS_chp = pd.DataFrame(typical_gas.loc[c]) * tmp_cap_chp['GAS']
    tmp_GAS_chp.rename(columns={c: 'GAS'}, inplace=True)
    tmp_other_chp = pd.DataFrame([tmp_cap_chp['GEO'], tmp_cap_chp['BIO'], tmp_cap_chp['HRD'], tmp_cap_chp['LIG'],
                                  tmp_cap_chp['OIL'], tmp_cap_chp['PEA'], tmp_cap_chp['WST']]).transpose()
    tmp_other_chp.rename(index={c: 'STUR'}, inplace=True)
    df_merged_chp = tmp_other_chp.merge(tmp_GAS_chp, how='outer', left_index=True, right_index=True)
    df_merged_chp[df_merged_chp < min_cap] = 0
    cap_chp[c] = df_merged_chp
    cap_chp[c].fillna(0, inplace=True)

# %% Typical unit allocation
allunits = {}

# zones = ['SE']   
for c in cap:
    # for c in zones:
    # Non CHP units
    cap_tot = cap[c]
    units = pd.DataFrame()
    for j, i in cap_tot.unstack().index:
        if cap_tot.loc[i, j] > 0:
            #        if cap_tot.loc[i]>0 & cap_tot.loc[j]>0:
            name = c + '_' + i + '_' + j
            tmp = typical[(typical.Technology == i) & (typical.Fuel == j)]
            if len(tmp) == 0:
                # try the generic entries in the dataframe:
                if len(typical[(typical.Technology == i) & (typical.Fuel == "*")]):
                    print('[INFO    ]: ' + 'Country ' + c + ' (' + i + ',' + j + '): no typical unit found, using ' +
                          'the generic unit for the provided technology')
                    tmp = typical[(typical.Technology == i) & (typical.Fuel == "*")]
                    units[name] = tmp.iloc[0, :]
                    units.loc['Technology', name], units.loc['Fuel', name] = i, j
                elif len(typical[(typical.Technology == i) & (typical.Fuel == "*")]):
                    print('[INFO    ]: ' + 'Country ' + c + ' (' + i + ',' + j + '): no typical unit found, using ' +
                          'the generic unit for the provided fuel')
                    tmp = typical[(typical.Technology == i) & (typical.Fuel == "*")]
                    units[name] = tmp.iloc[0, :]
                    units.loc['Technology', name], units.loc['Fuel', name] = i, j
                elif len(typical[(typical.Technology == '*') & (typical.Fuel == "*")]):
                    print('[INFO    ]: ' + 'Country ' + c + ' (' + i + ',' + j + '): no typical unit found, using ' +
                          'the generic unit definition (*,*)')
                    tmp = typical[(typical.Technology == '*') & (typical.Fuel == "*")]
                    units[name] = tmp.iloc[0, :]
                    units.loc['Technology', name], units.loc['Fuel', name] = i, j
                else:
                    print('[INFO    ]: ' + 'Country ' + c + ' (' + i + ',' + j + '): no typical unit found, no ' +
                          'generic unit found. The entry will be discarded!!')
            elif len(tmp) == 1:
                units[name] = tmp.iloc[0, :]
            elif len(tmp) > 1:
                print('Country ' + c + ' (' + i + ',' + j + '): more than one typical unit found, taking average')
                units[name] = tmp.mean()
                units.loc['Technology', name], units.loc['Fuel', name] = i, j

            # Adapting the resulting power plants definitions:
            units.loc['Unit', name] = name
            if units.loc['PowerCapacity', name] == 0:
                # keep the capacity as such, one single unit:
                units.loc['PowerCapacity', name] = cap_tot.loc[i, j]
                units.loc['Nunits', name] = 1
            else:
                units.loc['Nunits', name] = np.ceil(cap_tot.loc[i, j] / units.loc['PowerCapacity', name])
                units.loc['PowerCapacity', name] = cap_tot.loc[i, j] / units.loc['Nunits', name]
    if len(units) > 0:
        units = units.transpose()
        del units['Year']
        units.Zone = c
    else:
        print('[INFO    ]: ' + 'Country ' + c + ': no units found. Skipping')
        continue

    # CHP and TES
    # TES_CAPACITY = 1      #No of storage hours in TES
    cap_tot_chp = cap_chp[c]
    units_chp = pd.DataFrame()
    for j, i in cap_tot_chp.unstack().index:
        if cap_tot_chp.loc[i, j] > 0:
            name = c + '_' + i + '_' + j + '_CHP'
            tmp = typical_chp[(typical_chp.Technology == i) & (typical_chp.Fuel == j)]
            if len(tmp) == 0:
                # try the generic entries in the dataframe:
                if len(typical_chp[(typical_chp.Technology == i) & (typical_chp.Fuel == "*")]):
                    print('[INFO    ]: ' + 'Country ' + c + ' (' + i + ',' + j + '): no typical CHP unit found, ' +
                          'using the generic unit for the provided technology')
                    tmp = typical_chp[(typical_chp.Technology == i) & (typical_chp.Fuel == "*")]
                    units_chp[name] = tmp.iloc[0, :]
                    units_chp.loc['Technology', name], units_chp.loc['Fuel', name] = i, j
                elif len(typical_chp[(typical_chp.Technology == i) & (typical_chp.Fuel == "*")]):
                    print('[INFO    ]: ' + 'Country ' + c + ' (' + i + ',' + j + '): no typical CHP unit found, ' +
                          'using the generic unit for the provided fuel')
                    tmp = typical_chp[(typical_chp.Technology == i) & (typical_chp.Fuel == "*")]
                    units_chp[name] = tmp.iloc[0, :]
                    units_chp.loc['Technology', name], units_chp.loc['Fuel', name] = i, j
                elif len(typical_chp[(typical_chp.Technology == '*') & (typical_chp.Fuel == "*")]):
                    print('[INFO    ]: ' + 'Country ' + c + ' (' + i + ',' + j + '): no typical CHP unit found, ' +
                          'using the generic unit definition (*,*)')
                    tmp = typical_chp[(typical_chp.Technology == '*') & (typical_chp.Fuel == "*")]
                    units_chp[name] = tmp.iloc[0, :]
                    units_chp.loc['Technology', name], units_chp.loc['Fuel', name] = i, j
                else:
                    print('[INFO    ]: ' + 'Country ' + c + ' (' + i + ',' + j + '): no typical CHP unit found, ' +
                          'no generic unit found. The entry will be discarded!!')
            elif len(tmp) == 1:
                units_chp[name] = tmp.iloc[0, :]
            elif len(tmp) > 1:
                print('[INFO    ]: ' + 'Country ' + c + ' (' + i + ',' + j + '): more than one typical CHP unit ' +
                      'found, taking average')
                units_chp[name] = tmp.mean()
                units_chp.loc['Technology', name], units_chp.loc['Fuel', name] = i, j

            # Adapting the resulting power plants definitions:
            units_chp.loc['Unit', name] = name
            if units_chp.loc['PowerCapacity', name] == 0:
                # keep the capacity as such, one single unit:
                units_chp.loc['PowerCapacity', name] = cap_tot_chp.loc[i, j]
                units_chp.loc['Nunits', name] = 1
            else:
                units_chp.loc['Nunits', name] = np.ceil(cap_tot_chp.loc[i, j] / units_chp.loc['PowerCapacity', name])
                units_chp.loc['PowerCapacity', name] = cap_tot_chp.loc[i, j] / units_chp.loc['Nunits', name]

            if TES_CAPACITY == 0:
                print('[INFO    ]: ' + 'Country ' + c + ' (' + name + '): no TES unit')
            else:
                # units_chp.loc['STOCapacity',name] = units_chp[name, 'PowerCapacity'].values * TES_CAPACITY
                tmp_tes = units_chp.T
                tmp_tes['STOCapacity'] = tmp_tes['PowerCapacity'] / tmp_tes['CHPPowerToHeat'] * TES_CAPACITY
                tmp_tes['STOSelfDischarge'] = str(0.03)
                tmp_tes = tmp_tes.T
                units_chp.update(tmp_tes)
    if len(units_chp) > 0:
        units_chp = units_chp.transpose()
        del units_chp['Year']
        units_chp.Zone = c
        units = units.append(units_chp)
    else:
        print('[INFO    ]: ' + 'Country ' + c + ': no CHP units found. Skipping')

    # %%
    # TODO
    # Avoid merging units at this stage, just assign units as they were before
    # Special treatment for the hydro data.
    # HDAM and HPHS are merged into a single unit with the total reservoir capacity
    # Find if there are HPHS units:
    tmp = units[units.Technology == 'HPHS']
    if len(tmp) == 1:
        hphsdata = tmp.iloc[0, :]
        hphsindex = tmp.index[0]
        # The pumped hydro power is also the chargin power:
        hphsdata['STOMaxChargingPower'] = hphsdata['PowerCapacity']
        tmp = units[units.Technology == 'HDAM']
        if len(tmp) == 1:
            damdata = tmp.iloc[0, :]
            # adding the dam power to the pumpe hydro:
            hphsdata['PowerCapacity'] += damdata['PowerCapacity']
            # delte the hdam row:
            units = units[units.Technology != 'HDAM']
        if c in reservoirs.index:
            hphsdata['STOCapacity'] = reservoirs[c]
        else:
            print('[INFO    ]: ' + 'Country ' + c + ' No Reservoir Capacity data for country ' + c +
                  '. Assuming a conservative 5 hours of storage')
            hphsdata['STOCapacity'] = hphsdata['PowerCapacity'] * 5
        units.loc[hphsindex, :] = hphsdata
    elif len(tmp) == 0:
        tmp = units[units.Technology == 'HDAM']
        if len(tmp) == 1:
            if c in reservoirs.index:
                units.loc[tmp.index[0], 'STOCapacity'] = reservoirs[c]
            else:
                print('[INFO    ]: ' + 'Country ' + c + ' No Reservoir Capacity data for country ' + c +
                      '. Assuming a conservative 5 hours of storage')
                units.loc[tmp.index[0], 'STOCapacity'] = units.loc[tmp.index[0], 'PowerCapacity'] * 5
    else:
        sys.exit('Various HPHS units!')

        # Special treatment for BEVS
    if units[units.Technology == 'BEVS'].empty is True:
        print('[INFO    ]: ' + 'Country ' + c + ' (BEVS) capacity is 0 or BEVS are not present')
    else:
        tmp_bev = units[units.Technology == 'BEVS']
        bevsindex = tmp_bev.index[0]
        tmp_bev['STOMaxChargingPower'] = tmp_bev['PowerCapacity'] / 8.974294288
        tmp_bev['STOCapacity'] = tmp_bev['PowerCapacity']
        tmp_bev['PowerCapacity'] = tmp_bev['STOMaxChargingPower']
        units.update(tmp_bev)

    # Sort columns as they should be and check if Zone is defined
    cols = ['PowerCapacity', 'Unit', 'Zone', 'Technology', 'Fuel', 'Efficiency', 'MinUpTime',
            'MinDownTime', 'RampUpRate', 'RampDownRate', 'StartUpCost_pu', 'NoLoadCost_pu',
            'RampingCost', 'PartLoadMin', 'MinEfficiency', 'StartUpTime', 'CO2Intensity',
            'CHPType', 'CHPPowerToHeat', 'CHPPowerLossFactor', 'STOCapacity', 'STOSelfDischarge',
            'STOMaxChargingPower', 'STOChargingEfficiency', 'CHPMaxHeat', 'Nunits']
    units['Zone'] = c
    units = units[cols]

    allunits[c] = units


def write_pickle_file(units, file_name):
    """
    Function that creates a pickle file and saves newly created power plants
    :units:         allunits for example
    :file_name:     name of the pickle file (has to be a string)
    """
    allunits = units
    pkl_file = open(file_name + '.p', 'wb')
    pickle.dump(allunits, pkl_file)
    pkl_file.close()
    print('[INFO    ]: ' + 'Pickle file ' + file_name + ' has been written')


# write_pickle_file(allunits, 'Test')

# %% Count total number of units
def unit_count(units):
    """
    Function that counts number of units (powerplants) generatd by the script
    (This is useful to check the size of the problem)
    :units:         allunits for example
    """
    allunits = units
    unit_count = 0
    for c in allunits:
        unit_count = unit_count + allunits[c]['Unit'].count()
    print('[INFO    ]: ' + 'Total number of units in the region is ' + str(unit_count))


unit_count(allunits)


# %% Write csv file:
def write_csv_files(power_plant_filename, units, write_csv=None):
    """
    Function that generates .csv files in the Output/Database/PowerPlants/ folder
    :power_plant_filename:      clustered for example (has to be a string)
    :units:                     allunits for example
    """
    filename = power_plant_filename + '.csv'
    allunits = units
    if write_csv is True:
        for c in allunits:
            make_dir(output_folder + 'Database')
            folder = output_folder + 'Database/PowerPlants/'
            make_dir(folder)
            make_dir(folder + c)
            allunits[c].to_csv(folder + c + '/' + filename)
    else:
        print('[WARNING ]: ' + 'WRITE_CSV_FILES = False, unable to write .csv files')


write_csv_files('clustered_' + str(YEAR) + '_THFLEX', allunits, WRITE_CSV_FILES)
