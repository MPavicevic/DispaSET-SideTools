# Add the root folder of Dispa-SET-side tools to the path so that the library can be loaded:
import logging
import sys, os

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
import dispaset as ds
import dispaset_sidetools as dst
import energyscope as es
import pickle


sys.path.append(os.path.abspath('..'))

# %% ###################################
############## Path setup #############
#######################################
dst_path = Path(__file__).parents[1]
# Typical units
typical_units_folder = dst_path / 'Inputs' / 'EnergyScope'
scenario = 37500
case_study = str(scenario) + '_ElecImport=0_WIND_ONSHORE_and_PHS_fmax=1e15'

# Energy Scope
ES_folder = dst_path.parent / 'EnergyScope'
DST_folder = dst_path.parent / 'DispaSET-SideTools'

year = 2050
data_folder = ES_folder / 'Data' / str(year)
ES_path = ES_folder / 'energyscope' / 'STEP_2_Energy_Model'
step1_output = ES_folder / 'energyscope' / 'STEP_1_TD_selection' / 'TD_of_days.out'

# %% ###################################
########### Editable inputs ###########
#######################################
config_es = {'case_study': case_study+ '_loop_0',
             # Name of the case study. The outputs will be printed into : config['ES_path']+'\output_'+config['case_study']
             'comment': 'Test with low emissions',
             'run_ES': False,
             'import_reserves': '',
             'importing': True,
             'printing': False,
             'printing_td': False,
             'GWP_limit': scenario,  # [ktCO2-eq./year]	# Minimum GWP reduction
             'data_folder': data_folder,  # Folders containing the csv data files
             'ES_folder': ES_folder,  # Path to th directory of energyscope
             'ES_path': ES_path,  # Path to the energy model (.mod and .run files)
             'step1_output': step1_output,  # Output of the step 1 selection of typical days
             'all_data': dict(),
             'Working_directory': os.getcwd(),
             'reserves': pd.DataFrame(),
             'user_defined': dict()
             }

# %% ####################################
#### Update and Execute EnergyScope ####
########################################


# Reading the data
config_es['all_data'] = es.run_ES(config_es)
# No electricity imports
config_es['all_data']['Resources'].loc['ELECTRICITY', 'avail'] = 0
config_es['all_data']['Resources'].loc['ELEC_EXPORT', 'avail'] = 0
# No CCGT_AMMONIA
config_es['all_data']['Technologies'].loc['CCGT_AMMONIA', 'f_max'] = 0
# Allow infinite PV
# config_es['all_data']['Technologies'].loc['CCGT', 'f_max'] = 15
# config_es['user_defined']['solar_area'] = 1e15
#
# Allow infinite WIND_ONSHORE
config_es['all_data']['Technologies'].loc['WIND_ONSHORE', 'f_max'] = 1e15
# Allow infinite PHS
config_es['all_data']['Technologies'].loc['PHS', 'f_max'] = 1e15

# Printing and running
config_es['importing'] = False
config_es['printing'] = True
config_es['printing_td'] = True
config_es['run_ES'] = True
# config_es['all_data'] = es.run_ES(config_es)

# Static Data - to be created only once
el_demand = dst.get_demand_from_es(config_es)
# th_demand = dst.get_heat_demand_from_es(config_es)
af = dst.get_availability_factors_from_es(config_es)

inputs = dict()
results = dict()
GWP_op = dict()
capacities = dict()
reserves = dict()
shed_load = dict()
Price_CO2 = dict()

LL = pd.DataFrame()
Curtailment = pd.DataFrame()
end = 4
iteration = {}

