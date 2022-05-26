# -*- coding: utf-8 -*-
"""
This script generates the country Electricity End-use Demand time series for Dispa-SET
Input : EnergyScope database
Output : Database/TotalLoadValue/##/... .csv

@authors: Matija Pavičević, KU Leuven
          Sylvain Quoilin, KU Leuven
          Damon Coates, UCLouvain
          Guillaume Percy, UCLouvain
"""
from __future__ import division

import logging
import os
import sys

# sys.path.append(os.path.abspath(r'../..'))

from ..search import *
from ..constants import *

def get_demand_from_es(config_es, countries=['ES'], separator=';'):

    # separator = ';'
    #
    # countries = ['ES']
    #
    # ES_folder = '../../../EnergyScope/'
    ES_folder = config_es['ES_folder']
    ES_output = ES_folder / 'case_studies' / config_es['case_study']/'output'

    ######################################################################################################

    # Enter the starting date
    start = pd.to_datetime(date_str)
    drange = pd.date_range(start, periods=hourly_periods, freq='H')

    # Create final dataframe
    EUD_elec = pd.DataFrame(index=drange, columns=countries)

    for x in countries:

        grid_losses = grid_losses_list[countries.index(x)]

        # input file
        timeseries = pd.read_csv(config_es['data_folder']/'Time_series.csv', header=0, sep=separator)
        demands = pd.read_csv(config_es['data_folder']/'Demand.csv', sep=separator)
        el_demand_baseload = demands.loc[0,'HOUSEHOLDS'] + demands.loc[0,'SERVICES'] + demands.loc[0,'INDUSTRY']
        el_demand_variable = demands.loc[1,'HOUSEHOLDS'] + demands.loc[1,'SERVICES'] + demands.loc[1,'INDUSTRY']
        yearbal = pd.read_csv(ES_output/'year_balance.txt', delimiter='\t', index_col='Tech')
        # TotalLoadValue = from_excel_to_dataFrame(input_folder + x + '/' + 'DATA_preprocessing.xlsx', 'EUD_elec')
        TotalLoadValue = pd.DataFrame(timeseries.loc[:,'Electricity (%_elec)'] * el_demand_variable +
                                      el_demand_baseload / len(timeseries))
        TotalLoadValue.set_index(drange, inplace=True)

        extra_elec_demand = 0
        extra_demand_tech = list()
        for y in (elec_mobi_tech):
            elec = search_YearBalance(yearbal, y, 'ELECTRICITY')  # TO CHECK
            if elec != 0:
                extra_demand_tech.append(y)
                extra_elec_demand = extra_elec_demand - elec  # [GWh]

        factor = (search_YearBalance(yearbal, 'END_USES_DEMAND', 'ELECTRICITY') - extra_elec_demand * grid_losses) / \
                 (TotalLoadValue.sum())

        TotalLoadValue = TotalLoadValue.multiply(factor) * 1000
        TotalLoadValue_ESinput = pd.DataFrame(index=range(0, 8760), columns=extra_demand_tech)

        ElecLayers = pd.read_csv(ES_output/'hourly_data/layer_ELECTRICITY.txt', delimiter='\t')
        td_final = pd.read_csv(config_es['step1_output'], header=None)
        TD_DF = process_TD(td_final)

        for day in range(1, 366):
            for h in range(1, 25):
                thistd = get_TD(TD_DF, (day - 1) * 24 + h, n_TD)
                for y in extra_demand_tech:
                    TotalLoadValue_ESinput.at[(day - 1) * 24 + h - 1, y] = search_ElecLayers(ElecLayers, thistd, h,
                                                                                             y) * 1000  # TO CHECK

        TotalLoadValue_ESinput['Sum'] = -TotalLoadValue_ESinput.sum(axis=1)
        TotalLoadValue_ESinput = TotalLoadValue_ESinput.set_index(drange)
        EUD_elec[x] = TotalLoadValue.values + TotalLoadValue_ESinput['Sum'].multiply(1 + grid_losses).values

    write_csv_files('2015_ES', EUD_elec, 'TotalLoadValue', index=True, write_csv=True)

    return EUD_elec