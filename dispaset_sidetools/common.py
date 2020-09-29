# -*- coding: utf-8 -*-
"""
Created on Sat Dec 23 20:41:12 2017
 
@author: sylvain
"""
from __future__ import division

import pycountry
import datetime
import itertools
import os
import sys
import re
import logging

import numpy as np
import pandas as pd

# %%

entsoe_types = ['Wind Onshore ',
                'Geothermal ',
                'Hydro Water Reservoir ',
                'Hydro Pumped Storage ',
                'Nuclear ',
                'Hydro Run-of-river and poundage ',
                'Solar ',
                'Biomass ',
                'Other renewable ',
                'Fossil Brown coal/Lignite ',
                'Marine ',
                'Fossil Oil ',
                'Fossil Peat ',
                'Wind Offshore ',
                'Waste ',
                'Fossil Hard coal ',
                'Fossil Oil shale ',
                'Fossil Gas ',
                'Fossil Coal-derived gas ',
                'Other ']

# %%

'''
Dictionary with the common variable definitions
to be used in Dispa-SET
'''
commons = {}

# Logging
commons['logfile'] = str(datetime.datetime.now()).replace(':', '-').replace(' ', '_') + '.dispa_sidetools.log'

# Standard folders
commons['InputFolder'] = '../../Inputs/'
commons['OutputFolder'] = '../../Outputs/'

# Timestep
commons['TimeStep'] = '1h'

# DispaSET technologies:
commons['Technologies'] = ['COMC', 'GTUR', 'HDAM', 'HROR', 'HPHS', 'ICEN', 'PHOT', 'STUR', 'WTOF', 'WTON', 'CAES',
                           'BATS', 'BEVS', 'THMS', 'P2GS', 'SCSP']
# List of renewable technologies:
commons['tech_renewables'] = ['WTON', 'WTOF', 'PHOT', 'HROR']
# List of storage technologies:
commons['tech_storage'] = ['HDAM', 'HPHS', 'BATS', 'BEVS', 'CAES', 'THMS']
# List of CHP types:
commons['types_CHP'] = ['extraction', 'back-pressure', 'p2h']
# DispaSET fuels:
commons['Fuels'] = ['BIO', 'GAS', 'HRD', 'LIG', 'NUC', 'OIL', 'PEA', 'SUN', 'WAT', 'WIN', 'WST', 'OTH', 'GEO']
# DispaSET cooling technologies
commons['Cooling'] = ['AIR', 'MDT', 'NDT', 'OTB', 'OTS', 'OTF']
# Ordered list of fuels for plotting (the first ones are negative):
commons['MeritOrder'] = ['Storage', 'FlowOut', 'NUC', 'LIG', 'HRD', 'BIO', 'GAS', 'OIL', 'PEA', 'WST', 'SUN', 'WIN',
                         'FlowIn', 'WAT']
# Colors associated with each fuel:
commons['colors'] = {'LIG': '#af4b9180', 'PEA': '#af4b9199', 'HRD': 'darkviolet', 'OIL': 'magenta',
                     'GAS': '#d7642dff',
                     'NUC': '#466eb4ff',
                     'SUN': '#e6a532ff',
                     'WIN': '#41afaaff',
                     'WAT': '#00a0e1ff',
                     'BIO': '#7daf4bff', 'GEO': '#7daf4bbf',
                     'Storage': '#b93c46ff', 'FlowIn': '#b93c46b2', 'FlowOut': '#b93c4666',
                     'OTH': '#b9c33799', 'WST': '#b9c337ff',
                     'HDAM': '#00a0e1ff',
                     'HPHS': 'blue',
                     'THMS': '#C04000ff',
                     'BATS': '#41A317ff',
                     'BEVS': '#b9c33799'}
# Hatches associated with each fuel (random):
hatches = itertools.cycle(['x', '//', '\\', '/'])
commons['hatches'] = {}
for x in commons['colors']:
    commons['hatches'][x] = next(hatches)

# %%

