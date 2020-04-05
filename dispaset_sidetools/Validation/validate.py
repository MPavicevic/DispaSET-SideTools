import pandas as pd
import glob

input_folder = '../../Inputs/'  # to access DATA - DATA_brut & Typical_Units(to find installed power f [GW or GWh for storage])
output_folder = '../../Outputs/'

from search import search_YearBalance
from search import search_Dict_list
from search import search_PowerPlant
from search import from_excel_to_dataFrame


########################################################################################################################

# Get total heat produced by "HeatSLack" in EnergyScope

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

                #print(y + ' : ' + ' HT :' + str(value_HT) + ' LT_DEC : ' + str(value_LT_DEC) + ' LT : ' + str(value_LT_DHN)  )

        HeatSlack_demand.at[Country,'TOTAL_HT'] = total_HT
        HeatSlack_demand.at[Country,'TOTAL_LT_DEC'] = total_LT_dec
        HeatSlack_demand.at[Country,'TOTAL_LT_DHN'] = total_LT_dhn
        HeatSlack_demand.at[Country,'TOTAL_LT'] = total_LT_dhn + total_LT_dhn
        HeatSlack_demand.at[Country,'TOTAL'] = total_HT + total_LT_dec + total_LT_dhn

    #print(HeatSlack_demand)
    #HeatSlack_demand.to_csv('heatslack.csv')
    return HeatSlack_demand


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


#list = ['IND_COGEN_GAS','IND_DIRECT_ELEC','DEC_HP_ELEC','DHN_HP_ELEC','IND_BOILER_WOOD','IND_BOILER_WASTE','TS_DEC_HP_ELEC','TS_DHN_SEASONAL']
#print(get_ES_heatprod(list))


########################################################################################################################

#
#
#Function that builds the Sankey Diagram of Dispa-SET.
#
#
#
#

