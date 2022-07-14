import pandas as pd
import glob
import time
import logging
import energyscope as es

# import sys, os
# sys.path.append(os.path.abspath(r'..'))

from .common import *
from .constants import *


########################################################################################################################

# function that provides the value contained in the Assets.txt file (output from EnergyScope)
#
# ATTENTION : Assets.txt file has to be provided when running EnergyScope with AMPL
#
# Input :    tech = technology studied
#           feat = feature needed regarding to the technology studied
# Output :   Value of the feature asked

def search_assets(tech, feat, assets, country=None):
    # if country is None:
    #     assets = pd.read_csv(input_folder + country + '/' + 'Assets.txt', delimiter='\t')
    # else:
    #     assets = pd.read_csv(input_folder + '/' + 'Assets.txt', delimiter='\t')

    features = list(assets.head())
    features = [x.strip(' ') for x in features]
    # col_names = features[1:]

    # features.append("end")
    assets.columns = features

    output = float(assets.at[tech, feat])

    return output


def search_year_balance(yearbal, tech, feat):
    """
    Search year balance for individual technologies of interest
    :param yearbal:     Energy Scope year balance
    :param tech:        Technology of interest
    :param feat:        Feature needed regarding to the technology of interest
    :return:            Value of the feature asked
    """
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
def search_PowerPlant(country, tech, feat):
    PowPlant = pd.read_csv(output_folder + 'Database/PowerPlants/' + country + '/' + 'PowerPlants.csv')
    PowPlant.index = PowPlant['Unit']
    tech = ''.join(c for c in tech if c not in '-(){}<>[], ')
    if 'H2' not in tech:
        tech = ''.join([i for i in tech if not i.isdigit()])
    else:
        offset = tech.find('H2') - 3
        tech = tech[offset:]
    output = PowPlant.at[tech, feat]

    return output


########################################################################################################################
# Return the dataframe containing the EnergyScope Storage levels of 'type' 'Elec' or 'Heat'
#
#
#
def get_DistriStorage(country, type):
    if type == 'Heat':
        distriSto = pd.read_csv(input_folder + country + '/' + 'Distri_TS.txt', delimiter='\t')
    else:
        distriSto = pd.read_csv(input_folder + country + '/' + 'Distri_E_stored.txt', delimiter='\t')

    distriSto = distriSto.set_index(distriSto.columns[0])
    return distriSto


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
def search_HeatLayers(LayersDF, TD, hour, tech=None):
    if tech is None:
        output = LayersDF.loc[((TD - 1) * 24) + hour - 1, :]
    elif 'H2' in tech:
        output = LayersDF.at[((TD - 1) * 24) + hour - 1, tech]
    else:
        tech = ''.join(c for c in tech if c not in '-(){}<>[], ')
        tech = ''.join([i for i in tech if not i.isdigit()])
        output = LayersDF.at[((TD - 1) * 24) + hour - 1, tech]
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
def search_ElecLayers(ElecLayersDF, TD, hour, tech):
    if 'H2' in tech:
        output = ElecLayersDF.at[((TD - 1) * 24) + hour - 1, tech]
    else:
        tech = ''.join(c for c in tech if c not in '-(){}<>[], ')
        tech = ''.join([i for i in tech if not i.isdigit()])
        output = ElecLayersDF.at[((TD - 1) * 24) + hour - 1, tech]
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
def search_H2Layers(H2LayersDF, TD, hour, tech):
    tech = ''.join(c for c in tech if c not in '-(){}<>[], ')
    output = H2LayersDF.at[((TD - 1) * 24) + hour - 1, tech]
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
def search_Dict_list(old_list, type):
    mylist = old_list
    for i in mapping['TECH']:
        if mapping['TECH'][i] == type:
            mylist.append(i)
    return mylist


########################################################################################################################

#
#
# Input: -numbTD =  the number of typical days in the studied case
# Output: - list of TD's distribution
#
def distri_TD(n_TD, TD_final, country=None):
    # if country is None:
    #     TD_final = pd.read_csv(input_folder + country + '/' + 'TD_file.csv')
    # else:
    #     TD_final = pd.read_csv(input_folder + '/' + 'TD_file.csv')
    # # TD_final = pd.read_csv(input_folder_fromPrepare + country + '/' +'TD_file.csv')

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
def get_TD(TD_DF, hour, numbTD):
    n_TD = numbTD  # enter number of TD's

    TD = TD_DF.loc[hour - 1, 'TD']

    return TD


########################################################################################################################

#
# inputs :   -TD = Typical number
#           -hour = hour number
#           -tech = technology studied
# outputs :  - Values of LT for technology tech , for Typical day TD at h = hour

