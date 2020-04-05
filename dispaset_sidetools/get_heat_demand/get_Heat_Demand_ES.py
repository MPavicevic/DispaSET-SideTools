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
p2h_tech_1 = ['TOTAL','TOTAL_HT','TOTAL_LT','TOTAL_LT_DEC','TOTAL_LT_DHN']+p2h_tech #p2h_tech comes from constants.py

p2h_demand = pd.DataFrame(index=countries,columns = [p2h_tech_1])


for x in range(0,len(countries)):
    total_HT = 0
    total_LT_dec = 0
    total_LT_dhn = 0
    Country = countries[x]
    for y in p2h_tech_1:
        if y!= 'TOTAL' and y != 'TOTAL_HT' and y!= 'TOTAL_LT' and y!= 'TOTAL_LT_DEC' and y!= 'TOTAL_LT_DHN':
            value_HT = 0
            value_LT_DEC = 0
            value_LT_DHN = 0
            value_HT = abs(search_YearBalance(y,'HEAT_HIGH_T'))
            value_LT_DEC = abs(search_YearBalance(y,'HEAT_LOW_T_DECEN'))
            value_LT_DHN = abs(search_YearBalance(y,'HEAT_LOW_T_DHN'))

            techno = y
            p2h_demand.at[Country,techno] = value_HT + value_LT_DEC + value_LT_DHN

            if value_HT > 0:
                total_HT = total_HT + value_HT
            if value_LT_DEC > 0:
                total_LT_dec = total_LT_dec + value_LT_DEC
            if value_LT_DHN > 0:
                total_LT_dhn = total_LT_dhn + value_LT_DHN


    p2h_demand.at[Country,'TOTAL_HT'] = total_HT
    p2h_demand.at[Country,'TOTAL_LT_DEC'] = total_LT_dec
    p2h_demand.at[Country,'TOTAL_LT_DHN'] = total_LT_dhn
    p2h_demand.at[Country,'TOTAL_LT'] = total_LT_dhn + total_LT_dec
    p2h_demand.at[Country,'TOTAL'] = total_HT + total_LT_dec + total_LT_dhn

#print(p2h_demand)


#Cogen heat demand (=CHP heat production), from YearBalance:
#Enter CHP technology names
chp_tech_1 = ['TOTAL','TOTAL_HT','TOTAL_LT','TOTAL_LT_DEC','TOTAL_LT_DHN']+chp_tech   #p2h_tech comes from constants.py

chp_demand = pd.DataFrame(index=countries,columns = [chp_tech_1])

for x in range(0,len(countries)):
    total_HT = 0
    total_LT_dec = 0
    total_LT_dhn = 0
    Country = countries[x]
    for y in chp_tech_1:
        if y!= 'TOTAL' and y != 'TOTAL_HT' and y!= 'TOTAL_LT' and y!= 'TOTAL_LT_DEC' and y!= 'TOTAL_LT_DHN':
            value_HT = 0
            value_LT_DEC = 0
            value_LT_DHN = 0
            value_HT = abs(search_YearBalance(y,'HEAT_HIGH_T'))
            value_LT_DEC = abs(search_YearBalance(y,'HEAT_LOW_T_DECEN'))
            value_LT_DHN = abs(search_YearBalance(y,'HEAT_LOW_T_DHN'))
            techno = y
            chp_demand.at[Country,techno] = value_HT + value_LT_DEC + value_LT_DHN

            if value_HT > 0:
                total_HT = total_HT + value_HT
            if value_LT_DEC > 0:
                total_LT_dec = total_LT_dec + value_LT_DEC
            if value_LT_DHN > 0:
                total_LT_dhn = total_LT_dhn + value_LT_DHN

    chp_demand.at[Country,'TOTAL_HT'] = total_HT
    chp_demand.at[Country,'TOTAL_LT_DEC'] = total_LT_dec
    chp_demand.at[Country,'TOTAL_LT_DHN'] = total_LT_dhn
    chp_demand.at[Country,'TOTAL_LT'] = total_LT_dhn + total_LT_dec
    chp_demand.at[Country,'TOTAL'] = total_HT + total_LT_dec + total_LT_dhn

