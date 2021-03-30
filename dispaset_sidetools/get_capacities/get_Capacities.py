import numpy as np
import pandas as pd
import math

from ..search import sto_dhn
from ..common import make_dir

sidetools_folder = '../'  # folder with the common.py and various Dictionaries
input_folder = '../../Inputs/'  # to access DATA - DATA_brut & Typical_Units(to find installed power f [GW or GWh for storage])
output_folder = '../../Outputs/'
source_folder = 'EnergyScope/'
LTlayers = '../../Inputs/LTlayers.txt'

# %% Adjustable inputs that should be modified
# Scenario definition
""" output file: SOURCE + SCENARIO + '_' + str(YEAR) + '_' + CASE """
YEAR = 2015  # considered year
WRITE_CSV_FILES = True  # Write csv database
SCENARIO = 'Test'  # Scenario name, used for naming csv files
CASE = 'Test'  # Case name, used for naming csv files
# Enter Studied Countries
ZONE = ['BE']
SOURCE = 'EnergyScope'  # Source name, used for naming csv files

# Technology definition : if there are some data missing in files, define them here
TECHNOLOGY_THRESHOLD = 0  # threshold (%) below which a technology is considered negligible and no unit is created
STO_THRESHOLD = 0.5  # under STO_THRESHOLD GWh, we don't consider DHN_THMS
num_TD = 12  # number of TDs used in EnergyScope
# CHP_TES_CAPACITY = 12  # No of storage hours in TES
# CSP_TES_CAPACITY = 15  # No of storage hours in CSP units (usually 7.5 hours)
# P2G_TES_CAPACITY = 5  # No of storage hours in P2H units (500l tank = 5h of storage)
# CHP_TYPE = 'Extraction'  # Define CHP type: None, back-pressure or Extraction
# V2G_SHARE = 0.5  # Define how many EV's are V2G
# V2G_PE_RATIO = 4.1 # Define Power to Energy ratio [MWh / MW]

# Clustering options (reduce the number of units - healthy number of units should be <300)
# BIOGAS = 'GAS'  # Define what biogas fuel equals to (BIO or GAS)
# OCEAN = 'WAT'  # Define what ocean fuel equals to (WAT or OTH)
# CSP = True  # Turn Concentrated solar power on/off (when False grouped with PHOT)
# HYDRO_CLUSTERING = 'OFF'  # Define type of hydro clustering (OFF, HPHS, HROR)
# TECH_CLUSTERING = True  # Clusters technologies by treshold (efficient way to reduce total number of units)
# CLUSTER_TRESHOLD = 0.3  # Treshold for clustering technologies together 0-1 (if 0 no clustering)


""" 
    Data needed for the Power Plants in DISPA-SET (ES means from ES): 
    - Unit Name
    - Capacity : Power Capacity [MW]    ==>     ES + Up to US [Repartitionning through Typical_Units.csv]
    - Nunits                            ==>     ES Capacity Installed + [Repartitionning through Typical_Units.csv]
    - Year : Comissionning Year         ==>     For each year new powerplant database is needed
    - Technology                        ==>     ES + Dico
    - Fuel : Primary Fuel               ==>     ES + Dico
    - Fuel Prices                       ==>     Set them as constant
    -------- Technology and Fuel in ES correspond to 1 technology in DISPA-SET -------- 
    - Zone :                            ==>     To be implemented based on hystorical data
    - Efficiency [%]                    ==>     ES + Typical_units.csv
    - Efficiency at min load [%]        ==>     Typical_units.csv
    - CO2 Intensity [TCO2/MWh]          ==>     ES + Typical_units.csv
    - Min Load [%]                      ==>     Typical_units.csv
    - Ramp up rate [%/min]              ==>     Typical_units.csv
    - Ramp down rate [%/min]            ==>     Typical_units.csv
    - Start-up time[h]                  ==>     Typical_units.csv
    - MinUpTime [h]                     ==>     Typical_units.csv
    - Min down Time [h]                 ==>     Typical_units.csv
    - No Load Cost [EUR/h]              ==>     Typical_units.csv
    - Start-up cost [EUR]               ==>     Typical_units.csv
    - Ramping cost [EUR/MW]             ==>     Typical_units.csv
    - Presence of CHP [y/n] & Type      ==>     ES + Typical_units.csv
    - CHPPowerToHeat                    ==>     ES + Typical_units.csv
    - CHPPowerLossFactor                ==>     Typical_units.csv
    - CHPMaxHeat                        ==>     if needed from Typical_units.csv

    column_names = [# Generic
                    'Unit', 'PowerCapacity', 'Nunits', 'Zone', 'Zone_th', 'Zone_H2', 'Technology', 'Fuel', 
                    
                    # Technology specific
                    'Efficiency', 'MinUpTime', 'MinDownTime', 'RampUpRate', 'RampDownRate', 'StartUpCost_pu', 
                    'NoLoadCost_pu', 'RampingCost', 'PartLoadMin', 'MinEfficiency', 'StartUpTime', 'CO2Intensity',
                    'WaterWithdrawal', 'WaterConsumption',
                    
                    # CHP related
                    'CHPType', 'CHPPowerToHeat', 'CHPPowerLossFactor', 'CHPMaxHeat',
                    
                    # P2HT related
                    'COP', 'Tnominal', 'coef_COP_a', 'coef_COP_b', 
                    
                    # Storage related
                    'STOCapacity', 'STOSelfDischarge', 'STOMaxChargingPower', 'STOChargingEfficiency']
"""


# ---------------------------------------- DICO ----------------------------------------#
# For the moment, the dico is in the file, but this will have to be read from a .txt file
mapping = {}

