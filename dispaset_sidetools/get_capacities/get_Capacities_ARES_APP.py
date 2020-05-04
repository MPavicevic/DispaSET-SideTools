# -*- coding: utf-8 -*-
"""
This script generates the PowerPlant Dispa-SET data for the JRC-EU-TIMES runs

@authors: Matija Pavičević, KU Leuven
          Sylvain Quoilin, KU Leuven
"""
from __future__ import division

import pandas as pd
import numpy as np
import logging
# Local source tree imports
from ..common import date_range, get_country_codes, write_csv_files, commons

# Assing cooling based on wighted average
def assign_cooling(pp_data, TEMBA = None):
    if TEMBA == True:
        rename = {'PowerCapacity':'Power'}
        pp_data['Capacity'] = pp_data['PowerCapacity']
    for f in ['BIO', 'GAS', 'OIL', 'WST', 'HRD', 'PEA', 'GEO', 'OTH', 'WIN', 'SUN']:
        if f == 'WIN':
            pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Cooling'].isna()), 'Cooling'] = 'WIN'
        if f == 'SUN':
            for t in ['PHOT', 'STUR']:
                if t == 'PHOT':
                    pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Technology'] == t) &
                                (pp_data['Cooling'].isna()), 'Cooling'] = 'PV'
                if t == 'STUR':
                    pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Technology'] == t) &
                                (pp_data['Cooling'].isna()), 'Cooling'] = 'CSP'
        if (f == 'GEO') or (f == 'WST') or (f == 'BIO'):
            pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Cooling'].isna()) &
                        (pp_data['Capacity'] < 15), 'Cooling'] = 'AIR'
            pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Cooling'].isna()) &
                        (pp_data['Capacity'] >= 15), 'Cooling'] = 'MDT'
        if f == 'PEA':
            pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Cooling'].isna()), 'Cooling'] = 'MDT'
        if f == 'HRD':
            pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Cooling'].isna()) &
                        (pp_data['Capacity'] < 200), 'Cooling'] = 'AIR'
            pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Cooling'].isna()) &
                        (pp_data['Capacity'] >= 200) & (pp_data['Capacity'] < 450), 'Cooling'] = 'MDT'
            pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Cooling'].isna()), 'Cooling'] = 'OTS'
        if f == 'GAS':
            for t in ['STUR', 'COMC', 'GTUR', 'ICEN']:
                if t == 'ICEN':
                    pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Technology'] == t) & (pp_data['Capacity'] < 15) &
                                (pp_data['Cooling'].isna()),'Cooling'] = 'AIR'
                    pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Technology'] == t) & (pp_data['Capacity'] >= 15) &
                                (pp_data['Cooling'].isna()),'Cooling'] = 'OTF'
                if t == 'STUR':
                    pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Technology'] == t) &
                                (pp_data['Capacity'] < 20) & (pp_data['Cooling'].isna()),'Cooling'] = 'MDT'
                    pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Technology'] == t) &
                                (pp_data['Capacity'] >= 20) & (pp_data['Cooling'].isna()),'Cooling'] = 'OTF'
                if t == 'COMC':
                    pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Technology'] == t) &
                                (pp_data['Capacity'] >= 200) & (pp_data['Capacity'] < 250) &
                                (pp_data['Cooling'].isna()),'Cooling'] = 'AIR'
                    pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Technology'] == t) &
                                (pp_data['Capacity'] >= 180) & (pp_data['Capacity'] < 720) &
                                (pp_data['Cooling'].isna()),'Cooling'] = 'OTF'
                    pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Technology'] == t) &
                                (pp_data['Cooling'].isna()),'Cooling'] = 'MDT'
                if t == 'GTUR':
                    pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Technology'] == t) & (pp_data['Capacity'] < 15) &
                                (pp_data['Cooling'].isna()),'Cooling'] = 'AIR'
            pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Cooling'].isna()), 'Cooling'] = 'OTF'
        if (f == 'OIL') or (f == 'OTH'):
            for t in ['STUR', 'COMC', 'GTUR', 'ICEN']:
                if (t == 'COMC') or (t == 'STUR'):
                    pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Technology'] == t) & (pp_data['Capacity'] < 15) &
                                (pp_data['Cooling'].isna()),'Cooling'] = 'AIR'
                    pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Technology'] == t) &
                                (pp_data['Capacity'] >= 15) & (pp_data['Capacity'] < 720) &
                                (pp_data['Cooling'].isna()),'Cooling'] = 'OTF'
                    pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Technology'] == t) &
                                (pp_data['Cooling'].isna()),'Cooling'] = 'MDT'
                if (t == 'ICEN') or (t == 'GTUR'):
                    pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Technology'] == t) & (pp_data['Capacity'] > 0) &
                                (pp_data['Cooling'].isna()),'Cooling'] = 'AIR'
            pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Cooling'].isna()), 'Cooling'] = 'OTF'
    return pp_data


