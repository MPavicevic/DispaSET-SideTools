# -*- coding: utf-8 -*-
"""
Set of function for analyzing results from the North, Eastern and Central African Power Pools study

@authors: Matija Pavičević, Sylvain Quoilin
"""

# %% Imports
import os
import pickle
import sys
import logging

import matplotlib.cm as cm
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd

from matplotlib.patches import Rectangle
from dispaset_sidetools.common import commons, make_dir, reshape_timeseries

# Add the root folder of Dispa-SET-sidetools to the path so that the library can be loaded:
sys.path.append(os.path.abspath(r'../..'))
pd.options.display.float_format = '{:.4g}'.format
plt.style.use('default')

# %% Source/destination paths for data loading and plots/figures saving
input_folder = commons['InputFolder']
source_folder = 'ARES_Africa/'
results_folder = 'Results/'
# Select one of the folowing pickle files:
# 'JRC_Reference_results.p', 'JRC_Connected_results.p', 'JRC_WaterValue_results.p', 'TEMBA_results.p, 'Africa'
results_pickle = 'Africa'
output_folder = commons['OutputFolder']
make_dir(output_folder + source_folder)
make_dir(output_folder + source_folder + 'Figures/')
folder_figures = output_folder + source_folder + 'Figures/'
# only applicable for Africa scenarios - either Baseline or Connected
scenario = 'Connected'

########################################################################################################################
########################################!!! DO NOT MODIFY AFTER THIS LINE !!!###########################################
########################################################################################################################
# %% Flag that checks which scenario is being selected
if results_pickle == 'TEMBA_results.p':
    flag = 'TEMBA'
    make_dir(folder_figures + 'TEMBA/')
    folder_figures = folder_figures + 'TEMBA/'
elif results_pickle in ['JRC_Reference_results.p', 'JRC_Connected_results.p', 'JRC_WaterValue_results.p']:
    flag = 'Baseline'
    make_dir(folder_figures + 'Baseline/')
    folder_figures = folder_figures + 'Baseline/'
    if results_pickle == 'JRC_Reference_results.p':
        make_dir(folder_figures + 'Reference/')
        folder_figures = folder_figures + 'Reference/'
    elif results_pickle == 'JRC_Connected_results.p':
        make_dir(folder_figures + 'Connected/')
        folder_figures = folder_figures + 'Connected/'
    elif results_pickle == 'JRC_WaterValue_results.p':
        flag = 'WaterWalue'
        make_dir(folder_figures + 'WaterWalue/')
        folder_figures = folder_figures + 'WaterWalue/'
elif results_pickle == 'Africa':
    if scenario == 'Baseline':
        flag = 'Africa_Baseline'
    elif scenario == 'Connected':
        flag = 'Africa_Connected'
    make_dir(folder_figures + flag + '/')
    folder_figures = folder_figures + flag + '/'

# %% Load the inputs and the results/result analysis of the simulation
# Pickle files should always contain Dispa-SET results in the following order: inputs, results, r, costs, operation
if results_pickle in ['JRC_Reference_results.p', 'JRC_Connected_results.p', 'JRC_WaterValue_results.p',
                      'TEMBA_results.p']:
    with open(input_folder + source_folder + results_folder + results_pickle, 'rb') as handle:
        inputs = pickle.load(handle)
        results = pickle.load(handle)
        r = pickle.load(handle)
        costs = pickle.load(handle)
        operation = pickle.load(handle)
elif results_pickle == 'Africa':
    with open(input_folder + source_folder + results_folder + scenario + '_Inputs.p', 'rb') as handle:
        inputs = pickle.load(handle)
    with open(input_folder + source_folder + results_folder + scenario + '_Results.p', 'rb') as handle:
        results = pickle.load(handle)
    with open(input_folder + source_folder + results_folder + scenario + '_r.p', 'rb') as handle:
        r = pickle.load(handle)
    with open(input_folder + source_folder + results_folder + scenario + '_c.p', 'rb') as handle:
        costs = pickle.load(handle)
    with open(input_folder + source_folder + results_folder + scenario + '_operation.p', 'rb') as handle:
        operation = pickle.load(handle)
    with open(input_folder + source_folder + results_folder + scenario + '_pft.p', 'rb') as handle:
        pft = pickle.load(handle)
    with open(input_folder + source_folder + results_folder + scenario + '_pft_prct.p', 'rb') as handle:
        pft_prct = pickle.load(handle)


# %% Clean up scenario names to match labels in the study
def rename_scenarios(data, string, new_string):
    """
    Function used for renaming scenarios
    :param data:         either inputs, results, r, costs or operation
    :param string:       old string that should be renamed
    :param new_string:   new string
    :return:             data with new name
    """
    data = {k.replace(string, new_string): v for k, v in data.items()}
    return data


for to_rename in ['Baseline_NTC_', 'TEMBA_', 'Reference', '2.0deg', '1.5deg', 'Baseline_', 'Connected_']:
    if to_rename in ['TEMBA_', 'Baseline_NTC_', 'Baseline_', 'Connected_']:
        rename_into = ''
    elif to_rename == 'Reference':
        rename_into = 'Ref'
    elif to_rename == '2.0deg':
        rename_into = '2.0°C'
    elif to_rename == '1.5deg':
        rename_into = '1.5°C'
    else:
        logging.critical('Scenarios not properly selected ')
        sys.exit(0)

    inputs = rename_scenarios(inputs, to_rename, rename_into)
    results = rename_scenarios(results, to_rename, rename_into)
    r = rename_scenarios(r, to_rename, rename_into)
    costs = rename_scenarios(costs, to_rename, rename_into)
    operation = rename_scenarios(operation, to_rename, rename_into)

# List of new scenario names used inside the plots/figures
scenarios = list(results.keys())

# %% Set and list definition
tech_fuel = ['HDAM_WAT', 'HROR_WAT', 'HPHS_WAT', 'WTON_WIN', 'WTOF_WIN', 'PHOT_SUN', 'STUR_SUN', 'COMC_BIO', 'STUR_BIO',
             'STUR_NUC', 'STUR_GEO', 'STUR_GAS', 'GTUR_GAS', 'COMC_GAS', 'STUR_OIL', 'COMC_OIL', 'STUR_HRD', 'STUR_LIG',
             'STUR_BIO_CHP', 'STUR_GAS_CHP', 'STUR_HRD_CHP', 'STUR_OIL_CHP', 'GTUR_GAS_CHP', 'STUR_LIG_CHP',
             'COMC_GAS_CHP', 'P2HT_OTH', 'Heat Slack']

tech_fuel_heat = ['STUR_BIO_CHP', 'STUR_GAS_CHP', 'STUR_HRD_CHP', 'STUR_OIL_CHP', 'GTUR_GAS_CHP', 'STUR_LIG_CHP',
                  'COMC_GAS_CHP', 'P2HT_OTH', 'Heat Slack', 'Storage Losses']
tech_fuel_storage = ['HDAM_WAT', 'HROR_WAT', 'HPHS_WAT', 'BEVS_OTH']

# %% Colour selection
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
    """
    Function used for getting demand
    :param inputs:      inputs
    :param results:     results
    :param zones:       zones to filter
    :return:            demand
    """
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


# %% definition of power pools, each power pool is a separate list of zones
power_pools = [['BI', 'DJ', 'EG', 'ET', 'ER', 'KE', 'RW', 'SO', 'SD', 'SS', 'TZ', 'UG'],
               ['DZ', 'LY', 'MA', 'MR', 'TN'], ['CM', 'CF', 'CD', 'CG', 'GA', 'GQ', 'TD'],
               ['AO', 'BW', 'LS', 'MW', 'MZ', 'NA', 'SZ', 'ZA', 'ZM', 'ZW'],
               ['BF', 'BJ', 'CI', 'GH', 'GM', 'GN', 'GW', 'LR', 'ML', 'NE', 'NG', 'SL', 'SN', 'TG'],
               ['BI', 'DJ', 'EG', 'ET', 'ER', 'KE', 'RW', 'SO', 'SD', 'SS', 'TZ', 'UG',
                'DZ', 'LY', 'MA', 'MR', 'TN'], ['CM', 'CF', 'CD', 'CG', 'GA', 'GQ', 'TD',
                                                'AO', 'BW', 'LS', 'MW', 'MZ', 'NA', 'SZ', 'ZA', 'ZM', 'ZW',
                                                'BF', 'BJ', 'CI', 'GH', 'GM', 'GN', 'GW', 'LR', 'ML', 'NE', 'NG', 'SL',
                                                'SN', 'TG']
               ]