mapping = {}
mapping['entsoe2iso'] = {u'AT': u'AT',
                         u'BE': u'BE',
                         u'BG': u'BG',
                         u'CH': u'CH',
                         u'CY': u'CY',
                         u'CZ': u'CZ',
                         u'DE': u'DE',
                         u'DE_50HzT': u'DE',
                         u'DE_AT_LU': u'DE_AT_LU',
                         u'DE_Amprion': u'DE',
                         u'DE_TenneT_GER': u'DE',
                         u'DE_TransnetBW': u'DE',
                         u'DK': u'DK',
                         u'DK1': u'DK1',
                         u'DK2': u'DK2',
                         u'EE': u'EE',
                         u'ES': u'ES',
                         u'FI': u'FI',
                         u'FR': u'FR',
                         u'GB': u'GB',
                         u'GR': u'GR',
                         u'HR': u'HR',
                         u'HU': u'HU',
                         u'IE': u'IE',
                         u'IE_SEM': u'IE',
                         u'IT': u'IT',
                         u'IT_CNOR': u'IT',
                         u'IT_CSUD': u'IT',
                         u'IT_North': u'IT',
                         u'IT_SARD': u'IT',
                         u'IT_SICI': u'IT',
                         u'IT_SUD': u'IT',
                         u'LT': u'LT',
                         u'LU': u'LU',
                         u'LV': u'LV',
                         u'ME': u'ME',
                         u'MK': u'MK',
                         u'NIE': u'IE',
                         u'NL': u'NL',
                         u'NO': u'NO',
                         u'NO1': u'NO1',
                         u'NO2': u'NO2',
                         u'NO3': u'NO3',
                         u'NO4': u'NO4',
                         u'NO5': u'NO5',
                         u'PL': u'PL',
                         u'PT': u'PT',
                         u'RO': u'RO',
                         u'RS': u'RS',
                         u'SE': u'SE',
                         u'SE1': u'SE1',
                         u'SE2': u'SE2',
                         u'SE3': u'SE3',
                         u'SE4': u'SE4',
                         u'SI': u'SI',
                         u'SK': u'SK'}

mapping['original'] = {u'AT': u'AT',
                       u'BE': u'BE',
                       u'BG': u'BG',
                       u'CH': u'CH',
                       u'CY': u'CY',
                       u'CZ': u'CZ',
                       u'DE': u'DE',
                       u'DE_50HzT': u'DE_50HzT',
                       u'DE_AT_LU': u'DE_AT_LU',
                       u'DE_Amprion': u'DE_Amprion',
                       u'DE_TenneT_GER': u'DE_TenneT_GER',
                       u'DE_TransnetBW': u'DE_TransnetBW',
                       u'DK': u'DK',
                       u'DK1': u'DK1',
                       u'DK2': u'DK2',
                       u'EE': u'EE',
                       u'ES': u'ES',
                       u'FI': u'FI',
                       u'FR': u'FR',
                       u'GB': u'GB',
                       u'GR': u'GR',
                       u'HR': u'HR',
                       u'HU': u'HU',
                       u'IE': u'IE',
                       u'IE_SEM': u'IE_SEM',
                       u'IT': u'IT',
                       u'IT_CNOR': u'IT_CNOR',
                       u'IT_CSUD': u'IT_CSUD',
                       u'IT_North': u'IT_North',
                       u'IT_SARD': u'IT_SARD',
                       u'IT_SICI': u'IT_SICI',
                       u'IT_SUD': u'IT_SUD',
                       u'LT': u'LT',
                       u'LU': u'LU',
                       u'LV': u'LV',
                       u'ME': u'ME',
                       u'MK': u'MK',
                       u'NIE': u'NIE',
                       u'NL': u'NL',
                       u'NO': u'NO',
                       u'NO1': u'NO1',
                       u'NO2': u'NO2',
                       u'NO3': u'NO3',
                       u'NO4': u'NO4',
                       u'NO5': u'NO5',
                       u'PL': u'PL',
                       u'PT': u'PT',
                       u'RO': u'RO',
                       u'RS': u'RS',
                       u'SE': u'SE',
                       u'SE1': u'SE1',
                       u'SE2': u'SE2',
                       u'SE3': u'SE3',
                       u'SE4': u'SE4',
                       u'SI': u'SI',
                       u'SK': u'SK'}

