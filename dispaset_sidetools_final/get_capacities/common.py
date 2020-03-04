# -*- coding: utf-8 -*-
"""
Created on Sat Dec 23 20:41:12 2017
 
@author: sylvain
"""
from __future__ import division
import numpy as np
import pandas as pd
import os,sys
import datetime
import itertools


#%%

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

#%%

'''
Dictionary with the common variable definitions
to be used in Dispa-SET
'''
commons={}
# Timestep
commons['TimeStep'] = '1h'

# DispaSET technologies:
commons['Technologies'] = ['COMC', 'GTUR', 'HDAM', 'HROR', 'HPHS', 'ICEN', 'PHOT', 'STUR', 'WTOF', 'WTON', 'CAES', 'BATS',
                'BEVS', 'THMS', 'P2GS']
# List of renewable technologies:
commons['tech_renewables'] = ['WTON', 'WTOF', 'PHOT', 'HROR']
# List of storage technologies:
commons['tech_storage'] = ['HDAM', 'HPHS', 'BATS', 'BEVS', 'CAES', 'THMS']
# List of CHP types:
commons['types_CHP'] = ['extraction','back-pressure', 'p2h']
# DispaSET fuels:
commons['Fuels'] = ['BIO', 'GAS', 'HRD', 'LIG', 'NUC', 'OIL', 'PEA', 'SUN', 'WAT', 'WIN', 'WST', 'OTH','GEO']
# Ordered list of fuels for plotting (the first ones are negative):
commons['MeritOrder'] = ['Storage','FlowOut','NUC', 'LIG', 'HRD', 'BIO', 'GAS', 'OIL', 'PEA', 'WST', 'SUN', 'WIN', 'FlowIn', 'WAT']
# Colors associated with each fuel:
commons['colors'] = {'NUC': 'orange', 'LIG': 'brown', 'HRD': 'grey', 'BIO': 'darkgreen', 'GAS': 'lightcoral', 
       'OIL': 'chocolate','PEA':'green', 'WST': 'dodgerblue', 'SUN': 'yellow', 'WIN': 'red', 'FlowIn': 'green', 'WAT': 'blue', 
       'Storage': 'blue','FlowOut': 'green'}
# Hatches associated with each fuel (random):
hatches = itertools.cycle(['x', '//', '\\', '/'])
commons['hatches'] = {}
for x in commons['colors']:
    commons['hatches'][x] = next(hatches)
          


#%%

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
        mapping['iso2entsoe'][mapping['original'][key]].append( key )
    else:
        mapping['iso2entsoe'][mapping['original'][key]] = [key]    


#%%