#print(chp_demand)




#CHP sizes, from assets:
#Enter CHP technology names
chp_tech_2 = ['TOTAL']+chp_tech

#List of all the tech chp and p2h
tech = p2h_tech[5:] + chp_tech_2[1:]

chp_capa = pd.DataFrame(index=countries,columns = [chp_tech_2])

for x in range(0,len(countries)):
    total = 0
    Country = countries[x]
    for y in chp_tech_2:
        if y!= 'TOTAL':
            techno = y
            value = search_assets(techno, 'f')
            chp_capa.at[Country,techno] = value
            total = total + value
    chp_capa.at[Country, 'TOTAL'] = total
#print(chp_capa)


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


#heat_demand_ts.to_csv(output_folder + 'heat_dem_test.csv')

#Computing the total LT and HT heat produced by the heat slack tech of ES :



#keep only the percentage Tech_LT_heat_prod / CHP_LT_heat_prod + P2H_LT_heat_prod of this time series. put it back in heat_demand_ts for each country.
tech_country = list()
ratio_chpp2h_LT = pd.DataFrame(index=countries)
ratio_chpp2h_HT = pd.DataFrame(index=countries)

for x in range(0,len(countries)):
    Country = countries[x]
    for y in range(0,len(tech)):
        if (tech[y])[:3] == 'IND':
            tech_country.append(Country + '_' + tech[y])
            if tech[y][-4:] == 'ELEC':
                a = float(p2h_demand.loc[Country, tech[y]])
                c = float(chp_demand.loc[Country, 'TOTAL_HT'])
                b = float(p2h_demand.loc[Country, 'TOTAL_HT'])
                ratio_chpp2h_HT.at[Country, tech[y]] = a / (b + c)
            else:
                a = float(chp_demand.loc[Country, tech[y]])
                c = float(chp_demand.loc[Country,'TOTAL_HT'])
                b = float(p2h_demand.loc[Country, 'TOTAL_HT'])
                ratio_chpp2h_HT.at[Country,tech[y]] = a/(b+c)
        else:
            tech_country.append(Country + '_' + tech[y])
            if tech[y][-4:] == 'ELEC':
                a = float(p2h_demand.loc[Country, tech[y]])
                c = float(chp_demand.loc[Country,'TOTAL_LT'])
                b = float(p2h_demand.loc[Country, 'TOTAL_LT'])
                ratio_chpp2h_LT.at[Country,tech[y]] = a/(b+c)
            else:
                a = float(chp_demand.loc[Country, tech[y]])
                c = float(chp_demand.loc[Country, 'TOTAL_LT'])
                b = float(p2h_demand.loc[Country, 'TOTAL_LT'])
                ratio_chpp2h_LT.at[Country, tech[y]] = a / (b + c)


#print(ratio_chp_chpp2h)

#fill heat_demand_ESinput with ts * chp_type/chp+p2h for each chp tech
heat_demand_ESinput = pd.DataFrame(index=drange, columns=tech_country)

i = 0
for x in range(0,len(tech_country)):
    if (tech_country[x])[3:6] == 'IND':
        countr = (tech_country[x])[:2]
        factor = ratio_chpp2h_HT.loc[countr,(tech_country[x])[3:]]
        heat_demand_ESinput[(tech_country[x])] = heat_demand_ts_HT[countr].multiply(factor)

    else:
        countr = (tech_country[x])[:2]
        factor = ratio_chpp2h_LT.loc[countr, (tech_country[x])[3:]]
        heat_demand_ESinput[(tech_country[x])] = heat_demand_ts_LT[countr].multiply(factor)

#print(chp_demand.loc['BE', 'TOTAL_HT'])
#print(p2h_demand.loc['BE', 'TOTAL_HT'])
#print(search_YearBalance('IND_DIRECT_ELEC','HEAT_HIGH_T'))
#print(search_YearBalance('IND_COGEN_GAS','HEAT_HIGH_T'))

p2h_demand.to_csv('p2hdemand.csv')
chp_demand.to_csv('chpdemand.csv')

