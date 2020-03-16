import pandas as pd
import glob

input_folder = '../../Inputs/'  # to access DATA - DATA_brut & Typical_Units(to find installed power f [GW or GWh for storage])
output_folder = '../../Outputs/'

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
    input_folder = '../../Inputs/'  # input file = Assets.txt (to find installed power f [GW or GWh for storage])
    output_folder = '../../Outputs/'
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
    input_folder = '../../Inputs/'  # input file = Assets.txt (to find installed power f [GW or GWh for storage])
    output_folder = '../../Outputs/'
    yearbal = pd.read_csv(input_folder + 'YearBalance.txt', delimiter='\t')
    yearbal.set_index('Tech', inplace=True)
    techno = list(yearbal.index)
    techno2 = [x.strip(' ') for x in techno]
    yearbal.set_index([techno2], inplace=True)
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
    input_folder = '../../Outputs/'  # input file = PowerPlant.csv (to find installed power f [GW or GWh for storage])
    output_folder = '../../Outputs/'
    PowPlant = pd.read_csv(input_folder + 'PowerPlants.csv')
    PowPlant.index = PowPlant['Unit']
    tech = ''.join(c for c in tech if c not in '-(){}<>[], ')
    tech = ''.join([i for i in tech if not i.isdigit()])
    output = PowPlant.at[tech, feat]

    return output

########################################################################################################################

#
#
# Input :    type = 'LT' or 'HT'
#           TD = typical day studied
#           hour = hour studied
#           tech  = tech studied
# Output :   Value of the feature asked
#
#
def search_HeatLayers(type, TD, hour, tech):
    input_folder = '../../Inputs/'  # input file = PowerPlant.csv (to find installed power f [GW or GWh for storage])
    output_folder = '../../Outputs/'
    HeatLayers = pd.read_csv(input_folder + type+'layers.txt',delimiter='\t')
    tech = ''.join(c for c in tech if c not in '-(){}<>[], ')
    tech = ''.join([i for i in tech if not i.isdigit()])
    output = HeatLayers.at[((TD-1)*24)+hour - 1, tech]
    return output

########################################################################################################################

# Mapping for matching ES and DS nomenclature

TECH = {u'CCGT': u'COMC',
        u'COAL_US': u'COMC',
        u'COAL_IGCC': u'STUR',
        u'PV': u'PHOT',
        u'GEOTHERMAL': u'STUR',
        u'NUCLEAR': u'STUR',
        u'HYDRO_RIVER': u'HROR',
        u'NEW_HYDRO_RIVER': u'HROR',
        u'WIND': u'WTON',  # HYPOTHESIS : if not specified, Wind is assumed to be ONSHORE - TO CHECK
        u'WIND_OFFSHORE': u'WTOF',
        u'WIND_ONSHORE': u'WTON',
        u'IND_COGEN_GAS': u'STUR',
        u'IND_COGEN_WOOD': u'STUR',
        u'IND_COGEN_WASTE': u'STUR',
        u'IND_BOILER_GAS': u'HeatSlack',
        u'IND_BOILER_WOOD': u'HeatSlack',
        u'IND_BOILER_OIL': u'HeatSlack',
        u'IND_BOILER_COAL': u'HeatSlack',
        u'IND_BOILER_WASTE': u'HeatSlack',
        u'IND_DIRECT_ELEC': u'P2HT',  # TO CHECK
        u'DHN_HP_ELEC': u'P2HT',  # TO CHECK : HP = Heat Pump ?
        u'DHN_COGEN_GAS': u'STUR',
        u'DHN_COGEN_WOOD': u'STUR',
        u'DHN_COGEN_WASTE': u'STUR',
        u'DHN_COGEN_WET_BIOMASS': u'STUR',
        u'DHN_BOILER_GAS': u'HeatSlack',
        u'DHN_BOILER_WOOD': u'HeatSlack',
        u'DHN_BOILER_OIL': u'HeatSlack',
        u'DHN_DEEP_GEO': u'HeatSlack',
        u'DHN_SOLAR': u'HeatSlack',
        u'DEC_HP_ELEC': u'P2HT',  # TO CHECK : HP = Heat Pump ?
        u'DEC_THHP_GAS': u'HeatSlack',
        u'DEC_COGEN_GAS': u'STUR',
        u'DEC_COGEN_OIL': u'STUR',
        u'DEC_ADVCOGEN_GAS': u'STUR',
        u'DEC_ADVCOGEN_H2': u'STUR',
        u'DEC_BOILER_GAS': u'HeatSlack',
        u'DEC_BOILER_WOOD': u'HeatSlack',
        u'DEC_BOILER_OIL': u'HeatSlack',
        u'DEC_SOLAR': u'HeatSlack',
        u'DEC_DIRECT_ELEC': u'P2HT',  # TO CHECK : HP = Heat Pump ?
        u'PHS': u'HPHS',
        u'PHES': u'HPHS',
        u'DAM_STORAGE': u'HDAM',
        u'BATT_LI': u'BATS',
        u'BEV_BATT': u'BEVS',
        u'PHEV_BATT': u'BEVS',
        u'TS_DEC_DIRECT_ELEC': u'THMS',
        u'TS_DEC_HP_ELEC': u'THMS',
        u'TS_DEC_THHP_GAS': u'THMS',
        u'TS_DEC_COGEN_GAS': u'THMS',
        u'TS_DEC_COGEN_OIL': u'THMS',
        u'TS_DEC_ADVCOGEN_GAS': u'THMS',
        u'TS_DEC_ADVCOGEN_H2': u'THMS',
        u'TS_DEC_BOILER_GAS': u'THMS',
        u'TS_DEC_BOILER_WOOD': u'THMS',
        u'TS_DEC_BOILER_OIL': u'THMS',
        u'TS_DHN_DAILY': u'THMS',  # TO DO
        u'TS_DHN_SEASONAL': u'THMS',  # TO DO
        u'SEASONAL_NG': u'',  # TO DO
        u'SEASONAL_H2': u''}  # TO DO

