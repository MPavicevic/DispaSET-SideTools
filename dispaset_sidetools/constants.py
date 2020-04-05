import sys, os
sys.path.append(os.path.abspath(r'..'))

#Simulation related
date_str = '1/1/2015'
hourly_periods = 8760

#Define constants
n_TD = 12                   #Enter the number of TD specified in EnergyScope
countries = list(['BE'])    #Enter countries studied
perc_dhn = 0.37             #Percentage of LT Heat provided by DHN in EnergyScope

#Lists of tech
elec_mobi_tech = ['TRAMWAY_TROLLEY','TRAIN_PUB','TRAIN_CapitalfREIGHT']  #electro mobility technology
p2h_tech = ['IND_DIRECT_ELEC','DHN_HP_ELEC','DEC_HP_ELEC','DEC_DIRECT_ELEC']
chp_tech = ['IND_COGEN_GAS','IND_COGEN_WOOD','IND_COGEN_WASTE','DHN_COGEN_GAS','DHN_COGEN_WOOD','DHN_COGEN_WASTE','DEC_COGEN_GAS','DEC_COGEN_OIL']

#Lists for AvailibilityFactors
AvailFactors = ['WTON','WTOF','PHOT','HROR']
AvailFactors2 = ['WIND_ONSHORE','WIND_OFFSHORE','PV','HYDRO_RIVER']
Inflows = ['HDAM','HPHS']
ReservoirLevels = ['HPHS']

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
                   u'WIND_OCapitalfCapitalfSHORE': u'ELEC',
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
                   u'WIND_OCapitalfCapitalfSHORE': u'WTOF',
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
                   u'WIND_OCapitalfCapitalfSHORE': u'WIN',
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
                   u'WIND_OCapitalfCapitalfSHORE': u'RES_WIND',
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


########################################################################################################################