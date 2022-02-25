# -*- coding: utf-8 -*-
"""
This script generates the PowerPlant Dispa-SET data for the JRC-EU-TIMES runs

@authors: Matija Pavičević, KU Leuven
          Sylvain Quoilin, KU Leuven
"""
# System imports
from __future__ import division

import pickle
import sys,os
sys.path.append(os.path.abspath(r'../..')) 

import numpy as np
import pandas as pd

# Third-party imports
# Local source tree imports
from dispaset_sidetools.common import make_dir

# %% Adjustable inputs that should be modified
# Scenario definition
""" output file: SOURCE + SCENARIO + '_' + str(YEAR) + '_' + CASE """
YEAR = 2050  # considered year
WRITE_CSV_FILES = True  # Write csv database
SCENARIO = 'ProRes1'  # Scenario name, used for data and naming the files. ProRes1 or NearZeroCarbon
CASE = 'NOFLEX'  # Case name, used for naming csv files
SOURCE = 'JRC_EU_TIMES_'  # Source name, used for naming csv files

# Technology definition
TECHNOLOGY_THRESHOLD = 0.001  # threshold (%) below which a technology is considered negligible and no unit is created
# Define Power to Energy ratio [MWh / MW]
CHP_TES_CAPACITY = 0  # No of storage hours in TES
CSP_TES_CAPACITY = 8  # No of storage hours in CSP units (usually 7.5 hours)
P2G_TES_CAPACITY = 0  # No of storage hours in P2H units (500l tank = 5h of storage)
HYDRO_CAPACITY = 5 # No of storage hours in HPHS and HDAM
BATS_Liion_CAPACITY = 0 # No of storage hours for batteries
BATS_Lead_CAPACITY = 0
V2G_CAPACITY = 0 # No of storage for vehicles 2 grid 
H2_STORAGE = False

CHP_TYPE = 'Extraction'  # Define CHP type: None, back-pressure or Extraction
V2G_SHARE = 0  # Define how many EV's are V2G

# Clustering options (reduce the number of units - healthy number of units should be <300)
BIOGAS = 'GAS'  # Define what biogas fuel equals to (BIO or GAS)
OCEAN = 'WAT'  # Define what ocean fuel equals to (WAT or OTH)
CSP = True  # Turn Concentrated solar power on/off (when False grouped with PHOT)
HYDRO_CLUSTERING = 'OFF'  # Define type of hydro clustering (OFF, HPHS, HROR)
TECH_CLUSTERING = True  # Clusters technologies by treshold (efficient way to reduce total number of units)
CLUSTER_TRESHOLD = 0.3  # Treshold for clustering technologies together 0-1 (if 0 no clustering)

STOSELFDISCHARGE_SUN = 0.03
STOSELFDISCHARGE_P2H = 0.03
STOSELFDISCHARGE_TES = 0.03

# TODO:
CCS = False  # Turn Carbon capture and sotrage on/off  (When false grouped by same Fuel type)

# %% Inputs
# Folder destinations
input_folder = '../../Inputs/'  # Standard input folder
source_folder = 'JRC_EU_TIMES/'
output_folder = '../../Outputs/'  # Standard output folder
scenario = SCENARIO + '/'
year='2019/'
# Local files (Matijs/2019)
# Typical units
typical_units = pd.read_excel(input_folder + source_folder + year +'typical_Matijs.xlsx')
#Capacities
capacities_raw_h = pd.read_excel(
    input_folder + source_folder + year+ 'JRC_Capacities_fuel.xlsx', 
    header=None, nrows = 1, index_col = 0, skiprows = 1)
capacities_raw = pd.read_excel(
    input_folder + source_folder + year+ 'JRC_Capacities_fuel.xlsx', 
    header=None, index_col = 0, skiprows = 2)

# Power to heat
power2heat_capacities = pd.read_excel(input_folder + source_folder + year + 'HP_cap_Matijs1.xlsx', index_col=0)
power2heat_COP = pd.read_excel(input_folder + source_folder + year + 'COP_Matijs.xlsx', index_col=0)
EH_capacities = pd.read_excel(input_folder + source_folder + year + 'EH_cap_Matijs.xlsx', index_col=0)
BOIL_capacities = pd.read_excel(input_folder + source_folder + year + 'BOIL_cap_Matijs.xlsx', index_col=0)

#Capacities technology shares
tech_shares={}                             
for i in ['HRD','BIO','OIL','GAS','WST']:
    tech_shares[i]=pd.read_excel(input_folder + source_folder + year  + 'EUROPE_FuelTech_PCT_Final1.xlsx', sheet_name=i, index_col=0)

#Local Files (JRC-EU-TIMES)
typical_tech_input_raw_h = pd.read_excel(
    input_folder + source_folder + scenario + 'TIMES_Capacities_technology_2050_times_names.xlsx', 
    header=None, nrows = 2, index_col = 0, skiprows = 1)
typical_tech_input_raw = pd.read_excel(
    input_folder + source_folder + scenario +'TIMES_Capacities_technology_2050_times_names.xlsx',
    header=None, index_col = 0, skiprows = 3)

# Capacities

chp_capacities_raw_h = pd.read_excel(
    input_folder + source_folder + scenario + 'TIMES_CHP_Capacities_2050_times_names.xlsx', 
    header=None, nrows = 2, skiprows = 1, index_col = 0)
chp_capacities_raw = pd.read_excel(
    input_folder + source_folder + scenario + 'TIMES_CHP_Capacities_2050_times_names.xlsx', 
    header=None, index_col = 0, skiprows = 3)
p2g_capacities_raw_h = pd.read_excel(
    input_folder + source_folder + scenario + 'TIMES_P2GS_Capacities_2050.xlsx',
    header = None, nrows = 1, skiprows = 1, index_col=0)
p2g_capacities_raw = pd.read_excel(
    input_folder + source_folder + scenario + 'TIMES_P2GS_Capacities_2050.xlsx',
    header = None, skiprows = 2, index_col=0)
h2_storage_capacities = pd.read_excel(
    input_folder + source_folder + scenario + 'TIMES_H2STO_Capacities_2050.xlsx',
    header=None,skiprows=3, index_col=0)
bats_capacities_raw_h= pd.read_excel(
    input_folder + source_folder + scenario + 'TIMES_BATS_Capacities_2050.xlsx',
    header = None, nrows = 1, skiprows = 1, index_col=0)
bats_capacities_raw= pd.read_excel(
    input_folder + source_folder + scenario + 'TIMES_BATS_Capacities_2050.xlsx',
    header = None, skiprows = 2, index_col=0)

# Hydro reservoirs
reservoirs = pd.read_csv(input_folder + 'Default/' + 'Hydro_Reservoirs.csv', index_col=0, header=None)

# Electric wehicles
ev_batteries = pd.read_excel(input_folder + source_folder + scenario + 'TIMES_EV_Capacities.xlsx', index_col=0)

# %% Preprocessing of inputs 

