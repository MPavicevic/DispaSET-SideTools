import pandas as pd
import glob

#This function is called form other folder: DON'T change these paths /!\
input_folder = '../../Inputs/EnergyScope/'
output_folder = '../../Outputs/EnergyScope/'

input_PP_folder = '../../Dispa-SET.git/Database/PowerPlants/'  # input file = PowerPlants.csv



########################################################################################################################

# function that provides the value contained in the Assets.txt file (output from EnergyScope)
#
# ATTENTION : Assets.txt file has to be provided when running EnergyScope with AMPL
#
# Input :    tech = technology studied
#           feat = feature needed regarding to the technology studied
# Output :   Value of the feature asked

def search_assets(tech, feat):
    assets = pd.read_csv(input_folder + 'Assets.txt', delimiter='\t')

    features = list(assets.head())
    features = [x.strip(' ') for x in features]
    column = features.index(feat)
    col_names = features[1:]

    col_names.append("end")
    assets.columns = col_names

    output = float(assets.at[tech, feat])

    return output

########################################################################################################################

#
#
# Input :    tech = technology studied
#           feat = feature needed regarding to the technology studied
# Output :   Value of the feature asked
#
#
def search_YearBalance(tech, feat):
    yearbal = pd.read_csv(input_folder + 'YearBalance.txt', delimiter='\t')
    yearbal.set_index('Tech', inplace=True)
    techno = list(yearbal.index)
    techno2 = [x.strip(' ') for x in techno]
    yearbal.set_index([techno2], inplace=True)

    if 'F' in tech:
        tech = tech.replace('F','Capitalf')

    output = yearbal.at[tech, feat]

    return output

########################################################################################################################

#
#
# Input :    tech = technology studied
#           feat = feature needed regarding to the technology studied
# Output :   Value of the feature asked
#
#
def search_PowerPlant(tech, feat):
    PowPlant = pd.read_csv(output_folder + 'PowerPlants.csv')
    PowPlant.index = PowPlant['Unit']
    tech = ''.join(c for c in tech if c not in '-(){}<>[], ')
    tech = ''.join([i for i in tech if not i.isdigit()])
    output = PowPlant.at[tech, feat]

    return output

########################################################################################################################

#
#
# Input :    type = LTlayers or HTlayers dataframe
#           TD = typical day studied
#           hour = hour studied
#           tech  = tech studied
# Output :   Value of the feature asked
#
#
def search_HeatLayers(LayersDF, TD, hour, tech):
    tech = ''.join(c for c in tech if c not in '-(){}<>[], ')
    tech = ''.join([i for i in tech if not i.isdigit()])
    output = LayersDF.at[((TD-1)*24)+hour - 1, tech]
    return output


########################################################################################################################

#
#
# Input :  ElecLayersDF = ElecLayers dataframe
#           TD = typical day studied
#           hour = hour studied
#           tech  = tech studied
# Output :   Value of the feature asked
#
#
def search_ElecLayers(ElecLayersDF,TD, hour, tech):
    tech = ''.join(c for c in tech if c not in '-(){}<>[], ')
    tech = ''.join([i for i in tech if not i.isdigit()])
    output = ElecLayersDF.at[((TD-1)*24)+hour - 1, tech]
    return output


########################################################################################################################

#
# returns the tech's name in the DS format of the ES tech
# Input = ES name
# Output = DS name
#
def search_Dict_ES2DS(tech_ES):
    tech_DS = str(mapping['TECH'][tech_ES] + '_' + mapping['FUEL'][tech_ES])
    return tech_DS

########################################################################################################################

#
#
# returns list containing all the tech of type 'type' from ES
# Input = 'type'
# Output = list of tech of type 'tyoe'
#
def search_Dict_list(old_list,type):
    mylist = old_list
    for i in mapping['TECH']:
        if mapping['TECH'][i] == type:
            mylist.append(i)
    return mylist

########################################################################################################################


