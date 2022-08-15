# Add the root folder of Dispa-SET-side tools to the path so that the library can be loaded:
import os
import pickle
import sys
from pathlib import Path

import dispaset as ds
import energyscope as es
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import dispaset_sidetools as dst

sys.path.append(os.path.abspath('..'))

# %% #############################################
############## Folder and Path setup #############
##################################################
dst_path = Path(__file__).parents[1]
# Typical units
typical_units_folder = dst_path / 'Inputs' / 'EnergyScope'

# Energy Scope
ES_folder = dst_path.parent / 'EnergyScope'
DST_folder = dst_path.parent / 'DispaSET-SideTools'

target_year = 2050
config_link = {'DateRange': dst.get_date_range(target_year), 'TypicalUnits': typical_units_folder}
data_folder = ES_folder / 'Data' / str(target_year)
ES_path = ES_folder / 'energyscope' / 'STEP_2_Energy_Model'
step1_output = ES_folder / 'energyscope' / 'STEP_1_TD_selection' / 'TD_of_days.out'

dispaset_version = '2.5'  # 2.5 or 2.5_BS

# %% ###################################
########### Editable inputs ############
########################################
separator = ';'
scenario = 37000
case_study = str(scenario) + '_ELEImp=0_WIND_ONOFFSHORE=70_LOCALAMONIA_NUC=4_CURT=0'
initialize_ES = True

# EnergyScope inputs
config_es = {'case_study': case_study + '_loop_0', 'comment': 'Test with low emissions', 'run_ES': False,
             'import_reserves': '', 'importing': True, 'printing': False, 'printing_td': False, 'GWP_limit': scenario,
             'data_folder': data_folder, 'ES_folder': ES_folder, 'ES_path': ES_path, 'step1_output': step1_output,
             'all_data': dict(), 'Working_directory': os.getcwd(), 'reserves': pd.DataFrame(), 'user_defined': dict()}

ES_output = config_es['ES_folder'] / 'case_studies' / config_es['case_study'] / 'output'
# %% ####################################
#### Update and Execute EnergyScope ####
########################################

# Reading the data
config_es['all_data'] = es.run_ES(config_es)
# No electricity imports
config_es['all_data']['Resources'].loc['ELECTRICITY', 'avail'] = 0
config_es['all_data']['Resources'].loc['ELEC_EXPORT', 'avail'] = 0
# Limited ammonia imports
config_es['all_data']['Resources'].loc['AMMONIA', 'avail'] = 0
config_es['all_data']['Resources'].loc['AMMONIA_RE', 'avail'] = 0
# No CCGT_AMMONIA
config_es['all_data']['Technologies'].loc['CCGT_AMMONIA', 'f_max'] = 1e15
config_es['all_data']['Technologies'].loc['NUCLEAR', 'f_max'] = 4
# config_es['all_data']['Technologies'].loc['CCGT', 'f_max'] = 10
# Allow infinite PV
config_es['all_data']['Technologies'].loc['PV', 'f_max'] = 1e15
config_es['user_defined']['solar_area'] = 1e15
config_es['user_defined']['curt_perc_cap'] = 0
# Allow infinite WIND_ONSHORE
config_es['all_data']['Technologies'].loc['WIND_ONSHORE', 'f_max'] = 70
config_es['all_data']['Technologies'].loc['WIND_OFFSHORE', 'f_max'] = 70
# Allow infinite PHS
# config_es['all_data']['Technologies'].loc['PHS', 'f_max'] = 1e15
# Change storage parameters
config_es['all_data']['Storage_characteristics'].loc['H2_STORAGE', 'storage_charge_time'] = 6
config_es['all_data']['Storage_characteristics'].loc['H2_STORAGE', 'storage_discharge_time'] = 2
config_es['all_data']['Technologies'].loc['H2_STORAGE', 'c_inv'] = 3.66
# Change prices
config_es['all_data']['Resources'].loc['GAS', 'c_op'] = 0.2

# Printing and running
config_es['importing'] = False
config_es['printing'] = True
config_es['printing_td'] = True
config_es['run_ES'] = True
if initialize_ES:
    config_es['all_data'] = es.run_ES(config_es)

# %% Assign empty variables (to be populated inside the loop)
ds_inputs = {'Capacities': dict(), 'Costs': dict(), 'ElectricityDemand': dict(), 'HeatDemand': dict(),
             'H2Demand': dict(), 'OutageFactors': dict(), 'ReservoirLevels': dict(), 'AvailabilityFactors': dict()}
