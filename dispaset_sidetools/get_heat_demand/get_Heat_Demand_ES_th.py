from search import search_YearBalance
from search import search_assets
from dispaset_sidetools.common import make_dir
import pandas as pd

from search import get_TD
from search import search_HeatLayers
from search import from_excel_to_dataFrame
from search import get_TDFile

from search import search_ElecLayers
from search import get_TD

# %% Inputs
# Folder destinations
input_folder = '../../Inputs/'  # Standard input folder
output_folder = '../../Outputs/'  # Standard output folder
heating_folder = 'Heating_Demands/When2Heat/'

#Enter countries studied
countries = list(['BE', 'FR'])

#Enter the starting date
date_str = '1/1/2015'
start = pd.to_datetime(date_str)
hourly_periods = 8760
drange = pd.date_range(start, periods=hourly_periods, freq='H')


#Input file
EUD_heat = from_excel_to_dataFrame(input_folder + 'DATA_preprocessing_BE_FR.xlsx', 'EUD_heat')

for x in countries:
    perc_dhn = 0.37                                              #Value to be found in DATA.xlsx : 'share_heat_dhn: max'
#    perc_dhn_loss = 0.05                                        #Value to be found in DATA.xlsx : 'Loss_network: Heat_Low_T_dhn'
#    Prod_Tot_dhn = search_YearBalance('END_USES_DEMAND' ,'HEAT_LOW_T_DHN')*1000 #[MW]
    EUD_heat[x+'_DEC'] = EUD_heat[x+'_LT'].multiply(1-perc_dhn)
    EUD_heat[x+'_DHN'] = EUD_heat[x+'_LT'].multiply(perc_dhn)
    EUD_heat = EUD_heat.drop([x+'_LT'], axis=1)

EUD_heat = EUD_heat.set_index(drange)


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

write_csv_files('2015', EUD_heat,True)

