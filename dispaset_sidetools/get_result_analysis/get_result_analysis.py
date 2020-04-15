# -*- coding: utf-8 -*-
"""
Not part of Dispa-SET sidetools module
@authors: Andrea Mangipinto, Matija Pavičević
"""

# %% Imports

# Add the root folder of Dispa-SET to the path so that the library can be loaded:
import sys, os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pickle
import enlopy as el
import seaborn as sns
# Local source tree imports
from dispaset_sidetools.common import date_range, get_country_codes, write_csv_files, commons, make_dir

sys.path.append(os.path.abspath(r'../..'))
pd.options.display.float_format = '{:.4g}'.format
plt.style.use('default')

# %% Path where saving the plot figures
input_folder = commons['InputFolder']
source_folder = 'ARES_Africa/'
output_folder = commons['OutputFolder']
make_dir(output_folder + source_folder)
make_dir(output_folder + source_folder + 'Figures/')
folder_figures = output_folder + source_folder + 'Figures/'

# %% Load the inputs and the results/result analysis of the simulation
# Pickle files should alway contain results in the following order: inputs, results, r, costs, operation

with open(input_folder + source_folder + 'ARES_APP_Results.p', 'rb') as handle:
    inputs = pickle.load(handle)
    results = pickle.load(handle)
    r = pickle.load(handle)
    costs = pickle.load(handle)
    operation = pickle.load(handle)

scenarios = list(results.keys())

# %% Set and list definition
# tech_fuel_raw = list(inputs_R_H['units'].iloc[:, 0].astype(str).str[3:].unique())

tech_fuel = ['HDAM_WAT', 'HROR_WAT', 'HPHS_WAT', 'WTON_WIN', 'WTOF_WIN', 'PHOT_SUN', 'STUR_SUN', 'COMC_BIO', 'STUR_BIO',
             'STUR_NUC', 'STUR_GEO', 'STUR_GAS', 'GTUR_GAS', 'COMC_GAS', 'STUR_OIL', 'COMC_OIL', 'STUR_HRD', 'STUR_LIG',
             'STUR_BIO_CHP', 'STUR_GAS_CHP', 'STUR_HRD_CHP', 'STUR_OIL_CHP', 'GTUR_GAS_CHP', 'STUR_LIG_CHP',
             'COMC_GAS_CHP', 'P2HT_OTH', 'Heat Slack']

tech_fuel_heat = ['STUR_BIO_CHP', 'STUR_GAS_CHP', 'STUR_HRD_CHP', 'STUR_OIL_CHP', 'GTUR_GAS_CHP', 'STUR_LIG_CHP',
                  'COMC_GAS_CHP', 'P2HT_OTH', 'Heat Slack', 'Storage Losses']
tech_fuel_storage = ['HDAM_WAT', 'HROR_WAT', 'HPHS_WAT', 'BEVS_OTH']
colors_tech = {}
for tech in tech_fuel:
    if 'Slack' not in tech:
        if 'CHP' not in tech:
            colors_tech[tech] = commons['colors'][tech[-3:]]
        if 'CHP' in tech:
            colors_tech[tech] = commons['colors'][tech[5:-4]]

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
colors_tech['Backup Heater'] = 'darkorange'
colors_tech['Shed Load'] = 'orangered'
colors_tech['Lost Load'] = 'darkred'
colors_tech['Curtailment'] = 'salmon'
colors_tech['LostLoad'] = colors_tech['Lost Load']
colors_tech['CostLoadShedding'] = colors_tech['Shed Load']


# %% ########################### Analysis and charts #################################
# Helper functions
def filter_by_zone(inputs, zones):
    tmp_z = inputs['units']['Zone'].isin(zones)
    return tmp_z


def filter_by_tech(inputs, techs):
    tmp_t = inputs['units']['Technology'].isin(techs)
    return tmp_t


def filter_by_fuel(inputs, fuels):
    tmp_f = inputs['units']['Fuel'].isin(fuels)
    return tmp_f


def get_demand(inputs, results, zones=None):
    demand = {}
    if zones is None:
        zones = inputs['sets']['n']
    else:
        zones = zones
    for z in zones:
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


# %% Curtailment
def get_stats(inputs, results, variable):
    scenarios = list(results.keys())
    tmp = pd.DataFrame(index=['Total', 'Mean', 'Median', 'Max', 'Hours'], columns=scenarios)
    for s in scenarios:
        tmp.loc['Total', s] = results[s][variable].sum().sum()
        tmp.loc['Max', s] = results[s][variable].sum(axis=1).max()
        tmp.loc['Mean', s] = results[s][variable].sum(axis=1).mean()
        tmp.loc['Median', s] = results[s][variable].sum(axis=1).median()
        tmp.loc['Hours', s] = (results[s][variable].sum(axis=1) != 0).sum()
    return tmp


curtailment = get_stats(inputs, results, 'OutputCurtailedPower')
shed_load = get_stats(inputs, results, 'OutputShedLoad')