# This dictionary is used to sort out wether a TECH is a PowerPlant, a CHP or a STO
mapping['SORT'] = {u'CCGT': u'ELEC',
                   u'COAL_US': u'ELEC',
                   u'COAL_IGCC': u'ELEC',
                   u'PV': u'ELEC',
                   u'GEOTHERMAL': u'ELEC',
                   u'NUCLEAR': u'ELEC',
                   u'HYDRO_RIVER': u'ELEC',
                   u'NEW_HYDRO_RIVER': u'ELEC',
                   u'WIND': u'ELEC',  # IF WIND is not specified, WIND is asumed to be ONSHORE
                   u'WIND_OFFSHORE': u'ELEC',
                   u'WIND_ONSHORE': u'ELEC',
                   u'IND_COGEN_GAS': u'CHP',  # ADD extraction/back-pressure/other
                   u'IND_COGEN_WOOD': u'CHP',  # ADD extraction/back-pressure/other
                   u'IND_COGEN_WASTE': u'CHP',  # ADD extraction/back-pressure/other
                   u'IND_BOILER_GAS': u'HeatSlack',
                   u'IND_BOILER_WOOD': u'HeatSlack',
                   u'IND_BOILER_OIL': u'HeatSlack',
                   u'IND_BOILER_COAL': u'HeatSlack',
                   u'IND_BOILER_WASTE': u'HeatSlack',
                   u'IND_DIRECT_ELEC': u'P2HT',  # P2HT ?
                   u'DHN_HP_ELEC': u'P2HT',  # P2HT ?
                   u'DHN_COGEN_GAS': u'CHP',  # ADD extraction/back-pressure/other
                   u'DHN_COGEN_WOOD': u'CHP',  # ADD extraction/back-pressure/other
                   u'DHN_COGEN_WASTE': u'CHP',  # ADD extraction/back-pressure/other
                   u'DHN_COGEN_WET_BIOMASS': u'CHP',  # ADD extraction/back-pressure/other
                   u'DHN_BOILER_GAS': u'HeatSlack',
                   u'DHN_BOILER_WOOD': u'HeatSlack',
                   u'DHN_BOILER_OIL': u'HeatSlack',
                   u'DHN_DEEP_GEO': u'HeatSlack',
                   u'DHN_SOLAR': u'HeatSlack',
                   u'DEC_HP_ELEC': u'P2HT',  # P2HT ?
                   u'DEC_THHP_GAS': u'HeatSlack',
                   u'DEC_COGEN_GAS': u'CHP',  # ADD extraction/back-pressure/other
                   u'DEC_COGEN_OIL': u'CHP',  # ADD extraction/back-pressure/other
                   u'DEC_ADVCOGEN_GAS': u'CHP',  # ADD extraction/back-pressure/other
                   u'DEC_ADVCOGEN_H2': u'CHP',  # ADD extraction/back-pressure/other
                   u'DEC_BOILER_GAS': u'HeatSlack',
                   u'DEC_BOILER_WOOD': u'HeatSlack',
                   u'DEC_BOILER_OIL': u'HeatSlack',
                   u'DEC_SOLAR': u'HeatSlack',
                   u'DEC_DIRECT_ELEC': u'HeatSlack',
                   u'PHS': u'STO',
                   u'PHES': u'STO',  # Same thing than PHS ?
                   u'DAM_STORAGE': u'STO',
                   u'BATT_LI': u'STO',
                   u'BEV_BATT': u'STO',
                   u'PHEV_BATT': u'STO',
                   u'TS_DEC_DIRECT_ELEC': u'THMS',
                   u'TS_DEC_HP_ELEC': u'THMS',  # P2HT ?
                   u'TS_DEC_THHP_GAS': u'THMS',
                   u'TS_DEC_COGEN_GAS': u'THMS',
                   u'TS_DEC_COGEN_OIL': u'THMS',
                   u'TS_DEC_ADVCOGEN_GAS': u'THMS',
                   u'TS_DEC_ADVCOGEN_H2': u'THMS',
                   u'TS_DEC_BOILER_GAS': u'THMS',
                   u'TS_DEC_BOILER_WOOD': u'THMS',
                   u'TS_DEC_BOILER_OIL': u'THMS',
                   u'TS_DHN_DAILY': u'THMS',  # TO DO
                   u'TS_DHN_SEASONAL': u'THMS',  # TO DO
                   u'SEASONAL_NG': u'',  # TO DO
                   u'SEASONAL_H2': u''}  # TO DO

mapping['TECH'] = {u'CCGT': u'COMC',
                   u'COAL_US': u'COMC',
                   u'COAL_IGCC': u'STUR',
                   u'PV': u'PHOT',
                   u'GEOTHERMAL': u'STUR',
                   u'NUCLEAR': u'STUR',
                   u'HYDRO_RIVER': u'HROR',
                   u'NEW_HYDRO_RIVER': u'HROR',
                   u'WIND': u'WTON',
                   # HYPOTHESIS : if not specified, Wind is assumed to be ONSHORE - TO CHECK
                   u'WIND_OFFSHORE': u'WTOF',
                   u'WIND_ONSHORE': u'WTON',
                   u'IND_COGEN_GAS': u'STUR',
                   u'IND_COGEN_WOOD': u'STUR',
                   u'IND_COGEN_WASTE': u'STUR',
                   u'IND_BOILER_GAS': u'HeatSlack',
                   u'IND_BOILER_WOOD': u'HeatSlack',
                   u'IND_BOILER_OIL': u'HeatSlack',
                   u'IND_BOILER_COAL': u'HeatSlack',
                   u'IND_BOILER_WASTE': u'HeatSlack',
                   u'IND_DIRECT_ELEC': u'P2HT',  # TO CHECK
                   u'DHN_HP_ELEC': u'P2HT',  # TO CHECK : HP = Heat Pump ?
                   u'DHN_COGEN_GAS': u'STUR',
                   u'DHN_COGEN_WOOD': u'STUR',
                   u'DHN_COGEN_WASTE': u'STUR',
                   u'DHN_COGEN_WET_BIOMASS': u'STUR',
                   u'DHN_BOILER_GAS': u'HeatSlack',
                   u'DHN_BOILER_WOOD': u'HeatSlack',
                   u'DHN_BOILER_OIL': u'HeatSlack',
                   u'DHN_DEEP_GEO': u'HeatSlack',
                   u'DHN_SOLAR': u'HeatSlack',
                   u'DEC_HP_ELEC': u'P2HT',  # TO CHECK : HP = Heat Pump ?
                   u'DEC_THHP_GAS': u'HeatSlack',
                   u'DEC_COGEN_GAS': u'STUR',
                   u'DEC_COGEN_OIL': u'STUR',
                   u'DEC_ADVCOGEN_GAS': u'STUR',
                   u'DEC_ADVCOGEN_H2': u'STUR',
                   u'DEC_BOILER_GAS': u'HeatSlack',
                   u'DEC_BOILER_WOOD': u'HeatSlack',
                   u'DEC_BOILER_OIL': u'HeatSlack',
                   u'DEC_SOLAR': u'HeatSlack',
                   u'DEC_DIRECT_ELEC': u'P2HT',  # TO CHECK : HP = Heat Pump ?
                   u'PHS': u'HPHS',
                   u'PHES': u'HPHS',
                   u'DAM_STORAGE': u'HDAM',
                   u'BATT_LI': u'BATS',
                   u'BEV_BATT': u'BEVS',
                   u'PHEV_BATT': u'BEVS',
                   u'TS_DEC_DIRECT_ELEC': u'THMS',
                   u'TS_DEC_HP_ELEC': u'THMS',
                   u'TS_DEC_THHP_GAS': u'THMS',
                   u'TS_DEC_COGEN_GAS': u'THMS',
                   u'TS_DEC_COGEN_OIL': u'THMS',
                   u'TS_DEC_ADVCOGEN_GAS': u'THMS',
                   u'TS_DEC_ADVCOGEN_H2': u'THMS',
                   u'TS_DEC_BOILER_GAS': u'THMS',
                   u'TS_DEC_BOILER_WOOD': u'THMS',
                   u'TS_DEC_BOILER_OIL': u'THMS',
                   u'TS_DHN_DAILY': u'THMS',  # TO DO
                   u'TS_DHN_SEASONAL': u'THMS',  # TO DO
                   u'SEASONAL_NG': u'',  # TO DO
                   u'SEASONAL_H2': u''}  # TO DO

