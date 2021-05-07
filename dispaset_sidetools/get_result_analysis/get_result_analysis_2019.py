# -*- coding: utf-8 -*-
"""
Not part of Dispa-SET sidetools module
@author: Matijs Geivers
"""

# %% Imports

# Add the root folder of Dispa-SET to the path so that the library can be loaded:
import sys, os

sys.path.append(os.path.abspath(r'C:\Users\matijs\Documents\Dispa-SET-master'))

# Import Dispa-SET
import dispaset as ds

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt

pd.options.display.float_format = '{:.4g}'.format

import matplotlib.ticker as mtick
import enlopy as el

import seaborn as sns

plt.style.use('default')

# Path where saving the plot figures
output_folder = r"C:\Users\student\Documents\Dispa-SET1\Matijs\Output"

# sys.path.append(os.path.abspath(r'C:\Users\Andrea\GitHub\Dispa-SET-2.3\dispaset'))



#%% Read all variables (inputs, results, r, costs) from the pickle files - Faster!

# Read 2019 results
import pickle5 as pickle

with open(r'C:/Users/matijs/Documents/Dispa-SET-master/Data_2019/SimulationResults_2019/results1.p','rb') as pickle_file:
    results_M=pickle.load(pickle_file)
with open(r':/Users/matijs/Documents/Dispa-SET-master/Data_2019/SimulationResults_2019/inputs1.p','rb') as pickle_file:
    inputs_M=pickle.load(pickle_file)
r_M = ds.get_result_analysis(inputs_M,results_M)
#costs_ALL = ds.CostExPost(inputs_M,results_M)
    


# %% Put the results of the different scenarios in a dictionary to make easier the processing

results = {}

results['Matijs'] = results_M
scenarios = list(results.keys())

# %% Set and list definition

tech_fuel_raw = list(inputs_M['units'].iloc[:, 0].astype(str).str[3:].unique())
tech_fuel = ['HDAM_WAT', 'HROR_WAT', 'HPHS_WAT', 'WTON_WIN', 'WTOF_WIN', 'PHOT_SUN', 'STUR_SUN', 'COMC_BIO', 'STUR_BIO',
             'STUR_NUC',
             'STUR_GAS', 'GTUR_GAS', 'COMC_GAS', 'STUR_OIL', 'COMC_OIL','GTUR_OIL','STUR_HRD', 'STUR_LIG','STUR_WST',
             'STUR_BIO_CHP', 'STUR_GAS_CHP', 'STUR_HRD_CHP', 'STUR_OIL_CHP', 'GTUR_GAS_CHP', 'STUR_LIG_CHP',
             'COMC_GAS_CHP','STUR_WST_CHP', 'P2HT_OTH','REHE_OTH','HOBO_GAS', 'Heat Slack'
             'ICEN_OIL','ICEN_GAS','ICEN_GAS_CHP','ICEN_OIL_CHP','ICEN_BIO_CHP',
             ]

tech_fuel_heat = ['STUR_BIO_CHP', 'STUR_GAS_CHP', 'STUR_HRD_CHP', 'STUR_OIL_CHP', 'GTUR_GAS_CHP', 'STUR_LIG_CHP',
                  'COMC_GAS_CHP','STUR_WST_CHP','ICEN_GAS_CHP','ICEN_OIL_CHP','ICEN_BIO_CHP', 'P2HT_OTH','REHE_OTH','HOBO_GAS', 'Heat Slack', 'Storage Losses']
tech_fuel_storage = ['HDAM_WAT', 'HROR_WAT', 'HPHS_WAT']
colors_tech = {}
for tech in tech_fuel:
    if 'Slack' not in tech:
        if 'CHP' not in tech:
            colors_tech[tech] = ds.commons['colors'][tech[-3:]]
        if 'CHP' in tech:
            colors_tech[tech] = ds.commons['colors'][tech[5:-4]]

colors_tech['HDAM_WAT'] = 'darkblue'
colors_tech['HROR_WAT'] = 'blue'
colors_tech['WTON_WIN'] = 'aquamarine'
colors_tech['STUR_SUN'] = 'yellow'
colors_tech['COMC_BIO'] = 'lime'
colors_tech['GTUR_GAS'] = 'brown'
colors_tech['STUR_GAS'] = 'maroon'
colors_tech['STUR_OIL'] = 'magenta'
colors_tech['COMC_GAS_CHP'] = 'tan'
colors_tech['GTUR_GAS_CHP'] = 'tomato'
colors_tech['STUR_GAS_CHP'] = 'lightcoral'
colors_tech['STUR_BIO_CHP'] = 'lawngreen'
colors_tech['STUR_HRD_CHP'] = 'darkviolet'
colors_tech['STUR_OIL_CHP'] = 'pink'
colors_tech['STUR_LIG_CHP'] = 'violet'
colors_tech['P2HT_ELE'] = 'gold'
colors_tech['REHE_ELE'] = 'lime'
colors_tech['Heat Slack'] = 'darkorange'
colors_tech['Shed Load'] = 'orangered'
colors_tech['Lost Load'] = 'darkred'
colors_tech['Curtailment'] = 'salmon'
colors_tech['LostLoad'] = colors_tech['Lost Load']
colors_tech['CostLoadShedding'] = colors_tech['Shed Load']
colors_tech['CostHeatSlack'] = 'darkred'
colors_tech['CostStartUp'] = 'gold'
colors_tech['CostRampUp'] = 'salmon'

# %% ########################### Analysis and charts #################################

# %% Curtailment

curtail_tot = pd.DataFrame(index=['Curtailment'], columns=['Matijs'])

curtail_tot['Matijs'] = results_M['OutputCurtailedPower'].sum().sum() / 10 ** 6
curtail_stat = pd.DataFrame(index=['Mean Curtailment', 'Median Curtailment', 'Max Curtailment', 'Curtailment hours'],
                            columns=['Matijs'])

curtail_max = pd.DataFrame(index=['Max Curtailment'], columns=['Matijs'])
curtail_max['Matijs'] = results_M['OutputCurtailedPower'].sum(axis=1).max() / 10 ** 6

curtail_num = pd.DataFrame(index=['Curtailment hours'], columns=['Matijs'])
curtail_num['Matijs'] = (results_M['OutputCurtailedPower'].sum(axis=1) != 0).sum()

curtail_mean = pd.DataFrame(index=['Mean Curtailment'], columns=['Matijs'])
curtail_mean['Matijs'] = results_M['OutputCurtailedPower'].sum(axis=1).mean() / 1e3

