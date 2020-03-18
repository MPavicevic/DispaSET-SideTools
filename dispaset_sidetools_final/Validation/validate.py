import pandas as pd
import glob

input_folder = '../../Inputs/'  # to access DATA - DATA_brut & Typical_Units(to find installed power f [GW or GWh for storage])
output_folder = '../../Outputs/'

from search import search_YearBalance
from search import search_Dict_list
from search import search_PowerPlant


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

    Countries = ['BE']

    Power = pd.read_csv(input_folder + 'OutputPower_DS.csv')
    Heat = pd.read_csv(input_folder + 'OutputHeat_DS.csv')
    HeatSlack = pd.read_csv(input_folder + 'OutputHeatSlack_DS.csv')
    StorageInput = pd.read_csv(input_folder + 'OutputStorageInput_DS.csv')

    TotalLoadValue = pd.read_csv(input_folder + 'EUD_ELEC.txt', delimiter='\t', index_col=0)
    EUD_ELEC = TotalLoadValue.sum(axis=0) / 1000
    HeatDemand = pd.read_csv(input_folder + 'EUD_HEAT.txt', delimiter='\t', index_col=0)
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








