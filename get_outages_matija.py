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
## ENTSOE Outages
folder_OUT = './entsoe/OutagesPU'
listdir_OUT = os.listdir(folder_OUT)
files_OUT = [folder_OUT + '/' + f for f in listdir_OUT if (f[:4] == str(year)) and (f[-4:] == '.csv')]
data = pd.DataFrame()
for f in files_OUT:
    data_temp = pd.read_csv(f,header=[0],index_col=None,encoding='utf-16',low_memory=False,error_bad_lines=False,sep='\t',dtype=dtypes)
    data = data.append(data_temp,ignore_index=True)

## Dispa power plants
folder_units = 'Database/PowerPlants/'
allunits = {}
for c in mapping['dispa2entsoe']:
    file = folder_units + c + '/' + 'clustered.csv'
    if os.path.isfile(file):
        units = pd.read_csv(file)
        units = units[(units['Fuel']!='WAT') & (units['Fuel']!='WIN') & (units['Fuel']!='SUN')]
        allunits[c] = units
    else:
        print('No Power plant data for country ' + c + ' , no outages will be computed')
        continue

#As we compute every hour, if the minutes are not set to 0, the program does not compute the Outage
data['StartTime'] = pd.to_datetime(data['StartTS'])
data['StartTime'].minute = 0
data['EndTime'] = pd.to_datetime(data['EndTS'])
data['EndTime'].minute = 0

# Calculate reduced capacities
data['ReducedCapacity'] = data['AvailableCapacity']-data['InstalledGenCapacity']

## Filter only Active outages
data = data[data['Status']=='Active']

# Filter outages that are not related to powerplants and/or are missing input data
data = data.drop(data[data['ReducedCapacity']>=0].index)

# Set time series index for new dataframe
DateRange = pd.date_range(start=str(year) + '-01-01', end= str(year) + '-12-31 23:00', freq='H')

# Grouping into the same country regions of the same country
mapping_country = [('IT_North','IT'),
           ('IT_SUD','IT'),
           ('IT_PRGP','IT'),
           ('IT_BRNN','IT'),
           ('IT_SARD','IT'),
		   ('IT_ROSN','IT'),
           ('IT_CNOR','IT'),
           ('IT_FOGN','IT'),
           ('IT_CSUD','IT'),
           ('IT_SICI','IT'),
           ('NO1','NO'),
           ('NO2','NO'),
           ('NO3','NO'),
           ('NO4','NO'),
           ('NO5','NO'),
           ('SE1','SE'),
           ('SE2','SE'),
           ('SE3','SE'),
           ('SE4','SE'),
           ('DK1','DK'),
           ('DK2','DK'),
           ('DE_AT_LU','DE'),
           ('DE_TenneT_GER','DE'),
           ('DE_TransnetBW','DE'),
           ('DE_50HzT','DE'),
           ('DE_Amprion','DE'),
           ('GB','UK'),
           ('GR','EL')]
for k, v in mapping_country:
    data = data.replace(k, v)

# Replacing the fuel types by the one used in Dispa Set
#Not considering Marine, PEAT
mapping_fuel = [('Fossil Oil shale ','_STUR_OIL'),
           ('Nuclear ', '_STUR_NUC'),
           ('Other ','_STUR_OTH'),
		   ('Fossil Gas ','_COMC_GAS'),
           ('Fossil Peat ','N/A'),
           ('Hydro Pumped Storage ','_HPHS_WAT'),
           ('Hydro Run-of-river and poundage ','_HROR_WAT'),
           ('Wind Onshore ','_WTON_WIN'),
           ('Fossil Brown coal/Lignite ', '_STUR_LIG'),
           ('Wind Offshore ','_WTOF_WIN'),
           ('Biomass ', '_STUR_BIO'),
           ('Marine ','N/A'),
           ('Hydro Water Reservoir ','_HPHS_WAT'),
           ('Fossil Oil ','_STUR_OIL'),
           ('Fossil Hard coal ','_STUR_HRD'),
           ('Fossil Waste ','_STUR_WST'),
           ('Fossil Gas Stur ','_STUR_GAS'),
           ('Fossil Gas Gtur ','_GTUR_GAS'),
           ('Fossil Gas Icen ','_ICEN_GAS')]