mapping['entsoe2dispa'] = {u'AT': u'AT',
                           u'BE': u'BE',
                           u'BG': u'BG',
                           u'CH': u'CH',
                           u'CY': u'CY',
                           u'CZ': u'CZ',
                           u'DE': u'DE',
                           u'DK': u'DK',
                           u'EE': u'EE',
                           u'ES': u'ES',
                           u'FI': u'FI',
                           u'FR': u'FR',
                           u'GB': u'UK',
                           u'GR': u'EL',
                           u'HR': u'HR',
                           u'HU': u'HU',
                           u'IE': u'IE',
                           u'IT': u'IT',
                           u'LT': u'LT',
                           u'LU': u'LU',
                           u'LV': u'LV',
                           u'ME': u'ME',
                           u'MK': u'MK',
                           u'NL': u'NL',
                           u'NO': u'NO',
                           u'PL': u'PL',
                           u'PT': u'PT',
                           u'RO': u'RO',
                           u'RS': u'RS',
                           u'SE': u'SE',
                           u'SI': u'SI',
                           u'SK': u'SK'}

mapping['dispa2entsoe'] = {u'AT': u'AT',
                           u'BE': u'BE',
                           u'BG': u'BG',
                           u'CH': u'CH',
                           u'CY': u'CY',
                           u'CZ': u'CZ',
                           u'DE': u'DE',
                           u'DK': u'DK',
                           u'EE': u'EE',
                           u'ES': u'ES',
                           u'FI': u'FI',
                           u'FR': u'FR',
                           u'UK': u'GB',
                           u'EL': u'GR',
                           u'HR': u'HR',
                           u'HU': u'HU',
                           u'IE': u'IE',
                           u'IT': u'IT',
                           u'LT': u'LT',
                           u'LU': u'LU',
                           u'LV': u'LV',
                           u'ME': u'ME',
                           u'MK': u'MK',
                           u'NL': u'NL',
                           u'NO': u'NO',
                           u'PL': u'PL',
                           u'PT': u'PT',
                           u'RO': u'RO',
                           u'RS': u'RS',
                           u'SE': u'SE',
                           u'SI': u'SI',
                           u'SK': u'SK'}

mapping['iso2dispa'] = {u'AT': u'AT',
                        u'BE': u'BE',
                        u'BG': u'BG',
                        u'CH': u'CH',
                        u'CY': u'CY',
                        u'CZ': u'CZ',
                        u'DE': u'DE',
                        u'DE_50HzT': u'DE',
                        u'DE_AT_LU': u'DE',
                        u'DE_Amprion': u'DE',
                        u'DE_TenneT_GER': u'DE',
                        u'DE_TransnetBW': u'DE',
                        u'DK': u'DK',
                        u'DK1': u'DK',
                        u'DK2': u'DK',
                        u'EE': u'EE',
                        u'ES': u'ES',
                        u'FI': u'FI',
                        u'FR': u'FR',
                        u'GB': u'UK',
                        u'GR': u'EL',
                        u'HR': u'HR',
                        u'HU': u'HU',
                        u'IE': u'IE',
                        u'IE_SEM': u'IE',
                        u'IT': u'IT',
                        u'IT_CNOR': u'IT',
                        u'IT_CSUD': u'IT',
                        u'IT_North': u'IT',
                        u'IT_SARD': u'IT',
                        u'IT_SICI': u'IT',
                        u'IT_SUD': u'IT',
                        u'LT': u'LT',
                        u'LU': u'LU',
                        u'LV': u'LV',
                        u'ME': u'ME',
                        u'MK': u'MK',
                        u'NIE': u'IE',
                        u'NL': u'NL',
                        u'NO': u'NO',
                        u'NO1': u'NO',
                        u'NO2': u'NO',
                        u'NO3': u'NO',
                        u'NO4': u'NO',
                        u'NO5': u'NO',
                        u'PL': u'PL',
                        u'PT': u'PT',
                        u'RO': u'RO',
                        u'RS': u'RS',
                        u'SE': u'SE',
                        u'SE1': u'SE',
                        u'SE2': u'SE',
                        u'SE3': u'SE',
                        u'SE4': u'SE',
                        u'SI': u'SI',
                        u'SK': u'SK'}