mapping['FUEL'] = {u'CCGT': u'GAS',
                   u'COAL_IGCC': u'HRD',
                   u'COAL_US': u'HRD',
                   u'PV': u'SUN',
                   u'GEOTHERMAL': u'GEO',
                   u'NUCLEAR': u'NUC',
                   u'HYDRO_RIVER': u'WAT',
                   u'NEW_HYDRO_RIVER': u'WAT',
                   u'WIND': u'WIN',  # IF WIND is not specified, WIND is asumed to be ONSHORE
                   u'WIND_OFFSHORE': u'WIN',
                   u'WIND_ONSHORE': u'WIN',
                   u'IND_COGEN_GAS': u'GAS',
                   u'IND_COGEN_WOOD': u'BIO',
                   u'IND_COGEN_WASTE': u'WST',
                   u'IND_BOILER_GAS': u'HeatSlack',
                   u'IND_BOILER_WOOD': u'HeatSlack',
                   u'IND_BOILER_OIL': u'HeatSlack',
                   u'IND_BOILER_COAL': u'HeatSlack',
                   u'IND_BOILER_WASTE': u'HeatSlack',
                   u'IND_DIRECT_ELEC': u'OTH',  # P2HT ?
                   u'DHN_HP_ELEC': u'OTH',  # P2HT ?
                   u'DHN_COGEN_GAS': u'GAS',
                   u'DHN_COGEN_WOOD': u'BIO',
                   u'DHN_COGEN_WASTE': u'WST',
                   u'DHN_COGEN_WET_BIOMASS': u'BIO',
                   u'DHN_BOILER_GAS': u'HeatSlack',
                   u'DHN_BOILER_WOOD': u'HeatSlack',
                   u'DHN_BOILER_OIL': u'HeatSlack',
                   u'DHN_DEEP_GEO': u'HeatSlack',
                   u'DHN_SOLAR': u'HeatSlack',
                   u'DEC_HP_ELEC': u'OTH',  # P2HT ?
                   u'DEC_THHP_GAS': u'HeatSlack',
                   u'DEC_COGEN_GAS': u'GAS',
                   u'DEC_COGEN_OIL': u'OIL',
                   u'DEC_ADVCOGEN_GAS': u'GAS',
                   u'DEC_ADVCOGEN_H2': u'HYD',
                   u'DEC_BOILER_GAS': u'HeatSlack',
                   u'DEC_BOILER_WOOD': u'HeatSlack',
                   u'DEC_BOILER_OIL': u'HeatSlack',
                   u'DEC_SOLAR': u'HeatSlack',
                   u'DEC_DIRECT_ELEC': u'OTH',
                   u'PHS': u'WAT',
                   u'PHES': u'WAT',
                   u'DAM_STORAGE': u'WAT',
                   u'BATT_LI': u'OTH',  # Right fuel in DS terminology ??
                   u'BEV_BATT': u'OTH',  # Right fuel in DS terminology ??
                   u'PHEV_BATT': u'OTH',  # Right fuel in DS terminology ??
                   u'TS_DEC_DIRECT_ELEC': u'OTH',  # P2HT ?  #Do I need to specify a fuel for Thermal Storage ?
                   u'TS_DEC_HP_ELEC': u'OTH',  # P2HT ?
                   u'TS_DEC_THHP_GAS': u'GAS',
                   u'TS_DEC_COGEN_GAS': u'GAS',
                   u'TS_DEC_COGEN_OIL': u'OIL',
                   u'TS_DEC_ADVCOGEN_GAS': u'',
                   u'TS_DEC_ADVCOGEN_H2': u'',
                   u'TS_DEC_BOILER_GAS': u'',
                   u'TS_DEC_BOILER_WOOD': u'',
                   u'TS_DEC_BOILER_OIL': u'',
                   u'TS_DHN_DAILY': u'',  # TO DO
                   u'TS_DHN_SEASONAL': u'',  # TO DO
                   u'SEASONAL_NG': u'',  # TO DO
                   u'SEASONAL_H2': u''}  # TO DO

# DICO used to get efficiency of tech in layers_in_out
mapping['FUEL_ES'] = {u'CCGT': u'NG',
                      u'COAL_IGCC': u'COAL',
                      u'COAL_US': u'COAL',
                      u'PV': u'RES_SOLAR',
                      u'GEOTHERMAL': u'RES_GEO ',
                      u'NUCLEAR': u'URANIUM',
                      u'HYDRO_RIVER': u'RES_HYDRO',
                      u'NEW_HYDRO_RIVER': u'RES_HYDRO',
                      u'WIND': u'RES_WIND',  # IF WIND is not specified, WIND is asumed to be ONSHORE
                      u'WIND_OFFSHORE': u'RES_WIND',
                      u'WIND_ONSHORE': u'RES_WIND',
                      u'IND_COGEN_GAS': u'NG',
                      u'IND_COGEN_WOOD': u'WOOD',
                      u'IND_COGEN_WASTE': u'WASTE',
                      u'IND_BOILER_GAS': u'NG',
                      u'IND_BOILER_WOOD': u'WOOD',
                      u'IND_BOILER_OIL': u'LFO',
                      u'IND_BOILER_COAL': u'COAL',
                      u'IND_BOILER_WASTE': u'WASTE',
                      u'IND_DIRECT_ELEC': u'ELECTRICITY',  # P2HT ?
                      u'DHN_HP_ELEC': u'ELECTRICITY',  # P2HT ?
                      u'DHN_COGEN_GAS': u'NG',
                      u'DHN_COGEN_WOOD': u'WOOD',
                      u'DHN_COGEN_WASTE': u'WASTE',
                      u'DHN_COGEN_WET_BIOMASS': u'WET_BIOMASS',
                      u'DHN_BOILER_GAS': u'NG',
                      u'DHN_BOILER_WOOD': u'WOOD',
                      u'DHN_BOILER_OIL': u'LFO',
                      u'DHN_DEEP_GEO': u'RES_GEO ',
                      u'DHN_SOLAR': u'RES_SOLAR',
                      u'DEC_HP_ELEC': u'ELECTRICITY',
                      u'DEC_THHP_GAS': u'NG',
                      u'DEC_COGEN_GAS': u'NG',
                      u'DEC_COGEN_OIL': u'LFO',
                      u'DEC_ADVCOGEN_GAS': u'NG',
                      u'DEC_ADVCOGEN_H2': u'H2',
                      u'DEC_BOILER_GAS': u'NG',
                      u'DEC_BOILER_WOOD': u'WOOD',
                      u'DEC_BOILER_OIL': u'LFO',
                      u'DEC_SOLAR': u'RES_SOLAR',
                      u'DEC_DIRECT_ELEC': u'ELECTRICITY',
                      u'PHS': u'ELECTRICITY',  # STO ? Efficiency ?
                      u'PHES': u'ELECTRICITY',  # STO ? Efficiency ?
                      u'DAM_STORAGE': u'ELECTRICITY',  # STO ? Efficiency ?
                      u'BATT_LI': u'ELECTRICITY',  # STO ? Efficiency ?
                      u'BEV_BATT': u'ELECTRICITY',  # STO ? Efficiency ?
                      u'PHEV_BATT': u'ELECTRICITY',  # STO ? Efficiency ?
                      u'TS_DEC_DIRECT_ELEC': u'',  # P2HT ?  #Do I need to specify a fuel for Thermal Storage ?
                      u'TS_DEC_HP_ELEC': u'',  # P2HT ?
                      u'TS_DEC_THHP_GAS': u'',  # STO ? Efficiency ?
                      u'TS_DEC_COGEN_GAS': u'',  # STO ? Efficiency ?
                      u'TS_DEC_COGEN_OIL': u'LFO',  # STO ? Efficiency ?
                      u'TS_DEC_ADVCOGEN_GAS': u'',  # STO ? Efficiency ?
                      u'TS_DEC_ADVCOGEN_H2': u'',  # STO ? Efficiency ?
                      u'TS_DEC_BOILER_GAS': u'',  # STO ? Efficiency ?
                      u'TS_DEC_BOILER_WOOD': u'',  # STO ? Efficiency ?
                      u'TS_DEC_BOILER_OIL': u'',  # STO ? Efficiency ?
                      u'TS_DHN_DAILY': u'',  # TO DO #STO ? Efficiency ?
                      u'TS_DHN_SEASONAL': u'',  # TO DO #STO ? Efficiency ?
                      u'SEASONAL_NG': u'',  # TO DO #STO ? Efficiency ?
                      u'SEASONAL_H2': u''}  # TO DO #STO ? Efficiency ?