def get_Sankey():
    import plotly.graph_objects as go

    #Enter the studied case name : Heat_hourly_TD, Heat_correlation, Heat_yearly, Heat_daily, ...
    case_studied = 'Heat_hourly_TD'
    Countries = ['BE']

    Power = pd.read_csv(case_studied + '/' + 'OutputPower_' + case_studied +'.csv')
    Power = Power.set_index(Power.columns[0])
    Heat = pd.read_csv(case_studied + '/' +'OutputHeat_' + case_studied +'.csv')
    Heat = Heat.set_index(Heat.columns[0])
    HeatSlack = pd.read_csv(case_studied + '/' +'OutputHeatSlack_' + case_studied +'.csv')
    HeatSlack = HeatSlack.set_index(HeatSlack.columns[0])
    StorageInput = pd.read_csv(case_studied + '/' +'OutputStorageInput_' + case_studied +'.csv')
    StorageInput = StorageInput.set_index(StorageInput.columns[0])
    TotalLoadValue = pd.read_csv(case_studied + '/' +'TotalLoadValue.csv')
    TotalLoadValue = TotalLoadValue.set_index(TotalLoadValue.columns[0])
    HeatDemand = pd.read_csv(input_folder + 'EUD_HEAT.txt', delimiter='\t', index_col=0)
    HeatDemand = from_excel_to_dataFrame(case_studied + '/' + 'DATA_preprocessing_' + case_studied +'.xlsx','EUD_heat')

    EUD_ELEC = TotalLoadValue.sum(axis=0) / 1000
    EUD_HEAT_LT = HeatDemand[Countries[0] + '_LT'].sum(axis=0) / 1000
    EUD_HEAT_HT = HeatDemand[Countries[0] + '_HT'].sum(axis=0) / 1000


    PowColumn = Power.columns[1:]
    PowerTot = pd.DataFrame(columns=PowColumn)
    for i in PowerTot:
        PowerTot.at[0,i] = Power[i].sum(axis=0) / 1000
    HeatColumn = Heat.columns[1:]
    HeatTot = pd.DataFrame(columns=HeatColumn)
    for i in HeatTot:
        HeatTot.at[0,i] = Heat[i].sum(axis=0) / 1000
    HeatSlackColumn = HeatSlack.columns[1:]
    HeatSlackTot = pd.DataFrame(columns=HeatSlackColumn)
    for i in HeatSlackTot:
        HeatSlackTot.at[0, i] = HeatSlack[i].sum(axis=0) / 1000

    # Keep only BATT_LI and PHS
    StoColumn = list()
    for i in StorageInput.columns:
        if 'BATT_LI' in i or 'PHS' in i:
            StoColumn.append(i)
    StorageTot = pd.DataFrame(columns=StoColumn)
    for i in StorageTot:
        StorageTot.at[0, i] = StorageInput[i].sum(axis=0) / 1000

    #build labels
    mylabels = ['HEAT_HT','HEAT_LT_DHN','HEAT_LT_DEC', 'EUD_ELEC', 'EUD_LT_DHN', 'EUD_LT_DEC','EUD_HT','P2H','ELECTRICITY','HEATSLACK','OtherFuels']
    FuelLabels = ['BIO','GAS','GEO','HRD','HYD','LIG','NUC','OIL','PEA','SUN','WAT','WIN','WST']
    mylabels.extend(FuelLabels)
    mylabels.extend(PowColumn)
    mylabels.extend(HeatColumn)
    mylabels.extend(HeatSlackColumn)
    mylabels.extend(StoColumn)


    #build links
    mysource = list()
    mytarget = list()
    myvalue = list()

    # STORAGE FLOWS

    ELEC_extract = 0
    EUD_extract = 0
    for i in StorageTot:
        ThisFuel = search_PowerPlant(i, 'Fuel')

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
            ThisValue = StorageTot.loc[0, i] * search_PowerPlant(i, 'Efficiency')
            EUD_extract = EUD_extract + ThisValue
            myvalue.append(ThisValue)

    # ELECTRICITY FLOWS

    for i in PowerTot:
        if 'COGEN' in i:
            ThisFuel = search_PowerPlant(i, 'Fuel')
            if ThisFuel in mylabels:
                ThisSource = ThisFuel
            else:
                ThisSource = 'OtherFuels'
            mysource.append(mylabels.index(ThisSource))
            ThisTarget = i
            mytarget.append(mylabels.index(ThisTarget))
            ThisValue = PowerTot.loc[0, i] / search_PowerPlant(i, 'Efficiency')
            myvalue.append(ThisValue)

            ThisSource = i
            mysource.append(mylabels.index(ThisSource))
            ThisTarget = 'ELECTRICITY'
            mytarget.append(mylabels.index(ThisTarget))
            ThisValue = PowerTot.loc[0, i]
            myvalue.append(ThisValue)

        elif 'CCGT' in i:
            ThisFuel = search_PowerPlant(i, 'Fuel')
            if ThisFuel in mylabels:
                ThisSource = ThisFuel
            else:
                ThisSource = 'OtherFuels'
            mysource.append(mylabels.index(ThisSource))
            ThisTarget = i
            mytarget.append(mylabels.index(ThisTarget))
            ThisValue = PowerTot.loc[0, i] / search_PowerPlant(i, 'Efficiency')
            myvalue.append(ThisValue)

            ThisSource = i
            mysource.append(mylabels.index(ThisSource))
            ThisTarget = 'ELECTRICITY'
            mytarget.append(mylabels.index(ThisTarget))
            ThisValue = PowerTot.loc[0, i]
            myvalue.append(ThisValue)

        elif 'BATT' not in i:
            ThisFuel = search_PowerPlant(i, 'Fuel')
            if ThisFuel in mylabels:
                ThisSource = ThisFuel
            else:
                ThisSource = 'OtherFuels'
            mysource.append(mylabels.index(ThisSource))
            ThisTarget = i
            mytarget.append(mylabels.index(ThisTarget))
            ThisValue = PowerTot.loc[0, i] / search_PowerPlant(i, 'Efficiency')
            myvalue.append(ThisValue)

            ThisSource = i
            mysource.append(mylabels.index(ThisSource))
            ThisTarget = 'ELECTRICITY'
            mytarget.append(mylabels.index(ThisTarget))
            ThisValue = PowerTot.loc[0, i]
            myvalue.append(ThisValue)

    # HEAT FLOWS

    for i in HeatTot:
        if 'COGEN' in i:
            if "GAS" in i or "CCGT" in i:
                ThisSource = 'GAS'
            else:
                ThisSource = 'OtherFuels'
            mysource.append(mylabels.index(ThisSource))
            ThisTarget = i
            mytarget.append(mylabels.index(ThisTarget))
            ThisValue = HeatTot.loc[0, i] / search_PowerPlant(i, 'CHPPowerToHeat') / search_PowerPlant(i, 'Efficiency')
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

        elif 'HP' in i:
            ThisSource = 'ELECTRICITY'
            mysource.append(mylabels.index(ThisSource))
            ThisTarget = i
            mytarget.append(mylabels.index(ThisTarget))
            ThisValue = HeatTot.loc[0, i] / search_PowerPlant(i, 'COP')
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
            ThisValue = HeatTot.loc[0, i] / search_PowerPlant(i,
                                                              'COP')  # Or divide by efficiency ??? IND_DIRECT_ELEC case
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

    for i in HeatSlackTot:

        ThisFuel = search_PowerPlant(i, 'Fuel')
        if ThisFuel in mylabels:
            ThisSource = ThisFuel
        else:
            ThisSource = 'OtherFuels'
        mysource.append(mylabels.index(ThisSource))
        ThisTarget = 'HEATSLACK'
        mytarget.append(mylabels.index(ThisTarget))
        ThisValue = HeatSlackTot.loc[0, i] / search_PowerPlant(i, 'Efficiency')
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


    fig = go.Figure(data=[go.Sankey(
        node = dict(
        pad = 15,
        thickness = 20,
        line = dict(color = "black", width = 0.5),
        label = mylabels,
        color = "blue"
        ),
        link = dict(
        source = mysource,
        target = mytarget,
        value = myvalue
    ))])

    fig.update_layout(title_text="Sankey Diagram : figures in GWh", font_size=10)
    fig.show()