# %% Curtailment & Shed load
def get_stats(results, variable, zones):
    """
    Function used to search and filter through selected variable and zones in the results
    :param results:     dictionary of scenarios
    :param variable:    variable to search for
    :param zones:       zones to search for
    :return:            filtered variable
    """
    scenarios = list(results.keys())
    tmp = pd.DataFrame(index=['Total', 'Mean', 'Median', 'Max', 'Hours'], columns=scenarios)
    for s in scenarios:
        tmp.loc['Total', s] = results[s][variable].loc[:, results[s][variable].columns.isin(zones)].sum().sum()
        tmp.loc['Max', s] = results[s][variable].loc[:, results[s][variable].columns.isin(zones)].sum(axis=1).max()
        tmp.loc['Mean', s] = results[s][variable].loc[:, results[s][variable].columns.isin(zones)].sum(axis=1).mean()
        tmp.loc['Median', s] = results[s][variable].loc[:, results[s][variable].columns.isin(zones)].sum(
            axis=1).median()
        tmp.loc['Hours', s] = (
                results[s][variable].loc[:, results[s][variable].columns.isin(zones)].sum(axis=1) != 0).sum()
    return tmp


def plot_curtailment_shedding():
    all_pp = [power_pools[0], power_pools[1], power_pools[2], power_pools[3], power_pools[4],
              ['BI', 'DJ', 'EG', 'ET', 'ER', 'KE', 'RW', 'SO', 'SD', 'SS', 'TZ', 'UG',
               'DZ', 'LY', 'MA', 'MR', 'TN', 'CM', 'CF', 'CD', 'CG', 'GA', 'GQ', 'TD',
               'AO', 'BW', 'LS', 'MW', 'MZ', 'NA', 'SZ', 'ZA', 'ZM', 'ZW',
               'BF', 'BJ', 'CI', 'GH', 'GM', 'GN', 'GW', 'LR', 'ML', 'NE', 'NG', 'SL', 'SN', 'TG']]
    i = 0
    for z in all_pp:
        if i == 0:
            pp = 'EAPP'
        if i == 1:
            pp = 'NAPP'
        if i == 2:
            pp = 'CAPP'
        if i == 3:
            pp = 'SAPP'
        if i == 4:
            pp = 'WAPP'
        if i > 4:
            pp = ''

        curtailment = get_stats(results, 'OutputCurtailedPower', z)
        shed_load = get_stats(results, 'OutputShedLoad', z)

        # Curtailment % with regard to V-RES generation
        demand = pd.DataFrame(index=['DA'], columns=scenarios)
        en_vres = pd.DataFrame(index=['OutputPower'], columns=scenarios)
        tech_res = ['HROR', 'WTON', 'WTOF', 'PHOT']
        for s in scenarios:
            demand.loc['DA', s] = get_demand(inputs[s], results[s], z).sum().sum()
            demand.loc['DA_max', s] = get_demand(inputs[s], results[s], z).sum(axis=1).max()
            en_vres.loc['OutputPower', s] = results[s]['OutputPower'].loc[:, (filter_by_zone(inputs[s], z)) & (
                filter_by_tech(inputs[s], tech_res))].sum().sum()
            curtailment.loc['Percentage total VRES', s] = curtailment.loc['Total', s] / (
                    en_vres.loc['OutputPower', s] + curtailment.loc['Total', s]) * 100
            curtailment.loc['Percentage peak VRES', s] = curtailment.loc['Max', s] / (
                    en_vres.loc['OutputPower', s] + curtailment.loc['Max', s]) * 100
            shed_load.loc['Percentage total Load', s] = shed_load.loc['Total', s] / (
                    demand.loc['DA', s] + shed_load.loc['Total', s]) * 100
            shed_load.loc['Percentage peak Load', s] = shed_load.loc['Max', s] / (
                    demand.loc['DA_max', s] + shed_load.loc['Max', s]) * 100

        # Curtailment plot
        ax = curtailment.loc['Percentage total VRES', :].T.plot(kind='bar', color='salmon',
                                                                width=0.3, rot=0, position=1,
                                                                figsize=(14, 5), fontsize=15)
        ax2 = curtailment.loc['Percentage peak VRES', :].T.plot(kind='bar', color='firebrick',
                                                                secondary_y=True, ax=ax,
                                                                width=0.3, rot=0, position=0,
                                                                mark_right=False, fontsize=15)

        ax.set_ylabel('Percentage Total VRES', fontsize=15)
        ax2.set_ylabel('Percentage Peak VRES', fontsize=15)
        if flag == 'TEMBA':
            ax.set_xlabel('Scenario', fontsize=15)
        else:
            ax.set_xlabel('Weather year', fontsize=15)
        ax2.set_title("Curtailment " + pp, fontsize=15)

        ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
        ax2.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=2))
        ax.tick_params(axis='x', rotation=90)
        lines, labels = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax2.legend(lines + lines2, labels + labels2, loc='upper right')

        fig = ax2.get_figure()
        fig.savefig(folder_figures + "\Curtailment " + pp + '.png', bbox_inches='tight')
        fig.clf()

        # Shed Load plot
        ax = shed_load.loc['Percentage total Load', :].T.plot(kind='bar', color='orangered',
                                                              width=0.3, rot=0, position=1,
                                                              figsize=(14, 5), fontsize=15)
        ax2 = shed_load.loc['Percentage peak Load', :].T.plot(kind='bar', color='firebrick',
                                                              secondary_y=True, ax=ax,
                                                              width=0.3, rot=0, position=0,
                                                              mark_right=False, fontsize=15)

        ax.set_ylabel('Percentage Total Load', fontsize=15)
        ax2.set_ylabel('Percentage Peak Load', fontsize=15)
        if flag == 'TEMBA':
            ax.set_xlabel('Scenario', fontsize=15)
        else:
            ax.set_xlabel('Weather year', fontsize=15)
        ax2.set_title("Shed Load " + pp, fontsize=15)

        ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=2))
        ax2.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=1))
        ax.tick_params(axis='x', rotation=90)
        lines, labels = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax2.legend(lines + lines2, labels + labels2)

        fig = ax2.get_figure()
        fig.savefig(folder_figures + "\Shed Load " + pp + '.png', bbox_inches='tight')
        fig.clf()

        i = i + 1


# %% CO2 emissions
zones = [['BI', 'DJ', 'EG', 'ET', 'ER', 'KE', 'RW', 'SO', 'SD', 'SS', 'TZ', 'UG'],
         ['DZ', 'LY', 'MA', 'MR', 'TN'],
         ['CM', 'CF', 'CD', 'CG', 'GA', 'GQ', 'TD'],
         ['AO', 'BW', 'LS', 'MW', 'MZ', 'NA', 'SZ', 'ZA', 'ZM', 'ZW'],
         ['BF', 'BJ', 'CI', 'GH', 'GM', 'GN', 'GW', 'LR', 'ML', 'NE', 'NG', 'SL', 'SN', 'TG'],
         ]
fossil = ['GAS', 'HRD', 'LIG', 'OIL', 'OTH', 'BIO', 'WST']
techs = ['GTUR', 'STUR', 'COMC', 'ICEN']