#
#
# Input: - All HeatSlack (AKA boilers) present in Assets.txt
#        - DATA_BRUT.xlsx : 2.1 RESOURCES to get the resources price
#        - DATA_BRUT.xlsx : 3.2 TECH to get the specific tech operating costs
#        -
# Output: - A weighted average of the operating costs of the TECH_FUEL combination in boilers
#
def get_HeatSlackPrice(numTD):
    n_TD = numTD

    RESOURCES = from_excel_to_dataFrame(input_folder + 'DATA_preprocessing_BE.xlsx', 'RESOURCES') #Possède les prix des ressources dans la colonne c_op [Million_euros/GWh]
    TECH = from_excel_to_dataFrame(input_folder + 'DATA_preprocessing_BE.xlsx', 'TECH') #Possède les prix d'opération des technologies dans la colonne c_maint

    #Set Technologies as Index in RESOURCES (RESOURCES) and in TECH(param :)
    RESOURCES.set_index('{RESOURCES}',inplace=True)
    TECH.set_index('param:',inplace=True)

    #get a list with HeatSlack tech
    tech_HeatSlack = [k for k,v in mapping['SORT'].items() if v == 'HeatSlack']
    tech_HeatSlack_original = tech_HeatSlack
    tech_HeatSlack.append('Td ' )

# --------------------- PART TO DO WITH LTLayer ---------------------------- #
    #Part of the code where we check the ratio of production of all of the boilers
    LTLayers = pd.read_csv(input_folder + 'LTLayers.txt', delimiter='\t')
    LTLayerscolumns = LTLayers.columns.values.tolist()

    # with this we extract all tech which correspond to a HeatSlack
    LTLayers = LTLayers[tech_HeatSlack]

    #Sum all production of Boilers per typical days - groupBy
    LTLayers = LTLayers.groupby(['Td ']).sum()

    LTLayers['DEC_SOLAR'] =  1 #Temporary, just to be able to make my check

    #Multiply the TD production per the mydistri
#    mydistri = distri_TD(n_TD)
    mydistri = [34, 22, 29, 53, 28, 23, 29, 24, 36, 54, 17, 16] #temporary, just to get the idea
    LTLayers = LTLayers.mul(mydistri, axis=0)

    #GroupBy on all typical days, in order to obtain total prod per year of each boiler tech
    LTLayers = LTLayers.sum()

    # --------------------- PART TO DO WITH HTLayer ---------------------------- #
    # Part of the code where we check the ratio of production of all of the boilers
    HTLayers = pd.read_csv(input_folder + 'HTLayers.txt', delimiter='\t')
    HTLayerscolumns = HTLayers.columns.values.tolist()

    # with this we extract all tech which correspond to a HeatSlack
    HTLayers = HTLayers[tech_HeatSlack]

    # Sum all production of Boilers per typical days - groupBy
    HTLayers = HTLayers.groupby(['Td ']).sum()

    # Multiply the TD production per the mydistri - my distri is already defined above
    HTLayers = HTLayers.mul(mydistri, axis=0)

    # GroupBy on all typical days, in order to obtain total prod per year of each boiler tech
    HTLayers = HTLayers.sum()

    # ---------- NOW combine everything (LTLayers ad HTLayers) --------- #
    Heat = pd.concat([LTLayers,HTLayers])

    #get rid of duplicates ; because in any case no technologies can produce HT and LT at the same time - WATHC OUT : how do I get rid o duplicates that are worth zero
    Heat = Heat.sort_values(ascending=False)
    Heat = Heat.groupby(Heat.index).first()

    Heat_tot = Heat.sum()
    Heat_ratio = Heat / Heat_tot

    #Now we can add column to the dataframe (based on index):
    #       - c_maint for each technology (found in DATA_BRUT < 3.2 TECH)
    #       - c_op for each fuel (found in DATA_BRUT < 2.1 RESOURCES)
    #Note : to add the c_op, we need to have a correspondance with the Fuel
    Heat = Heat.to_frame().join(TECH['c_maint'], how='outer')
    #Heat = Heat.drop(0,axis=1)

    Fuel = pd.DataFrame.from_dict(mapping['FUEL_ES'],orient='index')
    Fuel = Fuel.reset_index().set_index(0) #Reset the index so that we can join properly the c_op
    Fuel = Fuel.join(RESOURCES['c_op [M€/GWh]'], how='outer')
    Fuel = Fuel.reset_index().set_index('index') #reset the technology as Index
    Fuel = Fuel.drop('level_0',axis=1) #drop the column with FUEL_ES
    Heat = Heat.join(Fuel, how='outer') #allows us to join c_op to the rest

    # Get the total prod of all Boilers to then define ratios of production for each tech
    Heat_tot = Heat[0].sum()
    Heat[0] = Heat[0] / Heat_tot

    #keep only Boilers tech
    Heat = Heat[Heat.index.isin(tech_HeatSlack_original)]

    #treat the NaN => set to 0
    Heat.fillna(0,inplace=True)

    #GW(h) in ES -> MW(h) in DS - TO DO
    Heat['c_maint'] = Heat['c_maint']/3.6 #go from [M€/GW/y] to [€/MWh] #price of maintenance of the Tech
    Heat['c_op [M€/GWh]'] = Heat['c_op [M€/GWh]']* 1000 #go from [M€/GWh] to [€/MWh] #price for the fuel

    #Get the HeatSlack Price : sum(ratio*(c_maint + c_op)) as full OPEX
    Heat['Price'] = Heat[0]*(Heat['c_op [M€/GWh]']+Heat['c_maint'])
    HeatSlackPrice = Heat['Price'].sum()

    return HeatSlackPrice