for i in range(end):
    print('loop number', i)

    # Dynamic Data - to be modified in a loop
    # compute the actual average annual emission factors for each resource
    GWP_op[i] = es.compute_gwp_op(config_es['data_folder'], ES_folder / 'case_studies' / config_es['case_study'])
    GWP_op[i].to_csv(ES_folder / 'case_studies' / config_es['case_study'] / 'output' / 'GWP_op.txt',
                     sep='\t')  # TODO automate
    # Reading the ES outputs
    es_outputs = es.read_outputs(config_es['case_study'], True, [])
    # TODO update with new possibility of changing output folder
    assets = pd.read_csv(ES_folder / 'case_studies' / config_es['case_study'] / 'output' / 'assets.txt',
                          delimiter='\t', skiprows=[1], index_col=False).set_index('TECHNOLOGIES') #TODO: improve get_capacities (read outputs from ES -> function to convert to DS syntax)
    assets.rename(columns=lambda x: x.strip(), inplace=True)
    assets.rename(index=lambda x: x.strip(), inplace=True)
    capacities[i] = dst.get_capacities_from_es(config_es, typical_units_folder=typical_units_folder,
                                               TECHNOLOGY_THRESHOLD=0.1) #TODO: remove really small technologies
    Price_CO2[i] = pd.read_csv(ES_folder / 'case_studies' / config_es['case_study'] / 'output' / 'CO2_cost.txt',
                               delimiter='\t', header=None)


    # compute fuel prices according to the use of RE vs NON-RE fuels
    yearbal = pd.read_csv(ES_folder / 'case_studies' / config_es['case_study'] / 'output' / 'year_balance.txt',
                          delimiter='\t', index_col='Tech')
    yearbal.rename(columns=lambda x: x.strip(), inplace=True)
    yearbal.rename(index=lambda x: x.strip(), inplace=True)
    resources = config_es['all_data']['Resources']
    df = yearbal.loc[resources.index, yearbal.columns.isin(list(resources.index))]
    costs = (df.mul(resources.loc[:, 'c_op'], axis=0).sum(axis=0) / df.sum(axis=0)).fillna(resources.loc[:, 'c_op'])

    # compute H2 yearly consumption and power capacity of electrolyser
    h2_layer = pd.read_csv(ES_folder / 'case_studies' / config_es['case_study'] / 'output' / 'hourly_data' /
                           'layer_H2.txt', delimiter='\t', index_col=[0, 1])
    h2_layer.rename(columns=lambda x: x.strip(), inplace=True)
    h2_layer.drop(columns=['H2_STORAGE_Pin', 'H2_STORAGE_Pout'], inplace=True)
    # computing consumption of H2
    h2_td = pd.DataFrame(-h2_layer[h2_layer < 0].sum(axis=1), columns=['ES_H2'])  # TODO automatise name zone assignment
    # transforming TD time series into yearly time series
    td_final = pd.read_csv(config_es['step1_output'], header=None)
    TD_DF = dst.process_TD(td_final)
    h2_ts = TD_DF.loc[:, ['TD', 'hour']]
    h2_ts = h2_ts.merge(h2_td, left_on=['TD', 'hour'], right_index=True).sort_index()
    h2_ts.drop(columns=['TD', 'hour'], inplace=True)
    dst.write_csv_files('H2_demand', h2_ts * 1000, 'H2_demand', index=True, write_csv=True)

    # compute outage factors for technologies using local resources (WOOD, WET_BIOMASS, WASTE)
    def compute_OutageFactor(config_es, assets, layer_name:str):
        """Computes the Outage Factor in a layer for each TD

        """
        layer = es.read_layer(config_es['case_study'], 'layer_'+layer_name).dropna(axis=1)
        layer = layer.loc[:, layer.min(axis=0) < -0.01]
        layer = layer / config_es['all_data']['Layers_in_out'].loc[
            layer.columns, layer_name]  # compute GWh of output layer
        layer = 1 - layer / assets.loc[layer.columns, 'f']
        return layer.loc[:,layer.max(axis=0)>1e-3]

    local_res = ['WASTE', 'WOOD', 'WET_BIOMASS']
    OutageFactors = compute_OutageFactor(config_es, assets, local_res[0])
    for r in local_res[1:]:
        OutageFactors = OutageFactors.merge(compute_OutageFactor(config_es, assets, r), left_index=True, right_index=True)

    OutageFactors_yr = TD_DF.loc[:, ['TD', 'hour']]
    OutageFactors_yr = OutageFactors_yr.merge(OutageFactors, left_on=['TD', 'hour'], right_index=True).sort_index()
    OutageFactors_yr.drop(columns=['TD', 'hour'], inplace=True)
    OutageFactors_yr.rename(columns= lambda x: 'ES_' + x, inplace=True)
    dst.write_csv_files('OutageFactor', OutageFactors_yr, 'OutageFactor', index=True, write_csv=True)

    th_demand = dst.get_heat_demand_from_es(config_es)

    sto_size = es_outputs['assets'].loc[config_es['all_data']['Storage_eff_in'].index,'f']
    sto_size = sto_size[sto_size >= 0.01]
    soc = es_outputs['energy_stored'].loc[:,sto_size.index] / sto_size
    soc.rename(columns= lambda x: 'ES_' + x, inplace=True)
    dst.write_csv_files('ReservoirLevels', soc, 'ReservoirLevels', index=True, write_csv=True)


    # %% ###################################
    ########## Execute Dispa-SET ##########
    #######################################
    # Load the configuration file
    config = ds.load_config('../ConfigFiles/Config_EnergyScope.xlsx')
    config['Outages'] = str(DST_folder / 'Outputs' / 'EnergyScope' / 'Database' / 'OutageFactor' / '##' /
                                  'OutageFactor.csv')
    config['ReservoirLevels'] = str(DST_folder / 'Outputs' / 'EnergyScope' / 'Database' / 'ReservoirLevels' / '##' /
                                  'ReservoirLevels.csv')
    config['SimulationDirectory'] = str(DST_folder / 'Simulations' / case_study)
    config['default']['PriceOfCO2'] = abs(Price_CO2[i].loc[0, 0] * 1000)
    for j in dst.mapping['FUEL_COST']:
        config['default'][dst.mapping['FUEL_COST'][j]] = costs.loc[j] * 1000
    config['H2RigidDemand'] = str(DST_folder / 'Outputs' / 'EnergyScope' / 'Database' / 'H2_demand' / 'ES' /
                                  'H2_demand.csv')

    # Build the simulation environment:
    SimData = ds.build_simulation(config)

    # Solve using GAMS:
    _ = ds.solve_GAMS(config['SimulationDirectory'], config['GAMS_folder'])

    # Load the simulation results:
    inputs[i], results[i] = ds.get_sim_results(config['SimulationDirectory'], cache=False)

    # save DS results
    ES_output = ES_folder / 'case_studies' / config_es['case_study'] / 'output'
    with open(ES_output / 'DS_Results.p', 'wb') as handle:
        pickle.dump(inputs[i], handle, protocol=pickle.HIGHEST_PROTOCOL)
        pickle.dump(results[i], handle, protocol=pickle.HIGHEST_PROTOCOL)

    # TODO : reading and storing ESTD results

    # run ES with reserves (2nd run)
    config_es['case_study'] = case_study + '_loop_' + str(i+1)

    # config_es['printing'] = False
    config_es['import_reserves'] = 'from_df'
    reserves[i] = pd.DataFrame(inputs[i]['param_df']['Demand'].loc[:, '2U'].values / 1000, columns=['end_uses_reserve'],
                               index=np.arange(1, 8761, 1))

    if i >= 1:
        if results[i]['OutputShedLoad'].empty:
            shed_load[i] = pd.DataFrame(0, columns=['end_uses_reserve'], index=np.arange(1, 8761, 1))
        else:
            shed_load[i] = pd.DataFrame(results[i]['OutputShedLoad'].values / 1000, columns=['end_uses_reserve'],
                                        index=np.arange(1, 8761, 1))

        config_es['reserves'] = config_es['reserves'] + shed_load[i].max()
    else:
        config_es['reserves'] = reserves[i]

    LL = pd.concat([LL, results[i]['OutputShedLoad']], axis=1)
    Curtailment = pd.concat([Curtailment, results[i]['OutputCurtailedPower']], axis=1)

    if (results[i]['OutputOptimizationError'].abs() > results[i]['OutputOptimalityGap']).any():
        print('Another iteration required')
    else:
        print('Final convergence occurred in loop: ' + str(i) + '. Soft-linking is now complete')
        break

    if i == end - 1:
        print('Last opt')
    else:
        config_es['all_data'] = es.run_ES(config_es)