dispaset_rename_fuels= {'Biogas' : 'BIOGAS',
                        'Biomass':'BIO',
                        'Other biomass':'BIO',
                        'Petroleum (possibly blended)':'OIL',
                        'Coal': 'HRD', 
                        'Gas (possibly blended)':'GAS', 
                        'Geothermal': 'GEO',
                        'Nuclear' : 'NUC',
                        'Ocean' : 'Ocean',
                        'Solar' : 'SUN',
                        'Wind' : 'WIN',
                        'Fossil Brown coal/Lignite':'LIG',
                        'Fossil Coal-derived gas':'HRD',
                        'Fossil Gas':'GAS',
                        'Fossil Hard coal': 'HRD',
                        'Fossil Oil':'OIL',
                        'Fossil Oil shale':'OIL',
                        'Hydro':'WAT',
                        'Hydrogen':'HYD',
                        'Hydro Pumped Storage':'WAT',
                        'HDAM':'WAT',
                        'Hydro Run-of-river and poundage':'WAT',
                        'Waste':'WST',
                        'Wind Offshore':'WIN',
                        'Wind Onshore':'WIN'}

dispaset_rename_tech= {'Int Combust' : 'ICEN',
                       ' PV ':'PHOT',
                       ' CSP ': 'STUR',
                       ' onshore ': 'WTON',
                       ' offshore ': 'WTOF',
                       'CCGT' : 'COMC',
                       'Comb CYC': 'COMC',
                       'Combined Cycle': 'COMC',
                       'IGCC': 'COMC',   
                       'thermal' : 'STUR',
                       'Supercritical': 'STUR',
                       'Nuclear': 'STUR',
                       'Steam Turb': 'STUR',
                       'steam turbine' : 'STUR',
                       'Ranking': 'STUR',
                       'Recovery Boiler': 'STUR',
                       'Autoproducer': 'Autoproducers',
                       'OCGT':'GTUR',
                       'Run-of-river': 'HROR',
                       'Run of River': 'HROR',
                       'Wave': 'WAVE',
                       'Tidal':'TIDAL',   
                       'SOFC': 'SOFC',
                       'PEM fuel cell':'PEMFC',
                       'Dams':'HDAM',
                       'Lake large scale':'HPHS',
                       'COMC_CCS': 'COMC_CCS',
                       'STUR_CCS': 'STUR_CCS',
                       'Electrolyzer': 'P2GS',
                       'Electrolyser' : 'P2GS',
                       'Lead-acid' : 'BATS',
                       'Li-ion' : 'BATS'}
# Get wind technology capacities before grouping them as WIN fuel type
capacities_wind=capacities_raw.copy(deep=True)
capacities_wind = capacities_wind.rename(columns=capacities_raw_h.iloc[0], copy=False)
capacities_wind.fillna(0, inplace = True)
 
# Pre-process the capacities (by fuel) changing the names from TIMES nomenclature to Dispa-SET nomencalture
capacities_raw = capacities_raw.rename(columns=capacities_raw_h.iloc[0], copy=False)  
capacities_raw.fillna(0, inplace = True)
capacities_raw.rename(columns=dispaset_rename_fuels, inplace = True)
capacities = capacities_raw.groupby(capacities_raw.columns, axis=1).sum()
    
#  Get Technologies capacities by multiplying  share (%) of each technology with capacities per fuel type
country=list(capacities.index)
for c in country:
    for t in ['COMC_PCT','GTUR_PCT','ICEN_PCT','STUR_PCT']:
        tech_shares['HRD'].loc[c,t]=tech_shares['HRD'].loc[c,t]*capacities.loc[c,'HRD']
        tech_shares['BIO'].loc[c,t]=tech_shares['BIO'].loc[c,t]*capacities.loc[c,'BIO']
        tech_shares['OIL'].loc[c,t]=tech_shares['OIL'].loc[c,t]*capacities.loc[c,'OIL']
        tech_shares['GAS'].loc[c,t]=tech_shares['GAS'].loc[c,t]*capacities.loc[c,'GAS']
        tech_shares['WST'].loc[c,t]=tech_shares['WST'].loc[c,t]*capacities.loc[c,'WST']
        
# Get chp capacities by multiplying technology capacity with share of chp for each technology
chp_gas1=pd.DataFrame(index=capacities.index,columns=['COMC','GTUR','ICEN','STUR'])
chp_bio1=pd.DataFrame(index=capacities.index,columns=['COMC','GTUR','ICEN','STUR'])
chp_oil1=pd.DataFrame(index=capacities.index,columns=['COMC','GTUR','ICEN','STUR'])
chp_wst1=pd.DataFrame(index=capacities.index,columns=['COMC','GTUR','ICEN','STUR'])
chp_hrd1=pd.DataFrame(index=capacities.index,columns=['COMC','GTUR','ICEN','STUR'])

for c in country:
    for t in ['COMC','GTUR','ICEN','STUR']:
        chp_gas1.loc[c,t]=tech_shares['GAS'].loc[c, t+'_PCT']*tech_shares['GAS'].loc[c,t+'_CHP_PCT']
        chp_bio1.loc[c,t]=tech_shares['BIO'].loc[c, t+'_PCT']*tech_shares['BIO'].loc[c,t+'_CHP_PCT']
        chp_oil1.loc[c,t]=tech_shares['OIL'].loc[c, t+'_PCT']*tech_shares['OIL'].loc[c,t+'_CHP_PCT']
        chp_wst1.loc[c,t]=tech_shares['WST'].loc[c, t+'_PCT']*tech_shares['WST'].loc[c,t+'_CHP_PCT']
        chp_hrd1.loc[c,t]=tech_shares['HRD'].loc[c, t+'_PCT']*tech_shares['HRD'].loc[c,t+'_CHP_PCT']
 
#%% Pre-process the technologies (JRC-EU-TIMES)
# Extend the fuels that were as merged cells in excel 
for c in range(len(typical_tech_input_raw_h.iloc[0,:])):
    if pd.isna(typical_tech_input_raw_h.iloc[0, c]): 
        typical_tech_input_raw_h.iloc[0, c] = typical_tech_input_raw_h.iloc[0, c - 1]    
# Change the fuel for LIG when specified in the technology row
for c in range(len(typical_tech_input_raw_h.iloc[0,:])):
    if 'lignite' in typical_tech_input_raw_h.iloc[1, c]:
            typical_tech_input_raw_h.iloc[0, c] = 'LIG'
# Rename all the fuels as before
typical_tech_input_raw_h.iloc[0,:].replace(dispaset_rename_fuels, inplace = True)
# First specify all the CCS units  
for c in range(len(typical_tech_input_raw_h.iloc[0,:])):
    if 'CCS' in typical_tech_input_raw_h.iloc[1, c]:
       if ' CC ' in typical_tech_input_raw_h.iloc[1, c]: 
           typical_tech_input_raw_h.iloc[1, c] = 'COMC_CCS'
       elif ' IGCC ' in typical_tech_input_raw_h.iloc[1, c]: 
           typical_tech_input_raw_h.iloc[1, c] = 'COMC_CCS'
       elif ' CCGT ' in typical_tech_input_raw_h.iloc[1, c]: 
           typical_tech_input_raw_h.iloc[1, c] = 'COMC_CCS'
       elif 'Comb CYC' in typical_tech_input_raw_h.iloc[1, c]: 
           typical_tech_input_raw_h.iloc[1, c] = 'COMC_CCS'
       elif 'Combined' in typical_tech_input_raw_h.iloc[1, c]: 
           typical_tech_input_raw_h.iloc[1, c] = 'COMC_CCS'
       elif 'Fluidized' in typical_tech_input_raw_h.iloc[1, c]: 
           typical_tech_input_raw_h.iloc[1, c] = 'STUR_CCS'
    if ' IGCC CO2Seq' in typical_tech_input_raw_h.iloc[1, c]: 
        typical_tech_input_raw_h.iloc[1, c] = 'COMC_CCS'