########################################################################################################################
#
#
# Input: -numbTD =  the number of typical days in the studied case
# Output: - list of TD's distribution
#
def get_TDFile(numbTD):
    n_TD = numbTD  # enter number of TD's

    # create an empty df
    # Enter the starting date
    date_str = '1/1/2015'
    start = pd.to_datetime(date_str)
    hourly_periods = 8760
    drange = pd.date_range(start, periods=hourly_periods, freq='H')

    TD_final = pd.DataFrame(index=range(0, 8760), columns=['#', 'hour', 'TD'])

    # Select lines of ESTD_12TD where TD are described
    newfile = open("newfile.txt", 'r+')
    ESTD_TD = input_folder + 'ESTD_'+str(n_TD)+'TD.dat'

    with open(ESTD_TD) as f:
        for line in f:
            if line[0] == '(':
                newfile.write(line)


    df = pd.read_csv('newfile.txt', delimiter='\t', index_col=0)
    cols = list(df.columns.values)

    TD_final.at[0, '#'] = int(cols[0])
    TD_final.at[0, 'hour'] = 1
    TD_final.at[0, 'TD'] = int(float(cols[4]))

    for index in range(1, 8760):
        TD_final.at[index, '#'] = int(df.iloc[index - 1, 0])
        TD_final.at[index, 'hour'] = int(df.iloc[index - 1, 2])
        TD_final.at[index, 'TD'] = int(df.iloc[index - 1, 4])

    TD_final.to_csv(input_folder + 'TD_file.csv')

########################################################################################################################

#
#
# Input: -numbTD =  the number of typical days in the studied case
# Output: - list of TD's distribution
#
def distri_TD(numbTD):
    n_TD = numbTD  # enter number of TD's

    TD_final = pd.read_csv(input_folder + 'TD_file.csv')

    distri = [0] * n_TD

    for i in range(1, 366):
        index = i * 24 - 1
        TD = TD_final.loc[index, 'TD']
        distri[TD - 1] = (distri[TD - 1] + 1)

    return distri


########################################################################################################################

#
#
# Input: -TD_DF = Typical days dataframe
#        -hour =  the hour we need to know the TD ([1 , 8760]
#        - numbTD = number of typical days
# Output: - TD number for the concerned hour
#
def get_TD(TD_DF, hour,numbTD):
    n_TD = numbTD  # enter number of TD's

    TD = TD_DF.loc[hour-1,'TD']

    return TD


########################################################################################################################

#
# inputs :   -TD = Typical number
#           -hour = hour number
#           -tech = technology studied
# outputs :  - Values of LT for technology tech , for Typical day TD at h = hour

def search_LTlayers(TD, hour, tech):
    LT_layers = pd.read_csv(input_folder + 'LTlayers.txt', delimiter='\t')

    techno = list(LT_layers.head())
    techno = [x.strip(' ') for x in techno]
    column = techno.index(tech)
    col_names = techno
    LT_layers.columns = col_names
    index = (TD - 1) * 24 + hour - 1
    output = float(LT_layers.at[index, tech])
    return output

########################################################################################################################