curtail_median = pd.DataFrame(index=['Median Curtailment'], columns=['Matijs'])
curtail_median['Matijs'] = results_M['OutputCurtailedPower'].sum(axis=1).median() / 1e3

curtail_stat.loc['Curtailment hours'] = curtail_num.values
curtail_stat.loc['Max Curtailment'] = curtail_max.values
curtail_stat.loc['Mean Curtailment'] = curtail_mean.values
curtail_stat.loc['Median Curtailment'] = curtail_median.values

# Curtailment % wrt to V-RES generation

en_vres = pd.DataFrame(index=results_M['OutputPower'].index, columns=['Matijs'])

en_vres.loc[:, 'Matijs'] = results_M['OutputPower'].loc[:,
                            results_M['OutputPower'].columns.str.contains('HROR|PHOT|WTOF|WTON')].sum(axis=1) / 1e6

curtail_tot.loc['Percentage total V-RES', 'Matijs'] = curtail_tot.loc['Curtailment', 'Matijs'] / (
            en_vres.sum(axis=0)['Matijs'] + curtail_tot.loc['Curtailment', 'Matijs']) * 100

curtail_max.loc['Percentage peak V-RES', 'Matijs'] = curtail_max.loc['Max Curtailment', 'Matijs'] / (
            en_vres.max(axis=0)['Matijs'] + curtail_max.loc['Max Curtailment', 'Matijs']) * 100


# %% Curtailment plot
curtail_tot.rename(columns={'Matijs':'.'},inplace=True)
curtail_max.rename(columns={'Matijs':'.'}, inplace=True)
ax = curtail_tot.loc['Percentage total V-RES', :].T.plot(kind='bar', color='salmon', width=0.05, rot=0, position=1,
                                                         legend=True, figsize=(7, 5), fontsize=15,ylim=(0,0.375))
ax2 = curtail_max.loc['Percentage peak V-RES', :].T.plot(kind='bar', color='firebrick', secondary_y=True, rot=0,
                                                         width=0.05, position=0, legend=True, mark_right=False,
                                                         fontsize=15)

ax.set_ylabel('Percentage Total V-RES', fontsize=15)
ax2.set_ylabel('Percentage Peak V-RES', fontsize=15)
#ax.set_xlabel('Scenario', fontsize=15)
ax2.set_title("Curtailment", fontsize=15)
# ax2.set_ylim(0, 90)
# handles, labels = ax.get_legend_handles_labels()
# handles2, labels2 = ax2.get_legend_handles_labels()
# handles.append(handles2[0])
# labels.append(labels2[0])
##ax.legend(reversed(handles), reversed(labels))

# ax.legend(bbox_to_anchor=(1.1, 1.05), fontsize=15)
ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=2))
ax2.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))

fig = ax2.get_figure()
fig.savefig(output_folder + "\Curtailment.png", bbox_inches='tight')

# %% Shed Load

shload_tot = pd.DataFrame(index=['Shed Load'], columns=['Matijs'])

shload_tot['Matijs'] = results_M['OutputShedLoad'].sum().sum() / 10 ** 6

shload_stat = pd.DataFrame(index=['Mean Load Shedding', 'Median Load Shedding', 'Max Shed Load', 'Load Shedding hours'],
                           columns=['Matijs'])
shload_max = pd.DataFrame(index=['Max Shed Load'], columns=['Matijs'])
shload_max['Matijs'] = results_M['OutputShedLoad'].sum(axis=1).max() / 1e3

shload_num = pd.DataFrame(index=['Load Shedding hours'], columns=['Matijs'])
shload_num['Matijs'] = (results_M['OutputShedLoad'].sum(axis=1) != 0).sum()

shload_mean = pd.DataFrame(index=['Mean Load Shedding'], columns=['Matijs'])
shload_mean['Matijs'] = results_M['OutputCurtailedPower'].sum(axis=1).mean() / 1e3

shload_median = pd.DataFrame(index=['Median Load Shedding'], columns=['Matijs'])
shload_median['Matijs'] = results_M['OutputCurtailedPower'].sum(axis=1).median() / 1e3

shload_stat.loc['Load Shedding hours'] = shload_num.values
shload_stat.loc['Max Shed Load'] = shload_max.values
shload_stat.loc['Mean Load Shedding'] = shload_mean.values
shload_stat.loc['Median Load Shedding'] = shload_median.values

def get_demand(inputs, results):
    demand = {}
    for z in inputs['sets']['n']:
        if 'OutputPowerConsumption' in results:
            loc = inputs['units']['Zone']
            demand_p2h = results['OutputPowerConsumption'].loc[:,
                         [u for u in results['OutputPowerConsumption'].columns if loc[u] == z]]
            demand_p2h = demand_p2h.sum(axis=1)
        else:
            demand_p2h = pd.Series(0, index=results['OutputPower'].index)
        demand_da = inputs['param_df']['Demand'][('DA', z)]
        demand[z] = pd.DataFrame(demand_da + demand_p2h, columns=[('DA', z)])
    demand = pd.concat(demand, axis=1)
    demand.columns = demand.columns.droplevel(-1)

    return demand

demand_M = get_demand(inputs_M, results_M)
demand_stat = pd.DataFrame(index=['Total Demand', 'Max Demand'], columns=['Matijs'])

demand_stat.loc['Total Demand', 'Matijs'] = demand_M.sum().sum() / 1e6
demand_stat.loc['Max Demand', 'Matijs'] = demand_M.sum(axis=1).max() / 1e3

shload_tot.loc['Percentage total Load', 'Matijs'] = shload_tot.loc['Shed Load', 'Matijs'] / demand_stat.loc[
    'Total Demand', 'Matijs'] * 100

shload_max.loc['Percentage peak Load', 'Matijs'] = shload_max.loc['Max Shed Load', 'Matijs'] / demand_stat.loc[
    'Max Demand', 'Matijs'] * 100


# %% Shed Load plot
shload_tot=shload_tot.rename(columns={'Matijs':'2019'})
shload_max=shload_max.rename(columns={'Matijs':'2019'})
ax = shload_tot.loc['Percentage total Load', :].T.plot(kind='bar', color='orangered', width=0.05, rot=0, figsize=(7, 5),
                                                       position=1, legend=True, fontsize=15,ylim=(0,0.000058))
ax2 = shload_max.loc['Percentage peak Load', :].T.plot(kind='bar', color='firebrick', secondary_y=True, rot=0, ax=ax,
                                                       width=0.05, position=0, legend=True, mark_right=False,
                                                       fontsize=15)

ax.set_ylabel('Percentage Total Load', fontsize=15)
ax2.set_ylabel('Percentage Peak Load', fontsize=15)
#♣ax.set_xlabel('Scenario', fontsize=15)
ax2.set_title("Shed Load", fontsize=15)
ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=5))
ax2.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=2))