'''
# Put the right nomenclature

from search import search_Dict_ES2DS
names = heat_demand_ESinput.columns
newnames = list()
for n in range(0,len(names)):
    namedS = search_Dict_ES2DS(names[n][3:])
    newnames.append(str((names[n])[:2]) + '_' + namedS)
heat_demand_ESinput.columns = newnames
'''

''' # comment all the When2Heat part.  Don't forget to recomment leap year modif ! ! ! ! 



















# To do : the same with the when2heat !

#enter the studied year
YEAR = 2030
# %% Define countries that have the weather year closer to the 2016
c = {}
c['2008'] = ['BE', 'CZ', 'DE', 'IE', 'FR', 'HR', 'LU', 'NL', 'UK']
c['2009'] = ['EE', 'LV', 'LT', 'HU', 'PL', 'RO', 'SI', 'SK', 'FI']
c['2010'] = []
c['2011'] = ['DK', 'IT', 'AT', 'CH']
c['2012'] = []
c['2013'] = ['BG', 'EL', 'ES', 'PT', 'SE', 'NO']

years = ['2008', '2009', '2010', '2011', '2012', '2013']

# Import heating demand profile
demand_heat = {}
demand_heat_tot = {}
demand_heat_ad = {}
demand_heat_conc = {}
# Create df with heat profiles
for y in years:
    demand_heat[y] = pd.read_csv(input_folder + heating_folder + 'When2Heat_' + y + '.csv', header=0, index_col=0)
    demand_heat[y]['UK'] = demand_heat[y]['GB']
    demand_heat[y].drop(columns=['GB'], inplace=True)


# Add correction for the not leap years
for temp in ['2009', '2010', '2011', '2013']:
    for h in ['00', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16',
              '17', '18', '19', '20', '21', '22', '23']:
        demand_heat[temp].loc[temp + '-02-29 ' + h + ':00:00', :] = (demand_heat[temp].loc[temp + '-02-28 ' + h +
                                                                    ':00:00', :] + demand_heat[temp].loc[temp +
                                                                    '-03-01 ' + h + ':00:00', :]) / 2
        demand_heat[temp].sort_index(inplace=True)
myindex = demand_heat['2009'].index



for y in years:
    demand_heat[y] = demand_heat[y].loc[:, c[y]]  # Select for each country the closest hourly profile
    demand_heat_ad[y] = demand_heat[y] / demand_heat[y].sum(axis=0)
    yr = YEAR


    hour = list(demand_heat[y].index)
    for h in range(0,len(hour)):
        hour[h] = str(YEAR) + (hour[h])[4:]

    demand_heat_ad[y].set_index(pd.Index(hour), inplace=True)

#    demand_heat_conc[y] = demand_heat_ad[y].reset_index(drop=True)
#    demand_heat_conc[y].to_csv(output_folder + 'heat_demand_test_W2H'+y+ '.csv')


demand_heat_ad_2030 = pd.concat(
    [demand_heat_ad['2008'], demand_heat_ad['2009'], demand_heat_ad['2010'], demand_heat_ad['2011'],
     demand_heat_ad['2012'], demand_heat_ad['2013']], axis=1, join='outer')

#print(demand_heat_ad_2030)

demand_heat_ad_2030.to_csv(output_folder + 'heat_demand_test_W2H.csv')



#fill heat_demand_W2H with demand_heat_ad_2030 * total prod for each chp tech
heat_demand_W2H = pd.DataFrame(index=hour, columns=tech_country)

for x in range(0,len(tech_country)):
    countr = (tech_country[x])[:2]
    factor = ratio_chp_chpp2h.loc[countr, (tech_country[x])[3:]]
    total_year_heat = heat_demand_ts[countr].sum()
    heat_demand_W2H[tech_country[x]] = demand_heat_ad_2030[countr].multiply(total_year_heat*factor)

#print(heat_demand_W2H)

heat_demand_W2H.to_csv(output_folder + 'heat_demand_W2H.csv')

'''

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

write_csv_files('2015', heat_demand_ESinput,True)
#write_csv_files('2030_fromW2H', heat_demand_W2H,True)