# Then use the dictionary to assign the dispaset technology names
for c in range(len(typical_tech_input_raw_h.iloc[0,:])):
    for key in dispaset_rename_tech:
        if key in typical_tech_input_raw_h.iloc[1,c]:
            typical_tech_input_raw_h.iloc[1,c] = dispaset_rename_tech[key]    
# Create a row as FUEL_TECH
typical_tech_input_raw_h.loc['index', :] = typical_tech_input_raw_h.iloc[0, :] + '_' + typical_tech_input_raw_h.iloc[1, :]
typical_tech_input_raw = typical_tech_input_raw.rename(columns=typical_tech_input_raw_h.loc['index', :], copy=False)  
typical_tech_input_raw.fillna(0, inplace = True)
typical_tech_input_raw = typical_tech_input_raw*1000  #Convert to MW

typical_tech_input = typical_tech_input_raw.groupby(typical_tech_input_raw.columns, axis=1).sum()

# Create the LIG column in the fuel dataframe and remove its value from the HRD columns
#capacities.loc[:,'LIG'] = typical_tech_input.loc[:,typical_tech_input.columns.str.contains('LIG')].values
#capacities.loc[:,'HRD'] = capacities.loc[:,'HRD'] - capacities.loc[:,'LIG']

# Pre-process the CHP technologies

# Extend the fuels that were as merged cells in excel 
for c in range(len(chp_capacities_raw_h.iloc[0,:])):
    if pd.isna(chp_capacities_raw_h.iloc[0, c]): 
        chp_capacities_raw_h.iloc[0, c] = chp_capacities_raw_h.iloc[0, c - 1]    
# Change the fuel for LIG when specified in the technology row
for c in range(len(chp_capacities_raw_h.iloc[0,:])):
    if 'lignite' in chp_capacities_raw_h.iloc[1, c]:
            chp_capacities_raw_h.iloc[0, c] = 'LIG'
chp_capacities_raw_h.iloc[0,:].replace(dispaset_rename_fuels, inplace = True)

# First specify all the CCS units   
# -> Commented as is not included in the following parts of the code
# for c in range(len(chp_capacities_raw_h.iloc[0,:])):
#     if 'CCS' in chp_capacities_raw_h.iloc[1, c]:
#        if ' CC ' in chp_capacities_raw_h.iloc[1, c]: chp_capacities_raw_h.iloc[1, c] = 'COMC_CCS'
#        elif ' IGCC ' in chp_capacities_raw_h.iloc[1, c]: chp_capacities_raw_h.iloc[1, c] = 'COMC_CCS'
#        elif ' CCGT ' in chp_capacities_raw_h.iloc[1, c]: chp_capacities_raw_h.iloc[1, c] = 'COMC_CCS'
#        elif 'Comb CYC' in chp_capacities_raw_h.iloc[1, c]: chp_capacities_raw_h.iloc[1, c] = 'COMC_CCS'
#        elif 'Combined' in chp_capacities_raw_h.iloc[1, c]: chp_capacities_raw_h.iloc[1, c] = 'COMC_CCS'
#        elif 'Fluidized' in chp_capacities_raw_h.iloc[1, c]: chp_capacities_raw_h.iloc[1, c] = 'STUR_CCS'
#     if ' IGCC CO2Seq' in chp_capacities_raw_h.iloc[1, c]: chp_capacities_raw_h.iloc[1, c] = 'COMC_CCS'
# Then use the dictionary to assign the dispaset technology names

for c in range(len(chp_capacities_raw_h.iloc[0,:])):
    for key in dispaset_rename_tech:
        if key in chp_capacities_raw_h.iloc[1,c]:
            chp_capacities_raw_h.iloc[1,c] = dispaset_rename_tech[key]    
# Create a row as FUEL_TECH
chp_capacities_raw_h.loc['index', :] = chp_capacities_raw_h.iloc[0, :] + '_' + chp_capacities_raw_h.iloc[1, :]
chp_capacities_raw = chp_capacities_raw.rename(columns=chp_capacities_raw_h.loc['index', :], copy=False)  
chp_capacities_raw.fillna(0, inplace = True)
chp_capacities_raw = chp_capacities_raw*1000  #Convert to MW

chp_capacities = chp_capacities_raw.groupby(chp_capacities_raw.columns, axis=1).sum()

chp_capacities.loc['MT',:] = 0
chp_capacities.sort_index(axis = 0, inplace = True)

# Pre-process the P2GS technologies

for c in range(len(p2g_capacities_raw_h.iloc[0,:])):
    for key in dispaset_rename_tech:
        if key in p2g_capacities_raw_h.iloc[0,c]:
            p2g_capacities_raw_h.iloc[0,c] = dispaset_rename_tech[key] 
                        
p2g_capacities_raw = p2g_capacities_raw.rename(columns=p2g_capacities_raw_h.iloc[0,:], copy=False)  
p2g_capacities_raw.fillna(0, inplace = True)
p2g_capacities_raw = p2g_capacities_raw*1000  #Convert to MW
p2g_capacities = p2g_capacities_raw.groupby(p2g_capacities_raw.columns, axis=1).sum() 

# Pre-process the batteries
# Function to insert row in the dataframe 
def Insert_row_(row_number, df, row_value): 
    if row_number==0:
        df1=row_value
      #  df1.index=[idx]
        df2=df
    else:# Slice the upper half of the dataframe 
        df1 = df[0:row_number]   
        # Store the result of lower half of the dataframe 
        df2 = df[row_number:]   
        # Insert the row in the upper half dataframe 
        df1 = df1.append(row_value)  
     #   df1.index[row_number] = [idx]
    # Concat the two dataframes 
    df_result = pd.concat([df1, df2])    
    # Return the updated dataframe 
    return df_result

countries = list(typical_tech_input_raw.index)
for c in range(len(countries)):
    if countries[c] not in bats_capacities_raw.index:
       bats_capacities_raw = Insert_row_(c, bats_capacities_raw,pd.DataFrame(np.zeros([1,len(bats_capacities_raw.iloc[0,:])]),columns = bats_capacities_raw.columns,index=[countries[c]])) 

for c in range(len(bats_capacities_raw_h.iloc[0,:])):
    if 'Li-ion' in bats_capacities_raw_h.iloc[0,c]:
        bats_capacities_raw_h.iloc[0,c]='Li-ion'
    elif 'Lead-acid' in bats_capacities_raw_h.iloc[0,c]:
        bats_capacities_raw_h.iloc[0,c]='Lead-acid'
    else:
       print('[CRITICAL  ]: There are other types of batteries than Li-ion and Lead-Acid')
       sys.exit()
bats_capacities_raw = bats_capacities_raw.rename(columns=bats_capacities_raw_h.iloc[0,:],copy=False)
bats_capacities_raw.fillna(0,inplace=True)
bats_capacities_copy = bats_capacities_raw.groupby(bats_capacities_raw.columns,axis=1).sum() # used to deal with the diff kinds of batteries

for c in range(len(bats_capacities_raw_h.iloc[0,:])):
    for key in dispaset_rename_tech:
        if key in bats_capacities_raw_h.iloc[0,c]:
            bats_capacities_raw_h.iloc[0,c] = dispaset_rename_tech[key] 
                        
bats_capacities_raw.columns = bats_capacities_raw_h.iloc[0,:] 
bats_capacities = bats_capacities_raw.groupby(bats_capacities_raw.columns, axis=1).sum()

# Check if the technology/fuel names are all considered in the renaming

