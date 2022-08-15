"""
This script generates the country time series for Dispa-SET
Input : EnergyScope database
Output : Database/Heat_demand/##/... .csv

@authors:
                Matija Pavičević, KU Leuven
                Paolo Thiran, UCLouvain
@contributors:
                Damon Coates, UCLouvain
                Guillaume Percy, UCLouvain
@supervision:
                Sylvain Quoilin, KU Leuven, ULiege
"""
from __future__ import division

import pandas as pd

from ..search import *
from ..common import *
from ..constants import *


def get_electricity_demand(es_outputs, td_df, drange, countries=['ES'], write_csv=True, file_name='Load'):
    """
    Compute electricity demand and convert it to dispaset readable format, i.e. csv time series
    :param es_outputs:  EnergyScope outputs
    :param td_df:       Typical day dataframe
    :param drange:      Date range
    :param countries:   Countries to apply the mapping function on
    :param write_csv:   Bool for creating csv file True/False
    :param file_name:   Name of the csv file
    :return:            Electricity demand
    """

    # Create final dataframe
    electricity = pd.DataFrame(index=drange, columns=countries)

    for country in countries:
        # %% read base and variable loads
        el_demand_baseload = es_outputs['demands'].loc[0, 'HOUSEHOLDS'] + es_outputs['demands'].loc[0, 'SERVICES'] + \
                             es_outputs['demands'].loc[0, 'INDUSTRY']
        el_demand_variable = es_outputs['demands'].loc[1, 'HOUSEHOLDS'] + es_outputs['demands'].loc[1, 'SERVICES'] + \
                             es_outputs['demands'].loc[1, 'INDUSTRY']
        total_load_value = pd.DataFrame(es_outputs['timeseries'].loc[:, 'Electricity (%_elec)'] * el_demand_variable +
                                        el_demand_baseload / len(es_outputs['timeseries']))
        total_load_value.set_index(drange, inplace=True)
        # %% Compute the potential extra demand
        extra_elec_demand = 0
        extra_demand_tech = list()
        for y in elec_mobi_tech:
            elec = search_year_balance(es_outputs['year_balance'], y, 'ELECTRICITY')  # TO CHECK
            if elec != 0:
                extra_demand_tech.append(y)
                extra_elec_demand = extra_elec_demand - elec  # [GWh]

        # %% Consider grid losses
        grid_losses = grid_losses_list[countries.index(country)]
        factor = (search_year_balance(es_outputs['year_balance'], 'END_USES_DEMAND', 'ELECTRICITY') -
                  extra_elec_demand * grid_losses) / (total_load_value.sum())
        # Increase total load by grid losses
        total_load_value = total_load_value.multiply(factor) * 1000
        total_load_value_es_input = assign_td(es_outputs['electricity_layers'], td_df) * 1000  # GW to MW
        # Add all the electricity demands into a single one and assign proper date range
        total_load_value_es_input['Sum'] = -total_load_value_es_input.sum(axis=1)
        total_load_value_es_input = total_load_value_es_input.set_index(drange)
        electricity[country] = total_load_value.values + total_load_value_es_input['Sum'].multiply(
            1 + grid_losses).values

    if write_csv:
        write_csv_files(file_name, electricity, 'TotalLoadValue', index=True, write_csv=True)

    return electricity


def get_heat_demand(es_outputs, td_df, drange, countries=None, write_csv=True, file_name='HeatDemand',
                    dispaset_version='2.5'):
    """
    Mapping function for heat demands
    :param es_outputs:  Energyscope outputs
    :param td_df:       Typical days dataframe
    :param countries:   Zones to be selected for mapping
    :param write_csv:   Bool that triggers writing csv files True/False
    :param file_name:   Name of the csv file
    :return:            Heat Demand timeseries
    """

    for country in countries:
        # %% assign typical days and convert to hourly timeseries
        ind_heat_es_input = assign_td(es_outputs['high_t_Layers'], td_df) * 1000  # GW to MW
        dhn_heat_es_input = assign_td(es_outputs['low_t_dhn_Layers'], td_df) * 1000  # GW to MW
        decen_heat_es_input = assign_td(es_outputs['low_t_decen_Layers'], td_df) * 1000  # GW to MW

        # %% sum all technologies of same layer
        # ind_heat_es = ind_heat_es_input[ind_heat_tech].sum(axis=1)
        # dhn_heat_es = dhn_heat_es_input[dhn_heat_tech].sum(axis=1)
        # decen_heat_es = decen_heat_es_input[decen_heat_tech].sum(axis=1)

        ind_heat_es = -ind_heat_es_input.loc[:, 'END_USE']
        dhn_heat_es = -dhn_heat_es_input.loc[:, 'END_USE']
        decen_heat_es = -decen_heat_es_input.loc[:, 'END_USE']

        # %% create a dataframe
        heat_es_input = pd.DataFrame()
        heat_es_input.loc[:, country + '_IND'] = ind_heat_es
        heat_es_input.loc[:, country + '_DHN'] = dhn_heat_es
        heat_es_input.loc[:, country + '_DEC'] = decen_heat_es
        heat_es_input.set_index(drange, inplace=True)

    # %% export to csv file
    if write_csv:
        write_csv_files(file_name, heat_es_input, 'HeatDemand', index=True, write_csv=True, heating=True)

    return heat_es_input