commons['ColumnNames'] = list(
    ['Unit', 'PowerCapacity', 'Nunits', 'Zone', 'Technology', 'Fuel', 'Efficiency', 'MinUpTime', 'MinDownTime',
     'RampUpRate', 'RampDownRate', 'StartUpCost_pu', 'NoLoadCost_pu', 'RampingCost', 'PartLoadMin',
     'MinEfficiency', 'StartUpTime', 'CO2Intensity', 'CHPType', 'CHPPowerToHeat', 'CHPPowerLossFactor',
     'COP', 'Tnominal', 'coef_COP_a', 'coef_COP_b', 'STOCapacity', 'STOSelfDischarge', 'STOMaxChargingPower',
     'STOChargingEfficiency', 'CHPMaxHeat', 'WaterWithdrawal', 'WaterConsumption'])

# inverting dictionary (list of subzones for each zone):
mapping['iso2entsoe'] = {}
for key in mapping['original']:
    if mapping['original'][key] in mapping['iso2entsoe']:
        mapping['iso2entsoe'][mapping['original'][key]].append(key)
    else:
        mapping['iso2entsoe'][mapping['original'][key]] = [key]


# %% Helper functions

def fix_na(series, fillzeros=True, verbose=True, name='', Nstd=4, outliers=None):
    """
    Function that fills zero and n/a values from a time series by interpolating
    from the same hours in the previous and next days

    :param series:  Pandas Series with proper datetime index
    :param fillzeros:   If true, also interpolates zero values in the time series
    :param verbose:     If true, prints information regarding the number of fixed data points
    :param name:        String with the name of the time series, for the display massage
    :param Nstd:        Number of standard deviations to use as threshold for outlier detection
    :param outliers:    List of lists with the start and stop periods to be discarded

    :returns:   Same series with filled nan values
    """
    longname = name + ' ' + str(series.index.freq)
    # turn all zero values into na:
    if fillzeros:
        series[series == 0] = np.nan
    # check for outliers:
    toohigh = series > series.mean() + Nstd * series.std()
    if np.sum(toohigh) > 0:
        print('Time series "' + longname + '": ' + str(
            np.sum(toohigh)) + ' data points unrealistically high. They will be fixed as well')
        series[toohigh] = np.nan
    # write na in all the locations defined as "outlier"
    if outliers:
        count = 0
        for r in outliers:
            idx = (series.index > pd.to_datetime(r[0])) & (series.index < pd.to_datetime(r[-1]))
            series[idx] = np.nan
            count += np.sum(idx)
        print('Time series "' + longname + '": ' + str(count) + ' data points flagged as outliers and removed')

    # Now fix all nan values: 
    loc = np.where(series.isnull())[0]
    print('Time series "' + longname + '": ' + str(len(loc)) + ' data points to fix')
    for i in loc:
        idx = series.index[i]
        # go see if previous days are defined at the same hour:
        left = np.nan
        idxleft = idx + datetime.timedelta(days=-1)
        while np.isnan(left) and idxleft in series.index:
            if np.isnan(series[idxleft]):
                idxleft = idxleft + datetime.timedelta(days=-1)
            else:
                left = series[idxleft]

        right = np.nan
        idxright = idx + datetime.timedelta(days=1)
        while np.isnan(right) and idxright in series.index:
            if np.isnan(series[idxright]):
                idxright = idxright + datetime.timedelta(days=1)
            else:
                right = series[idxright]

        if (not np.isnan(left)) and (not np.isnan(right)):
            series[idx] = (left + right) / 2
        elif (not np.isnan(left)) and np.isnan(right):
            series[idx] = left
        elif np.isnan(left) and (not np.isnan(right)):
            series[idx] = right
        else:
            print('ERROR : no valid data found to fill the data point ' + str(idx))

    return series


def make_dir(path):
    """
    Function that creates directories (usually used for outputs)

    :param path:    Path to make dir
    :return:        Created directory
    """
    if not os.path.isdir(path):
        os.mkdir(path)


def date_range(start_date, end_date, freq):
    """
    Function that creates pandas date-range between two dates

    :param start_date:  Start date string
    :param end_date:    Ened date string
    :param freq:        Frequency H, D, Y...
    :return:            Date range with specific frequency
    """
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    drange = pd.date_range(start, end, freq=freq)
    drange = drange.drop(end)
    return drange