# Curtailment % with regard to V-RES generation
demand = pd.DataFrame(index=['DA'], columns=scenarios)
en_vres = pd.DataFrame(index=['OutputPower'], columns=scenarios)
zones = inputs['R_H']['sets']['n']
tech_res = ['HROR', 'WTON', 'WTOF', 'PHOT']
for s in scenarios:
    demand.loc['DA', s] = get_demand(inputs[s], results[s], zones).sum().sum()
    demand.loc['DA_max', s] = get_demand(inputs[s], results[s], zones).sum(axis=1).max()
    en_vres.loc['OutputPower', s] = results[s]['OutputPower'].loc[:, (filter_by_zone(inputs[s], zones)) & (
        filter_by_tech(inputs[s], tech_res))].sum().sum()
    curtailment.loc['Percentage total VRES', s] = curtailment.loc['Total', s] / (
            en_vres.loc['OutputPower', s] + curtailment.loc['Total', s]) * 100
    curtailment.loc['Percentage peak VRES', s] = curtailment.loc['Max', s] / (
            en_vres.loc['OutputPower', s] + curtailment.loc['Max', s]) * 100
    shed_load.loc['Percentage total Load', s] = shed_load.loc['Total', s] / (
            demand.loc['DA', s] + shed_load.loc['Total', s]) * 100
    shed_load.loc['Percentage peak Load', s] = shed_load.loc['Max', s] / (
            demand.loc['DA_max', s] + shed_load.loc['Max', s]) * 100

# %% Curtailment plot

ax = curtailment.loc['Percentage total VRES', :].T.plot(kind='bar', color='salmon', width=0.3, rot=0, position=1,
                                                        legend=True, figsize=(14, 5), fontsize=15)
ax2 = curtailment.loc['Percentage peak VRES', :].T.plot(kind='bar', color='firebrick', secondary_y=True, rot=0, ax=ax,
                                                        width=0.3, position=0, legend=True, mark_right=False,
                                                        fontsize=15)

ax.set_ylabel('Percentage Total VRES', fontsize=15)
ax2.set_ylabel('Percentage Peak VRES', fontsize=15)
ax.set_xlabel('Scenario', fontsize=15)
ax2.set_title("Curtailment", fontsize=15)

ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=1))
ax2.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=1))

fig = ax2.get_figure()
fig.savefig(folder_figures + "\Curtailment.png", bbox_inches='tight')
fig.clf()

# %% Shed Load plot

ax = shed_load.loc['Percentage total Load', :].T.plot(kind='bar', color='orangered', width=0.3, rot=0, figsize=(14, 5),
                                                      position=1, legend=True, fontsize=15)
ax2 = shed_load.loc['Percentage peak Load', :].T.plot(kind='bar', color='firebrick', secondary_y=True, rot=0, ax=ax,
                                                      width=0.3, position=0, legend=True, mark_right=False,
                                                      fontsize=15)

ax.set_ylabel('Percentage Total Load', fontsize=15)
ax2.set_ylabel('Percentage Peak Load', fontsize=15)
ax.set_xlabel('Scenario', fontsize=15)
ax2.set_title("Shed Load", fontsize=15)
ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=3))
ax2.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=1))

fig = ax2.get_figure()
fig.savefig(folder_figures + "\Shed Load.png", bbox_inches='tight')
fig.clf()

# %% CO2 emissions
co2 = pd.DataFrame(columns=scenarios)
fossil = ['GAS', 'HRD', 'LIG', 'OIL', 'OTH', 'BIO', 'WST']
techs = ['GTUR', 'STUR', 'COMC', 'ICEN']
for s in scenarios:
    for f in fossil:
        for t in techs:
            idx = t + '_' + f
            co2.loc[idx, s] = r[s]['UnitData']['CO2 [t]'].loc[(filter_by_zone(inputs[s], zones)) &
                                                              (filter_by_fuel(inputs[s], [f]) & filter_by_tech(
                                                                  inputs[s], [t]))].sum()
co2 = co2[(co2.T != 0).any()] / 1e6

# %% co2 emissions plot
ax = co2.T.plot(kind='bar', stacked=True, rot=0, color=[colors_tech.get(x) for x in co2.index], legend=False,
                figsize=(14, 5), fontsize=15)

# for container, hatch in zip(ax.containers,
#                             ("", '', '', '', '', '', '', '///', '///', '///', '///', '///', '///', '///', '///')):
#     for patch in container.patches:
#         patch.set_hatch(hatch)

ax.set_ylabel('[$CO_{2}$ [Mton]', fontsize=15)
ax.set_xlabel('Scenario', fontsize=15)
ax.set_title("$CO_{2}$ emissions", fontsize=15)
handles, labels = ax.get_legend_handles_labels()
ax.legend(reversed(handles), reversed(labels), loc='center left', bbox_to_anchor=(1, 0.5), ncol=1, fontsize=15)
ax.set_ylim(0, co2.sum().max() * 1.05)

fig = ax.get_figure()
fig.savefig(folder_figures + "\CO2 emissions.png", bbox_inches='tight')
fig.clf()

