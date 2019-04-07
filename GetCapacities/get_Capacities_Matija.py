# -*- coding: utf-8 -*-
"""
This script generates the PowerPlant Dispa-SET data for the EU run

All the times in the data are in UTC!
 
CTA: Control Area
BZN: Bidding zone
CTY: Country 

@author: S. Quoilin, JRC
"""

from __future__ import division
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
import sys
import pickle
from common import mapping,outliers_vre,fix_na,make_dir,entsoe_types,commons
from functools import reduce

#%% Adjustable inputs that should be modified
    
year = 2016                  # considered year
write_csv = False            # Write csv database
threshold = 0.035            # threshold (%) below which a technology is considered negligible and no unit is created
include_chp = False          # Switch CHP units on/off
tes_capacity = 0             # No of storage hours in TES

#%% Inputs
'''Get typical units:'''
typical = pd.read_excel('typical_units_matija.xlsx')
typical_chp = pd.read_excel('typical_units_chp_matija.xlsx')

'''Get capacities:'''

bevs = pd.read_csv('BEVS_2016_2030_2050.csv',index_col=0)
#if year == 2030:
#    capacities = pd.read_csv('capacities_2030.csv',index_col=0)
#    bevs_cap = pd.DataFrame(bevs['P_2030']).rename(columns = {'P_2030':'BEVS'})
#elif year == 2050:
#    capacities = pd.read_csv('capacities_2050.csv',index_col=0)
#    bevs_cap = pd.DataFrame(bevs['P_2050']).rename(columns = {'P_2050':'BEVS'})
#elif year == 2016:
#    bevs_cap = pd.DataFrame(bevs['P_2016']).rename(columns = {'P_2016':'BEVS'})
#else:
#    print('selected year is not 2030 or 2050')

if year == 2030:
    capacities = pd.read_csv('EU_TIMES_ProRes1_2030.csv',index_col=0)
    df = pd.read_csv('EU_TIMES_ProRes1_BEVS_2030.csv',index_col=0)
    bevs_cap = pd.DataFrame(df['BEVS']/18)
elif year == 2050:
    capacities = pd.read_csv('EU_TIMES_ProRes1_2050.csv',index_col=0)
    df = pd.read_csv('EU_TIMES_ProRes1_BEVS_2050.csv',index_col=0)
    bevs_cap = pd.DataFrame(df['BEVS']/18)
elif year == 2016:
    bevs_cap = pd.DataFrame(bevs['P_2016']).rename(columns = {'P_2016':'BEVS'})
else:
    print('selected year is not 2030 or 2050')

#%% Load reservoir capacities from entso-e (maximum value of the provided time series)
reservoirs = pd.read_csv('hydro_capacities.csv',index_col=0,header=None)
reservoirs = reservoirs[1]
# Add the missing data:
reservoirs['BE'] = 6000             # About 4.5 hours at full load
reservoirs['DE'] = 718728           # From Eurelectrics
reservoirs['EL'] = 1.7E6           # From Eurelectrics
   

if year == 2016:
    cap,cap_chp = pickle.load(open('chp_and_nonchp_capacities'+str(year)+'.p','rb'))
    countries = list(cap)
    for c in countries:
        tmp_BEV = pd.DataFrame(bevs_cap.loc[c])
        tmp_BEV.rename(columns={c: 'OTH'},inplace=True)
        cap[c] = cap[c].add(tmp_BEV,fill_value=0)