def get_country_codes(zones):
    """
    This function returns ISO2 country codes used inside Dispa-SET from real country names
    :param zones:       List of country names
    :return:            List of country codes
    """
    dic = {'Democratic Republic of the Congo': 'Congo, The Democratic Republic of the',
           'Republic of the Congo': 'Congo',
           'United Republic of Tanzania': 'Tanzania, United Republic of',
           'Tanzania': 'Tanzania, United Republic of',
           "Cote d'Ivoire": "Côte d'Ivoire",
           'Swaziland': 'Eswatini',
           'western Sahara': 'Western Sahara',
           'Santa Helena': 'Saint Helena, Ascension and Tristan da Cunha',
           'Reunion': 'Réunion',
           'Congo Dem Rep': 'Congo, The Democratic Republic of the',
           "Cote D'Ivoire": "Côte d'Ivoire",
           'São Tomé and Príncipe': 'Sao Tome and Principe',
           'Sao Tome & Principe': 'Sao Tome and Principe',
           'Cape Verde': 'Cabo Verde'
           }
    zones = [dic.get(n, n) for n in zones]
    countries = {}
    for country in pycountry.countries:
        countries[country.name] = country.alpha_2
    codes = [countries.get(country, 'Unknown code') for country in zones]
    return codes


def write_csv_files(data, model_folder, source_name, variable_name, year=None, write_csv=False, agg_type=None):
    """
    Dispa-SET-sidetools function that generates zonal csv. files in Dispa-SET readable format
    :param data:                Data to be saved as csv. files
    :param model_folder:        Name of the model whos database should be generated
    :param source_name:         Name of the model for which Dispa-SET database is created
    :param variable_name:       Name of the variable to be saved: TotalLoadValue, AvailabilityFactor...
    :param year:                Optional Year for the input data
    :param write_csv:           True creates csv database
    :param agg_type:                Type of data to be written ['Zonal','Aggregated']
    :return:
    """
    acronym = re.sub(r'[a-z ]+', '', variable_name)
    if write_csv is True:
        make_dir('../../Outputs/')
        make_dir('../../Outputs/' + model_folder)
        make_dir('../../Outputs/' + model_folder + '/Database/')
        folder = '../../Outputs/' + model_folder + '/Database/' + variable_name + '/'
        make_dir(folder)
        if (agg_type == 'Zonal') or (agg_type is None):
            if isinstance(data, dict):
                for c in list(data):
                    make_dir(folder + c)
                    data[c].to_csv(folder + c + '/' + acronym + '_' + source_name + '_' + str(year) + '.csv',
                                   header=True)
                    logging.info(variable_name + ' database was created for zone: ' + c + '.')
            else:
                for c in data.columns:
                    make_dir(folder + c)
                    data[c].to_csv(folder + c + '/' + acronym + '_' + source_name + '_' + str(year) + '.csv',
                                   header=False)
                    logging.info(variable_name + ' database was created for zone: ' + c + '.')
        elif agg_type == 'Aggregated':
            data.to_csv(folder + acronym + '_' + source_name + '_' + str(year) + '.csv', header=True)
            logging.info(agg_type + ' Database was created for the following input: ' + variable_name + '.')
        else:
            logging.critical('Wrong type name. Should be: Zonal, Aggregated or None!')
            sys.exit(0)


def leap_year(y):
    if int(y) % 400 == 0:
        return True
    if int(y) % 100 == 0:
        return False
    if int(y) % 4 == 0:
        return True
    else:
        return False


def invert_dic_df(dic, tablename=''):
    """
    Function that takes as input a dictionary of dataframes, and inverts the key of
    the dictionary with the columns headers of the dataframes

    :param dic:         dictionary of dataframes, with the same columns headers and the same index
    :param tablename:   string with the name of the table being processed (for the error msg)
    :returns:           dictionary of dataframes, with swapped headers
    """
    # keys are defined as the keys of the original dictionary, cols are the columns of the original dataframe
    # items are the keys of the output dictionary, i.e. the columns of the original dataframe    
    dic_out = {}
    # First, check that all indexes have the same length:
    index = dic[list(dic.keys())[0]].index
    for key in dic:
        if len(dic[key].index) != len(index):
            sys.exit('The indexes of the data tables "' + tablename + '" are not equal in all the files')

    # Then put the data in a panda Panel with minor orientation:
    panel = pd.Panel.fromDict(dic, orient='minor')
    # Display a warning if some items are missing in the original data:
    for item in panel.items:
        for key in dic.keys():
            if item not in dic[key].columns:
                print(
                    'The column "' + item + '" is not present in "' + key + '" for the "' + tablename + '" data. Zero '
                                                                                                        'will be assumed')
        dic_out[item] = panel[item].fillna(0)
    return dic_out


