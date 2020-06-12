from __future__ import division

import sys, os
sys.path.append(os.path.abspath(r'../..'))


from dispaset_sidetools import *
import numpy as np
import pandas as pd
import math

from dispaset_sidetools.common import *
from dispaset_sidetools.search import * #from_excel_to_dataFrame,search_YearBalance
from dispaset_sidetools.constants import *# countries,n_TD,elec_mobi_tech,p2h_tech

input_folder = '../../Inputs/EnergyScope/'
output_folder = '../../Outputs/EnergyScope/'
sidetools_folder = '../'

heating_folder = 'Heating_Demands/When2Heat/'

#P2H heat production, from YearBalance

#Enter P2H technology names
p2h_tech_1 = ['TOTAL','TOTAL_HT','TOTAL_LT','TOTAL_LT_DEC','TOTAL_LT_DHN'] + p2h_tech

#Cogen heat demand (=CHP heat production), from YearBalance:
#Enter CHP technology names
#chp_tech = ['TOTAL','TOTAL_HT','TOTAL_LT','TOTAL_LT_DEC','TOTAL_LT_DHN','IND_COGEN_GAS','IND_COGEN_WOOD','IND_COGEN_WASTE','DHN_COGEN_GAS','DHN_COGEN_WOOD','DHN_COGEN_WASTE','DEC_COGEN_GAS','DEC_COGEN_OIL']

#CHP sizes, from assets:
#Enter CHP technology names
chp_tech_1 = ['TOTAL'] + chp_tech

#List of all the tech chp and p2h
tech = p2h_tech_1[5:] + chp_tech_1[1:]


#Times Series (ts) of total heat demand, from input of EnergyScope

#heat_demand_ts = pd.read_csv(input_folder+'EUD_HEAT.txt',delimiter = '\t' ,index_col = 0) #[MWH]
heat_demand_ts = from_excel_to_dataFrame(input_folder + 'DATA_preprocessing_BE.xlsx', 'EUD_heat')

#Enter the starting date
start = pd.to_datetime(date_str)
drange = pd.date_range(start, periods=hourly_periods, freq='H')

heat_demand_ts.set_index(drange, inplace=True)
heat_demand_ts_LT = pd.DataFrame(index=drange)
heat_demand_ts_HT = pd.DataFrame(index=drange)

for Country in countries:
    col_LT = Country + '_LT'
    col_HT = Country + '_HT'
    heat_demand_ts_HT[Country] = heat_demand_ts[col_HT]
    heat_demand_ts_LT[Country] = heat_demand_ts[col_LT]

#keep only the percentage Tech_LT_heat_prod / CHP_LT_heat_prod + P2H_LT_heat_prod of this time series. put it back in heat_demand_ts for each country.
tech_country = list()

LTlayers = pd.read_csv(input_folder + 'LTlayers.txt',delimiter='\t')
HTlayers = pd.read_csv(input_folder + 'HTlayers.txt',delimiter='\t')
TD_DF = pd.read_csv(input_folder + 'TD_file.csv')

for y in tech:
    tech_country.append(Country + '_' + y)

ratio_chpp2h_LT = {}
ratio_chpp2h_HT = {}


td_demand_HT = pd.DataFrame(columns=tech) #to create ratios based on typical days
td_demand_LT = pd.DataFrame(columns=tech)


for x in range(0,len(countries)):
    Country = countries[x]
    ratio_chpp2h_LT_day = pd.DataFrame(index=range(0,365))
    ratio_chpp2h_HT_day = pd.DataFrame(index=range(0,365))

    for td in range(1,n_TD+1):
        TOTAL_HT = 0
        TOTAL_LT = 0
        for y in tech:
            value_HT = 0
            value_LT = 0
            for h in range(1,25):
                value_HT = value_HT + search_HeatLayers(HTlayers,td,h,y)
                value_LT = value_LT + search_HeatLayers(LTlayers,td,h,y)
            if 'IND' in y:
                td_demand_HT.at[td-1,y]=value_HT
                td_demand_LT.at[td-1,y] = 0
                TOTAL_HT = TOTAL_HT + value_HT
            else:
                td_demand_HT.at[td - 1, y] = 0
                td_demand_LT.at[td-1,y] = value_LT
                TOTAL_LT = TOTAL_LT + value_LT

        td_demand_HT.at[td-1,'TOTAL_HT'] = TOTAL_HT
        td_demand_LT.at[td-1,'TOTAL_LT'] = TOTAL_LT

    for day in range(1,366):
        TD = get_TD(TD_DF,(day-1)*24 + 1,n_TD)
        for y in range(0,len(tech)):
            if (tech[y])[:3] == 'IND':
                a = float(td_demand_HT.loc[TD-1, tech[y]])
                c = float(td_demand_HT.loc[TD-1,'TOTAL_HT'])
                ratio_chpp2h_HT_day.at[day-1, tech[y]] = a /c
            else:
                a = float(td_demand_LT.loc[TD-1, tech[y]])
                c = float(td_demand_LT.loc[TD-1,'TOTAL_LT'])
                ratio_chpp2h_LT_day.at[day-1,tech[y]] = a/c
    ratio_chpp2h_LT[countries[x]] = ratio_chpp2h_LT_day
    ratio_chpp2h_HT[countries[x]] = ratio_chpp2h_HT_day

#fill heat_demand_ESinput with ts * chp_type/chp+p2h for each chp tech

heat_demand_ESinput = pd.DataFrame(index=range(0,8760), columns=tech_country)
i = 0
for x in range(0,len(tech_country)):
    countr = (tech_country[x])[:2]
    countrynumber = countries.index(countr)
    for h in range(0,8760):
        thisday = int(h/24)
        if (tech_country[x])[3:6] == 'IND':
            factor = float(ratio_chpp2h_HT[countr].loc[thisday,(tech_country[x])[3:]])
            heat_demand_ESinput.at[h,(tech_country[x])] = heat_demand_ts_HT.iloc[h,countrynumber] * factor
        else:
            factor = float(ratio_chpp2h_LT[countr].loc[thisday, (tech_country[x])[3:]])
            heat_demand_ESinput.at[h,(tech_country[x])] = heat_demand_ts_LT.iloc[h,countrynumber] * factor

heat_demand = heat_demand_ESinput.set_index(drange)




def write_csv_files(dem_filename, heat_demand,WRITE_CSV_FILES):
    filename = dem_filename + '.csv'
    allunits = heat_demand
    if WRITE_CSV_FILES is True:
            make_dir(output_folder + 'Database')
            make_dir(output_folder + 'Database' + '/Heat_demand')
            folder = output_folder + 'Database/Heat_demand/'
            allunits.to_csv(folder +  '/' + filename)
    else:
        print('[WARNING ]: ' + 'WRITE_CSV_FILES = False, unable to write .csv files')

write_csv_files('2015_daily', heat_demand,True)