else:
    #%% CHP data
    countries = list(capacities.index)
    # Load data
    file_CHP_heat_capacity = 'heat_capacity_2016.csv'
    file_CHP = 'CHP_EU_input_data_2016.csv'
    data_CHP = pd.read_csv(file_CHP, index_col=0)
    data_CHP_heat_capacity = pd.read_csv(file_CHP_heat_capacity, index_col=0)
    # Proces data
    data_CHP['Power2Heat'] = data_CHP['Power'] / data_CHP['Heat']
    chp_max_capacities = pd.DataFrame(index=capacities.index,columns = capacities.columns) # zamjeni index i column
    
    for f_stur in ['BIO', 'HRD', 'LIG', 'PEA', 'OIL', 'WST', 'GEO']:
        chp_max_capacities[f_stur] = capacities[f_stur] / typical_chp.loc[(typical_chp['Fuel']==f_stur) & (typical_chp['Technology']=='STUR'),'CHPPowerToHeat'].values 
    chp_max_capacities['GAS'] = capacities['GAS'] / typical_chp.loc[(typical_chp['Fuel']== 'GAS') & (typical_chp['Technology']=='COMC'),'CHPPowerToHeat'].values
    
    def chp_heat_cap(Q,Q_max):
        fuel = Q_max.name
        tmp_Q = pd.DataFrame([Q,Q_max]).T
        tmp_Q.fillna(0,inplace = True)
        tmp_Q.loc[tmp_Q['Heat'] >= tmp_Q[fuel],'Fuel'] = tmp_Q[fuel]
        tmp_Q.loc[tmp_Q['Heat'] < tmp_Q[fuel],'Fuel'] = tmp_Q['Heat']
        Q_fuel = tmp_Q['Fuel']
        Q_new = Q - Q_fuel
        Q_fuel = pd.DataFrame(Q_fuel)
        Q_fuel.columns = [fuel]
        Q_new = pd.DataFrame(Q_new)
        Q_new.columns = ['Heat']
        return Q_fuel, Q_new
    
    fuels = ['BIO','GAS','HRD','LIG','PEA','WST','OIL','GEO']
    Q = data_CHP_heat_capacity['Heat']
    tmp = {}
    chp_heat_capacities = pd.DataFrame()
    chp_power_capacities = pd.DataFrame()
    for f in fuels:
        Q_max = chp_max_capacities[f]
        tmp[f] = chp_heat_cap(Q,Q_max)
        Q = tmp[f][1].iloc[:,0]
        new_df = tmp[f][0]
        if f == 'GAS':
            new_df_pow = new_df * typical_chp.loc[(typical_chp['Fuel']== 'GAS') & (typical_chp['Technology']=='COMC'),'CHPPowerToHeat'].values
        else:
            new_df_pow = new_df * typical_chp.loc[(typical_chp['Fuel']==f) & (typical_chp['Technology']=='STUR'),'CHPPowerToHeat'].values
        chp_heat_capacities = pd.concat([chp_heat_capacities, new_df], axis=1)
        chp_power_capacities = pd.concat([chp_power_capacities, new_df_pow], axis=1)
    # chp_power_capacities['HYD','NUC','SUN', 'WAT','WIN']
    chp_power_capacities.fillna(0,inplace=True)   
    
    
    # # Load reservoir capacities from entso-e (maximum value of the provided time series)
    # reservoirs = pd.read_csv('hydro_capacities.csv',index_col=0,header=None)
    # reservoirs = reservoirs[1]
    # # Add the missing data:
    # reservoirs['BE'] = 6000             # About 4.5 hours at full load
    # reservoirs['DE'] = 718728           # From Eurelectrics
    # reservoirs['EL'] = 1.7E6           # From Eurelectrics
    
    # countries = list(capacities.index)
    # capacities = capacities.transpose()
    no_chp_capacities = capacities.sub(chp_power_capacities,fill_value=0)
    no_chp_capacities.fillna(0,inplace=True)
    no_chp_capacities = no_chp_capacities.transpose()
    chp_power_capacities = chp_power_capacities.T
    
    #%% Generate capacities for each country
    hydro_clustering = 'Yes'
    no_countries = len(countries)
    typical_tech = pd.read_csv('typical_technologies.csv',index_col=0)
    typical_stur = pd.DataFrame(np.ones(no_countries),index=countries,columns=['STUR'])
    
    #%% WIND
    typical_win = pd.DataFrame([typical_tech['WTON'],typical_tech['WTOF']]).transpose()
    typical_win['sum'] = typical_win.sum(axis=1)
    typical_win = (typical_win.loc[:,'WTON':'WTOF'].div(typical_win['sum'], axis=0))
    typical_win = typical_win[typical_win.replace([np.inf, -np.inf], np.nan).notnull().all(axis=1)].fillna(0)
    #%% GAS
    typical_gas = pd.DataFrame([typical_tech['COMC'],typical_tech['GTUR'],typical_tech['ICEN'],typical_tech['STUR']]).transpose()
    typical_gas['sum'] = typical_gas.sum(axis=1)
    typical_gas = (typical_gas.loc[:,'COMC':'STUR'].div(typical_gas['sum'], axis=0))
    typical_gas = typical_gas[typical_win.replace([np.inf, -np.inf], np.nan).notnull().all(axis=1)].fillna(0)
    #%% HYDRO
    typical_wat = pd.DataFrame([typical_tech['HDAM'],typical_tech['HROR'],typical_tech['HPHS']]).transpose()
    if hydro_clustering == 'Yes':
        typical_wat['cluster'],typical_wat['sum'] = typical_wat['HDAM'] + typical_wat['HPHS'], typical_wat.sum(axis=1)
        typical_wat.drop(['HDAM', 'HPHS'], axis=1,inplace=True)
        typical_wat = (typical_wat.loc[:,'HROR':'cluster'].div(typical_wat['sum'], axis=0))
        typical_wat = typical_wat[typical_wat.replace([np.inf, -np.inf], np.nan).notnull().all(axis=1)].fillna(0)
        typical_wat.rename(columns={'cluster': 'HPHS'},inplace=True)
    else:
        typical_wat['sum'] = typical_wat.sum(axis=1)
        typical_wat = (typical_wat.loc[:,'HDAM':'HPHS'].div(typical_wat['sum'], axis=0))
        typical_wat = typical_wat[typical_wat.replace([np.inf, -np.inf], np.nan).notnull().all(axis=1)].fillna(0)
    #%% SOLAR
    typical_sun = pd.DataFrame(typical_tech['PHOT'])
    
    #%% Non CHP units
    cap = {} 
    cap_chp = {}
    for c in countries:
        tmp_cap = pd.DataFrame(no_chp_capacities[c]).transpose()
        tmp_SUN = pd.DataFrame(typical_sun.loc[c])*tmp_cap['SUN']
        tmp_SUN.rename(columns={c: 'SUN'},inplace=True)
        tmp_WAT = pd.DataFrame(typical_wat.loc[c])*tmp_cap['WAT']
        tmp_WAT.rename(columns={c: 'WAT'},inplace=True)
        tmp_WIN = pd.DataFrame(typical_win.loc[c])*tmp_cap['WIN']
        tmp_WIN.rename(columns={c: 'WIN'},inplace=True)
        tmp_GAS = pd.DataFrame(typical_gas.loc[c])*tmp_cap['GAS']
        tmp_GAS.rename(columns={c: 'GAS'},inplace=True)
        tmp_BEV = pd.DataFrame(bevs_cap.loc[c])
        tmp_BEV.rename(columns={c: 'OTH'},inplace=True)
        tmp_other = pd.DataFrame([tmp_cap['GEO'],tmp_cap['BIO'],tmp_cap['HRD'],tmp_cap['LIG'],
                                  tmp_cap['NUC'],tmp_cap['OIL'],tmp_cap['PEA'],tmp_cap['WST']]).transpose()
        tmp_other.rename(index={c: 'STUR'},inplace=True)
        df_merged = tmp_other.merge(tmp_GAS, how='outer', left_index=True, right_index=True)
        total_cap = df_merged.sum().sum()
        min_cap = total_cap*threshold
        df_merged[df_merged < min_cap] = 0
        df_merged = df_merged.merge(tmp_WAT, how='outer', left_index=True, right_index=True)
        df_merged = df_merged.merge(tmp_WIN, how='outer', left_index=True, right_index=True)
        df_merged = df_merged.merge(tmp_SUN, how='outer', left_index=True, right_index=True)
        df_merged = df_merged.merge(tmp_BEV, how='outer', left_index=True, right_index=True)
        cap[c] = df_merged
        cap[c].fillna(0,inplace=True)    
        # CHP
        tmp_cap_chp = pd.DataFrame(chp_power_capacities[c]).transpose()
        tmp_GAS_chp = pd.DataFrame(tmp_cap_chp['GAS'])
        tmp_GAS_chp.rename(index={c: 'COMC'},inplace=True)
        tmp_other_chp = pd.DataFrame([tmp_cap_chp['GEO'],tmp_cap_chp['BIO'],tmp_cap_chp['HRD'],tmp_cap_chp['LIG'],
                                    tmp_cap_chp['OIL'],tmp_cap_chp['PEA'],tmp_cap_chp['WST']]).transpose()
        tmp_other_chp.rename(index={c: 'STUR'},inplace=True)
        df_merged_chp = tmp_other_chp.merge(tmp_GAS_chp, how='outer', left_index=True, right_index=True)
        df_merged_chp[df_merged_chp < min_cap] = 0
        cap_chp[c] = df_merged_chp
        cap_chp[c].fillna(0,inplace=True)

