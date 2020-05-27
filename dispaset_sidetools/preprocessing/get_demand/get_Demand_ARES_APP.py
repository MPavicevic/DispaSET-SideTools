# -*- coding: utf-8 -*-
"""
@author: Matija Pavičević
"""

from __future__ import division

# Local source tree imports
from ...common import date_range, get_country_codes


def get_demands(data_full, data_annual, YEAR, SOURCE = 'JRC'):
    data_full.dropna(axis=1, inplace=True)

    data = {}
    date_2010 = date_range('1/1/2010', '1/1/2011', freq='H')
    date_2015 = date_range('1/1/2015', '1/1/2016', freq='H')
    data[str(2010)] = data_full.loc[data_full['Year'] == 2010]
    data[str(2015)] = data_full.loc[data_full['Year'] == 2015]
    data[str(2010)].set_index(date_2010, inplace=True)
    data[str(2015)].set_index(date_2015, inplace=True)
    data[str(2010)].drop(columns=['Year', 'Hour'], inplace=True)
    data[str(2015)].drop(columns=['Year', 'Hour'], inplace=True)

    country_codes = get_country_codes(list(data[str(2015)].columns))
    data[str(2010)].columns = country_codes
    data[str(2015)].columns = country_codes

    # South Sudan profile scaled from Sudan
    ss_annual = 391800  # MWh
    data['2015']['SS'] = data['2015'].loc[:, 'SD'] / data['2015'].loc[:, 'SD'].sum() * ss_annual

    # Annual adjustments based on external projections
    tmp_data = data_annual.loc[(data_annual['Source'] == SOURCE) & (data_annual['Year'] == YEAR)]
    tmp_data.index = tmp_data['Country']

    # Scaling to desired year according to source
    annual_scaling_factor = data['2015'] / data['2015'].sum()
    data[str(YEAR)] = annual_scaling_factor * tmp_data['Energy'] * 1e3
    data[str(YEAR)].dropna(axis=1,inplace=True)

    return data[str(YEAR)]
