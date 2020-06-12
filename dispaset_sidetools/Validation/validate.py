import pandas as pd
import glob

#from search import search_YearBalance
#from search import search_Dict_list
#from search import search_Dict_ES2DS
#from search import search_PowerPlant
#from search import from_excel_to_dataFrame
#from search import search_assets
#from search import distri_TD
#from search import get_TD
#from search import get_TDFile

import sys, os
sys.path.append(os.path.abspath(r'../..'))

from dispaset_sidetools import *
import numpy as np
import pandas as pd
import math

from dispaset_sidetools.common import *
from dispaset_sidetools.search import *
from dispaset_sidetools.constants import *

#Select the studied case:

#case_studied = 'Heat_correlation'
#case_studied = 'Heat_hourly_TD'
#case_studied = 'Heat_hourly_TD_FullElecEUD'
#case_studied = 'Heat_hourly_TD_Full_HT'
#case_studied = 'Heat_daily'
#case_studied = 'Heat_hourly_TD_RectifiedPV-DECHP'
#case_studied = 'Heat_hourly_TD_NoSeasonalTS_DHN'
#case_studied = 'Heat_hourly_TD_NoLT'
#case_studied = 'Heat_hourly_TD_NewEUDelec'
#case_studied = 'NoHeat'
#case_studied = 'Heat_hourly_TD_HL1'
#case_studied = 'Heat_hourly_TD_HL100'
#case_studied = 'Heat_hourly_TD_HL150'
#case_studied = 'Heat_hourly_TD_HL250'
#case_studied = 'Heat_hourly_TD_HL300'
#case_studied = 'Heat_hourly_TD_HL365'
#case_studied = '365TDfrom12TD'
#case_studied = 'Heat_hourly_dispatch'
#case_studied = '365TDfrom12TD_NoConstraints'
#case_studied = 'Heat_th'
case_studied = 'FinalCases_BE2015'
#case_studied = 'Heat_th_HS35'
#case_studied = 'Heat_th_dhn_prod_losses'
#case_studied = 'Heat_th_FullBatt'


############################################# Create EnergyScope Elec production yearly profiles #####################################################

#
#
#
#
#
# Inputs :  x = Country studied
#
#
#
#
def get_elec_yearly_profiles(x):
    perc_dhn = perc_dhn_list[countries.index(x)]
    DHN_prod_losses = DHN_Prod_losses_list[countries.index(x)]
    DHN_Sto_losses = DHN_Sto_losses_list[countries.index(x)]
    grid_losses = grid_losses_list[countries.index(x)]

    #tech_of_interest=  ['END_USE','IND_COGEN_GAS','CCGT','PV','WIND','WIND_ONSHORE','WIND_OFFSHORE','HYDRO_DAM','DAM_STORAGE','DAM_STORAGE_Pin','DAM_STORAGE_Pout','HYDRO_RIVER','GEOTHERMAL','DHN_HP_ELEC','DEC_HP_ELEC','IND_DIRECT_ELEC','PHES_Pin','PHES_Pout','PHS_Pin','PHS_Pout','BATT_LI_Pin','BATT_LI_Pout','H2_ELECTROLYSIS']
    tech_of_interest = ['END_USE'] + power_tech + elec_mobi_tech + ['HYDRO_DAM','DAM_STORAGE','DAM_STORAGE_Pin','DAM_STORAGE_Pout','PHES_Pin','PHES_Pout','PHS','PHS_Pin','PHS_Pout','BATT_LI_Pin','BATT_LI_Pout']  # + ['ELECTRICITY']


    #Run this if you want to get the electricity import
    #tech_of_interest = ['ELECTRICITY']

    distriTD = distri_TD(x,n_TD)
    TD_DF = pd.read_csv(input_folder + x + '/' + 'TD_file.csv')
    ElecLayerDF = pd.read_csv(input_folder + x + '/' + 'ElecLayers.txt', delimiter='\t', index_col=0)
    ElecLayerDF = ElecLayerDF.reset_index()
    ElecLayerDF.drop(ElecLayerDF.columns[[-1, ]], axis=1, inplace=True)
    ElecLayer_year = pd.DataFrame(index=range(1,8761),columns=tech_of_interest)
    for day in range(1, 366):
        for h in range(1, 25):
            thistd = get_TD(TD_DF, (day - 1) * 24 + h, n_TD)
            for i in ElecLayerDF.columns:
                if i in tech_of_interest:
                    ElecLayer_year.at[(day - 1) * 24 + h, i] = ElecLayerDF.loc[(thistd-1)*24+h-1,i]*1000
                else:
                    if 'Capitalf' in i:
                        new_i = i.replace('Capitalf','F')
                        if new_i in tech_of_interest:
                            ElecLayer_year.at[(day - 1) * 24 + h, new_i] = ElecLayerDF.loc[(thistd - 1) * 24 + h - 1, i] * 1000

    Elec_Sto = get_DistriStorage(x,'Elec')
    if 'PHS' in ElecLayerDF.columns or 'PHS_Pin' in ElecLayerDF.columns or 'PHES_Pin' in ElecLayerDF.columns:
        try:
            if search_YearBalance(x,'PHS','ELECTRICITY') != 0:
                ElecLayer_year['PHS'] = Elec_Sto['PHS'].multiply(1000)
        except:
            if search_YearBalance(x,'PHES','ELECTRICITY') != 0:
                ElecLayer_year['PHES'] = Elec_Sto['PHES'].multiply(1000)
    if 'BATT_LI' in ElecLayerDF.columns or 'BATT_LI_Pin' in ElecLayerDF.columns:
        if search_YearBalance(x,'BATT_LI','ELECTRICITY') != 0:
            ElecLayer_year['BATT_LI'] = Elec_Sto['BATT_LI'].multiply(1000)
    if 'DAM_STORAGE' in ElecLayerDF.columns or 'DAM_STORAGE_Pin' in ElecLayerDF.columns:
        if search_YearBalance(x,'DAM_STORAGE','ELECTRICITY') != 0 or search_YearBalance(x,'HYDRO_DAM','ELECTRICITY') != 0:
            ElecLayer_year['DAM_STORAGE'] = Elec_Sto['DAM_STORAGE'].multiply(1000)

    ElecLayer_year.to_csv(case_studied + '/ElecLayers_year_'+ case_studied + '_' + x + '.csv')

get_elec_yearly_profiles('BE')


############################################# Create EnergyScope Heat production yearly profiles #####################################################

#
#
#
#
#
# Inputs :  x = Country studied
#
#
#
#
def get_heat_yearly_profiles(x):
    perc_dhn = perc_dhn_list[countries.index(x)]
    DHN_prod_losses = DHN_Prod_losses_list[countries.index(x)]
    DHN_Sto_losses = DHN_Sto_losses_list[countries.index(x)]
    grid_losses = grid_losses_list[countries.index(x)]


    #tech_of_interest=['END_USE','IND_COGEN_GAS','DHN_HP_ELEC','DEC_HP_ELEC','IND_DIRECT_ELEC','IND_BOILER_WOOD','IND_BOILER_WASTE','TS_DHN_DAILY_Pin','TS_DHN_DAILY_Pout','TS_DHN_SEASONAL_Pin','TS_DHN_SEASONAL_Pout','TS_DEC_HP_ELEC_Pin','TS_DEC_HP_ELEC_Pout']
    tech_of_interest = ['END_USE'] + p2h_tech + chp_tech + OtherHeat_tech



    distriTD = distri_TD(x, n_TD)
    TD_DF = pd.read_csv(input_folder + x + '/' + 'TD_file.csv')
    LTLayersDF = pd.read_csv(input_folder + x + '/' + 'LTLayers.txt', delimiter='\t', index_col=0)
    HTLayersDF = pd.read_csv(input_folder + x + '/' + 'HTLayers.txt', delimiter='\t', index_col=0)
    LTLayersDF = LTLayersDF.reset_index()
    HTLayersDF = HTLayersDF.reset_index()


    HeatLayer_year = pd.DataFrame(index=range(1,8761),columns=tech_of_interest + ['END_USE_LT','END_USE_HT'])
    for day in range(1, 366):
        for h in range(1, 25):
            thistd = get_TD(TD_DF, (day - 1) * 24 + h, n_TD)
            for i in HTLayersDF.columns:
                if i in tech_of_interest:
                    if 'END_USE' in i:
                        HeatLayer_year.loc[(day - 1) * 24 + h, 'END_USE_LT'] = LTLayersDF.loc[(thistd - 1) * 24 + h - 1, i] * 1000
                        HeatLayer_year.loc[(day - 1) * 24 + h,  'END_USE_HT'] = HTLayersDF.loc[(thistd-1)*24+h-1,i]*1000
                    if 'IND' in i:
                        HeatLayer_year.loc[(day - 1) * 24 + h, i] = HTLayersDF.loc[(thistd-1)*24+h-1,i]*1000
                    else:
                        HeatLayer_year.loc[(day - 1) * 24 + h, i] = LTLayersDF.loc[(thistd - 1) * 24 + h - 1, i] * 1000

    HeatLayer_year.to_csv(case_studied + '/HeatLayer_year_' + case_studied +  '_' + x + '.csv')
get_heat_yearly_profiles('BE')

########################################################################################################################

# Get total heat produced by "HeatSLack" in EnergyScope
#
#
#
#
#
#
def get_HeatSlack():


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
                try:
                    value_HT = abs(search_YearBalance(Country,y,'HEAT_HIGH_T'))
                    value_LT_DEC = abs(search_YearBalance(Country,y,'HEAT_LOW_T_DECEN'))
                    value_LT_DHN = abs(search_YearBalance(Country,y,'HEAT_LOW_T_DHN'))
                except:
                    print('INFO : ' + y + ' not present in ' + Country)
                techno = y
                HeatSlack_demand.at[Country,techno] = value_HT + value_LT_DEC + value_LT_DHN

                if value_HT > 0:
                    total_HT = total_HT + value_HT
                if value_LT_DEC > 0:
                    total_LT_dec = total_LT_dec + value_LT_DEC
                if value_LT_DHN > 0:
                    total_LT_dhn = total_LT_dhn + value_LT_DHN

                #print(y + ' : ' + ' HT :' + str(value_HT) + ' LT_DEC : ' + str(value_LT_DEC) + ' LT : ' + str(value_LT_DHN)  )

        HeatSlack_demand.at[Country,'TOTAL_HT'] = total_HT
        HeatSlack_demand.at[Country,'TOTAL_LT_DEC'] = total_LT_dec
        HeatSlack_demand.at[Country,'TOTAL_LT_DHN'] = total_LT_dhn
        HeatSlack_demand.at[Country,'TOTAL_LT'] = total_LT_dec + total_LT_dhn
        HeatSlack_demand.at[Country,'TOTAL'] = total_HT + total_LT_dec + total_LT_dhn

    #print(HeatSlack_demand)
    HeatSlack_demand.to_csv('heatslack.csv')
    return HeatSlack_demand

get_HeatSlack()

########################################################################################################################

# function that gives the production in LT and HT heat for specified technologies in Energyscope

def get_ES_heatprod(x,list_tech):
    perc_dhn = perc_dhn_list[countries.index(x)]
    DHN_prod_losses = DHN_Prod_losses_list[countries.index(x)]
    DHN_Sto_losses = DHN_Sto_losses_list[countries.index(x)]
    grid_losses = grid_losses_list[countries.index(x)]

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
            value_HT = search_YearBalance(x,t, 'HEAT_HIGH_T')
            value_LT_DEC = search_YearBalance(x,t, 'HEAT_LOW_T_DECEN')
            value_LT_DHN = search_YearBalance(x,t, 'HEAT_LOW_T_DHN')
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
            value_HT = abs(search_YearBalance(x,t, 'HEAT_HIGH_T'))
            value_LT_DEC = abs(search_YearBalance(x,t, 'HEAT_LOW_T_DECEN'))
            value_LT_DHN = abs(search_YearBalance(x,t, 'HEAT_LOW_T_DHN'))

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

    Heat_prod.to_csv('Heat_prod.csv')
    print(Heat_prod)
    return Heat_prod


list = ['IND_COGEN_GAS','IND_DIRECT_ELEC','DEC_HP_ELEC','DHN_HP_ELEC','IND_BOILER_WOOD','IND_BOILER_WASTE','TS_DEC_HP_ELEC','TS_DHN_SEASONAL']
get_ES_heatprod('BE',chp_tech + p2h_tech+OtherHeat_tech)


########################################################################################################################

#
#
#Function that builds the Sankey Diagram of Dispa-SET.
#
#   Inputs : Flow_Threshold = Minimum flow to be put in Sankey [GWh]
#
#
#