#%% Typical unit allocation
allunits = {}

# zones = ['SE']   
for c in cap:
# for c in zones:
    # Non CHP units
    cap_tot = cap[c]
    units = pd.DataFrame()
    for j,i in cap_tot.unstack().index:
        if cap_tot.loc[i,j]>0:
#        if cap_tot.loc[i]>0 & cap_tot.loc[j]>0:
            name = c+'_'+i+'_'+j
            tmp = typical[(typical.Technology == i) & (typical.Fuel==j)]
            if len(tmp)==0:
                # try the generic entries in the dataframe:
                if len(typical[(typical.Technology == i) & (typical.Fuel=="*")]):
                    print('Country ' + c + ' (' + i + ',' + j + '): no typical unit found, using the generic unit for the provided technology')
                    tmp = typical[(typical.Technology == i) & (typical.Fuel=="*")]
                    units[name] = tmp.iloc[0,:]
                    units.loc['Technology',name],units.loc['Fuel',name]=i,j
                elif len(typical[(typical.Technology == i) & (typical.Fuel=="*")]):
                    print('Country ' + c + ' (' + i + ',' + j + '): no typical unit found, using the generic unit for the provided fuel')
                    tmp = typical[(typical.Technology == i) & (typical.Fuel=="*")]
                    units[name] = tmp.iloc[0,:]
                    units.loc['Technology',name],units.loc['Fuel',name]=i,j
                elif len(typical[(typical.Technology == '*') & (typical.Fuel=="*")]):
                    print('Country ' + c + ' (' + i + ',' + j + '): no typical unit found, using the generic unit definition (*,*)')
                    tmp = typical[(typical.Technology == '*') & (typical.Fuel=="*")]
                    units[name] = tmp.iloc[0,:]
                    units.loc['Technology',name],units.loc['Fuel',name]=i,j
                else:
                    print('Country ' + c + ' (' + i + ',' + j + '): no typical unit found, no generic unit found. The entry will be discarded!!')
            elif len(tmp) ==1:
                units[name] = tmp.iloc[0,:]
            elif len(tmp)>1:
                print('Country ' + c + ' (' + i + ',' + j + '): more than one typical unit found, taking average')
                units[name] = tmp.mean()
                units.loc['Technology',name],units.loc['Fuel',name]=i,j
                
            # Adapting the resulting power plants definitions:
            units.loc['Unit',name] = name
            if units.loc['PowerCapacity',name]==0:
                # keep the capacity as such, one single unit:
                units.loc['PowerCapacity',name] = cap_tot.loc[i,j]
                units.loc['Nunits',name] = 1
            else:
                units.loc['Nunits',name] = np.ceil(cap_tot.loc[i,j]/units.loc['PowerCapacity',name])
                units.loc['PowerCapacity',name] = cap_tot.loc[i,j]/units.loc['Nunits',name]
    if len(units)>0:
        units = units.transpose()
        del units['Year']
        units.Zone=c
    else:
        print('Country ' + c + ': no units found. Skipping')
        continue

