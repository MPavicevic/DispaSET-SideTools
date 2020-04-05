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

for y in tech:
    dhn=0
    ind=0
    dec=0
    dhn = search_YearBalance(y, 'HEAT_LOW_T_DHN')
    ind = search_YearBalance(y, 'HEAT_HIGH_T')
    dec = search_YearBalance(y, 'HEAT_LOW_T_DECEN')
    if dhn!=0 or ind!=0 or dec!=0:
        tech_country.append(Country + '_' + y)



heat_demand_ESinput = pd.DataFrame(index=range(0,8760), columns=tech_country)

LTlayers = pd.read_csv(input_folder + 'LTlayers.txt',delimiter='\t')
HTlayers = pd.read_csv(input_folder + 'HTlayers.txt',delimiter='\t')
TD_DF = pd.read_csv(input_folder + 'TD_file.csv')

for x in range(0,len(countries)):
    for day in range(1,366):
        for h in range(1,25):
            thistd = get_TD(TD_DF,(day-1)*24+h,n_TD)
            for y in tech:
                name = countries[x] + '_' + y
                if 'IND' in y:
                    heat_demand_ESinput.at[(day-1)*24+h-1, name] = search_HeatLayers(HTlayers,thistd,h,y) * 1000
                else:
                    heat_demand_ESinput.at[(day-1)*24+h-1, name] = search_HeatLayers(LTlayers, thistd,h,y) * 1000

heat_demand = heat_demand_ESinput.set_index(drange)


####################################        Correlation            ######################################

TD_DF = pd.read_csv(input_folder + 'TD_file.csv')
ElecLayersDF = pd.read_csv(input_folder + 'ElecLayers.txt', delimiter='\t')
EUD_elec = from_excel_to_dataFrame(input_folder + 'DATA_preprocessing_BE.xlsx', 'EUD_elec')
Renewables_prod = from_excel_to_dataFrame(input_folder + 'DATA_preprocessing_BE.xlsx','AvailabilityFactors')


for x in countries:
    cog_col = [x+'_IND_COGEN_GAS']
    direct_col = [x + '_IND_DIRECT_ELEC']
    IND_COGEN_CORREL = pd.DataFrame(index=range(0,8760),columns=cog_col)
    IND_DIRECT_ELEC_CORREL = pd.DataFrame(index=range(0, 8760), columns=direct_col)

    PV_capa = search_assets('PV','f')
    WTOF_capa = search_assets('WIND_OFFSHORE','f')
    WTON_capa = search_assets('WIND_ONSHORE', 'f')
    HROR_capa = search_assets('HYDRO_RIVER', 'f')

    count = 0
    for day in range(1,366):
        for h in range(1,25):
            thistd = get_TD(TD_DF,(day-1)*24+h,n_TD)
            thisEUD = -EUD_elec.loc[(day-1)*24+h,x]/1000
            thisPV = Renewables_prod.loc[(day-1)*24+h-1, x+'_PV'] * PV_capa
            thisWTOF = Renewables_prod.loc[(day-1)*24+h-1, x+'_WIND_ONSHORE'] * WTOF_capa
            thisWTON = Renewables_prod.loc[(day-1)*24+h-1, x+'_WIND_OFFSHORE'] * WTON_capa
            thisHydro = Renewables_prod.loc[(day-1)*24+h-1, x+'_HYDRO_RIVER'] * HROR_capa

            balance_elec = thisEUD + search_ElecLayers(ElecLayersDF,thistd, h, 'ELEC_EXPORT') + search_ElecLayers(ElecLayersDF,thistd, h, 'CCGT') + thisPV + thisWTON + thisWTOF + thisHydro + search_ElecLayers(ElecLayersDF,thistd, h, 'DHN_HP_ELEC') + search_ElecLayers(ElecLayersDF,thistd, h, 'DEC_HP_ELEC') + search_ElecLayers(ElecLayersDF,thistd, h, 'TRAMWAY_TROLLEY')+ search_ElecLayers(ElecLayersDF,thistd, h, 'TRAIN_PUB') + search_ElecLayers(ElecLayersDF,thistd, h, 'TRAIN_CapitalfREIGHT')+ search_ElecLayers(ElecLayersDF,thistd, h, 'PYROLYSIS') + search_ElecLayers(ElecLayersDF,thistd, h, 'PHS_Pin') + search_ElecLayers(ElecLayersDF,thistd, h, 'PHS_Pout') + search_ElecLayers(ElecLayersDF,thistd, h, 'BATT_LI_Pin') + search_ElecLayers(ElecLayersDF,thistd, h, 'BATT_LI_Pout')

            if balance_elec>0:
                IND_COGEN_CORREL.at[(day-1)*24+h-1,cog_col[0]] = 0
                IND_DIRECT_ELEC_CORREL.at[(day-1)*24+h-1,direct_col[0]] = heat_demand_ts_HT.iloc[(day-1)*24+h-1,0]
                count = count + 1
            else:
                IND_COGEN_CORREL.at[(day-1)*24+h-1,cog_col[0]] = heat_demand_ts_HT.iloc[(day-1)*24+h-1,0]
                IND_DIRECT_ELEC_CORREL.at[(day-1)*24+h-1,direct_col[0]] = 0


cogen_correl = IND_COGEN_CORREL.set_index(drange)
ind_elec_correl = IND_DIRECT_ELEC_CORREL.set_index(drange)

heat_demand['BE_IND_DIRECT_ELEC'] = ind_elec_correl['BE_IND_DIRECT_ELEC']
heat_demand['BE_IND_COGEN_GAS'] = cogen_correl['BE_IND_COGEN_GAS']


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

write_csv_files('2015_Correlation', heat_demand,True)