def outliers():
    '''
    This function defines time periods for each country in which the data does not 
    seem valid. This data will be considered as "na"
    '''
    ranges = {}
    outliers = {}
    #outliers = {u'BE': [], u'FR': [], u'BG': [], u'DK': [(735612.53820901422, 735612.62590625312)], u'HR': [], u'DE': [], u'HU': [], u'FI': [], u'NL': [(735907.32921977597, 735907.41733813006), (735602.99937646941, 735605.10796213965)], u'PT': [(735598.6295930316, 735619.14557657496)], u'NO': [(735745.8264080761, 735746.24270383955), (735895.9517985431, 735896.07509171346), (735926.08301755099, 735927.05576440226), (735869.41674146405, 735869.50025776995)], u'LV': [], u'LT': [(735785.82905850408, 735786.04482155212), (735798.66518474743, 735798.7505921725), (735935.94665249111, 735936.2295015289), (735935.22139854799, 735935.46798488859), (735938.96370889456, 735941.04518771137), (735873.19804395817, 735873.38914837223)], u'LU':  [(735898.47441307071, 735898.55872384156)], u'RO': [], u'PL': [], u'CH': [(735787.71925159334, 735791.17127904913), (735838.86978038121, 735842.08900132135), (735916.27196352172, 735918.13985505234)], u'GR': [], u'EE': [], u'IT': [], u'CZ': [],  u'GB': [(735685.99277645408, 735686.09793827578), (735716.38690001634, 735716.59087768791), (735760.48796047701, 735760.72838215914), (735872.51793561061, 735872.63207756763), (735875.49432917498, 735875.58696793742), (735921.56994357647, 735921.7440045228)], u'IE': [], u'ES': [(735598.62651070219, 735619.07704007719)], u'ME': [(735795.05120633147, 735797.10911439522), (735800.03732719063, 735802.10430092853), (735877.46725129429, 735879.1132151183), (735906.02992733684, 735907.12361028313)], u'RS': [(735895.9068327985, 735896.10482712497)], u'MK': [(735959.00664555351, 735959.23999600962)], u'SK': [], u'SI': [], u'SE': [], u'AT': [(735930.04036569176, 735933.05850997614), (735956.07027365128, 735958.12056654855), (735960.49794897414, 735962.58813083824)]}
    
    regions = mapping['original']
    
    ranges['2015'] = {u'AT': [['2015-11-28 00:58:07.595768272', '2015-12-01 01:24:15.261938272'],
              ['2015-12-24 01:41:11.643470228', '2015-12-26 02:53:36.949794440'],
              ['2015-12-28 11:57:02.791365536', '2015-12-30 14:06:54.504423736']],
             u'BE': [],
             u'BG': [],
             u'CH': [['2015-07-08 17:15:43.337664752', '2015-07-12 04:06:38.509844764'],
              ['2015-08-28 20:52:29.024936556', '2015-09-01 02:08:09.714164660'],
              ['2015-11-14 06:31:37.648276760', '2015-11-16 03:21:23.476522564']],
             u'CZ': [],
             u'DE': [],
             u'DK': [['2015-01-14 12:55:01.258828863', '2015-01-14 15:01:18.300269320']],
             u'EE': [],
             u'ES': [['2014-12-31 15:02:10.524669216', '2015-01-21 01:50:56.262668967']],
             u'FI': [],
             u'FR': [],
             u'GB': [['2015-03-28 23:49:35.885632261', '2015-03-29 02:21:01.867027358'],
              ['2015-04-28 09:17:08.161411734', '2015-04-28 14:10:51.832235232'],
              ['2015-06-11 11:42:39.785213694', '2015-06-11 17:28:52.218549772'],
              ['2015-10-01 12:25:49.636756628', '2015-10-01 15:10:11.501843108'],
              ['2015-10-04 11:51:50.040718316', '2015-10-04 14:05:14.029792696'],
              ['2015-11-19 13:40:43.125006928', '2015-11-19 17:51:21.990769880']],
             u'GR': [],
             u'HR': [],
             u'HU': [],
             u'IE': [],
             u'IT': [],
             u'LT': [['2015-07-06 19:53:50.654752626', '2015-07-07 01:04:32.582102938'],
              ['2015-07-19 15:57:51.962177752', '2015-07-19 18:00:51.163703576'],
              ['2015-12-03 22:43:10.775232016', '2015-12-04 05:30:28.932096812'],
              ['2015-12-03 05:18:48.834546356', '2015-12-03 11:13:53.894373848'],
              ['2015-12-06 23:07:44.448489996', '2015-12-09 01:05:04.218262060'],
              ['2015-10-02 04:45:10.997985676', '2015-10-02 09:20:22.419360280']],
             u'LU': [['2015-10-27 11:23:09.289309460', '2015-10-27 13:24:33.739910872']],
             u'LV': [],
             u'ME': [['2015-07-16 01:13:44.227038770', '2015-07-18 02:37:07.483747156'],
              ['2015-07-21 00:53:45.069270284', '2015-07-23 02:30:11.600225418'],
              ['2015-10-06 11:12:50.511826872', '2015-10-08 02:43:01.786220892'],
              ['2015-11-04 00:43:05.721903296', '2015-11-05 02:57:59.928462580']],
             u'MK': [['2015-12-27 00:09:34.175823480', '2015-12-27 05:45:35.655231404']],
             u'NL': [['2015-11-05 07:54:04.588644056', '2015-11-05 10:00:58.014437556'],
              ['2015-01-04 23:59:06.126956865', '2015-01-07 02:35:27.928865701']],
             u'NO': [['2015-05-27 19:50:01.657775044', '2015-05-28 05:49:29.611737504'],
              ['2015-10-24 22:50:35.394123940', '2015-10-25 01:48:07.924042716'],
              ['2015-11-24 01:59:32.716405616', '2015-11-25 01:20:18.044355512'],
              ['2015-09-28 10:00:06.462494284', '2015-09-28 12:00:22.271323576']],
             u'PL': [],
             u'PT': [['2014-12-31 15:06:36.837930009', '2015-01-21 03:29:37.816076204']],
             u'RO': [],
             u'RS': [['2015-10-24 21:45:50.353790448', '2015-10-25 02:30:57.063597812']],
             u'SE': [],
             u'SI': [],
             u'SK': []
             }
    
    ranges['2016'] = {
                 u'AT': [],
                 u'BE': [],
                 u'BG': [],
                 u'CH': [],
                 u'CZ': [],
                 u'DE': [['2016-04-03 04:44:33.364333440', '2016-04-03 07:27:55.411679592']],
                 u'DK': [],
                 u'EE': [['2016-06-19 05:33:09.179889856', '2016-06-19 12:05:51.793706416']],
                 u'ES': [],
                 u'FI': [],
                 u'FR': [],
                 u'GB': [],
                 u'GR': [],
                 u'HR': [],
                 u'HU': [],
                 u'IE': [],
                 u'IT': [],
                 u'LT': [],
                 u'LU': [],
                 u'LV': [],
                 u'ME': [['2016-08-30 01:06:50.817502808', '2016-09-01 01:51:45.165189872'],
                  ['2016-08-15 23:41:50.950183872', '2016-08-18 02:22:44.123151448'],
                  ['2016-12-31 12:39:45.350549960', '2017-01-01 00:52:48.896340200']],
                 u'MK': [['2016-04-22 17:23:23.638618064', '2016-04-22 20:25:52.399840952']],
                 u'NL': [],
                 u'NO': [['2016-05-02 14:20:48.800733312', '2016-05-04 10:57:31.576487344'],
                  ['2016-10-29 22:57:22.070775472', '2016-10-30 01:34:27.116294056']],
                 u'PL': [],
                 u'PT': [],
                 u'RO': [],
                 u'RS': [['2016-10-29 21:54:32.052560', '2016-10-30 05:22:44.849118144']],
                 u'SE': [],
                 u'SI': [],
                 u'SK': []
                 }
    

    # concatenate the differant ranges:
    for key in regions:
        tmp = []
        for y in ranges:
            if key in ranges[y] and len(ranges[y][key])>0:
                tmp += ranges[y][key]
        if len(tmp) > 0:
            outliers[key] = tmp
                
            
    
    return outliers


