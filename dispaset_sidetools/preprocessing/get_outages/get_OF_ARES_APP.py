# -*- coding: utf-8 -*-
"""
This script generates the PowerPlant Dispa-SET data for the JRC-EU-TIMES runs

@authors: Matija Pavičević, KU Leuven
          Sylvain Quoilin, KU Leuven
"""
from __future__ import division

import pandas as pd

from ...common import date_range, get_ktoe_to_mwh


def get_outages(allunits, generation, capacity_factors, SOURCE, YEAR):
    # Annual generation in MWh
    generation = get_ktoe_to_mwh(generation, ['Biofuels', 'Fosil', 'Hydro', 'Geothermal', 'RES'])
    aa = pd.concat(allunits, ignore_index=True)
    bio_units = list(aa.loc[aa['Fuel'] == 'BIO']['Unit'])
    bio_data = aa.loc[aa['Fuel'] == 'BIO']

# Identify annual generation per zone and share of installed capacity
    for c in list(bio_data['Zone'].unique()):
        if c in list(generation.index):
            bio_data.loc[bio_data['Zone'] == c, 'Share'] = bio_data['PowerCapacity'].loc[bio_data['Zone'] == c] / \
                                                           bio_data['PowerCapacity'].loc[bio_data['Zone'] == c].sum()
            bio_data.loc[bio_data['Zone'] == c, 'Generation_Historic'] = generation['Biofuels'][c]
        else:
            bio_data.loc[bio_data['Zone'] == c, 'Generation_Historic'] = 0
    # Assign annual generation for each individual unit based on shares
    bio_data['Generation_Historic'] = bio_data['Generation_Historic'] * bio_data['Share']
    # Identify capacity factors
    bio_data['CF'] = bio_data['Generation_Historic'] / bio_data['PowerCapacity'] / 8760
    bio_data.set_index('Unit', inplace=True)

    ones_df_bio = pd.DataFrame(index=date_range('1/1/' + str(YEAR), '1/1/' + str(YEAR + 1), freq='H'),
                               columns=bio_units).fillna(1)
    if SOURCE == 'TEMBA':
        bio_outage = ones_df_bio - ones_df_bio * 0.8
    else:
        bio_outage = ones_df_bio - ones_df_bio * bio_data['CF']

    geo_units = list(aa.loc[aa['Fuel'] == 'GEO']['Unit'])
    geo_data = aa.loc[aa['Fuel'] == 'GEO']

    # Identify annual generation per zone and share of installed capacity
    for c in list(geo_data['Zone'].unique()):
        if c in list(generation.index):
            geo_data.loc[geo_data['Zone'] == c, 'Share'] = geo_data['PowerCapacity'].loc[geo_data['Zone'] == c] / \
                                                           geo_data['PowerCapacity'].loc[geo_data['Zone'] == c].sum()
            geo_data.loc[geo_data['Zone'] == c, 'Generation_Historic'] = generation['Geothermal'][c]
        else:
            geo_data.loc[geo_data['Zone'] == c, 'Generation_Historic'] = 0
    # Assign annual generation for each individual unit based on shares
    geo_data['Generation_Historic'] = geo_data['Generation_Historic'] * geo_data['Share']
    # Identify capacity factors
    geo_data['CF'] = geo_data['Generation_Historic'] / geo_data['PowerCapacity'] / 8760
    geo_data.set_index('Unit', inplace=True)

    ones_df_geo = pd.DataFrame(index=date_range('1/1/' + str(YEAR), '1/1/' + str(YEAR + 1), freq='H'),
                               columns=geo_units).fillna(1)
    if SOURCE == 'TEMBA':
        geo_outage = ones_df_geo - ones_df_geo * 0.65
    else:
        geo_outage = ones_df_geo - ones_df_geo * geo_data['CF']

# Identify zones where units are selected
    csp_units = list(aa.loc[(aa['Fuel'] == 'SUN') & (aa['Technology'] == 'STUR')]['Unit'])
    csp_data = aa.loc[(aa['Fuel'] == 'SUN') & (aa['Technology'] == 'STUR')]

    for c in list(csp_data['Zone'].unique()):
        if c in list(generation.index):
            csp_data.loc[csp_data['Zone'] == c, 'CF'] = capacity_factors.loc[c]['CF_CSP']
        else:
            csp_data.loc[csp_data['Zone'] == c, 'CF'] = 0
    csp_data.set_index('Unit', inplace=True)
    ones_df_csp = pd.DataFrame(index=date_range('1/1/' + str(YEAR), '1/1/' + str(YEAR + 1), freq='H'),
                               columns=csp_units).fillna(1)

    csp_outage = ones_df_csp - ones_df_csp * csp_data['CF']

    outage = pd.concat([bio_outage, geo_outage, csp_outage], axis=1, sort=False, join='inner')
    units_with_outage = pd.concat([bio_data, geo_data, csp_data], axis=0, sort=False)
    units_with_outage = units_with_outage.loc[units_with_outage['Zone'].isin(list(generation.index))]

    tmp_out = {}
    for c in list(units_with_outage['Zone'].unique()):
        units = units_with_outage.loc[units_with_outage['Zone'] == c].index
        tmp_out[c] = outage.loc[:, units]

    return tmp_out
