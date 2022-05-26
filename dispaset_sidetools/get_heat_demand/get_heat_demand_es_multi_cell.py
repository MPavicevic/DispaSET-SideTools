"""
This script generates the country Heat End-use Demand time series for Dispa-SET
Input : EnergyScope database
Output : Database/Heat_demand/##/... .csv

@authors: Matija Pavičević, KU Leuven
          Sylvain Quoilin, KU Leuven
          Damon Coates, UCLouvain
          Guillaume Percy, UCLouvain
"""

import sys, os

# sys.path.append(os.path.abspath(r'../..'))

# from dispaset_sidetools import *
import numpy as np
import pandas as pd
import math
import logging

# from dispaset_sidetools.common import *
from ..search import *
from ..constants import *
from ..common import *


def get_heat_demand_from_es(config_es, countries = ['ES'], separator = ';'):

    # separator = ';'

    # countries = ['ES']

    # ES_folder = '../../../EnergyScope/'
    ES_folder = config_es['ES_folder']
    ES_output = ES_folder / 'case_studies' / config_es['case_study'] / 'output'

    # Enter the starting date
    start = pd.to_datetime(date_str)
    drange = pd.date_range(start, periods=hourly_periods, freq='H')

    EUD_heat = {}

    for x in countries:
        # perc_dhn = perc_dhn_list[countries.index(x)]
        DHN_Sto_losses = DHN_Sto_losses_list[countries.index(x)]

        # Input file
        timeseries = pd.read_csv(config_es['data_folder']/'Time_series.csv', header=0, sep=separator)
        demands = pd.read_csv(config_es['data_folder']/'Demand.csv', sep=separator)
        yearbal = pd.read_csv(ES_output/'year_balance.txt', delimiter='\t', index_col='Tech')

        heat_demand = demands.loc[3, 'HOUSEHOLDS'] + demands.loc[3, 'SERVICES'] + demands.loc[3, 'INDUSTRY']
        Heat = pd.DataFrame(timeseries.loc[:, 'Space Heating (%_sh)'] * heat_demand)
        Heat.set_index(drange, inplace=True)

        ind_heat_ESinput = pd.DataFrame(index=range(0, 8760), columns=ind_heat_tech)
        dhn_heat_ESinput = pd.DataFrame(index=range(0, 8760), columns=dhn_heat_tech)
        decen_heat_ESinput = pd.DataFrame(index=range(0, 8760), columns=decen_heat_tech)

        high_t_Layers = pd.read_csv(ES_output/'hourly_data/layer_HEAT_HIGH_T.txt', delimiter='\t')
        low_t_decen_Layers = pd.read_csv(ES_output/'hourly_data/layer_HEAT_LOW_T_DECEN.txt',
                                         delimiter='\t')
        low_t_dhn_Layers = pd.read_csv(ES_output/'hourly_data/layer_HEAT_LOW_T_DHN.txt', delimiter='\t')
        td_final = pd.read_csv(config_es['step1_output'], header=None)
        TD_DF = process_TD(td_final)

        ind_vals = ([day, h] for day in range(1, 366) for h in range(1, 25))
        for day, h in ind_vals:
            thistd = get_TD(TD_DF, (day - 1) * 24 + h, n_TD)
            ind_heat_ESinput.loc[(day - 1) * 24 + h - 1, :] = search_HeatLayers(high_t_Layers, thistd, h) * 1000
            dhn_heat_ESinput.loc[(day - 1) * 24 + h - 1, :] = search_HeatLayers(low_t_dhn_Layers, thistd, h) * 1000
            decen_heat_ESinput.loc[(day - 1) * 24 + h - 1, :] = search_HeatLayers(low_t_decen_Layers, thistd, h) * 1000

        dhn_sto_losses = abs(dhn_heat_ESinput['TS_DHN_SEASONAL_Pin'].sum()) * DHN_Sto_losses

        ind_heat_ES = ind_heat_ESinput[ind_heat_tech].sum(axis=1)
        dhn_heat_ES = dhn_heat_ESinput[dhn_heat_tech].sum(axis=1)
        decen_heat_ES = decen_heat_ESinput[decen_heat_tech].sum(axis=1)

        # Compute ratio_dhn_prod_losses
        # dhn_sto_losses = Distri_TS['TS_DHN_SEASONAL'].sum() * DHN_Sto_losses
        prod_dhn = 0
        for i in dhn_tech:
            prod_dhn = prod_dhn + search_YearBalance(yearbal, i, 'HEAT_LOW_T_DHN')
        losses_dhn = dhn_heat_ES.sum() * 0.05 / 1000
        ratio_dhn_prod_losses = (prod_dhn - losses_dhn - dhn_sto_losses) / dhn_heat_ES.sum()

        heat_ESinput = pd.DataFrame()
        heat_ESinput.loc[:, x + '_IND'] = ind_heat_ES
        heat_ESinput.loc[:, x + '_DHN'] = dhn_heat_ES
        heat_ESinput.loc[:, x + '_DEC'] = decen_heat_ES

        heat_ESinput.set_index(drange, inplace=True)

        # heat_ESinput.loc[:, x + '_DEC'] = heat_ESinput[x + '_LT'].multiply(1 - perc_dhn)
        # heat_ESinput[x + '_DHN'] = heat_ESinput[x + '_LT'].multiply(perc_dhn) * ratio_dhn_prod_losses
        # heat_ESinput = heat_ESinput.drop([x + '_LT'], axis=1)
        # heat_ESinput[x + '_IND'] = heat_ESinput[x + '_HT']
        # heat_ESinput = heat_ESinput.drop([x + '_HT'], axis=1)
        # heat_ESinput = heat_ESinput.set_index(drange)
        #
        # EUD_heat.loc[x] = heat_ESinput

    write_csv_files('2015_ES_th', heat_ESinput, 'HeatDemand', index=True, write_csv=True, heating=True)

    return heat_ESinput
