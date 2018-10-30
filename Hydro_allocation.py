# -*- coding: utf-8 -*-
"""
Created on Mon Oct 29 14:53:06 2018

@author: Matija Pavičević
"""

from __future__ import division
import pandas as pd
import numpy as np
import os
import sys
import pickle
from common import mapping,outliers_vre,fix_na,make_dir,entsoe_types,commons

# Set year to get data
year = 2016
write_csv = True  

# Folders with input data
folder_CBF = './Database/CrossBorderFlows/1h'
listdir_CBF = os.listdir(folder_CBF)
files_CBF = [folder_CBF + '/' + f for f in listdir_CBF if (f[:4] == str(year)) and (f[-4:] == '.csv')]
for f in files_CBF:
    CrossBorderFlows = pd.read_csv(f, index_col=0)

for c in mapping['entsoe2dispa']:
    file_TLV = './Database/TotalLoadValue/'+ c + '/1h/' + str(year) + '.csv'
   
    if os.path.isfile(file_TLV):
        TotalLoadValue = pd.read_csv(file_TLV, index_col=0, header = None, names = c) 
        
    else:
        print('No Load file found for country ' + c + '. The Total Load Value cannot be imported')
        continue