def search_LTlayers(country, TD, hour, tech):
    LT_layers = pd.read_csv(input_folder + country + '/' + 'LTlayers.txt', delimiter='\t')

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
def sto_dhn(tech_names, TYPE, numTD, assets, layer_t, td_hourly, country=None):  # Change the number of arguments - TO DO
    n_TD = numTD
    type = 'TS_DHN_' + TYPE
    f_ts_dhn = search_assets(type, 'f', assets)  # Here, change the number of arguments - TO DO
    tech_chp = []
    tech_p2h = []
    tech_heat = []
    for elem in tech_names:
        if elem[:3] == 'DHN':
            if elem[4:9] == 'COGEN':
                tech_chp.append(elem)
            elif (elem[4:10] == 'BOILER') or (elem[4:9] == 'SOLAR') or (elem[4:8] == 'DEEP'):
                tech_heat.append(elem)
            else:
                tech_p2h.append(elem)
    tech_all = tech_chp + tech_p2h + tech_heat

    sto_dhn_td = pd.DataFrame(index=range(0, n_TD), columns=tech_all)  # sto of each tech, daily (TD)

    if f_ts_dhn == 0:  # This means there are no installed capacity, you can return an empty list
        dhn_sto = pd.DataFrame(columns=tech_all)
        return dhn_sto

    # 1) Build a dataframe with LTLayers data
    lt_layers_df_ori = layer_t
    lt_layers_df = lt_layers_df_ori[tech_all].copy()  # Keeping only the releveant columns
    lt_layers_df['SUM'] = lt_layers_df.sum(numeric_only=True, axis=1)  # Sum of all production at each hour

    # 2) Compute Ratios
    lt_layers_df[tech_all] = lt_layers_df[tech_all].div(lt_layers_df['SUM'], axis=0)

    # 3) get Sto_Type_P_in, and Multiply Ratio with Storage Input at each hour
    sto_df = -lt_layers_df_ori[type + '_Pin']  # Storage input at each hour ;
    # NOTE : '-' sign is necessary as P_in is defined as negative
    lt_layers_df[tech_all] = lt_layers_df[tech_all].mul(sto_df, axis=0)

    # 4) groupby, TD, sum
    #       - Add the TD column from the original
    lt_layers_df['Td'] = lt_layers_df_ori.iloc[:, 0].copy()  # Copy the first column which contains the Td
    #       - Drop the SUM column
    lt_layers_df.drop('SUM', axis=1, inplace=True)
    #       - GroupBy
    sto_dhn_td = lt_layers_df.groupby('Td').sum()

    # Multiply each elem of sto_dhn_td by distri_TD => gives total prod Sto of tech_x - HERE
    # if country is None:
    #     mydistri = distri_TD(country, n_TD, td_hourly)
    # else:
    #     mydistri = distri_TD(n_TD)
    mydistri = distri_TD(n_TD, td_hourly, country)
    dhn_interm = sto_dhn_td.mul(mydistri, axis=0)

    # Multiply f_ts_dhn_seasonal by each ratio of storage. SizeOfSto_tech_x = f_ts_dhn_seasonal * (total_prod_Sto_tech_x) / (SUMi total_prod_Sto_techi)
    dhn_interm2 = pd.DataFrame(columns=tech_all)
    dhn_sto = pd.DataFrame(columns=tech_all)
    for i in tech_all:
        dhn_interm2.at[0, i] = dhn_interm[i].sum()
    integ_dhn_sto = dhn_interm2.sum(axis=1)

    for i in tech_all:
        dhn_sto.at[0, i] = f_ts_dhn * dhn_interm2.loc[0, i] / (integ_dhn_sto[0])

    return dhn_sto


########################################################################################################################

# SEARCH TYPICAL UNITS : for the moment, these functions have to be called before running our scripts, but eventually, it could be useful to integrate it in the run of PowerPlants.py

# Create Dataframe with the DS column names, and as index, all the TECH in DS terminology
# Are these the right columns ? - TO CHECK
# column_names = ['Unit', 'PowerCapacity', 'Nunits', 'Zone', 'Technology', 'Fuel', 'Efficiency', 'MinUpTime',
#                 'MinDownTime', 'RampUpRate', 'RampDownRate', 'StartUpCost_pu', 'NoLoadCost_pu',
#                 'RampingCost', 'PartLoadMin', 'MinEfficiency', 'StartUpTime', 'CO2Intensity',
#                 'CHPType', 'CHPPowerToHeat', 'CHPPowerLossFactor', 'COP', 'Tnominal', 'coef_COP_a', 'coef_COP_b',
#                 'STOCapacity', 'STOSelfDischarge', 'STOMaxChargingPower', 'STOChargingEfficiency', 'CHPMaxHeat']

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