fig = ax2.get_figure()
fig.savefig(output_folder + "\Shed Load.png", bbox_inches='tight')


# %% Energy output

def get_en_prod(results, scenario='None'):
    # Extract raw energy prodction from results
    en_prod_raw = pd.DataFrame(results['OutputPower'].sum(axis=0).values, columns=[scenario],
                               index=results['OutputPower'].columns).T
    # Define df with grouped energy production
    en_prod = pd.DataFrame(columns=tech_fuel, index=[scenario])

    # Fill the df
    if isinstance(results['LostLoad_WaterSlack'], int):
        en_prod.loc[scenario, 'Lost Load'] = -(
                    results['LostLoad_2D'].sum().sum() + results['LostLoad_2U'].sum().sum() + results[
                'LostLoad_3U'].sum().sum() + results['LostLoad_MaxPower'].sum().sum() + results[
                        'LostLoad_MinPower'].sum().sum() + results['LostLoad_RampDown'].sum().sum() + results[
                        'LostLoad_RampUp'].sum().sum() + results['LostLoad_WaterSlack']) / 10 ** 6
    else:
        en_prod.loc[scenario, 'Lost Load'] = -(
                    results['LostLoad_2D'].sum().sum() + results['LostLoad_2U'].sum().sum() + results[
                'LostLoad_3U'].sum().sum() + results['LostLoad_MaxPower'].sum().sum() + results[
                        'LostLoad_MinPower'].sum().sum() + results['LostLoad_RampDown'].sum().sum() + results[
                        'LostLoad_RampUp'].sum().sum() + results['LostLoad_WaterSlack'].sum()) / 10 ** 6
    en_prod.loc[scenario, 'Shed Load'] = -results['OutputShedLoad'].sum().sum() / 10 ** 6
    en_prod.loc[scenario, 'Curtailment'] = -results_M['OutputCurtailedPower'].sum().sum() / 10 ** 6

    for t in tech_fuel:
        en_prod.loc[scenario, t] = en_prod_raw.loc[:, en_prod_raw.columns.str.endswith(t)].values.sum() / 1e6

    for c in en_prod.columns:
        if en_prod[c].values.sum() == 0:
            en_prod.drop(columns=[c], inplace=True)

    # Reordering the order of columns to be coherent in the plot
    en_prod_list = list(en_prod.columns)
    en_prod_list = en_prod_list[-3:] + en_prod_list[:-3]
    en_prod = en_prod[en_prod_list]

    return en_prod

# Example to create a df with en_prod for all 5 scenarios

en_prod = pd.DataFrame(index=scenarios, columns=get_en_prod(results['Matijs'], 'Matijs').columns)

for scenario in scenarios:
    en_prod.loc[scenario, :] = get_en_prod(results[scenario], scenario).iloc[0, :]

en_prod.fillna(0, inplace=True)

# % Increase in RES absorption
en_prod_sun = en_prod.loc[:, en_prod.columns.str.contains('_SUN')].sum(axis=1)
en_prod_win = en_prod.loc[:, en_prod.columns.str.contains('_WIN')].sum(axis=1)
en_prod_bio = en_prod.loc[:, en_prod.columns.str.contains('_BIO')].sum(axis=1)

# Energy Mix

demand = inputs_M['param_df']['Demand']['DA']
demand_p2h_raw_M = results_M['OutputPowerConsumption']

sto_input_raw_M = results_M['OutputStorageInput']

shed_load_M = pd.DataFrame(
    results_M['OutputShedLoad'].loc[:, ~ results_M['OutputShedLoad'].columns.str.contains('x|y')],
    index=demand.index, columns=inputs_M['param_df']['sets']['n'])
shed_load_M.fillna(0, inplace=True)

ll_max_M = pd.DataFrame(results_M['LostLoad_MaxPower'], index=demand.index,
                          columns=inputs_M['param_df']['sets']['n'])
ll_max_M.fillna(0, inplace=True)

ll_min_M = pd.DataFrame(results_M['LostLoad_MinPower'], index=demand.index,
                          columns=inputs_M['param_df']['sets']['n'])
ll_min_M.fillna(0, inplace=True)

demand_p2h_M = pd.DataFrame(index=demand_p2h_raw_M.index, columns=inputs_M['param_df']['sets']['n'])

sto_input_M = pd.DataFrame(index=sto_input_raw_M.index, columns=inputs_M['param_df']['sets']['n'])

for c in inputs_M['param_df']['sets']['n']:
    demand_p2h_M.loc[:, c] = demand_p2h_raw_M.loc[:, demand_p2h_raw_M.columns.str.contains(' ' + c + '_')].sum(
        axis=1)

for c in inputs_M['param_df']['sets']['n']:
    sto_input_M.loc[:, c] = sto_input_raw_M.loc[:, sto_input_raw_M.columns.str.contains(' ' + c + '_')].sum(
        axis=1)

energy_mix_den = pd.DataFrame(index=['0'], columns=scenarios)
energy_mix_den.loc[:, 'Matijs'] = (
                                           demand + demand_p2h_M + sto_input_M - shed_load_M - ll_max_M + ll_min_M).sum().sum() / 1e6

energy_mix = pd.DataFrame(index=scenarios, columns=en_prod.columns)
energy_mix.loc['Matijs'] = en_prod.loc['Matijs'] / energy_mix_den['Matijs'].values
energy_mix = energy_mix.abs()
#energy_mix.drop(index = ['Lost Load', 'Shed Load', 'Curtailment'], inplace = True)

# %% Energy output plot

# Use this to change what columns are not plotted from the original df
en_prod_plot = en_prod
en_prod_plot=en_prod_plot.rename(index={'Matijs':' '})
#en_prod_plot.drop(columns = ['Lost Load', 'Shed Load', 'Curtailment'], inplace = True)
#en_prod_plot.drop(columns=['BEVS_OTH'], inplace=True)

ax = en_prod_plot.plot(kind='bar', stacked=True, rot=0, width=0.3, color=[colors_tech.get(x) for x in en_prod_plot.columns],
                       legend=False, figsize=(7.5, 6), fontsize=15)

for container, hatch in zip(ax.containers, (
'', '', "", '', '', '', '', '', '', '', '', '', '', '', '', '', '', '///', '///', '///', '///', '///', '///', '///', '///', '///',
'///', '///')):
    for patch in container.patches:
        patch.set_hatch(hatch)