# CHP and TES
    # tes_capacity = 1      #No of storage hours in TES
    cap_tot_chp = cap_chp[c]
    units_chp = pd.DataFrame()        
    for j,i in cap_tot_chp.unstack().index:
        if cap_tot_chp.loc[i,j]>0:
            name = c+'_'+i+'_'+j+'_CHP'
            tmp = typical_chp[(typical_chp.Technology == i) & (typical_chp.Fuel==j)]
            if len(tmp)==0:
                # try the generic entries in the dataframe:
                if len(typical_chp[(typical_chp.Technology == i) & (typical_chp.Fuel=="*")]):
                    print('Country ' + c + ' (' + i + ',' + j + '): no typical CHP unit found, using the generic unit for the provided technology')
                    tmp = typical_chp[(typical_chp.Technology == i) & (typical_chp.Fuel=="*")]
                    units_chp[name] = tmp.iloc[0,:]
                    units_chp.loc['Technology',name],units_chp.loc['Fuel',name]=i,j
                elif len(typical_chp[(typical_chp.Technology == i) & (typical_chp.Fuel=="*")]):
                    print('Country ' + c + ' (' + i + ',' + j + '): no typical CHP unit found, using the generic unit for the provided fuel')
                    tmp = typical_chp[(typical_chp.Technology == i) & (typical_chp.Fuel=="*")]
                    units_chp[name] = tmp.iloc[0,:]
                    units_chp.loc['Technology',name],units_chp.loc['Fuel',name]=i,j
                elif len(typical_chp[(typical_chp.Technology == '*') & (typical_chp.Fuel=="*")]):
                    print('Country ' + c + ' (' + i + ',' + j + '): no typical CHP unit found, using the generic unit definition (*,*)')
                    tmp = typical_chp[(typical_chp.Technology == '*') & (typical_chp.Fuel=="*")]
                    units_chp[name] = tmp.iloc[0,:]
                    units_chp.loc['Technology',name],units_chp.loc['Fuel',name]=i,j
                else:
                    print('Country ' + c + ' (' + i + ',' + j + '): no typical CHP unit found, no generic unit found. The entry will be discarded!!')
            elif len(tmp) ==1:
                units_chp[name] = tmp.iloc[0,:]
            elif len(tmp)>1:
                print('Country ' + c + ' (' + i + ',' + j + '): more than one typical CHP unit found, taking average')
                units_chp[name] = tmp.mean()
                units_chp.loc['Technology',name],units_chp.loc['Fuel',name]=i,j
                
            # Adapting the resulting power plants definitions:
            units_chp.loc['Unit',name] = name
            if units_chp.loc['PowerCapacity',name] == 0:
                # keep the capacity as such, one single unit:
                units_chp.loc['PowerCapacity',name] = cap_tot_chp.loc[i,j]
                units_chp.loc['Nunits',name] = 1
            else:
                units_chp.loc['Nunits',name] = np.ceil(cap_tot_chp.loc[i,j]/units_chp.loc['PowerCapacity',name])
                units_chp.loc['PowerCapacity',name] = cap_tot_chp.loc[i,j]/units_chp.loc['Nunits',name]
            
            if tes_capacity == 0:
                print('Country ' + c + ' (' + name + '): no TES unit')
            else:
                # units_chp.loc['STOCapacity',name] = units_chp[name, 'PowerCapacity'].values * tes_capacity
                tmp_tes = units_chp.T
                tmp_tes['STOCapacity'] = tmp_tes['PowerCapacity'] / tmp_tes['CHPPowerToHeat'] * tes_capacity
                tmp_tes['STOSelfDischarge'] = str(0.03)
                units_chp.update(tmp_tes)
    if len(units_chp)>0:
        units_chp = units_chp.transpose()
        del units_chp['Year']
        units_chp.Zone=c
        units = units.append(units_chp)
    else:
        print('Country ' + c + ': no CHP units found. Skipping')

    
    #%%
    # Special treatment for the hydro data.
    # HDAM and HPHS are merged into a single unit with the total reservoir capacity
    # Find if there are HPHS units:
    tmp = units[units.Technology=='HPHS']
    if len(tmp)==1:
        hphsdata = tmp.iloc[0,:]
        hphsindex = tmp.index[0]
        # The pumped hydro power is also the chargin power:
        hphsdata['STOMaxChargingPower']=hphsdata['PowerCapacity']
        tmp = units[units.Technology=='HDAM']
        if len(tmp)==1:
            damdata = tmp.iloc[0,:]
            # adding the dam power to the pumpe hydro:
            hphsdata['PowerCapacity'] += damdata['PowerCapacity']
            # delte the hdam row:
            units = units[units.Technology!='HDAM']
        if c in reservoirs.index:
            hphsdata['STOCapacity'] = reservoirs[c]
        else:
            print('Country ' + c + ' No Reservoir Capacity data for country ' + c + '. Assuming a conservative 5 hours of storage')
            hphsdata['STOCapacity'] = hphsdata['PowerCapacity']*5
        units.loc[hphsindex,:] = hphsdata
    elif len(tmp)==0:
        tmp = units[units.Technology=='HDAM']
        if len(tmp)==1:
            if c in reservoirs.index:
                units.loc[tmp.index[0],'STOCapacity'] = reservoirs[c]
            else:
                print('Country ' + c + ' No Reservoir Capacity data for country ' + c + '. Assuming a conservative 5 hours of storage')
                units.loc[tmp.index[0],'STOCapacity'] = units.loc[tmp.index[0],'PowerCapacity'] * 5
    else:
        sys.exit('Various HPHS units!')            
    
    # Special treatment for BEVS
    if units[units.Technology == 'BEVS'].empty == True:
        print('Country '+ c + ' (BEVS) capacity is 0 or BEVS are not present')
    else:
        tmp_bev = units[units.Technology == 'BEVS']
        bevsindex = tmp_bev.index[0]
        tmp_bev['STOMaxChargingPower'] = tmp_bev['PowerCapacity']
        tmp_bev['STOCapacity'] = tmp_bev['PowerCapacity']*4618.28
        units.update(tmp_bev)
        
    #Sort columns as they should be and check if Zone is defined
    cols = ['PowerCapacity', 'Unit', 'Zone', 'Technology', 'Fuel', 'Efficiency', 'MinUpTime',
            'MinDownTime', 'RampUpRate', 'RampDownRate', 'StartUpCost_pu', 'NoLoadCost_pu', 
            'RampingCost', 'PartLoadMin', 'MinEfficiency', 'StartUpTime', 'CO2Intensity', 
            'CHPType', 'CHPPowerToHeat', 'CHPPowerLossFactor', 'STOCapacity', 'STOSelfDischarge', 
            'STOMaxChargingPower', 'STOChargingEfficiency', 'CHPMaxHeat', 'Nunits']
    units['Zone'] = c
    units = units[cols]
        
    allunits[c]  = units 


   
# #%% Write csv file:
# '''    
# inputs (power plant file name as a string)
# :pp_filename:     clustered for example
# :units:           allunits for example
# '''
# def write_csv_files(pp_filename,units):
#     filename = pp_filename + '.csv'
#     allunits = units
#     for c in allunits:
#         make_dir('Database')
#         folder = 'Database/PowerPlants/'
#         make_dir(folder)
#         make_dir(folder + c)
#         allunits[c].to_csv(folder + c + '/' + filename)     

#write_csv_files('clustered_' + str(year),allunits)