# Input data preprocessing
def powerplant_data_preprocessing(pp_data):
    """
    Function used to preprocess raw excel data
    :param pp_data:     Raw excel data
    :return:            Processed power plant data
    """
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
             'KERO': 'OIL', 'LIQ': 'OIL', 'SHALE': 'OIL', 'NAP': 'OIL',
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

    cooling = {'MDT': 'MDT/NDT', 'NDT': 'MDT/NDT', 'NDT/D': 'MDT/NDT',
               'OTF': 'OTF/OTS', 'OTB': 'OTF/OTS', 'OTS': 'OTF/OTS'}

    pp_data['Fuel'] = pp_data['Fuel'].replace(fuels)
    pp_data['Technology'] = pp_data['Technology'].replace(technologies)
    pp_data = assign_cooling(pp_data)
    pp_data['Cooling'] = pp_data['Cooling'].replace(cooling)
    return pp_data


def assign_typical_units(pp_data, typical_units, typical_cooling):
    """
    Function to assign typical units
    :param pp_data:         Preprocessed powerplant data
    :param typical_units    Typical units from csv files
    :return:                Data in dispaset readable format
    """
    # Assign data to Dispa-SET readable format
    data = pd.DataFrame(columns=commons['ColumnNames'])
    data['Unit'] = pp_data['Plant']
    data['Zone'] = get_country_codes(list(pp_data['Country']))
    data['Fuel'] = pp_data['Fuel']
    data['Technology'] = pp_data['Technology']
    data['PowerCapacity'] = pp_data['Capacity']

    # Historic units assign only 1 per unit
    data['Nunits'] = 1

    # Assign missing data from typical units
    cols = ['Efficiency', 'MinUpTime', 'MinDownTime', 'RampUpRate', 'RampDownRate', 'StartUpCost_pu', 'NoLoadCost_pu',
            'RampingCost', 'PartLoadMin', 'MinEfficiency', 'StartUpTime', 'CO2Intensity',
            'COP', 'Tnominal', 'coef_COP_a', 'coef_COP_b',
            'STOCapacity', 'STOSelfDischarge', 'STOMaxChargingPower', 'STOChargingEfficiency']

    # Assign cooling data from typical cooling
    cool_cols = ['WaterWithdrawal', 'WaterConsumption']

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
                if fuel != 'OTH':
                    for cooling in ['AIR', 'WIN', 'PV', 'CSP', 'OTF/OTS', 'MDT/NDT']:
                        if data.loc[(data['Technology'] == technology) & (data['Fuel'] == fuel) &
                                    (pp_data['Cooling'] == cooling)].empty:
                            continue
                        else:
                            data.loc[(data['Technology'] == technology) & (data['Fuel'] == fuel) &
                                     (pp_data['Cooling'] == cooling), cool_cols] = typical_cooling.loc[
                                (typical_cooling['Technology'] == technology) & (typical_cooling['Fuel'] == fuel) &
                                (typical_cooling['Process'] == cooling), cool_cols].values
                            logging.info('Typical cooling assigned to: ' + fuel + ' + ' + technology + ' + ' + cooling +
                                         ' combination.')
                else:
                    logging.warning('Typical cooling was not assigned to ' + fuel + '. No typical data available for OTH!')

    return data


# Preprocess historic hydro units
def get_hydro_units(data_hydro, EFFICIENCY):
    """
    :param data_hydro:      Raw hydro data from xlsx files
    :return hydro_units:    Hydro units in dispaset format
    """
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
    for key in ['MinUpTime', 'MinDownTime', 'StartUpCost_pu', 'NoLoadCost_pu', 'RampingCost', 'PartLoadMin',
                'StartUpTime', 'CO2Intensity']:
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
    hydro_units.loc[data_hydro['STOCapacity'] / hydro_units['PowerCapacity'] >= 5, 'STOCapacity'] = data_hydro[
        'STOCapacity']
    # HROR efficiency is 1
    hydro_units.loc[hydro_units['Technology'] == 'HROR', 'Efficiency'] = 1
    return hydro_units