dispaset_fuels = list(dispaset_rename_fuels.values())
dispaset_tech = list(dispaset_rename_tech.values())

capacities_columns = list(capacities.columns)
if len(list(set(capacities_columns) - set(dispaset_fuels))) == 0:
    print('[INFO    ]: All Fuels have been correctly renamed from TIMES to Dispa-SET nomenclature in capacities')
else: 
    print('[CRITICAL ]: There are fuels that were not considered in the capacities renaming, please check.')
    sys.exit()

typical_tech_input_fuels = list(typical_tech_input_raw_h.iloc[0,:])
if len(list(set(typical_tech_input_fuels) - set(dispaset_fuels))) == 0:
    print('[INFO    ]: All Fuels have been correctly renamed from TIMES to Dispa-SET nomenclature in typical_tech_input')
else: 
    print('[CRITICAL ]: There are fuels that were not considered in the typical_tech_input renaming, please check.')
    sys.exit()

typical_tech_input_tech = list(typical_tech_input_raw_h.iloc[1,:])
if len(list(set(typical_tech_input_tech) - set(dispaset_tech))) == 0:
    print('[INFO    ]: All Technlogies have been correctly renamed from TIMES to Dispa-SET nomenclature in typical_tech_input')
else: 
    print('[CRITICAL ]: There are technologies that were not considered in the typical_tech_input renaming, please check.')
    sys.exit()

chp_capacities_fuels = list(chp_capacities_raw_h.iloc[0,:])
if len(list(set(chp_capacities_fuels) - set(dispaset_fuels))) == 0:
    print('[INFO    ]: All Fuels have been correctly renamed from TIMES to Dispa-SET nomenclature in chp_capacities')
else: 
    print('[CRITICAL ]: There are fuels that were not considered in the chp_capacities renaming, please check.')
    sys.exit()

chp_capacities_tech = list(chp_capacities_raw_h.iloc[1,:])
if len(list(set(chp_capacities_tech) - set(dispaset_tech))) == 0:
    print('[INFO    ]: All Technlogies have been correctly renamed from TIMES to Dispa-SET nomenclature in chp_capacities')
else: 
    print('[CRITICAL ]: There are technologies that were not considered in the chp_capacities renaming, please check.')
    sys.exit()

# %% Load typical units (JRC-EU-TIMES)
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


typical = get_typical_units(typical_units)
typical_chp = get_typical_units(typical_units, chp_type=CHP_TYPE)

#
'''Get capacities:'''
fuel_types = ['BIO', 'GAS', 'GEO', 'HRD', 'HYD', 'LIG', 'NUC', 'OIL', 'PEA', 'SUN', 'WAT', 'WIN', 'WST']
#capacities[BIOGAS] = capacities[BIOGAS] + capacities['Biogas']
#capacities.drop(columns=['Biogas'], inplace=True)
#capacities[OCEAN] = capacities[OCEAN] + capacities['Ocean']
#capacities.drop(columns=['Ocean'], inplace=True)
#capacities = pd.DataFrame(capacities, columns=fuel_types).fillna(0)


# TODO
def get_typical_capacities(capacities, year=None):
    typical_capacities = capacities.copy()
    return typical_capacities


# %% Load reservoir capacities from entso-e (maximum value of the provided time series)
# TODO
def get_reservoir_capacities(reservoirs):
    reservoirs = reservoirs[1]
    return reservoirs


reservoirs = get_reservoir_capacities(reservoirs)

# %% BATS and BEVS data
bevs_cap = pd.DataFrame()
# bevs_cap['BEVS'] = ev_batteries[str(YEAR)] * 1000
bevs_cap['BEVS'] = ev_batteries['GW'] * 1000


# %% CHP Data

chp_fuel_types = ['BIO_COMC', 'BIO_STUR', 'BIO_GTUR', 'BIO_ICEN',
                  'GAS_COMC', 'GAS_STUR', 'GAS_GTUR', 'GAS_ICEN',
                  'Biogas_COMC', 'Biogas_STUR', 'Biogas_GTUR', 'Biogas_ICEN',
                  'HRD_COMC', 'HRD_STUR', 'HRD_GTUR', 'HRD_ICEN',
                  'LIG_COMC', 'LIG_STUR', 'LIG_GTUR', 'LIG_ICEN',
                  'OIL_COMC', 'OIL_STUR', 'OIL_GTUR', 'OIL_ICEN']

# chp_capacities = pd.DataFrame(chp_capacities, columns=chp_fuel_types).fillna(0)

if len(list(set(chp_fuel_types) - set(chp_capacities.columns))) != 0:
    for c in list(set(chp_fuel_types) - set(chp_capacities.columns)):
        chp_capacities.loc[:,c] = 0

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
# data_CHP_heat_capacity = pd.read_csv(input_folder + 'Heat_Capacities.csv', index_col=0)

# %% Generate capacities for each country
no_countries = len(countries)


def get_above_tech_treshold(typical_tech, treshold):
    tmp = pd.DataFrame(typical_tech, columns=['COMC', 'ICEN', 'GTUR', 'STUR']).fillna(0)
    tmp['sum'] = typical_tech.sum(axis=1)
    cond1 = tmp["COMC"] > tmp["sum"] * treshold
    cond2 = tmp["ICEN"] > tmp["sum"] * treshold
    cond3 = tmp["GTUR"] > tmp["sum"] * treshold
    cond4 = tmp["STUR"] > tmp["sum"] * treshold
    tmp1 = tmp['COMC'][cond1]
    tmp2 = tmp['ICEN'][cond2]
    tmp3 = tmp['GTUR'][cond3]
    tmp4 = tmp['STUR'][cond4]
    tmp = pd.DataFrame([tmp1, tmp2, tmp3, tmp4]).fillna(0).T
    tmp.columns = ['COMC', 'ICEN', 'GTUR', 'STUR']
    return tmp


def get_below_tech_treshold(typical_tech, treshold):
    tmp = pd.DataFrame(typical_tech, columns=['COMC', 'ICEN', 'GTUR', 'STUR']).fillna(0)
    tmp['sum'] = typical_tech.sum(axis=1)
    cond1 = tmp["COMC"] < tmp["sum"] * treshold
    cond2 = tmp["ICEN"] < tmp["sum"] * treshold
    cond3 = tmp["GTUR"] < tmp["sum"] * treshold
    cond4 = tmp["STUR"] < tmp["sum"] * treshold
    tmp1 = tmp['COMC'][cond1]
    tmp2 = tmp['ICEN'][cond2]
    tmp3 = tmp['GTUR'][cond3]
    tmp4 = tmp['STUR'][cond4]
    tmp = pd.DataFrame([tmp1, tmp2, tmp3, tmp4]).fillna(0).T
    tmp.columns = ['COMC', 'ICEN', 'GTUR', 'STUR']
    return tmp