def get_Sankey_DS(x, Flow_Threshold):
    import plotly.graph_objects as go

    Min_Treshold = Flow_Threshold                # Min value to be put on the Sankey [GWh]
    perc_dhn = perc_dhn_list[countries.index(x)]
    DHN_prod_losses = DHN_Prod_losses_list[countries.index(x)]
    DHN_Sto_losses = DHN_Sto_losses_list[countries.index(x)]
    grid_losses = grid_losses_list[countries.index(x)]

    Power = pd.read_csv(case_studied + '/' + 'OutputPower_' + case_studied +'.csv')
    Power = Power.set_index(Power.columns[0])
    Heat = pd.read_csv(case_studied + '/' +'OutputHeat_' + case_studied +'.csv')
    Heat = Heat.set_index(Heat.columns[0])
    HeatSlack = pd.read_csv(case_studied + '/' +'OutputHeatSlack_' + case_studied +'.csv')
    HeatSlack = HeatSlack.set_index(HeatSlack.columns[0])
    StorageInput = pd.read_csv(case_studied + '/' +'OutputStorageInput_' + case_studied +'.csv')
    StorageInput = StorageInput.set_index(StorageInput.columns[0])
    TotalLoadValue = pd.read_csv(case_studied + '/' +'TotalLoadValue'+ '_' + x + '.csv')
    TotalLoadValue = TotalLoadValue.set_index(TotalLoadValue.columns[0])
#    HeatDemand = pd.read_csv(input_folder + 'EUD_HEAT.txt', delimiter='\t', index_col=0)
    HeatDemand = from_excel_to_dataFrame(case_studied + '/' + 'DATA_preprocessing_' + case_studied + '_' + x + '.xlsx','EUD_heat')

    EUD_ELEC = TotalLoadValue.sum(axis=0) / 1000
    EUD_HEAT_LT = HeatDemand[x + '_LT'].sum(axis=0) / 1000
    EUD_HEAT_HT = HeatDemand[x + '_HT'].sum(axis=0) / 1000

    PowColumn = Power.columns
    PowColumn_x = []
    PowerTot = pd.DataFrame(columns=PowColumn)
    for i in PowerTot:
        if ' ' + x + '_' in i:
            PowColumn_x.append(i)
            PowerTot.at[0,i] = Power[i].sum(axis=0) / 1000

    HeatColumn = Heat.columns
    HeatColumn_x = []
    HeatTot = pd.DataFrame(columns=HeatColumn)
    for i in HeatTot:
        if ' ' + x + '_' in i:
            HeatColumn_x.append(i)
            HeatTot.at[0,i] = Heat[i].sum(axis=0) / 1000

    HeatSlackColumn = HeatSlack.columns[1:]
    HeatSlackColumn_x = []
    HeatSlackTot = pd.DataFrame(columns=HeatSlackColumn)
    for i in HeatSlackTot:
        if ' ' + x + '_' in i:
            HeatSlackColumn_x.append(i)
            HeatSlackTot.at[0, i] = HeatSlack[i].sum(axis=0) / 1000

    # Keep only BATT_LI and PHS
    StoColumn = []
    for i in StorageInput.columns:
        if 'BATT_LI' in i or 'PHS' in i or 'PHES' in i:
            if ' ' + x + '_' in i:
                StoColumn.append(i)
    StorageTot = pd.DataFrame(columns=StoColumn)
    for i in StorageTot:
        StorageTot.at[0, i] = StorageInput[i].sum(axis=0) / 1000

    #build labels
    mylabels = ['HEAT_HT','HEAT_LT_DHN','HEAT_LT_DEC', 'EUD_ELEC', 'EUD_LT_DHN', 'EUD_LT_DEC','EUD_HT','P2H','ELECTRICITY','HEATSLACK','OtherFuels']
    FuelLabels = ['BIO','GAS','GEO','HRD','HYD','LIG','NUC','OIL','PEA','SUN','WAT','WIN','WST']
    mylabels.extend(FuelLabels)
    mylabels.extend(PowColumn_x)
    mylabels.extend(HeatColumn_x)
    mylabels.extend(HeatSlackColumn_x)
    mylabels.extend(StoColumn)


    #build links
    mysource = []
    mytarget = []
    myvalue = []

    # STORAGE FLOWS

    ELEC_extract = 0
    EUD_extract = 0
    for i in StorageTot:
        ThisFuel = search_PowerPlant(x,i, 'Fuel')
        if 'BATT' in i:
            ThisSource = 'ELECTRICITY'
            mysource.append(mylabels.index(ThisSource))
            ThisTarget = i
            mytarget.append(mylabels.index(ThisTarget))
            ThisValue = StorageTot.loc[0, i]
            ELEC_extract = ELEC_extract + ThisValue
            myvalue.append(ThisValue)
            ThisSource = i
            mysource.append(mylabels.index(ThisSource))
            ThisTarget = 'EUD_ELEC'
            mytarget.append(mylabels.index(ThisTarget))
            ThisValue = PowerTot.loc[0,i]
            EUD_extract = EUD_extract + ThisValue
            myvalue.append(ThisValue)
        elif 'PHS' in i or 'PHES' in i:
            ThisSource = 'ELECTRICITY'
            mysource.append(mylabels.index(ThisSource))
            ThisTarget = i
            mytarget.append(mylabels.index(ThisTarget))
            ThisValue = StorageTot.loc[0, i]
            ELEC_extract = ELEC_extract + ThisValue
            myvalue.append(ThisValue)
            ThisSource = i
            mysource.append(mylabels.index(ThisSource))
            ThisTarget = 'EUD_ELEC'
            mytarget.append(mylabels.index(ThisTarget))
            ThisValue = PowerTot.loc[0,i]
            EUD_extract = EUD_extract + ThisValue
            myvalue.append(ThisValue)

    # ELECTRICITY FLOWS

    for i in PowColumn_x:
        if 'COGEN' in i:
            ThisFuel = search_PowerPlant(x,i, 'Fuel')
            if ThisFuel in mylabels:
                ThisSource = ThisFuel
            else:
                ThisSource = 'OtherFuels'
            mysource.append(mylabels.index(ThisSource))
            ThisTarget = i
            mytarget.append(mylabels.index(ThisTarget))
            ThisValue = PowerTot.loc[0, i] / search_PowerPlant(x,i, 'Efficiency')
            myvalue.append(ThisValue)

            ThisSource = i
            mysource.append(mylabels.index(ThisSource))
            ThisTarget = 'ELECTRICITY'
            mytarget.append(mylabels.index(ThisTarget))
            ThisValue = PowerTot.loc[0, i]
            myvalue.append(ThisValue)

        elif 'CCGT' in i:
            ThisFuel = search_PowerPlant(x,i, 'Fuel')
            if ThisFuel in mylabels:
                ThisSource = ThisFuel
            else:
                ThisSource = 'OtherFuels'
            mysource.append(mylabels.index(ThisSource))
            ThisTarget = i
            mytarget.append(mylabels.index(ThisTarget))
            ThisValue = PowerTot.loc[0, i] / search_PowerPlant(x,i, 'Efficiency')
            myvalue.append(ThisValue)

            ThisSource = i
            mysource.append(mylabels.index(ThisSource))
            ThisTarget = 'ELECTRICITY'
            mytarget.append(mylabels.index(ThisTarget))
            ThisValue = PowerTot.loc[0, i]
            myvalue.append(ThisValue)

        elif 'BATT' not in i and 'PHS' not in i and 'PHES' not in i:
            ThisFuel = search_PowerPlant(x,i, 'Fuel')
            if ThisFuel in mylabels:
                ThisSource = ThisFuel
            else:
                ThisSource = 'OtherFuels'
            mysource.append(mylabels.index(ThisSource))
            ThisTarget = i
            mytarget.append(mylabels.index(ThisTarget))
            ThisValue = PowerTot.loc[0, i] / search_PowerPlant(x,i, 'Efficiency')
            myvalue.append(ThisValue)

            ThisSource = i
            mysource.append(mylabels.index(ThisSource))
            ThisTarget = 'ELECTRICITY'
            mytarget.append(mylabels.index(ThisTarget))
            ThisValue = PowerTot.loc[0, i]
            myvalue.append(ThisValue)

    # HEAT FLOWS

    for i in HeatColumn_x:
        if 'COGEN' in i:
#            ThisFuel = search_PowerPlant(i, 'Fuel')
#            if ThisFuel in mylabels:
#                ThisSource = ThisFuel
#            else:
#                ThisSource = 'OtherFuels'
#            ThisTarget = i
#            ThisValue = HeatTot.loc[0, i] / search_PowerPlant(i, 'CHPPowerToHeat') / search_PowerPlant(i, 'Efficiency')

            ThisSource = i
            mysource.append(mylabels.index(ThisSource))
            if 'DHN' in i:
                ThisTarget = 'HEAT_LT_DHN'
            elif 'DEC' in i:
                ThisTarget = 'HEAT_LT_DEC'
            else:
                ThisTarget = 'HEAT_HT'
            mytarget.append(mylabels.index(ThisTarget))
            ThisValue = HeatTot.loc[0, i]
            myvalue.append(ThisValue)

        elif 'HP' in i:
            ThisSource = 'ELECTRICITY'
            mysource.append(mylabels.index(ThisSource))
            ThisTarget = i
            mytarget.append(mylabels.index(ThisTarget))
            ThisValue = HeatTot.loc[0, i] / search_PowerPlant(x,i, 'COP')
            myvalue.append(ThisValue)

            ThisSource = i
            mysource.append(mylabels.index(ThisSource))
            if 'DHN' in i:
                ThisTarget = 'HEAT_LT_DHN'
            elif 'DEC' in i:
                ThisTarget = 'HEAT_LT_DEC'
            else:
                ThisTarget = 'HEAT_HT'
            mytarget.append(mylabels.index(ThisTarget))
            ThisValue = HeatTot.loc[0, i]
            myvalue.append(ThisValue)

        elif 'ELEC' in i:
            ThisSource = 'ELECTRICITY'
            mysource.append(mylabels.index(ThisSource))
            ThisTarget = i
            mytarget.append(mylabels.index(ThisTarget))
            ThisValue = HeatTot.loc[0, i] / search_PowerPlant(x,i,'COP')  # Or divide by efficiency ??? IND_DIRECT_ELEC case
            myvalue.append(ThisValue)

            ThisSource = i
            mysource.append(mylabels.index(ThisSource))
            if 'DHN' in i:
                ThisTarget = 'HEAT_LT_DHN'
            elif 'DEC' in i:
                ThisTarget = 'HEAT_LT_DEC'
            else:
                ThisTarget = 'HEAT_HT'
            mytarget.append(mylabels.index(ThisTarget))
            ThisValue = HeatTot.loc[0, i]
            myvalue.append(ThisValue)


        else:
            if "GAS" in i or "CCGT" in i:
                ThisSource = 'GAS'
            else:
                ThisSource = 'ELECTRICITY'

            mysource.append(mylabels.index(ThisSource))
            if 'DHN' in i:
                ThisTarget = 'HEAT_LT_DHN'
            elif 'DEC' in i:
                ThisTarget = 'HEAT_LT_DEC'
            else:
                ThisTarget = 'HEAT_HT'
            mytarget.append(mylabels.index(ThisTarget))
            ThisValue = HeatTot.loc[0, i]
            myvalue.append(ThisValue)

    # HEATSLACK FLOWS

    for i in HeatSlackColumn_x:

        ThisFuel = search_PowerPlant(x,i, 'Fuel')
        if ThisFuel in mylabels:
            ThisSource = ThisFuel
        else:
            ThisSource = 'OtherFuels'
        mysource.append(mylabels.index(ThisSource))
        ThisTarget = 'HEATSLACK'
        mytarget.append(mylabels.index(ThisTarget))
        ThisValue = HeatSlackTot.loc[0, i] / search_PowerPlant(x,i, 'Efficiency')
        myvalue.append(ThisValue)

        ThisSource = 'HEATSLACK'
        mysource.append(mylabels.index(ThisSource))
        if 'DHN' in i:
            ThisTarget = 'HEAT_LT_DHN'
        elif 'DEC' in i:
            ThisTarget = 'HEAT_LT_DEC'
        else:
            ThisTarget = 'HEAT_HT'
        mytarget.append(mylabels.index(ThisTarget))
        ThisValue = HeatSlackTot.loc[0, i]
        myvalue.append(ThisValue)

    # Add the ELEC_EUD
    mysource.append(mylabels.index('ELECTRICITY'))
    mytarget.append(mylabels.index('EUD_ELEC'))
    myvalue.append(float(EUD_ELEC) - ELEC_extract)



    #Only keep on the Sankey values <= 10 GWh
    vect_length = len(myvalue)
    n_elem_removed = 0
    for ind in range(0,vect_length):
        i = ind-n_elem_removed
        if myvalue[i] < Min_Treshold:
            print(str( mylabels[mysource[i]]) + ' to ' + str(mylabels[mytarget[i]]) + ' removed : ' + str(myvalue[i]) + ' GWh')
            myvalue = myvalue[:i] + myvalue[i+1:]
            mysource = mysource[:i] + mysource[i+1:]
            mytarget = mytarget[:i] + mytarget[i+1:]
            vect_length = vect_length-1
            n_elem_removed = n_elem_removed+1


    #Add different colours:
    mylinkcolor = []
    vect_length = len(myvalue)
    for i in range(0,vect_length):
        if mylabels[mytarget[i]] == 'ELECTRICITY' or mylabels[mysource[i]] == 'ELECTRICITY' or mylabels[mytarget[i]] == 'EUD_ELEC':
            mylinkcolor.append('lightskyblue')
        elif mylabels[mysource[i]] == 'WAT':
            mylinkcolor.append('royalblue')
        elif mylabels[mysource[i]] == 'SUN':
            mylinkcolor.append('chartreuse')
        elif mylabels[mysource[i]] == 'WIN':
            mylinkcolor.append('lightgreen')
        elif mylabels[mytarget[i]] == 'HEAT_HT':
            mylinkcolor.append('coral')
        elif mylabels[mytarget[i]] == 'HEAT_LT_DEC' or mylabels[mytarget[i]] == 'HEAT_LT_DHN':
            mylinkcolor.append('darksalmon')
        elif mylabels[mysource[i]] == 'GAS':
            mylinkcolor.append('orange')
        else:
            mylinkcolor.append('grey')

    fig = go.Figure(data=[go.Sankey(
        node = dict(
        pad = 20,
        thickness = 15,
        line = dict(color = "black", width = 0.5),
        label = mylabels,
        color = 'lightgray'
        ),
        link = dict(
        source = mysource,
        target = mytarget,
        value = myvalue,
        color = mylinkcolor
    ))])

    fig.update_layout(dict(
    title = "Dispa-SET Sankey Diagram" + ' zone ' + x +  " : case " + case_studied +  " (figures in GWh)",
    height = 800,
    font = dict(
      size = 9
    ),
))