FUEL = {u'CCGT': u'GAS',
        u'COAL_IGCC': u'HRD',
        u'COAL_US': u'HRD',
        u'PV': u'SUN',
        u'GEOTHERMAL': u'GEO',
        u'NUCLEAR': u'NUC',
        u'HYDRO_RIVER': u'WAT',
        u'NEW_HYDRO_RIVER': u'WAT',
        u'WIND': u'WIN',  # IF WIND is not specified, WIND is asumed to be ONSHORE
        u'WIND_OFFSHORE': u'WIN',
        u'WIND_ONSHORE': u'WIN',
        u'IND_COGEN_GAS': u'GAS',
        u'IND_COGEN_WOOD': u'BIO',
        u'IND_COGEN_WASTE': u'WST',
        u'IND_BOILER_GAS': u'HeatSlack',
        u'IND_BOILER_WOOD': u'HeatSlack',
        u'IND_BOILER_OIL': u'HeatSlack',
        u'IND_BOILER_COAL': u'HeatSlack',
        u'IND_BOILER_WASTE': u'HeatSlack',
        u'IND_DIRECT_ELEC': u'OTH',  # P2HT ?
        u'DHN_HP_ELEC': u'OTH',  # P2HT ?
        u'DHN_COGEN_GAS': u'GAS',
        u'DHN_COGEN_WOOD': u'BIO',
        u'DHN_COGEN_WASTE': u'WST',
        u'DHN_COGEN_WET_BIOMASS': u'BIO',
        u'DHN_BOILER_GAS': u'HeatSlack',
        u'DHN_BOILER_WOOD': u'HeatSlack',
        u'DHN_BOILER_OIL': u'HeatSlack',
        u'DHN_DEEP_GEO': u'HeatSlack',
        u'DHN_SOLAR': u'HeatSlack',
        u'DEC_HP_ELEC': u'OTH',  # P2HT ?
        u'DEC_THHP_GAS': u'HeatSlack',
        u'DEC_COGEN_GAS': u'GAS',
        u'DEC_COGEN_OIL': u'OIL',
        u'DEC_ADVCOGEN_GAS': u'GAS',
        u'DEC_ADVCOGEN_H2': u'HYD',
        u'DEC_BOILER_GAS': u'HeatSlack',
        u'DEC_BOILER_WOOD': u'HeatSlack',
        u'DEC_BOILER_OIL': u'HeatSlack',
        u'DEC_SOLAR': u'HeatSlack',
        u'DEC_DIRECT_ELEC': u'OTH',
        u'PHS': u'WAT',
        u'PHES': u'WAT',
        u'DAM_STORAGE': u'WAT',
        u'BATT_LI': u'OTH',  # Right fuel in DS terminology ??
        u'BEV_BATT': u'OTH',  # Right fuel in DS terminology ??
        u'PHEV_BATT': u'OTH',  # Right fuel in DS terminology ??
        u'TS_DEC_DIRECT_ELEC': u'OTH',  # P2HT ?  #Do I need to specify a fuel for Thermal Storage ?
        u'TS_DEC_HP_ELEC': u'OTH',  # P2HT ?
        u'TS_DEC_THHP_GAS': u'GAS',
        u'TS_DEC_COGEN_GAS': u'GAS',
        u'TS_DEC_COGEN_OIL': u'OIL',
        u'TS_DEC_ADVCOGEN_GAS': u'',
        u'TS_DEC_ADVCOGEN_H2': u'',
        u'TS_DEC_BOILER_GAS': u'',
        u'TS_DEC_BOILER_WOOD': u'',
        u'TS_DEC_BOILER_OIL': u''}