mapping['CHP_HEAT'] = {u'IND_COGEN_GAS': u'HEAT_HIGH_T',
                       u'IND_COGEN_WOOD': u'HEAT_HIGH_T',
                       u'IND_COGEN_WASTE': u'HEAT_HIGH_T',
                       u'DHN_COGEN_GAS': u'HEAT_LOW_T_DHN',
                       u'DHN_COGEN_WOOD': u'HEAT_LOW_T_DHN',
                       u'DHN_COGEN_WASTE': u'HEAT_LOW_T_DHN',
                       u'DHN_COGEN_WET_BIOMASS': u'HEAT_LOW_T_DHN',
                       u'DEC_COGEN_GAS': u'HEAT_LOW_T_DECEN',
                       u'DEC_COGEN_OIL': u'HEAT_LOW_T_DECEN',
                       u'DEC_ADVCOGEN_GAS': u'HEAT_LOW_T_DECEN',
                       u'DEC_ADVCOGEN_H2': u'HEAT_LOW_T_DECEN'}

mapping['P2HT_HEAT'] = {u'IND_DIRECT_ELEC': u'HEAT_HIGH_T',
                        u'DHN_HP_ELEC': u'HEAT_LOW_T_DHN',
                        u'DEC_HP_ELEC': u'HEAT_LOW_T_DECEN'}
# u'TS_DEC_HP_ELEC': u''} - Thermal Storage : is P2HT techno ?

# That dictionary could be automatize for DEC_P2HT - IS IT BETTER THOUGH ? - TO CHECK
mapping['THERMAL_STORAGE'] = {u'DEC_DIRECT_ELEC': u'TS_DEC_DIRECT_ELEC',
                              u'DEC_HP_ELEC': u'TS_DEC_HP_ELEC',
                              u'DEC_THHP_GAS': u'TS_DEC_THHP_GAS',
                              u'DEC_COGEN_GAS': u'TS_DEC_COGEN_GAS',
                              u'DEC_COGEN_OIL': u'TS_DEC_COGEN_OIL',
                              u'DEC_ADVCOGEN_GAS': u'TS_DEC_ADVCOGEN_GAS',
                              u'DEC_ADVCOGEN_H2': u'TS_DEC_ADVCOGEN_H2',
                              u'DEC_BOILER_GAS': u'TS_DEC_BOILER_GAS',
                              u'DEC_BOILER_WOOD': u'TS_DEC_BOILER_WOOD',
                              u'DEC_BOILER_OIL': u'TS_DEC_BOILER_OIL', }


# -------------------------------- FUNCTION ---------------------------- #

# function that provides the value contained in the Assets.txt file (output from EnergyScope)
# Input :    tech = technology studied
#           feat = feature needed regarding to the technology studied
# Output :   Value of the feature asked
def search_assets(tech, feat):
    assets = pd.read_csv(input_folder + 'Assets.txt', delimiter='\t')

    features = list(assets.head())
    features = [x.strip(' ') for x in features]
    column = features.index(feat)
    col_names = features[1:]

    col_names.append("end")
    assets.columns = col_names

    output = assets.at[tech, feat]

    return output


# function that reads DATA_brut.xlsx, containing DATA from Energyscope and returns a DataFrame with which we can work with easily to extract data
# Input :    filename = name of the Excel from which we extract DATA (DATA_brut.xlsx)
#           tab = the name of the tab from which we are extracting data
# Output :   the DATA contained in the TAB as a DaataFrame
def from_excel_to_dataFrame(filename, tab):
    # Import the excel file and call it xls_file
    excel_file = pd.ExcelFile(filename)

    # Load the excel_file's Sheet named tab, as a dataframe
    df = excel_file.parse(tab)

    return df


''' 
    Data needed for the Power Plants in DISPA-SET (ES means from ES): 
        - Unit Name
        - Capacity : Power Capacity [MW]    ==>     ES + Up to US [Repartitionning through Typical_Units.csv]
        - Nunits                            ==>     ES Capacity Installed + [Repartitionning through Typical_Units.csv]
        - Year : Comissionning Year
        - Technology                        ==>     ES + Dico
        - Fuel : Primary Fuel               ==>     ES + Dico
        - Fuel Prices                       ==>     Set them as constant
        -------- Technology and Fuel in DS correspond to 1 technology in DISPA-SET -------- 
        - Zone                              ==>     Up to us (Guillaume and Damon)
        - Efficiency [%]
        - Efficiency at min load [%]
        - CO2 Intensity [TCO2/MWh]
        - Min Load [%]
        - Ramp up rate [%/min]
        - Ramp down rate [%/min]
        - Start-up time[h]
        - MinUpTime [h]
        - Min down Time [h]
        - No Load Cost [EUR/h]
        - Start-up cost [EUR]
        - Ramping cost [EUR/MW]
        - Presence of CHP [y/n]             ==>     ES

            column_names = ['Unit', 'PowerCapacity', 'Nunits', 'Zone', 'Technology', 'Fuel', 'Efficiency', 'MinUpTime',
            'MinDownTime', 'RampUpRate', 'RampDownRate', 'StartUpCost_pu', 'NoLoadCost_pu',
            'RampingCost', 'PartLoadMin', 'MinEfficiency', 'StartUpTime', 'CO2Intensity',
            'CHPType', 'CHPPowerToHeat', 'CHPPowerLossFactor', 'COP', 'Tnominal', 'coef_COP_a', 'coef_COP_b',
            'STOCapacity', 'STOSelfDischarge', 'STOMaxChargingPower', 'STOChargingEfficiency', 'CHPMaxHeat']


'''


