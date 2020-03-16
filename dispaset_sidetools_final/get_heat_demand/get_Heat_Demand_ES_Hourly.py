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

#Cogen heat demand (=CHP heat production), from YearBalance:
#Enter CHP technology names
chp_tech = ['TOTAL','TOTAL_HT','TOTAL_LT','TOTAL_LT_DEC','TOTAL_LT_DHN','IND_COGEN_GAS','IND_COGEN_WOOD','IND_COGEN_WASTE','DHN_COGEN_GAS','DHN_COGEN_WOOD','DHN_COGEN_WASTE','DEC_COGEN_GAS','DEC_COGEN_OIL']

#CHP sizes, from assets:
#Enter CHP technology names
chp_tech = ['TOTAL','IND_COGEN_GAS','IND_COGEN_WOOD','IND_COGEN_WASTE','DHN_COGEN_GAS','DHN_COGEN_WOOD','DHN_COGEN_WASTE','DEC_COGEN_GAS','DEC_COGEN_OIL']

#List of all the tech chp and p2h
tech = p2h_tech[5:] + chp_tech[1:]


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

#keep only the percentage Tech_LT_heat_prod / CHP_LT_heat_prod + P2H_LT_heat_prod of this time series. put it back in heat_demand_ts for each country.
tech_country = list()

for y in tech:
    dhn=0
    ind=0
    dec=0
    dhn = search_YearBalance(y, 'HEAT_LOW_T_DHN')
    ind = search_YearBalance(y, 'HEAT_HIGH_T')
    dec = search_YearBalance(y, 'HEAT_LOW_T_DECEN')
    if dhn!=0 or ind!=0 or dec!=0:
        tech_country.append(Country + '_' + y)


print(tech_country)

heat_demand_ESinput = pd.DataFrame(index=range(0,8760), columns=tech_country)

for x in range(0,len(countries)):
    for day in range(1,366):
        print(day)
        for h in range(1,25):
            thistd = get_TD((day-1)*24+h,n_TD)
            for y in tech:
                name = countries[x] + '_' + y
                if 'IND' in y:
                    heat_demand_ESinput.at[(day-1)*24+h-1, name] = search_HeatLayers('HT',thistd,h,y) * 1000
                else:
                    heat_demand_ESinput.at[(day-1)*24+h-1, name] = search_HeatLayers('LT', thistd,h,y) * 1000

heat_demand = heat_demand_ESinput.set_index(drange)
print(heat_demand)




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

write_csv_files('2015', heat_demand,True)