ENS_max = pd.DataFrame()
LL = pd.DataFrame()
LostLoad = pd.DataFrame()
Generation = {'Ele': pd.DataFrame(),
              'Heat': pd.DataFrame()}
Emissions = pd.DataFrame()
for i in range(end):
    ENS_max.loc[i, 'Error>Accuracy'] = results[i]['OutputOptimizationError'].max()
    # ENS_max.loc[i, 'ENS'] = results[i]['OutputShedLoad'].sum(axis=0).values + \
    #                         results[i]['OutputHeatSlack'].sum(axis=0).values
    if not (results[i]['OutputHeatSlack'].empty) and (results[i]['OutputShedLoad'].empty):
        LostLoad = results[i]['OutputShedLoad'] + results[i]['OutputHeatSlack'].values
    if not results[i]['OutputShedLoad'].empty:
        LostLoad = results[i]['OutputShedLoad']
    ENS_max.loc[i, 'ENS'] = LostLoad.sum(axis=0).values / 1e3
    LL = pd.concat([LL, LostLoad], axis=1)
    tmp = ds.plot_energy_zone_fuel(inputs[i], results[i], ds.get_indicators_powerplant(inputs[i], results[i]))
    Generation['Ele'] = pd.concat([Generation['Ele'], tmp[0]], axis=0)
    Generation['Heat'] = pd.concat([Generation['Heat'], tmp[1]], axis=0)
    Emissions.loc[i,'CO2'] = results[i]['OutputEmissions'].sum().sum()