def get_tech_treshold(typical_tech, treshold):
    tmp_above = get_above_tech_treshold(typical_tech, treshold)
    tmp_below = get_below_tech_treshold(typical_tech, treshold)
    tmp_below['sum'] = tmp_below.sum(axis=1)
    tmp = pd.DataFrame(index=countries)
    tmp['COMC'] = tmp_above.loc[(tmp_above["COMC"] > tmp_above["STUR"]) &
                                (tmp_above["COMC"] > tmp_above["GTUR"]) &
                                (tmp_above["COMC"] > tmp_above["ICEN"]),
                                ["COMC"]]
    tmp['COMC'] = tmp['COMC'] + tmp_below['sum']

    tmp['ICEN'] = tmp_above.loc[(tmp_above["ICEN"] > tmp_above["STUR"]) &
                                (tmp_above["ICEN"] > tmp_above["GTUR"]) &
                                (tmp_above["ICEN"] > tmp_above["COMC"]),
                                ["ICEN"]]
    tmp['ICEN'] = tmp['ICEN'] + tmp_below['sum']

    tmp['GTUR'] = tmp_above.loc[(tmp_above["GTUR"] > tmp_above["STUR"]) &
                                (tmp_above["GTUR"] > tmp_above["COMC"]) &
                                (tmp_above["GTUR"] > tmp_above["ICEN"]),
                                ["GTUR"]]
    tmp['GTUR'] = tmp['GTUR'] + tmp_below['sum']

    tmp['STUR'] = tmp_above.loc[(tmp_above["STUR"] > tmp_above["COMC"]) &
                                (tmp_above["STUR"] > tmp_above["GTUR"]) &
                                (tmp_above["STUR"] > tmp_above["ICEN"]),
                                ["STUR"]]
    tmp['STUR'] = tmp['STUR'] + tmp_below['sum']
    tmp.fillna(0, inplace=True)
    aa = pd.concat([tmp, tmp_above]).max(level=0)
    return aa


# %% Generate Typical_tech dataframes

if len(list(set(chp_fuel_types) - set(typical_tech_input.columns))) != 0:
    for c in list(set(chp_fuel_types) - set(typical_tech_input.columns)):
        typical_tech_input.loc[:,c] = 0

if CCS is False:
    typical_tech_input['GAS_COMC'] = typical_tech_input['GAS_COMC'] + typical_tech_input['GAS_COMC_CCS']
    typical_tech_input.drop(columns=['GAS_COMC_CCS'], inplace=True)
    if 'BIO_COMC_CCS'in typical_tech_input.columns:
        typical_tech_input['BIO_COMC'] = typical_tech_input['BIO_COMC'] + typical_tech_input['BIO_COMC_CCS']
        typical_tech_input.drop(columns=['BIO_COMC_CCS'], inplace = True)
    if 'BIO_STUR_CCS' in typical_tech_input.columns:
        typical_tech_input['BIO_STUR'] = typical_tech_input['BIO_STUR'] + typical_tech_input['BIO_STUR_CCS']
        typical_tech_input.drop(columns=['BIO_STUR_CCS'], inplace = True)
    if 'HRD_COMC_CCS' in typical_tech_input.columns:
        typical_tech_input['HRD_COMC'] = typical_tech_input['HRD_COMC'] + typical_tech_input['HRD_COMC_CCS']
        typical_tech_input.drop(columns=['HRD_COMC_CCS'], inplace = True)

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

if TECH_CLUSTERING is True:
    typical_tech_bio = get_tech_treshold(typical_tech_bio, CLUSTER_TRESHOLD)
    typical_tech_gas = get_tech_treshold(typical_tech_gas, CLUSTER_TRESHOLD)
    typical_tech_hrd = get_tech_treshold(typical_tech_hrd, CLUSTER_TRESHOLD)
    typical_tech_oil = get_tech_treshold(typical_tech_oil, CLUSTER_TRESHOLD)

# typical_tech_input.drop(columns=['GAS_Autoproducers', 'OIL_Autoproducers'], inplace=True)
technology_types = ['HDAM', 'HROR', 'HPHS', 'PHOT', 'WTOF', 'WTON', 'CAES', 'BATS', 'BEVS', 'THMS']
typical_tech = pd.DataFrame([typical_tech_input['WAT_HDAM'], typical_tech_input['WAT_HPHS'],
                             typical_tech_input['WAT_HROR'], typical_tech_input['WIN_WTOF'],
                             typical_tech_input['WIN_WTON']]).T
typical_tech.columns = typical_tech.columns.str[4:]

for c in typical_tech.index:
    if typical_tech.loc[c,['HDAM', 'HROR', 'HPHS']].sum() == 0:
        typical_tech.loc[c,'HDAM'] = 1
    if typical_tech.loc[c,['WTOF', 'WTON']].sum() == 0:
        typical_tech.loc[c,'WTON'] = 1
        
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

# %% OIL
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
# Make a function with three statements, hydro can either HROR only, HDAM+HPHS, or each technology individually
def get_typical_hydro(typical_hydro, clustering=None):
    """
    Function that loads typical hydro units from the typical_tech and assigns one of several clustering options:
        - HROR only
        - HROR & HPHS (HPHS + HDAM)
        - HROR, HPHS & HDAM individually
    """

    if clustering == 'HROR':
        typical_wat = typical_hydro.copy()
        typical_wat['HROR'] = typical_wat['HDAM'] + typical_wat['HPHS'] + typical_wat['HROR']
        typical_wat.drop(['HDAM', 'HPHS'], axis=1, inplace=True)
        typical_wat = (typical_wat.loc[:, ['HROR']].div(typical_wat['HROR'], axis=0))
        typical_wat.fillna(0, inplace=True)
    else:
        # elif clustering == 'OFF':
        typical_wat = typical_hydro.copy()
        typical_wat['sum'] = typical_wat.sum(axis=1)
        typical_wat = (typical_wat.loc[:, ['HDAM', 'HROR', 'HPHS']].div(typical_wat['sum'], axis=0))
        typical_wat = typical_wat[typical_wat.replace([np.inf, -np.inf], np.nan).notnull().all(axis=1)].fillna(0)
    return typical_wat


typical_wat = get_typical_hydro(typical_hydro=pd.DataFrame([typical_tech['HDAM'], typical_tech['HROR'],
                                                            typical_tech['HPHS']]).T, clustering=HYDRO_CLUSTERING)

# %% P2H data (Matijs/2019)
power2heat_capacities = pd.DataFrame(power2heat_capacities)
p2h_cap = pd.DataFrame()
p2h_cap['P2HT'] = power2heat_capacities.iloc[:, 0] * 1000
#p2h_cap.drop(p2h_cap.index[:3], inplace=True)
EH_capacities = pd.DataFrame(EH_capacities)
EH_cap = pd.DataFrame()
EH_cap['REHE'] = EH_capacities.iloc[:, 0] * 1000

BOIL_capacities = pd.DataFrame(BOIL_capacities)
BOIL_cap = pd.DataFrame()
BOIL_cap['HOBO'] = BOIL_capacities.iloc[:, 0] * 1000

# %% SOLAR (Matijs/2019)
typical_sun1 = typical_sun.copy(deep=True)
typical_sun1=typical_sun1.rename(index={'CY': 'BIH'},columns={'STUR': 'SCSP'})
for c in country:
    typical_sun1.loc[c,'PHOT']=1
    typical_sun1.loc[c,'SCSP']=0
typical_sun1.loc['ES','PHOT']=0.674
typical_sun1.loc['ES','SCSP']=0.326


# %% CHP and NON-CHP total power capacities (Matijs/2019)
fuels = ['BIO', 'GAS', 'HRD', 'LIG', 'PEA', 'WST', 'OIL', 'GEO']
chp_power_capacities1 = pd.DataFrame(columns=fuels)
chp_power_capacities1['GAS'] = chp_gas1.sum(axis=1)
chp_power_capacities1['BIO'] = chp_bio1.sum(axis=1)
chp_power_capacities1['HRD'] = chp_hrd1.sum(axis=1)
chp_power_capacities1['WST'] = chp_wst1.sum(axis=1)
chp_power_capacities1['OIL'] = chp_oil1.sum(axis=1)
chp_power_capacities1.fillna(0, inplace=True)
no_chp_capacities1 = capacities.sub(chp_power_capacities1, fill_value=0)
no_chp_capacities1.fillna(0, inplace=True)
no_chp_capacities1 = no_chp_capacities1.transpose()
chp_power_capacities1 = chp_power_capacities1.T