# Merge two series
def merge_power_plants(data_1, data_2):
    """
    Merge two preprocessed powerplant databases
    :param data_1:      First database, conventional units
    :param data_2:      Second database, hydro units
    :return:            Merged data
    """
    data = data_1.append(data_2, ignore_index=True, sort=False)
    data['PowerCapacity'] = data['PowerCapacity'].astype(float)
    return data


# %% TEMBA Processing
def get_temba_plants(temba_inputs, old_units, hydro_units, typical_units, typical_cooling, YEAR, TEMBA=False, scenario=False):
    """
    Function that adds temba capacities to the existing ones
    :param temba_inputs:    TEMBA projections
    :param hydro_units:     Hydro units
    :param old_units        Old units
    :param typical_units    Typical units
    :return:                Database of power plants
    """
    if TEMBA is True:
        temba_fuels = {'Biomass': 'BIO', 'Biomass with ccs': 'BIO',
                       'Coal': 'HRD', 'Coal with ccs': 'HRD',
                       'Gas': 'GAS', 'Gas with ccs': 'GAS',
                       'Geothermal': 'GEO',
                       'Hydro': 'WAT',
                       'Nuclear': 'NUC',
                       'Oil': 'OIL',
                       'Solar CSP': 'SUN', 'Solar PV': 'SUN',
                       'Wind': 'WIN'}

        temba_techs = {'Biomass': 'STUR',
                       'Biomass with ccs': 'STUR',
                       'Coal': 'STUR', 'Coal with ccs': 'STUR',
                       'Gas': 'COMC', 'Gas with ccs': 'COMC',
                       'Geothermal': 'STUR',
                       'Hydro': 'WAT',
                       'Nuclear': 'STUR',
                       'Oil': 'ICEN',
                       'Solar CSP': 'STUR', 'Solar PV': 'PHOT',
                       'Wind': 'WTON'}
        # Share of HDAM units and tipical number of sotrage hours per zone
        share = {}
        storage = {}
        for c in hydro_units['Zone']:
            share[c] = hydro_units['PowerCapacity'].loc[
                           (hydro_units['Zone'] == c) & (hydro_units['Technology'] == 'HDAM')].sum() / \
                       hydro_units['PowerCapacity'].loc[(hydro_units['Zone'] == c)].sum()
            storage[c] = hydro_units['STOCapacity'].loc[
                             (hydro_units['Zone'] == c) & (hydro_units['Technology'] == 'HDAM')].sum() / \
                         hydro_units['PowerCapacity'].loc[(hydro_units['Zone'] == c)].sum()
        tmp_hydro_data = pd.DataFrame.from_dict(share, orient='index', columns=['HDAM_share'])
        tmp_hydro_data['STO_hours'] = pd.DataFrame.from_dict(storage, orient='index')
        tmp_hydro_data.fillna(0, inplace=True)
        # Process new TEMBA additions (excluding hydro, assigned later)
        aa = temba_inputs[temba_inputs['parameter'].str.contains("New power generation capacity")]
        aa = aa[aa['scenario'].str.contains(scenario)]
        aa.fillna(0, inplace=True)
        selected_years = list(range(2015, YEAR + 1))
        selected_years = [str(i) for i in selected_years]
        col_names = ['variable', 'scenario', 'country', 'parameter'] + selected_years
        bb = aa[selected_years].sum(axis=1)
        aa['Total'] = bb
        aa['Fuel'] = aa['variable']
        aa['Technology'] = aa['variable']
        aa['Fuel'] = aa['Fuel'].replace(temba_fuels)
        aa['Technology'] = aa['Technology'].replace(temba_techs)
        aa['New'] = 'New'
        temba_fosil = aa[~aa['Fuel'].str.contains("WAT")]
        temba_hydro = aa[aa['Fuel'].str.contains("WAT")]
        temba_fosil['Name'] = temba_fosil[['country', 'Fuel', 'Technology', 'New']].apply(lambda x: '_'.join(x), axis=1)
        temba_HROR = temba_hydro.copy()
        temba_HDAM = temba_hydro.copy()
        temba_HROR.set_index('country', inplace=True, drop=False)
        temba_HDAM.set_index('country', inplace=True, drop=False)
        temba_HROR = temba_HROR[temba_HROR.index.isin(tmp_hydro_data.index)]
        temba_HDAM = temba_HDAM[temba_HDAM.index.isin(tmp_hydro_data.index)]
        temba_HROR['Total'] = temba_HROR['Total'] * (1 - tmp_hydro_data['HDAM_share'])
        temba_HDAM['Total'] = temba_HDAM['Total'] * tmp_hydro_data['HDAM_share']
        tech_hror = {'WAT': 'HROR'}
        tech_hdam = {'WAT': 'HDAM'}
        temba_HROR['Technology'] = temba_HROR['Technology'].replace(tech_hror)
        temba_HDAM['Technology'] = temba_HDAM['Technology'].replace(tech_hdam)
        temba_HROR['Name'] = temba_HROR[['country', 'Fuel', 'Technology', 'New']].apply(lambda x: '_'.join(x), axis=1)
        temba_HDAM['Name'] = temba_HDAM[['country', 'Fuel', 'Technology', 'New']].apply(lambda x: '_'.join(x), axis=1)
        temba_HROR.reset_index(drop=True, inplace=True)
        temba_HDAM.reset_index(drop=True, inplace=True)
        temba_tmp = temba_fosil.append(temba_HROR, ignore_index=True)
        temba_tmp = temba_tmp.append(temba_HDAM, ignore_index=True)
        temba = pd.DataFrame(columns=commons['ColumnNames'])
        temba['Unit'] = temba_tmp['Name']
        temba['Zone'] = temba_tmp['country']
        temba['Fuel'] = temba_tmp['Fuel']
        temba['Technology'] = temba_tmp['Technology']
        temba['PowerCapacity'] = temba_tmp['Total'] * 1e3
        temba = temba[(temba[['PowerCapacity']] != 0).all(axis=1)]
        # merge HROR series

        # Historic units assign only 1 per unit
        temba['Nunits'] = 1

        # Assign missing data from typical units
        cols = ['Efficiency', 'MinUpTime', 'MinDownTime', 'RampUpRate', 'RampDownRate', 'StartUpCost_pu',
                'NoLoadCost_pu',
                'RampingCost', 'MinEfficiency', 'StartUpTime', 'CO2Intensity', 'COP', 'Tnominal',
                'coef_COP_a',
                'coef_COP_b', 'STOCapacity', 'STOSelfDischarge', 'STOMaxChargingPower', 'STOChargingEfficiency']

        for fuel in commons['Fuels']:
            for technology in commons['Technologies']:
                if temba.loc[(temba['Technology'] == technology) & (temba['Fuel'] == fuel)].empty:
                    # logging.info(fuel + ' and ' + technology + ' combination not present in this database.')
                    continue
                else:
                    temba.loc[(temba['Technology'] == technology) & (temba['Fuel'] == fuel), cols] = \
                        typical_units.loc[
                            (typical_units['Technology'] == technology) & (typical_units['Fuel'] == fuel), cols].values
                    temba.loc[(temba['Technology'] == technology) & (temba['Fuel'] == fuel), 'PartLoadMin'] = \
                        typical_units.loc[
                            (typical_units['Technology'] == technology) &
                            (typical_units['Fuel'] == fuel), 'PartLoadMin'].values * typical_units.loc[
                            (typical_units['Technology'] == technology) &
                            (typical_units['Fuel'] == fuel), 'PowerCapacity'].values / temba.loc[
                            (temba['Technology'] == technology) & (temba['Fuel'] == fuel), 'PowerCapacity']
                    temba.loc[(temba['Technology'] == technology) & (temba['Fuel'] == fuel) &
                              (temba['PartLoadMin'] >= 1), 'PartLoadMin'] = typical_units.loc[
                            (typical_units['Technology'] == technology) &
                            (typical_units['Fuel'] == fuel), 'PartLoadMin'].values
                    logging.info('Typical units assigned to: ' + fuel + ' and ' + technology + ' combination.')

        temba['Cooling'] = np.nan
        temba = assign_cooling(temba, TEMBA=True)
        cooling = {'MDT': 'MDT/NDT', 'NDT': 'MDT/NDT', 'NDT/D': 'MDT/NDT',
                   'OTF': 'OTF/OTS', 'OTB': 'OTF/OTS', 'OTS': 'OTF/OTS'}
        temba['Cooling'] = temba['Cooling'].replace(cooling)

        # Assign cooling data from typical cooling
        cool_cols = ['WaterWithdrawal', 'WaterConsumption']

        for fuel in temba['Fuel'].unique():
            for technology in temba['Technology'].unique():
                if temba.loc[(temba['Technology'] == technology) & (temba['Fuel'] == fuel)].empty:
                    # logging.info(fuel + ' and ' + technology + ' combination not present in this database.')
                    continue
                else:
                    if fuel != 'OTH':
                        for cooling in ['AIR', 'WIN', 'PV', 'CSP', 'OTF/OTS', 'MDT/NDT']:
                            if temba.loc[(temba['Technology'] == technology) & (temba['Fuel'] == fuel) &
                                        (temba['Cooling'] == cooling)].empty:
                                continue
                            else:
                                temba.loc[(temba['Technology'] == technology) & (temba['Fuel'] == fuel) &
                                         (temba['Cooling'] == cooling), cool_cols] = typical_cooling.loc[
                                    (typical_cooling['Technology'] == technology) & (typical_cooling['Fuel'] == fuel) &
                                    (typical_cooling['Process'] == cooling), cool_cols].values
                                logging.info(
                                    'Typical cooling assigned to: ' + fuel + ' + ' + technology + ' + ' + cooling +
                                    ' combination.')
                    else:
                        logging.warning(
                            'Typical cooling was not assigned to ' + fuel + '. No typical data available for OTH!')

        temba.drop(['Cooling', 'Capacity'], axis=1, inplace=True)
        for c in temba.loc[(temba['Technology'] == 'HDAM'), 'Zone']:
            temba.loc[(temba['Technology'] == 'HDAM') & (temba['Zone'] == c), 'STOCapacity'] = \
                tmp_hydro_data.at[c, 'STO_hours'] * \
                temba.loc[(temba['Technology'] == 'HDAM') & (temba['Zone'] == c), 'PowerCapacity']

        # data = data.append(temba, ignore_index=True)
        data = merge_power_plants(merge_power_plants(old_units, hydro_units), temba)
    else:
        logging.info('TEMBA model not selected')
        data = merge_power_plants(old_units, hydro_units)
    return data