LL = LL / 1e3
Generation['Ele'].reset_index(inplace=True, drop=True)
Generation['Ele']=Generation['Ele'].loc[:, (Generation['Ele'] != 0).any(axis=0)]
cols_ele = Generation['Ele'].columns
Generation['Ele'].loc[:,'Iteration'] = Generation['Ele'].index
Generation['Ele'].loc[:,'Scenario'] = '12.5 kTCO2'
Generation['Ele'].loc[:, 'Zone'] = 'ELE'
Generation['Heat']=Generation['Heat'].loc[:, (Generation['Heat'] != 0).any(axis=0)]
cols_heat = Generation['Heat'].columns
Generation['Heat'].loc[:, 'Iteration'] = np.arange(len(Generation['Heat'])) // 3 + 1
Generation['Heat'].loc[:, 'Iteration'] = Generation['Heat'].loc[:, 'Iteration'] - 1
Generation['Heat'].loc[:, 'Scenario'] = '12.5 kTCO2'
Generation['Heat'].loc[:, 'Zone'] = Generation['Heat'].index
Generation['Heat'].reset_index(inplace=True, drop=True)



Ele_pivot = pd.melt(Generation['Ele'], id_vars=['Scenario','Iteration', 'Zone'], value_vars=cols_ele, value_name='Generation')
Heat_pivot = pd.melt(Generation['Heat'], id_vars=['Scenario','Iteration','Zone'], value_vars=cols_heat, value_name='Generation')

# Generation_pivot = pd.pivot_table(df, values='S', index=['P', 'Q'], columns=['R'], aggfunc=np.sum)

with open(case_study + '.p', 'wb') as handle:
    pickle.dump(inputs, handle, protocol=pickle.HIGHEST_PROTOCOL)
    pickle.dump(results, handle, protocol=pickle.HIGHEST_PROTOCOL)

# with open(case_study + '.p', 'rb') as handle:
#     inputs = pickle.load(handle)
#     results = pickle.load(handle)

# Plots
import pandas as pd

rng = pd.date_range('2015-1-1', '2015-12-31', freq='H')
# Generate country-specific plots
ds.plot_zone(inputs[0], results[0], rng=rng, z_th='ES_DHN')

# Bar plot with the installed capacities in all countries:
cap = ds.plot_zone_capacities(inputs[2], results[2])

# Bar plot with installed storage capacity
sto = ds.plot_tech_cap(inputs[2])

# Violin plot for CO2 emissions
ds.plot_co2(inputs[3], results[3], figsize=(9, 6), width=0.9)

# Bar plot with the energy balances in all countries:
GenPerZone = ds.plot_energy_zone_fuel(inputs[3], results[3], ds.get_indicators_powerplant(inputs[3], results[3]))