#%% Costs
costs_brakedown = pd.DataFrame(columns=scenarios)
for s in scenarios:
    for f in fossil:
        for t in techs:
            idx = t + '_' + f
            costs_brakedown.loc[idx, s] = operation[s].T.loc[(filter_by_zone(inputs[s], zones)) &
                                                              (filter_by_fuel(inputs[s], [f]) & filter_by_tech(
                                                                  inputs[s], [t]))].sum().sum()
    costs_brakedown.loc['ShedLoad', s] = costs[s][0]['CostLoadShedding'].sum()
costs_brakedown = costs_brakedown[(costs_brakedown.T != 0).any()]

# %% Costs breakdown plot
plt.style.use('default')

ax = costs_brakedown.T.plot(kind='bar', stacked=True, rot=0,
                               color=[colors_tech.get(x) for x in costs_brakedown.columns], legend=False,
                               figsize=(14, 5), fontsize=15)

# for container, hatch in zip(ax.containers, ('///', '///', '///', '///', '///', '///', '///', '///',)):
#     for patch in container.patches:
#         patch.set_hatch(hatch)

ax.set_ylabel('Costs [Billion €]', fontsize=15)
ax.set_xlabel('Scenario', fontsize=15)
ax.set_title("Total System Costs", fontsize=15)
handles, labels = ax.get_legend_handles_labels()
ax.legend(reversed(handles), reversed(labels), loc='center left', bbox_to_anchor=(1, 0.5), ncol=1, fontsize=15)
ax.set_ylim(0, costs_brakedown.sum().max() * 1.05)
ax.ticklabel_format(axis='y', style='sci', scilimits=(9,9))

fig = ax.get_figure()
fig.savefig(folder_figures + "\Costs Breakdown.png", bbox_inches='tight')
fig.clf()

# aa = costs_brakedown.sum()
# aa.to_csv('TotalCosts.csv')
# bb = aa/demand.loc['DA',:]
# bb.to_csv('AverageCosts.csv')

# %% Shadow price ALLFLEX - NOFLEX
import matplotlib

shad_price_ALL = results['R_H']['ShadowPrice']

for c in shad_price_ALL.columns:
    shad_price_ALL.loc[shad_price_ALL[c] >= 1e5, :] = 1e5

shad_price_ALL.sort_index(axis=1, inplace=True)

shad_price_NO = results['RN_H']['ShadowPrice']

for c in shad_price_NO.columns:
    shad_price_NO.loc[shad_price_NO[c] >= 1e5, :] = 1e5

shad_price_NO.sort_index(axis=1, inplace=True)

shad_price_TALL = results['T_H']['ShadowPrice']

for c in shad_price_TALL.columns:
    shad_price_TALL.loc[shad_price_TALL[c] >= 1e5, :] = 1e5

shad_price_TALL.sort_index(axis=1, inplace=True)

shad_price_TNO = results['TN_H']['ShadowPrice']

for c in shad_price_TNO.columns:
    shad_price_TNO.loc[shad_price_TNO[c] >= 1e5, :] = 1e5

shad_price_TNO.sort_index(axis=1, inplace=True)

# plots
fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(20, 7))
# fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(20, 7))

# sns.set(font_scale=1.17)
# fig, ax = plt.subplots(figsize=(10,5))
xticks_sh = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
ax1 = sns.heatmap(shad_price_ALL.T, ax=axes[0], vmax=400, cmap='summer', yticklabels=True, cbar=False)
sns.heatmap(shad_price_ALL.T, ax=axes[0], mask=shad_price_ALL.T < 1e5, cbar=False, cmap='bwr')
ax2 = sns.heatmap(shad_price_NO.T, ax=axes[1], cmap='summer', vmax=400, yticklabels=True, cbar=False)
sns.heatmap(shad_price_NO.T, ax=axes[1], mask=shad_price_NO.T < 1e5, cbar=False, cmap='bwr')

# PuOr
ax1.set_title('Shadow price for each zone - R_H', fontsize=18)
ax1.set_yticklabels(shad_price_ALL.columns, rotation=0)
ax1.set_xticks(range(1, 8784, 798))
ax1.set_xticklabels(xticks_sh, rotation=0)
ax1.tick_params(labelsize=15)

ax2.set_title('Shadow price for each zone - RN_H', fontsize=18)
ax2.set_yticklabels(shad_price_ALL.columns, rotation=0)
ax2.set_xticks(range(1, 8784, 798))
ax2.set_xticklabels(xticks_sh, rotation=0)
ax2.tick_params(labelsize=15)

mappable = ax1.get_children()[0]
cbar = plt.colorbar(mappable, ax=[axes[0], axes[1]], orientation='vertical')
cbar.ax.tick_params(labelsize=15)

fig = ax2.get_figure()
fig.legend(bbox_to_anchor=(1.04,0.5), loc="center left", borderaxespad=0)
# fig.tight_layout()
fig.subplots_adjust(right=0.75)
fig.savefig(folder_figures + "\Shadow price.png", bbox_inches='tight')
# fig.show()
fig.clf()