def search_TypicalUnits_CHP(country, tech, fuel, CHPType):
    # Créer la liste des fichiers à parcourir
    files = [f for f in glob.glob(input_folder + country + '/' + "**/*.csv", recursive=True)]

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


def process_TD(td_final):
    """
    Process typical days of the year into hourly format, i.e. assign xxx values to 8760 hours of the year
    :param td_final:    typical day dataframe, each typical day assigned to one day of the year
    :return:            hourly dataframe with typical days assigned to each hour of the year
    """

    td_unique = td_final[0].unique()
    td_unique_sorted = pd.DataFrame({'TD_day': np.sort(td_unique), 'TD': range(1, len(np.sort(td_unique).tolist()) + 1, 1)})
    mapping_td = dict(td_unique_sorted[['TD_day', 'TD']].values)
    td_hourly = pd.DataFrame({'h_year': range(1, 8761, 1), 'hour': ''})
    list_int = list(range(1, 25, 1))
    days = pd.Series(td_final[0])
    days = days.repeat(24).reset_index()
    td_hourly['hour'] = np.tile(list_int, len(td_hourly) // len(list_int))
    td_hourly['day'] = days[0]
    td_hourly['TD'] = td_hourly['day'].map(mapping_td)

    return td_hourly


# compute outage factors for technologies using local resources (WOOD, WET_BIOMASS, WASTE)
def compute_outage_factor(config_es, assets, layer_name: str):
    """Computes the Outage Factor in a layer for each TD
    :param config_es:   EnergyScope config
    :param assets:      EnergyScope assets
    :param layer_name:  Name of the layer to compute outages
    :return :           Outage factors for the layer
    """

    layer = es.read_layer(config_es['case_study'], 'layer_' + layer_name).dropna(axis=1)
    layer = layer.loc[:, layer.min(axis=0) < -0.01]
    layer = layer / config_es['all_data']['Layers_in_out'].loc[layer.columns, layer_name]  # compute GWh of output layer
    layer = 1 - layer / assets.loc[layer.columns, 'f']
    return layer.loc[:, layer.max(axis=0) > 1e-3]


def clean_blanks(df, cols=True, idx=True):
    """
    Clean blak spaces in columns and indexes
    :param df:      dataframe to be cleaned
    :param cols:    bool cols True/False
    :param idx:     bool index True/False
    :return:        cleaned dataframe
    """
    if cols:
        df.rename(columns=lambda x: x.strip(), inplace=True)
    if idx:
        df.rename(index=lambda x: x.strip(), inplace=True)
    return df


def assign_td(df, td_df):
    """
    Assign typical days to a dataframe and process to hourly timeseries
    :param df:      dataframe to be processed
    :param td_df:   typical day dataframe
    :return:        new dataframe
    """
    assigned_df = td_df.loc[:, ['TD', 'hour']]
    assigned_df = assigned_df.merge(df, left_on=['TD', 'hour'], right_index=True).sort_index()
    assigned_df.drop(columns=['TD', 'hour'], inplace=True)
    return assigned_df


def write_csv_files(file_name, demand, var_name, index=True, write_csv=None, country=None, inflows=None, heating=False):
    """
    Write csv files in appropriate dispaset format
    :param file_name:   name of the csv file
    :param demand:      timeseries to be saved as csv file
    :param var_name:    name of the variable, can be same as file_name
    :param index:       index bool True/False
    :param write_csv:   write csv file trigger on/off
    :param country:     country demand is located in, one csv file per country/zone
    :param inflows:     special case for inflows
    :param heating:     special case for heating
    :return:
    """
    filename = file_name + '.csv'
    if write_csv:
        make_dir(output_folder)
        make_dir(output_folder + 'Database')
        if inflows is None:
            folder = output_folder + 'Database/' + var_name + '/'
            make_dir(folder)
        else:
            folder = output_folder + 'Database/' + 'HydroData/'
            make_dir(folder)
            folder = folder + var_name + '/'
            make_dir(folder)
        if country is None:
            if heating is True:
                make_dir(folder)
                demand.to_csv(folder + filename, header=True, index=index)
            else:
                make_dir(folder + 'ES/')
                demand.to_csv(folder + 'ES/' + filename, header=True, index=index)
        else:
            make_dir(folder + country)
            demand.to_csv(folder + country + '/' + filename, header=True, index=index)
    else:
        logging.warning('WRITE_CSV_FILES = False, unable to write .csv files inside the ' + var_name + ' folder')