cap1 = {}
cap_chp1 = {}
# Non CHP units 
#substract chp capacities from total technology capacities, then merge all technologies cap per country
for c in country:
    tmp_CAP = pd.DataFrame(no_chp_capacities1[c]).transpose()
    tmp_bio=pd.DataFrame(index=[c],columns=['COMC','ICEN','STUR','GTUR'])
    tmp_bio['COMC']=tech_shares['BIO'].loc[c,'COMC_PCT']-chp_bio1.loc[c,'COMC']
    tmp_bio['ICEN']=tech_shares['BIO'].loc[c,'ICEN_PCT']-chp_bio1.loc[c,'ICEN']
    tmp_bio['GTUR']=tech_shares['BIO'].loc[c,'GTUR_PCT']-chp_bio1.loc[c,'GTUR']
    tmp_bio['STUR']=tech_shares['BIO'].loc[c,'STUR_PCT']-chp_bio1.loc[c,'STUR']
    tmp_bio=tmp_bio.transpose()
    tmp_bio.rename(columns={c: 'BIO'}, inplace=True)
    
    tmp_gas=pd.DataFrame(index=[c],columns=['COMC','ICEN','STUR','GTUR','HOBO'])
    tmp_gas['COMC']=tech_shares['GAS'].loc[c,'COMC_PCT']-chp_gas1.loc[c,'COMC']
    tmp_gas['ICEN']=tech_shares['GAS'].loc[c,'ICEN_PCT']-chp_gas1.loc[c,'ICEN']
    tmp_gas['GTUR']=tech_shares['GAS'].loc[c,'GTUR_PCT']-chp_gas1.loc[c,'GTUR']
    tmp_gas['STUR']=tech_shares['GAS'].loc[c,'STUR_PCT']-chp_gas1.loc[c,'STUR']
    tmp_gas['HOBO']=BOIL_cap.loc[c,'HOBO']
    tmp_gas=tmp_gas.transpose()
    tmp_gas.rename(columns={c: 'GAS'}, inplace=True)
    
    tmp_hrd=pd.DataFrame(index=[c],columns=['COMC','ICEN','STUR','GTUR'])
    tmp_hrd['COMC']=tech_shares['HRD'].loc[c,'COMC_PCT']-chp_hrd1.loc[c,'COMC']
    tmp_hrd['ICEN']=tech_shares['HRD'].loc[c,'ICEN_PCT']-chp_hrd1.loc[c,'ICEN']
    tmp_hrd['GTUR']=tech_shares['HRD'].loc[c,'GTUR_PCT']-chp_hrd1.loc[c,'GTUR']
    tmp_hrd['STUR']=tech_shares['HRD'].loc[c,'STUR_PCT']-chp_hrd1.loc[c,'STUR']
    tmp_hrd=tmp_hrd.transpose()
    tmp_hrd.rename(columns={c: 'HRD'}, inplace=True)
    
    tmp_oil=pd.DataFrame(index=[c],columns=['COMC','ICEN','STUR','GTUR'])
    tmp_oil['COMC']=tech_shares['OIL'].loc[c,'COMC_PCT']-chp_oil1.loc[c,'COMC']
    tmp_oil['ICEN']=tech_shares['OIL'].loc[c,'ICEN_PCT']-chp_oil1.loc[c,'ICEN']
    tmp_oil['GTUR']=tech_shares['OIL'].loc[c,'GTUR_PCT']-chp_oil1.loc[c,'GTUR']
    tmp_oil['STUR']=tech_shares['OIL'].loc[c,'STUR_PCT']-chp_oil1.loc[c,'STUR']
    tmp_oil=tmp_oil.transpose()
    tmp_oil.rename(columns={c: 'OIL'}, inplace=True)
    
    tmp_wst=pd.DataFrame(index=[c],columns=['COMC','ICEN','STUR','GTUR'])
    tmp_wst['COMC']=tech_shares['WST'].loc[c,'COMC_PCT']-chp_wst1.loc[c,'COMC']
    tmp_wst['ICEN']=tech_shares['WST'].loc[c,'ICEN_PCT']-chp_wst1.loc[c,'ICEN']
    tmp_wst['GTUR']=tech_shares['WST'].loc[c,'GTUR_PCT']-chp_wst1.loc[c,'GTUR']
    tmp_wst['STUR']=tech_shares['WST'].loc[c,'STUR_PCT']-chp_wst1.loc[c,'STUR']
    tmp_wst=tmp_wst.transpose()
    tmp_wst.rename(columns={c: 'WST'}, inplace=True)
    
    tmp_sun = pd.DataFrame(typical_sun1.loc[c]) * tmp_CAP['SUN']
    tmp_sun.rename(columns={c: 'SUN'}, inplace=True)
    
    tmp_wat=pd.DataFrame(index=[c],columns=['HDAM','HROR','HPHS',])
    tmp_wat.loc[c,'HROR']=capacities_wind.loc[c,'Hydro Run-of-river and poundage']
    tmp_wat.loc[c,'HDAM']=capacities_wind.loc[c,'HDAM']
    tmp_wat.loc[c,'HPHS']=capacities_wind.loc[c,'Hydro Pumped Storage']
    tmp_wat=tmp_wat.transpose()
    tmp_wat.rename(columns={c: 'WAT'}, inplace=True)
    
    tmp_win=pd.DataFrame(index=[c],columns=['WTON','WTOF'])
    tmp_win.loc[c,'WTON']=capacities_wind.loc[c,'Wind Onshore']
    tmp_win.loc[c,'WTOF']=capacities_wind.loc[c,'Wind Offshore']
    tmp_win=tmp_win.transpose()
    tmp_win.rename(columns={c: 'WIN'}, inplace=True)
    
    tmp_P2Ha=pd.DataFrame(index=[c],columns=['P2HT','REHE'])
    tmp_P2Ha.loc[c,'P2HT'] = p2h_cap.loc[c,'P2HT']
    tmp_P2Ha.loc[c,'REHE'] = EH_cap.loc[c,'REHE']
    tmp_P2Ha=tmp_P2Ha.transpose()
    tmp_P2Ha.rename(columns={c: 'OTH'}, inplace=True)
    
    tmp_OTHER = pd.DataFrame([tmp_CAP['GEO'], tmp_CAP['LIG'], tmp_CAP['NUC'], tmp_CAP['PEA']]).T
    tmp_OTHER.rename(index={c: 'STUR'}, inplace=True)
    df_merged = tmp_OTHER.merge(tmp_gas, how='outer', left_index=True, right_index=True)
    df_merged = df_merged.merge(tmp_bio, how='outer', left_index=True, right_index=True)
    df_merged = df_merged.merge(tmp_hrd, how='outer', left_index=True, right_index=True)
    df_merged = df_merged.merge(tmp_oil, how='outer', left_index=True, right_index=True)
    df_merged = df_merged.merge(tmp_wat, how='outer', left_index=True, right_index=True)
    df_merged = df_merged.merge(tmp_win, how='outer', left_index=True, right_index=True)
    df_merged = df_merged.merge(tmp_sun, how='outer', left_index=True, right_index=True)
    df_merged = df_merged.merge(tmp_P2Ha, how='outer', left_index=True, right_index=True)
    df_merged.fillna(0,inplace=True)
    total_cap = df_merged.sum().sum()
    min_cap = total_cap * TECHNOLOGY_THRESHOLD
    df_merged[df_merged < min_cap] = 0
    cap1[c] = df_merged
    cap1[c].fillna(0, inplace=True)
    
     # CHP units
    tmp_CAP_chp = pd.DataFrame(chp_power_capacities1[c]).transpose()
    tmp_gas_chp = pd.DataFrame(index=[c],columns=['COMC','GTUR','ICEN','STUR'])
    tmp_gas_chp.loc[c,:]=chp_gas1.loc[c,:]
    tmp_gas_chp=tmp_gas_chp.transpose()
    tmp_gas_chp.rename(columns={c: 'GAS'}, inplace=True)
    
    tmp_bio_chp = pd.DataFrame(index=[c],columns=['COMC','GTUR','ICEN','STUR'])
    tmp_bio_chp.loc[c,:]=chp_bio1.loc[c,:]
    tmp_bio_chp=tmp_bio_chp.transpose()
    tmp_bio_chp.rename(columns={c: 'BIO'}, inplace=True)
    
    tmp_wst_chp = pd.DataFrame(index=[c],columns=['COMC','GTUR','ICEN','STUR'])
    tmp_wst_chp.loc[c,:]=chp_wst1.loc[c,:]
    tmp_wst_chp=tmp_wst_chp.transpose()
    tmp_wst_chp.rename(columns={c: 'WST'}, inplace=True)
    
    tmp_oil_chp = pd.DataFrame(index=[c],columns=['COMC','GTUR','ICEN','STUR'])
    tmp_oil_chp.loc[c,:]=chp_oil1.loc[c,:]
    tmp_oil_chp=tmp_oil_chp.transpose()
    tmp_oil_chp.rename(columns={c: 'OIL'}, inplace=True)
    
    
    tmp_OTHER_chp = pd.DataFrame([tmp_CAP_chp['GEO'], tmp_CAP_chp['LIG'], tmp_CAP_chp['PEA'],tmp_CAP_chp['HRD']]).transpose()
    tmp_OTHER_chp.rename(index={c: 'STUR'}, inplace=True)
    df_merged_chp1 = tmp_OTHER_chp.merge(tmp_bio_chp, how='outer', left_index=True, right_index=True)
    df_merged_chp1 = df_merged_chp1.merge(tmp_oil_chp, how='outer', left_index=True, right_index=True)
    df_merged_chp1 = df_merged_chp1.merge(tmp_wst_chp, how='outer', left_index=True, right_index=True)
    df_merged_chp1 = df_merged_chp1.merge(tmp_gas_chp, how='outer', left_index=True, right_index=True)
    df_merged_chp1.fillna(0,inplace=True)
    df_merged_chp1[df_merged_chp1 < min_cap] = 0
    cap_chp1[c] = df_merged_chp1
    cap_chp1[c].fillna(0, inplace=True)