def outliers_vre():
    '''
    This function defines time periods for each country in which the data does not 
    seem valid. This data will be considered as "na"
    '''
    ranges = {}
    outliers = {}
    #outliers = {u'BE': [], u'FR': [], u'BG': [], u'DK': [(735612.53820901422, 735612.62590625312)], u'HR': [], u'DE': [], u'HU': [], u'FI': [], u'NL': [(735907.32921977597, 735907.41733813006), (735602.99937646941, 735605.10796213965)], u'PT': [(735598.6295930316, 735619.14557657496)], u'NO': [(735745.8264080761, 735746.24270383955), (735895.9517985431, 735896.07509171346), (735926.08301755099, 735927.05576440226), (735869.41674146405, 735869.50025776995)], u'LV': [], u'LT': [(735785.82905850408, 735786.04482155212), (735798.66518474743, 735798.7505921725), (735935.94665249111, 735936.2295015289), (735935.22139854799, 735935.46798488859), (735938.96370889456, 735941.04518771137), (735873.19804395817, 735873.38914837223)], u'LU':  [(735898.47441307071, 735898.55872384156)], u'RO': [], u'PL': [], u'CH': [(735787.71925159334, 735791.17127904913), (735838.86978038121, 735842.08900132135), (735916.27196352172, 735918.13985505234)], u'GR': [], u'EE': [], u'IT': [], u'CZ': [],  u'GB': [(735685.99277645408, 735686.09793827578), (735716.38690001634, 735716.59087768791), (735760.48796047701, 735760.72838215914), (735872.51793561061, 735872.63207756763), (735875.49432917498, 735875.58696793742), (735921.56994357647, 735921.7440045228)], u'IE': [], u'ES': [(735598.62651070219, 735619.07704007719)], u'ME': [(735795.05120633147, 735797.10911439522), (735800.03732719063, 735802.10430092853), (735877.46725129429, 735879.1132151183), (735906.02992733684, 735907.12361028313)], u'RS': [(735895.9068327985, 735896.10482712497)], u'MK': [(735959.00664555351, 735959.23999600962)], u'SK': [], u'SI': [], u'SE': [], u'AT': [(735930.04036569176, 735933.05850997614), (735956.07027365128, 735958.12056654855), (735960.49794897414, 735962.58813083824)]}
    
    regions = mapping['original']
    
    ranges['2015'] = {u'RO': [['2015-02-19 00:00:00', '2015-02-21 00:00:00'],['2015-03-29 12:00:00', '2015-03-30 12:00:00']]}
    
    ranges['2016'] = {u'AT': [['2016-07-17 19:00:00', '2016-07-18 23:00:00']],u'CH': [['2016-01-08 20:01:39.532733116', '2016-01-09 03:01:31.746116052']],  u'NO': [['2016-10-29 21:56:06.303014384', '2016-10-30 01:25:01.613557712']], u'IT': [['2016-10-27 03:39:15.567116664', '2016-10-31 19:04:45.504684224']]}
                 
    

    # concatenate the differant ranges:
    for key in regions:
        tmp = []
        for y in ranges:
            if key in ranges[y] and len(ranges[y][key])>0:
                tmp += ranges[y][key]
        if len(tmp) > 0:
            outliers[key] = tmp
                
            
    
    return outliers


