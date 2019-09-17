# -*- coding: utf-8 -*-
"""
Created on Tue Sep 17 10:53:00 2019

@author: Matija Pavičević, KU Leuven
"""


# System imports
from __future__ import division
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
import sys
import pickle
# Third-party imports
# Local source tree imports
from dispaset_sidetools.common import mapping,outliers_vre,fix_na,make_dir,entsoe_types,commons

input_folder = '../../Inputs/'  # Standard input folder
output_folder = '../../Outputs/'# Standard output folder

data = pd.read_excel(input_folder + '/NTCCapacities/NTC_2040.xlsx')

data['Unnamed: 0'] = data['Unnamed: 0'].str.replace('LUB','LU')
data['Unnamed: 0'] = data['Unnamed: 0'].str.replace('LUG','LU')
data['Unnamed: 0'] = data['Unnamed: 0'].str.replace('LUF','LU')
data['Unnamed: 0'] = data['Unnamed: 0'].str.replace('LUv','LU')
data['Unnamed: 0'] = data['Unnamed: 0'].str.replace('PLE','PL')
data['Unnamed: 0'] = data['Unnamed: 0'].str.replace('PLI','PL')
data['Unnamed: 0'] = data['Unnamed: 0'].str.replace('DEkf','DE')
data['Unnamed: 0'] = data['Unnamed: 0'].str.replace('DKe','DK')
data['Unnamed: 0'] = data['Unnamed: 0'].str.replace('DKw','DK')
data['Unnamed: 0'] = data['Unnamed: 0'].str.replace('DKkf','DK')
data['Unnamed: 0'] = data['Unnamed: 0'].str.replace('NOs','NO')
data['Unnamed: 0'] = data['Unnamed: 0'].str.replace('NOn','NO')
data['Unnamed: 0'] = data['Unnamed: 0'].str.replace('NOm','NO')
data['Unnamed: 0'] = data['Unnamed: 0'].str.replace('SE1','SE')
data['Unnamed: 0'] = data['Unnamed: 0'].str.replace('SE2','SE')
data['Unnamed: 0'] = data['Unnamed: 0'].str.replace('SE3','SE')
data['Unnamed: 0'] = data['Unnamed: 0'].str.replace('SE4','SE')
data['Unnamed: 0'] = data['Unnamed: 0'].str.replace('GB','UK')
data['Unnamed: 0'] = data['Unnamed: 0'].str.replace('GR','EL')
data['Unnamed: 0'] = data['Unnamed: 0'].str.replace('FRc','FR')
data['Unnamed: 0'] = data['Unnamed: 0'].str.replace('ITCO','IT')
data['Unnamed: 0'] = data['Unnamed: 0'].str.replace('ITn','IT')
data['Unnamed: 0'] = data['Unnamed: 0'].str.replace('ITsar','IT')
data['Unnamed: 0'] = data['Unnamed: 0'].str.replace('ITsic','IT')
data['Unnamed: 0'] = data['Unnamed: 0'].str.replace('ITs','IT')
data['Unnamed: 0'] = data['Unnamed: 0'].str.replace('NI','IE')
data['Unnamed: 0'] = data['Unnamed: 0'].str.replace('-',' -> ')

zones1 = list(data['Unnamed: 0'].str[:2].unique())
data.set_index(data['Unnamed: 0'],inplace=True)

data = data.groupby(data.index).sum()

data['Reverse'] = data.index.str[6:] + ' -> ' + data.index.str[:2]
zones2 = list(data['Reverse'].str[:2].unique())

in_first = set(zones1)
in_second = set(zones2)
in_second_but_not_in_first = in_second - in_first
zone = zones1 + list(in_second_but_not_in_first)

for z in zone:
    data.drop(data[(data.index.str[6:] == z) & (data.index.str[:2] == z)].index, inplace = True)

data.drop(columns=['Unnamed: 0'],inplace=True)
data.drop(index=['Border'],inplace=True)
#data.reset_index(inplace=True)

def get_NTC(column1,column2,index2):
    ntc = pd.DataFrame(data[column1])
    ntc_2 = pd.DataFrame(data[column2])
    ntc_2.columns= [column1]
    ntc_2.set_index(data[index2],inplace=True)
    ntc = ntc.append(ntc_2)
    return ntc

column1 = 'NTC 2020'
column2 = 'Unnamed: 2'
index2 = 'Reverse'
ntc_2020 = get_NTC(column1,column2,index2)

column1 = 'NTC 2027'
column2 = 'Unnamed: 4'
ntc_2027 = get_NTC(column1,column2,index2)

column1 = 'NTC ST2040'
column2 = 'Unnamed: 6'
ntc_2040_ST = get_NTC(column1,column2,index2)

column1 = 'NTC DG2040'
column2 = 'Unnamed: 8'
ntc_2040_DG = get_NTC(column1,column2,index2)

column1 = 'NTC GCA2040'
column2 = 'Unnamed: 10'
ntc_2040_GCA = get_NTC(column1,column2,index2)

ntc = pd.concat([ntc_2020,ntc_2027,ntc_2040_GCA],axis=1)
delta = ntc.pct_change(axis='columns')
delta.replace([np.inf, -np.inf,np.nan], 0, inplace=True)
delta['mean'] = 7/20*delta['NTC 2027'] + 13/20*delta['NTC GCA2040'] 

ntc_2050 = pd.DataFrame(ntc_2040_GCA['NTC GCA2040'] + ntc_2040_GCA['NTC GCA2040'] * delta['mean'])
ntc_2050 = ntc_2050.round(0).astype(int)
ntc_2050 = ntc_2050.T

cols = list(ntc_2050.columns)

year = 2016
data2 = pd.DataFrame(ntc_2050,index=pd.date_range(start=str(year) + '-01-01', end= str(year) + '-12-31 23:00', freq='H'))
data2 = data2.fillna(1)

data2 = pd.DataFrame(data2.values*ntc_2050.values, columns=data2.columns, index=data2.index)

def write_csv_files(filename,data,write_csv=None):
    '''
    Function that generates .csv files in the Output/Database/PowerPlants/ folder
    :power_plant_filename:      clustered for example (has to be a string)
    :units:                     allunits for example
    '''
    filename = filename + '.csv'
    if write_csv == True:
        make_dir(output_folder + 'Database')
        folder = output_folder + 'Database/DayAheadNTC/'
        make_dir(folder)
        folder = folder + '/1h/'
        make_dir(folder)
        data.to_csv(folder + '/' + filename)     
    else:
        print('[WARNING ]: '+'WRITE_CSV_FILES = False, unable to write .csv files')

write_csv_files('NTC_2050',data2,write_csv=True)