ax.axhline(y=0, xmin=-1, xmax=1, color='black', linestyle='-', lw=1)
ax.set_ylabel('Energy [TWh]', fontsize=15)
#ax.set_xlabel('Scenario', fontsize=15)
ax.set_title("Energy Output per Fuel / Technology", fontsize=15)
handles, labels = ax.get_legend_handles_labels()
ax.legend(reversed(handles), reversed(labels), loc='center left', bbox_to_anchor=(1, 0.5), ncol=2, fontsize=15)

fig = ax.get_figure()
fig.savefig(output_folder + "\Energy output.png", bbox_inches='tight')

# %% Heating output

heat_prod_raw_M = pd.DataFrame(results_M['OutputHeat'].sum(axis=0).values, columns=['Matijs'],
                                 index=results_M['OutputHeat'].columns).T
heat_prod_raw_M['Heat Slack'] = results_M['OutputHeatSlack'].sum().sum()

# Heat storage losses

heat_sto_col_M = inputs_M['units']['StorageSelfDischarge'].loc[
    inputs_M['units']['StorageSelfDischarge'] > 0].index
sto_self_dis = 0.03 / 24
sto_loss_M = results_M['OutputStorageLevel'].loc[:,
               results_M['OutputStorageLevel'].columns.str.contains('_CHP|P2HT')] * sto_self_dis

heat_prod = pd.DataFrame(index=scenarios, columns=tech_fuel_heat)

for t in tech_fuel_heat:
    heat_prod.loc['Matijs', t] = heat_prod_raw_M.loc[:, heat_prod_raw_M.columns.str.endswith(t)].values.sum() / 1e6

heat_prod.loc['Matijs', 'Storage Losses'] = sto_loss_M.sum().sum() / 1e6

for c in heat_prod.columns:
    if heat_prod[c].values.sum() == 0:
        heat_prod.drop(columns=[c], inplace=True)

heat_prod.rename(columns={"P2HT_OTH": "P2HT_ELE"}, inplace=True)
heat_prod.rename(columns={"REHE_OTH": "REHE_ELE"}, inplace=True)
#heat_prod.rename(columns={"Heat Slack": "Backup Heater"}, inplace=True)

# Energy Heat mix

heat_demand_raw_ALL = inputs_M['param_df']['HeatDemand']

heat_demand_ALL = pd.DataFrame(index=heat_demand_raw_ALL.index, columns=inputs_M['param_df']['sets']['n'])


heat_slack_ALL = pd.DataFrame(index=heat_demand_raw_ALL.index, columns=inputs_M['param_df']['sets']['n'])

for c in inputs_M['param_df']['sets']['n']:
    heat_demand_ALL.loc[:, c] = heat_demand_raw_ALL.loc[:, heat_demand_raw_ALL.columns.str.contains(' ' + c + '_')].sum(
        axis=1)

for c in inputs_M['param_df']['sets']['n']:
    heat_slack_ALL.loc[:, c] = results_M['OutputHeatSlack'].loc[:,
                               results_M['OutputHeatSlack'].columns.str.contains(' ' + c + '_')].sum(axis=1)

heat_mix = pd.DataFrame(index=scenarios, columns=heat_prod.columns)

heat_mix.loc['Matijs', :] = heat_prod.loc['Matijs'] / ((heat_demand_ALL - heat_slack_ALL).sum(axis=1).sum() / 1e6)
heat_mix.drop(columns=['Heat Slack'], inplace=True)


# %% Heat output plot
heat_prod=heat_prod.rename(index={'Matijs':' '})
ax = heat_prod.plot(kind='bar', stacked=True, rot=0, width=0.4, color=[colors_tech.get(x) for x in heat_prod.columns],
                    legend=True, figsize=(10, 7.5), fontsize=15)

for container, hatch in zip(ax.containers, ("///", '///', '///', '///', '///', '///', '///', '///', '///', '///','///','///','///')):
    for patch in container.patches:
        patch.set_hatch(hatch)
# ax.axhline(y=1528, xmin=-1, xmax=1, color = 'black', linestyle='-', lw = 1)

ax.set_ylabel('Heat [TWh]', fontsize=15)
#ax.set_xlabel('Scenario', fontsize=15)
ax.set_title("Heat Output", fontsize=15)
handles, labels = ax.get_legend_handles_labels()

ax.legend(reversed(handles), reversed(labels), loc='center left', bbox_to_anchor=(1, 0.5), ncol=1, fontsize=15)

fig = ax.get_figure()
fig.savefig(output_folder + "\Heat output2.png", bbox_inches='tight')

# %% CO2 emissions

co2_prod_raw_ALL = pd.DataFrame(r_M['UnitData']['CO2 [t]'].values, columns=['ALLFLEX'],
                                index=r_M['UnitData']['CO2 [t]'].index).T


co2_prod = pd.DataFrame(index=['ALLFLEX'], columns=tech_fuel)

for t in tech_fuel:
    co2_prod.loc['ALLFLEX', t] = co2_prod_raw_ALL.loc[:, co2_prod_raw_ALL.columns.str.endswith(t)].values.sum() / 1e6

# CO2 Backup Heater [Mton co2]
co2_prod.loc['ALLFLEX', "Heat Slack"] = (heat_prod.loc[' ', "Heat Slack"] * 0.5 / 0.95)


#co2_prod.rename(columns={"Heat Slack": "Backup Heater"}, inplace=True)
co2= pd.DataFrame()
co2['CO2'] = results_M['OutputHeat'].sum() * 0.457*0.87
co2=co2.transpose()
co2_total=co2.loc[:, co2.columns.str.endswith('HOBO_GAS')].values.sum()
co2_total=co2_total/1000000
co2_prod.loc['ALLFLEX','HOBO_GAS']=co2_total
 # MWh * tCO2 / MWh = tCO2
#co2.fillna(0, inplace=True)

for c in co2_prod.columns:
    if co2_prod[c].values.sum() == 0:
        co2_prod.drop(columns=[c], inplace=True)

# %% co2 emissions plot
A=co2_prod.values.sum(axis=1)
co2_prod=co2_prod.rename(index={'ALLFLEX':' '})
ax = co2_prod.plot(kind='bar', stacked=True, rot=0,width=0.3, color=[colors_tech.get(x) for x in co2_prod.columns], legend=False,
                   figsize=(10, 7.5), fontsize=15)

for container, hatch in zip(ax.containers,
                            ("", '', '', '', '', '','///','///', '///', '///', '///', '///', '///', '///', '///', '///')):
    for patch in container.patches:
        patch.set_hatch(hatch)