#%%
def fix_na(series,fillzeros=True,verbose=True,name='',Nstd=4,outliers=None):
    '''
    Function that fills zero and n/a values from a time series by interpolating
    from the same hours in the previous and next days
    
    :param series:  Pandas Series with proper datetime index
    :param fillzeros:   If true, also interpolates zero values in the time series
    :param verbose:     If true, prints information regarding the number of fixed data points
    :param name:        String with the name of the time series, for the display massage
    :param Nstd:        Number of standard deviations to use as threshold for outlier detection
    :param outliers:    List of lists with the start and stop periods to be discarded
    
    :returns:   Same series with filled nan values
    '''
    longname = name + ' ' + str(series.index.freq)
    # turn all zero values into na:
    if fillzeros:
        series[series==0] = np.nan
    # check for outliers:
    toohigh = series>series.mean()+Nstd*series.std()
    if np.sum(toohigh) > 0:
        print('Time series "' + longname + '": ' + str(np.sum(toohigh)) + ' data points unrealistically high. They will be fixed as well')
        series[toohigh] = np.nan
    # write na in all the locations defined as "outlier"
    if outliers:
        count=0
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
            
        right  =np.nan
        idxright = idx + datetime.timedelta(days=1)
        while np.isnan(right) and idxright in series.index:
            if np.isnan(series[idxright]):
                idxright = idxright + datetime.timedelta(days=1)   
            else:
                right = series[idxright]
            
        if (not np.isnan(left)) and (not np.isnan(right)):
            series[idx] = (left + right)/2
        elif (not np.isnan(left)) and np.isnan(right):
            series[idx] = left
        elif np.isnan(left) and (not np.isnan(right)):
            series[idx] = right
        else:
            print('ERROR : no valid data found to fill the data point ' + str(idx))
        
    return series

def make_dir(path):
    if not os.path.isdir(path):
        os.mkdir(path)

def invert_dic_df(dic,tablename=''):
    """
    Function that takes as input a dictionary of dataframes, and inverts the key of
    the dictionary with the columns headers of the dataframes

    :param dic: dictionary of dataframes, with the same columns headers and the same index
    :param tablename: string with the name of the table being processed (for the error msg)
    :returns: dictionary of dataframes, with swapped headers
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
                print('The column "' + item + '" is not present in "' + key + '" for the "' + tablename + '" data. Zero will be assumed')
        dic_out[item] = panel[item].fillna(0)
    return dic_out