#    title_text = "Sankey Diagram : figures in GWh", font_size = 10
    fig.show()

#get_Sankey_DS('BE',10)


########################################################################################################################

#
#
#Function that builds the Sankey Diagram of Dispa-SET.
#
#   inputs :   includemob = True if include mobility, False if not
#              Flow_Treshold : minimum flow value to be put on the Sankey [GWh]
#
#
#

def get_Sankey_ES(x,includemob,Flow_Treshold):
    import plotly.graph_objects as go

    mobilityincluded = includemob           # Include Mobility in Sankey
    Min_Treshold = Flow_Treshold            # Min flow to be put on the Sankey [GWh]
    perc_dhn = perc_dhn_list[countries.index(x)]
    DHN_prod_losses = DHN_Prod_losses_list[countries.index(x)]
    DHN_Sto_losses = DHN_Sto_losses_list[countries.index(x)]
    grid_losses = grid_losses_list[countries.index(x)]

    TotalLoadValue = from_excel_to_dataFrame(case_studied + '/' + 'DATA_preprocessing_' + case_studied + '_' + x +'.xlsx','EUD_elec')
    HeatDemand = from_excel_to_dataFrame(case_studied + '/' + 'DATA_preprocessing_' + case_studied + '_' + x +'.xlsx','EUD_heat')

    EUD_ELEC = TotalLoadValue.sum(axis=0) / 1000
    EUD_HEAT_LT = HeatDemand[x + '_LT'].sum(axis=0) / 1000
    EUD_HEAT_HT = HeatDemand[x + '_HT'].sum(axis=0) / 1000

    ES_Output_Power = pd.read_csv(case_studied + '/' +'ElecLayers_year_' + case_studied + '_' + x + '.csv')
    ES_Output_Power = ES_Output_Power.set_index(ES_Output_Power.columns[0])
    ES_Output_Heat = pd.read_csv(case_studied + '/' +'HeatLayer_year_' + case_studied + '_' + x + '.csv')
    ES_Output_Heat = ES_Output_Heat.set_index(ES_Output_Heat.columns[0])
    ES_efficienies = from_excel_to_dataFrame(case_studied + '/' + 'DATA_preprocessing_' + case_studied + '_' + x + '.xlsx','layers_in_out')
    ES_efficienies = ES_efficienies.set_index(ES_efficienies.columns[0])

    YearBal_DF = pd.read_csv(input_folder + x + '/' + 'YearBalance.txt', delimiter= '\t', index_col=0)

    PowColumn = []
    HeatColumn = []
    MobColumn = []
    StoColumn = []
    H2Column = []

    for i in YearBal_DF.index:
        i = i.strip(' ')
        if i in power_tech:
            PowColumn.append(i)
        if i in p2h_tech or i in chp_tech or i in OtherHeat_tech:
            HeatColumn.append(i)
        if i in elec_mobi_tech or i in OtherMob_tech:
            MobColumn.append(i)
        if i in storage_tech:
            StoColumn.append(i)
        if i in H2_tech:
            H2Column.append(i)

    #build labels
    mylabels = ['ELECTRICITY','HEAT_HIGH_T','HEAT_LOW_T_DHN','HEAT_LOW_T_DECEN', 'MOB_PUBLIC', 'MOB_PRIVATE', 'MOB_FREIGHT','NON_ENERGY','EUD_ELEC','H2']
    FuelLabels = ['GASOLINE','DIESEL','BIOETHANOL','BIODIESEL','LFO','NG','SLF','WOOD','WET_BIOMASS','COAL','URANIUM','WASTE','H2','RES_WIND','RES_SOLAR','RES_HYDRO','RES_GEO']
    mylabels.extend(FuelLabels)
    mylabels.extend(PowColumn)
    mylabels.extend(HeatColumn)
    mylabels.extend(MobColumn)
    mylabels.extend(StoColumn)
    mylabels.extend(H2Column)

    ########## Production per Unit DataFrame ########################################

    df_prod = pd.DataFrame(index=['Production per unit [GWh]:'], columns=['EnergyScope'])

    df_prod.at['Production per unit [GWh]:', 'EnergyScope'] = ' '

    for i in StoColumn:
        if 'DHN' in i:
            df_prod.at[i + '_Pin', 'EnergyScope'] = -ES_Output_Heat[i + '_Pin'].sum(axis=0) / 1000
            df_prod.at[i + '_Pout', 'EnergyScope'] = ES_Output_Heat[i + '_Pout'].sum(axis=0) / 1000

        elif 'DEC' in i:
            df_prod.at[i + '_Pin', 'EnergyScope'] = -ES_Output_Heat[i + '_Pin'].sum(axis=0) / 1000
            df_prod.at[i + '_Pout', 'EnergyScope'] = ES_Output_Heat[i + '_Pout'].sum(axis=0) / 1000
        elif 'IND' in i:
            df_prod.at[i + '_Pin', 'EnergyScope'] = -ES_Output_Heat[i + '_Pin'].sum(axis=0) / 1000
            df_prod.at[i + '_Pout', 'EnergyScope'] = ES_Output_Heat[i + '_Pout'].sum(axis=0) / 1000
        else:
            df_prod.at[i + '_Pin', 'EnergyScope'] = -ES_Output_Power[i + '_Pin'].sum(axis=0) / 1000
            df_prod.at[i + '_Pout', 'EnergyScope'] = ES_Output_Power[i + '_Pout'].sum(axis=0) / 1000
    for i in PowColumn:
        if 'COGEN' in i:
            df_prod.at[i+ '_Elec', 'EnergyScope'] = search_YearBalance(x,i, 'ELECTRICITY')
        else:
            df_prod.at[i, 'EnergyScope'] = search_YearBalance(x,i, 'ELECTRICITY')
    for i in HeatColumn:
        if 'IND' in i:
            if 'COGEN' in i:
                df_prod.at[i + '_Heat', 'EnergyScope'] = search_YearBalance(x,i, 'HEAT_HIGH_T')
            else:
               df_prod.at[i, 'EnergyScope'] = search_YearBalance(x,i,'HEAT_HIGH_T')
        elif 'DHN' in i:
            if 'COGEN' in i:
                df_prod.at[i + '_Heat', 'EnergyScope'] = search_YearBalance(x, i, 'HEAT_LOW_T_DHN')
            else:
                df_prod.at[i, 'EnergyScope'] = search_YearBalance(x,i,'HEAT_LOW_T_DHN')
        else:
            if 'COGEN' in i:
                df_prod.at[i + '_Heat' , 'EnergyScope'] = search_YearBalance(x, i, 'HEAT_LOW_T_DECEN')
            else:
                df_prod.at[i, 'EnergyScope'] = search_YearBalance(x,i,'HEAT_LOW_T_DECEN')
    for i in MobColumn:
        if 'PUB' in i or 'TRAMWAY' in i or 'BUS_COACH_HYDIESEL' in i:
            df_prod.at[i, 'EnergyScope'] = search_YearBalance(x,i, 'MOB_PUBLIC')
        elif 'REIGHT' in i or 'TRUCK_NG' in i:
            if 'TRAIN' in i:
                df_prod.at[i, 'EnergyScope'] = search_YearBalance(x,i, 'MOB_FREIGHT_RAIL')
            elif 'BOAT' in i:
                df_prod.at[i, 'EnergyScope'] = search_YearBalance(x,i, 'MOB_FREIGHT_BOAT')
            else:
                df_prod.at[i, 'EnergyScope'] = search_YearBalance(x,i, 'MOB_FREIGHT_ROAD')
        else:
            df_prod.at[i, 'EnergyScope'] = search_YearBalance(x,i, 'MOB_PRIVATE')

    #build links
    mysource = []
    mytarget = []
    myvalue = []

    # STORAGE FLOWS

    ELEC_extract = 0
    EUD_extract = 0
    DHN_extract = 0
    DEC_extract = 0
    IND_extract = 0
    EUD_IND_extract = 0
    EUD_DHN_extract = 0
    EUD_DEC_extract = 0
    for i in StoColumn:
        ThisFuel = mapping['FUEL_ES'][i]
        if 'BATT' in i:
            ThisSource = 'ELECTRICITY'
            mysource.append(mylabels.index(ThisSource))
            ThisTarget = i
            mytarget.append(mylabels.index(ThisTarget))
            ThisValue = df_prod.loc[i+ '_Pin','EnergyScope']
            ELEC_extract = ELEC_extract + ThisValue
            myvalue.append(ThisValue)
            ThisSource = i
            mysource.append(mylabels.index(ThisSource))
            ThisTarget = 'EUD_ELEC'
            mytarget.append(mylabels.index(ThisTarget))
            ThisValue = df_prod.loc[i+ '_Pout','EnergyScope']
            EUD_extract = EUD_extract + ThisValue
            myvalue.append(ThisValue)
        elif 'PHS' in i or 'PHES' in i:
            ThisSource = 'ELECTRICITY'
            mysource.append(mylabels.index(ThisSource))
            ThisTarget = i
            mytarget.append(mylabels.index(ThisTarget))
            ThisValue = df_prod.loc[i + '_Pin', 'EnergyScope']
            ELEC_extract = ELEC_extract + ThisValue
            myvalue.append(ThisValue)
            ThisSource = i
            mysource.append(mylabels.index(ThisSource))
            ThisTarget = 'EUD_ELEC'
            mytarget.append(mylabels.index(ThisTarget))
            ThisValue = df_prod.loc[i + '_Pout', 'EnergyScope']
            EUD_extract = EUD_extract + ThisValue
            myvalue.append(ThisValue)
        elif 'DAM' in i:
            ThisSource = ThisFuel
            mysource.append(mylabels.index(ThisSource))
            ThisTarget = i
            mytarget.append(mylabels.index(ThisTarget))
            ThisValue = df_prod.loc[i + '_Pout', 'EnergyScope']
            myvalue.append(ThisValue)
            ThisSource = i
            mysource.append(mylabels.index(ThisSource))
            ThisTarget = 'ELECTRICITY'
            mytarget.append(mylabels.index(ThisTarget))
            ThisValue = df_prod.loc[i + '_Pout', 'EnergyScope']
            myvalue.append(ThisValue)

        '''
        elif 'TS' in i:
            if 'DHN' in i:
                ThisSource = 'DHN_HP_ELEC'
                mysource.append(mylabels.index(ThisSource))
                ThisTarget = i
                mytarget.append(mylabels.index(ThisTarget))
                ThisValue = df_prod.loc[i + '_Pin', 'EnergyScope']
                DHN_extract = DHN_extract + ThisValue
                myvalue.append(ThisValue)
                ThisSource = i
                mysource.append(mylabels.index(ThisSource))
                ThisTarget = 'HEAT_LOW_T_DHN'
                mytarget.append(mylabels.index(ThisTarget))
                ThisValue = df_prod.loc[i + '_Pout', 'EnergyScope']
                EUD_DHN_extract = EUD_DHN_extract + ThisValue
                myvalue.append(ThisValue)
            elif 'DEC' in i:
                ThisSource = 'DEC_HP_ELEC'
                mysource.append(mylabels.index(ThisSource))
                ThisTarget = i
                mytarget.append(mylabels.index(ThisTarget))
                ThisValue = df_prod.loc[i + '_Pin', 'EnergyScope']
                DHN_extract = DHN_extract + ThisValue
                myvalue.append(ThisValue)
                ThisSource = i
                mysource.append(mylabels.index(ThisSource))
                ThisTarget = 'HEAT_LOW_T_DECEN'
                mytarget.append(mylabels.index(ThisTarget))
                ThisValue = df_prod.loc[i + '_Pout', 'EnergyScope']
                EUD_DEC_extract = EUD_DEC_extract + ThisValue
                myvalue.append(ThisValue)
            else:
                ThisSource = 'IND_COGEN_GAS'
                mysource.append(mylabels.index(ThisSource))
                ThisTarget = i
                mytarget.append(mylabels.index(ThisTarget))
                ThisValue = df_prod.loc[i + '_Pin', 'EnergyScope']
                IND_extract = IND_extract + ThisValue
                myvalue.append(ThisValue)
                ThisSource = i
                mysource.append(mylabels.index(ThisSource))
                ThisTarget = 'HEAT_HIGH_T'
                mytarget.append(mylabels.index(ThisTarget))
                ThisValue = df_prod.loc[i + '_Pout', 'EnergyScope']
                EUD_IND_extract = EUD_IND_extract + ThisValue
                myvalue.append(ThisValue)
        '''


    # ELECTRICITY FLOWS

    for i in PowColumn:
        if 'COGEN' in i:
            ThisFuel = mapping['FUEL_ES'][i]
            if ThisFuel in mylabels:
                ThisSource = ThisFuel
            else:
                ThisSource = 'OtherFuels'
            mysource.append(mylabels.index(ThisSource))
            ThisTarget = i
            mytarget.append(mylabels.index(ThisTarget))
            if 'Capitalf' in i:
                new_i = i.replace('Capitalf','F')
                ThisValue = df_prod.loc[i + '_Elec', 'EnergyScope'] / abs(ES_efficienies.loc[new_i, 'ELECTRICITY'] / ES_efficienies.loc[new_i, ThisFuel])
            else:
                ThisValue = df_prod.loc[i + '_Elec','EnergyScope'] / abs(ES_efficienies.loc[i,'ELECTRICITY']/ES_efficienies.loc[i,ThisFuel])
            myvalue.append(ThisValue)

            ThisSource = i
            mysource.append(mylabels.index(ThisSource))
            ThisTarget = 'ELECTRICITY'
            mytarget.append(mylabels.index(ThisTarget))
            ThisValue = df_prod.loc[i + '_Elec','EnergyScope']
            myvalue.append(ThisValue)

        elif 'CCGT' in i:
            ThisFuel = mapping['FUEL_ES'][i]
            if ThisFuel in mylabels:
                ThisSource = ThisFuel
            else:
                ThisSource = 'OtherFuels'
            mysource.append(mylabels.index(ThisSource))
            ThisTarget = i
            mytarget.append(mylabels.index(ThisTarget))
            if 'Capitalf' in i:
                new_i = i.replace('Capitalf','F')
                ThisValue = df_prod.loc[i, 'EnergyScope'] / abs(ES_efficienies.loc[new_i, 'ELECTRICITY'] / ES_efficienies.loc[new_i, ThisFuel])
            else:
                ThisValue = df_prod.loc[i,'EnergyScope'] / abs(ES_efficienies.loc[i,'ELECTRICITY']/ES_efficienies.loc[i,ThisFuel])
            myvalue.append(ThisValue)

            ThisSource = i
            mysource.append(mylabels.index(ThisSource))
            ThisTarget = 'ELECTRICITY'
            mytarget.append(mylabels.index(ThisTarget))
            ThisValue = df_prod.loc[i,'EnergyScope']
            myvalue.append(ThisValue)

        else:
            ThisFuel = mapping['FUEL_ES'][i]
            if ThisFuel in mylabels:
                ThisSource = ThisFuel
            else:
                ThisSource = 'OtherFuels'
            mysource.append(mylabels.index(ThisSource))
            ThisTarget = i
            mytarget.append(mylabels.index(ThisTarget))
            if 'Capitalf' in i:
                new_i = i.replace('Capitalf','F')
                ThisValue = df_prod.loc[i, 'EnergyScope'] / abs(ES_efficienies.loc[new_i, 'ELECTRICITY'] / ES_efficienies.loc[new_i, ThisFuel])
            else:
                ThisValue = df_prod.loc[i,'EnergyScope'] / abs(ES_efficienies.loc[i,'ELECTRICITY']/ES_efficienies.loc[i,ThisFuel])
            myvalue.append(ThisValue)

            ThisSource = i
            mysource.append(mylabels.index(ThisSource))
            ThisTarget = 'ELECTRICITY'
            mytarget.append(mylabels.index(ThisTarget))
            ThisValue = df_prod.loc[i,'EnergyScope']
            myvalue.append(ThisValue)

    # HEAT FLOWS
    for i in HeatColumn:
        if 'COGEN' in i:
            ThisSource = i
            mysource.append(mylabels.index(ThisSource))
            if 'DHN' in i:
                ThisTarget = 'HEAT_LOW_T_DHN'
            elif 'DEC' in i:
                ThisTarget = 'HEAT_LOW_T_DECEN'
            else:
                ThisTarget = 'HEAT_HIGH_T'
            mytarget.append(mylabels.index(ThisTarget))
            try:
                ThisValue = df_prod.loc[i+'_Heat','EnergyScope']
            except:
                print('INFO : ' + i + ' not used in ' + x)
            myvalue.append(ThisValue)

        elif 'HP' in i:
            ThisSource = 'ELECTRICITY'
            mysource.append(mylabels.index(ThisSource))
            ThisTarget = i
            mytarget.append(mylabels.index(ThisTarget))
            if 'DHN' in i:
                ThisValue = df_prod.loc[i,'EnergyScope'] / abs(ES_efficienies.loc[i,'HEAT_LOW_T_DHN']/ES_efficienies.loc[i,'ELECTRICITY'])
            elif 'DEC' in i:
                ThisValue = df_prod.loc[i,'EnergyScope'] / abs(ES_efficienies.loc[i,'HEAT_LOW_T_DECEN']/ES_efficienies.loc[i,'ELECTRICITY'])
            else:
                ThisValue = df_prod.loc[i, 'EnergyScope'] / abs(ES_efficienies.loc[i, 'HEAT_HIGH_T'] / ES_efficienies.loc[i, 'ELECTRICITY'])
            myvalue.append(ThisValue)

            ThisSource = i
            mysource.append(mylabels.index(ThisSource))
            if 'DHN' in i:
                ThisTarget = 'HEAT_LOW_T_DHN'
                ThisValue = df_prod.loc[i,'EnergyScope']
            elif 'DEC' in i:
                ThisTarget = 'HEAT_LOW_T_DECEN'
                ThisValue = df_prod.loc[i,'EnergyScope']
            else:
                ThisTarget = 'HEAT_HIGH_T'
                ThisValue = df_prod.loc[i,'EnergyScope']
            mytarget.append(mylabels.index(ThisTarget))
            myvalue.append(ThisValue)

        elif 'ELEC' in i:
            ThisSource = 'ELECTRICITY'
            mysource.append(mylabels.index(ThisSource))
            ThisTarget = i
            mytarget.append(mylabels.index(ThisTarget))
            if 'DHN' in i:
                ThisValue = df_prod.loc[i, 'EnergyScope'] / abs(ES_efficienies.loc[i, 'HEAT_LOW_T_DHN'] / ES_efficienies.loc[i, 'ELECTRICITY'])
            elif 'DEC' in i:
                ThisValue = df_prod.loc[i, 'EnergyScope'] / abs(ES_efficienies.loc[i, 'HEAT_LOW_T_DECEN'] / ES_efficienies.loc[i, 'ELECTRICITY'])
            else:
                ThisValue = df_prod.loc[i, 'EnergyScope'] / abs(ES_efficienies.loc[i, 'HEAT_HIGH_T'] / ES_efficienies.loc[i, 'ELECTRICITY'])

            myvalue.append(ThisValue)

            ThisSource = i
            mysource.append(mylabels.index(ThisSource))
            if 'DHN' in i:
                ThisTarget = 'HEAT_LOW_T_DHN'
            elif 'DEC' in i:
                ThisTarget = 'HEAT_LOW_T_DECEN'
            else:
                ThisTarget = 'HEAT_HIGH_T'
            mytarget.append(mylabels.index(ThisTarget))
            ThisValue = df_prod.loc[i,'EnergyScope']
            myvalue.append(ThisValue)


        else:
            ThisFuel = mapping['FUEL_ES'][i]
            if ThisFuel in mylabels:
                ThisSource = ThisFuel
            else:
                ThisSource = 'OtherFuels'
            mysource.append(mylabels.index(ThisSource))
            ThisTarget = i
            mytarget.append(mylabels.index(ThisTarget))
            if 'DHN' in i:
                ThisValue = df_prod.loc[i, 'EnergyScope'] / abs(ES_efficienies.loc[i, 'HEAT_LOW_T_DHN'] / ES_efficienies.loc[i, ThisSource])
            elif 'DEC' in i:
                ThisValue = df_prod.loc[i, 'EnergyScope'] / abs(ES_efficienies.loc[i, 'HEAT_LOW_T_DECEN'] / ES_efficienies.loc[i, ThisSource])
            else:
                ThisValue = df_prod.loc[i, 'EnergyScope'] / abs(ES_efficienies.loc[i, 'HEAT_HIGH_T'] / ES_efficienies.loc[i, ThisSource])
            myvalue.append(ThisValue)

            ThisSource = i
            mysource.append(mylabels.index(ThisSource))
            if 'DHN' in i:
                ThisTarget = 'HEAT_LOW_T_DHN'
            elif 'DEC' in i:
                ThisTarget = 'HEAT_LOW_T_DECEN'
            else:
                ThisTarget = 'HEAT_HIGH_T'
            mytarget.append(mylabels.index(ThisTarget))
            ThisValue = df_prod.loc[i,'EnergyScope']
            myvalue.append(ThisValue)

    # Mobility flows
    if mobilityincluded == True:
        for i in MobColumn:
            if i in elec_mobi_tech:
                ThisSource = 'ELECTRICITY'
                mysource.append(mylabels.index(ThisSource))
                if 'Capitalf' in i:
                    thistech = i.replace('Capitalf','F')
                    ThisValue = df_prod.loc[i, 'EnergyScope'] * abs(ES_efficienies.loc[thistech, 'ELECTRICITY'])
                else:
                    ThisValue = df_prod.loc[i, 'EnergyScope'] * abs(ES_efficienies.loc[i, 'ELECTRICITY'])
                myvalue.append(ThisValue)
            elif 'UEL_CELL' in i:
                ThisSource = 'H2'
                mysource.append(mylabels.index(ThisSource))
                ThisValue = abs(search_YearBalance(x,i,'H2'))
                myvalue.append(ThisValue)
            else:
                if 'CAR_HEV' in i:
                    ThisSource = 'GASOLINE'
                elif 'DIESEL' in i:
                    ThisSource = 'DIESEL'
                elif 'NG' in i:
                    ThisSource = 'NG'
                else:
                    ThisFuel = mapping['FUEL_ES'][i]
                    if ThisFuel in mylabels:
                        ThisSource = ThisFuel
                    else:
                        ThisSource = 'OtherFuels'
                mysource.append(mylabels.index(ThisSource))

                if 'Capitalf' in i:
                    thistech = i.replace('Capitalf','F')
                    ThisValue = df_prod.loc[i,'EnergyScope'] * abs(ES_efficienies.loc[thistech,ThisSource])
                else:
                    ThisValue = df_prod.loc[i, 'EnergyScope'] * abs(ES_efficienies.loc[i,ThisSource])
                myvalue.append(ThisValue)

            if 'PUB' in i:
                ThisTarget = 'MOB_PUBLIC'
            elif 'REIGHT' in i:
                ThisTarget = 'MOB_FREIGHT'
            else:
                ThisTarget = 'MOB_PRIVATE'
            mytarget.append(mylabels.index(ThisTarget))

    # H2 flows

    for i in H2Column:
        if 'ELECTROLYSIS' in i:
            ThisSource = 'ELECTRICITY'
            mysource.append(mylabels.index(ThisSource))
            ThisValue = abs(search_YearBalance(x,i, 'ELECTRICITY'))
            myvalue.append(ThisValue)
            ThisTarget = 'H2'
            mytarget.append(mylabels.index(ThisTarget))
        elif 'H2_NG' in i:
            ThisSource = 'NG'
            mysource.append(mylabels.index(ThisSource))
            ThisValue = abs(search_YearBalance(x,i, 'NG'))
            myvalue.append(ThisValue)
            ThisTarget = 'H2'
            mytarget.append(mylabels.index(ThisTarget))


    # Add the ELEC_EUD
    mysource.append(mylabels.index('ELECTRICITY'))
    mytarget.append(mylabels.index('EUD_ELEC'))
    myvalue.append(float(EUD_ELEC) - ELEC_extract)



    #Only keep on the Sankey values <= 10 GWh
    vect_length = len(myvalue)
    n_elem_removed = 0
    for ind in range(0,vect_length):
        i = ind-n_elem_removed
        if myvalue[i] < Min_Treshold:
            print(str( mylabels[mysource[i]]) + ' to ' + str(mylabels[mytarget[i]]) + ' removed : ' + str(myvalue[i]) + ' GWh')
            myvalue = myvalue[:i] + myvalue[i+1:]
            mysource = mysource[:i] + mysource[i+1:]
            mytarget = mytarget[:i] + mytarget[i+1:]
            vect_length = vect_length-1
            n_elem_removed = n_elem_removed+1


    #Add different colours:
    mylinkcolor = []
    vect_length = len(myvalue)
    for i in range(0,vect_length):
        if mylabels[mytarget[i]] == 'MOB_PRIVATE' or mylabels[mytarget[i]] == 'MOB_PUBLIC' or mylabels[mytarget[i]] == 'MOB_FREIGHT':
            mylinkcolor.append('lightgrey')
        elif mylabels[mytarget[i]] == 'ELECTRICITY' or mylabels[mysource[i]] == 'ELECTRICITY' or mylabels[mytarget[i]] == 'EUD_ELEC':
            mylinkcolor.append('lightskyblue')
        elif mylabels[mysource[i]] == 'RES_HYDRO':
            mylinkcolor.append('royalblue')
        elif mylabels[mysource[i]] == 'RES_SOLAR':
            mylinkcolor.append('chartreuse')
        elif mylabels[mysource[i]] == 'RES_WIND':
            mylinkcolor.append('lightgreen')
        elif mylabels[mysource[i]] == 'WOOD':
            mylinkcolor.append('darkgreen')
        elif mylabels[mysource[i]] == 'WASTE':
            mylinkcolor.append('goldenrod')
        elif mylabels[mytarget[i]] == 'HEAT_HIGH_T':
            mylinkcolor.append('coral')
        elif mylabels[mytarget[i]] == 'HEAT_LOW_T_DECEN' or mylabels[mytarget[i]] == 'HEAT_LOW_T_DHN':
            mylinkcolor.append('darksalmon')
        elif mylabels[mysource[i]] == 'NG':
            mylinkcolor.append('orange')
        else:
            mylinkcolor.append('grey')

    for i in range(len(mylabels)):
        if 'Capitalf' in mylabels[i]:
            mylabels[i] = mylabels[i].replace('Capitalf','F')

    fig = go.Figure(data=[go.Sankey(
        node = dict(
        pad = 20,
        thickness = 15,
        line = dict(color = "black", width = 0.5),
        label = mylabels,
        color = 'lightgray'
        ),
        link = dict(
        source = mysource,
        target = mytarget,
        value = myvalue,
        color = mylinkcolor
    ))])

    fig.update_layout(dict(
    title = "EnergyScope Sankey Diagram zone " + x + " : case " + case_studied +  " (figures in GWh)",
    height = 800,
    font = dict(
      size = 9
    ),
))