ax.set_ylabel('[$CO_{2}$ [Mton]', fontsize=15)
#ax.set_xlabel('Scenario', fontsize=15)
ax.set_title("$CO_{2}$ emissions", fontsize=15)
handles, labels = ax.get_legend_handles_labels()
ax.legend(reversed(handles), reversed(labels), loc='center left', bbox_to_anchor=(1, 0.5), ncol=1, fontsize=15)

fig = ax.get_figure()
fig.savefig(output_folder + "\CO2 emissions.png", bbox_inches='tight')

# %% Shifted Load

sto_cap_ALL = pd.DataFrame(inputs_M['units']['StorageCapacity'][inputs_M['units']['StorageCapacity'] > 0].values,
                           columns=["ALLFLEX"], index=list(
        inputs_M['units']['StorageCapacity'][inputs_M['units']['StorageCapacity'] > 0].index)).T
sto_cap_ALL_tot = sto_cap_ALL * inputs_M['units'].loc[sto_cap_ALL.columns, 'Nunits']

delta_ALL = results_M['OutputStorageLevel'].diff()
shift_load_raw_ALL = pd.DataFrame(delta_ALL[delta_ALL > 0].sum(), columns=['ALLFLEX'],
                                  index=delta_ALL[delta_ALL > 0].columns).T
stor_usage_raw_ALL = pd.DataFrame(-delta_ALL[delta_ALL < 0].sum(), columns=['ALLFLEX'],
                                  index=delta_ALL[delta_ALL < 0].columns).T

shift_load = pd.DataFrame(index=['ALLFLEX'], columns=tech_fuel)


for t in tech_fuel:
    shift_load.loc['ALLFLEX', t] = shift_load_raw_ALL.loc[:,
                                   shift_load_raw_ALL.columns.str.endswith(t)].values.sum() / 1e6

    shift_load.loc['ALLFLEX', t] = shift_load_raw_ALL.loc[:,
                                   shift_load_raw_ALL.columns.str.endswith(t)].values.sum() / 1e6

shift_load.fillna(0, inplace=True)

for c in shift_load.columns:
    if shift_load[c].values.sum() == 0:
        shift_load.drop(columns=[c], inplace=True)

shift_load.rename(columns={"P2HT_OTH": "P2HT_ELE"}, inplace=True)

sto_cycle_ALL = stor_usage_raw_ALL / sto_cap_ALL_tot


# %% Shifted load plot

ax = shift_load.plot(kind='bar', stacked=True, rot=0, color=[colors_tech.get(x) for x in shift_load.columns],
                     legend=False, figsize=(7, 5), fontsize=15)

for container, hatch in zip(ax.containers, ('', '', '', "///", '///', '///', '///', '///', '///', '///', '///')):
    for patch in container.patches:
        patch.set_hatch(hatch)

ax.set_ylabel('Energy [TWh]', fontsize=15)
ax.set_xlabel('Scenario', fontsize=15)
ax.set_title("Shifted Load", fontsize=15)
handles, labels = ax.get_legend_handles_labels()

ax.legend(reversed(handles), reversed(labels), loc='center left', bbox_to_anchor=(1, 0.5), ncol=1, fontsize=15)

fig = ax.get_figure()
fig.savefig(output_folder + "\Load Shift.png", bbox_inches='tight')

# %% Shadow Prices plots
# %% Shadow price ALLFLEX - NOFLEX
import matplotlib

shad_price_ALL = results_M['HeatShadowPrice']

for c in shad_price_ALL.columns:
    shad_price_ALL.loc[shad_price_ALL[c] >= 1e5, :] = 1e5

shad_price_ALL.sort_index(axis=1, inplace=True)

#shad_price_NO = results_NO['ShadowPrice']

# =============================================================================
# for c in shad_price_NO.columns:
#     shad_price_NO.loc[shad_price_NO[c] >= 1e5, :] = 1e5
# 
# shad_price_NO.sort_index(axis=1, inplace=True)
# =============================================================================

#fig, axes = plt.subplots(nrows=2, ncols=1, sharex=False, figsize=(20, 14))

# =============================================================================
sns.set(font_scale=1)
fig, ax = plt.subplots(figsize=(15,5))

xticks_sh = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


ax1 = sns.heatmap(shad_price_ALL.T, vmax=200,vmin=0, cmap='summer', yticklabels=True, cbar=False)
#sns.heatmap(shad_price_ALL.T, mask=shad_price_ALL.T < 1e5, cbar=False, cmap='bwr')

# =============================================================================
# 
# ax2 = sns.heatmap(shad_price_ALL.T, ax=axes[1], cmap='summer', vmax=400, yticklabels=True, cbar=False)
# sns.heatmap(shad_price_ALL.T, ax=axes[1], mask=shad_price_ALL.T < 1e5, cbar=False, cmap='bwr')
# =============================================================================
aaaa=pd.DataFrame()
aaaa['c']=shad_price_ALL.columns
# PuOr
# =============================================================================
# ax2.set_title('Shadow price for each zone - ALLFLEX', fontsize=18)
# ax2.set_yticklabels(aaaa.loc[:,'c'], rotation=0)
# ax2.set_xticks(range(1, 8784, 798))
# ax2.set_xticklabels(xticks_sh, rotation=0)
# ax2.tick_params(labelsize=15)
# =============================================================================


ax1.set_title('Heat Shadow price for each zone', fontsize=18)
ax1.set_yticklabels(shad_price_ALL.columns, rotation=0,)
ax1.set_xticks(range(1, 8784, 798))
ax1.set_xticklabels(xticks_sh, rotation=0)
ax1.tick_params(labelsize=15)



mappable = ax1.get_children()[0]
cbar = plt.colorbar(mappable, orientation='vertical')
cbar.ax.tick_params(labelsize=15)


plt.show()

fig = ax1.get_figure()
fig.savefig(output_folder + "\HeatShadow price Matijs_200.png", bbox_inches='tight')

# %% Shadow price
import matplotlib.cm as cm
from matplotlib.patches import Rectangle

import cooked_input
from dispaset.common3 import commons,make_dir,reshape_timeseries