inputs_mts, results_mts = dict(), dict()
inputs, results, GWP_op, reserves, shed_load, Price_CO2 = dict(), dict(), dict(), dict(), dict(), dict()
LL, Curtailment = pd.DataFrame(), pd.DataFrame()
iteration = {}

# Assign soft-linking iteration parameters
max_loops = 4

# %% ###################################
######## Soft-linking procedure ########
########################################
# for i in [2]:
#     config_es['case_study'] = case_study + '_loop_' + str(i)
for i in range(max_loops):
    print('loop number', i)

    # Dynamic Data - to be modified in a loop
    # Compute the actual average annual emission factors for each resource
    # TODO automate
    GWP_op[i] = es.compute_gwp_op(config_es['data_folder'], ES_folder / 'case_studies' / config_es['case_study'])
    GWP_op[i].to_csv(ES_folder / 'case_studies' / config_es['case_study'] / 'output' / 'GWP_op.txt', sep='\t')

    # %% Reading the ES outputs
    es_outputs = es.read_outputs(config_es['case_study'], True, [])
    es_outputs['GWP_op'] = GWP_op[i]
    es_outputs['timeseries'] = pd.read_csv(config_es['data_folder'] / 'Time_series.csv', header=0, sep=separator)
    es_outputs['demands'] = pd.read_csv(config_es['data_folder'] / 'Demand.csv', sep=separator)
    es_outputs['layers_in_out'] = pd.read_csv(config_es['data_folder'] / 'Layers_in_out.csv', sep=separator,
                                              index_col='param layers_in_out:')
    es_outputs['storage_characteristics'] = pd.read_csv(config_es['data_folder'] / 'Storage_characteristics.csv',
                                                        sep=separator, index_col='param :')
    es_outputs['storage_eff_in'] = pd.read_csv(config_es['data_folder'] / 'Storage_eff_in.csv',
                                               sep=separator, index_col='param storage_eff_in :')
    es_outputs['storage_eff_out'] = pd.read_csv(config_es['data_folder'] / 'Storage_eff_out.csv',
                                                sep=separator, index_col='param storage_eff_out:')
    es_outputs['high_t_Layers'] = pd.read_csv(ES_folder / 'case_studies' / config_es['case_study'] / 'output' /
                                              'hourly_data' / 'layer_HEAT_HIGH_T.txt', delimiter='\t', index_col=[0, 1])
    es_outputs['low_t_decen_Layers'] = pd.read_csv(ES_folder / 'case_studies' / config_es['case_study'] / 'output' /
                                                   'hourly_data' / 'layer_HEAT_LOW_T_DECEN.txt', delimiter='\t',
                                                   index_col=[0, 1])
    es_outputs['low_t_dhn_Layers'] = pd.read_csv(ES_folder / 'case_studies' / config_es['case_study'] / 'output' /
                                                 'hourly_data' / 'layer_HEAT_LOW_T_DHN.txt', delimiter='\t',
                                                 index_col=[0, 1])

    # TODO update with new possibility of changing output folder
    # Clean ES outputs i.e. remove blank spaces
    es_outputs['assets'] = dst.clean_blanks(es_outputs['assets'])
    es_outputs['year_balance'] = dst.clean_blanks(es_outputs['year_balance'])
    es_outputs['layers_in_out'] = dst.clean_blanks(es_outputs['layers_in_out'])
    es_outputs['storage_characteristics'] = dst.clean_blanks(es_outputs['storage_characteristics'])
    es_outputs['storage_eff_in'] = dst.clean_blanks(es_outputs['storage_eff_in'])
    es_outputs['storage_eff_out'] = dst.clean_blanks(es_outputs['storage_eff_out'])
    es_outputs['high_t_Layers'] = dst.clean_blanks(es_outputs['high_t_Layers'], idx=False)
    es_outputs['low_t_decen_Layers'] = dst.clean_blanks(es_outputs['low_t_decen_Layers'], idx=False)
    es_outputs['low_t_dhn_Layers'] = dst.clean_blanks(es_outputs['low_t_dhn_Layers'], idx=False)

    # transforming TD time series into yearly time series
    td_df = dst.process_TD(td_final=pd.read_csv(config_es['step1_output'], header=None))

    # %% compute fuel prices according to the use of RE vs NON-RE fuels
    resources = config_es['all_data']['Resources']
    df = es_outputs['year_balance'].loc[resources.index, es_outputs['year_balance'].columns.isin(list(resources.index))]
    ds_inputs['Costs'][i] = (df.mul(resources.loc[:, 'c_op'], axis=0).sum(axis=0) /
                             df.sum(axis=0)).fillna(resources.loc[:, 'c_op'])

    # %% Compute availability factors and scaled inflows
    ds_inputs['AvailabilityFactors'][i] = dst.get_availability_factors(es_outputs, config_link['DateRange'],
                                                                       file_name_af='AF_2015_ES',
                                                                       file_name_sif='IF_2015_ES')

    # %% Compute electricity demand
    es_outputs['electricity_layers'] = pd.read_csv(ES_folder / 'case_studies' / config_es['case_study'] / 'output' /
                                                   'hourly_data' / 'layer_ELECTRICITY.txt', delimiter='\t',
                                                   index_col=[0, 1])
    ds_inputs['ElectricityDemand'][i] = dst.get_electricity_demand(es_outputs, td_df, config_link['DateRange'],
                                                                   file_name='2015_ES')

    # %% compute H2 yearly consumption and power capacity of electrolyser
    es_outputs['h2_layer'] = pd.read_csv(ES_folder / 'case_studies' / config_es['case_study'] / 'output' /
                                         'hourly_data' / 'layer_H2.txt', delimiter='\t', index_col=[0, 1])
    ds_inputs['H2Demand'][i] = dst.get_h2_demand(es_outputs['h2_layer'], td_df, config_link['DateRange'],
                                                 dispaset_version=dispaset_version)

    # %% Get capacities from ES, map them to DS with external typical unit database
    typical_units = pd.read_csv(config_link['TypicalUnits'] / 'Typical_Units.csv')
    ds_inputs['Capacities'][i] = dst.get_capacities_from_es(es_outputs, typical_units=typical_units, td_df=td_df,
                                                            technology_threshold=0.1, dispaset_version=dispaset_version,
                                                            config_link=config_link)  # TODO: remove really small technologies

    # %% Assign outage factors for technologies that generate more than available
    ds_inputs['OutageFactors'][i] = dst.get_outage_factors(config_es, es_outputs, drange=config_link['DateRange'],
                                                           local_res=['WASTE', 'WOOD', 'WET_BIOMASS'], td_df=td_df)

    # %% Compute heat demand for different heating layers
    ds_inputs['HeatDemand'][i] = dst.get_heat_demand(es_outputs, td_df, config_link['DateRange'],
                                                     countries=['ES'], file_name='2015_ES_th',
                                                     dispaset_version=dispaset_version)

    # %% Assign storage levels
    ds_inputs['ReservoirLevels'][i] = dst.get_soc(es_outputs, config_es, config_link['DateRange'])

    # %% ###################################
    ########## Execute Dispa-SET ##########
    #######################################
    # Load the appropriate configuration file (2.5 or boundary sector version)
    if dispaset_version == '2.5':
        config = ds.load_config('../ConfigFiles/Config_EnergyScope.xlsx')
    if dispaset_version == '2.5_BS':
        config = ds.load_config('../ConfigFiles/Config_EnergyScope_BS.xlsx')
    # Assign new input csv files if needed
    config['ReservoirLevels'] = str(DST_folder / 'Outputs' / 'EnergyScope' / 'Database' / 'ReservoirLevels' / '##' /
                                    'ReservoirLevels.csv')

    config['SimulationDirectory'] = str(DST_folder / 'Simulations' / str(case_study + '_loop_' + str(i)))
    config['default']['PriceOfCO2'] = abs(es_outputs['CO2_cost'].loc['CO2_cost', 'CO2_cost'] * 1000)
    config['default']['CostCurtailment'] = abs(es_outputs['Curtailment_cost'].loc['Curtailment_cost',
                                                                                  'Curtailment_cost'] * 1000)
    for j in dst.mapping['FUEL_COST']:
        config['default'][dst.mapping['FUEL_COST'][j]] = ds_inputs['Costs'][i].loc[j] * 1000

    #%% Dispa-SET version 2.5
    if dispaset_version == '2.5':
        config['H2FlexibleDemand'] = str(DST_folder / 'Outputs' / 'EnergyScope' / 'Database' / 'H2_demand' / 'ES' /
                                         'H2_demand.csv')
        config['H2FlexibleCapacity'] = str(DST_folder / 'Outputs' / 'EnergyScope' / 'Database' / 'H2_demand' / 'ES' /
                                           'PtLCapacities.csv')
        config['Outages'] = str(DST_folder / 'Outputs' / 'EnergyScope' / 'Database' / 'OutageFactor' / '##' /
                                'OutageFactor.csv')

    #%% Dispa-SET version boundary sector
    if dispaset_version == '2.5_BS':
        # config['BoundarySectorDemand'] = 137
        config['BoundarySectorData'] = str(DST_folder / 'Outputs' / 'EnergyScope' / 'Database' / 'H2_demand' / 'ES' /
                                           'PtLCapacities.csv')
        # config['BoundarySectorNTC'] = 139
        # config['BoundarySectorInterconnections'] = 140
        config['BSFlexibleDemand'] = str(DST_folder / 'Outputs' / 'EnergyScope' / 'Database' / 'H2_demand' / 'ES' /
                                         'H2_demand.csv')
        # config['BSFlexibleSupply'] = 142
        # config['CostBoundarySectorSlack'] = 170

    # Build the simulation environment:
    SimData = ds.build_simulation(config)

    # Solve using GAMS:
    _ = ds.solve_GAMS(config['SimulationDirectory'], config['GAMS_folder'])

    # Load the simulation results:
    inputs_mts[i], results_mts[i] = ds.get_sim_results(config, cache=False, inputs_file='Inputs_MTS.p',
                                                       results_file='Results_MTS.gdx')
    inputs[i], results[i] = ds.get_sim_results(config, cache=False)

    # %% Save DS results to pickle file
    ES_output = ES_folder / 'case_studies' / config_es['case_study'] / 'output'
    with open(ES_output / 'DS_Results.p', 'wb') as handle:
        pickle.dump(inputs[i], handle, protocol=pickle.HIGHEST_PROTOCOL)
        pickle.dump(results[i], handle, protocol=pickle.HIGHEST_PROTOCOL)

    # TODO: reading and storing ESTD results

    # %% Run ES with reserves (2nd+ run)
    config_es['case_study'] = case_study + '_loop_' + str(i + 1)
    config_es['import_reserves'] = 'from_df'
    # TODO: check if leap year can be introduced
    reserves[i] = pd.DataFrame(results[i]['OutputDemand_3U'].values / 1000, columns=['end_uses_reserve'],
                               index=np.arange(1, 8761, 1))
    # Check if it is necessary to apply additional reserve requirements
    if i >= 1:
        if results[i]['OutputShedLoad'].empty:
            shed_load[i] = pd.DataFrame(0, columns=['end_uses_reserve'], index=np.arange(1, 8761, 1))
        else:
            shed_load[i] = pd.DataFrame(results[i]['OutputShedLoad'].values / 1000, columns=['end_uses_reserve'],
                                        index=np.arange(1, 8761, 1))
        config_es['reserves'] = config_es['reserves'] + shed_load[i].max()
    else:
        config_es['reserves'] = reserves[i]

    with open('ES_reserve_' + case_study + '_loop_' + str(i) + '.p', 'wb') as handle:
        pickle.dump(config_es['reserves'], handle, protocol=pickle.HIGHEST_PROTOCOL)

    LL = pd.concat([LL, results[i]['OutputShedLoad']], axis=1)
    Curtailment = pd.concat([Curtailment, results[i]['OutputCurtailedPower']], axis=1)

    if (results[i]['OutputOptimizationCheck'].abs() > 0).any():
        print('Another iteration required')
    else:
        print('Final convergence occurred in loop: ' + str(i) + '. Soft-linking is now complete')
        break

    # %% Brake loop at the maximum loops specified
    if i == max_loops - 1:
        print('Last opt')
    else:
        config_es['all_data'] = es.run_ES(config_es)