#    title_text = "Sankey Diagram : figures in GWh", font_size = 10
    fig.show()

#get_Sankey_ES('BE',True,7)

########################################################################################################################

# function that compares the demands/productions, results between ES and DS
#
#
# Inputs :  x = Country studied
#           n_th_version = true if the new Dispa-SET heat management has been used.
#
#
#
def get_results_comparison(x,n_th_version):

    #ATTENTION : verify the files in the Inputs folder are the good ones (e.g. Assets, YearBalance,...)
    perc_dhn = perc_dhn_list[countries.index(x)]
    DHN_prod_losses = DHN_Prod_losses_list[countries.index(x)]
    DHN_Sto_losses = DHN_Sto_losses_list[countries.index(x)]
    grid_losses = grid_losses_list[countries.index(x)]


    DS_Output_Power = pd.read_csv(case_studied + '/' + 'OutputPower_' + case_studied +'.csv')
    DS_Output_Power = DS_Output_Power.set_index(DS_Output_Power.columns[0])
    DS_Output_Heat = pd.read_csv(case_studied + '/' +'OutputHeat_' + case_studied +'.csv')
    DS_Output_Heat = DS_Output_Heat.set_index(DS_Output_Heat.columns[0])
    DS_Output_HeatSlack = pd.read_csv(case_studied + '/' +'OutputHeatSlack_' + case_studied +'.csv')
    DS_Output_HeatSlack = DS_Output_HeatSlack.set_index(DS_Output_HeatSlack.columns[0])
    DS_Output_StorageInput = pd.read_csv(case_studied + '/' +'OutputStorageInput_' + case_studied +'.csv')
    DS_Output_StorageInput = DS_Output_StorageInput.set_index(DS_Output_StorageInput.columns[0])
    DS_Output_StorageLevel = pd.read_csv(case_studied + '/' +'OutputStorageLevel_' + case_studied +'.csv')
    DS_Output_StorageLevel = DS_Output_StorageLevel.set_index(DS_Output_StorageLevel.columns[0])

    DS_Input_Power = pd.read_csv(case_studied + '/' +'TotalLoadValue' + '_' + x + '.csv')
    DS_Input_Power = DS_Input_Power.set_index(DS_Input_Power.columns[0])
    if n_th_version:
        DS_Input_Heat = pd.read_csv(case_studied + '/' + 'HeatDemand_' + case_studied + '_' + x + '.csv')
    else:
        DS_Input_Heat = pd.read_csv(case_studied + '/' + 'HeatDemand_' + case_studied +'_'+ x + '.csv')
        DS_Input_Heat = DS_Input_Heat.set_index(DS_Input_Heat.columns[0])
    DS_PowerPlants = pd.read_csv(case_studied + '/' + 'PowerPlants' + '_' + x + '.csv')
    DS_PowerPlants = DS_PowerPlants.set_index(DS_PowerPlants.columns[0])

    ES_Input_Power = from_excel_to_dataFrame(input_folder + x + '/' + 'DATA_preprocessing.xlsx', 'EUD_elec')
    ES_Input_Heat = from_excel_to_dataFrame(input_folder + x + '/' + 'DATA_preprocessing.xlsx', 'EUD_heat')
    ES_Input_AvailFactors = from_excel_to_dataFrame(input_folder + x + '/' + 'DATA_preprocessing.xlsx', 'AvailabilityFactors')
    ES_Output_Power = pd.read_csv(case_studied + '/' +'ElecLayers_year_' + case_studied + '_' + x +'.csv')
    ES_Output_Power = ES_Output_Power.set_index(ES_Output_Power.columns[0])
    ES_Output_Heat = pd.read_csv(case_studied + '/' +'HeatLayer_year_' + case_studied + '_' + x +'.csv')
    ES_Output_Heat = ES_Output_Heat.set_index(ES_Output_Heat.columns[0])
    YearBal_DF_index = []
    YearBal_DF = pd.read_csv(input_folder + x + '/' + 'YearBalance.txt', delimiter='\t', index_col=0)
    for i in YearBal_DF.index:
        item = i.strip(' ')
        YearBal_DF_index.append(item)

    #change _DS_Output_Power column names
    mylist = []
    for name in DS_Output_Power.columns:
        name = ''.join(c for c in name if c not in '-(){}<>[], ')
        if 'H2' not in name:
            name = ''.join([i for i in name if not i.isdigit()])
        else:
            offset = name.find('H2')-3
            name = name[offset:]
        mylist.append(name)
    DS_Output_Power.columns = mylist

    #change _DS_Output_Heat column names
    mylist_h = []
    for name in DS_Output_Heat.columns:
        name = ''.join(c for c in name if c not in '-(){}<>[], ')
        name = ''.join([i for i in name if not i.isdigit()])
        mylist_h.append(name)
    DS_Output_Heat.columns = mylist_h

    #change _DS_Output_StorageLevel column names
    mylist_sto_lev = []
    for name in DS_Output_StorageLevel.columns:
        name = ''.join(c for c in name if c not in '-(){}<>[], ')
        name = ''.join([i for i in name if not i.isdigit()])
        mylist_sto_lev.append(name)
    DS_Output_StorageLevel.columns = mylist_sto_lev

    #change _DS_Output_StorageInput column names
    mylist_sto_in = []
    for name in DS_Output_StorageInput.columns:
        name = ''.join(c for c in name if c not in '-(){}<>[], ')
        name = ''.join([i for i in name if not i.isdigit()])
        mylist_sto_in.append(name)
    DS_Output_StorageInput.columns = mylist_sto_in

    comp_elements = ['Elec / Heat demand / prod [GWh]:','Total_Elec_Demand','Total_Elec_Mobility','Total_Elec_Prod', 'Total_LT_DHN_Demand', 'Total_LT_DHN_Prod','HeatSlack DHN','Total_LT_DEC_Demand','Total_LT_DEC_Prod','HeatSlack DEC','Total_LT_Demand' ,'Total_LT_Prod','HeatSlack LT','Total_HT_Demand','Total_HT_Prod',  'HeatSlack HT']
    comp_df = pd.DataFrame(index = comp_elements, columns=['EnergyScope','Dispa-SET'])

    comp_df.at['Elec / Heat demand / prod [GWh]:','EnergyScope'] = ' '
    comp_df.at['Elec / Heat demand / prod [GWh]:', 'Dispa-SET'] = ' '

    #Electricity demand :
    comp_df.at['Total_Elec_Demand','EnergyScope'] = int(ES_Input_Power.sum(axis=0)) / 1000
    comp_df.at['Total_Elec_Demand','Dispa-SET'] = int(DS_Input_Power.sum(axis=0))/ 1000

    #ES elec used for mobility
    total_elec_mob = 0
    for i in elec_mobi_tech:
        total_elec_mob = total_elec_mob - search_YearBalance(x,i,'ELECTRICITY')
    comp_df.at['Total_Elec_Mobility','EnergyScope'] = total_elec_mob
    comp_df.at['Total_Elec_Mobility','Dispa-SET'] = 0

    #Total elec produced
    power_tech = DS_Output_Power.columns
    total_elec_prod_ES = 0
    total_elec_prod_DS = 0
    for i in power_tech:
        tech = i