def plot_heatmap(Load, x='dayofyear', y='hour', aggfunc='sum', bins=8, figsize=(15, 14), edgecolors='none',
                 cmap='Oranges', colorbar=True, columns=1, x_ax_label=[0, 2], y_ax_label=[0, 2], pool = False,
                 png_name=None, vmin=0, vmax=400,
                 **pltargs):
    """ Returns a 2D heatmap of the reshaped timeseries based on x, y
    Arguments:
        Load:           1D pandas with timed index
        x:              Parameter for :meth:`enlopy.analysis.reshape_timeseries`
        y:              Parameter for :meth:`enlopy.analysis.reshape_timeseries`
        bins:           Number of bins for colormap
        figsize:        Size of figure to be plotted
        edgecolors:     colour of edges around individual squares. 'none' or 'w' is recommended.
        cmap:           colormap name (from colorbrewer, matplotlib etc.)
        colorbar:       show colorbar
        columns:        number of columns to be ploted
        x_ax_label      list of positions where x label should be plotted
        y_ax_label      list of positions where y label should be plotted
        png_name        name of figure to be saved
        **pltargs: Exposes matplotlib.plot arguments
    Returns:
        2d heatmap
    """
    rows = int(len(Load.columns) / columns) + (len(Load.columns) % columns > 0)
    fig = plt.figure(figsize=figsize, constrained_layout=True)
    spec = fig.add_gridspec(nrows=rows, ncols=columns + 1)

    # axs = axs.ravel()
    cmap_obj = cm.get_cmap(cmap, bins)
    i = 0
    for row in range(rows):
        for col in range(columns):
            ax = fig.add_subplot(spec[row, col])
            if i < len(Load.columns):
                bb = Load.iloc[:, i]
                x_y = reshape_timeseries(bb, x=x, y=y, aggfunc=aggfunc)
                heatmap = ax.pcolor(x_y, cmap=cmap_obj, edgecolors=edgecolors, vmin=vmin, vmax=vmax)
                ax.set_xlim(right=len(x_y.columns))
                ax.set_ylim(top=len(x_y.index))
                ax.set_xticks([0,90,180,270,365])
                ax.set_yticks([0, 8, 16, 24])
                if i in x_ax_label:
                    ax.set_xlabel(x)
                if i in y_ax_label:
                    ax.set_ylabel(y)
                ax.set_title(bb.name)
                if pool is True:
                    if i < 12:
                        for spine in ax.spines.values():
                            spine.set_edgecolor('#be64e1')
                            spine.set_linewidth(4)
                    elif (i >=12) and (i <17):
                        for spine in ax.spines.values():
                            spine.set_edgecolor('#b4dc00')
                            spine.set_linewidth(4)
                    elif i >=17:
                        for spine in ax.spines.values():
                            spine.set_edgecolor('#ffd000')
                            spine.set_linewidth(4)
            if i >= len(Load.columns):
                fig.delaxes(ax)
            i = i + 1
    if colorbar:
        ax2 = fig.add_subplot(spec[:, columns])
        fig.colorbar(heatmap, ax=ax2, location='right', shrink=0.8)
        fig.delaxes(ax2)
    # folder_figures = output_folder + source_folder + 'Figures/'
    #fig.savefig(folder_figures + '/' + png_name + '.png')
    plt.show()
shad_el = results_M['ShadowPrice']
shad_heat = results_M['HeatShadowPrice']


plot_heatmap(shad_el, bins=30, figsize=(10, 9), cmap='RdBu_r', colorbar=True, columns=5, pool=False,
             x_ax_label=[20, 21, 22, 23, 24], y_ax_label=[0, 5, 10, 15, 20], png_name='Shadow Price Wet', vmax=200)
plot_heatmap(shad_heat, bins=30, figsize=(10, 9), cmap='RdBu_r', colorbar=True, columns=5, pool=False,
             x_ax_label=[20, 21, 22, 23, 24], y_ax_label=[0, 5, 10, 15, 20], png_name='Shadow Price Wet', vmax=100)
    
# %% Shadow price duration curve
# TODO If needed do the 28 plots where all the 5 scenarios are shown at the same time.

shad_price_ALL = results_M['ShadowPrice']

el.plot_LDC(shad_price_ALL, stacked=False, x_norm=False, legend=True)
plt.ylabel('Daily Generation Cost Electricity [M€]')
plt.xlabel('Hour')
plt.legend()





# %% Costs breakdown
# =============================================================================
# 
# costs_raw_ALL = pd.DataFrame(costs_ALL[0].sum(axis=0).values, columns=['ALLFLEX'], index=costs_ALL[0].columns).T
# 
# costs = pd.DataFrame(index=scenarios, columns=costs_ALL[0].columns)
# 
# costs.loc['Matijs', :] = costs_raw_ALL.values / 1e9
# 
# for c in costs.columns:
#     if costs[c].values.sum() == 0:
#         costs.drop(columns=[c], inplace=True)
# 
# costs_var_raw_ALL = pd.DataFrame(
#     (results_M['OutputPower'] * inputs_M['param_df']['CostVariable']).fillna(0).sum(axis=0).values,
#     columns=['ALLFLEX'],
#     index=(results_M['OutputPower'] * inputs_M['param_df']['CostVariable']).fillna(0).sum(axis=0).index).T
# costs_HOBO=pd.DataFrame(
#     (results_M['OutputHeat'] * inputs_M['param_df']['CostVariable']).fillna(0).sum(axis=0).values,
#     columns=['ALLFLEX'],
#     index=(results_M['OutputPower'] * inputs_M['param_df']['CostVariable']).fillna(0).sum(axis=0).index).T
# costs_var_HOBO = pd.DataFrame(index=scenarios, columns=tech_fuel)
# 
# for t in tech_fuel:
#     costs_var_HOBO.loc['Matijs', t] = costs_HOBO.loc[:, costs_var_raw_ALL.columns.str.endswith(t)].values.sum() / 1e9
# 
# costs_var = pd.DataFrame(index=scenarios, columns=tech_fuel)
# 
# for t in tech_fuel:
#     costs_var.loc['Matijs', t] = costs_var_raw_ALL.loc[:, costs_var_raw_ALL.columns.str.endswith(t)].values.sum() / 1e9
# costs_var.loc['Matijs','HOBO_GAS']=costs_var_HOBO.loc['Matijs','HOBO_GAS']
# 
# 
# for c in costs_var.columns:
#     if costs_var[c].values.sum() == 0:
#         costs_var.drop(columns=[c], inplace=True)
# 
# costs_breakdown = pd.concat([costs, costs_var], axis=1, sort=False)
# 
# costs_breakdown.drop(columns=['CostVariable'], inplace=True)
# costs_breakdown.drop(columns=['CostHeat'], inplace=True)
# 
# cols = ['CostHeatSlack', 'STUR_BIO_CHP', 'STUR_GAS_CHP','ICEN_GAS_CHP', 'STUR_HRD_CHP', 'STUR_OIL_CHP', 'GTUR_GAS_CHP', 
#         'COMC_GAS_CHP','HOBO_GAS',
#         'STUR_BIO', 'STUR_NUC', 'STUR_GAS', 'GTUR_GAS', 'COMC_GAS', 'STUR_OIL', 'STUR_HRD',
#         'STUR_LIG',
#         'CostStartUp', 'CostRampUp', 'Spillage', 'CostLoadShedding', 'LostLoad']
# 
# costs_breakdown = costs_breakdown[cols]
# #costs_breakdown.rename(columns={"CostHeatSlack": "CostBackupHeater"}, inplace=True)
# #costs_breakdown.rename(columns={"CostLoadShedding": "CostShedLoad"}, inplace=True)
# 
# costs_breakdown_plot = costs_breakdown
# costs_breakdown_plot.drop(columns=['Spillage'], inplace=True)
# costs_breakdown_plot.drop(columns=['LostLoad'], inplace=True)
# 
# costs_chp = costs_breakdown.loc[:, costs_breakdown.columns.str.endswith('CHP')].sum(axis=1)
# 
# tot_syst_cost = pd.DataFrame(index=['Total system Cost'], columns=scenarios)
# tot_syst_cost1 = pd.DataFrame(index=['Total system Cost'], columns=scenarios)
# tot_syst_cost.loc[:, 'Matijs'] = costs_raw_ALL.sum(axis=1).values / 1e9
# tot_syst_cost1.loc[:, 'Matijs'] = costs_breakdown_plot.sum(axis=1).values 
# 
# 
# # %% Costs breakdown plot
# plt.style.use('default')
# costs_breakdown_plot.rename(index={'Matijs':' '},inplace=True)
# ax = costs_breakdown_plot.plot(kind='bar', stacked=True, rot=0,
#                                color=[colors_tech.get(x) for x in costs_breakdown_plot.columns], legend=False,
#                                figsize=(10, 7.5), fontsize=15,width=0.4)
# 
# for container, hatch in zip(ax.containers, ('///', '///', '///', '///', '///', '///', '///', '///','///','///',)):
#     for patch in container.patches:
#         patch.set_hatch(hatch)
# 
# ax.set_ylabel('Costs [Billion €]', fontsize=15)
# #ax.set_xlabel('Scenario', fontsize=15)
# ax.set_title("Total System Costs", fontsize=15)
# handles, labels = ax.get_legend_handles_labels()
# ax.legend(reversed(handles), reversed(labels), loc='center left', bbox_to_anchor=(1, 0.5), ncol=2, fontsize=15)
# 
# fig = ax.get_figure()
# fig.savefig(output_folder + "\Costs Breakdown.png", bbox_inches='tight')
# 
# 
# =============================================================================