with open(case_study + '.p', 'wb') as handle:
    pickle.dump(inputs, handle, protocol=pickle.HIGHEST_PROTOCOL)
    pickle.dump(results, handle, protocol=pickle.HIGHEST_PROTOCOL)
    pickle.dump(inputs_mts, handle, protocol=pickle.HIGHEST_PROTOCOL)
    pickle.dump(results_mts, handle, protocol=pickle.HIGHEST_PROTOCOL)

aa=pd.DataFrame()
for i in range(max_loops):
    for j in ['COMC', 'GTUR']:
        tmp = inputs[i]['units'].loc[(inputs[i]['units']['Technology']==j) & (inputs[i]['units']['Fuel']=='GAS')]
        aa.loc[i, [j+'_GAS']] = (tmp['PowerCapacity'] * tmp['Nunits']).values[0]

aa['Total'] = aa.sum(axis=1)

# with open(case_study + '.p', 'rb') as handle:
#     inputs = pickle.load(handle)
#     results = pickle.load(handle)
#     inputs_mts = pickle.load(handle)
#     results_mts = pickle.load(handle)

# ENS_max = pd.DataFrame()
# LL = pd.DataFrame()
# LostLoad = pd.DataFrame()
# Generation = {'Ele': pd.DataFrame(),
#               'Heat': pd.DataFrame()}
# Emissions = pd.DataFrame()
# for i in range(max_loops):
#     ENS_max.loc[i, 'Error>Accuracy'] = results[i]['OutputOptimizationError'].max()
#     # ENS_max.loc[i, 'ENS'] = results[i]['OutputShedLoad'].sum(axis=0).values + \
#     #                         results[i]['OutputHeatSlack'].sum(axis=0).values
#     if not (results[i]['OutputHeatSlack'].empty) and (results[i]['OutputShedLoad'].empty):
#         LostLoad = results[i]['OutputShedLoad'] + results[i]['OutputHeatSlack'].values
#     if not results[i]['OutputShedLoad'].empty:
#         LostLoad = results[i]['OutputShedLoad']
#     ENS_max.loc[i, 'ENS'] = LostLoad.sum(axis=0).values / 1e3
#     LL = pd.concat([LL, LostLoad], axis=1)
#     tmp = ds.plot_energy_zone_fuel(inputs[i], results[i], ds.get_indicators_powerplant(inputs[i], results[i]))
#     Generation['Ele'] = pd.concat([Generation['Ele'], tmp[0]], axis=0)
#     Generation['Heat'] = pd.concat([Generation['Heat'], tmp[1]], axis=0)
#     Emissions.loc[i, 'CO2'] = results[i]['OutputEmissions'].sum().sum()
#
# LL = LL / 1e3
# Generation['Ele'].reset_index(inplace=True, drop=True)
# Generation['Ele'] = Generation['Ele'].loc[:, (Generation['Ele'] != 0).any(axis=0)]
# cols_ele = Generation['Ele'].columns
# Generation['Ele'].loc[:, 'Iteration'] = Generation['Ele'].index
# Generation['Ele'].loc[:, 'Scenario'] = '12.5 kTCO2'
# Generation['Ele'].loc[:, 'Zone'] = 'ELE'
# Generation['Heat'] = Generation['Heat'].loc[:, (Generation['Heat'] != 0).any(axis=0)]
# cols_heat = Generation['Heat'].columns
# Generation['Heat'].loc[:, 'Iteration'] = np.arange(len(Generation['Heat'])) // 3 + 1
# Generation['Heat'].loc[:, 'Iteration'] = Generation['Heat'].loc[:, 'Iteration'] - 1
# Generation['Heat'].loc[:, 'Scenario'] = '12.5 kTCO2'
# Generation['Heat'].loc[:, 'Zone'] = Generation['Heat'].index
# Generation['Heat'].reset_index(inplace=True, drop=True)
#
# Ele_pivot = pd.melt(Generation['Ele'], id_vars=['Scenario', 'Iteration', 'Zone'], value_vars=cols_ele,
#                     value_name='Generation')
# Heat_pivot = pd.melt(Generation['Heat'], id_vars=['Scenario', 'Iteration', 'Zone'], value_vars=cols_heat,
#                      value_name='Generation')
#
# # Generation_pivot = pd.pivot_table(df, values='S', index=['P', 'Q'], columns=['R'], aggfunc=np.sum)
#
#
# Plots
import pandas as pd