# Analyse the results for each country and provide quantitative indicators:
r = ds.get_result_analysis(inputs[0], results[0])


# Create figure and subplot manually
fig, host = plt.subplots(figsize=(8, 4))  # (width, height) in inches
# (see https://matplotlib.org/3.3.3/api/_as_gen/matplotlib.pyplot.subplots.html)

par1 = host.twinx()
par2 = host.twinx()

host.set_xlim(0, 3)
host.set_ylim(0, ENS_max['Error>Accuracy'].max()*1.02)
par1.set_ylim(0, LL.sum().max()*1.03)
par2.set_ylim(0, LL.max().max()*1.03)

host.set_xlabel("Iteration")
host.set_ylabel("Error>Accuracy [EUR]")
par1.set_ylabel("ENS [GWh]")
par2.set_ylabel("ENS_max [GW]")

color1 = plt.cm.viridis(0.9)
color2 = plt.cm.viridis(0.5)
color3 = plt.cm.viridis(0)

#TODO automatise
p1, = host.plot(ENS_max.index, ENS_max.loc[:, 'Error>Accuracy'], color=color1, label='Error>Accuracy')
p2, = par1.plot(ENS_max.index, LL.sum().values, color=color2, label="ENS")
p3, = par2.plot(ENS_max.index, LL.max().values, color=color3, label="ENS_max")

lns = [p1, p2, p3]
host.legend(handles=lns, loc='best')

# right, left, top, bottom
par2.spines['right'].set_position(('outward', 60))

# no x-ticks
par2.xaxis.set_ticks([0, 1, 2, 3])

host.yaxis.label.set_color(p1.get_color())
par1.yaxis.label.set_color(p2.get_color())
par2.yaxis.label.set_color(p3.get_color())

# plt.axhline(y=850, color='r', linestyle='dashed', label='Optimality treshold')

plt.title('Optimality gap = 0.05%')

# Adjust spacings w.r.t. figsize
fig.tight_layout()
# Alternatively: bbox_inches='tight' within the plt.savefig function
#                (overwrites figsize)

# Best for professional typesetting, e.g. LaTeX
# plt.savefig("0.005.png")
# For raster graphics use the dpi argument. E.g. '[...].png", dpi=200)'

plt.show()



bb = pd.DataFrame()
CF = {}
for i in range(0, end):
    aa = inputs[i]['units'].loc[:, ['PowerCapacity', 'Nunits', 'Fuel', 'Technology']]
    aa.to_csv('Capacity_' + str(scenario) + '_' + str(i) + '.csv')

    CF[i] = results[i]['OutputPower'].sum() / (
                inputs[i]['units'].loc[:, 'PowerCapacity'] * inputs[i]['units'].loc[:, 'Nunits']) / 8760
    CF[i].fillna(0, inplace=True)

    CF[i].to_csv('CF_' + str(scenario) + '_' + str(i) + '.csv')


import pandas as pd
from plotnine import *

scenario = '37.5 kTCO2'

mix1 = pd.read_csv("PivotTable_Generation.csv")
# mix_min_max1 = pd.read_csv("data_figure13_minmax.csv")
# mix_min_max1['min'] = mix_min_max1['min'] * 100
# mix_min_max1['max'] = mix_min_max1['max'] * 100
cat_order = ['BIO', 'GEO', 'NUC', 'PEA', 'OIL', 'GAS', 'HRD', 'OTH', 'AIR', 'WST', 'WAT', 'SUN', 'WIN']
mix1['variable'] = pd.Categorical(mix1['variable'], categories=cat_order, ordered=True)

if scenario == '37.5 kTCO2':
    mix = mix1[mix1['Scenario'] != '12.5 kTCO2']
    # mix_min_max1['Label'] = mix_min_max1['min'].round(1).astype(str) + '% - ' + mix_min_max1['max'].round(1).astype(
    #     str) + '%'
    # mix_min_max = mix_min_max1[mix_min_max1['Scenario'] != "Connected"]