# %% Average cost of el without lost load

def ll_hours_index(results):
    if results['LostLoad_MaxPower'].values.sum() > 0:
        ll_hours_index = results['LostLoad_MaxPower'].index
    else:
        ll_hours_index = []
    return ll_hours_index


ll_hours_index_ALL = ll_hours_index(results_M)


def get_demand(inputs, results):
    demand = {}
    for z in inputs['sets']['n']:
# =============================================================================
#         if 'OutputPowerConsumption' in results:
#             demand_p2h = ds.filter_by_zone(results['OutputPowerConsumption'], inputs, z)
#             demand_p2h = demand_p2h.sum(axis=1)
#         else:
# =============================================================================
        demand_p2h = pd.Series(0, index=results['OutputPower'].index)
        demand_da = inputs['param_df']['Demand'][('DA', z)]
        demand[z] = pd.DataFrame(demand_da + demand_p2h, columns=[('DA', z)])
    demand = pd.concat(demand, axis=1)
    demand.columns = demand.columns.droplevel(-1)

    return demand


demand_f_ALL = get_demand(inputs_M, results_M).drop(list(ll_hours_index_ALL))


total_load_f_ALL = demand_f_ALL.sum().sum()
cost_f_ALL = results_M['OutputSystemCost'].drop(list(ll_hours_index_ALL)).sum()
cost_av_f_ALL = cost_f_ALL / total_load_f_ALL




# %% Heat demand shares

heat_demand_raw = inputs_M['param_df']['HeatDemand']

heat_demand = pd.DataFrame(index=heat_demand_raw.index, columns=inputs_M['param_df']['sets']['n'])

for c in inputs_M['param_df']['sets']['n']:
    heat_demand.loc[:, c] = heat_demand_raw.loc[:, heat_demand_raw.columns.str.contains(' ' + c + '_')].sum(axis=1)

heat_demand_dh = pd.DataFrame(index=heat_demand_raw.index, columns=heat_demand_raw.columns)
heat_demand_p2h = pd.DataFrame(index=heat_demand_raw.index, columns=heat_demand_raw.columns)

heat_demand_dh = heat_demand_raw.loc[:, heat_demand_raw.columns.str.contains('CHP')]
heat_demand_p2h = heat_demand_raw.loc[:, heat_demand_raw.columns.str.contains('P2HT')]

heat_demand_dh_tot = heat_demand_dh.sum(axis=1)
heat_demand_p2h_tot = heat_demand_p2h.sum(axis=1)

dh_perc = (heat_demand_dh_tot.sum()) / (heat_demand.sum(axis=1).sum())
p2h_perc = (heat_demand_p2h_tot.sum()) / (heat_demand.sum(axis=1).sum())

demand = inputs_M['param_df']['Demand']['DA']

demand_ratio = heat_demand.sum(axis=1).sum() / demand.sum().sum()

# for t in heat_demand_raw.columns:
#    if 'P2HT' in t:
#        heat_demand_p2h.loc[:,t] = heat_demand_raw.loc[:,t].sum(axis = 1)
#    else:
#        heat_demand_dh.loc[:,t] = heat_demand_raw.loc[:,heat_demand_raw.columns.str.contains(t)].sum(axis = 1)



# %% NTC Congestion

# libraries
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap

import matplotlib as mpl

countries = ['AT', 'BE', 'BG', 'CH', 'CZ', 'DE', 'DK', 'EE', 'EL', 'ES', 'FI', 'FR', 'HR', 'HU', 'IE', 'IT', 'LT', 'LU',
             'LV', 'NL', 'NO', 'PL', 'PT', 'RO', 'SE', 'SI', 'SK', 'UK']


# Build a dataframe with your connections

def build_cong_df(r_scenario):
    cong_scenario = pd.DataFrame(columns=['from', 'to', 'value'])

    for i in range(0, len(list(r_scenario['Congestion'].keys()))):
        cong_scenario.loc[i, 'from'] = list(r_scenario['Congestion'].keys())[i][:2]
        cong_scenario.loc[i, 'to'] = list(r_scenario['Congestion'].keys())[i][-2:]
        cong_scenario.loc[i, 'value'] = list(r_scenario['Congestion'].values())[i]

    cong_scenario["value"] = pd.to_numeric(cong_scenario["value"])

    return cong_scenario