def get_ktoe_to_mwh(data, keys):
    """
    Function that converts ktoe to mwh
    :param data:    pd.DataFrame
    :param keys:    Column names where conversion should occur
    :return:        Data in MWh
    """
    for key in keys:
        data[key] = data[key] * 11630
    return data


def get_gwh_to_mwh(data, keys):
    """
    Function that converts gwh to mwh
    :param data:    pd.DataFrame
    :param keys:    Column names where conversion should occur
    :return:        Data in MWh
    """
    for key in keys:
        data[key] = data[key] * 1000
    return data


def make_timeseries(x=None, year=None, length=None, startdate=None, freq=None):
    """Convert numpy array to a pandas series with a timed index. Convenience wrapper around a datetime-indexed pd.DataFrame.

    Parameters:
        x: (nd.array) raw data to wrap into a pd.Series
        startdate: pd.datetime
        year: year of timeseries
        freq: offset keyword (e.g. 15min, H)
        length: length of timeseries
    Returns:
        pd.Series or pd.Dataframe with datetimeindex
    """

    if startdate is None:
        if year is None:
            logging.info('No info on the year was provided. Using current year')
            year = pd.datetime.now().year
        startdate = pd.datetime(year, 1, 1, 0, 0, 0)

    if x is None:
        if length is None:
            raise ValueError('The length or the timeseries has to be provided')
    else:  # if x is given
        length = len(x)
        if freq is None:
            # Shortcuts: Commonly used frequencies are automatically assigned
            if len(x) == 8760 or len(x) == 8784:
                freq = 'H'
            elif len(x) == 35040:
                freq = '15min'
            elif len(x) == 12:
                freq = 'm'
            else:
                raise ValueError('Input vector length must be 12, 8760 or 35040. Otherwise freq has to be defined')

    #enddate = startdate + pd.datetools.timedelta(seconds=_freq_to_sec(freq) * (length - 1) )
    date_list = pd.date_range(start=startdate, periods=length, freq=freq)
    if x is None:
        return pd.Series(np.nan, index=date_list)
    elif isinstance(x, (pd.DataFrame, pd.Series)):
        x.index = date_list
        return x
    elif isinstance(x, (np.ndarray, list)):
        if len(x.shape) > 1:
            return pd.DataFrame(x, index=date_list)
        else:
            return pd.Series(x, index=date_list)
    else:
        raise ValueError('Unknown type of data passed')

def clean_convert(x, force_timed_index=True, always_df=False, **kwargs):
    """Converts a list, a numpy array, or a dataframe to pandas series or dataframe, depending on the
    compatibility and the requirements. Designed for maximum compatibility.

    Arguments:
        x (list, np.ndarray): Vector or matrix of numbers. it can be pd.DataFrame, pd.Series, np.ndarray or list
        force_timed_index (bool): if True it will return a timeseries index
        year (int): Year that will be used for the index
        always_df (bool): always return a dataframe even if the data is one dimensional
        **kwargs: Exposes arguments of :meth:`make_timeseries`
    Returns:
        pd.Series: Timeseries

    """

    if isinstance(x, list):  # nice recursions
        return clean_convert(pd.Series(x), force_timed_index, always_df, **kwargs)

    elif isinstance(x, np.ndarray):
        if len(x.shape) == 1:
            return clean_convert(pd.Series(x), force_timed_index, always_df, **kwargs)
        else:
            return clean_convert(pd.DataFrame(x), force_timed_index, always_df, **kwargs)

    elif isinstance(x, pd.Series):
        if always_df:
            x = pd.DataFrame(x)
        if x.index.is_all_dates:
            return x
        else:  # if not datetime index
            if force_timed_index:
                logging.debug('Forcing Datetimeindex into passed timeseries.'
                              'For more accurate results please pass a pandas time-indexed timeseries.')
                return make_timeseries(x, **kwargs)
            else:  # does not require datetimeindex
                return x

    elif isinstance(x, pd.DataFrame):
        if x.shape[1] == 1 and not always_df:
            return clean_convert(x.squeeze(), force_timed_index, always_df, **kwargs)
        else:
            if force_timed_index and not x.index.is_all_dates:
                return make_timeseries(x, **kwargs)
            else:  # does not require datetimeindex
                return x
    else:
        raise ValueError(
            'Unrecognized Type. Has to be one of the following: pd.DataFrame, pd.Series, np.ndarray or list')