#
#
# inputs :   - tech_names = vector containing all the P2H and CHP names
#           - LTlayers = LT_layers.txt file from ES
#           - TYPE = 'SEASONAL' or 'DAILY'
#           - numTD = number of typical days
# Outputs :  - the yearly energy of dhn_sto_daily or dhn_sto_seasonal for each CHP or P2H
#
#
def sto_dhn(tech_names, LTlayers, TYPE, numTD):
    n_TD = numTD
    type = 'TS_DHN_' + TYPE
    f_ts_dhn = search_assets(type, 'f')
    tech_chp = []
    tech_p2h = []
    for elem in tech_names:
        if elem[:3] == 'DHN':
            if elem[4:9] == 'COGEN':
                tech_chp.append(elem)
            else:
                tech_p2h.append(elem)
    tech_all = tech_chp + tech_p2h
    #    print(tech_all)
    sto_dhn_td = pd.DataFrame(index=range(0, 12), columns=tech_all)  # sto of each tech, daily (TD)

    for td in range(1, n_TD + 1):
        dhn_df = pd.DataFrame(index=range(0, 24), columns=tech_all)  # prod of each tech, hourly
        sto_dhn_df = pd.DataFrame(index=range(0, 24), columns=tech_all)  # Sto of each tech, hourly
        for h in range(1, 25):
            sumh = 0
            for t in tech_all:
                value = search_LTlayers(td, h, t)
                dhn_df.at[h - 1, t] = value
                sumh = sumh + value
            if sumh != 0:
                for t in tech_all:
                    sto_dhn_df.at[h - 1, t] = abs(search_LTlayers(td, h, type + '_Pin')) * (dhn_df.loc[h - 1, t]) / sumh
        for t in tech_all:
            sto_dhn_td.at[td - 1, t] = sto_dhn_df[t].sum(axis=0)

    # Multiply each elem of sto_dhn_td by distri_TD => gives total prod Sto of tech_x
    mydistri = distri_TD(n_TD)
    dhn_interm = sto_dhn_td.mul(mydistri, axis=0)

    # Multiply f_ts_dhn_seasonal by each ratio of storage. SizeOfSto_tech_x = f_ts_dhn_seasonal * (total_prod_Sto_tech_x) / (SUMi total_prod_Sto_techi)
    dhn_interm2 = pd.DataFrame(columns=tech_all)
    dhn_sto = pd.DataFrame(columns=tech_all)
    for i in tech_all:
        dhn_interm2.at[0, i] = dhn_interm[i].sum()
    integ_dhn_sto = dhn_interm2.sum(axis=1)

    #    if integ_dhn_sto.values > 0.5 :
    #        for i in tech_all:
    #            dhn_sto.at[0,i] = f_ts_dhn * dhn_interm2.loc[0,i] / (integ_dhn_sto[0]) * 1000 #Storage in MWh in Dispa-Set
    #        return dhn_sto
    #    else :
    #        return nan

    for i in tech_all:
        dhn_sto.at[0, i] = f_ts_dhn * dhn_interm2.loc[0, i] / (integ_dhn_sto[0])
    return dhn_sto



########################################################################################################################

# SEARCH TYPICAL UNITS : for the moment, these functions have to be called before running our scripts, but eventually, it could be useful to integrate it in the run of PowerPlants.py

# Create Dataframe with the DS column names, and as index, all the TECH in DS terminology
# Are these the right columns ? - TO CHECK
column_names = ['Unit', 'PowerCapacity', 'Nunits', 'Zone', 'Technology', 'Fuel', 'Efficiency', 'MinUpTime',
                'MinDownTime', 'RampUpRate', 'RampDownRate', 'StartUpCost_pu', 'NoLoadCost_pu',
                'RampingCost', 'PartLoadMin', 'MinEfficiency', 'StartUpTime', 'CO2Intensity',
                'CHPType', 'CHPPowerToHeat', 'CHPPowerLossFactor', 'COP', 'Tnominal', 'coef_COP_a', 'coef_COP_b',
                'STOCapacity', 'STOSelfDischarge', 'STOMaxChargingPower', 'STOChargingEfficiency', 'CHPMaxHeat']

########################################################################################################################


# Input :    tech = technology studied
#           feat = feature needed regarding to the technology studied
# Output :   Dataframe with oeline containing the new Typical Unit
def search_TypicalUnits(tech, fuel):
    # Créer la liste des fichiers à parcourir
    files = [f for f in glob.glob(input_folder + "**/*.csv", recursive=True)]
    # Parcourir les fichiers dans tous les dossiers et sous-dossiers
    for f in files:
        PowerPlants = pd.read_csv(f)
        # Si on tient le bon couple de tech_fuel...
        if (not PowerPlants.loc[(PowerPlants['Technology'] == tech) & (PowerPlants['Fuel'] == fuel)].empty):
            print('[INFO] : correspondance found for', (tech, fuel), 'in file', f)
            # Sort columns as they should be
            try:
                PowerPlants = PowerPlants[column_names]
                return PowerPlants.loc[(PowerPlants['Technology'] == tech) & (PowerPlants['Fuel'] == fuel)]
            except:
                print('not the right format of column_names in file', f)
            return PowerPlants.loc[(PowerPlants['Technology'] == tech) & (PowerPlants['Fuel'] == fuel)]

    return pd.DataFrame(columns=column_names)  # 'NOTHING for' + tech + fuel