for k, v in mapping_fuel:
    data = data.replace(k, v)

# List all countries with available outages
data = data[(data['AreaTypeCode']!='CTA') & (data['ProdType']!='_HDAM_WAT') & (data['ProdType']!='_HPHS_WAT') & (data['ProdType']!='_HROR_WAT') & (data['ProdType']!='_WTOF_WIN') & (data['ProdType']!='_WTON_WIN') & (data['ProdType']!='N/A')]
countries = list(set(data['MapCode']))

# Crate Outage factors directory
folder = './Database/OutageFactors/'
file_outages = str(year) + '.csv'

#for each type of fuel compute the outage factors
allunits_outage = {}
singleunit_actual_capacity = []
for c in mapping['dispa2entsoe']:
    #Select a country:
    df_country = pd.DataFrame(index=DateRange)
    data_country = data[data['MapCode'] == c]
    # same as before check that country is present in the database
    file = folder_units + c + '/' + 'clustered.csv'
    if os.path.isfile(file):
        allunits_name = allunits[c]['Unit']
        allunits_power = allunits[c][['Unit','PowerCapacity','Nunits']].set_index('Unit')
        allunits_power = allunits_power['PowerCapacity']*allunits_power['Nunits']
        allunits_power = allunits_power.transpose()
        allunits_country = pd.DataFrame(np.ones((len(DateRange),len(allunits[c]))),index=DateRange, columns=allunits_name)
        allunits_capacity = pd.DataFrame(allunits_country.values*allunits_power.values, columns=allunits_country.columns, index=allunits_country.index)
        for f in allunits_name:
            f = f[2:]
            fuelName = c + f
            singleunit_capacity = allunits_capacity[fuelName]
            df_fuel = pd.Series(np.ones((len(DateRange),)),index=DateRange, name = fuelName)
            newData = data_country[data_country['ProdType'] == f]
            plantseries = pd.Series(np.zeros((len(DateRange),)),index=DateRange, name = fuelName)
            for Start in newData['StartTime']:
                temp = newData[newData['StartTime']==Start]
                endtimes = temp['EndTime']
                # Resetting the minutes to 0
                Start = Start.replace(minute = 0)
                for End in endtimes:
                    individual_plantdata = temp[temp['EndTime']==End]
                    ReducedGen = individual_plantdata['ReducedCapacity'].unique()
                    # Resetting the minutes to 0
                    End = End.replace(minute = 0)
                    NewDateRange = pd.date_range(start=Start, end=End, freq='H')
                    Tempseries = pd.Series(float(ReducedGen[0])*np.ones((len(NewDateRange),)),index=NewDateRange, name = fuelName)
                    plantseries.update(Tempseries)
                    # Calculate actual available capacity
                    singleunit_actual_capacity = singleunit_capacity + plantseries
            # Update actuall capacities of all units
            allunits_capacity.update(singleunit_actual_capacity)
#            print('unit ' + fuelName + ' updated')
        outage = pd.DataFrame(allunits_country.values - allunits_capacity.values/allunits_power.values, columns=allunits_country.columns, index=allunits_country.index)
        allunits_outage[c] = pd.DataFrame(allunits_country.values - allunits_capacity.values/allunits_power.values, columns=allunits_country.columns, index=allunits_country.index)
        # populate data in .csv files            
        fileout = folder + c + '/' + file_outages
        make_dir(folder)
        make_dir(folder + c + '/')
        outage.to_csv(fileout,encoding='utf-8')  
        print('Outage Factors for ' + c + ' created')              
        # Check if Outage factors are > than 1
        for z in outage:
            if outage[z].max() > 1:
                print('Outage factor in ' + z + ' > 1, check the results carefully')
            else:
                continue
            
    else:
#        print('No Power plant data for country ' + c + ' , no outages will be computed')
        continue