def plot_co2():
    co2 = pd.DataFrame(columns=scenarios)
    # fossil = ['GAS', 'HRD', 'LIG', 'OIL', 'OTH', 'BIO', 'WST']
    # techs = ['GTUR', 'STUR', 'COMC', 'ICEN']
    for s in scenarios:
        for f in fossil:
            for t in techs:
                idx = t + '_' + f
                co2.loc[idx, s] = r[s]['UnitData']['CO2 [t]'].loc[(filter_by_zone(inputs[s], zones)) &
                                                                  (filter_by_fuel(inputs[s], [f]) & filter_by_tech(
                                                                      inputs[s], [t]))].sum()
    co2 = co2[(co2.T != 0).any()] / 1e6

    # co2 emissions plot
    ax = co2.T.plot(kind='bar', stacked=True, rot=0, color=[colors_tech.get(x) for x in co2.index], legend=False,
                    figsize=(14, 5), fontsize=15)

    ax.set_ylabel('[$CO_{2}$ [Mton]', fontsize=15)
    if flag == 'TEMBA':
        ax.set_xlabel('Scenario', fontsize=15)
    else:
        ax.set_xlabel('Weather year', fontsize=15)
    ax.set_title("$CO_{2}$ emissions", fontsize=15)

    handles, labels = ax.get_legend_handles_labels()
    ax.legend(reversed(handles), reversed(labels), loc='center left', bbox_to_anchor=(1, 0.5), ncol=1, fontsize=15)
    ax.set_ylim(0, co2.sum().max() * 1.05)
    ax.tick_params(axis='x', rotation=90)

    if flag == 'Baseline':
        # Add rectangle for year 1985
        rect = Rectangle((4.5, 0), 1, co2.sum().max() * 1.025,
                         linewidth=2, edgecolor='green', linestyle='dashed', facecolor='None', clip_on=False, zorder=2)
        ax.add_patch(rect)
        # Add the rectangle
        rect = Rectangle((28.5, 0), 1, co2.sum().max() * 1.025,
                         linewidth=2, edgecolor='red', linestyle='dashed', facecolor='None', clip_on=False, zorder=2)
        ax.add_patch(rect)

    fig = ax.get_figure()
    fig.savefig(folder_figures + "\CO2 emissions.png", bbox_inches='tight')
    fig.clf()


# %% Costs
def plot_costs():
    costs_brakedown = pd.DataFrame(columns=scenarios)
    for s in scenarios:
        for f in fossil:
            for t in techs:
                idx = t + '_' + f
                costs_brakedown.loc[idx, s] = operation[s].T.loc[(filter_by_zone(inputs[s], zones)) &
                                                                 (filter_by_fuel(inputs[s], [f]) & filter_by_tech(
                                                                     inputs[s], [t]))].sum().sum()
        costs_brakedown.loc['ShedLoad', s] = costs[s][0]['CostLoadShedding'].sum()
    costs_brakedown = costs_brakedown[(costs_brakedown.T != 0).any()] / 1e9

    # Costs breakdown plot
    plt.style.use('default')

    ax = costs_brakedown.T.plot(kind='bar', stacked=True, rot=0,
                                color=[colors_tech.get(x) for x in costs_brakedown.columns], legend=False,
                                figsize=(14, 5), fontsize=15)

    ax.set_ylabel('Costs [Billion €]', fontsize=15)
    if flag == 'TEMBA':
        ax.set_xlabel('Scenario', fontsize=15)
    else:
        ax.set_xlabel('Weather year', fontsize=15)
    ax.set_title("Total System Costs", fontsize=15)
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(reversed(handles), reversed(labels), loc='center left', bbox_to_anchor=(1, 0.5), ncol=1, fontsize=15)
    ax.set_ylim(0, costs_brakedown.sum().max() * 1.05)
    ax.ticklabel_format(axis='y', style='plain', scilimits=(9, 9))
    ax.tick_params(axis='x', rotation=90)

    if flag == 'Baseline':
        # Add rectangle for year 1985
        rect = Rectangle((4.5, 0), 1, costs_brakedown.sum().max() * 1.025,
                         linewidth=2, edgecolor='green', linestyle='dashed', facecolor='None', clip_on=False, zorder=2)
        ax.add_patch(rect)
        # Add the rectangle
        rect = Rectangle((28.5, 0), 1, costs_brakedown.sum().max() * 1.025,
                         linewidth=2, edgecolor='red', linestyle='dashed', facecolor='None', clip_on=False, zorder=2)
        ax.add_patch(rect)

    fig = ax.get_figure()
    fig.savefig(folder_figures + "\Costs Breakdown.png", bbox_inches='tight')
    fig.clf()


# %% fuel breakdown plot
def plot_fuel_bar(data, plot_style='default', fig_size=(14, 5), font_size=15, y_label=None, x_label=None,
                  title=None, style='plain', sci_limits=None, png_name=None):
    """
    Function that generates plot per fuel types for each scenario
    :param data:            raw data in form of timeseries
    :param plot_style:      plot style
    :param fig_size:        size of figure 14,5 prefered
    :param font_size:       font size prefered 15
    :param y_label:         y-label
    :param x_label:         x-label (in this case refers to scenarios)
    :param title:           chart title
    :param sci_limits:      scientific axis limits (0,3,6,9...)
    :param png_name:        name of file to be saved on the hard drive
    :return:
    """
    plt.style.use(plot_style)

    ax = data.T.plot(kind='bar',
                     stacked=True,
                     rot=0,
                     color=[commons['colors'].get(x) for x in data.T.columns],
                     legend=False,
                     figsize=fig_size,
                     fontsize=15)

    ax.set_ylabel(y_label, fontsize=font_size)
    ax.set_xlabel(x_label, fontsize=font_size)
    ax.set_title(title, fontsize=font_size)
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(reversed(handles), reversed(labels), loc='center left', bbox_to_anchor=(1, 0.5), ncol=1,
              fontsize=font_size)
    ax.set_ylim(0, data.sum().max() * 1.05)
    ax.ticklabel_format(axis='y', style=style, scilimits=sci_limits)
    ax.tick_params(axis='x', rotation=90)

    fig = ax.get_figure()
    fig.savefig(folder_figures + "/" + png_name + ".png", bbox_inches='tight')
    fig.clf()


# %% Generation
def get_generation_indicators(results, zones):
    generation_breakdown = pd.DataFrame(columns=scenarios)
    for s in scenarios:
        for f in commons['Fuels']:
            idx = f
            generation_breakdown.loc[idx, s] = results[s]['OutputPower'].T.loc[(filter_by_zone(inputs[s], zones)) &
                                                                               (filter_by_fuel(inputs[s],
                                                                                               [f]))].sum().sum()
    generation_breakdown = generation_breakdown[(generation_breakdown.T != 0).any()] / 1e6
    return generation_breakdown


# %% Water withdrawals and consumption
def get_water_indicators(r, zones):
    """

    :param r:       r calculated by dispaset
    :param zones:   zones to get the data for
    :return:
    """
    withdrawal_breakedown = pd.DataFrame(columns=scenarios)
    consumption_breakedown = pd.DataFrame(columns=scenarios)
    for s in scenarios:
        for f in commons['Fuels']:
            idx = f
            withdrawal_breakedown.loc[idx, s] = r[s]['WaterConsumptionData']['UnitLevel']['WaterWithdrawal'].T.loc[
                (filter_by_zone(inputs[s], zones)) & (filter_by_fuel(inputs[s], [f]))].sum().sum()
            consumption_breakedown.loc[idx, s] = r[s]['WaterConsumptionData']['UnitLevel']['WaterConsumption'].T.loc[
                (filter_by_zone(inputs[s], zones)) & (filter_by_fuel(inputs[s], [f]))].sum().sum()
    withdrawal_breakedown = withdrawal_breakedown[(withdrawal_breakedown.T != 0).any()] / 1e9
    consumption_breakedown = consumption_breakedown[(consumption_breakedown.T != 0).any()] / 1e9
    return withdrawal_breakedown, consumption_breakedown