#        tech = ''.join(c for c in tech if c not in '-(){}<>[], ')
#        tech = ''.join([i for i in tech if not i.isdigit()])
        if tech[3:] != 'BATT_LI' and i[3:] != 'PHS' and i[3:] in YearBal_DF_index:
            total_elec_prod_ES = total_elec_prod_ES + search_YearBalance(x,tech[3:], 'ELECTRICITY')
            total_elec_prod_DS = total_elec_prod_DS + int(DS_Output_Power[i].sum(axis=0))/ 1000
    comp_df.at['Total_Elec_Prod', 'EnergyScope'] = total_elec_prod_ES
    comp_df.at['Total_Elec_Prod', 'Dispa-SET'] = total_elec_prod_DS

    #Total Heat demand
    total_LT_DHN_Demand_ES = int(ES_Input_Heat[x + '_LT'].sum(axis=0)) / 1000 * perc_dhn
    total_LT_DEC_Demand_ES = int(ES_Input_Heat[x + '_LT'].sum(axis=0)) / 1000 * (1 - perc_dhn)
    total_HT_Demand_ES = int(ES_Input_Heat[x+ '_HT'].sum(axis=0)) / 1000

    total_LT_DHN_Demand_DS = 0
    total_LT_DEC_Demand_DS = 0
    total_HT_Demand_DS = 0
    if n_th_version:
        total_LT_DHN_Demand_DS = DS_Input_Heat[x+'_DHN'].sum()/1000
        total_LT_DEC_Demand_DS = DS_Input_Heat[x+'_DEC'].sum()/1000
        total_HT_Demand_DS = DS_Input_Heat[x+'_IND'].sum()/1000
    else:
        heat_tech = DS_Input_Heat.columns
        for i in heat_tech:
            if 'DHN' in i:
                total_LT_DHN_Demand_DS = total_LT_DHN_Demand_DS + int(DS_Input_Heat[i].sum(axis = 0))/1000
            elif 'DEC' in i:
                total_LT_DEC_Demand_DS = total_LT_DEC_Demand_DS + int(DS_Input_Heat[i].sum(axis = 0))/1000
            else:
                total_HT_Demand_DS = total_HT_Demand_DS + int(DS_Input_Heat[i].sum(axis=0))/1000

    comp_df.at['Total_LT_DHN_Demand','EnergyScope'] = total_LT_DHN_Demand_ES
    comp_df.at['Total_LT_DHN_Demand','Dispa-SET'] = total_LT_DHN_Demand_DS
    comp_df.at['Total_LT_DEC_Demand','EnergyScope'] = total_LT_DEC_Demand_ES
    comp_df.at['Total_LT_DEC_Demand','Dispa-SET'] = total_LT_DEC_Demand_DS
    comp_df.at['Total_LT_Demand','EnergyScope'] = total_LT_DEC_Demand_ES + total_LT_DHN_Demand_ES
    comp_df.at['Total_LT_Demand','Dispa-SET'] = total_LT_DEC_Demand_DS + total_LT_DHN_Demand_DS
    comp_df.at['Total_HT_Demand','EnergyScope'] = total_HT_Demand_ES
    comp_df.at['Total_HT_Demand','Dispa-SET'] = total_HT_Demand_DS

    # Total Heat Prod
    total_LT_DHN_Prod_DS = 0
    total_LT_DEC_Prod_DS = 0
    total_HT_Prod_DS = 0

    total_LT_DHN_Prod_ES = 0
    total_LT_DEC_Prod_ES = 0
    total_HT_Prod_ES = 0
    heat_tech_out = DS_Output_Heat.columns
    for tech in heat_tech_out:
        ES_tech = ''.join(c for c in tech if c not in '-(){}<>[], ')
        ES_tech = ''.join([i for i in ES_tech if not i.isdigit()])
        if 'DHN' in tech:
            total_LT_DHN_Prod_DS = total_LT_DHN_Prod_DS + int(DS_Output_StorageInput[tech].sum(axis=0)) / 1000
            total_LT_DHN_Prod_ES = total_LT_DHN_Prod_ES + search_YearBalance(x,ES_tech[3:],'HEAT_LOW_T_DHN')
        elif 'DEC' in tech:
            total_LT_DEC_Prod_DS = total_LT_DEC_Prod_DS + int(DS_Output_StorageInput[tech].sum(axis=0)) / 1000
            total_LT_DEC_Prod_ES = total_LT_DEC_Prod_ES + search_YearBalance(x,ES_tech[3:],'HEAT_LOW_T_DECEN')
        else:
            total_HT_Prod_DS = total_HT_Prod_DS + int(DS_Output_StorageInput[tech].sum(axis=0)) / 1000
            total_HT_Prod_ES = total_HT_Prod_ES + search_YearBalance(x,ES_tech[3:],'HEAT_HIGH_T')

    comp_df.at['Total_LT_DHN_Prod','EnergyScope'] = total_LT_DHN_Prod_ES
    comp_df.at['Total_LT_DHN_Prod', 'Dispa-SET'] = total_LT_DHN_Prod_DS
    comp_df.at['Total_LT_DEC_Prod','EnergyScope'] = total_LT_DEC_Prod_ES
    comp_df.at['Total_LT_DEC_Prod', 'Dispa-SET'] = total_LT_DEC_Prod_DS
    comp_df.at['Total_LT_Prod','EnergyScope'] = total_LT_DHN_Prod_ES + total_LT_DEC_Prod_ES
    comp_df.at['Total_LT_Prod', 'Dispa-SET'] = total_LT_DHN_Prod_DS + total_LT_DEC_Prod_DS
    comp_df.at['Total_HT_Prod','EnergyScope'] = total_HT_Prod_ES
    comp_df.at['Total_HT_Prod', 'Dispa-SET'] = total_HT_Prod_DS


    # HeatSlack :

    HeatSlack_ES = get_HeatSlack()

    total_DHN_HeatSlack_DS = 0
    total_DEC_HeatSlack_DS = 0
    total_HT_HeatSlack_DS = 0
    heatslack_tech = DS_Output_HeatSlack.columns
    for tech in heatslack_tech:
        if 'DHN' in tech:
            total_DHN_HeatSlack_DS = total_DHN_HeatSlack_DS + int(DS_Output_HeatSlack[tech].sum(axis=0)) / 1000
        elif 'DEC' in tech:
            total_DEC_HeatSlack_DS = total_DEC_HeatSlack_DS + int(DS_Output_HeatSlack[tech].sum(axis=0)) / 1000
        else:
            total_HT_HeatSlack_DS = total_HT_HeatSlack_DS + int(DS_Output_HeatSlack[tech].sum(axis=0)) / 1000

    comp_df.at['HeatSlack DHN','EnergyScope'] = int(HeatSlack_ES.loc['BE','TOTAL_LT_DHN'])
    comp_df.at['HeatSlack DHN', 'Dispa-SET'] = total_DHN_HeatSlack_DS
    comp_df.at['HeatSlack DEC','EnergyScope'] = int(HeatSlack_ES.loc['BE','TOTAL_LT_DEC'])
    comp_df.at['HeatSlack DEC', 'Dispa-SET'] = total_DEC_HeatSlack_DS
    comp_df.at['HeatSlack LT','EnergyScope'] = int(HeatSlack_ES.loc['BE','TOTAL_LT'])
    comp_df.at['HeatSlack LT', 'Dispa-SET'] = total_DHN_HeatSlack_DS + total_DEC_HeatSlack_DS
    comp_df.at['HeatSlack HT','EnergyScope'] = int(HeatSlack_ES.loc['BE','TOTAL_HT'])
    comp_df.at['HeatSlack HT', 'Dispa-SET'] = total_HT_HeatSlack_DS

    ########## RES DataFrame ########################################

    RES_elements = ['RES production [MWh]:', 'Prod_Elec_PV', 'Diff_Prod_Elec_PV', 'Prod_Elec_WIND_ONSHORE', 'Diff_Prod_Elec_WIND_ONSHORE', 'Prod_Elec_WIND_OFFSHORE', 'Diff_Prod_Elec_WIND_OFFSHORE', 'Prod_Elec_HYDRO_RIVER', 'Diff_Prod_Elec_HYDRO_RIVER', 'Curtailment']
    comp_df_RES = pd.DataFrame(index = RES_elements, columns=['EnergyScope','Dispa-SET'])
    comp_df_RES.at['RES production [MWh]:','EnergyScope'] = ' '
    comp_df_RES.at['RES production [MWh]:', 'Dispa-SET'] = ' '

    # Curtailment :
    total_curtail_ES = 0
    total_curtail_DS = 0
    prod_RES_ES = 0
    prod_RES_DS = 0
    AF_tech = ES_Input_AvailFactors.columns
    for i in AF_tech[1:]:
        prod_RES_ES = search_YearBalance(x,i[3:],'ELECTRICITY')*1000
        prod_RES_DS = DS_Output_Power[i].sum(axis=0)

        curtail_ES = ES_Input_AvailFactors[i].sum(axis=0)*search_assets(x,i[3:], 'f')*1000 - prod_RES_ES
        curtail_DS = ES_Input_AvailFactors[i].sum(axis=0)*search_assets(x,i[3:], 'f')*1000 - prod_RES_DS

        total_curtail_ES = total_curtail_ES + curtail_ES
        total_curtail_DS = total_curtail_DS + curtail_DS

        comp_df_RES.at['Prod_Elec_' + i[3:], 'EnergyScope'] = prod_RES_ES
        comp_df_RES.at['Prod_Elec_' + i[3:], 'Dispa-SET'] = prod_RES_DS

        comp_df_RES.at['Diff_Prod_Elec_' + i[3:], 'EnergyScope'] = 0
        comp_df_RES.at['Diff_Prod_Elec_' + i[3:], 'Dispa-SET'] = prod_RES_DS-prod_RES_ES

    comp_df_RES.at['Curtailment','EnergyScope'] = total_curtail_ES
    comp_df_RES.at['Curtailment', 'Dispa-SET'] = total_curtail_DS

    ########## Installed Capacities DataFrame ########################################

    comp_df_capa = pd.DataFrame(index = ['Installed capacities [GW]:'], columns=['EnergyScope','Dispa-SET'])
    comp_df_capa.at['Installed capacities [GW]:','EnergyScope'] = ' '
    comp_df_capa.at['Installed capacities [GW]:', 'Dispa-SET'] = ' '

    for i in DS_PowerPlants.index:
        comp_df_capa.at[i, 'EnergyScope'] = search_assets(x,i[3:],'f')

        #if storage technology:
        if DS_PowerPlants.loc[i,'Technology'] == 'BATS' or DS_PowerPlants.loc[i,'Technology'] == 'HPHS' or DS_PowerPlants.loc[i,'Technology'] == 'BEVS' or DS_PowerPlants.loc[i,'Technology'] == 'CAES' or DS_PowerPlants.loc[i,'Technology'] == 'HDAM' or DS_PowerPlants.loc[i,'Technology'] == 'THMS' or DS_PowerPlants.loc[i,'Technology'] == 'P2GS':
            comp_df_capa.at[i, 'Dispa-SET'] = DS_PowerPlants.loc[i, 'STOCapacity'] / 1000
        else:
            if DS_PowerPlants.loc[i,'COP'] > 0:
                p2hratio = DS_PowerPlants.loc[i,'COP']
            else:
                p2hratio = 1

            comp_df_capa.at[i, 'Dispa-SET'] = DS_PowerPlants.loc[i,'Nunits'] * DS_PowerPlants.loc[i,'PowerCapacity'] /1000 * p2hratio


    ########## Production per Unit DataFrame ########################################

    comp_df_prod = pd.DataFrame(index = ['Production per unit [GWh]:'], columns=['EnergyScope','Dispa-SET'])

    comp_df_prod.at['Production per unit [GWh]:','EnergyScope'] = ' '
    comp_df_prod.at['Production per unit [GWh]:', 'Dispa-SET'] = ' '

    for i in power_tech:
        if 'PHS' in i or 'BATT_LI' in i or 'PHES' in i:
            comp_df_prod.at['Total Prod Elec ' + i + '_Pin', 'Dispa-SET'] = DS_Output_StorageInput[i].sum(axis=0) / 1000
            comp_df_prod.at['Total Prod Elec ' + i + '_Pin', 'EnergyScope'] = -ES_Output_Power[i[3:] + '_Pin'].sum(axis=0) /1000
            comp_df_prod.at['Total Prod Elec ' + i + '_Pout', 'Dispa-SET'] = DS_Output_Power[i].sum(axis=0) / 1000
            comp_df_prod.at['Total Prod Elec ' + i + '_Pout', 'EnergyScope'] = ES_Output_Power[i[3:] + '_Pout'].sum(axis=0) /1000
        else:
            comp_df_prod.at['Total Prod Elec ' + i, 'EnergyScope'] = search_YearBalance(x,i[3:],'ELECTRICITY')
            comp_df_prod.at['Total Prod Elec ' + i, 'Dispa-SET'] = DS_Output_Power[i].sum(axis=0) / 1000

    for i in heat_tech_out:
        Heat_tech_ES = ''.join(c for c in i if c not in '-(){}<>[], ')
        Heat_tech_ES = ''.join([i for i in Heat_tech_ES if not i.isdigit()])
        comp_df_prod.at['Total Prod Heat ' + Heat_tech_ES, 'Dispa-SET'] = DS_Output_StorageInput[i].sum(axis=0) / 1000
        if i in DS_Output_HeatSlack.columns:
            comp_df_prod.at['HeatSlack ' + Heat_tech_ES, 'Dispa-SET'] = DS_Output_HeatSlack[i].sum(axis=0) / 1000
        if 'IND' in i:
            comp_df_prod.at['Total Prod Heat ' + Heat_tech_ES, 'EnergyScope'] = search_YearBalance(x,Heat_tech_ES[3:], 'HEAT_HIGH_T')
            if i in DS_Output_HeatSlack.columns:
                comp_df_prod.at['HeatSlack ' + Heat_tech_ES, 'EnergyScope'] = ' '
        elif 'DHN' in i:
            comp_df_prod.at['Total Prod Heat ' + Heat_tech_ES, 'EnergyScope'] = search_YearBalance(x,Heat_tech_ES[3:], 'HEAT_LOW_T_DHN')
            if i in DS_Output_HeatSlack.columns:
                comp_df_prod.at['HeatSlack ' + Heat_tech_ES, 'EnergyScope'] = ' '
        else:
            comp_df_prod.at['Total Prod Heat ' + Heat_tech_ES, 'EnergyScope'] = search_YearBalance(x,Heat_tech_ES[3:], 'HEAT_LOW_T_DECEN')
            if i in DS_Output_HeatSlack.columns:
                comp_df_prod.at['HeatSlack ' + Heat_tech_ES, 'EnergyScope'] = ' '

    ########## Max production VS installed capacity ########################################

    comp_df_Maxprod = pd.DataFrame(index = ['Installed Capacity VS Max Power [MW]:'], columns=['Installed Capacity','EnergyScope','Dispa-SET'])

    comp_df_Maxprod.at['Installed Capacity VS Max Power [MW]:','Installed Capacity'] = ' '
    comp_df_Maxprod.at['Installed Capacity VS Max Power [MW]:','EnergyScope'] = ' '
    comp_df_Maxprod.at['Installed Capacity VS Max Power [MW]:','Dispa-SET'] = ' '

    for i in comp_df_capa.index[1:]:
        if comp_df_capa.at[i,'EnergyScope'] != 0:
            if 'PHS' in i or 'BATT_LI' in i:
                comp_df_Maxprod.at[i + ' [MWh]', 'Installed Capacity'] = comp_df_capa.loc[i, 'EnergyScope'] * 1000
            else:
                comp_df_Maxprod.at[i,'Installed Capacity'] = comp_df_capa.loc[i,'EnergyScope'] * 1000
            if 'DEC' in i or 'DHN' in i or '_IND' in i:
                comp_df_Maxprod.at[i,'EnergyScope'] = ES_Output_Heat[i[3:]].max()
                comp_df_Maxprod.at[i, 'Dispa-SET'] = DS_Output_StorageInput[i].max()
            elif 'WIND_OFFSHORE' in i:
                comp_df_Maxprod.at[i,'EnergyScope'] = ES_Output_Power['WIND_OFFSHORE'].max()
                comp_df_Maxprod.at[i, 'Dispa-SET'] = DS_Output_Power[i].max()
            elif 'PHS' in i or 'BATT_LI' in i:
                Max_ES = ES_Output_Power[i[3:]].max()
                Max_DS = DS_Output_StorageLevel[i].max()
                comp_df_Maxprod.at[i + ' [MWh]', 'EnergyScope'] = Max_ES
                comp_df_Maxprod.at[i + ' [MWh]', 'Dispa-SET'] = Max_DS
            elif i[3:] in YearBal_DF_index and i in DS_Output_Power.columns:
                comp_df_Maxprod.at[i, 'EnergyScope'] = max(ES_Output_Power[i[3:]],key=abs)
                comp_df_Maxprod.at[i, 'Dispa-SET'] = max(DS_Output_Power[i],key=abs)

    print('############################      Get comparison      ###############################')

    print(comp_df)
    print('-----------------------------------------------------------')
    print(comp_df_RES)
    print('-----------------------------------------------------------')
    print(comp_df_capa)
    print('-----------------------------------------------------------')
    print(comp_df_prod)
    print('-----------------------------------------------------------')
    print(comp_df_Maxprod)
    print('-----------------------------------------------------------')
    comp_df.to_csv('comp_df.csv')
    comp_df_RES.to_csv('comp_df_RES.csv')
    comp_df_capa.to_csv('comp_df_capa.csv')
    comp_df_prod.to_csv('comp_df_prod.csv')
    comp_df_Maxprod.to_csv('comp_df_Maxprod.csv')