# %% Typical unit allocation
allunits = {}

for c in cap1:
    # Non CHP units
    cap_tot = cap1[c]
    units = pd.DataFrame()
    for j, i in cap_tot.unstack().index:
        if cap_tot.loc[i, j] > 0:
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
            # CSP
            if CSP_TES_CAPACITY == 0:
                print('[INFO    ]: ' + 'Country ' + c + ' (' + name + '): no TES unit')
            else:
                if (i == 'SCSP') and (j == 'SUN'):
                    tmp_tes = pd.DataFrame(units.loc[:, name], columns=[name]).T
                    tmp_tes['STOCapacity'] = tmp_tes['PowerCapacity'] * CSP_TES_CAPACITY
                    tmp_tes['STOSelfDischarge'] = STOSELFDISCHARGE_SUN
                    tmp_tes = tmp_tes.T
                    units.update(tmp_tes)
                    print('[INFO    ]: ' + 'Country ' + c + ' (' + name + '): Storage of ' + str(CSP_TES_CAPACITY) +
                          ' h added')

    if len(units) > 0:
        units = units.transpose()
        del units['Year']
        units['Zone_th']=np.nan
        units.Zone = c
        if c+'_P2HT_OTH' in units.values:
            units.loc[c+'_P2HT_OTH','Zone_th']= c+'_th'
        if c+'_HOBO_GAS' in units.values:
            units.loc[c+'_HOBO_GAS','Zone_th']= c+'_th'
        if c+'_REHE_OTH' in units.values:
            units.loc[c+'_REHE_OTH','Zone_th']= c+'_th'
        
    else:
        print('[INFO    ]: ' + 'Country ' + c + ': no units found. Skipping')
        continue

    # CHP and TES
    # CHP_TES_CAPACITY = 1      #No of storage hours in TES
    cap_tot_chp = cap_chp1[c]
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
            # TES
            if CHP_TES_CAPACITY == 0:
                print('[INFO    ]: ' + 'Country ' + c + ' (' + name + '): no TES unit')
            else:
                # units_chp.loc['STOCapacity',name] = units_chp[name, 'PowerCapacity'].values * CHP_TES_CAPACITY
                tmp_tes = units_chp.T
                tmp_tes['STOCapacity'] = tmp_tes['PowerCapacity'] / tmp_tes['CHPPowerToHeat'] * CHP_TES_CAPACITY
                tmp_tes['STOSelfDischarge'] = STOSELFDISCHARGE_TES
                tmp_tes = tmp_tes.T
                units_chp.update(tmp_tes)
    if len(units_chp) > 0:
        units_chp = units_chp.transpose()
        del units_chp['Year']
        units_chp.Zone = c
        units_chp['Zone_th']= c+'_th'
        units = units.append(units_chp)
    else:
        print('[INFO    ]: ' + 'Country ' + c + ': no CHP units found. Skipping')

    # %%
    # Avoid merging units at this stage, just assign units as they were before
    # Special treatment for the hydro data.
    # HDAM and HPHS are merged into a single unit with the total reservoir capacity
    # Find if there are HPHS units:
    if HYDRO_CLUSTERING == 'HPHS':
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
                hphsdata['STOCapacity'] = hphsdata['PowerCapacity'] * HYDRO_CAPACITY
            units.loc[hphsindex, :] = hphsdata
        elif len(tmp) == 0:
            tmp = units[units.Technology == 'HDAM']
            if len(tmp) == 1:
                if c in reservoirs.index:
                    units.loc[tmp.index[0], 'STOCapacity'] = reservoirs[c]
                else:
                    print('[INFO    ]: ' + 'Country ' + c + ' No Reservoir Capacity data for country ' + c +
                          '. Assuming a conservative 5 hours of storage')
                    units.loc[tmp.index[0], 'STOCapacity'] = units.loc[tmp.index[0], 'PowerCapacity'] * HYDRO_CAPACITY
        else:
            sys.exit('Various HPHS units!')
    else:
        tmp = units[units.Technology == 'HPHS']
        if len(tmp) == 1:
            hphsdata = tmp.iloc[0, :]
            hphsindex = tmp.index[0]
            # The pumped hydro power is also the chargin power:
            hphsdata['STOMaxChargingPower'] = hphsdata['PowerCapacity']
            print(
                '[INFO    ]: ' + 'Country ' + c + ' (HPHS,WAT) No Reservoir Capacity data for country ' + c + '. Assuming a conservative' + str(HYDRO_CAPACITY) + 'hours of storage')
            hphsdata['STOCapacity'] = hphsdata['PowerCapacity'] * HYDRO_CAPACITY
            units.loc[hphsindex, :] = hphsdata
        else:
            print('[INFO    ]: ' + 'Country ' + c + ' No HPHS for country ' + c)

        tmp = units[units.Technology == 'HDAM']
        if len(tmp) == 1:
            hphsdata = tmp.iloc[0, :]
            hphsindex = tmp.index[0]
            if c in reservoirs.index:
                units.loc[tmp.index[0], 'STOCapacity'] = reservoirs[c]
            else:
                print(
                    '[INFO    ]: ' + 'Country ' + c + ' (HDAM,WAT) No Reservoir Capacity data for country ' + c + '. Assuming a conservative'+ str(HYDRO_CAPACITY) + 'hours of storage')
                units.loc[tmp.index[0], 'STOCapacity'] = units.loc[tmp.index[0], 'PowerCapacity'] * HYDRO_CAPACITY
        else:
            print('[INFO    ]: ' + 'Country ' + c + ' No HDAM for country ' + c)

    # Special treatment for BEVS
    if units[units.Technology == 'BEVS'].empty is True:
        print('[INFO    ]: ' + 'Country ' + c + ' (BEVS) capacity is 0 or BEVS are not present')
    else:
        tmp_bev = units[units.Technology == 'BEVS']
        bevsindex = tmp_bev.index[0]
        tmp_bev['PowerCapacity'] = tmp_bev['PowerCapacity'] * V2G_SHARE
        tmp_bev['STOMaxChargingPower'] = tmp_bev['PowerCapacity']
        tmp_bev['STOCapacity'] = tmp_bev['PowerCapacity'] * V2G_CAPACITY
        # tmp_bev['PowerCapacity'] = tmp_bev['STOMaxChargingPower']
        units.update(tmp_bev)
        if units[units.Technology == 'BEVS'].PowerCapacity.values == 0:
            units = units[units.Technology != 'BEVS']

    # Special treatment for P2H
    if units[units.Technology == 'P2HT'].empty is True:
        print('[INFO    ]: ' + 'Country ' + c + ' (P2HT) capacity is 0 or P2HT are not present')
    else:
        tmp_p2h = units[units.Technology == 'P2HT']
        tmp_p2h['COP'] = power2heat_COP['COP'].loc[c]
        tmp_p2h['Tnominal'] = power2heat_COP['Tnominal'].loc[c]
        tmp_p2h['coef_COP_a'] = power2heat_COP['coef_COP_a'].loc[c]
        tmp_p2h['coef_COP_b'] = power2heat_COP['coef_COP_b'].loc[c]
        # P2H TES
        if P2G_TES_CAPACITY == 0:
            print('[INFO    ]: ' + 'Country ' + c + ' (' + name + '): no P2H_TES unit')
        else:
            tmp_p2h['STOCapacity'] = tmp_p2h['PowerCapacity'] * P2G_TES_CAPACITY
            tmp_p2h['STOSelfDischarge'] = STOSELFDISCHARGE_P2H
        units.update(tmp_p2h)
        
    # Special treatment for P2GS units
    tmp=units[units.Fuel == 'HYD']  
    if len(tmp) == 0:
        print('[INFO    ]: ' + 'Country ' + c + ' (P2G) capacity is 0 or H2 storage is not present')
    elif len(tmp) == 1:
        h2data = tmp
        h2index = tmp.index
        h2data['STOMaxChargingPower'] = h2data['PowerCapacity']
        h2data['PowerCapacity']=typical_tech_input.loc[c,'HYD_PEMFC']
        if H2_STORAGE:
            h2data['STOCapacity'] = h2_storage_capacities.loc[c,1]/(3.6e-6) #convert from PJ to MWh
        else:
            h2data['STOCapacity'] = 0
        units.loc[h2index,:] = h2data    
        if h2data['PowerCapacity'].item() ==0 and h2data['STOMaxChargingPower'].item() ==0:
            units.drop(c+'_P2GS_HYD', inplace=True)
    else:
        sys.exit('Too many P2G units!')
        
    # Special treatment for bats units
    tmp=units[units.Technology == 'BATS']
    if len(tmp) == 0:
        print('[INFO    ]: ' + 'Country ' + c + ' batteries are not present')
    elif len(tmp) == 1:
        batsdata = tmp
        batsindex = tmp.index
        if BATS_Lead_CAPACITY == 0:
            units.drop(c+'_BATS_OTH', inplace=True)
        else:
            batsdata['PowerCapacity'] = batsdata['PowerCapacity'].values/(3.6e-6) # From PJ/h to MW
            batsdata['STOCapacity'] = BATS_Liion_CAPACITY * bats_capacities_copy.loc[c,'Li-ion'] + BATS_Lead_CAPACITY * bats_capacities_copy.loc[c,'Lead-acid']
            batsdata['STOCapacity'] = batsdata['STOCapacity'].values/(3.6e-6) # From PJ to MWh
            batsdata['STOMaxChargingPower'] = batsdata['PowerCapacity'].copy()
            units.loc[batsindex,:] = batsdata
    else:
       sys.exit('Too many bats units!') 
    
    # Sort columns as they should be and check if Zone is defined
    units.loc[:,'WaterWithdrawal']=0
    units.loc[:,'WaterConsumption']=0
    cols = ['Unit', 'PowerCapacity', 'Nunits', 'Zone','Zone_th', 'Technology', 'Fuel', 'Efficiency', 'MinUpTime',
            'MinDownTime', 'RampUpRate', 'RampDownRate', 'StartUpCost_pu', 'NoLoadCost_pu',
            'RampingCost', 'PartLoadMin', 'MinEfficiency', 'StartUpTime', 'CO2Intensity',
            'CHPType', 'CHPPowerToHeat', 'CHPPowerLossFactor', 'COP', 'Tnominal', 'coef_COP_a', 'coef_COP_b',
            'STOCapacity', 'STOSelfDischarge', 'STOMaxChargingPower', 'STOChargingEfficiency','WaterWithdrawal','WaterConsumption']
    units['Zone'] = c
    #units['Nunits'].fillna(0,inplace=True)
    units = units[cols]

    allunits[c] = units




# %%


def write_pickle_file(units, file_name):
    """
    Function that creates a pickle file and saves newly created power plants
    :units:         allunits for example
    :file_name:     name of the pickle file (has to be a string)
    """
    allunits = units

    make_dir((input_folder))
    make_dir(input_folder + source_folder )
    folder = input_folder + source_folder + scenario
    make_dir(folder)
    pkl_file = open(folder + file_name + '.p', 'wb')
    pickle.dump(allunits, pkl_file)
    pkl_file.close()
    print('[INFO    ]: ' + 'Pickle file ' + file_name + ' has been written')

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
            make_dir((output_folder))
            make_dir(output_folder + source_folder + 'Database')
            folder = output_folder + source_folder + 'Database/' + scenario + 'PowerPlants/'
            make_dir(folder)
            make_dir(folder + c)
            allunits[c].to_csv(folder + c + '/' + filename)
    else:
        print('[WARNING ]: ' + 'WRITE_CSV_FILES = False, unable to write .csv files')

write_csv_files(SOURCE + SCENARIO + '_' + str(YEAR) + '_' + CASE, allunits, WRITE_CSV_FILES)
#write_pickle_file(allunits, SOURCE + SCENARIO + '_' + str(YEAR) + '_' + CASE)