########################################################################################################################


def search_TypicalUnits_CHP(tech, fuel, CHPType):
    # Créer la liste des fichiers à parcourir
    files = [f for f in glob.glob(input_folder + "**/*.csv", recursive=True)]

    # Parcourir les fichiers dans tous les dossiers et sous-dossiers
    for f in files:
        PowerPlants = pd.read_csv(f)

        # Si on tient le bon couple de tech_fuel...
        if (not PowerPlants.loc[(PowerPlants['Technology'] == tech) & (PowerPlants['Fuel'] == fuel) & (
                PowerPlants['CHPType'] == CHPType)].empty):
            print('[INFO] : correspondance found for', (tech, fuel, CHPType), 'in file', f)
            # Sort columns as they should be
            try:
                PowerPlants = PowerPlants[column_names]
                return PowerPlants.loc[(PowerPlants['Technology'] == tech) & (PowerPlants['Fuel'] == fuel) & (
                            PowerPlants['CHPType'] == CHPType)]
            except:
                print('not the right format of column_names in file', f)
            return PowerPlants.loc[(PowerPlants['Technology'] == tech) & (PowerPlants['Fuel'] == fuel) & (
                        PowerPlants['CHPType'] == CHPType)]

        elif (not PowerPlants.loc[(PowerPlants['Technology'] == tech) & (PowerPlants['Fuel'] == fuel) & (
                PowerPlants['CHPType'] == 'Extraction')].empty):

            print('[WARNING] : no correspondance found for', (tech, fuel, CHPType),
                  'but well for CHPType = Extraction ; imposed filling typical units with the Extraction type as',
                  CHPType)
            PowerPlants.loc[
                (PowerPlants['Technology'] == tech) & (PowerPlants['Fuel'] == fuel), 'CHPType'] = 'back-pressure'

            return PowerPlants.loc[(PowerPlants['Technology'] == tech) & (PowerPlants['Fuel'] == fuel)]
    return pd.DataFrame(columns=column_names)  # 'NOTHING for' + tech + fuel


########################################################################################################################

def write_TypicalUnits(missing_tech):
    Typical_Units = pd.read_csv(input_folder + 'Typical_Units.csv')
    powerplants = pd.DataFrame(columns=column_names)

    for (i, j) in missing_tech:
        tmp = search_TypicalUnits(i, j)
        if tmp.empty:
            print('[WARNING] : no correspondance found for the TECH_FUEL :', (i, j))
        else:
            powerplants = pd.concat([powerplants, tmp])
    Typical_Units = pd.concat([Typical_Units, powerplants])
    Typical_Units.to_csv(input_folder + 'Typical_Units_modif.csv', index=False)

########################################################################################################################

def write_TypicalUnits_CHP(missing_tech_CHP):
    Typical_Units = pd.read_csv(input_folder + 'Typical_Units.csv')
    powerplants = pd.DataFrame(columns=column_names)

    for (i, j, k) in missing_tech_CHP:
        tmp = search_TypicalUnits_CHP(i, j, k)
        if tmp.empty:
            print('[WARNING] : no correspondance found for the TECH_FUEL :', (i, j, k))
        else:
            powerplants = pd.concat([powerplants, tmp])
    Typical_Units = pd.concat([Typical_Units, powerplants])
    Typical_Units.to_csv(input_folder + 'Typical_Units_modif.csv', index=False)



########################################################################################################################

# function that reads DATA_brut.xlsx, containing DATA from Energyscope and returns a DataFrame with which we can work with easily to extract data
# Input :    filename = name of the Excel from which we extract DATA (DATA_brut.xlsx)
#           tab = the name of the tab from which we are extracting data
# Output :   the DATA contained in the TAB as a DaataFrame
def from_excel_to_dataFrame(filename, tab):
    # Import the excel file and call it xls_file
    excel_file = pd.ExcelFile(filename)

    # Load the excel_file's Sheet named tab, as a dataframe
    df = excel_file.parse(tab)

    if tab == 'EUD_elec' or tab == 'EUD_heat' or tab == 'AvailibilityFactors':
        df = df.set_index(df.columns[0])

    return df