get_results_comparison('BE','True')


########################################################################################################################

def get_indicators(x):
    perc_dhn = perc_dhn_list[countries.index(x)]
    DHN_prod_losses = DHN_Prod_losses_list[countries.index(x)]
    DHN_Sto_losses = DHN_Sto_losses_list[countries.index(x)]
    grid_losses = grid_losses_list[countries.index(x)]

    DS_Output_Power = pd.read_csv(case_studied + '/' + 'OutputPower_' + case_studied + '.csv')
    DS_Output_Power = DS_Output_Power.set_index(DS_Output_Power.columns[0])
    DS_Output_Heat = pd.read_csv(case_studied + '/' + 'OutputHeat_' + case_studied + '.csv')
    DS_Output_Heat = DS_Output_Heat.set_index(DS_Output_Heat.columns[0])
    DS_Output_HeatSlack = pd.read_csv(case_studied + '/' + 'OutputHeatSlack_' + case_studied + '.csv')
    DS_Output_HeatSlack = DS_Output_HeatSlack.set_index(DS_Output_HeatSlack.columns[0])
    DS_Output_StorageInput = pd.read_csv(case_studied + '/' + 'OutputStorageInput_' + case_studied + '.csv')
    DS_Output_StorageInput = DS_Output_StorageInput.set_index(DS_Output_StorageInput.columns[0])
    DS_Output_StorageLevel = pd.read_csv(case_studied + '/' + 'OutputStorageLevel_' + case_studied + '.csv')
    DS_Output_StorageLevel = DS_Output_StorageLevel.set_index(DS_Output_StorageLevel.columns[0])
    DS_Output_PowerConsumption = pd.read_csv(case_studied + '/' + 'OutputPowerConsumption_'+ case_studied + '.csv')
    DS_Output_PowerConsumption = DS_Output_PowerConsumption.set_index(DS_Output_PowerConsumption.columns[0])
    DS_Output_LoadShedding = pd.read_csv(case_studied + '/' + 'OutputShedLoad_'+ case_studied + '.csv')
    DS_Output_LoadShedding = DS_Output_LoadShedding.set_index(DS_Output_LoadShedding.columns[0])

    DS_Input_Power = pd.read_csv(case_studied + '/' +'TotalLoadValue' + '_' + x + '.csv', header=None)
    DS_Input_Power = DS_Input_Power.set_index(DS_Input_Power.columns[0])
    DS_Input_Heat = pd.read_csv(case_studied + '/' +'HeatDemand' + '_' +case_studied + '_' + x + '.csv')
    DS_Input_Heat = DS_Input_Heat.set_index(DS_Input_Heat.columns[0])

    DS_PowerPlants = pd.read_csv(case_studied + '/' + 'PowerPlants' + '_' + x + '.csv')
    DS_PowerPlants = DS_PowerPlants.set_index(DS_PowerPlants.columns[0])

    ES_Output_Power = pd.read_csv(case_studied + '/' +'ElecLayers_year_' + case_studied + '_' + x +'.csv')
    ES_Output_Power = ES_Output_Power.set_index(ES_Output_Power.columns[0])

    #change _DS_Output_Power column names
    mylist = []
    for name in DS_Output_Power.columns:
        name = ''.join(c for c in name if c not in '-(){}<>[], ')
        if 'H2' not in name:
            name = ''.join([i for i in name if not i.isdigit()])
        else:
            offset = name.find('H2')-3
            name = name[offset:]
        mylist.append(name)
    DS_Output_Power.columns = mylist

    #change _DS_Output_PowerConsumption column names
    mylist = []
    for name in DS_Output_PowerConsumption.columns:
        name = ''.join(c for c in name if c not in '-(){}<>[], ')
        if 'H2' not in name:
            name = ''.join([i for i in name if not i.isdigit()])
        else:
            offset = name.find('H2')-3
            name = name[offset:]
        mylist.append(name)
    DS_Output_PowerConsumption.columns = mylist


    #change _DS_Output_Heat column names
    mylist_h = []
    for name in DS_Output_Heat.columns:
        name = ''.join(c for c in name if c not in '-(){}<>[], ')
        name = ''.join([i for i in name if not i.isdigit()])
        mylist_h.append(name)
    DS_Output_Heat.columns = mylist_h

    #change _DS_Output_StorageLevel column names
    mylist_sto_lev = []
    for name in DS_Output_StorageLevel.columns:
        name = ''.join(c for c in name if c not in '-(){}<>[], ')
        name = ''.join([i for i in name if not i.isdigit()])
        mylist_sto_lev.append(name)
    DS_Output_StorageLevel.columns = mylist_sto_lev

    #change _DS_Output_StorageInput column names
    mylist_sto_in = []
    for name in DS_Output_StorageInput.columns:
        name = ''.join(c for c in name if c not in '-(){}<>[], ')
        name = ''.join([i for i in name if not i.isdigit()])
        mylist_sto_in.append(name)
    DS_Output_StorageInput.columns = mylist_sto_in









    # Capacity margin:
    capa_margin_df = pd.DataFrame(index = DS_Output_Power.index, columns=capa_margin_tech)
    capa_margin_sto_df = pd.DataFrame(index= DS_Output_Power.index, columns = capa_margin_tech)
    capa_margin_ratioload_df = pd.DataFrame(index= DS_Output_Power.index, columns = ['Load','OtherCons','TotalLoad','capa_marg_ratioload','capa_marg_ratioload_sto'])


    for i in capa_margin_tech:
        if i != 'BATT_LI' and i != 'PHS' :
            capa_installed = DS_PowerPlants.loc[x + '_' +i, 'Nunits'] * DS_PowerPlants.loc[x+ '_'+i, 'PowerCapacity']
            capa_margin_df.loc[:,i] = DS_Output_Power[x + '_' + i]
            capa_margin_df[i] = - (capa_margin_df[i].sub(capa_installed))

    capa_margin_df['Capacity_Margin'] = capa_margin_df.sum(axis = 1)
    Cap_Mar_Average = capa_margin_df['Capacity_Margin'].sum()/8760
    Cap_Mar_Min = capa_margin_df['Capacity_Margin'].min()

    sto_df = pd.DataFrame(index= DS_Output_Power.index, columns= ['level','power_max'])
    for i in capa_margin_tech:
        if i == 'BATT_LI' or i == 'PHS':
            capa_installed = DS_PowerPlants.loc[x + '_' + i, 'STOCapacity'] * DS_PowerPlants.loc[x + '_' +i, 'Nunits']
            sto_df.loc[:,'level'] = DS_Output_StorageLevel[x + '_' + i].multiply(capa_installed)
            sto_df.loc[:,'power_max'] = DS_PowerPlants.loc[x + '_' + i, 'PowerCapacity']*DS_PowerPlants.loc[x + '_' +i, 'Nunits']
            capa_margin_sto_df.loc[:, i] = sto_df[['level','power_max']].min(axis = 1)

    capa_margin_sto_df['Capacity_Margin'] = capa_margin_df['Capacity_Margin']
    capa_margin_sto_df['Capacity_Margin_sto'] = capa_margin_sto_df.sum(axis = 1)
    Cap_Mar_sto_Average = capa_margin_sto_df['Capacity_Margin_sto'].sum()/8760
    Cap_Mar_sto_Min = capa_margin_sto_df['Capacity_Margin_sto'].min()

    mydate = capa_margin_df.index
    count_Cap_Mar_sto = 0
    count_Cap_Mar = 0
    for i in range(0,8760):
        if capa_margin_df.loc[mydate[i],'Capacity_Margin'] < 0.1:                       #To change to vary the treshold
            count_Cap_Mar = count_Cap_Mar + 1
    for i in range(0,8760):
        if capa_margin_sto_df.loc[mydate[i],'Capacity_Margin_sto'] < 1400:              #To change to vary the treshold
            count_Cap_Mar_sto = count_Cap_Mar_sto + 1

    # Ratio Capacity margin / Total Load
    capa_margin_ratioload_df['Load'] = DS_Input_Power
    capa_margin_ratioload_df.at[capa_margin_ratioload_df.index[0],'Load'] = DS_Input_Power.columns[0]

    capa_margin_ratioload_df['OtherCons'] = DS_Output_PowerConsumption.sum(axis = 1)
    capa_margin_ratioload_df['TotalLoad'] = capa_margin_ratioload_df.sum(axis = 1)
    peak_load = capa_margin_ratioload_df['TotalLoad'].max()
    capa_margin_ratioload_df['capa_marg_ratioload'] = capa_margin_df['Capacity_Margin'] / peak_load
    capa_margin_ratioload_df['capa_marg_ratioload_sto'] = capa_margin_sto_df['Capacity_Margin_sto'] / peak_load

    max_load_index = capa_margin_ratioload_df['TotalLoad'].idxmax()

    Cap_Mar_ratio_Average = capa_margin_ratioload_df['capa_marg_ratioload'].sum() / 8760
    Cap_Mar_ratio_Min = capa_margin_ratioload_df['capa_marg_ratioload'].min()

    Cap_Mar_ratio_sto_Average = capa_margin_ratioload_df['capa_marg_ratioload_sto'].sum()/8760
    Cap_Mar_ratio_sto_Min = capa_margin_ratioload_df['capa_marg_ratioload_sto'].min()

    count_Cap_Mar_ratio_sto = 0
    count_Cap_Mar_ratio = 0
    for i in range(0,8760):
        if capa_margin_ratioload_df.loc[mydate[i],'capa_marg_ratioload'] < 0.1:         #To change to vary the treshold
            count_Cap_Mar_ratio = count_Cap_Mar_ratio + 1
    for i in range(0,8760):
        if capa_margin_ratioload_df.loc[mydate[i],'capa_marg_ratioload_sto'] < 0.1:     #To change to vary the treshold
            count_Cap_Mar_ratio_sto = count_Cap_Mar_ratio_sto + 1

    ##################
    # Final definition of Capacity margin
    # Capacity margin : Final definition((capa_inst - prod(h)) + sto(h) + load_storage(h) ) / load(withoutstorage)(h):

    capa_margin_final = pd.DataFrame(index=DS_Output_Power.index, columns=capa_margin_tech)

    Total_conso = pd.DataFrame(index=DS_Output_Power.index, columns = ['Total_EUD'])
    Total_conso['DHN_prod'] = DS_Output_PowerConsumption[x+'_DHN_HP_ELEC']
    Total_conso['DHN_Sto_IN-OUT'] = (DS_Output_StorageInput[x+'_DHN_HP_ELEC']-DS_Output_Heat[x+'_DHN_HP_ELEC']).multiply(1/search_PowerPlant(x,x+'_DHN_HP_ELEC','COP'))
    Total_conso[Total_conso['DHN_Sto_IN-OUT'] < 0] = 0
    Total_conso['DHN'] = Total_conso['DHN_prod'] - Total_conso['DHN_Sto_IN-OUT']
    Total_conso['DEC_prod'] = DS_Output_PowerConsumption[x+'_DEC_HP_ELEC']
    Total_conso['DEC_Sto_IN-OUT'] = (DS_Output_StorageInput[x+'_DEC_HP_ELEC']-DS_Output_Heat[x+'_DEC_HP_ELEC']).multiply(1/search_PowerPlant(x,x+'_DEC_HP_ELEC','COP'))
    Total_conso[Total_conso['DEC_Sto_IN-OUT'] < 0] = 0
    Total_conso['DEC'] = Total_conso['DEC_prod'] - Total_conso['DEC_Sto_IN-OUT']
    Total_conso = Total_conso.drop(['DHN_prod'], axis=1)
    Total_conso = Total_conso.drop(['DEC_prod'], axis=1)
    Total_conso['Total_EUD'] = DS_Input_Power.sum(axis=1)  + Total_conso['DHN'] + Total_conso['DEC'] #+ DS_Output_PowerConsumption[x+'_IND_DIRECT_ELEC']
    max_demand_index = Total_conso['Total_EUD'].idxmax()
    for i in capa_margin_tech:
        if i != 'BATT_LI' and i != 'PHS' :
            capa_installed = DS_PowerPlants.loc[x + '_' +i, 'Nunits'] * DS_PowerPlants.loc[x+ '_'+i, 'PowerCapacity']
            capa_margin_final.loc[:, i] = DS_Output_Power[x + '_' + i]
            capa_margin_final[i] = - (capa_margin_df[i].sub(capa_installed))
        else:
            capa_installed = DS_PowerPlants.loc[x + '_' + i, 'STOCapacity'] * DS_PowerPlants.loc[x + '_' +i, 'Nunits']
            sto_df.loc[:,'level'] = DS_Output_StorageLevel[x + '_' + i].multiply(capa_installed)
            sto_df.loc[:,'power_max'] = DS_PowerPlants.loc[x + '_' + i, 'PowerCapacity']*DS_PowerPlants.loc[x + '_' +i, 'Nunits']
            capa_margin_final.loc[:, i] = sto_df[['level','power_max']].min(axis = 1)

    capa_margin_final['Capacity Margin [MW]'] = capa_margin_final.sum(axis=1) + Total_conso['DHN_Sto_IN-OUT'] + Total_conso['DEC_Sto_IN-OUT'] #+ DS_Output_StorageInput[x + '_BATT_LI']
    capa_margin_final['Capacity Margin [-]'] = capa_margin_final['Capacity Margin [MW]']/(Total_conso['Total_EUD'])
    count_Cap_Mar_final = 0
    for i in range(0, 8760):
        if capa_margin_final.loc[mydate[i], 'Capacity Margin [-]'] < 0.1:  # To change to vary the treshold
            count_Cap_Mar_final= count_Cap_Mar_final + 1

    ###########



    # Day with highest EUD (elec + heat)
    Total_EUD = pd.DataFrame(index = DS_Output_Power.index,columns=['Total_EUD'])
    Total_EUD['Total_EUD'] = DS_Input_Power.sum(axis=1) + DS_Input_Heat.sum(axis=1)
    max_EUD_index = Total_EUD['Total_EUD'].idxmax()
