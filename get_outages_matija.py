# -*- coding: utf-8 -*-
"""
Created on Mon Nov  5 07:45:46 2018

@author: Matija Pavičević
"""

from __future__ import division
import pandas as pd
import numpy as np
import os
import sys
import pickle
from common import mapping,outliers_vre,fix_na,make_dir,entsoe_types,commons
import chardet

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass
 
    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass
    return False

# Set year to get data
year = 2016
write_csv = True  

dtypes={'year':np.int16,
        'month':np.int16,
        'day':np.int16}

# Set folder with input data
folder_OUT = './entsoe/OutagesPU'
listdir_OUT = os.listdir(folder_OUT)
files_OUT = [folder_OUT + '/' + f for f in listdir_OUT if (f[:4] == str(year)) and (f[-4:] == '.csv')]
for f in files_OUT:
#    with open(f, 'rb') as fr:
#        encode = chardet.detect(fr.read())  # or readline if the file is large
#    Outages = pd.read_csv(f, encoding=encode['encoding'], header=0)
    data = pd.read_csv(f,header=[0],index_col=None,encoding='utf-16',low_memory=False,error_bad_lines=False,sep='\t',dtype=dtypes)
#    data.index = pd.to_datetime(data.DateTime)
#    zones = list(data.MapCode.unique())

#As we compute every hour, if the minutes are not set to 0, the program does not compute the Outage
data['StartTime'] = pd.to_datetime(data['StartTS'])
data['StartTime'].minute = 0

data['EndTime'] = pd.to_datetime(data['EndTS'])
data['EndTime'].minute = 0

## Filter only Active outages
data = data[data['Status']=='Active']

# Set time series index for new dataframe
DateRange = pd.date_range(start=str(year) + '-01-01', end= str(year) + '-12-31 23:00', freq='H')

# Grouping into the same country regions of the same country
mapping = [('IT_North','IT'),('IT_SUD','IT'),('IT_PRGP','IT'),('IT_BRNN','IT'),('IT_SARD','IT'),
			('IT_ROSN','IT'),('IT_CNOR','IT'),('IT_FOGN','IT'),('IT_CSUD','IT'),( 'IT_SICI','IT'),
			('NO1','NO'),('NO2','NO'),('NO3','NO'),('NO4','NO'),('NO5','NO')
			,('SE1','SE'),('SE2','SE'),('SE3','SE'),('SE4','SE'),('DK1','DK'),('DK2','DK'),
			('DE_AT_LU','DE'),('DE_TenneT_GER','DE'),('DE_TransnetBW','DE'),('DE_50HzT','DE'),('DE_Amprion','DE'),
            ('GB','UK'),('GR','EL')]
for k, v in mapping:
    data = data.replace(k, v)
# Replacing the fuel types by the one used in Dispa Set
				#Not considering Marine, PEAT
mapping = [('Fossil Oil shale ','_STUR_OIL'),( 'Nuclear ', '_STUR_NUC'),('Other ','_STUR_OTH'),
			( 'Fossil Gas ','_COMC_GAS'),('Fossil Peat ','N/A'),( 'Hydro Pumped Storage ','_HPHS_WAT'),
			('Hydro Run-of-river and poundage ','_HROR_WAT'),('Wind Onshore ','_WTON_WIN'),
			( 'Fossil Brown coal/Lignite ', '_STUR_LIG'),('Wind Offshore ','_WTOF_WIN'),
			('Biomass ', '_STUR_BIO'),('Marine ','N/A'),('Hydro Water Reservoir ','_HPHS_WAT'),
			('Fossil Oil ','_STUR_OIL'),( 'Fossil Hard coal ','_STUR_HRD')]
for k, v in mapping:
    data = data.replace(k, v)

# List all countries with available outages
data = data[data['ProdType']!='N/A']
countries = list(set(data['MapCode']))
fuels = list(set(data['ProdType']))

#for each type of fuel compute the outage factors
for c in countries:
	#Select a country
    df_country = pd.DataFrame(index=DateRange)
    dataCountry = data[data['MapCode'] == c]
    for f in fuels[1:]:
         fuelName = c + f
         newData = dataCountry[dataCountry['ProdType'] == f]
         plants = list(set(newData['UnitName']))
         df_fuel = pd.Series(np.zeros((len(DateRange),)),index=DateRange, name = fuelName)
         i = 1
         InstalledCapaFuel = 0
         for pp in plants:
             print(i," out of ", len(plants), "plants")
             plantdata = newData[newData['UnitName'] == pp]
             InstalledCapa = sorted(plantdata['InstalledGenCapacity'].unique())
             InstalledCapaFuel += float(InstalledCapa[0])
             plantseries = pd.Series(float(InstalledCapa[0])*np.ones((len(DateRange),)),index=DateRange, name = fuelName)
             plantNormalSeries = pd.Series(float(InstalledCapa[0])*np.ones((len(DateRange),)),index=DateRange, name = fuelName)
             for Start in plantdata['StartTime']:
                 temp = plantdata[plantdata['StartTime']==Start]
                 endtimes = temp['EndTime']
                 #Again we have to "erase the minutes"
                 Start = Start.replace(minute = 0)
                 for End in endtimes:
                     individual_plantdata = temp[temp['EndTime']==End]
                     ActualGen = individual_plantdata['AvailableCapacity'].unique()
                     #Sometimes mistakes are encoded in the ENTSOE file
                     if is_number(ActualGen[0]):
                         if (float(ActualGen[0]) <=0):
                             ActualGen[0] = 0
                             #Again we have to "erase the minutes"
                             End = End.replace(minute = 0)
                             NewDateRange = pd.date_range(start=Start, end=End, freq='H')
                             Tempseries = pd.Series(float(ActualGen[0])*np.ones((len(NewDateRange),)),index=NewDateRange, name = fuelName)
                             plantseries.update(Tempseries)
                				#df_fuel is the effective loss in generation
                 df_fuel = (df_fuel - plantseries + plantNormalSeries)
                 i = i+1
#         Nunits = load_country['Nunits']
#         Nunits = Nunits[Nunits.index==fuelName]
         df_fuel = df_fuel/InstalledCapaFuel
#         if df_fuel.max()>1 :
#             while(1):
#                 print( "wrong")
         df_country = pd.concat([df_country, df_fuel], axis=1)
    folder = './Database/OutageFactors/'
    file = str(year) + '.csv'
    fileout = folder + c + '/' + file
    make_dir(folder)
    make_dir(folder + c + '/')
    df_country.to_csv(fileout,encoding='utf-8')
             