else:
    mix = mix1[mix1['Scenario'] != 'Baseline']
    # mix_min_max1['Label'] = mix_min_max1['min'].round(1).astype(str) + '% - ' + mix_min_max1['max'].round(1).astype(
    #     str) + '%'
    # mix_min_max = mix_min_max1[mix_min_max1['Scenario'] != "Baseline"]

mix.reset_index(inplace=True)
# mix_min_max.reset_index(inplace=True)

fuel_cmap = {'LIG': '#af4b9180', 'PEA': '#af4b9199', 'HRD': 'darkviolet', 'OIL': 'magenta',
             'GAS': '#d7642dff',
             'NUC': '#466eb4ff',
             'SUN': '#e6a532ff',
             'WIN': '#41afaaff',
             'WAT': '#00a0e1ff',
             'BIO': '#7daf4bff', 'GEO': '#7daf4bbf',
             'Storage': '#b93c46ff', 'FlowIn': '#b93c46b2', 'FlowOut': '#b93c4666',
             'OTH': '#b9c33799', 'WST': '#b9c337ff',
             'HDAM': '#00a0e1ff',
             'HPHS': 'blue',
             'THMS': '#C04000ff',
             'BATS': '#41A317ff',
             'BEVS': '#b9c33799'}

g = (ggplot(mix) +
     aes(x=mix['Iteration'], y=mix['Generation'], fill=mix['variable']) +
     geom_bar(stat="identity", width=1, size=0.15, color="black") +
     facet_wrap('Zone', ncol=2, scales="free_x") +
     scale_y_continuous(labels=lambda l: ["%d%%" % (v * 100) for v in l]) +
     scale_fill_manual(values=fuel_cmap, name="") +
     labs(title = scenario,
          x="Rank (climate years sorted by \n renewable energy generation)",
          y="Share of annual generation (%)",
          fill = 'Fuel') +
     theme_minimal() +
     # geom_hline(mix_min_max, aes(yintercept=mix_min_max['max'] / 100), color='white') +
     # geom_hline(mix_min_max, aes(yintercept=mix_min_max['min'] / 100), color='white') +
     # annotate('text', x=19, y=0.5, color="white", size=10, label=mix_min_max['Label']) +
     # theme(axis_text_x=element_text(vjust=0), legend_margin=0, subplots_adjust={'wspace': 0.10, 'hspace': 0.25},
     #       legend_position=(.5, 0), legend_direction='horizontal') +
     coord_flip() +
     guides(fill = guide_legend(nrow = 1, reverse = True))
     )

g

if scenario == 'Baseline':
    (ggsave(g, "figure13_Baseline.png", width=15.5 / 2.5, height=12 / 2.5))
else:
    (ggsave(g, "figure13_Connected.png", width=15.5 / 2.5, height=12 / 2.5))

import calendar
from plotnine import *
aa = pd.DataFrame()
for itteration in [0,3]:
    df = results[itteration]['ShadowPrice']
    df['Month'] = df.index.month
    df['Day'] = df.index.dayofyear
    df['Hour'] = df.index.hour
    df['Zone'] = 'ES_ELE'
    if itteration == 0:
        df['Iteration'] = 'No Reserve'
    elif itteration == 1:
        df['Iteration'] = 'Initialization'
    else:
        df['Iteration'] = 'Iteration ' + str(itteration-1)

    df1 = results[itteration]['HeatShadowPrice']
    df1['Month'] = df1.index.month
    df1['Day'] = df1.index.dayofyear
    df1['Hour'] = df1.index.hour
    df1 = pd.melt(df1, id_vars=['Month', 'Day','Hour'], value_vars=['ES_DEC','ES_DHN','ES_IND'], value_name='ES', var_name='Zone')
    if itteration == 0:
        df1['Iteration'] = 'No Reserve'
    elif itteration == 1:
        df1['Iteration'] = 'Initialization'
    else:
        df1['Iteration'] = 'Iteration ' + str(itteration-1)

    aa = pd.concat([aa, df, df1])

aa.reset_index(inplace=True,drop=True)
aa['Month'] = aa['Month'].apply(lambda x: calendar.month_abbr[x])
cat_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
aa['Month'] = pd.Categorical(aa['Month'], categories=cat_order, ordered=True)
aa['Iteration'] = pd.Categorical(aa['Iteration'], categories=['No Reserve', 'Iteration 2'], ordered=True)
aa['Zone'] = pd.Categorical(aa['Zone'], categories=['ES_ELE', 'ES_DEC','ES_DHN','ES_IND'], ordered=True)