# %% Plot heatmap
def plot_heatmap(Load, x='dayofyear', y='hour', aggfunc='sum', bins=8, figsize=(15, 14), edgecolors='none',
                 cmap='Oranges', colorbar=True, columns=1, x_ax_label=[0, 2], y_ax_label=[0, 2], pool=False,
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
                ax.set_xticks([0, 90, 180, 270, 365])
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
                    elif (i >= 12) and (i < 17):
                        for spine in ax.spines.values():
                            spine.set_edgecolor('#b4dc00')
                            spine.set_linewidth(4)
                    elif i >= 17:
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
    fig.savefig(folder_figures + '/' + png_name + '.png')
    plt.show()


# %% Plot percentiles
def plot_percentiles(Load, x='hour', zz='week', perc_list=[[5, 95], [25, 75], 50], columns=1, ax=None, color='blue',
                     figsize=(15, 15), fig_name=None, x_ax_label=[0, 2], y_ax_label=[0, 2], y_label=None,
                     y_limit=(0, 1), **kwargs):
    """Plot predefined percentiles per timestep

    Arguments:
        Load: 1D pandas with timed index
        x (str): x axis aggregator. See :meth:`enlopy.analysis.reshape_timeseries`
        zz (str): similar to above for y axis
        perc_list(list): List of percentiles to plot. If it is an integer then it will be plotted as a line. If it is list it has to contain two items and it will be plotted using fill_between()
        **kwargs: exposes arguments of :meth:`matplotlib.pyplot.fill_between`
    Returns:
        Plot

    """

    rows = int(len(Load.columns) / columns) + (len(Load.columns) % columns > 0)
    fig = plt.figure(figsize=figsize, constrained_layout=True)
    spec = fig.add_gridspec(nrows=rows, ncols=columns)

    j = 0
    for row in range(rows):
        for col in range(columns):
            if j < len(Load.columns):
                ax = fig.add_subplot(spec[row, col])
                bb = Load.iloc[:, j]
                a = reshape_timeseries(bb, x=x, y=zz, aggfunc='mean')
                xx = a.columns.values
                for i in perc_list:
                    if len(np.atleast_1d(i)) == 1:
                        perc = a.apply(lambda x: np.nanpercentile(x.values, i), axis=0)
                        ax.plot(xx, perc.values, color='black')
                    elif len(np.atleast_1d(i)) == 2:
                        perc0 = a.apply(lambda x: np.nanpercentile(x.values, i[0]), axis=0)
                        perc1 = a.apply(lambda x: np.nanpercentile(x.values, i[1]), axis=0)

                        ax.fill_between(xx, perc0, perc1, lw=.5, alpha=.3, color=color)
                    else:
                        raise ValueError('List items should be scalars or 2-item lists')

                ax.set_xlim(left=min(xx), right=max(xx))
                # ax.set_xlabel(x)
                if j in x_ax_label:
                    ax.set_xlabel(x)
                if j in y_ax_label:
                    ax.set_ylabel(y_label)
                ax.set_title(bb.name)
                if y_limit is not None:
                    ax.set_ylim(y_limit)
            j = j + 1
    # folder_figures = output_folder + source_folder + 'Figures/'
    # fig.savefig(folder_figures + "\Hydro_CF_PowerPool.png")
    fig.savefig(folder_figures + '/' + fig_name + '.png')
    plt.show()


def get_append_scenarios(results, variable):
    tmp = pd.DataFrame()
    for s in scenarios:
        tmp = tmp.append(results[s][variable])
    return tmp


# aa = get_append_scenarios(results, 'OutputStorageLevel')
#
# plot_percentiles(aa, x='dayofyear', zz='year', color='blue', columns = 5, figsize=(12,14),
#                  perc_list=[[0,100], [5, 95], [25, 75], 50], fig_name='Storage Levels ',
#                  x_ax_label=[11, 12], y_ax_label=[0, 2, 4, 6, 8, 10, 12], y_label='Storage Level', y_limit=(0, 1.05)
#                  )

# %% Startups
def get_startups(inputs, results):
    startups = pd.DataFrame(index=scenarios, columns=inputs['1980']['units'].index)
    shutdowns = pd.DataFrame(index=scenarios, columns=inputs['1980']['units'].index)
    for s in scenarios:
        tmp_startups = results[s]['OutputCommitted'].copy()
        for u in tmp_startups:
            values = tmp_startups.loc[:, u].values
            diff = -(np.roll(values, 1) - values)
            diff[diff <= 0] = 0
            tmp_startups[u] = diff
        startups.loc[s, tmp_startups.columns] = tmp_startups.sum(axis=0)
        startups.fillna(0, inplace=True)

        # DataFrame with shutdown times for each unit (1 for shutdown)
        tmp_shutdowns = results[s]['OutputCommitted'].copy()
        for u in tmp_shutdowns:
            values = tmp_shutdowns.loc[:, u].values
            diff = (np.roll(values, 1) - values)
            diff[diff <= 0] = 0
            tmp_shutdowns[u] = diff
        shutdowns.loc[s, tmp_shutdowns.columns] = tmp_shutdowns.sum(axis=0)
        shutdowns.fillna(0, inplace=True)
    return startups, shutdowns


def get_startup_indicators(data, zones):
    startup = pd.DataFrame(columns=scenarios)
    for s in scenarios:
        for f in fossil:
            idx = f
            startup.loc[idx, s] = data.loc[s, (filter_by_zone(inputs[s], zones)) &
                                           (filter_by_fuel(inputs[s], [f]))].sum()
    startup = startup[(startup.T != 0).any()]
    return startup


# %% Assign inflows for particular power plants
def plot_water_stress():
    inflows_KENITRA = pd.read_csv(input_folder + source_folder + 'AfricaDamsInFlows/' + '067_Allal_Al_Fassi.csv',
                                  index_col=0, parse_dates=['time'])
    inflows_KENITRA.rename(columns={'dis': '[135, 137, 139, 179, 186, 192, 198, 199] - DZ - STUR - GAS'}, inplace=True)
    inflows_KENITRA = inflows_KENITRA * 3600
    inflows_KENITRA = inflows_KENITRA.resample('H').interpolate(method='linear')

    inflows_GQ = pd.read_csv(input_folder + source_folder + 'AfricaDamsInFlows/' + '039_Djiboloho.csv', index_col=0,
                             parse_dates=['time'])
    inflows_GQ.rename(columns={'dis': '[435, 437, 439] - GQ - GTUR - GAS'}, inplace=True)
    inflows_GQ = inflows_GQ * 3600
    inflows_GQ = inflows_GQ.resample('H').interpolate(method='linear')

    inflows_RW = pd.read_csv(input_folder + source_folder + 'AfricaDamsInFlows/' + '083_Ntaruka.csv', index_col=0,
                             parse_dates=['time'])
    inflows_RW.rename(columns={'dis': '[613, 614] - RW - ICEN - GAS'}, inplace=True)
    inflows_RW = inflows_RW * 3600
    inflows_RW = inflows_RW.resample('H').interpolate(method='linear')

    unit_name = ['[135, 137, 139, 179, 186, 192, 198, 199] - DZ - STUR - GAS',
                 '[435, 437, 439] - GQ - GTUR - GAS',
                 '[613, 614] - RW - ICEN - GAS']
    tmp_unit_withd = pd.DataFrame(columns=unit_name)
    for s in scenarios:
        aa = pd.DataFrame(columns=unit_name)
        aa['[135, 137, 139, 179, 186, 192, 198, 199] - DZ - STUR - GAS'] = \
            r[s]['WaterConsumptionData']['UnitLevel']['WaterWithdrawal'].loc[:,
            '[135, 137, 139, 179, 186, 192, 198, 199] - DZ - STUR - GAS'] * 588 / 2570.2
        aa['[435, 437, 439] - GQ - GTUR - GAS'] = \
            r[s]['WaterConsumptionData']['UnitLevel']['WaterWithdrawal'].loc[:,
            '[435, 437, 439] - GQ - GTUR - GAS'] * 84 / 146.9
        aa['[613, 614] - RW - ICEN - GAS'] = \
            r[s]['WaterConsumptionData']['UnitLevel']['WaterWithdrawal'].loc[:,
            '[613, 614] - RW - ICEN - GAS']
        tmp_unit_withd = tmp_unit_withd.append(aa)

    inflows = pd.concat([inflows_KENITRA, inflows_GQ], axis=1, sort=False)
    inflows = pd.concat([inflows, inflows_RW], axis=1, sort=False)
    inflows.fillna(0, inplace=True)

    unit_stress = tmp_unit_withd / inflows
    unit_stress.rename(columns={'[135, 137, 139, 179, 186, 192, 198, 199] - DZ - STUR - GAS': 'Kenitra - NAPP',
                                '[435, 437, 439] - GQ - GTUR - GAS': 'Kilometro Cinco - CAPP',
                                '[613, 614] - RW - ICEN - GAS': 'Kibuye Kivuwatt - EAPP'}, inplace=True)
    # bb = r['1980']['WaterConsumptionData']['UnitLevel']['WaterWithdrawal'].loc[:,'[182] - Koudiet Eddraouch'] / inflows_koudiet

    # aa = tmp_withd/inflows
    # bb = aa.dropna(axis=1)
    #
    plot_percentiles(unit_stress, x='dayofyear', zz='year', color='red', columns=3, figsize=(12, 4),
                     perc_list=[[0, 100], [5, 95], [25, 75], 50], fig_name='Withdrawal Hourly v1',
                     x_ax_label=[0, 1, 2, 22, 23], y_ax_label=[0, 5, 10, 15, 20], y_label='Water stress index [-]',
                     y_limit=None
                     )


generation = {}
# %% Execute plot scripts
if flag == 'WaterWalue':
    plot_heatmap(results['1985']['StorageShadowPrice'], bins=30, figsize=(15, 12), cmap='RdBu_r', colorbar=True,
                 columns=2,
                 x_ax_label=[10, 11, 12], y_ax_label=[0, 3, 6, 9, 12], png_name='Storage Shadow Price Wet')
    plot_heatmap(results['2009']['StorageShadowPrice'], bins=30, figsize=(15, 12), cmap='RdBu_r', colorbar=True,
                 columns=2,
                 x_ax_label=[10, 11, 12], y_ax_label=[0, 3, 6, 9, 12], png_name='Storage Shadow Price Dry')
else:
    # plot_curtailment_shedding()
    # plot_co2()
    # plot_costs()
    # if flag == 'TEMBA':
    #     plot_fuel_bar(get_generation_indicators(results, zones), y_label='Generation [TWh]', x_label='Scenario',
    #                   title='Total Generation', sci_limits=(0, 0), png_name='Generation Breakdown')
    #     plot_fuel_bar(get_water_indicators(r, zones)[0], y_label='Withdrawal (billion m3)', x_label='Scenario',
    #                   title='Water Withdrawal', sci_limits=(0, 0), png_name='Water Withdrawal')
    #     plot_fuel_bar(get_water_indicators(r, zones)[1], y_label='Consumption (billion m3)', x_label='Scenario',
    #                   title='Water Consumption', sci_limits=(0, 0), png_name='Water Consumption')
    # else:
    #     plot_fuel_bar(get_generation_indicators(results, zones), y_label='Generation [TWh]', x_label='Weather year',
    #                   title='Total Generation', sci_limits=(0, 0), png_name='Generation Breakdown')
    #     plot_fuel_bar(get_water_indicators(r, zones)[0], y_label='Withdrawal (billion m3)', x_label='Weather year',
    #                   title='Water Withdrawal', sci_limits=(0, 0), png_name='Water Withdrawal')
    #     plot_fuel_bar(get_water_indicators(r, zones)[1], y_label='Consumption (billion m3)', x_label='Weather year',
    #                   title='Water Consumption', sci_limits=(0, 0), png_name='Water Consumption')

    # %% Plots for Individual power pools
    if (flag == 'Baseline') and (results_pickle != 'JRC_Connected_results.p'):
        aa = get_startups(inputs, results)
    i = 0
    for z in power_pools:
        if i == 0:
            png_name = 'EAPP'
        if i == 1:
            png_name = 'NAPP'
        if i == 2:
            png_name = 'CAPP'
        if i == 3:
            png_name = 'SAPP'
        if i == 4:
            png_name = 'WAPP'
        if i == 5:
            png_name = 'Africa'

        generation[png_name] = get_generation_indicators(results, z)
        i = i + 1

    #     if flag == 'TEMBA':
    #         plot_fuel_bar(get_water_indicators(r, z)[0], y_label='Withdrawal (billion m3)', x_label='Scenario',
    #                       title='Water Withdrawal ' + png_name, sci_limits=(0, 0), png_name='Water Withdrawal ' + png_name)
    #         plot_fuel_bar(get_water_indicators(r, z)[1], y_label='Consumption (billion m3)', x_label='Scenario',
    #                       title='Water Consumption ' + png_name, sci_limits=(0, 0),
    #                       png_name='Water Consumption ' + png_name)
    #         plot_fuel_bar(get_generation_indicators(results, z), y_label='Generation [TWh]', x_label='Scenario',
    #                       title='Total Generation ' + png_name, sci_limits=(0, 0),
    #                       png_name='Generation Breakdown ' + png_name)
    #     else:
    #         plot_fuel_bar(get_water_indicators(r, z)[0], y_label='Withdrawal (billion m3)', x_label='Weather year',
    #                       title='Water Withdrawal ' + png_name, sci_limits=(0, 0), png_name='Water Withdrawal ' + png_name)
    #         plot_fuel_bar(get_water_indicators(r, z)[1], y_label='Consumption (billion m3)', x_label='Weather year',
    #                       title='Water Consumption ' + png_name, sci_limits=(0, 0),
    #                       png_name='Water Consumption ' + png_name)
    #         plot_fuel_bar(get_generation_indicators(results, z), y_label='Generation [TWh]', x_label='Weather year',
    #                       title='Total Generation ' + png_name, sci_limits=(0, 0),
    #                       png_name='Generation Breakdown ' + png_name)
    #     if (flag == 'Baseline') and (results_pickle != 'JRC_Connected_results.p'):
    #         startup = get_startup_indicators(aa[0], z)
    #         plot_fuel_bar(startup, y_label='Startups [-]', x_label='Weather year', title='Total Startups ' + png_name,
    #                       sci_limits=(0, 0), png_name='Startups ' + png_name)
    #         shutdown = get_startup_indicators(aa[1], z)
    #         plot_fuel_bar(shutdown, y_label='Shutdowns [-]', x_label='Weather year', title='Total Shutdowns ' + png_name,
    #                       sci_limits=(0, 0), png_name='Shutdowns ' + png_name)
    #     i = i + 1
    #
    # if flag == 'Baseline':
    #     wet = results['1985']['ShadowPrice']
    #     wet = wet[zones]
    #     dry = results['2009']['ShadowPrice']
    #     dry = dry[zones]
    #     avg = results['1999']['ShadowPrice']
    #     avg = avg[zones]
    #
    #     plot_heatmap(wet, bins=30, figsize=(10, 9), cmap='RdBu_r', colorbar=True, columns=5, pool=True,
    #                  x_ax_label=[20, 21, 22, 23, 24], y_ax_label=[0, 5, 10, 15, 20], png_name='Shadow Price Wet')
    #     plot_heatmap(dry, bins=30, figsize=(10, 9), cmap='RdBu_r', colorbar=True, columns=5, pool=True,
    #                  x_ax_label=[20, 21, 22, 23, 24], y_ax_label=[0, 5, 10, 15, 20], png_name='Shadow Price Dry')
    #     plot_heatmap(avg, bins=30, figsize=(10, 9), cmap='RdBu_r', colorbar=True, columns=5, pool=True,
    #                  x_ax_label=[20, 21, 22, 23, 24], y_ax_label=[0, 5, 10, 15, 20], png_name='Shadow Price Avg')
    #
    #     if (flag == 'Baseline') and (results_pickle != 'JRC_Connected_results.p'):
    #         plot_water_stress()
    #         demand = inputs['1985']['param_df']['Demand']['DA']
    #         demand = demand / demand.max()
    #         demand = demand[zones]
    #         plot_heatmap(demand, bins=30, figsize=(10, 9), cmap='Blues', colorbar=True, columns=5, pool=True,
    #                      x_ax_label=[20, 21, 22, 23, 24], y_ax_label=[0, 5, 10, 15, 20], png_name='Demand',
    #                      vmin=0.25, vmax=1)

# startup = aa[0]
# startup = startup.loc[:, (startup != 0).any(axis=0)]
#
# startup.to_csv('startups.csv')
#
# bb = pd.DataFrame()
# for z in zones:
#     aa = get_generation_indicators(results, z)
#     bb.loc[z]
#
#
# def get_water_indicators_hourly(r, zones, s):
#     """
#
#     :param r:       r calculated by dispaset
#     :param zones:   zones to get the data for
#     :return:
#     """
#     withdrawal_breakedown = pd.DataFrame(columns=zones)
#     consumption_breakedown = pd.DataFrame(columns=zones)
#     for z in zones:
#         withdrawal_breakedown.loc[:, z] = r[s]['WaterConsumptionData']['UnitLevel']['WaterWithdrawal'].T.loc[
#             (filter_by_zone(inputs[s], [z]))].sum()
#         consumption_breakedown.loc[:, z] = r[s]['WaterConsumptionData']['UnitLevel']['WaterConsumption'].T.loc[
#             (filter_by_zone(inputs[s], [z]))].sum()
#     return withdrawal_breakedown, consumption_breakedown
#
#
# tmp_withd = pd.DataFrame(columns=zones)
# tmp_cons = pd.DataFrame(columns=zones)
# for s in scenarios:
#     aa = get_water_indicators_hourly(r, zones, s)
#     tmp_withd = tmp_withd.append(aa[0])
#     tmp_cons = tmp_cons.append(aa[1])
#
# max_withd = tmp_withd.max(axis=0)
# max_cons = tmp_cons.max(axis=0)
#
# tmp_withd = tmp_withd / max_withd
# tmp_cons = tmp_cons / max_cons
#
# tmp_withd.fillna(0, inplace=True)
# tmp_cons.dropna(axis='columns', inplace=True)
#
# # inflows = pd.read_csv(input_folder + source_folder + 'Inflows.csv', index_col = 0)
#
#
#
# aa = pd.DataFrame(columns=scenarios)
# bb = pd.DataFrame(columns=scenarios)
# for s in scenarios:
#     aa[s] = r[s]['WaterConsumptionData']['ZoneLevel']['WaterConsumption'].sum()
#     bb[s] = r[s]['WaterConsumptionData']['ZoneLevel']['WaterWithdrawal'].sum()
#
# import geopandas as gpd
#
# fp = input_folder + source_folder + 'Africa.shp'
# map_df = gpd.read_file(fp)
# # check the GeoDataframe
# map_df.head()
#
# temba_inputs = pd.read_csv(input_folder + source_folder + 'TEMBA_Results.csv', header=0, index_col=0)
#
# temba_fuels = {'Biomass': 'BIO', 'Biomass with ccs': 'BIO',
#                'Coal': 'HRD', 'Coal with ccs': 'HRD',
#                'Gas': 'GAS', 'Gas with ccs': 'GAS',
#                'Geothermal': 'GEO',
#                'Hydro': 'WAT',
#                'Nuclear': 'NUC',
#                'Oil': 'OIL',
#                'Solar CSP': 'SUN', 'Solar PV': 'SUN',
#                'Wind': 'WIN'}
#
# temba_techs = {'Biomass': 'STUR', 'Biomass with ccs': 'STUR',
#                'Coal': 'STUR', 'Coal with ccs': 'STUR',
#                'Gas': 'COMC', 'Gas with ccs': 'COMC',
#                'Geothermal': 'STUR',
#                'Hydro': 'WAT',
#                'Nuclear': 'STUR',
#                'Oil': 'ICEN',
#                'Solar CSP': 'STUR', 'Solar PV': 'PHOT',
#                'Wind': 'WTON'}
#
# temba_inputs['Fuel'] = temba_inputs['variable']
# temba_inputs['Technology'] = temba_inputs['variable']
# temba_inputs['Fuel'] = temba_inputs['Fuel'].replace(temba_fuels)
# temba_inputs['Technology'] = temba_inputs['Technology'].replace(temba_techs)
#
# scenario = '1.5deg'
# aa = temba_inputs.loc[(temba_inputs['parameter'] == 'Power Generation (Aggregate)') &
#                       (temba_inputs['scenario'] == scenario) &
#                       (temba_inputs['country'].isin(zones))]
#
# df1 = pd.pivot_table(aa, index=['Fuel'], values=['2025', '2035', '2045'], aggfunc=np.sum)
# df1.to_clipboard(sep=',')
#
# bb = get_generation_indicators(results, zones)
# bb.to_clipboard(sep=',')
#
# scenario = '1.5deg'
# cc = temba_inputs.loc[(temba_inputs['parameter'] == 'Water consumption aggregated') &
#                       (temba_inputs['scenario'] == scenario) &
#                       (temba_inputs['country'].isin(zones))]
#
# cc = cc.loc[cc['Fuel'].isin(commons['Fuels'])]
# df2 = pd.pivot_table(cc, index=['Fuel'], values=['2025', '2035', '2045'], aggfunc=np.sum)
# df2.to_clipboard(sep=',')
#
# scenario = 'Reference'
# cc = temba_inputs.loc[(temba_inputs['parameter'] == 'Water Withdrawal') &
#                       (temba_inputs['scenario'] == scenario) &
#                       (temba_inputs['country'].isin(zones))]
#
# cc = cc.loc[cc['Fuel'].isin(commons['Fuels'])]
# df2 = pd.pivot_table(cc, index=['Fuel'], values=['2025', '2035', '2045'], aggfunc=np.sum)
# df2.to_clipboard(sep=',')

zones = [['BI', 'DJ', 'EG', 'ET', 'ER', 'KE', 'RW', 'SO', 'SD', 'SS', 'TZ', 'UG'],
         ['DZ', 'LY', 'MA', 'MR', 'TN'],
         ['CM', 'CF', 'CD', 'CG', 'GA', 'GQ', 'TD'],
         ['AO', 'BW', 'LS', 'MW', 'MZ', 'NA', 'SZ', 'ZA', 'ZM', 'ZW'],
         ['BF', 'BJ', 'CI', 'GH', 'GM', 'GN', 'GW', 'LR', 'ML', 'NE', 'NG', 'SL', 'SN', 'TG'],
         ['BI', 'DJ', 'EG', 'ET', 'ER', 'KE', 'RW', 'SO', 'SD', 'SS', 'TZ', 'UG',
          'DZ', 'LY', 'MA', 'MR', 'TN',
          'CM', 'CF', 'CD', 'CG', 'GA', 'GQ', 'TD',
          'AO', 'BW', 'LS', 'MW', 'MZ', 'NA', 'SZ', 'ZA', 'ZM', 'ZW',
          'BF', 'BJ', 'CI', 'GH', 'GM', 'GN', 'GW', 'LR', 'ML', 'NE', 'NG', 'SL', 'SN', 'TG']
         ]
fuels = ['BIO', 'HRD', 'WAT', 'WIN', 'SUN', 'NUC', 'PEA', 'OIL', 'GAS', 'GEO']
# aa = inputs['1980']['units'].loc[(inputs['1980']['units']['Zone'].isin(zones[0])) & (inputs['1980']['units']['Fuel'].isin(fuels)), 'PowerCapacity'].sum()

techs_stor = ['HDAM', 'HPHS', 'SCSP']
techs = ['COMC', 'GTUR', 'HDAM', 'HROR', 'HPHS', 'ICEN', 'PHOT', 'STUR', 'WTOF', 'WTON', 'CAES',
         'BATS', 'BEVS', 'THMS', 'P2GS', 'P2HT', 'SCSP', 'COMC_CCS']

aa = pd.DataFrame()
bb = pd.DataFrame()
cc = pd.DataFrame()
dd = pd.DataFrame()
generation = {}
co2 = {}
co2_int = {}
gen = {}
cost = {}
cost_spec = {}
consumption = {}
withdrawal = {}
consumption_int = {}
withdrawal_int = {}
consumption_tot = {}
withdrawal_tot = {}
curtailment = pd.DataFrame()
shedload = pd.DataFrame()
demand = pd.DataFrame()
stor_level = {}
capacity = pd.DataFrame()

i = 0
for z in zones:
    if i == 0:
        row = 'EAPP'
    elif i == 1:
        row = 'NAPP'
    elif i == 2:
        row = 'CAPP'
    elif i == 3:
        row = 'SAPP'
    elif i == 4:
        row = 'WAPP'
    elif i == 5:
        row = 'Africa'

    # for f in fuels:
    #     tmp = inputs['1980']['units'].loc[(inputs['1980']['units']['Zone'].isin(z)) & (inputs['1980']['units']['Fuel'].isin([f]))].copy()
    #     tmp['Total'] = tmp['PowerCapacity'] * tmp['Nunits']
    #     aa.loc[row, f] = tmp['Total'].sum()
    # for s in techs_stor:
    #     tmp = inputs['1980']['units'].loc[(inputs['1980']['units']['Zone'].isin(z)) & (inputs['1980']['units']['Technology'].isin([s]))].copy()
    #     cc.loc[row, s] = tmp['StorageCapacity'].sum()

    co2[row] = pd.DataFrame()
    gen[row] = pd.DataFrame()
    cost[row] = pd.DataFrame()
    consumption[row] = pd.DataFrame()
    withdrawal[row] = pd.DataFrame()
    stor_level[row] = pd.DataFrame()
    N = 24 * 7

    for y in range(1980, 2019, 1):
        tmp_stor = results[str(y)]['OutputStorageLevel'].loc[:,inputs[str(y)]['units']['Zone'].isin(z)] * inputs[str(y)]['units'].loc[inputs[str(y)]['units']['Zone'].isin(z),'StorageCapacity'].dropna()
        tmp_stor = tmp_stor.reset_index()
        stor_level[row].loc[:,y] = tmp_stor.sum(axis=1)
        tmp_bb = inputs[str(y)]['param_df']['StorageInflow'].loc[:, inputs['1980']['units']['Zone'].isin(z)]
        tmp_bb2 = inputs[str(y)]['param_df']['AvailabilityFactor'].loc[:, (inputs['1980']['units']['Zone'].isin(z)) &
                                                                          (inputs['1980']['units'][
                                                                               'Technology'] == 'HROR')] * \
                  inputs[str(y)]['units'].loc[(inputs['1980']['units']['Zone'].isin(z)) &
                                              (inputs['1980']['units']['Technology'] == 'HROR')]['PowerCapacity']
        bb.loc[row, y] = (tmp_bb.sum().sum() + tmp_bb2.sum().sum()) / 8760

        curtailment.loc[y, row] = r[str(y)]['ZoneData']['Curtailment'].loc[
            r[str(y)]['ZoneData']['Curtailment'].index.isin(z)].sum()
        shedload.loc[y, row] = r[str(y)]['ZoneData']['LoadShedding'].loc[
            r[str(y)]['ZoneData']['LoadShedding'].index.isin(z)].sum()
        demand.loc[y, row] = r[str(y)]['ZoneData']['Demand'].loc[
            r[str(y)]['ZoneData']['Demand'].index.isin(z)].sum()
        for f in fuels:
            tmp_co2 = r[str(y)]['UnitData'].loc[
                (inputs[str(y)]['units']['Zone'].isin(z)) & (inputs[str(y)]['units']['Fuel'].isin([f]))]
            co2[row].loc[f, y] = tmp_co2['CO2 [t]'].sum()
            gen[row].loc[f, y] = tmp_co2['Generation [TWh]'].sum()
            cost[row].loc[f, y] = tmp_co2['Total Costs [EUR]'].sum()
            consumption[row].loc[f, y] = tmp_co2['WaterConsumption'].sum()
            withdrawal[row].loc[f, y] = tmp_co2['WaterWithdrawal'].sum()
        cost[row].loc['ShedLoad', y] = 800 * results[str(y)]['OutputShedLoad'].loc[:,results[str(y)]['OutputShedLoad'].columns.isin(z)].sum().sum()

    co2[row] = co2[row][(co2[row].T != 0).any()]
    gen[row] = gen[row][(gen[row].T != 0).any()] * 1e6
    cost[row] = cost[row][(cost[row].T != 0).any()]
    consumption[row] = consumption[row][(consumption[row].T != 0).any()]
    withdrawal[row] = withdrawal[row][(withdrawal[row].T != 0).any()]

    co2_int[row] = co2[row].sum() / gen[row].sum() * 1000
    cost_spec[row] = cost[row].sum() / gen[row].sum()

    consumption_int[row] = consumption[row].drop('WAT').sum() / gen[row].sum()
    withdrawal_int[row] = withdrawal[row].drop('WAT').sum() / gen[row].sum()

    consumption_tot[row] = consumption[row].sum() / gen[row].sum()
    withdrawal_tot[row] = withdrawal[row].sum() / gen[row].sum()


    stor_level[row] = stor_level[row].groupby(stor_level[row].index // N).mean()

    for f in fuels:
        tmp = inputs['1980']['units'].loc[(inputs['1980']['units']['Fuel']==f) &
                                                          (inputs['1980']['units']['Zone'].isin(z))]
        if tmp.empty:
            capacity.loc[row, f] = 0
        else:
            tmp['TotCap'] = tmp['PowerCapacity'] * tmp['Nunits']
            capacity.loc[row, f] = tmp['TotCap'].sum()
    # generation[row] = {}
    # for f in fuels:
    #     generation[row][f] = pd.DataFrame()
    #     for t in techs:
    #         for y in range(1980,2019,1):
    #             tmp_gen = results[str(y)]['OutputPower'].loc[:,(inputs[str(y)]['units']['Zone'].isin(z)) & (inputs[str(y)]['units']['Technology'].isin([t])) & (inputs[str(y)]['units']['Fuel'].isin([f]))]
    #             generation[row][f].loc[t,y] = tmp_gen.sum().sum()
    #     generation[row][f] = generation[row][f][(generation[row][f].T != 0).any()]
    # generation[row] = dict([(k, v) for k, v in generation[row].items() if len(v) > 0])
    #
    # for t in techs:
    #     tmp = inputs['1980']['units'].loc[(inputs['1980']['units']['Zone'].isin(z)) & (inputs['1980']['units']['Technology'].isin([t]))].copy()
    #     tmp['Total'] = tmp['PowerCapacity'] * tmp['Nunits']
    #     dd.loc[row, t] = tmp['Total'].sum()
    # Storage levels



    i = i + 1

bb = bb.T

# Congestions
congestion = pd.DataFrame()
pp_conection = {'2025': {'CAPP -> EAPP':['CD -> BI', 'CD -> RW', 'CD -> SS', 'CD -> TZ', 'CD -> UG'],
                         'EAPP -> CAPP':['BI -> CD', 'RW -> CD', 'SS -> CD', 'TZ -> CD', 'UG -> CD'],
                         'CAPP -> SAPP':['CD -> AO', 'CD -> ZM'],
                         'SAPP -> CAPP':['AO -> CD', 'ZM -> CD'],
                         'CAPP -> WAPP':['CM -> NG'],
                         'WAPP -> CAPP':['NG -> CM'],
                         'EAPP -> NAPP':['EG -> LY'],
                         'NAPP -> EAPP':['LY -> EG'],
                         'EAPP -> SAPP':['TZ -> ZM', 'TZ -> MZ', 'TZ -> MW'],
                         'SAPP -> EAPP':['ZM -> TZ', 'MZ -> TZ', 'MW -> TZ'],
                         'NAPP -> WAPP':['MR -> SN', 'MR -> ML'],
                         'WAPP -> NAPP':['SN -> MR', 'ML -> MR']},
                '2018': {'CAPP -> EAPP':['CD -> BI', 'CD -> RW'],
                         'EAPP -> CAPP':['BI -> CD', 'RW -> CD'],
                         'CAPP -> SAPP':['CD -> AO', 'CD -> ZM'],
                         'SAPP -> CAPP':['AO -> CD', 'ZM -> CD'],
                         'EAPP -> NAPP':['EG -> LY'],
                         'NAPP -> EAPP':['LY -> EG'],
                         'EAPP -> SAPP':['TZ -> ZM'],
                         'SAPP -> EAPP':['ZM -> TZ'],
                         'NAPP -> WAPP':['MR -> SN'],
                         'WAPP -> NAPP':['SN -> MR']},
                }

yr = '2025'

congestion_i = pd.DataFrame()
congestion_e = pd.DataFrame()
for c in pp_conection[yr]:
    for y in range(1980, 2019, 1):
        tmp = pd.DataFrame()
        for j in pp_conection[yr][c]:
            # tmp = results[str(y)]['OutputFlow']
            if j in r[str(y)]['Congestion']:
                tmp.loc[c,j] = r[str(y)]['Congestion'][j]

        if tmp.empty:
            congestion.loc[y, c] = 0
        else:
            tmp2 = tmp.sum(axis = 1)/len(tmp.columns)
            congestion.loc[y, c] = tmp2.values[0]

# Flows between Power Pools

def get_imports(flows, z):
    """
    Function that computes the balance of the imports/exports of a given zone

    :param flows:           Pandas dataframe with the timeseries of the exchanges
    :param z:               Zone to consider
    :returns NetImports:    Scalar with the net balance over the whole time period
    """
    NetImports = 0
    Imports = 0
    Exports = 0
    for key in flows:
        if key[:len(z)] == z:
            NetImports -= flows[key]
            Imports += flows[key]
        elif key[-len(z):] == z:
            NetImports += flows[key]
            Exports += flows[key]
    return NetImports, Imports, Exports

flow = {}
flow_grouped = {}
imports_z = {}
exports_z = {}
net_imports_z = {}
imports_grouped_z = {}
exports_grouped_z = {}
net_imports_grouped_z = {}
N = 24*7
for y in range(1980, 2019, 1):
    flow[y] = pd.DataFrame()
    imports_z[y] = pd.DataFrame()
    exports_z[y] = pd.DataFrame()
    net_imports_z[y] = pd.DataFrame()
    imports_grouped_z[y] = pd.DataFrame()
    exports_grouped_z[y] = pd.DataFrame()
    net_imports_grouped_z[y] = pd.DataFrame()
    for c in pp_conection[yr]:
        tmp_h = pd.DataFrame()
        for j in pp_conection[yr][c]:
            if j in results[str(y)]['OutputFlow'].columns:
                tmp_h.loc[:,j] = results[str(y)]['OutputFlow'].loc[:,j]
        if tmp_h.empty:
            flow[y].loc[:, c] = pd.DataFrame(0,index=results[str(y)]['OutputFlow'].index,columns=[c])
        else:
            flow[y].loc[:,c] = tmp_h.sum(axis=1)
    flow_grouped[y] = flow[y].copy()
    flow_grouped[y].reset_index(inplace=True)
    flow_grouped[y] = flow_grouped[y].groupby(flow_grouped[y].index // N).sum()
    for p in ['CAPP', 'EAPP', 'NAPP', 'SAPP', 'WAPP']:
        # tmp_net, tmp_i, tmp_e = get_imports(flow[y], p)
        net_imports_z[y].loc[:,p], imports_z[y].loc[:,p], exports_z[y].loc[:,p] = get_imports(flow[y], p)
        net_imports_grouped_z[y].loc[:, p], imports_grouped_z[y].loc[:, p], exports_grouped_z[y].loc[:, p] = get_imports(flow_grouped[y], p)

pp_net_imports = {}

for p in ['CAPP', 'EAPP', 'NAPP', 'SAPP', 'WAPP']:
    pp_net_imports[p] = pd.DataFrame()
    for y in range(1980, 2019, 1):
        pp_net_imports[p].loc[:,y] = net_imports_grouped_z[y].loc[:,p]
    pp_net_imports[p] = pp_net_imports[p] / 1e3
    pp_net_imports[p]['Count_+'] = pp_net_imports[p].gt(0).sum(axis=1)
    pp_net_imports[p]['Count_-'] = pp_net_imports[p].lt(0).sum(axis=1)
    pp_net_imports[p]['Avg'] = pp_net_imports[p].mean(axis=1)
    pp_net_imports[p]['Min'] = pp_net_imports[p].min(axis=1)
    pp_net_imports[p]['Max'] = pp_net_imports[p].max(axis=1)

tot_consumption = {}
tot_withdrawal = {}
tot_withdrawal_old = {}
tot_consumption_int = pd.DataFrame()
tot_withdrawal_int = pd.DataFrame()
tot_consumption_tot = pd.DataFrame()
tot_withdrawal_tot = pd.DataFrame()

tot_withdrawal_int_old = pd.DataFrame()
tot_withdrawal_tot_old = pd.DataFrame()

WW_correction = pd.read_csv('Water_Withdrawal_Correction.csv', index_col=0)

for z in zones[5]:
    tot_consumption[z] = pd.DataFrame()
    tot_withdrawal[z] = pd.DataFrame()
    tot_withdrawal_old[z] = pd.DataFrame()
    for y in range(1980,2019,1):
        for f in fuels:
            tmp_wc = r[str(y)]['UnitData'].loc[
                (inputs[str(y)]['units']['Zone'].isin([z])) & (inputs[str(y)]['units']['Fuel'].isin([f]))]
            tot_consumption[z].loc[f, y] = tmp_wc['WaterConsumption'].sum()
            tmp_ww = tmp_wc.copy()
            if tmp_ww.empty:
                continue
            else:
                tmp_ww.loc[:,'WaterWithdrawal_Old'] = tmp_wc['WaterWithdrawal']
            if f == 'WAT':
                tmp_ww.loc[:,'Nunits'] = WW_correction.loc[inputs[str(y)]['units']['Zone'].isin([z])]['Nunits']
                tmp_ww.loc[:,'Units'] = WW_correction.loc[inputs[str(y)]['units']['Zone'].isin([z])]['Alpha']
                tmp_ww.loc[:,'WaterWithdrawal_Old'] = tmp_ww.loc[:,'WaterWithdrawal']
                tmp_ww.loc[:,'WaterWithdrawal'] = tmp_ww['WaterWithdrawal_Old']/tmp_ww['Nunits']*tmp_ww['Units']
            tot_withdrawal[z].loc[f, y] = tmp_ww['WaterWithdrawal'].sum()
            if tmp_ww.empty:
                continue
            else:
                tot_withdrawal_old[z].loc[f,y] = tmp_ww['WaterWithdrawal_Old'].sum()

    tot_consumption[z] = tot_consumption[z][(tot_consumption[z].T != 0).any()]
    tot_withdrawal[z] = tot_withdrawal[z][(tot_withdrawal[z].T != 0).any()]
    if 'WAT' in tot_consumption[z].index:
        tot_consumption_int.loc[:,z] = tot_consumption[z].drop('WAT').sum().T /1e9
        tot_withdrawal_int.loc[:,z] = tot_withdrawal[z].drop('WAT').sum().T /1e9
        tot_withdrawal_int_old.loc[:, z] = tot_withdrawal_old[z].drop('WAT').sum().T / 1e9
    else:
        tot_consumption_int.loc[:,z] = tot_consumption[z].sum().T /1e9
        tot_withdrawal_int.loc[:,z] = tot_withdrawal[z].sum().T /1e9
        tot_withdrawal_int_old.loc[:, z] = tot_withdrawal_old[z].sum().T / 1e9

    tot_consumption_tot.loc[:,z] = tot_consumption[z].sum().T /1e9
    tot_withdrawal_tot.loc[:,z] = tot_withdrawal[z].sum().T / 1e9
    tot_withdrawal_tot_old.loc[:, z] = tot_withdrawal_old[z].sum().T / 1e9
    # tot_consumption_int.columns = zones[5]