def reshape_timeseries(Load, x='dayofyear', y=None, aggfunc='sum'):
    """Returns a reshaped pandas DataFrame that shows the aggregated load for selected
    timeslices. e.g. time of day vs day of year

    Parameters:
        Load (pd.Series, np.ndarray): timeseries
        x (str): x axis aggregator. Has to be an accessor of pd.DatetimeIndex
         (year, dayoftime, week etc.)
        y (str): similar to above for y axis
    Returns:
        reshaped pandas dataframe according to x,y
    """

    # Have to convert to dataframe in order for pivottable to work
    # 1D, Dataframe
    a = clean_convert(Load.copy(), force_timed_index=True, always_df=True)
    a.name = 0
    if len(a.columns) > 1:
        raise ValueError('Works only with 1D')

    if x is not None:
        a[x] = getattr(a.index, x)
    if y is not None:
        a[y] = getattr(a.index, y)
    a = a.reset_index(drop=True)

    return a.pivot_table(index=x, columns=y,
                         values=a.columns[0],
                         aggfunc=aggfunc).T

def round_down(num, divisor):
    return num - (num%divisor)


#%% Countries used in the analysis
commons['PowerPools'] = {}


commons['PowerPools']['EAPP'] = ['Burundi', 'Djibouti', 'Egypt', 'Ethiopia', 'Eritrea', 'Kenya', 'Rwanda', 'Somalia',
                                 'Sudan', 'South Sudan', 'Tanzania', 'Uganda']
commons['PowerPools']['NAPP'] = ['Algeria', 'Libya', 'Morocco', 'Mauritania', 'Tunisia']
commons['PowerPools']['CAPP'] = ['Angola', 'Cameroon', 'Central African Republic', 'Republic of the Congo', 'Chad',
                                 'Gabon', 'Equatorial Guinea', 'Democratic Republic of the Congo']
commons['PowerPools']['WAPP'] = ['Benin', 'Burkina Faso', "Côte d'Ivoire", 'Gambia', 'Ghana', 'Guinea', 'Guinea-Bissau',
                                 'Liberia', 'Mali', 'Niger', 'Nigeria','Senegal', 'Sierra Leone', 'Togo']
commons['PowerPools']['SAPP'] = ['Botswana', 'Lesotho', 'Malawi', 'Mozambique', 'Namibia', 'South Africa', 'Swaziland',
                                 'Zambia', 'Zimbabwe']


def used_power_pools(power_pools):
    """
    returns list of countries from selected power pools
    :param power_pools:     list of power pools
    :return:                list of countries alpha2 codes
    """
    used = set()
    countries = []
    for p in power_pools:
        countries.extend(commons['PowerPools'][p])
    countries = [x for x in countries if x not in used and (used.add(x) or True)]
    countries = get_country_codes(countries)
    return countries


def alpha3_from_alpha2(alpha_2):
    """
    Returns alpha3 from alpha2 country codes
    :param alpha_2:     list of alpha2 country codes
    :return:            list of alpha3 country codes
    """
    alpha3 = []
    for z in alpha_2:
        alpha3.append(pycountry.countries.get(alpha_2=z).alpha_3)
    return alpha3

commons['coastal_countries'] = {}
commons['coastal_countries']['Africa'] = ['BJ', 'CD', 'MA', 'EG', 'LY', 'AO', 'SO', 'ZA', 'MZ', 'ER', 'NA', 'TZ', 'TN', 'DZ', 'GA',
                                          'NG', 'SD', 'MR', 'GH', 'KE', 'SN', 'CI', 'CM', 'SL', 'GW', 'GN', 'DJ', 'GQ',
                                          'GM', 'TG', 'LR', 'CG']
