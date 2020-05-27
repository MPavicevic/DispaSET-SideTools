# -*- coding: utf-8 -*-
"""
@author: Matija Pavičević
"""

from __future__ import division

import pandas as pd
import os
import sys
import enlopy as el
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import logging
import matplotlib.cm as cm
# Local source tree imports
from dispaset_sidetools.common import date_range, get_country_codes, write_csv_files, commons

sys.path.append(os.path.abspath(r'../..'))

# %% Inputs
# Folder destinations
input_folder = commons['InputFolder']
source_folder = 'ARES_Africa/'
output_folder = commons['OutputFolder']

# File names
input_file_hourly_data = 'Estimated hourly load profiles (for 2010 and 2015).xlsx'
sheet_hourly_data = 'Hourly load profiles'
input_file_annual_data = 'Annual_Demand_Statistics.xlsx'
sheet_annual_data = 'Inputs'

# Other options
WRITE_CSV = False
YEAR = 2015

# Source for demand projections
# TEMBA, IEA, JRC, World Bank, CIA: World Fact Book, Indexmundi
SOURCE = 'JRC'

# %% Data preprocessing
xls = pd.ExcelFile(input_folder + source_folder + input_file_hourly_data)
data_full = pd.read_excel(xls, sheet_name=sheet_hourly_data, header=0)
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
data_annual = pd.read_excel(input_folder + source_folder + input_file_annual_data, sheet_annual_data)
tmp_data = data_annual.loc[(data_annual['Source'] == SOURCE) & (data_annual['Year'] == YEAR)]
tmp_data.index = tmp_data['Country']

# Scaling to desired year according to source
annual_scaling_factor = data['2015'] / data['2015'].sum()
data[str(YEAR)] = annual_scaling_factor * tmp_data['Energy'] * 1e3
data[str(YEAR)].dropna(axis=1,inplace=True)

# Generate database
write_csv_files(data[str(YEAR)], 'ARES_APP', SOURCE, 'TotalLoadValue', str(YEAR), WRITE_CSV, 'Zonal')


def make_timeseries(x=None, year=None, length=None, startdate=None, freq=None):
    """Convert numpy array to a pandas series with a timed index. Convenience wrapper around a datetime-indexed pd.DataFrame.

    Parameters:
        x: (nd.array) raw data to wrap into a pd.Series
        startdate: pd.datetime
        year: year of timeseries
        freq: offset keyword (e.g. 15min, H)
        length: length of timeseries
    Returns:
        pd.Series or pd.Dataframe with datetimeindex
    """

    if startdate is None:
        if year is None:
            logging.info('No info on the year was provided. Using current year')
            year = pd.datetime.now().year
        startdate = pd.datetime(year, 1, 1, 0, 0, 0)

    if x is None:
        if length is None:
            raise ValueError('The length or the timeseries has to be provided')
    else:  # if x is given
        length = len(x)
        if freq is None:
            # Shortcuts: Commonly used frequencies are automatically assigned
            if len(x) == 8760 or len(x) == 8784:
                freq = 'H'
            elif len(x) == 35040:
                freq = '15min'
            elif len(x) == 12:
                freq = 'm'
            else:
                raise ValueError('Input vector length must be 12, 8760 or 35040. Otherwise freq has to be defined')

    #enddate = startdate + pd.datetools.timedelta(seconds=_freq_to_sec(freq) * (length - 1) )
    date_list = pd.date_range(start=startdate, periods=length, freq=freq)
    if x is None:
        return pd.Series(np.nan, index=date_list)
    elif isinstance(x, (pd.DataFrame, pd.Series)):
        x.index = date_list
        return x
    elif isinstance(x, (np.ndarray, list)):
        if len(x.shape) > 1:
            return pd.DataFrame(x, index=date_list)
        else:
            return pd.Series(x, index=date_list)
    else:
        raise ValueError('Unknown type of data passed')

