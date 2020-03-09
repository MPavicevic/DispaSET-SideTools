import pandas as pd
import glob

input_folder = '../../Inputs/'  # to access DATA - DATA_brut & Typical_Units(to find installed power f [GW or GWh for storage])
output_folder = '../../Outputs/'

from search import search_YearBalance
from search import search_Dict_list


########################################################################################################################

# Get total heat produced by HeatSLack in EnergyScope

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