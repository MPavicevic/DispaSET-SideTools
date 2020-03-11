import pandas as pd
import glob

input_folder = '../../Inputs/'  # to access DATA - DATA_brut & Typical_Units(to find installed power f [GW or GWh for storage])
output_folder = '../../Outputs/'

from search import search_YearBalance
from search import search_Dict_list


########################################################################################################################

# Get total heat produced by HeatSLack in EnergyScope

def get_HeatSlack():


    #Enter countries studied
    countries = list(['BE'])

#Non cogen nor P2H heat production, from YearBalance

#Take all the Heatslack technology names
    tech_list = ['TOTAL','TOTAL_HT','TOTAL_LT','TOTAL_LT_DEC','TOTAL_LT_DHN']
    HS_tech = search_Dict_list(tech_list,'HeatSlack')

    HeatSlack_demand = pd.DataFrame(index=countries,columns = [HS_tech])

    for x in range(0,len(countries)):
        total_HT = 0
        total_LT_dec = 0
        total_LT_dhn = 0
        Country = countries[x]
        for y in HS_tech:
            if y!= 'TOTAL' and y != 'TOTAL_HT' and y!= 'TOTAL_LT' and y!= 'TOTAL_LT_DEC' and y!= 'TOTAL_LT_DHN':
                value_HT = 0
                value_LT_DEC = 0
                value_LT_DHN = 0
                value_HT = abs(search_YearBalance(y,'HEAT_HIGH_T'))
                value_LT_DEC = abs(search_YearBalance(y,'HEAT_LOW_T_DECEN'))
                value_LT_DHN = abs(search_YearBalance(y,'HEAT_LOW_T_DHN'))

                techno = y
                HeatSlack_demand.at[Country,techno] = value_HT + value_LT_DEC + value_LT_DHN

                if value_HT > 0:
                    total_HT = total_HT + value_HT
                if value_LT_DEC > 0:
                    total_LT_dec = total_LT_dec + value_LT_DEC
                if value_LT_DHN > 0:
                    total_LT_dhn = total_LT_dhn + value_LT_DHN

                print(y + ' : ' + ' HT :' + str(value_HT) + ' LT_DEC : ' + str(value_LT_DEC) + ' LT : ' + str(value_LT_DHN)  )

        HeatSlack_demand.at[Country,'TOTAL_HT'] = total_HT
        HeatSlack_demand.at[Country,'TOTAL_LT_DEC'] = total_LT_dec
        HeatSlack_demand.at[Country,'TOTAL_LT_DHN'] = total_LT_dhn
        HeatSlack_demand.at[Country,'TOTAL_LT'] = total_LT_dhn + total_LT_dhn
        HeatSlack_demand.at[Country,'TOTAL'] = total_HT + total_LT_dec + total_LT_dhn

#print(HeatSlack_demand)
    HeatSlack_demand.to_csv('heatslack.csv')


########################################################################################################################

# function that gives the production in LT and HT heat for specified technologies in Energyscope

def get_ES_heatprod(list_tech):
    total_HT = 0
    total_LT_dec = 0
    total_LT_dhn = 0
    newlist = list_tech + ['Total_HT','Total_LT_DHN','Total_LT_DEC','Total_LT']
    Heat_prod = pd.DataFrame(index=newlist, columns=['High_Temp','Low_Temp_DHN','Low_Temp_DEC'])
    for t in list_tech:
        value_HT = 0
        value_LT_DEC = 0
        value_LT_DHN = 0
        if t[:2] == 'TS':
            value_HT = search_YearBalance(t, 'HEAT_HIGH_T')
            value_LT_DEC = search_YearBalance(t, 'HEAT_LOW_T_DECEN')
            value_LT_DHN = search_YearBalance(t, 'HEAT_LOW_T_DHN')
            if value_HT < 0:
                total_HT = total_HT + value_HT
                Heat_prod.at[t, 'High_Temp'] = value_HT
            if value_LT_DEC < 0:
                total_LT_dec = total_LT_dec + value_LT_DEC
                Heat_prod.at[t, 'Low_Temp_DEC'] = value_LT_DEC
            if value_LT_DHN < 0:
                total_LT_dhn = total_LT_dhn + value_LT_DHN
                Heat_prod.at[t, 'Low_Temp_DHN'] = value_LT_DHN
        else:
            value_HT = abs(search_YearBalance(t, 'HEAT_HIGH_T'))
            value_LT_DEC = abs(search_YearBalance(t, 'HEAT_LOW_T_DECEN'))
            value_LT_DHN = abs(search_YearBalance(t, 'HEAT_LOW_T_DHN'))

        if value_HT > 0:
            total_HT = total_HT + value_HT
            Heat_prod.at[t, 'High_Temp'] = value_HT
        if value_LT_DEC > 0:
            total_LT_dec = total_LT_dec + value_LT_DEC
            Heat_prod.at[t, 'Low_Temp_DEC'] = value_LT_DEC
        if value_LT_DHN > 0:
            total_LT_dhn = total_LT_dhn + value_LT_DHN
            Heat_prod.at[t, 'Low_Temp_DHN'] = value_LT_DHN

    Heat_prod.at['Total_HT', 'High_Temp'] = total_HT
    Heat_prod.at['Total_LT_DHN', 'Low_Temp_DHN'] = total_LT_dhn
    Heat_prod.at['Total_LT_DHN', 'Low_Temp_DEC'] = total_LT_dec
    Heat_prod.at['Total_LT','Low_Temp_DEC'] = total_LT_dec + total_LT_dhn

    return Heat_prod


list = ['IND_COGEN_GAS','IND_DIRECT_ELEC','DEC_HP_ELEC','DHN_HP_ELEC','IND_BOILER_WOOD','IND_BOILER_WASTE','TS_DEC_HP_ELEC','TS_DHN_SEASONAL']
print(get_ES_heatprod(list))