#    print(max_EUD_index)
#    print(Total_EUD.loc[max_EUD_index,'Total_EUD'])
#    print(capa_margin_sto_df.loc[max_EUD_index,'Capacity_Margin_sto'] / )



    # Number of start-up
    Num_Startup = pd.DataFrame(index = ['Number of start-up:'], columns=['EnergyScope','Dispa-SET'])
    Num_Startup.at['Number of start-up:','EnergyScope'] = ' '
    Num_Startup.at['Number of start-up:','Dispa-SET'] = ' '

    date_list = DS_Output_Power.index

    for tech in capa_margin_tech +['IND_COGEN_GAS','IND_COGEN_WASTE','DHN_COGEN_GAS','DHN_COGEN_WOOD','DHN_COGEN_WET_BIOMASS','DHN_COGEN_WASTE','DEC_COGEN_GAS']:
        count_ES = 0
        count_DS = 0
        for i in range(1,8760):
            if ES_Output_Power.loc[i+1,tech] > 0 and ES_Output_Power.loc[i,tech] == 0:
                count_ES = count_ES+1
            if DS_Output_Power.loc[date_list[i],x + '_' +tech] > 0 and DS_Output_Power.loc[date_list[i-1],x + '_' +tech] == 0:
                count_DS = count_DS+1
        Num_Startup.at[tech,'EnergyScope'] = count_ES
        Num_Startup.at[tech,'Dispa-SET'] = count_DS

    # Load Shedding
    LoadShedding = pd.DataFrame(columns=['Starting hour','Consecutive hours','Shed_max [MW]','Shed_max [% of peak load]','Shed_average [% of peak load]','Energy Shedded [MWh]'])
    LS_occ = 0
    i = 0
    j = 0
    while i < 8760:
        j = i
        if DS_Output_LoadShedding.loc[DS_Output_LoadShedding.index[i],x] > 0:
            LS = True
            LS_value = 0
            LS_value_max = 0
            LS_occ = LS_occ + 1
            while LS == True:
                LS_value = LS_value + DS_Output_LoadShedding.loc[DS_Output_LoadShedding.index[j],x]
                if DS_Output_LoadShedding.loc[DS_Output_LoadShedding.index[j+1],x] > 0:
                    if DS_Output_LoadShedding.loc[DS_Output_LoadShedding.index[j], x] > LS_value_max:
                        LS_value_max = DS_Output_LoadShedding.loc[DS_Output_LoadShedding.index[j], x]
                    j = j + 1
                else:
                    LS = False
                    if DS_Output_LoadShedding.loc[DS_Output_LoadShedding.index[j], x] > LS_value_max:
                        LS_value_max = DS_Output_LoadShedding.loc[DS_Output_LoadShedding.index[j], x]

            LoadShedding.at[LS_occ-1, 'Starting hour'] = i
            LoadShedding.at[LS_occ - 1, 'Consecutive hours'] = j-i+1
            LoadShedding.at[LS_occ-1,'Shed_max [MW]'] = LS_value_max
            LoadShedding.at[LS_occ - 1, 'Shed_max [% of peak load]'] = LS_value_max*100 / Total_conso['Total_EUD'].max()
            LoadShedding.at[LS_occ - 1, 'Shed_average [% of peak load]'] = LS_value*100 / (Total_conso['Total_EUD'].max()*(j-i+1))
            LoadShedding.at[LS_occ - 1, 'Energy Shedded [MWh]'] = LS_value
            i = j + 1
        else:
            i = i + 1

    LoadShedding.at['Total','Energy Shedded [MWh]'] = LoadShedding['Energy Shedded [MWh]'].sum(axis = 0)
    LoadShedding.at['Total','Starting hour'] = ' '
    LoadShedding.at['Total', 'Consecutive hours'] = LoadShedding['Consecutive hours'].sum(axis = 0)
    LoadShedding.at['Total', 'Shed_max [MW]'] = LoadShedding['Shed_max [MW]'].max()

    # Other indicators

    print('############################      Get Indicators      ###############################')
    print('-----------------------------------------------------------')
    '''
    print('Capacity Margin in absolute values [MW] : ')
    print('Average capacity margin: ' + str(Cap_Mar_Average) + ' MW')
    print('Average capacity margin with storage: ' + str(Cap_Mar_sto_Average) + ' MW')
    print('Minimum capacity margin: ' + str(Cap_Mar_Min) + ' MW')
    print('Minimum capacity margin with storage: ' + str(Cap_Mar_sto_Min) + ' MW')
    print('Hours with capacity margin < 0.1 MW: ' + str(count_Cap_Mar) + ' hours')
    print('Hours with capacity margin with storage < 1400 MW: ' + str(count_Cap_Mar_sto) + ' hours')
    print('-----------------------------------------------------------')
    print('Capacity Margin to peak-load ratio [-] : ')
    print('Average capacity margin to peak-load ratio: ' + str(Cap_Mar_ratio_Average))
    print('Average capacity margin to peak-load ratio with storage: ' + str(Cap_Mar_ratio_sto_Average))
    print('Minimum capacity margin to peak-load ratio: ' + str(Cap_Mar_ratio_Min))
    print('Minimum capacity margin to peak-load ratio with storage: ' + str(Cap_Mar_ratio_sto_Min))
    print('Hours with capacity margin to peak-load ratio < 0.1: ' + str(count_Cap_Mar_ratio) + ' hours')
    print('Hours with capacity margin to peak-load ratio with storage < 0.1: ' + str(count_Cap_Mar_ratio_sto) + ' hours')
    print('-----------------------------------------------------------')
    print('Peak load hour: ' + max_load_index)
    print('Capacity margin with storage at peak load hour: ' + str(capa_margin_ratioload_df.loc[max_load_index, 'capa_marg_ratioload_sto']))
    print('-----------------------------------------------------------')
    print('Peak EUD hour: ' + max_EUD_index)
    print('Capacity margin with storage at peak EUD hour: ' + str(capa_margin_sto_df.loc[max_EUD_index, 'Capacity_Margin_sto'] / peak_load))
    print('Hours with capacity margin with storage < 0.1: ' + str(count_Cap_Mar_ratio_sto) + ' hours')
    print('-----------------------------------------------------------')
    '''
    print('Capacity margin: final definition ')
    print('Minium capacity margin: ' + str(capa_margin_final['Capacity Margin [-]'].min()) )
    print('Hours with capacity margin < 0.1: ' + str(count_Cap_Mar_final) )
    print('-----------------------------------------------------------')
    print(Num_Startup)
    print('-----------------------------------------------------------')
    print('Load Shedding periods:')
    print(LoadShedding)
    print('-----------------------------------------------------------')


    capa_margin_df.to_csv('Capacity_Margin' + '_BE' + '.csv')
    capa_margin_sto_df.to_csv('Capacity_Margin_Storage_' + x + '.csv')
    LoadShedding.to_csv('Load Shedding_' + x + '.csv' )

get_indicators('BE')


