aa.rename({'ES':'EUR/MWh'}, axis='columns',inplace=True)

#%% Build the plot
g = (ggplot(aa, aes(x='Day',y='Hour',fill='EUR/MWh'))
     + geom_tile(color='white',size=.01)
     + facet_grid('Zone ~ Iteration')
     # + labs(title='Shadow Prices in Electricity and Heating zones')
     # + scale_fill_cmap('plasma')
     + scale_y_continuous(breaks=(0,6,12,18,24))
     + scale_x_continuous(breaks=(0,91,182,273,365))
     + scale_fill_gradient2(low="green", mid="lightblue", high="red",
                   midpoint=200,
                   breaks=(0,100, 200, 300, 400),
                   limits=(0,420))
     + theme_minimal()
     + theme(legend_position = 'right',
               plot_title = element_text(size=10),
            legend_title= element_text(size=8)
               # axis_text_y = element_text(size=10)
             )
)

g

(ggsave(g, "ShadowPrice_" + str(scenario) + '.png', width=11.5/2.5, height=11.5/2.5, dpi = 300))

bb=pd.DataFrame()
for itteration in range(4):
    df2 = pd.DataFrame(results[itteration]['OutputOptimizationError'], columns=['Error'])
    df2.reset_index(inplace=True, drop=True)
    df2.drop(df2.tail(1).index, inplace=True)
    df2[df2 > 50000] = 50000
    df2[df2 < -50000] = -50000
    df2.loc[:,'RollingHorizon'] = df2.index
    df2.loc[:,'Iteration'] = str(itteration)
    # df2.loc[:, 'Iteration'] = itteration
    bb = pd.concat([bb, df2])

bb['Error'] = bb['Error'].astype(float)

g2 = (ggplot(bb, aes(y='RollingHorizon',x='Iteration',fill='Error'))
     + geom_tile(color='white',size=.01)
     # + facet_grid('Zone ~ Iteration')
     # + labs(title='Shadow Prices in Electricity and Heating zones')
     # + scale_fill_cmap('plasma')
     # + scale_y_continuous(breaks=(0,6,12,18,24))
     + scale_y_continuous(breaks=(0,11,22,33,44,55,66,77,88,99,110,121))
     + xlab("")
     + scale_fill_gradient2(low="green", mid="lightblue", high="red",
                   midpoint=0,
                   breaks=(-50000, 0, 50000),
                   limits=(-50000, 50000))
     + theme_minimal()
     + theme(legend_position = 'right',
            plot_title = element_text(size=10),
            legend_title= element_text(size=8),
            # axis_text_y = element_text(size=10)
             )
)

g2

(ggsave(g2, "ItterationError_" + str(scenario) + '.png', width=11.5/2.5, height=6.5/2.5, dpi = 300))

N = 24*3
cc = pd.DataFrame()
for i in range(4):
    results[i]['OutputShedLoad'].set_index('index', inplace=True)
    df3 = results[i]['OutputShedLoad']
    df3.reset_index(inplace=True)
    df3 = df3.groupby(df3.index // N).sum()
    df3.loc[:,'Iteration'] = i
    df3.loc[:,'RollingHorizon'] = df3.index
    cc = pd.concat([cc,df3])

cc = cc.rename(columns={'ES':'ENS'})
cc['ENS'] = cc['ENS'].astype(float)

ENS_max.loc[:,'Iteration']=ENS_max.index

g3 = (ggplot(ENS_max, aes(x='Iteration', y='ENS'))
     + geom_col(fill='red')
     + scale_y_reverse()
     + theme_minimal()
     + ylab('ENS [GWh]')
     + theme(legend_position = 'right',
            legend_title= element_text(size=8)
               # axis_text_y = element_text(size=10)
             )
)

g3

(ggsave(g3, "ENS_" + str(scenario) + '.png', width=11.5/2.5, height=5.3/2.5, dpi = 300))


