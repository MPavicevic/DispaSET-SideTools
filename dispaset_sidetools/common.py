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
# Timestep
commons['TimeStep'] = '1h'

# DispaSET technologies:
commons['Technologies'] = ['COMC', 'GTUR', 'HDAM', 'HROR', 'HPHS', 'ICEN', 'PHOT', 'STUR', 'WTOF', 'WTON', 'CAES',
                           'BATS',
                           'BEVS', 'THMS', 'P2GS']
# List of renewable technologies:
commons['tech_renewables'] = ['WTON', 'WTOF', 'PHOT', 'HROR']
# List of storage technologies:
commons['tech_storage'] = ['HDAM', 'HPHS', 'BATS', 'BEVS', 'CAES', 'THMS']
# List of CHP types:
commons['types_CHP'] = ['extraction', 'back-pressure', 'p2h']
# DispaSET fuels:
commons['Fuels'] = ['BIO', 'GAS', 'HRD', 'LIG', 'NUC', 'OIL', 'PEA', 'SUN', 'WAT', 'WIN', 'WST', 'OTH', 'GEO']
# Ordered list of fuels for plotting (the first ones are negative):
commons['MeritOrder'] = ['Storage', 'FlowOut', 'NUC', 'LIG', 'HRD', 'BIO', 'GAS', 'OIL', 'PEA', 'WST', 'SUN', 'WIN',
                         'FlowIn', 'WAT']
# Colors associated with each fuel:
commons['colors'] = {'NUC': 'orange', 'LIG': 'brown', 'HRD': 'grey', 'BIO': 'darkgreen', 'GAS': 'lightcoral',
                     'OIL': 'chocolate', 'PEA': 'green', 'WST': 'dodgerblue', 'SUN': 'yellow', 'WIN': 'red',
                     'FlowIn': 'green', 'WAT': 'blue',
                     'Storage': 'blue', 'FlowOut': 'green'}
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
           'Tanzania': 'Tanzania, United Republic of',
           "Cote d'Ivoire": "Côte d'Ivoire",
           'Swaziland': 'Eswatini',
           'western Sahara': 'Western Sahara',
           'Santa Helena': 'Saint Helena, Ascension and Tristan da Cunha',
           'Reunion': 'Réunion'}
    zones = [dic.get(n, n) for n in zones]
    countries = {}
    for country in pycountry.countries:
        countries[country.name] = country.alpha_2
    codes = [countries.get(country, 'Unknown code') for country in zones]
    return codes


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
                    'The column "' + item + '" is not present in "' + key + '" for the "' + tablename + '" data. Zero will be assumed')
        dic_out[item] = panel[item].fillna(0)
    return dic_out
