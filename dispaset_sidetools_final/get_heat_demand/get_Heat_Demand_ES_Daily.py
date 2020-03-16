from search import search_YearBalance
from search import search_assets
from dispaset_sidetools.common import make_dir
import pandas as pd

from search import get_TD
from search import search_HeatLayers

# %% Inputs
# Folder destinations
input_folder = '../../Inputs/'  # Standard input folder
output_folder = '../../Outputs/'  # Standard output folder
heating_folder = 'Heating_Demands/When2Heat/'

#Enter countries studied
countries = list(['BE'])

#Enter number of TD
n_TD = 12

#P2H heat production, from YearBalance

#Enter P2H technology names
p2h_tech = ['TOTAL','TOTAL_HT','TOTAL_LT','TOTAL_LT_DEC','TOTAL_LT_DHN','IND_DIRECT_ELEC','DHN_HP_ELEC','DEC_HP_ELEC','DEC_DIRECT_ELEC']

p2h_demand = pd.DataFrame(index=countries,columns = [p2h_tech])


for x in range(0,len(countries)):
    total_HT = 0
    total_LT_dec = 0
    total_LT_dhn = 0
    Country = countries[x]
    for y in p2h_tech:
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
chp_tech = ['TOTAL','TOTAL_HT','TOTAL_LT','TOTAL_LT_DEC','TOTAL_LT_DHN','IND_COGEN_GAS','IND_COGEN_WOOD','IND_COGEN_WASTE','DHN_COGEN_GAS','DHN_COGEN_WOOD','DHN_COGEN_WASTE','DEC_COGEN_GAS','DEC_COGEN_OIL']

chp_demand = pd.DataFrame(index=countries,columns = [chp_tech])

for x in range(0,len(countries)):
    total_HT = 0
    total_LT_dec = 0
    total_LT_dhn = 0
    Country = countries[x]
    for y in chp_tech:
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
chp_tech = ['TOTAL','IND_COGEN_GAS','IND_COGEN_WOOD','IND_COGEN_WASTE','DHN_COGEN_GAS','DHN_COGEN_WOOD','DHN_COGEN_WASTE','DEC_COGEN_GAS','DEC_COGEN_OIL']

#List of all the tech chp and p2h
tech = p2h_tech[5:] + chp_tech[1:]

chp_capa = pd.DataFrame(index=countries,columns = [chp_tech])

for x in range(0,len(countries)):
    total = 0
    Country = countries[x]
    for y in chp_tech:
        if y!= 'TOTAL':
            techno = y
            value = search_assets(techno, 'f')
            chp_capa.at[Country,techno] = value
            total = total + value
    chp_capa.at[Country, 'TOTAL'] = total
#print(chp_capa)


#Times Series (ts) of total heat demand, from input of EnergyScope

heat_demand_ts = pd.read_csv(input_folder+'EUD_HEAT.txt',delimiter = '\t' ,index_col = 0) #[MWH]

#Enter the starting date
date_str = '1/1/2015'
start = pd.to_datetime(date_str)
hourly_periods = 8760
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


#keep only the percentage Tech_LT_heat_prod / CHP_LT_heat_prod + P2H_LT_heat_prod of this time series. put it back in heat_demand_ts for each country.
tech_country = list()
ratio_chpp2h_LT = pd.DataFrame(index=countries)
ratio_chpp2h_HT = pd.DataFrame(index=countries)

td_demand_HT = pd.DataFrame(columns=tech) #to create ratios based on typical days
td_demand_LT = pd.DataFrame(columns=tech)


for x in range(0,len(countries)):
    Country = countries[x]

    for td in range(1,numbTD+1):
        TOTAL_HT = 0
        TOTAL_LT = 0
        for y in tech:
            value_HT = 0
            value_LT = 0
            for h in range(1,25):
                value_HT = value_HT + search_HeatLayers('HT',td,h,y)
                value_LT = value_LT + search_HeatLayers('LT',td,h,y)
            if 'IND' in y:
                td_demand_HT.at[td-1,y]=value_HT
                td_demand_LT.at[td-1,y] = 0
                TOTAL_HT = TOTAL_HT + value_HT
            else:
                td_demand_HT.at[td - 1, y] = 0
                td_demand_LT.at[td-1,y] = value_LT
                TOTAL_LT = TOTAL_LT + value_LT

        td_demand_HT.at[td-1,'TOTAT_HT'] = TOTAL_HT
        td_demand_LT.at[td - 1, 'TOTAT_LT'] = TOTAL_LT

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