########################################################################################################################

# u'TS_DHN_DAILY': u'', #TO DO
# u'TS_DHN_SEASONAL': u'', #TO DO
# u'SEASONAL_NG': u'', #TO DO
#  u'SEASONAL_H2': u''} #TO DO


#
#
# returns the tech's name in the DS format of the ES tech
# Input = ES name
# Output = DS name
#
def search_Dict_ES2DS(tech_ES):
    tech_DS = str(TECH[tech_ES] + '_' + FUEL[tech_ES])
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
    for i in TECH:
        if TECH[i] == type:
            mylist.append(i)
    return mylist

########################################################################################################################
#
#
# Input: -numbTD =  the number of typical days in the studied case
# Output: - list of TD's distribution
#
def distri_TD(numbTD):
    input_folder = '../../Inputs/'  # input file = ESTD_12TD.txt (to find installed power f [GW or GWh for storage])
    output_folder = '../../Outputs/'

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
    ESTD_TD = input_folder + 'ESTD_12TD.dat'
    with open(ESTD_TD) as f:
        for line in f:
            if line[0] == '(':
                newfile.write(line)

    df = pd.read_csv('newfile.txt', delimiter='\t', index_col=0)

    cols = list(df.columns.values)
    TD_final.at[0, '#'] = int(cols[0])
    TD_final.at[0, 'hour'] = 1
    TD_final.at[0, 'TD'] = int(cols[4])
    for index in range(1, 8760):
        TD_final.at[index, '#'] = int(df.iloc[index - 1, 0])
        TD_final.at[index, 'hour'] = int(df.iloc[index - 1, 2])
        TD_final.at[index, 'TD'] = int(df.iloc[index - 1, 4])

    print(TD_final)

    distri = [0] * n_TD

    for i in range(1, 366):
        index = i * 24 - 1
        TD = TD_final.loc[index, 'TD']
        distri[TD - 1] = (distri[TD - 1] + 1)

    return distri

########################################################################################################################

#
#
# Input: -hour =  the hour we need to know the TD ([1 , 8760]
#        - numbTD = number of typical days
# Output: - TD number for the concerned hour
#
def get_TD(hour,numbTD):
    input_folder = '../../Inputs/'  # input file = ESTD_12TD.txt (to find installed power f [GW or GWh for storage])
    output_folder = '../../Outputs/'

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
    ESTD_TD = input_folder + 'ESTD_12TD.dat'
    with open(ESTD_TD) as f:
        for line in f:
            if line[0] == '(':
                newfile.write(line)

    df = pd.read_csv('newfile.txt', delimiter='\t', index_col=0)

    cols = list(df.columns.values)
    TD_final.at[0, '#'] = int(cols[0])
    TD_final.at[0, 'hour'] = 1
    TD_final.at[0, 'TD'] = int(cols[4])
    for index in range(1, 8760):
        TD_final.at[index, '#'] = int(df.iloc[index - 1, 0])
        TD_final.at[index, 'hour'] = int(df.iloc[index - 1, 2])
        TD_final.at[index, 'TD'] = int(df.iloc[index - 1, 4])

    TD = TD_final.loc[hour-1,'TD']

    return TD

########################################################################################################################

#
# inputs :   -TD = Typical number
#           -hour = hour number
#           -tech = technology studied
# outputs :  - Values of LT for technology tech , for Typical day TD at h = hour

def search_LTlayers(TD, hour, tech):
    input_folder = '../../Inputs/'  # input file = Assets.txt (to find installed power f [GW or GWh for storage])
    output_folder = '../../Outputs/'
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


# distri_TD(12)
#
#
# heat_tech = [ 'DHN_HP_ELEC', 'DHN_COGEN_GAS', 'DHN_COGEN_WOOD', 'DHN_COGEN_WET_BIOMASS', 'DHN_COGEN_WASTE']
# LTlayers = '../Inputs/LTlayers.txt'
# print(sto_dhn(heat_tech, LTlayers,'SEASONAL',12))
# print(sto_dhn(heat_tech, LTlayers,'DAILY',12))


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

##List of TECH_FUEL to get : HROR WAT, COMC HRD, STUR BIO/WST/OIL/HYD
# missing_tech = [['HROR','WAT'],['COMC','HRD'],['STUR','BIO'],['STUR','WST'],['STUR','OIL'],['STUR','HYD']]
# missing_chp = [['STUR','BIO','back-pressure'],['STUR','WST','back-pressure'],['STUR','OIL','back-pressure']]
#
# write_TypicalUnits(missing_tech)
# write_TypicalUnits_CHP(missing_chp)