def clean_convert(x, force_timed_index=True, always_df=False, **kwargs):
    """Converts a list, a numpy array, or a dataframe to pandas series or dataframe, depending on the
    compatibility and the requirements. Designed for maximum compatibility.

    Arguments:
        x (list, np.ndarray): Vector or matrix of numbers. it can be pd.DataFrame, pd.Series, np.ndarray or list
        force_timed_index (bool): if True it will return a timeseries index
        year (int): Year that will be used for the index
        always_df (bool): always return a dataframe even if the data is one dimensional
        **kwargs: Exposes arguments of :meth:`make_timeseries`
    Returns:
        pd.Series: Timeseries

    """

    if isinstance(x, list):  # nice recursions
        return clean_convert(pd.Series(x), force_timed_index, always_df, **kwargs)

    elif isinstance(x, np.ndarray):
        if len(x.shape) == 1:
            return clean_convert(pd.Series(x), force_timed_index, always_df, **kwargs)
        else:
            return clean_convert(pd.DataFrame(x), force_timed_index, always_df, **kwargs)

    elif isinstance(x, pd.Series):
        if always_df:
            x = pd.DataFrame(x)
        if x.index.is_all_dates:
            return x
        else:  # if not datetime index
            if force_timed_index:
                logging.debug('Forcing Datetimeindex into passed timeseries.'
                              'For more accurate results please pass a pandas time-indexed timeseries.')
                return make_timeseries(x, **kwargs)
            else:  # does not require datetimeindex
                return x

    elif isinstance(x, pd.DataFrame):
        if x.shape[1] == 1 and not always_df:
            return clean_convert(x.squeeze(), force_timed_index, always_df, **kwargs)
        else:
            if force_timed_index and not x.index.is_all_dates:
                return make_timeseries(x, **kwargs)
            else:  # does not require datetimeindex
                return x
    else:
        raise ValueError(
            'Unrecognized Type. Has to be one of the following: pd.DataFrame, pd.Series, np.ndarray or list')


def reshape_timeseries(Load, x='dayofyear', y=None, aggfunc='sum'):
    """Returns a reshaped pandas DataFrame that shows the aggregated load for selected
    timeslices. e.g. time of day vs day of year

    Parameters:
        Load (pd.Series, np.ndarray): timeseries
        x (str): x axis aggregator. Has to be an accessor of pd.DatetimeIndex
         (year, dayoftime, week etc.)
        y (str): similar to above for y axis
    Returns:
        reshaped pandas dataframe according to x,y
    """

    # Have to convert to dataframe in order for pivottable to work
    # 1D, Dataframe
    a = clean_convert(Load.copy(), force_timed_index=True, always_df=True)
    a.name = 0
    if len(a.columns) > 1:
        raise ValueError('Works only with 1D')

    if x is not None:
        a[x] = getattr(a.index, x)
    if y is not None:
        a[y] = getattr(a.index, y)
    a = a.reset_index(drop=True)

    return a.pivot_table(index=x, columns=y,
                         values=a.columns[0],
                         aggfunc=aggfunc).T


def plot_heatmap(Load, x='dayofyear', y='hour', aggfunc='sum', bins=8,
                figsize=(8,6), edgecolors='none', cmap='Oranges', colorbar=True, ax=None, **pltargs):
    """ Returns a 2D heatmap of the reshaped timeseries based on x, y

    Arguments:
        Load: 1D pandas with timed index
        x: Parameter for :meth:`enlopy.analysis.reshape_timeseries`
        y: Parameter for :meth:`enlopy.analysis.reshape_timeseries`
        bins: Number of bins for colormap
        edgecolors: colour of edges around individual squares. 'none' or 'w' is recommended.
        cmap: colormap name (from colorbrewer, matplotlib etc.)
        **pltargs: Exposes matplotlib.plot arguments
    Returns:
        2d heatmap
    """
    columns = 5
    rows = int(len(Load.columns) / columns) + (len(Load.columns) % columns > 0)
    fig = plt.figure(figsize=figsize,constrained_layout=True)
    # axs = plt.subplots(rows, columns, figsize=figsize, sharex=True, sharey=True, )
    spec = fig.add_gridspec(nrows= rows, ncols = columns +1)
    # fig.subplots_adjust(hspace=0.4)

    # axs = axs.ravel()
    cmap_obj = cm.get_cmap(cmap, bins)
    i = 0
    for row in range(rows):

        for col in range(columns):
            ax = fig.add_subplot(spec[row, col])
            bb = Load.iloc[:, i]
            x_y = reshape_timeseries(bb, x=x, y=y, aggfunc=aggfunc)
            heatmap = ax.pcolor(x_y, cmap=cmap_obj, edgecolors=edgecolors)
            ax.set_xlim(right=len(x_y.columns))
            ax.set_ylim(top=len(x_y.index))
            if i >=20:
                ax.set_xlabel(x)
            if i in [0,5, 10, 15, 20]:
                ax.set_ylabel(y)
            ax.set_title(bb.name)
            i = i + 1
    if colorbar:
        ax2 = fig.add_subplot(spec[:, columns])
        fig.colorbar(heatmap, ax=ax2, location='right', shrink=0.8)
        fig.delaxes(ax2)
    folder_figures = output_folder + source_folder + 'Figures/'
    fig.savefig(folder_figures + "\Heatmap_Demand.png")

    plt.show()

aa = data[str(YEAR)] / data[str(YEAR)].max()
plot_heatmap(aa, figsize=(15,14))