cong_M = build_cong_df(r_M)



# %% Draw map function

def draw_map_cong(cong_scenario, scenario, path=False, namefile=None):
    plt.figure(figsize=(20, 10))
    #    plt.subplot(111)

    #    #Custom adjust of the subplots
    #    plt.subplots_adjust(left=0.05,right=0.9,top=0.90,bottom=0.1,wspace=0.15,hspace=0.15)
    #    plt.subplots_adjust(left=0.05,right=0.95,top=0.90,bottom=0.05,wspace=0.15,hspace=0.05)

    #    fig = plt.figure(figsize=(7,10))
    y1_shift = 4.5
    x1_shift = 6.5

    x1 = -12
    x2 = 28
    y1 = 36
    y2 = 65
    #    y1 = 32.
    #    x1 = -18.
    #    x2 = 32.

    #    lat_ts=(x1+x2)/2
    m = Basemap(projection='merc', resolution='l', lat_0=(y1 + y2) / 2, llcrnrlat=y1, urcrnrlat=y2, llcrnrlon=x1,
                urcrnrlon=x2)
    m.drawcountries(linewidth=0.2)
    m.fillcontinents(color='white', lake_color='white')
    m.drawcoastlines(linewidth=0.2)

    position = {'AT': (3431171.010925041 - x1_shift * 1e5, 2196945.658932812 - y1_shift * 1e5),
                'BE': (2409122.63439698 - x1_shift * 1e5, 2782458.279736769 - y1_shift * 1e5),
                'BG': (4708739.694503188 - x1_shift * 1e5, 1523426.2665741867 - y1_shift * 1e5),
                'CH': (2847144.9315600675 - x1_shift * 1e5, 2143261.1721419306 - y1_shift * 1e5),
                'CZ': (3668436.7387408563 - x1_shift * 1e5, 2596767.239598376 - y1_shift * 1e5),
                'DE': (2956650.5058508394 - x1_shift * 1e5, 2811413.149362125 - y1_shift * 1e5),
                'DK': (3066156.080141611 - x1_shift * 1e5, 3733264.972073233 - y1_shift * 1e5),
                'EE': (4818245.26879396 - x1_shift * 1e5, 4345101.374055384 - y1_shift * 1e5),
                'EL': (4380222.971630873 - x1_shift * 1e5, 942744.7517043282 - y1_shift * 1e5),
                'ES': (1533078.0400708055 - x1_shift * 1e5, 1084664.6122998544 - y1_shift * 1e5),
                'FI': (4818245.26879396 - x1_shift * 1e5, 5495424.022817817 - y1_shift * 1e5),
                'FR': (2190111.4858154366 - x1_shift * 1e5, 1984171.5761665502 - y1_shift * 1e5),
                'HR': (3768436.7387408563 - x1_shift * 1e5, 1623426.2665741867 - y1_shift * 1e5),
                'HU': (4161211.823049329 - x1_shift * 1e5, 2143261.1721419306 - y1_shift * 1e5),
                'IE': (1095055.7429077183 - x1_shift * 1e5, 3167223.489534808 - y1_shift * 1e5),
                'IT': (3176418.223779655 - x1_shift * 1e5, 1498500.042589245 - y1_shift * 1e5),
                'LT': (4599234.120212416 - x1_shift * 1e5, 3533264.972073233 - y1_shift * 1e5),
                'LU': (2646388.3622127953 - x1_shift * 1e5, 2596767.239598376 - y1_shift * 1e5),
                'LV': (4708739.694503188 - x1_shift * 1e5, 3931681.3009275147 - y1_shift * 1e5),
                'NL': (2600757.3894058308 - x1_shift * 1e5, 3076765.6906770044 - y1_shift * 1e5),
                'NO': (3066156.080141611 - x1_shift * 1e5, 5012797.17202571 - y1_shift * 1e5),
                'PL': (4161211.823049329 - x1_shift * 1e5, 2987330.8735358263 - y1_shift * 1e5),
                'PT': (1095055.7429077183 - x1_shift * 1e5, 1013449.4429983455 - y1_shift * 1e5),
                'RO': (4708739.694503188 - x1_shift * 1e5, 1984171.5761665502 - y1_shift * 1e5),
                'SE': (3613683.9515954703 - x1_shift * 1e5, 5012797.17202571 - y1_shift * 1e5),
                'SI': (3613683.9515954703 - x1_shift * 1e5, 1984171.5761665502 - y1_shift * 1e5),
                'SK': (4106459.0359039432 - x1_shift * 1e5, 2415178.327890961 - y1_shift * 1e5),
                'UK': (1752089.1886523492 - x1_shift * 1e5, 3351332.1756189675 - y1_shift * 1e5)}

    # Add color bar to the right
    colors = range(8784)
    #    cmap = plt.cm.hot_r
    cmap = mpl.colors.LinearSegmentedColormap.from_list("", ["green", "orange", "red"])
    vmin = min(colors)
    vmax = max(colors)

    G = nx.from_pandas_edgelist(cong_scenario, 'from', 'to', edge_attr='value', create_using=nx.DiGraph(directed=True))
    colors = [i['value'] for i in dict(G.edges).values()]

    nx.draw(G, position, with_labels=True, arrows=True, connectionstyle='arc3, rad = 0.1', edge_color=colors,
            node_color='lightblue', node_size=600, font_size=15, edge_cmap=cmap)

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=vmin, vmax=vmax))
    sm._A = []
    cbar = plt.colorbar(sm)
    cbar.ax.tick_params(labelsize=15)
    plt.title("Map of Congestion", fontsize=15)

    if path is not False:
        fig.savefig(path + '/' + namefile, bbox_inches='tight')
        plt.show()
    else:
        plt.show()


# %% Draw the NTC map

path = output_folder
draw_map_cong(cong_M, scenario = '2019', path = path, namefile = 'NTC ALLFLEX')


# %% Dis
#patch plot


# %% Additional functions from the read results dispaset file

# if needed, define the plotting range for the dispatch plot:
import pandas as pd

rng = pd.date_range(start='2016-01-01', end='2016-12-31', freq='h')

# Generate country-specific plots
ds.plot_zone(inputs_M, results_M, rng=rng, z='DE')

# Bar plot with the installed capacities in all countries:
cap = ds.plot_zone_capacities(inputs_M,results_M)

# Bar plot with the energy balances in all countries:
ds.plot_energy_zone_fuel(inputs_M, results_M, ds.get_indicators_powerplant(inputs_M, results_M))