# function writes the powerplant.xlsx as input of DISPA-SET
# Input :    tech = technology studied, in ES terminology
# Output :   Powerplants.csv written
def define_PP():
    # Read the file
    assets = pd.read_csv(input_folder + 'Assets.txt', delimiter='\t')

    # Get all column names
    head = list(assets.head())

    # Get all Technologies as an iindex to be used later as index of the PowerPlants DataFrame
    all_tech = assets.index

    # Create Dataframe with the DS column names, and as index, all the TECH in DS terminology
    # Are these the right columns ? - TO CHECK
    column_names = ['Unit', 'PowerCapacity', 'Nunits', 'Zone', 'Technology', 'Fuel', 'Efficiency', 'MinUpTime',
                    'MinDownTime', 'RampUpRate', 'RampDownRate', 'StartUpCost_pu', 'NoLoadCost_pu',
                    'RampingCost', 'PartLoadMin', 'MinEfficiency', 'StartUpTime', 'CO2Intensity',
                    'CHPType', 'CHPPowerToHeat', 'CHPPowerLossFactor', 'COP', 'Tnominal', 'coef_COP_a', 'coef_COP_b',
                    'STOCapacity', 'STOSelfDischarge', 'STOMaxChargingPower', 'STOChargingEfficiency', 'CHPMaxHeat']

    PowerPlants = pd.DataFrame(columns=column_names, index=all_tech)

    # ------------- Get the ES datas -------------

    # Get layers_in_out will be used to get :
    #         1) PowerToHeatRatio for CHP TECH
    #         2) COP_nom for COP TECH
    layers_in_out = from_excel_to_dataFrame(input_folder + 'DATA_BRUT.xlsx', '3.1 layers_in_out')
    # Changer les index pour avoir les technologies en Index
    layers_in_out.index = layers_in_out.loc[:, 0]

    # Get 3.3 STO_sto_caracteristics will be used to get :
    #         1) STOCpacity for STO TECH
    #         2) STOSellfDischarge for STO TECH
    #         3) STOMaxChargingPower for STO TECH
    STO_caracteristics = from_excel_to_dataFrame(input_folder + 'DATA_BRUT.xlsx', '3.3 STO_sto_caracteristics')
    # Changer les index pour avoir les technologies en Index
    STO_caracteristics.index = STO_caracteristics.iloc[:, 0]
    STO_caracteristics.drop(0, axis=1, inplace=True)

    # Get 3.3 STO_sto_eff_in will be used to get :
    #         1) Efficiency for STO TECH
    STO_eff_in = from_excel_to_dataFrame(input_folder + 'DATA_BRUT.xlsx', '3.3 STO_sto_eff_in')
    # Changer les index pour avoir les technologies en Index
    STO_eff_in.index = STO_eff_in.iloc[:, 0]

    # Get 3.3 STO_sto_eff_out will be used to get :
    #         1) STOChargingEfficiency for STO TECH
    STO_eff_out = from_excel_to_dataFrame(input_folder + 'DATA_BRUT.xlsx', '3.3 STO_sto_eff_out')
    # Changer les index pour avoir les technologies en Index
    STO_eff_out.index = STO_eff_out.iloc[:, 0]

    # Get Typical Units will be used for :
    #         1) EfficiencyAtMinLoad
    #         2) MinLoad
    #         3) RampUpRate
    #         4) RampDownRate
    #         5) StartUpTime
    #         6) MinUpTime
    #         7) MinDownTime
    #         8) NoLoadCost
    #         9) StartUpCost
    #         10) RampingCost
    Typical_Units = pd.read_csv(input_folder + 'Typical_Units.csv')

    # Fill in the capacity value at Power Capacity column
    PowerPlants['PowerCapacity'] = assets[
        '  f_min']  # The assets.txt file is not in a right format to work with dataframe to get capacity installed f properly - TO FIX
    # Watch out for STO_TECH /!\ - PowerCapacity in DS is MW, where f is in GW/GWh
    # Here everything is in GW/GWh

    ##Change TECH from ES terminology to DS terminology ===== WATCH OUT : what about TECH with NaN ??
    # PowerPlants['TECH_DS'] = PowerPlants.index.to_series().map(mapping['TECH'])

    # Fill in the column Technology, Fuel according to the mapping Dictionary defined here above
    PowerPlants['Technology'] = PowerPlants.index.to_series().map(mapping['TECH'])
    PowerPlants['Fuel'] = PowerPlants.index.to_series().map(mapping['FUEL'])

    # the column Sort is added to do some conditional changes for CHP and STO units
    PowerPlants['Sort'] = PowerPlants.index.to_series().map(mapping['SORT'])

    # Get rid of technology that do not have a Sort category + HeatSlack + Thermal Storage
    indexToDrop = PowerPlants[
        (PowerPlants['Sort'].isna()) | (PowerPlants['Sort'] == 'HeatSlack') | (PowerPlants['Sort'] == 'THMS')].index
    print(
        '[WARNING] : several tech are dropped as they are not referenced in the Dictionary : Sort. Here is the list : ',
        PowerPlants[PowerPlants['Sort'].isna()].index.tolist())
    print('[WARNING] : several tech are dropped as they become HeatSlack in DS. Here is the list : ',
          PowerPlants[PowerPlants['Sort'] == 'HeatSlack'].index.tolist())

    OriginalPP = PowerPlants.copy()  # Keep the original data just in case
    PowerPlants.drop(indexToDrop, inplace=True)

    # Getting all CHP/P2HT/ELEC/STO TECH present in the ES implementation
    CHP_tech = list(PowerPlants.loc[PowerPlants[
                                        'Sort'] == 'CHP'].index)  # On cast le truc en list pour pouvoir le traiter facilement dans une boucle for
    P2HT_tech = list(PowerPlants.loc[PowerPlants[
                                         'Sort'] == 'P2HT'].index)  # On cast le truc en list pour pouvoir le traiter facilement dans une boucle for
    ELEC_tech = list(PowerPlants.loc[PowerPlants[
                                         'Sort'] == 'ELEC'].index)  # On cast le truc en list pour pouvoir le traiter facilement dans une boucle for
    STO_tech = list(PowerPlants.loc[PowerPlants[
                                        'Sort'] == 'STO'].index)  # On cast le truc en list pour pouvoir le traiter facilement dans une boucle for
    THMS_tech = list(PowerPlants.loc[PowerPlants[
                                         'Sort'] == 'THMS'].index)  # On cast le truc en list pour pouvoir le traiter facilement dans une boucle for
    heat_tech = P2HT_tech + CHP_tech

    # Variable used later in CHP and P2HT units regarding THMS of DHN units
    tech_sto_daily = 'TS_DHN_DAILY'
    sto_daily_cap = float(OriginalPP.at[tech_sto_daily, 'PowerCapacity'])
    sto_daily_losses = STO_caracteristics.at[tech_sto_daily, 'storage_losses']
    tech_sto_seasonal = 'TS_DHN_SEASONAL'
    sto_seasonal_cap = float(OriginalPP.at[tech_sto_seasonal, 'PowerCapacity'])
    sto_seasonal_losses = STO_caracteristics.at[tech_sto_seasonal, 'storage_losses']

    # --------------- Changes only for ELEC Units  --------------- TO CHECK
    #      - Efficiency
    for tech in ELEC_tech:
        tech_ressource = mapping['FUEL_ES'][tech]  # gets the correct column electricity to look up per CHP tech
        try:
            Efficiency = abs(layers_in_out.at[tech, 'ELECTRICITY'] / layers_in_out.at[
                tech, tech_ressource])  # If the TECH is ELEC , Efficiency is simply abs(ELECTRICITY/RESSOURCES)
        except:
            print('[WARNING] : technology ', tech, 'has not been found in layers_in_out')

        PowerPlants.loc[PowerPlants.index == tech, 'Efficiency'] = Efficiency

    # --------------- Changes only for CHP Units  --------------- TO CHECK
    #      - Efficiency - TO DO
    #      - PowerPlantsrToTheatRatio
    #      - CHPType
    #      - TO CHECK/FINISH

    # for each CHP_tech, we will extract the PowerToHeat Ratio and add it to the PowerPlants dataFrame
    for tech in CHP_tech:
        tech_ressource = mapping['FUEL_ES'][tech]  # gets the correct column ressources to look up per CHP tech
        tech_heat = mapping['CHP_HEAT'][tech]  # gets the correct column heat to look up per CHP tech
        try:
            PowerToHeatRatio = abs(layers_in_out.at[tech, 'ELECTRICITY'] / layers_in_out.at[tech, tech_heat])
            Efficiency = abs(layers_in_out.at[tech, 'ELECTRICITY'] / layers_in_out.at[
                tech, tech_ressource])  # If the TECH is CHP  , Efficiency is simply abs(ELECTRICITY/RESSOURCES)
        except:
            print('[WARNING] : technology ', tech, 'has not been found in layers_in_out')

        PowerPlants.loc[PowerPlants.index == tech, 'CHPPowerToHeat'] = PowerToHeatRatio
        PowerPlants.loc[PowerPlants.index == tech, 'Efficiency'] = Efficiency

        # As far as I know, CHP units in ES have a constant PowerToHeatRatio ; which makes them 'back-pressure' units by default - TO IMPROVE
        PowerPlants.loc[PowerPlants.index == tech, 'CHPType'] = 'back-pressure'

        # Power Capacity of the plant is defined in ES regarding Heat..
        # But in DS, it is defined regarding Elec. Hence PowerCap_DS = PowerCap_ES*phi ; where phi is the PowerToHeat Ratio
        PowerPlants.loc[PowerPlants.index == tech, 'PowerCapacity'] = float(
            PowerPlants.at[tech, 'PowerCapacity']) * PowerToHeatRatio

    # --------------- Changes only for P2HT Units  --------------- TO CHECK
    #      - Efficiency - it's just 1
    #      - COP
    #      - TO CHECK/FINISH

    # for each P2HT_tech, we will extract the COP Ratio and add it to the PowerPlants dataFrame
    for tech in P2HT_tech:
        tech_ressource = mapping['FUEL_ES'][tech]
        tech_heat = mapping['P2HT_HEAT'][tech]  # gets the correct column heat to look up per CHP tech

        #        Efficiency = layers_in_out.at[tech,'ELECTRICITY']/layers_in_out.at[tech,tech_ressource]#
        Efficiency = 1  # by default - TO CHECK
        PowerPlants.loc[PowerPlants.index == tech, 'Efficiency'] = Efficiency

        try:
            COP = abs(layers_in_out.at[tech, tech_heat] / layers_in_out.at[tech, 'ELECTRICITY'])
        except:
            print('[WARNING] : technology P2HT', tech, 'has not been found in layers_in_out')

        PowerPlants.loc[PowerPlants.index == tech, 'COP'] = COP

        # Power Capacity of the plant is defined in ES regarding Heat..
        # But in DS, it is defined regarding Elec. Hence PowerCap_DS = PowerCap_ES/COP
        PowerPlants.loc[PowerPlants.index == tech, 'PowerCapacity'] = float(PowerPlants.at[tech, 'PowerCapacity']) / COP

    # ----------------------------------THERMAL STORAGE FOR P2HT AND CHP UNITS ------------------------------------------------------ #
    # tech_sto can be of 2 cases :
    #    1) either the CHP tech is DEC_TECH, then it has its own personal storage named TS_DEC_TECH
    #    2) or the CHP tech is DHN_TECH. these tech are asociated with TS_DHN_DAILY and TS_DHN_SEASONAL ; we need to investigate several cases :
    #        a) TS_DHN_DAILY/SEASONAL has no capacity installed : it's like DHN_TECH has no storage
    #        b) one of the two TS_DHN_DAILY/SEASONAL has some capacity installed ; we can split this among the COGEN units
    #        c) the two TS_DHN_DAILY/SEASONAL has some capacity installed ; what do we do ? - TO DO

    # ---------------------------------------------------------------------- RUN THIS PART ONCE THEN USE A LIST ------------------------------------------------------------------------ #
    # get the dhn_daily and dhn_seasonal before the for loop
    # the list used CHP_tech could be brought to a smaller number reducing computation time - throughthe use of tech.startswith('DHN_') ? - TO DO
    #    sto_dhn_daily = sto_dhn(heat_tech, LTlayers,'DAILY',12)
    #    sto_dhn_seasonal = sto_dhn(heat_tech, LTlayers,'SEASONAL',12)

    #    tot_sto_dhn_daily = sto_dhn_daily.sum()
    #    tot_sto_dhn_seasonal = sto_dhn_seasonal.sum()

    # Value for the fixed EnergyScope Data :
    d = {'DHN_COGEN_GAS': [0], 'DHN_COGEN_WOOD': [0], 'DHN_COGEN_WET_BIOMASS': [0], 'DHN_COGEN_WASTE': [0],
         'DHN_HP_ELEC': [0]}
    d2 = {'DHN_COGEN_GAS': [0], 'DHN_COGEN_WOOD': [0], 'DHN_COGEN_WET_BIOMASS': [0], 'DHN_COGEN_WASTE': [0],
          'DHN_HP_ELEC': [2.210936 * 10000000]}  # 10^7
    sto_dhn_daily = pd.DataFrame(data=d)
    sto_dhn_seasonal = pd.DataFrame(data=d2)

    tot_sto_dhn_daily = sto_dhn_daily.sum()
    tot_sto_dhn_seasonal = sto_dhn_seasonal.sum()

    #    print(sto_dhn_daily)
    #    print(sto_dhn_seasonal)
    #    print(tot_sto_dhn_daily)
    #    print(tot_sto_dhn_seasonal)

    # ---------------------------------------------------------------------- RUN THIS PART ONCE THEN USE A LIST ------------------------------------------------------------------------ #

    for tech in heat_tech:
        try:

            if tech.startswith('DEC_'):
                tech_sto = 'TS_' + tech
                STOCapacity = OriginalPP.at[tech_sto, 'PowerCapacity']

                PowerPlants.at[tech, 'STOCapacity'] = STOCapacity  # in GWh

                STOSelfDischarge = STO_caracteristics.at[tech_sto, 'storage_losses']
                PowerPlants.at[tech, 'STOSelfDischarge'] = STOSelfDischarge  # in GWh

            elif tech.startswith('DHN_'):

                # Investigate case a,b and c
                if (sto_daily_cap < STO_THRESHOLD) & (sto_seasonal_cap < STO_THRESHOLD):  # case a
                    print('[INFO] : neither of TS_DHN_DAILY or TS_DHN_SEASONAL has capacity installed in EnergyScope')
                    PowerPlants.at[tech, 'STOCapacity'] = 0  # in GWh
                    PowerPlants.at[tech, 'STOSelfDischarge'] = 0  # in GWh

                elif (sto_daily_cap > STO_THRESHOLD) | (sto_seasonal_cap > STO_THRESHOLD):
                    if (sto_daily_cap > STO_THRESHOLD) & (sto_seasonal_cap > STO_THRESHOLD):  # case c
                        print(
                            '[ERROR] : case NOT HANDLED for the moment : TS_DHN_DAILY and TS_DHN_SEASONAL are implemented both above THMS Threshold in EnergyScope')
                        # This case is still to do, to know if we double the tech and split the power capacity among the two techs



                    else:  # case b
                        if (sto_daily_cap > STO_THRESHOLD):

                            # To set the STOCapacity, it is not so trivial - see Guillaume's Function
                            STOCapacity = sto_dhn_daily[tech]
                            PowerPlants.at[tech, 'STOCapacity'] = STOCapacity  # in GWh

                            print('[INFO] : THMS', tech_sto_daily, 'has a capacity installed of', sto_daily_cap,
                                  'split for', tech, 'at the value of', float(STOCapacity))
                            #                            print('[ERROR] : case NOT HANDLED for the moment : TS_DHN_DAILY and TS_DHN_SEASONAL are implemented above THMS Threshold in EnergyScope')

                            #                            STOSelfDischarge = STO_caracteristics.at[tech_sto_daily,'storage_losses']
                            PowerPlants.at[tech, 'STOSelfDischarge'] = sto_daily_losses  # in GWh


                        elif (sto_seasonal_cap > STO_THRESHOLD):
                            # To set the STOCapacity, it is not so trivial - Check guillaume's function
                            STOCapacity = sto_dhn_seasonal[tech]
                            PowerPlants.at[tech, 'STOCapacity'] = STOCapacity  # in GWh

                            print('[INFO] : THMS', tech_sto_seasonal, 'has a capacity installed of', sto_seasonal_cap,
                                  'split for', tech, 'at the value of', float(STOCapacity))
                            #                            print('[ERROR] : case NOT HANDLED for the moment : TS_DHN_DAILY and TS_DHN_SEASONAL are implemented above THMS Threshold in EnergyScope')

                            #                            STOSelfDischarge = STO_caracteristics.at[tech_sto_seasonal,'storage_losses'] #TS_DHN_SEASONAL
                            PowerPlants.at[tech, 'STOSelfDischarge'] = sto_seasonal_losses  # in GWh

        #            else : #If the unit is IND - so making HIGH TEMPERATURE - no Thermal Storage

        #            tech_sto = mapping['THERMAL_STORAGE'][tech]
        #            STOCapacity = OriginalPP.at[tech_sto,'PowerCapacity']
        #            PowerPlants.at[tech,'STOCapacity'] = STOCapacity #in GWh

        except:
            print('[DEBUGGING] : technology ', tech, 'bugs with Thermal Storage')

    # -------------- STO UNITS --------------------- ==> Only units storing ELECTRICITY - TO CHECK
    #      - STOCapacity
    #      - STOSelfDischarge
    #      - PowerCapacity
    #      - STOMaxChargingPower
    #      - STOChargingEfficiency
    #      - Efficiency
    #      - TO CHECK/FINISH

    for tech in STO_tech:

        try:
            STOCapacity = PowerPlants.at[
                tech, 'PowerCapacity']  # GW to MW is done further #For other Tech ' f' in ES = PowerCapacity, whereas for STO_TECH ' f' = STOCapacity
            STOSelfDischarge = STO_caracteristics.at[
                tech, 'storage_losses']  # In ES, the units are [%/s] whereas in DS the units are [%/h]

            # Caracteristics of charging and discharging
            PowerCapacity = float(STOCapacity) / STO_caracteristics.at[
                tech, 'storage_discharge_time']  # PowerCapacity = Discharging Capacity for STO_TECH in DS #GW to MW is done further
            STOMaxChargingPower = float(STOCapacity) / STO_caracteristics.at[
                tech, 'storage_charge_time'] * 1000  # GW to MW

            # Because STO_TECH in my dictionaries only concerns Storing giving back to ELECTTRICITY
            StoChargingEfficiency = STO_eff_in.at[tech, 'ELECTRICITY']
            Efficiency = STO_eff_out.at[tech, 'ELECTRICITY']

            PowerPlants.loc[
                PowerPlants.index == tech, ['STOCapacity', 'STOSelfDischarge', 'PowerCapacity', 'STOMaxChargingPower',
                                            'STOChargingEfficiency', 'Efficiency']] = [STOCapacity, STOSelfDischarge,
                                                                                       PowerCapacity,
                                                                                       STOMaxChargingPower,
                                                                                       StoChargingEfficiency,
                                                                                       Efficiency]

        except:
            print('[WARNING] : technology ', tech, 'has not been found in STO_eff_out/eff_in/_cracteristics')

    # ------------ TYPICAL UNITS MAKING ----------
    # Part of the code where you fill in DATA coming from typical units

    # ------------------- STLL NEEDED ??? --------------------- - TO CHECK
    # Adding the typical units DATA for (see under)
    #      'MinUpTime', 'MinDownTime', 'RampUpRate', 'RampDownRate', 'StartUpCost_pu', 'NoLoadCost_pu', 'RampingCost', 'PartLoadMin', 'MinEfficiency', 'StartUpTime', 'CO2Intensity',
    Technology_Fuel_in_system = PowerPlants[['Technology', 'Fuel']].copy()
    Technology_Fuel_in_system = Technology_Fuel_in_system.drop_duplicates(subset=['Technology', 'Fuel'], keep='first')
    Technology_Fuel_in_system = Technology_Fuel_in_system.values.tolist()

    #    #Handle NaN - TO CHANGE
    #    PowerPlants.fillna(0,inplace = True)

    # Typical Units : run through Typical_Units with existing Technology_Fuel pairs in ES simulation

    # Caracteristics is a list over which we need to iterate for typical Units
    Caracteristics = ['MinUpTime', 'MinDownTime', 'RampUpRate', 'RampDownRate', 'StartUpCost_pu', 'NoLoadCost_pu',
                      'RampingCost', 'PartLoadMin', 'MinEfficiency', 'StartUpTime', 'CO2Intensity',
                      'CHPPowerLossFactor']

    # Get Indexes to iterate over them
    index_list = list(PowerPlants.loc[PowerPlants['Sort'] != 'CHP'].index.values.tolist())
    index_CHP_list = list(PowerPlants.loc[PowerPlants['Sort'] == 'CHP'].index.values.tolist())

    # For non-CHP units
    for index in index_list:
        Series = PowerPlants.loc[index]
        Tech = Series['Technology']
        Fuel = Series['Fuel']

        Typical_row = Typical_Units.loc[(Typical_Units['Technology'] == Tech) & (Typical_Units['Fuel'] == Fuel)]

        # If there is no correspondance in Typical_row
        if Typical_row.empty:
            print('[ERROR] : There was no correspondance for the Technology', Tech, 'and fuel', Fuel,
                  'in the Typical_Units file', '(', index, ')')

            # IS THIS the best way to handle the lack of presence in Typical_Units ? - TO IMPROVE
            print('[INFO] : So the Technology', Tech, 'and fuel', Fuel, 'will be dropped from dataset')
            PowerPlants.drop(index, inplace=True)

        # If the unit is present in Typical_Units.csv
        else:
            for carac in Caracteristics:
                value = Typical_row[carac].values

                # Adding the needed caracteristics of typical units
                # Take into account the cases whhere the array is of length :
                #    1) nul : no value, the thing is empty
                #    2) 1 : then everything is fine
                #    3) > 1 : then .. What do we do ?
                if len(value) == 0:
                    print('[ERROR] : for caracteristics', carac,
                          ' no correspondance has been found for the Technology ', Tech, ' and Fuel ', Fuel, '(', index,
                          ')')
                elif len(value) == 1:  # Normal case
                    value = float(value)
                    PowerPlants.loc[index, carac] = value
                elif len(value) > 1:
                    print('[WARNING] : for caracteristics', carac, 'size of value is > 1 for the Technology ', Tech,
                          ' and Fuel ', Fuel)

                # END of the carac loop

            # TO DO LIST :
            # 1) f from EnergyScope is in GW/GWh -> set in MW/MWh
            tmp_PowerCap = float(PowerPlants.loc[index, 'PowerCapacity'])
            PowerPlants.loc[index, 'PowerCapacity'] = tmp_PowerCap * 1000
            tmp_Sto = float(PowerPlants.loc[index, 'STOCapacity'])
            PowerPlants.loc[index, 'STOCapacity'] = tmp_Sto * 1000

            # 2) Divide the capacity in assets into N_Units

            # Take into account the case where PowerCapacity in TypicalUnits is 0 - (e.g for BEVS, P2HT)
            # The solution is to set the PowerCapacity as the one given by EnergyScope and set 1 NUnits
            if (Typical_row['PowerCapacity'].values == 0.):
                Number_units = 1
                PowerPlants.loc[index, 'Nunits'] = Number_units

                # If the technology is not implemented in ES, PowerCapacity will be 0
            elif (float(Typical_row['PowerCapacity'].values) != 0) & (float(Series['PowerCapacity']) == 0.):
                Number_units = 0
                PowerPlants.loc[index, 'Nunits'] = Number_units

            elif (float(Typical_row['PowerCapacity'].values) != 0) & (float(Series['PowerCapacity']) > 0.):
                Number_units = math.ceil(
                    float(PowerPlants.loc[index, 'PowerCapacity']) / float(Typical_row['PowerCapacity']))
                PowerPlants.loc[index, 'Nunits'] = math.ceil(Number_units)
                PowerPlants.loc[index, 'PowerCapacity'] = float(PowerPlants.loc[index, 'PowerCapacity']) / math.ceil(
                    Number_units)

        # END of Typical_row.empty loop

    # For CHP units
    for index in index_CHP_list:
        Series = PowerPlants.loc[index]
        Tech = Series['Technology']
        Fuel = Series['Fuel']
        CHPType = Series['CHPType']

        Typical_row = Typical_Units.loc[(Typical_Units['Technology'] == Tech) & (Typical_Units['Fuel'] == Fuel) & (
                    Typical_Units['CHPType'] == CHPType)]

        # If there is no correspondance in Typical_row
        if Typical_row.empty:
            print('[ERROR] : There was no correspondance for the COGEN', (Tech, Fuel, CHPType),
                  'in the Typical_Units file', '(', index, ')')

            # IS THIS the best way to handle the lack of presence in Typical_Units ? - TO IMPROVE
            print('[INFO] : So the Technology', (Tech, Fuel, CHPType), 'will be dropped from dataset')
            PowerPlants.drop(index, inplace=True)

        # If the unit is present in Typical_Units.csv
        else:
            for carac in Caracteristics:
                value = Typical_row[carac].values

                # Adding the needed caracteristics of typical units
                # Take into account the cases whhere the array is of length :
                #    1) nul : no value, the thing is empty
                #    2) 1 : then everything is fine
                #    3) > 1 : then .. What do we do ?
                if len(value) == 0:
                    print('[ERROR] : for caracteristics', carac, ' no correspondance has been found for the COGEN',
                          (Tech, Fuel, CHPType), 'in the Typical_Units file', '(', index, ')')
                elif len(value) == 1:  # Normal case
                    value = float(value)
                    PowerPlants.loc[index, carac] = value
                elif len(value) > 1:
                    print('[WARNING] : for caracteristics', carac, 'size of value is > 1 for the Technology ', Tech,
                          ' and Fuel ', Fuel)

                # Fine-tuning depending on the carac and different types of TECH
                if (carac == 'CHPPowerLossFactor') & (CHPType == 'back-pressure'):
                    if value > 0:
                        print('[WARNING] the CHP back-pressure unit', Tech,
                              'has been assigned a non-0 CHPPowerLossFactor. This value has to be forced to 0 to work with DISPA-SET')
                        PowerPlants.loc[index, carac] = 0

                # END of the carac loop

            # 1) f from EnergyScope is in GW/GWh -> set in MW/MWh
            tmp_PowerCap = float(PowerPlants.loc[index, 'PowerCapacity'])
            PowerPlants.loc[index, 'PowerCapacity'] = tmp_PowerCap * 1000
            tmp_Sto = float(PowerPlants.loc[index, 'STOCapacity'])
            PowerPlants.loc[index, 'STOCapacity'] = tmp_Sto * 1000

            # 2) Divide the capacity in assets into N_Units

            # Take into account the case where PowerCapacity in TypicalUnits is 0 - (e.g for BEVS, P2HT)
            # The solution is to leave the PowerCapacity as the one given by EnergyScope and set 1 NUnits
            if (Typical_row['PowerCapacity'].values == 0.):
                Number_units = 1
                PowerPlants.loc[index, 'Nunits'] = Number_units

                # If the technology is not implemented in ES, PowerCapacity will be 0
            elif (Typical_row['PowerCapacity'].values != 0) & (float(Series['PowerCapacity']) == 0.):
                Number_units = 0
                PowerPlants.loc[index, 'Nunits'] = Number_units

            elif (Typical_row['PowerCapacity'].values != 0) & (float(Series['PowerCapacity']) > 0.):
                Number_units = math.ceil(
                    float(PowerPlants.loc[index, 'PowerCapacity']) / float(Typical_row['PowerCapacity']))
                PowerPlants.loc[index, 'Nunits'] = math.ceil(Number_units)
                PowerPlants.loc[index, 'PowerCapacity'] = float(PowerPlants.loc[index, 'PowerCapacity']) / math.ceil(
                    Number_units)

            # 3) Thermal Storage
            # Finish the correspondance for Thermal Storage - divide it by the number of units to have it equally shared among the cluster of units
            if not (float(PowerPlants.loc[
                              index, 'STOCapacity']) > 0):  # If there is a Thermal Storage and then a STOCapacity at the index

                # Access the row and column of a dataframe : to get to STOCapacity of the checked tech
                if Number_units >= 1:
                    PowerPlants.loc[index, 'STOCapacity'] = float(PowerPlants.loc[index, 'STOCapacity']) / Number_units

    # ------------ Last stuff to do ------------
    # Change the value of the Zone - TO IMPROVE WITH SEVERAL COUNTRIES
    PowerPlants['Zone'] = ZONE[0]

    # Put the index as the Units
    PowerPlants['Unit'] = ZONE[0] + '_' + PowerPlants.index

    # Sort columns as they should be
    PowerPlants = PowerPlants[column_names]
    print(PowerPlants['Nunits'])

    return PowerPlants


def write_csv_files(file_name, demand, write_csv=None):
    filename = file_name + '.csv'
    if write_csv == True:
        for c in demand:
            make_dir(output_folder + 'Database')
            folder = output_folder + 'Database/PowerPlants/'
            make_dir(folder)
            make_dir(folder + c)
            demand[c].to_csv(folder + c + '/' + filename, header=False)
    else:
        print('[WARNING ]: ' + 'WRITE_CSV_FILES = False, unable to write .csv files')


allunits = define_PP()
allunits.to_csv(output_folder + 'PowerPlants.csv', index=False)

# do a function which writes the PowerPlants for several countries ? If e run several nodes ? - TO IMPROVE
# write_csv_files('2015',ZONE,True)

# allunits.to_csv(output_folder + source_folder + 'Database/PowerPlants.csv')
# write_csv_files(SOURCE + SCENARIO + '_' + str(YEAR) + '_' + CASE, allunits, WRITE_CSV_FILES)
# write_pickle_file(allunits, SOURCE + SCENARIO + '_' + str(YEAR) + '_' + CASE)