# Generation of allunits
def get_allunits(data, countries):
    """
    Function that assigns allunits
    :param data:    data sorted
    :return:        return allunits
    """
    allunits = {}
    unique_fuel = {}
    unique_tech = {}
    for c in countries:
        allunits[c] = data.loc[data['Zone'] == c]
        unique_fuel[c] = list(allunits[c]['Fuel'].unique())
        unique_tech[c] = list(allunits[c]['Technology'].unique())
    return allunits

# write_csv_files(allunits, 'ARES_APP', SOURCE, 'PowerPlants', str(YEAR), WRITE_CSV, 'Zonal')
#
# if WRITE_CSV is True:
#     import pickle
#
#     with open(input_folder + source_folder + 'TEMBA_capacities_' + str(YEAR) + '.p', 'wb') as handle:
#         pickle.dump(allunits, handle, protocol=pickle.HIGHEST_PROTOCOL)
#
#     with open(input_folder + source_folder + 'Units_from_get_Capacities.p', 'rb') as handle:
#         allunits = pickle.load(handle)
#
# tmp = {}
# for p in ['NAPP', 'EAPP', 'CAPP']:
#     if p == 'NAPP':
#         zones = get_country_codes(countries_NAPP)
#     elif p == 'CAPP':
#         zones = get_country_codes(countries_CAPP)
#     else:
#         zones = get_country_codes(countries_EAPP)
#     aa = {}
#     for fuel in data['Fuel'].unique():
#         aa[fuel] = data.loc[(data['Zone'].isin(zones)) & (data['Fuel'] == fuel)]['PowerCapacity'].sum()
#     tmp[p] = aa

# bb = pd.DataFrame.from_dict(tmp)
#
# bb.to_csv('Ares_capacites.csv')
