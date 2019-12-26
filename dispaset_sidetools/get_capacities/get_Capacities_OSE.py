# -*- coding: utf-8 -*-
"""
This script generates the PowerPlant Dispa-SET data for the EU run

@authors: Matija Pavičević, KU Leuven
          Sylvain Quoilin, KU Leuven
"""
# System imports
from __future__ import division
import pandas as pd
import numpy as np
import pickle
# Third-party imports
# Local source tree imports
from dispaset_sidetools.common import mapping,outliers_vre,fix_na,make_dir,entsoe_types,commons

#%% Adjustable inputs that should be modified
YEAR = 2030                     # considered year
WRITE_CSV_FILES = True         # Write csv database
TECHNOLOGY_THRESHOLD = 0.001   # threshold (%) below which a technology is considered negligible and no unit is created
TES_CAPACITY = 0               # No of storage hours in TES
CHP_TYPE = None         # Define CHP type: None, back-pressure or Extraction

input_folder = '../../Inputs/'  # Standard input folder
output_folder = '../../Outputs/'# Standard output folder

# data = pd.read_excel(input_folder + 'results_191113.xlsx','raw_all')
data = pd.read_excel(input_folder + 'results_191113.xlsx','raw_MEDIAN')
data['Variable'] = data['Variable'].str.replace('coal','Coal')
data['Variable'] = data['Variable'].str.replace('onshore','Onshore')
data['Variable'] = data['Variable'].str.replace('offshore','Offshore')
data['Variable'] = data['Variable'].str.replace('Natural Gas','Gas CCGT')
data['Variable'] = data['Variable'].str.replace('Natural Gas','Gas CCGT')
data['Variable'] = data['Variable'].str.replace('Pumped Hydro','Pumped hydro')

# model = 'CALLIOPE'                    # Chose one of 6 models
# model = 'DIETER'                      
# model = 'dynELMOD'
# model = 'EMMA'
# model = 'URBS'
# model = 'PLEXOS'

scenario = 'Baseline battery costs'     # Chose one of 3 scenarios
# scenario = '50percent battery costs'
# scenario = '25percent battery costs'

coverage = 'Full geographic coverage'   # Chose germany only or full geographic coverage
# coverage = 'Germany only'

#%% Inputs
# Load typical units
'''Get typical units:'''
def get_typical_units(typical_units, CHP_Type=None):
    '''
    Function that:
        - loads typical units from the Inputs/Typical_Units.csv file 
        - assigns CHP units based on type: Extraction, back-pressure or None (no CHP units)
    '''
    if CHP_Type == 'Extraction':
        typical_units = typical_units.copy()
    elif CHP_Type == 'back-pressure':
        typical_units = typical_units.copy()
        typical_units['CHPPowerLossFactor'].values[typical_units['CHPPowerLossFactor'] > 0] = 0
        typical_units['CHPType'].replace(to_replace ='Extraction', value ='back-pressure',inplace=True) 
    elif CHP_Type == None:
        typical_units = typical_units.copy()
        typical_units['CHPType'],typical_units['CHPPowerLossFactor'],typical_units['CHPPowerToHeat'] = np.nan, np.nan ,np.nan  
    else:
        print('[CRITICAL ]: CHP_Type is of wrong string (should be set to None, Extraction or back-pressure)')
    return typical_units

# get model data is a function that scrolls through modells and scenarios and collects the plant capacities data
def get_model_data(input_data, model_name, scenario, geographic_coverage):
    df = input_data
    tmp_df = df[(df['Model'] == model_name) & (df['Scenario'] == scenario + '|' + geographic_coverage)]
    return tmp_df

typical = get_typical_units(typical_units=pd.read_csv(input_folder + 'Typical_Units.csv'))
typical_chp = get_typical_units(typical_units=pd.read_csv(input_folder + 'Typical_Units.csv'), CHP_Type = CHP_TYPE)

models = list(data['Model'].unique())
scenarios = ['Baseline battery costs', '50percent battery costs', '25percent battery costs']
coverages = ['Germany only', 'Full geographic coverage']

# models = ['CALLIOPE']                    # Chose one of 6 models
# models = ['DIETER']
# models = ['dynELMOD']
# models = ['EMMA']
# model = 'urbs'
# models = ['PLEXOS']
# coverage = ['Full geographic coverage']

for model in models:
    for scenario in scenarios:
        for coverage in coverages:
# if model == model:
#     if scenario == scenario:
#         if coverage in coverage:

            # tmp_data = data[(data['Model'] == model)]
            # scenarios = list(tmp_data['Scenario'].unique())

            #TODO
            #%% This is model comparison part
            if coverage == 'Germany only':
                model_data = get_model_data(data,model,scenario,coverage)
                model_data['Region'] = model_data['Region'].replace({'Total covered region': 'DE'})
                model_data.drop_duplicates(inplace=True)
            else:
                model_data = get_model_data(data,model,scenario,coverage)
                model_data = model_data[model_data['Region'] != 'Total covered region']
                model_data['Region'] = model_data['Region'].replace({'GB': 'UK', 'GR': 'EL'})

            indexNames = model_data[(model_data['Unit'] == 'GWh') & (model_data['Variable'] == 'Capacity|Electricity|Hydro Reservoir')].index
            model_data.drop(indexNames , inplace=True)

            # model_data['Value'].values[model_data['Value'] < 0.01] = 0

            #
            '''Get capacities:'''
            batteries = pd.read_csv(input_folder + 'Electric_Vehicles_v2.csv',index_col=0)
            bevs_cap = pd.DataFrame(batteries['BEVS'])
            bevs_cap = bevs_cap*0
            zones = list(bevs_cap.index.unique())

            region_list = list(model_data['Region'].unique())
            if len(region_list) == 0:
                print('no region in region list')
            else:

                batteries,batteries_stor,batteries_crate = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
                capacities = pd.DataFrame()
                typical_tech = pd.DataFrame(columns=['COMC','GTUR','HDAM','HPHS','HROR','ICEN','STUR','WTON','WTOF','PHOT','BEVS','BATS'])
                for region in region_list:
                    tmp_OTH_BATS = model_data[(model_data['Region']==region) & (model_data['Variable'] == 'Capacity|Electricity|Storage|Liion|Power')]
                    tmp_OTH_BATS_STOR = model_data[(model_data['Region']==region) & (model_data['Variable'] == 'Capacity|Electricity|Storage|Liion|Energy')]
                    tmp_OTH_BATS_CRATE = model_data[(model_data['Region']==region) & (model_data['Variable'] == 'Capacity|Electricity|Storage|Liion|C-rate')]
                    tmp_NUC_STUR = model_data[(model_data['Region']==region) & (model_data['Variable'] == 'Capacity|Electricity|Nuclear')]
                    tmp_NUC_STUR['Fuel'], tmp_NUC_STUR['Technology'] = 'NUC','STUR'
                    tmp_LIG_STUR = model_data[(model_data['Region']==region) & (model_data['Variable'] == 'Capacity|Electricity|Lignite')]
                    tmp_LIG_STUR['Fuel'], tmp_LIG_STUR['Technology'] = 'LIG','STUR'
                    tmp_HRD_STUR = model_data[(model_data['Region']==region) & (model_data['Variable'] == 'Capacity|Electricity|Hard Coal')]
                    tmp_HRD_STUR['Fuel'], tmp_HRD_STUR['Technology'] = 'HRD', 'STUR'
                    tmp_GAS_COMC = model_data[(model_data['Region']==region) & (model_data['Variable'] == 'Capacity|Electricity|Gas CCGT')]
                    tmp_GAS_COMC['Fuel'], tmp_GAS_COMC['Technology'] = 'GAS', 'COMC'
                    tmp_GAS_GTUR = model_data[(model_data['Region']==region) & (model_data['Variable'] == 'Capacity|Electricity|Gas OCGT')]
                    tmp_GAS_GTUR['Fuel'], tmp_GAS_GTUR['Technology'] = 'GAS', 'GTUR'
                    tmp_OIL_STUR = model_data[(model_data['Region']==region) & (model_data['Variable'] == 'Capacity|Electricity|Oil')]
                    tmp_OIL_STUR['Fuel'], tmp_OIL_STUR['Technology'] = 'OIL', 'STUR'
                    tmp_BIO_STUR = model_data[(model_data['Region']==region) & (model_data['Variable'] == 'Capacity|Electricity|Bioenergy')]
                    tmp_BIO_STUR['Fuel'], tmp_BIO_STUR['Technology'] = 'BIO', 'STUR'
                    tmp_OTH_STUR = model_data[(model_data['Region']==region) & (model_data['Variable'] == 'Capacity|Electricity|Other nonrenewable')]
                    tmp_OTH_STUR['Fuel'], tmp_OTH_STUR['Technology'] = 'OTH', 'STUR'
                    tmp_WST_STUR = model_data[(model_data['Region']==region) & (model_data['Variable'] == 'Capacity|Electricity|Other renewable')]
                    tmp_WST_STUR['Fuel'], tmp_WST_STUR['Technology'] = 'WST', 'STUR'
                    tmp_WIN_WTON = model_data[(model_data['Region']==region) & (model_data['Variable'] == 'Capacity|Electricity|Wind Onshore')]
                    tmp_WIN_WTON['Fuel'], tmp_WIN_WTON['Technology'] = 'WIN', 'WTON'
                    tmp_WIN_WTOF = model_data[(model_data['Region']==region) & (model_data['Variable'] == 'Capacity|Electricity|Wind Offshore')]
                    tmp_WIN_WTOF['Fuel'], tmp_WIN_WTOF['Technology'] = 'WIN', 'WTOF'
                    tmp_SUN_PHOT = model_data[(model_data['Region']==region) & (model_data['Variable'] == 'Capacity|Electricity|Solar PV')]
                    tmp_SUN_PHOT['Fuel'], tmp_SUN_PHOT['Technology'] = 'SUN', 'PHOT'
                    tmp_WAT_HROR = model_data[(model_data['Region']==region) & (model_data['Variable'] == 'Capacity|Electricity|Hydro ROR')]
                    tmp_WAT_HROR['Fuel'], tmp_WAT_HROR['Technology'] = 'WAT', 'HROR'
                    tmp_WAT_HDAM = model_data[(model_data['Region']==region) & (model_data['Variable'] == 'Capacity|Electricity|Hydro Reservoir')]
                    tmp_WAT_HDAM['Fuel'], tmp_WAT_HDAM['Technology'] = 'WAT', 'HDAM'
                    tmp_WAT_HPHS = model_data[(model_data['Region']==region) & (model_data['Variable'] == 'Capacity|Electricity|Storage|Pumped hydro|Power')]
                    tmp_WAT_HPHS['Fuel'], tmp_WAT_HPHS['Technology'] = 'WAT', 'HPHS'
                    tmp_WAT_HPHS_STOR = model_data[(model_data['Region']==region) & (model_data['Variable'] == 'Capacity|Electricity|Storage|Pumped hydro|Energy')]

                    batteries, batteries_stor, batteries_crate = batteries.append(tmp_OTH_BATS), batteries_stor.append(tmp_OTH_BATS_STOR), batteries_crate.append(tmp_OTH_BATS_CRATE)

                    tmp_capacities = [tmp_NUC_STUR,tmp_LIG_STUR,tmp_HRD_STUR,tmp_GAS_COMC,tmp_GAS_GTUR,tmp_OIL_STUR,tmp_BIO_STUR,tmp_OTH_STUR,
                                      tmp_WST_STUR,tmp_WIN_WTON,tmp_WIN_WTOF,tmp_SUN_PHOT,tmp_WAT_HROR,tmp_WAT_HDAM,tmp_WAT_HPHS]
                    tmp_capacities = pd.concat(tmp_capacities)
                    tmp_capacities.set_index('Fuel',inplace=True)
                    tmp_capacities = tmp_capacities.groupby('Fuel').sum()
                    tmp_capacities = pd.DataFrame(tmp_capacities['Value']).T
                    tmp_capacities.rename(index={'Value':region},inplace=True)
                    capacities = capacities.append(tmp_capacities)


                    tmp_technologies = [tmp_GAS_COMC,tmp_GAS_GTUR,tmp_WIN_WTON,tmp_WIN_WTOF,tmp_SUN_PHOT,tmp_WAT_HROR,tmp_WAT_HDAM,tmp_WAT_HPHS]
                    tmp_technologies = pd.concat(tmp_technologies)
                    tmp_technologies.set_index('Technology',inplace=True)
                    tmp_technologies = tmp_technologies.groupby('Technology').sum()
                    tmp_technologies = pd.DataFrame(tmp_technologies['Value']).T
                    tmp_technologies.rename(index={'Value':region},inplace=True)
                    typical_tech = typical_tech.append(tmp_technologies)
                    typical_tech.fillna(0,inplace=True)

                capacities = pd.DataFrame(capacities,index = zones,columns=['BIO','GAS','HRD','LIG','GEO','NUC','OIL','OTH','SUN','WIN','WAT','PEA','WST'])
                capacities = capacities*1000

                typical_tech = pd.DataFrame(typical_tech,index = zones)
                typical_tech.fillna(1,inplace=True)

                batteries, batteries_stor, batteries_crate = batteries.set_index('Region'), batteries_stor.set_index('Region'), batteries_crate.set_index('Region')
                tmp_batteries = pd.DataFrame([batteries['Value']*1000,batteries_stor['Value']*1000],['Power','Storage']).T
                tmp_batteries['Storage'].fillna(tmp_batteries['Power'],inplace=True)

                bats_cap = pd.DataFrame(tmp_batteries['Power'],index=zones)
                bats_cap.rename(columns={"Power": "BATS"},inplace=True)
                bats_stor = pd.DataFrame(tmp_batteries['Storage'],index=zones)

                #%% End of model comparison part

                #TODO
                def get_typical_capacities(capacities,year=None):
                    typical_capacities = capacities.copy()
                    return typical_capacities

                #%% Load reservoir capacities from entso-e (maximum value of the provided time series)
                #TODO
                def get_reservoir_capacities():
                    reservoirs = pd.read_csv(input_folder + 'Hydro_Reservoirs.csv',index_col=0,header=None)
                    reservoirs = reservoirs[1]
                    return reservoirs

                reservoirs = get_reservoir_capacities()

                if YEAR == 2016:
                    cap,cap_chp = pickle.load(open('chp_and_nonchp_capacities'+str(YEAR)+'.p','rb'))
                    countries = list(cap)
                    for c in countries:
                        tmp_BEV = pd.DataFrame(bevs_cap.loc[c])
                        tmp_BEV.rename(columns={c: 'OTH'},inplace=True)
                        cap[c] = cap[c].add(tmp_BEV,fill_value=0)

                else:
                    #%% CHP data
                    # countries = list(capacities.index)
                    countries = region_list
                    # Load data
                    # file_CHP_heat_capacity = 'heat_capacity_2050.csv'
                    # file_CHP = 'CHP_EU_input_data_2016.csv'
                    # data_CHP = pd.read_csv(file_CHP, index_col=0)
                    # data_CHP_heat_capacity = pd.read_csv(file_CHP_heat_capacity, index_col=0)
                    data_CHP_heat_capacity = pd.read_csv(input_folder + 'Heat_Capacities.csv', index_col=0)
                    #%% Generate capacities for each country
                    no_countries = len(countries)
                #TODO
                    # typical_tech = pd.read_csv(input_folder + 'Typical_Technologies.csv',index_col=0)

                    typical_stur = pd.DataFrame(np.ones(no_countries),index=countries,columns=['STUR'])

                    #%% Proces data
                    chp_max_capacities = pd.DataFrame(index=capacities.index,columns = capacities.columns) # zamjeni index i column

                    #%% WIND
                    typical_win = pd.DataFrame([typical_tech['WTON'],typical_tech['WTOF']]).transpose()
                    typical_win['sum'] = typical_win.sum(axis=1)
                    typical_win = (typical_win.loc[:,'WTON':'WTOF'].div(typical_win['sum'], axis=0))
                    # typical_win = typical_win[typical_win.replace([np.inf, -np.inf], np.nan).notnull().all(axis=1)].fillna(0)
                    typical_win = typical_win.fillna(0)


                    #%% GAS
                    typical_gas = pd.DataFrame([typical_tech['COMC'],typical_tech['GTUR'],typical_tech['ICEN'],typical_tech['STUR']]).transpose()
                    typical_gas['sum'] = typical_gas.sum(axis=1)
                    typical_gas = (typical_gas.loc[:,'COMC':'STUR'].div(typical_gas['sum'], axis=0))
                    typical_gas = typical_gas.fillna(0)

                    #%% HYDRO
                #TODO
                    # Make a function with three statements, hydro can either HROR only, HDAM+HPHS, or each technology individually
                    def get_typical_hydro(typical_hydro,clustering=None):
                        '''
                        Function that loads typical hydro units from the typical_tech and assigns one of several clustering options:
                            - HROR only
                            - HROR & HPHS (HPHS + HDAM)
                            - HROR, HPHS & HDAM individually
                        '''
                        if clustering == 'On':
                            typical_wat = typical_hydro.copy()
                            typical_wat['cluster'],typical_wat['sum'] = typical_wat['HDAM'] + typical_wat['HPHS'], typical_wat.sum(axis=1)
                            typical_wat.drop(['HDAM', 'HPHS'], axis=1,inplace=True)
                            typical_wat = (typical_wat.loc[:,'HROR':'cluster'].div(typical_wat['sum'], axis=0))
                            # typical_wat = typical_wat[typical_wat.replace([np.inf, -np.inf], np.nan).notnull().all(axis=1)].fillna(0)
                            typical_wat = typical_wat.fillna(0)
                            typical_wat.rename(columns={'cluster': 'HPHS'},inplace=True)
                        else:
                            typical_wat = typical_hydro.copy()
                            typical_wat['sum'] = typical_wat.sum(axis=1)
                            typical_wat = (typical_wat.loc[:,'HDAM':'HPHS'].div(typical_wat['sum'], axis=0))
                            # typical_wat = typical_wat[typical_wat.replace([np.inf, -np.inf], np.nan).notnull().all(axis=1)].fillna(0)
                            typical_wat = typical_wat.fillna(0)
                        return typical_wat
                    typical_wat = get_typical_hydro(typical_hydro = pd.DataFrame([typical_tech['HDAM'],typical_tech['HROR'],typical_tech['HPHS']]).transpose(),clustering='Off')

                    #%% SOLAR
                    typical_sun = pd.DataFrame(typical_tech['PHOT'])
                    typical_sun = typical_sun.loc[:,'PHOT'].div(typical_sun.loc[:,'PHOT'])
                    typical_sun = pd.DataFrame(typical_sun)

                    #%% Determine CHP max heat capacities based on P2H ratio
                    tmp_chp_max_capacities = pd.DataFrame()
                    for f_stur in ['BIO', 'HRD', 'LIG', 'PEA', 'OIL', 'WST', 'GEO']:
                        chp_max_capacities[f_stur] = capacities[f_stur] / typical_chp.loc[(typical_chp['Fuel']==f_stur) & (typical_chp['Technology']=='STUR'),'CHPPowerToHeat'].values
                    # chp_max_capacities['GAS'] = capacities['GAS'] / typical_chp.loc[(typical_chp['Fuel']== 'GAS') & (typical_chp['Technology']=='COMC'),'CHPPowerToHeat'].values
                    tmp_chp_max_capacities['GAS_COMC'] = capacities['GAS'] * typical_gas['COMC'] / typical_chp.loc[(typical_chp['Fuel']== 'GAS') & (typical_chp['Technology']=='COMC'),'CHPPowerToHeat'].values
                    tmp_chp_max_capacities['GAS_GTUR'] = capacities['GAS'] * typical_gas['GTUR'] / typical_chp.loc[(typical_chp['Fuel']== 'GAS') & (typical_chp['Technology']=='GTUR'),'CHPPowerToHeat'].values
                    tmp_chp_max_capacities['GAS_STUR'] = capacities['GAS'] * typical_gas['STUR'] / typical_chp.loc[(typical_chp['Fuel']== 'GAS') & (typical_chp['Technology']=='STUR'),'CHPPowerToHeat'].values
                    tmp_chp_max_capacities['GAS_ICEN'] = capacities['GAS'] * typical_gas['ICEN'] / typical_chp.loc[(typical_chp['Fuel']== 'GAS') & (typical_chp['Technology']=='ICEN'),'CHPPowerToHeat'].values
                    chp_max_capacities['GAS'] = tmp_chp_max_capacities.sum(axis=1)

                    def chp_heat_cap(Q,Q_max):
                        '''
                        Function that assigns heat capacity to specific fuel type based on Q < Q_max or Q => Q_max
                        This is used later on to asign remaining heat demand to other CHP technologies and fuels
                        '''
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
                    countries = list(chp_max_capacities.index)
                    Q = data_CHP_heat_capacity['Heat']
                    Q = (Q[Q.index.isin(countries)])
                    tmp = {}
                    chp_heat_capacities = pd.DataFrame()
                    chp_power_capacities = pd.DataFrame()
                    tmp_new_df_pow_gas = pd.DataFrame()
                    for f in fuels:
                        Q_max = chp_max_capacities[f]
                        tmp[f] = chp_heat_cap(Q,Q_max)
                        Q = tmp[f][1].iloc[:,0]
                        new_df = tmp[f][0]
                        if f == 'GAS':
                            # new_df_pow = new_df * typical_chp.loc[(typical_chp['Fuel']== 'GAS') & (typical_chp['Technology']=='COMC'),'CHPPowerToHeat'].values
                            tmp_new_df_pow_gas['GAS_COMC'] = new_df[f] * typical_gas['COMC'] * typical_chp.loc[(typical_chp['Fuel']== 'GAS') & (typical_chp['Technology']=='COMC'),'CHPPowerToHeat'].values
                            tmp_new_df_pow_gas['GAS_GTUR'] = new_df[f] * typical_gas['GTUR'] * typical_chp.loc[(typical_chp['Fuel']== 'GAS') & (typical_chp['Technology']=='GTUR'),'CHPPowerToHeat'].values
                            tmp_new_df_pow_gas['GAS_STUR'] = new_df[f] * typical_gas['STUR'] * typical_chp.loc[(typical_chp['Fuel']== 'GAS') & (typical_chp['Technology']=='STUR'),'CHPPowerToHeat'].values
                            tmp_new_df_pow_gas['GAS_ICEN'] = new_df[f] * typical_gas['ICEN'] * typical_chp.loc[(typical_chp['Fuel']== 'GAS') & (typical_chp['Technology']=='ICEN'),'CHPPowerToHeat'].values
                            new_df_pow = pd.DataFrame(tmp_new_df_pow_gas.sum(axis=1),columns=['GAS'])
                        else:
                            new_df_pow = new_df * typical_chp.loc[(typical_chp['Fuel']==f) & (typical_chp['Technology']=='STUR'),'CHPPowerToHeat'].values
                        chp_heat_capacities = pd.concat([chp_heat_capacities, new_df], axis=1)
                        chp_power_capacities = pd.concat([chp_power_capacities, new_df_pow], axis=1)
                    # chp_power_capacities['HYD','NUC','SUN', 'WAT','WIN']
                    chp_power_capacities.fillna(0,inplace=True)

                    no_chp_capacities = capacities.sub(chp_power_capacities,fill_value=0)
                    no_chp_capacities.fillna(0,inplace=True)
                    no_chp_capacities = no_chp_capacities.transpose()
                    chp_power_capacities = chp_power_capacities.T

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
                        tmp_BAT = pd.DataFrame(bats_cap.loc[c])
                        tmp_BAT.rename(columns={c: 'OTH'},inplace=True)
                        tmp_BAT_BEV = tmp_BEV.append(tmp_BAT)
                        tmp_other = pd.DataFrame([tmp_cap['GEO'],tmp_cap['BIO'],tmp_cap['HRD'],tmp_cap['LIG'],tmp_cap['NUC'],
                                                  tmp_cap['OIL'],tmp_cap['OTH'],tmp_cap['PEA'],tmp_cap['WST']]).transpose()
                        tmp_other.rename(index={c: 'STUR'},inplace=True)
                        df_merged = tmp_other.merge(tmp_GAS, how='outer', left_index=True, right_index=True)
                        df_merged = df_merged.merge(tmp_WAT, how='outer', left_index=True, right_index=True)
                        df_merged = df_merged.merge(tmp_WIN, how='outer', left_index=True, right_index=True)
                        df_merged = df_merged.merge(tmp_SUN, how='outer', left_index=True, right_index=True)
                        total_cap = df_merged.sum().sum()
                        min_cap = total_cap*TECHNOLOGY_THRESHOLD
                        df_merged[df_merged < min_cap] = 0
                        df_merged = df_merged.merge(tmp_BAT_BEV, how='outer', left_index=True, right_index=True,on=['OTH'])
                        cap[c] = df_merged
                        cap[c].fillna(0,inplace=True)
                        # CHP
                        tmp_cap_chp = pd.DataFrame(chp_power_capacities[c]).transpose()
                        tmp_GAS_chp = pd.DataFrame(typical_gas.loc[c])*tmp_cap_chp['GAS']
                        tmp_GAS_chp.rename(columns={c: 'GAS'},inplace=True)
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
                                    print('[INFO    ]: ' + 'Country ' + c + ' (' + i + ',' + j + '): no typical unit found, using the generic unit for the provided technology')
                                    tmp = typical[(typical.Technology == i) & (typical.Fuel=="*")]
                                    units[name] = tmp.iloc[0,:]
                                    units.loc['Technology',name],units.loc['Fuel',name]=i,j
                                elif len(typical[(typical.Technology == i) & (typical.Fuel=="*")]):
                                    print('[INFO    ]: ' + 'Country ' + c + ' (' + i + ',' + j + '): no typical unit found, using the generic unit for the provided fuel')
                                    tmp = typical[(typical.Technology == i) & (typical.Fuel=="*")]
                                    units[name] = tmp.iloc[0,:]
                                    units.loc['Technology',name],units.loc['Fuel',name]=i,j
                                elif len(typical[(typical.Technology == '*') & (typical.Fuel=="*")]):
                                    print('[INFO    ]: ' + 'Country ' + c + ' (' + i + ',' + j + '): no typical unit found, using the generic unit definition (*,*)')
                                    tmp = typical[(typical.Technology == '*') & (typical.Fuel=="*")]
                                    units[name] = tmp.iloc[0,:]
                                    units.loc['Technology',name],units.loc['Fuel',name]=i,j
                                else:
                                    print('[INFO    ]: ' + 'Country ' + c + ' (' + i + ',' + j + '): no typical unit found, no generic unit found. The entry will be discarded!!')
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
                        print('[INFO    ]: ' + 'Country ' + c + ': no units found. Skipping')
                        continue

                # CHP and TES
                    # TES_CAPACITY = 1      #No of storage hours in TES
                    cap_tot_chp = cap_chp[c]
                    units_chp = pd.DataFrame()
                    for j,i in cap_tot_chp.unstack().index:
                        if cap_tot_chp.loc[i,j]>0:
                            name = c+'_'+i+'_'+j+'_CHP'
                            tmp = typical_chp[(typical_chp.Technology == i) & (typical_chp.Fuel==j)]
                            if len(tmp)==0:
                                # try the generic entries in the dataframe:
                                if len(typical_chp[(typical_chp.Technology == i) & (typical_chp.Fuel=="*")]):
                                    print('[INFO    ]: ' + 'Country ' + c + ' (' + i + ',' + j + '): no typical CHP unit found, using the generic unit for the provided technology')
                                    tmp = typical_chp[(typical_chp.Technology == i) & (typical_chp.Fuel=="*")]
                                    units_chp[name] = tmp.iloc[0,:]
                                    units_chp.loc['Technology',name],units_chp.loc['Fuel',name]=i,j
                                elif len(typical_chp[(typical_chp.Technology == i) & (typical_chp.Fuel=="*")]):
                                    print('[INFO    ]: ' + 'Country ' + c + ' (' + i + ',' + j + '): no typical CHP unit found, using the generic unit for the provided fuel')
                                    tmp = typical_chp[(typical_chp.Technology == i) & (typical_chp.Fuel=="*")]
                                    units_chp[name] = tmp.iloc[0,:]
                                    units_chp.loc['Technology',name],units_chp.loc['Fuel',name]=i,j
                                elif len(typical_chp[(typical_chp.Technology == '*') & (typical_chp.Fuel=="*")]):
                                    print('[INFO    ]: ' + 'Country ' + c + ' (' + i + ',' + j + '): no typical CHP unit found, using the generic unit definition (*,*)')
                                    tmp = typical_chp[(typical_chp.Technology == '*') & (typical_chp.Fuel=="*")]
                                    units_chp[name] = tmp.iloc[0,:]
                                    units_chp.loc['Technology',name],units_chp.loc['Fuel',name]=i,j
                                else:
                                    print('[INFO    ]: ' + 'Country ' + c + ' (' + i + ',' + j + '): no typical CHP unit found, no generic unit found. The entry will be discarded!!')
                            elif len(tmp) ==1:
                                units_chp[name] = tmp.iloc[0,:]
                            elif len(tmp)>1:
                                print('[INFO    ]: ' + 'Country ' + c + ' (' + i + ',' + j + '): more than one typical CHP unit found, taking average')
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

                            if TES_CAPACITY == 0:
                                print('[INFO    ]: ' + 'Country ' + c + ' (' + name + '): no TES unit')
                            else:
                                # units_chp.loc['STOCapacity',name] = units_chp[name, 'PowerCapacity'].values * TES_CAPACITY
                                tmp_tes = units_chp.T
                                tmp_tes['STOCapacity'] = tmp_tes['PowerCapacity'] / tmp_tes['CHPPowerToHeat'] * TES_CAPACITY
                                tmp_tes['STOSelfDischarge'] = str(0.03)
                                units_chp.update(tmp_tes)
                    if len(units_chp)>0:
                        units_chp = units_chp.transpose()
                        del units_chp['Year']
                        units_chp.Zone=c
                        units = units.append(units_chp)
                    else:
                        print('[INFO    ]: ' + 'Country ' + c + ': no CHP units found. Skipping')


                    #%%
                    #TODO
                    # Avoid merging units at this stage, just assign units as they were before
                    # Special treatment for the hydro data.
                    # HDAM and HPHS are merged into a single unit with the total reservoir capacity
                    # Find if there are HPHS units:
                    tmp = units[units.Technology=='HPHS']
                    if len(tmp)==1:
                        hphsdata = tmp.iloc[0,:]
                        hphsindex = tmp.index[0]
                        # The pumped hydro power is also the chargin power:
                        hphsdata['STOMaxChargingPower']=hphsdata['PowerCapacity']
                        print('[INFO    ]: ' + 'Country ' + c + ' No Reservoir Capacity data for country ' + c + '. Assuming a conservative 8 hours of storage')
                        hphsdata['STOCapacity'] = hphsdata['PowerCapacity']*8
                        units.loc[hphsindex,:] = hphsdata
                    else:
                        print('[INFO    ]: ' + 'Country ' + c + ' No HPHS for country ' + c)

                    tmp = units[units.Technology=='HDAM']
                    if len(tmp)==1:
                        hphsdata = tmp.iloc[0,:]
                        hphsindex = tmp.index[0]
                        if c in reservoirs.index:
                            units.loc[tmp.index[0],'STOCapacity'] = reservoirs[c]
                        else:
                            print('[INFO    ]: ' + 'Country ' + c + ' No Reservoir Capacity data for country ' + c + '. Assuming a conservative 5 hours of storage')
                            units.loc[tmp.index[0],'STOCapacity'] = units.loc[tmp.index[0],'PowerCapacity'] * 8
                    else:
                        print('[INFO    ]: ' + 'Country ' + c + ' No HDAM for country ' + c)

                    # tmp = units[units.Technology=='HPHS']
                    # if len(tmp)==1:
                    #     hphsdata = tmp.iloc[0,:]
                    #     hphsindex = tmp.index[0]
                    #     # The pumped hydro power is also the chargin power:
                    #     hphsdata['STOMaxChargingPower']=hphsdata['PowerCapacity']
                    #     tmp = units[units.Technology=='HDAM']
                    #     if len(tmp)==1:
                    #         damdata = tmp.iloc[0,:]
                    #         # adding the dam power to the pumpe hydro:
                    #         hphsdata['PowerCapacity'] += damdata['PowerCapacity']
                    #         # delte the hdam row:
                    #         units = units[units.Technology!='HDAM']
                    #     if c in reservoirs.index:
                    #         hphsdata['STOCapacity'] = reservoirs[c]
                    #     else:
                    #         print('[INFO    ]: ' + 'Country ' + c + ' No Reservoir Capacity data for country ' + c + '. Assuming a conservative 5 hours of storage')
                    #         hphsdata['STOCapacity'] = hphsdata['PowerCapacity']*5
                    #     units.loc[hphsindex,:] = hphsdata
                    # elif len(tmp)==0:
                    #     tmp = units[units.Technology=='HDAM']
                    #     if len(tmp)==1:
                    #         if c in reservoirs.index:
                    #             units.loc[tmp.index[0],'STOCapacity'] = reservoirs[c]
                    #         else:
                    #             print('[INFO    ]: ' + 'Country ' + c + ' No Reservoir Capacity data for country ' + c + '. Assuming a conservative 5 hours of storage')
                    #             units.loc[tmp.index[0],'STOCapacity'] = units.loc[tmp.index[0],'PowerCapacity'] * 5
                    # else:
                    #     sys.exit('Various HPHS units!')

                    # Special treatment for BEVS
                    if units[units.Technology == 'BEVS'].empty == True:
                        print('[INFO    ]: ' + 'Country '+ c + ' (BEVS) capacity is 0 or BEVS are not present')
                    else:
                        tmp_bev = units[units.Technology == 'BEVS']
                        bevsindex = tmp_bev.index[0]
                        tmp_bev['STOMaxChargingPower'] = tmp_bev['PowerCapacity']
                        tmp_bev['STOCapacity'] = tmp_bev['PowerCapacity']*4618.28
                        units.update(tmp_bev)

                    # Special treatment for BATS
                    if units[units.Technology == 'BATS'].empty == True:
                        print('[INFO    ]: ' + 'Country '+ c + ' (BATS) capacity is 0 or BATS are not present')
                    else:
                        tmp_bat = units[units.Technology == 'BATS']
                        batsindex = tmp_bat.index[0]
                        tmp_bat['STOMaxChargingPower'] = tmp_bat['PowerCapacity']
                        # tmp_bat['STOCapacity'] = tmp_bat['PowerCapacity']
                        tmp_bat['STOCapacity'] = bats_stor.loc[c].values
                        units.update(tmp_bat)

                    #Sort columns as they should be and check if Zone is defined
                    cols = ['PowerCapacity', 'Unit', 'Zone', 'Technology', 'Fuel', 'Efficiency', 'MinUpTime',
                            'MinDownTime', 'RampUpRate', 'RampDownRate', 'StartUpCost_pu', 'NoLoadCost_pu',
                            'RampingCost', 'PartLoadMin', 'MinEfficiency', 'StartUpTime', 'CO2Intensity',
                            'CHPType', 'CHPPowerToHeat', 'CHPPowerLossFactor', 'STOCapacity', 'STOSelfDischarge',
                            'STOMaxChargingPower', 'STOChargingEfficiency', 'CHPMaxHeat', 'Nunits']
                    units['Zone'] = c
                    units = units[cols]

                    allunits[c]  = units

                def write_pickle_file(units,file_name):
                    '''
                    Function that creates a pickle file and saves newly created power plants
                    :units:         allunits for example
                    :file_name:     name of the pickle file (has to be a string)
                    '''
                    allunits = units
                    pkl_file = open(file_name + '.p', 'wb')
                    pickle.dump(allunits,pkl_file)
                    pkl_file.close()
                    print('[INFO    ]: ' + 'Pickle file ' + file_name + ' has been written')
                # write_pickle_file(allunits, 'Test')

                #%% Count total number of units
                def unit_count(units):
                    '''
                    Function that counts number of units (powerplants) generatd by the script
                    (This is useful to check the size of the problem)
                    :units:         allunits for example
                    '''
                    allunits = units
                    unit_count = 0
                    for c in allunits:
                        unit_count = unit_count + allunits[c]['Unit'].count()
                    print('[INFO    ]: '+'Total number of units in the region is ' + str(unit_count))

                unit_count(allunits)

                #%% Write csv file:
                def write_csv_files(power_plant_filename,units,write_csv=None):
                    '''
                    Function that generates .csv files in the Output/Database/PowerPlants/ folder
                    :power_plant_filename:      clustered for example (has to be a string)
                    :units:                     allunits for example
                    '''
                    filename = power_plant_filename + '.csv'
                    allunits = units
                    if write_csv == True:
                        for c in allunits:
                            make_dir(output_folder + 'Database')
                            folder = output_folder + 'Database/PowerPlants/'
                            make_dir(folder)
                            make_dir(folder + c)
                            allunits[c].to_csv(folder + c + '/' + filename)
                    else:
                        print('[WARNING ]: '+'WRITE_CSV_FILES = False, unable to write .csv files')

                coverage = coverage.replace(' ','_')
                write_csv_files(model + '_' + scenario + '_' + coverage + '_' + str(YEAR),allunits,WRITE_CSV_FILES)
