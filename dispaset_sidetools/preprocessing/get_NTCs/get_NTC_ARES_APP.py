# -*- coding: utf-8 -*-
"""
@author: Matija Pavičević
"""

from __future__ import division

import pandas as pd

# Local source tree imports
from ...common import date_range


def get_NTCs(data,YEAR):
    """
    FUnction that reads the NTCs and tranforms them into dispa-set format
    :param data:    raw input data
    :param YEAR:    year to be assigned to the index
    :return:        processed NTC's
    """
    countries = list(data.index)
    tmp = {}
    for home in countries:
        for away in countries:
            tmp[home + ' -> ' + away] = data.loc[home, away]
    ntcs = pd.DataFrame(tmp, index=date_range('1/1/' + str(YEAR), '1/1/' + str(YEAR + 1), freq='H'))
    ntcs.dropna(axis=1, inplace=True)
    return ntcs