def get_h2_demand(h2_layer, td_df, drange, write_csv=True, file_name='H2_demand', dispaset_version='2.5'):
    """
    Get h2 demand from ES and convert it into DS demand timeseries
    :param h2_layer:    H2 inputs layer
    :param td_df:       typical day assignment
    :param write_csv:   write csv files
    :return:            h2 demand timeseries
    """
    h2_layer = clean_blanks(h2_layer, idx=False)
    if any(item in ['H2_STORAGE_Pin', 'H2_STORAGE_Pout'] for item in h2_layer.columns):
        h2_layer.drop(columns=['H2_STORAGE_Pin', 'H2_STORAGE_Pout'], inplace=True)
    # computing consumption of H2
    # TODO automatise name zone assignment
    h2_td = pd.DataFrame(-h2_layer[h2_layer < 0].sum(axis=1), columns=['ES_H2'])
    h2_ts = assign_td(h2_td, td_df) * 1000  # Convert to MW
    h2_ts.set_index(drange, inplace=True)
    if dispaset_version == '2.5':
        h2_max_demand = pd.DataFrame(h2_ts.max(), columns=['Capacity'])
    if write_csv:
        write_csv_files(file_name, h2_ts, 'H2_demand', index=True, write_csv=True)
        if dispaset_version == '2.5':
            write_csv_files('PtLCapacities', h2_max_demand, 'H2_demand', index=True, write_csv=True)
    return h2_ts


def get_outage_factors(config_es, es_outputs, local_res, td_df, drange, write_csv=True):
    """
    Assign outage factors for technologies that generate more than available
    :param config_es:   EnergyScope config file
    :param es_outputs:  Energy scope outputs
    :param local_res:   Resources to compute outages
    :param td_df:       Typical day dataframe
    :return:            Outage factors
    """
    outage_factors = compute_outage_factor(config_es, es_outputs['assets'], local_res[0])
    for r in local_res[1:]:
        outage_factors = outage_factors.merge(compute_outage_factor(config_es, es_outputs['assets'], r),
                                              left_index=True, right_index=True)

    outage_factors_yr = td_df.loc[:, ['TD', 'hour']]
    outage_factors_yr = outage_factors_yr.merge(outage_factors, left_on=['TD', 'hour'], right_index=True).sort_index()
    outage_factors_yr.drop(columns=['TD', 'hour'], inplace=True)
    outage_factors_yr.rename(columns=lambda x: 'ES_' + x, inplace=True)
    outage_factors_yr.set_index(drange, inplace=True)
    if write_csv:
        write_csv_files('OutageFactor', outage_factors_yr, 'OutageFactor', index=True, write_csv=True)
    return outage_factors_yr


def get_soc(es_outputs, config_es, drange, sto_size_min=0.01, countries=None, write_csv=True,
            file_name='ReservoirLevels'):
    """
    Compute the state of the charge of storage technologies
    :param es_outputs:      EnergyScope outputs
    :param config_es:       EnergyScope config file
    :param drange:          Date range
    :param sto_size_min:    Minimum storage size to be considered
    :param countries:       Countries to iterate over
    :param write_csv:       Bool for writing csv files True/False
    :param file_name:       Name of the csv file
    :return:                State of the charge
    """

    # TODO: make generic for any country
    sto_size = es_outputs['assets'].loc[config_es['all_data']['Storage_eff_in'].index, 'f']
    sto_size = sto_size[sto_size >= sto_size_min]
    soc = es_outputs['energy_stored'].loc[:, sto_size.index] / sto_size
    soc.rename(columns=lambda x: 'ES_' + x, inplace=True)
    soc.set_index(drange, inplace=True)

    if write_csv:
        write_csv_files(file_name, soc, 'ReservoirLevels', index=True, write_csv=True)
    return soc


def get_availability_factors(es_outputs, drange, countries=['ES'], write_csv=True, file_name_af='AvailabilityFactors',
                             file_name_sif='ScaledInFlows'):
    """
    Get availability factors from Energy Scope and covert them to Dispa-SET readable format
    :param es_outputs:      EnergyScope outputs
    :param config_es:       EnergyScope config file
    :param drange:          Date range
    :param countries:       Countries to iterate over
    :param write_csv:       Bool for writing csv files True/False
    :param file_name_af:    Name of the availability factor csv file
    :param file_name_sif:   Name of the scaled inflows csv file
    :return:                RES time-series
    """

    # %% Create data structures
    res_timeseries = {}
    inflow_timeseries = {}

    for country in countries:
        # %% Fix input files
        es_outputs['timeseries'].set_index(drange, inplace=True)
        af_es_df = es_outputs['timeseries'].loc[:, ['PV', 'Wind_onshore', 'Wind_offshore', 'Hydro_river']]

        # %% Compute availability factors
        availability_factors_ds = []
        for i in af_es_df:
            if i in mapping['TECH']:
                availability_factors_ds.append(mapping['TECH'][i])
        availability_factors_ds_df = af_es_df.set_axis(availability_factors_ds, axis=1, inplace=False)
        for i in availability_factors_ds:
            availability_factors_ds_df.loc[availability_factors_ds_df[i] < 0, i] = 0
            availability_factors_ds_df.loc[availability_factors_ds_df[i] > 1, i] = 1
        res_timeseries[country] = availability_factors_ds_df

        # %% Compute scaled inflows, if present
        try:
            inflows_ds = []
            inflows_es_df = es_outputs['timeseries'].loc[:, ['Hydro_dam']]
            for i in inflows_es_df:
                if i in mapping['TECH']:
                    inflows_ds.append(mapping['TECH'][i])
            inflow_timeseries[country] = inflows_es_df.set_axis(inflows_ds, axis=1)
        except:
            logging.error('Hydro_dam time-series not present in ES')

        # %% Export to csv
        if write_csv:
            write_csv_files(file_name_af, res_timeseries[country], 'AvailabilityFactors', index=True, write_csv=True,
                            country=country)
            if inflow_timeseries:
                write_csv_files(file_name_sif, inflow_timeseries[country], 'ScaledInFlows', index=True, write_csv=True,
                                country=country, inflows=True)

    return res_timeseries
