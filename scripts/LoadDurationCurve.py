# -*- coding: utf-8 -*-
"""
Created on Tue Nov  5 08:38:52 2019

@author: Matija Pavičević
"""

from __future__ import division
import pandas as pd
import numpy as np
import os
from dispaset_sidetools.common import mapping,outliers,fix_na,make_dir
import matplotlib.pyplot as plt
import enlopy as el
from itertools import product

input_folder = '../Inputs/DatabasesHeatingDemand/'  # Standard input folder
output_folder = '../Outputs/'# Standard output folder

years = list(range(2008, 2014))

data = {}
data_LDC = {}
for year in years:
    data[year] = pd.read_csv(input_folder + 'When2Heat_' + str(year) + '.csv')
    data[year].drop('Unnamed: 0', axis = 1, inplace=True)
    if year % 4 == 0:
        data[year].set_index(pd.date_range(start=str(year) + '-01-01 00:00:00', 
            end=str(year) + '-12-31 23:00:00', periods=8784), inplace=True)
    else:
        data[year].set_index(pd.date_range(start=str(year) + '-01-01 00:00:00', 
            end=str(year) + '-12-31 23:00:00', periods=8760), inplace=True)
    data[year] = data[year][~((data[year].index.month == 2) & (data[year].index.day == 29))]
    data[year].reset_index(drop=True,inplace=True)

countries = list(data[year].columns)
grouped = {}
for c in countries:
    grouped[c] = pd.concat([data[years[0]][c],data[years[1]][c],data[years[2]][c],
                      data[years[3]][c],data[years[4]][c],data[years[5]][c]],axis=1)    
    grouped[c].columns = years

ncols = len(countries) // 4
nrows = 4  # len(cntries_to_choose)
fig, axes = plt.subplots(nrows=nrows, ncols=ncols, sharey=False, frameon=True,
                         gridspec_kw={'wspace': 0.3, 'hspace': .35},
                         figsize=(1.65*2 * ncols, 1.9*2 * nrows),
                         facecolor='#fff4f2')  # #d4ffff

for icountry, iax in zip(countries, axes.ravel()):
    el.plot_LDC(grouped[icountry],ax=iax, y_norm=False, stacked=False)
    iax.tick_params(axis='both', which='major', labelsize=8)

    # Plot simulation results
    x1, y1 = el.get_LDC(grouped[icountry], y_norm=False, x_norm=True)
#    iax.plot(x1, y1, color='red', lw=1.5)
#    LF_sim = str(np.round(y1.mean() / y1.max(), 2))
        # Axes formatting - titles
    yaxis_max = np.max(y1.max()) * 1.01
    iax.set_xlim([0, 1])
    iax.set_ylim([0, yaxis_max])
    iax.set_title(icountry)

fig.savefig('LDC_Heating.pdf', transparent=True)


el.plot_percentiles(grouped[icountry][2008], x='week', zz='hour')
el.plot_heatmap(grouped[icountry][2008], edgecolors='none')
el.plot_3d(grouped[icountry][2008], x='hour', y='month', aggfunc='mean', cmap='Blues')
el.plot_boxplot(grouped[icountry][2008], by='day')
el.get_load_archetypes(grouped[icountry][2008], 5, plot_diagnostics=True)
el.get_load_stats(grouped[icountry][2008])