rng = pd.date_range('2015-1-1', '2015-12-31', freq='H')
# Generate country-specific plots
ds.plot_zone(inputs[3], results[3], rng=rng, z_th='ES_DHN')
#
# # Bar plot with the installed capacities in all countries:
# cap = ds.plot_zone_capacities(inputs[2], results[2])
#
# # Bar plot with installed storage capacity
# sto = ds.plot_tech_cap(inputs[2])
#
# # Violin plot for CO2 emissions
# ds.plot_co2(inputs[3], results[3], figsize=(9, 6), width=0.9)
#
# # Bar plot with the energy balances in all countries:
# GenPerZone = ds.plot_energy_zone_fuel(inputs[3], results[3], ds.get_indicators_powerplant(inputs[3], results[3]))
#
# # Analyse the results for each country and provide quantitative indicators:
# r = ds.get_result_analysis(inputs[0], results[0])
#
# # Create figure and subplot manually
# fig, host = plt.subplots(figsize=(8, 4))  # (width, height) in inches
# # (see https://matplotlib.org/3.3.3/api/_as_gen/matplotlib.pyplot.subplots.html)
#
# par1 = host.twinx()
# par2 = host.twinx()
#
# host.set_xlim(0, 3)
# host.set_ylim(0, ENS_max['Error>Accuracy'].max() * 1.02)
# par1.set_ylim(0, LL.sum().max() * 1.03)
# par2.set_ylim(0, LL.max().max() * 1.03)
#
# host.set_xlabel("Iteration")
# host.set_ylabel("Error>Accuracy [EUR]")
# par1.set_ylabel("ENS [GWh]")
# par2.set_ylabel("ENS_max [GW]")
#
# color1 = plt.cm.viridis(0.9)
# color2 = plt.cm.viridis(0.5)
# color3 = plt.cm.viridis(0)
#
# # TODO automatise
# p1, = host.plot(ENS_max.index, ENS_max.loc[:, 'Error>Accuracy'], color=color1, label='Error>Accuracy')
# p2, = par1.plot(ENS_max.index, LL.sum().values, color=color2, label="ENS")
# p3, = par2.plot(ENS_max.index, LL.max().values, color=color3, label="ENS_max")
#
# lns = [p1, p2, p3]
# host.legend(handles=lns, loc='best')
#
# # right, left, top, bottom
# par2.spines['right'].set_position(('outward', 60))
#
# # no x-ticks
# par2.xaxis.set_ticks([0, 1, 2, 3])
#
# host.yaxis.label.set_color(p1.get_color())
# par1.yaxis.label.set_color(p2.get_color())
# par2.yaxis.label.set_color(p3.get_color())
#
# # plt.axhline(y=850, color='r', linestyle='dashed', label='Optimality treshold')
#
# plt.title('Optimality gap = 0.05%')
#
# # Adjust spacings w.r.t. figsize
# fig.tight_layout()
# # Alternatively: bbox_inches='tight' within the plt.savefig function
# #                (overwrites figsize)
#
# # Best for professional typesetting, e.g. LaTeX
# # plt.savefig("0.005.png")
# # For raster graphics use the dpi argument. E.g. '[...].png", dpi=200)'
#
# plt.show()
#
# bb = pd.DataFrame()
# CF = {}
# for i in range(0, max_loops):
#     aa = inputs[i]['units'].loc[:, ['PowerCapacity', 'Nunits', 'Fuel', 'Technology']]
#     aa.to_csv('Capacity_' + str(scenario) + '_' + str(i) + '.csv')
#
#     CF[i] = results[i]['OutputPower'].sum() / (
#             inputs[i]['units'].loc[:, 'PowerCapacity'] * inputs[i]['units'].loc[:, 'Nunits']) / 8760
#     CF[i].fillna(0, inplace=True)
#
#     CF[i].to_csv('CF_' + str(scenario) + '_' + str(i) + '.csv')
#
# import pandas as pd
# from plotnine import *
#
# scenario = '37.5 kTCO2'
#
# mix1 = pd.read_csv("PivotTable_Generation.csv")
# # mix_min_max1 = pd.read_csv("data_figure13_minmax.csv")
# # mix_min_max1['min'] = mix_min_max1['min'] * 100
# # mix_min_max1['max'] = mix_min_max1['max'] * 100
# cat_order = ['BIO', 'GEO', 'NUC', 'PEA', 'OIL', 'GAS', 'HRD', 'OTH', 'AIR', 'WST', 'WAT', 'SUN', 'WIN']
# mix1['variable'] = pd.Categorical(mix1['variable'], categories=cat_order, ordered=True)
#
# if scenario == '37.5 kTCO2':
#     mix = mix1[mix1['Scenario'] != '12.5 kTCO2']
#     # mix_min_max1['Label'] = mix_min_max1['min'].round(1).astype(str) + '% - ' + mix_min_max1['max'].round(1).astype(
#     #     str) + '%'
#     # mix_min_max = mix_min_max1[mix_min_max1['Scenario'] != "Connected"]
# else:
#     mix = mix1[mix1['Scenario'] != 'Baseline']
#     # mix_min_max1['Label'] = mix_min_max1['min'].round(1).astype(str) + '% - ' + mix_min_max1['max'].round(1).astype(
#     #     str) + '%'
#     # mix_min_max = mix_min_max1[mix_min_max1['Scenario'] != "Baseline"]
#
# mix.reset_index(inplace=True)
# # mix_min_max.reset_index(inplace=True)
#
# fuel_cmap = {'LIG': '#af4b9180', 'PEA': '#af4b9199', 'HRD': 'darkviolet', 'OIL': 'magenta',
#              'GAS': '#d7642dff',
#              'NUC': '#466eb4ff',
#              'SUN': '#e6a532ff',
#              'WIN': '#41afaaff',
#              'WAT': '#00a0e1ff',
#              'BIO': '#7daf4bff', 'GEO': '#7daf4bbf',
#              'Storage': '#b93c46ff', 'FlowIn': '#b93c46b2', 'FlowOut': '#b93c4666',
#              'OTH': '#b9c33799', 'WST': '#b9c337ff',
#              'HDAM': '#00a0e1ff',
#              'HPHS': 'blue',
#              'THMS': '#C04000ff',
#              'BATS': '#41A317ff',
#              'BEVS': '#b9c33799'}
#
# g = (ggplot(mix) +
#      aes(x=mix['Iteration'], y=mix['Generation'], fill=mix['variable']) +
#      geom_bar(stat="identity", width=1, size=0.15, color="black") +
#      facet_wrap('Zone', ncol=2, scales="free_x") +
#      scale_y_continuous(labels=lambda l: ["%d%%" % (v * 100) for v in l]) +
#      scale_fill_manual(values=fuel_cmap, name="") +
#      labs(title=scenario,
#           x="Rank (climate years sorted by \n renewable energy generation)",
#           y="Share of annual generation (%)",
#           fill='Fuel') +
#      theme_minimal() +
#      # geom_hline(mix_min_max, aes(yintercept=mix_min_max['max'] / 100), color='white') +
#      # geom_hline(mix_min_max, aes(yintercept=mix_min_max['min'] / 100), color='white') +
#      # annotate('text', x=19, y=0.5, color="white", size=10, label=mix_min_max['Label']) +
#      # theme(axis_text_x=element_text(vjust=0), legend_margin=0, subplots_adjust={'wspace': 0.10, 'hspace': 0.25},
#      #       legend_position=(.5, 0), legend_direction='horizontal') +
#      coord_flip() +
#      guides(fill=guide_legend(nrow=1, reverse=True))
#      )
#
# g
#
# if scenario == 'Baseline':
#     (ggsave(g, "figure13_Baseline.png", width=15.5 / 2.5, height=12 / 2.5))
# else:
#     (ggsave(g, "figure13_Connected.png", width=15.5 / 2.5, height=12 / 2.5))
#
# import calendar
# from plotnine import *
#
# aa = pd.DataFrame()
# for itteration in [0, 3]:
#     df = results[itteration]['ShadowPrice']
#     df['Month'] = df.index.month
#     df['Day'] = df.index.dayofyear
#     df['Hour'] = df.index.hour
#     df['Zone'] = 'ES_ELE'
#     if itteration == 0:
#         df['Iteration'] = 'No Reserve'
#     elif itteration == 1:
#         df['Iteration'] = 'Initialization'
#     else:
#         df['Iteration'] = 'Iteration ' + str(itteration - 1)
#
#     df1 = results[itteration]['HeatShadowPrice']
#     df1['Month'] = df1.index.month
#     df1['Day'] = df1.index.dayofyear
#     df1['Hour'] = df1.index.hour
#     df1 = pd.melt(df1, id_vars=['Month', 'Day', 'Hour'], value_vars=['ES_DEC', 'ES_DHN', 'ES_IND'], value_name='ES',
#                   var_name='Zone')
#     if itteration == 0:
#         df1['Iteration'] = 'No Reserve'
#     elif itteration == 1:
#         df1['Iteration'] = 'Initialization'
#     else:
#         df1['Iteration'] = 'Iteration ' + str(itteration - 1)
#
#     aa = pd.concat([aa, df, df1])
#
# aa.reset_index(inplace=True, drop=True)
# aa['Month'] = aa['Month'].apply(lambda x: calendar.month_abbr[x])
# cat_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
# aa['Month'] = pd.Categorical(aa['Month'], categories=cat_order, ordered=True)
# aa['Iteration'] = pd.Categorical(aa['Iteration'], categories=['No Reserve', 'Iteration 2'], ordered=True)
# aa['Zone'] = pd.Categorical(aa['Zone'], categories=['ES_ELE', 'ES_DEC', 'ES_DHN', 'ES_IND'], ordered=True)
#
# aa.rename({'ES': 'EUR/MWh'}, axis='columns', inplace=True)
#
# # %% Build the plot
# g = (ggplot(aa, aes(x='Day', y='Hour', fill='EUR/MWh'))
#      + geom_tile(color='white', size=.01)
#      + facet_grid('Zone ~ Iteration')
#      # + labs(title='Shadow Prices in Electricity and Heating zones')
#      # + scale_fill_cmap('plasma')
#      + scale_y_continuous(breaks=(0, 6, 12, 18, 24))
#      + scale_x_continuous(breaks=(0, 91, 182, 273, 365))
#      + scale_fill_gradient2(low="green", mid="lightblue", high="red",
#                             midpoint=200,
#                             breaks=(0, 100, 200, 300, 400),
#                             limits=(0, 420))
#      + theme_minimal()
#      + theme(legend_position='right',
#              plot_title=element_text(size=10),
#              legend_title=element_text(size=8)
#              # axis_text_y = element_text(size=10)
#              )
#      )
#
# g
#
# (ggsave(g, "ShadowPrice_" + str(scenario) + '.png', width=11.5 / 2.5, height=11.5 / 2.5, dpi=300))
#
# bb = pd.DataFrame()
# for itteration in range(4):
#     df2 = pd.DataFrame(results[itteration]['OutputOptimizationError'], columns=['Error'])
#     df2.reset_index(inplace=True, drop=True)
#     df2.drop(df2.tail(1).index, inplace=True)
#     df2[df2 > 50000] = 50000
#     df2[df2 < -50000] = -50000
#     df2.loc[:, 'RollingHorizon'] = df2.index
#     df2.loc[:, 'Iteration'] = str(itteration)
#     # df2.loc[:, 'Iteration'] = itteration
#     bb = pd.concat([bb, df2])
#
# bb['Error'] = bb['Error'].astype(float)
#
# g2 = (ggplot(bb, aes(y='RollingHorizon', x='Iteration', fill='Error'))
#       + geom_tile(color='white', size=.01)
#       # + facet_grid('Zone ~ Iteration')
#       # + labs(title='Shadow Prices in Electricity and Heating zones')
#       # + scale_fill_cmap('plasma')
#       # + scale_y_continuous(breaks=(0,6,12,18,24))
#       + scale_y_continuous(breaks=(0, 11, 22, 33, 44, 55, 66, 77, 88, 99, 110, 121))
#       + xlab("")
#       + scale_fill_gradient2(low="green", mid="lightblue", high="red",
#                              midpoint=0,
#                              breaks=(-50000, 0, 50000),
#                              limits=(-50000, 50000))
#       + theme_minimal()
#       + theme(legend_position='right',
#               plot_title=element_text(size=10),
#               legend_title=element_text(size=8),
#               # axis_text_y = element_text(size=10)
#               )
#       )
#
# g2
#
# (ggsave(g2, "ItterationError_" + str(scenario) + '.png', width=11.5 / 2.5, height=6.5 / 2.5, dpi=300))
#
# N = 24 * 3
# cc = pd.DataFrame()
# for i in range(4):
#     results[i]['OutputShedLoad'].set_index('index', inplace=True)
#     df3 = results[i]['OutputShedLoad']
#     df3.reset_index(inplace=True)
#     df3 = df3.groupby(df3.index // N).sum()
#     df3.loc[:, 'Iteration'] = i
#     df3.loc[:, 'RollingHorizon'] = df3.index
#     cc = pd.concat([cc, df3])
#
# cc = cc.rename(columns={'ES': 'ENS'})
# cc['ENS'] = cc['ENS'].astype(float)
#
# ENS_max.loc[:, 'Iteration'] = ENS_max.index
#
# g3 = (ggplot(ENS_max, aes(x='Iteration', y='ENS'))
#       + geom_col(fill='red')
#       + scale_y_reverse()
#       + theme_minimal()
#       + ylab('ENS [GWh]')
#       + theme(legend_position='right',
#               legend_title=element_text(size=8)
#               # axis_text_y = element_text(size=10)
#               )
#       )
#
# g3
#
# (ggsave(g3, "ENS_" + str(scenario) + '.png', width=11.5 / 2.5, height=5.3 / 2.5, dpi=300))
#
# import networkx as nx
#
# G = nx.Graph()
# G.add_nodes_from([("A", {'label': 'a'}), ("B", {'label': 'b'}),
#                   ("C", {'label': 'c'})])
#
# G.add_edges_from([("A", "B"), ("A", "C")])
#
# H = nx.Graph()
# H.add_nodes_from([("X", {'label': 'a'}), ("Y", {'label': 'y'}),
#                   ("Z", {'label': 'z'})])
# H.add_edges_from([("X", "Y"), ("X", "Z")])
#
#
# # This is the function which checks for equality of labels
# def return_eq(node1, node2):
#     return node1['label'] == node2['label']
#
#
# print(nx.graph_edit_distance(G, H, node_match=return_eq))
# # Output: 3