get_Sankey()


########################################################################################################################

# function that compaires the demands, results between ES and DS

def get_results_comparison():

    #Enter the studied case name : Heat_hourly_TD, Heat_correlation, Heat_yearly, Heat_daily, ...
    case_studied = 'Heat_hourly_TD'
    Countries = ['BE']

    DS_Output_Power = pd.read_csv(case_studied + '/' + 'OutputPower_' + case_studied +'.csv')
    DS_Output_Power = DS_Output_Power.set_index(DS_Output_Power.columns[0])
    DS_Output_Heat = pd.read_csv(case_studied + '/' +'OutputHeat_' + case_studied +'.csv')
    DS_Output_Heat = DS_Output_Heat.set_index(DS_Output_Heat.columns[0])
    DS_Output_HeatSlack = pd.read_csv(case_studied + '/' +'OutputHeatSlack_' + case_studied +'.csv')
    DS_Output_HeatSlack = DS_Output_HeatSlack.set_index(DS_Output_HeatSlack.columns[0])
    DS_Output_StorageInput = pd.read_csv(case_studied + '/' +'OutputStorageInput_' + case_studied +'.csv')
    DS_Output_StorageInput = DS_Output_StorageInput.set_index(DS_Output_StorageInput.columns[0])

    DS_Input_Power = pd.read_csv(case_studied + '/' +'TotalLoadValue.csv')
    DS_Input_Power = DS_Input_Power.set_index(DS_Input_Power.columns[0])
    DS_Input_Heat = pd.read_csv(case_studied + '/' + 'HeatDemand_' + case_studied +'.csv')
    DS_Input_Heat = DS_Input_Heat.set_index(DS_Input_Heat.columns[0])

    ES_Input_Power = from_excel_to_dataFrame(input_folder + 'DATA_preprocessing_BE.xlsx', 'EUD_elec')
    ES_Input_Heat = from_excel_to_dataFrame(input_folder + 'DATA_preprocessing_BE.xlsx', 'EUD_heat')

    comp_elements = ['Total_Elec_Demand','Total_Elec_Mobility','Total_Elec_Prod', 'Total_LT_DHN_Demand', 'Total_LT_DHN_Prod','HeatSlack DHN','Total_LT_DEC_Demand','Total_LT_DEC_Prod','HeatSlack DEC','Total_LT_Demand' ,'Total_LT_Prod','HeatSlack LT','Total_HT_Demand','Total_HT_Prod',  'HeatSlack HT']
    comp_df = pd.DataFrame(index = comp_elements, columns=['EnergyScope','Dispa-SET'])

    #Electricity demand :
    comp_df.at['Total_Elec_Demand','EnergyScope'] = int(ES_Input_Power.sum(axis=0)) / 1000
    comp_df.at['Total_Elec_Demand','Dispa-SET'] = int(DS_Input_Power.sum(axis=0))/ 1000

    #ES elec used for mobility
    mob_elec_tech = ['TRAMWAY_TROLLEY','TRAIN_PUB','TRAIN_CapitalfREIGHT']
    total_elec_mob = 0
    for i in mob_elec_tech:
        total_elec_mob = total_elec_mob - search_YearBalance(i,'ELECTRICITY')
    comp_df.at['Total_Elec_Mobility','EnergyScope'] = total_elec_mob
    comp_df.at['Total_Elec_Mobility','Dispa-SET'] = 0

    #Total elec produced
    power_tech = DS_Output_Power.columns
    total_elec_prod_ES = 0
    total_elec_prod_DS = 0
    for i in power_tech:
        tech = i
        tech = ''.join(c for c in tech if c not in '-(){}<>[], ')
        tech = ''.join([i for i in tech if not i.isdigit()])
        if tech[3:] != 'BATT_LI' and i[2:] != 'PHS':
            total_elec_prod_ES = total_elec_prod_ES + search_YearBalance(tech[3:], 'ELECTRICITY')
            total_elec_prod_DS = total_elec_prod_DS + int(DS_Output_Power[i].sum(axis=0))/ 1000
    comp_df.at['Total_Elec_Prod', 'EnergyScope'] = total_elec_prod_ES
    comp_df.at['Total_Elec_Prod', 'Dispa-SET'] = total_elec_prod_DS

    #Total Heat demand
    for x in Countries:
        perc_dhn = 0.37  # Value to be found in DATA.xlsx : 'share_heat_dhn: max'
        total_LT_DHN_Demand_ES = int(ES_Input_Heat[x + '_LT'].sum(axis=0)) / 1000 * perc_dhn
        total_LT_DEC_Demand_ES = int(ES_Input_Heat[x + '_LT'].sum(axis=0)) / 1000 * (1 - perc_dhn)
        total_HT_Demand_ES = int(ES_Input_Heat[x+ '_HT'].sum(axis=0)) / 1000

        total_LT_DHN_Demand_DS = 0
        total_LT_DEC_Demand_DS = 0
        total_HT_Demand_DS = 0
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
            total_LT_DHN_Prod_DS = total_LT_DHN_Prod_DS + int(DS_Output_Heat[tech].sum(axis=0)) / 1000
            total_LT_DHN_Prod_ES = total_LT_DHN_Prod_ES + search_YearBalance(ES_tech[3:],'HEAT_LOW_T_DHN')
        elif 'DEC' in tech:
            total_LT_DEC_Prod_DS = total_LT_DEC_Prod_DS + int(DS_Output_Heat[tech].sum(axis=0)) / 1000
            total_LT_DEC_Prod_ES = total_LT_DEC_Prod_ES + search_YearBalance(ES_tech[3:],'HEAT_LOW_T_DECEN')
        else:
            total_HT_Prod_DS = total_HT_Prod_DS + int(DS_Output_Heat[tech].sum(axis=0)) / 1000
            total_HT_Prod_ES = total_HT_Prod_ES + search_YearBalance(ES_tech[3:],'HEAT_HIGH_T')

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




    print(comp_df)



get_results_comparison()





