import math
import os
import sys

from dispaset_sidetools.search import *  # line to import the dictionary
from dispaset_sidetools.constants import *  # line to import the dictionary

sys.path.append(os.path.abspath(r'../..'))

# from dispaset_sidetools.common import column_names
# from dispaset_sidetools.search import *  # line to import the dictionary
# from dispaset_sidetools.constants import *  # line to import the dictionary

# folder with the common.py and various Dictionaries
sidetools_folder = '../'
# to access DATA - DATA_preprocessing_BE & Typical_Units(to find installed power f [GW or GWh for storage])
# input_folder = '../../Inputs/EnergyScope/'
# output_folder = '../../Outputs/EnergyScope/'
LTlayers = input_folder + 'LTlayers.txt'

# %% Adjustable inputs that should be modified
# Scenario definition
""" output file: SOURCE + SCENARIO + '_' + str(YEAR) + '_' + CASE """
YEAR = 2015  # considered year
WRITE_CSV_FILES = True  # Write csv database

# Technology definition : if there are some data missing in files, define them here
TECHNOLOGY_THRESHOLD = 0  # threshold (%) below which a technology is considered negligible and no unit is created
STO_THRESHOLD = 0.5  # under STO_THRESHOLD GWh, we don't consider DHN_THMS

separator = ';'

""" 
    Data needed for the Power Plants in DISPA-SET (ES means from ES): 
    - Unit Name
    - Capacity : Power Capacity [MW]    ==>     ES + Up to US [Repartitionning through Typical_Units.csv]
    - Nunits                            ==>     ES Capacity Installed + [Repartitionning through Typical_Units.csv]
    - Year : Comissionning Year         ==>     For each year new powerplant database is needed
    - Technology                        ==>     ES + Dico
    - Fuel : Primary Fuel               ==>     ES + Dico
    - Fuel Prices                       ==>     Set them as constant
    -------- Technology and Fuel in ES correspond to 1 technology in DISPA-SET -------- 
    - Zone :                            ==>     To be implemented based on hystorical data
    - Efficiency [%]                    ==>     ES + Typical_units.csv
    - Efficiency at min load [%]        ==>     Typical_units.csv
    - CO2 Intensity [TCO2/MWh]          ==>     ES + Typical_units.csv
    - Min Load [%]                      ==>     Typical_units.csv
    - Ramp up rate [%/min]              ==>     Typical_units.csv
    - Ramp down rate [%/min]            ==>     Typical_units.csv
    - Start-up time[h]                  ==>     Typical_units.csv
    - MinUpTime [h]                     ==>     Typical_units.csv
    - Min down Time [h]                 ==>     Typical_units.csv
    - No Load Cost [EUR/h]              ==>     Typical_units.csv
    - Start-up cost [EUR]               ==>     Typical_units.csv
    - Ramping cost [EUR/MW]             ==>     Typical_units.csv
    - Presence of CHP [y/n] & Type      ==>     ES + Typical_units.csv
    - CHPPowerToHeat                    ==>     ES + Typical_units.csv
    - CHPPowerLossFactor                ==>     Typical_units.csv
    - CHPMaxHeat                        ==>     if needed from Typical_units.csv

    column_names = [# Generic
                    'Unit', 'PowerCapacity', 'Nunits', 'Zone', 'Zone_th', 'Zone_H2', 'Technology', 'Fuel', 
                    
                    # Technology specific
                    'Efficiency', 'MinUpTime', 'MinDownTime', 'RampUpRate', 'RampDownRate', 'StartUpCost_pu', 
                    'NoLoadCost_pu', 'RampingCost', 'PartLoadMin', 'MinEfficiency', 'StartUpTime', 'CO2Intensity',
                    'WaterWithdrawal', 'WaterConsumption',
                    
                    # CHP related
                    'CHPType', 'CHPPowerToHeat', 'CHPPowerLossFactor', 'CHPMaxHeat',
                    
                    # P2HT related
                    'COP', 'Tnominal', 'coef_COP_a', 'coef_COP_b', 
                    
                    # Storage related
                    'STOCapacity', 'STOSelfDischarge', 'STOMaxChargingPower', 'STOChargingEfficiency']
"""


# function writes the powerplant.xlsx as input of DISPA-SET
# Input :    tech = technology studied, in ES terminology
# Output :   Powerplants.csv written
def define_PP(Zone):
    print('-------------------------------------------------------------')
    print('[INFO] : Starting to build the PowerPlants file of the zone :', Zone)
    print('-------------------------------------------------------------')

    # Read the file
    assets = pd.read_csv(input_folder + Zone + '/' + 'Assets.txt', delimiter='\t')
    assets.columns = assets.columns.str.replace(' ','')

    # Get all Technologies as an index to be used later as index of the PowerPlants DataFrame
    # all_tech = assets.index
    all_tech = assets.loc[:,'TECHNOLOGIES']

    PowerPlants = pd.DataFrame(columns=column_names, index=all_tech)

    # ------------- Get the ES data -------------

    # Get layers_in_out will be used to get :
    #         1) PowerToHeatRatio for CHP TECH
    #         2) COP_nom for COP TECH
    layers_in_out = from_excel_to_dataFrame(input_folder + Zone + '/' + 'DATA_preprocessing.xlsx', 'layers_in_out')
    # Changer les index pour avoir les technologies en Index
    layers_in_out.index = layers_in_out.loc[:, 0]

    # Get 3.3 STO_sto_characteristics will be used to get :
    #         1) STOCpacity for STO TECH
    #         2) STOSellfDischarge for STO TECH
    #         3) STOMaxChargingPower for STO TECH
    STO_caracteristics = from_excel_to_dataFrame(input_folder + Zone + '/' + 'DATA_preprocessing.xlsx',
                                                 'STO_sto_characteristics')
    # Changer les index pour avoir les technologies en Index
    STO_caracteristics.index = STO_caracteristics.iloc[:, 0]
    STO_caracteristics.drop(0, axis=1, inplace=True)
    #       Strip white spaces from column and index
    STO_caracteristics.rename(columns=lambda x: x.strip(), inplace=True)
    STO_caracteristics.index = STO_caracteristics.index.str.strip()

    # Get 3.3 STO_sto_eff_in will be used to get :
    #         1) Efficiency for STO TECH
    STO_eff_in = from_excel_to_dataFrame(input_folder + Zone + '/' + 'DATA_preprocessing.xlsx', 'STO_sto_eff_in')
    # Changer les index pour avoir les technologies en Index
    STO_eff_in.index = STO_eff_in.iloc[:, 0]
    #       Strip white spaces from column and index
    STO_eff_in.rename(columns=lambda x: x.strip(), inplace=True)
    STO_eff_in.index = STO_eff_in.index.str.strip()

    # Get 3.3 STO_sto_eff_out will be used to get :
    #         1) STOChargingEfficiency for STO TECH
    STO_eff_out = from_excel_to_dataFrame(input_folder + Zone + '/' + 'DATA_preprocessing.xlsx', 'STO_sto_eff_out')
    # Changer les index pour avoir les technologies en Index
    STO_eff_out.index = STO_eff_out.iloc[:, 0]
    #       Strip white spaces from colum and index
    STO_eff_out.rename(columns=lambda x: x.strip(), inplace=True)
    STO_eff_out.index = STO_eff_out.index.str.strip()

    # Get Typical Units will be used for :
    #         1) EfficiencyAtMinLoad
    #         2) MinLoad
    #         3) RampUpRate
    #         4) RampDownRate
    #         5) StartUpTime
    #         6) MinUpTime
    #         7) MinDownTime
    #         8) NoLoadCost
    #         9) StartUpCost
    #         10) RampingCost
    Typical_Units = pd.read_csv(input_folder + 'Typical_Units.csv')

    # Fill in the capacity value at Power Capacity column
    # The assets.txt file is not in a right format to work with dataframe to get capacity installed f properly - TO FIX
    PowerPlants['PowerCapacity'] = assets['f_min']
    # Watch out for STO_TECH /!\ - PowerCapacity in DS is MW, where f is in GW/GWh
    # Here everything is in GW/GWh

    # Change TECH from ES terminology to DS terminology ===== WATCH OUT : what about TECH with NaN ??
    # PowerPlants['TECH_DS'] = PowerPlants.index.to_series().map(mapping['TECH'])

    # Fill in the column Technology, Fuel according to the mapping Dictionary defined here above
    PowerPlants['Technology'] = PowerPlants.index.to_series().map(mapping['TECH'])
    PowerPlants['Fuel'] = PowerPlants.index.to_series().map(mapping['FUEL'])

    # the column Sort is added to do some conditional changes for CHP and STO units
    PowerPlants['Sort'] = PowerPlants.index.to_series().map(mapping['SORT'])

    # Get rid of technology that do not have a Sort category + HeatSlack + Thermal Storage
    indexToDrop = PowerPlants[
        (PowerPlants['Sort'].isna()) | (PowerPlants['Sort'] == 'HeatSlack') | (PowerPlants['Sort'] == 'THMS')].index
    print(
        '[WARNING] : several tech are dropped as they are not referenced in the Dictionary : Sort. Here is the list : ',
        PowerPlants[PowerPlants['Sort'].isna()].index.tolist())
    print('[WARNING] : several tech are dropped as they become HeatSlack in DS. Here is the list : ',
          PowerPlants[PowerPlants['Sort'] == 'HeatSlack'].index.tolist())

    OriginalPP = PowerPlants.copy()  # Keep the original data just in case
    PowerPlants.drop(indexToDrop, inplace=True)

    # Getting all CHP/P2HT/ELEC/STO TECH present in the ES implementation
    CHP_tech = list(PowerPlants.loc[PowerPlants['Sort'] == 'CHP'].index)
    P2HT_tech = list(PowerPlants.loc[PowerPlants['Sort'] == 'P2HT'].index)
    HEAT_tech = list(PowerPlants.loc[PowerPlants['Sort'] == 'HEAT'].index)
    ELEC_tech = list(PowerPlants.loc[PowerPlants['Sort'] == 'ELEC'].index)
    STO_tech = list(PowerPlants.loc[PowerPlants['Sort'] == 'STO'].index)
    P2GS_tech = list(PowerPlants.loc[PowerPlants['Sort'] == 'P2GS'].index)
    H2_STO_tech = list(PowerPlants.loc[PowerPlants['Sort'] == 'P2GS_STO'].index)
    THMS_tech = list(PowerPlants.loc[PowerPlants['Sort'] == 'THMS'].index)
    heat_tech = P2HT_tech + CHP_tech + HEAT_tech

    # Variable used later in CHP and P2HT units regarding THMS of DHN units
    tech_sto_daily = 'TS_DHN_DAILY'
    sto_daily_cap = float(OriginalPP.at[tech_sto_daily, 'PowerCapacity'])
    sto_daily_losses = STO_caracteristics.at[tech_sto_daily, 'storage_losses']
    tech_sto_seasonal = 'TS_DHN_SEASONAL'
    sto_seasonal_cap = float(OriginalPP.at[tech_sto_seasonal, 'PowerCapacity'])
    sto_seasonal_losses = STO_caracteristics.at[tech_sto_seasonal, 'storage_losses']

    # --------------- Changes only for ELEC Units  --------------- TO CHECK
    #      - Efficiency
    for tech in ELEC_tech:
        tech_ressource = mapping['FUEL_ES'][tech]  # gets the correct column electricity to look up per CHP tech
        try:
            # If the TECH is ELEC , Efficiency is simply abs(ELECTRICITY/RESSOURCES)
            Efficiency = abs(layers_in_out.at[tech, 'ELECTRICITY'] / layers_in_out.at[tech, tech_ressource])
            PowerPlants.loc[PowerPlants.index == tech, 'Efficiency'] = Efficiency
        except:
            print('[WARNING] : technology ', tech, 'has not been found in layers_in_out')

    # --------------- Changes only for P2GS Units  --------------- TO CHECK
    #      - Efficiency
    #       -
    #       Then comes the associated storage
    #       -
    for tech in P2GS_tech:
        # gets the correct column electricity to look up per CHP tech
        tech_ressource = mapping['FUEL_ES'][tech]
        try:
            # If the TECH is ELEC , Efficiency is simply abs(ELECTRICITY/RESSOURCES) - TO CHECK -------------------
            Efficiency = abs(layers_in_out.at[tech, 'H2'] / layers_in_out.at[tech, tech_ressource])
            PowerPlants.loc[PowerPlants.index == tech, 'Efficiency'] = Efficiency
        except:
            print('[WARNING] : technology ', tech, 'has not been found in layers_in_out')

        try:
            # Associate the right P2GS Storage ith the P2GS production unit - TO DO  ----------------------------
            p2gs_sto = mapping['P2GS_STORAGE'][tech]
            # OK
        except:
            print('[WARNING] : associated P2GS storage ', p2gs_sto, 'is not referenced in the dictionary')

        try:
            # For other Tech ' f' in ES = PowerCapacity, whereas for STO_TECH ' f' = STOCapacity
            STOCapacity = PowerPlants.at[p2gs_sto, 'PowerCapacity']
            STOSelfDischarge = STO_caracteristics.at[p2gs_sto, 'storage_losses']
            StoChargingEfficiency = STO_eff_in.at[p2gs_sto, 'H2']
            # GW to MW
            STOMaxChargingPower = float(STOCapacity) / STO_caracteristics.at[p2gs_sto, 'storage_charge_time'] * 1000
            PowerPlants.loc[
                PowerPlants.index == tech, ['STOCapacity', 'STOSelfDischarge', 'STOMaxChargingPower',
                                            'STOChargingEfficiency']] = [STOCapacity, STOSelfDischarge,
                                                                         STOMaxChargingPower,
                                                                         StoChargingEfficiency]
        except:
            print('[WARNING] : technology ', p2gs_sto, 'has not been found in STO_eff_out/eff_in/_characteristics')

    # --------------- Changes only for CHP Units  --------------- TO CHECK
    #      - Efficiency - TO DO
    #      - PowerToTheatRatio
    #      - CHPType
    #      - TO CHECK/FINISH

    # for each CHP_tech, we will extract the PowerToHeat Ratio and add it to the PowerPlants dataFrame
    for tech in CHP_tech:
        tech_ressource = mapping['FUEL_ES'][tech]  # gets the correct column resources to look up per CHP tech
        tech_heat = mapping['CHP_HEAT'][tech]  # gets the correct column heat to look up per CHP tech
        try:
            PowerToHeatRatio = abs(layers_in_out.at[tech, 'ELECTRICITY'] / layers_in_out.at[tech, tech_heat])
            # If the TECH is CHP  , Efficiency is simply abs(ELECTRICITY/RESSOURCES)
            Efficiency = abs(layers_in_out.at[tech, 'ELECTRICITY'] / layers_in_out.at[tech, tech_ressource])
        except:
            print('[WARNING] : technology ', tech, 'has not been found in layers_in_out')

        PowerPlants.loc[PowerPlants.index == tech, 'CHPPowerToHeat'] = PowerToHeatRatio
        PowerPlants.loc[PowerPlants.index == tech, 'Efficiency'] = Efficiency

        # As far as I know, CHP units in ES have a constant PowerToHeatRatio ; which makes them 'back-pressure' units
        # by default - TO IMPROVE
        PowerPlants.loc[PowerPlants.index == tech, 'CHPType'] = 'back-pressure'

        # Power Capacity of the plant is defined in ES regarding Heat.. But in DS, it is defined regarding Elec.
        # Hence PowerCap_DS = PowerCap_ES*phi ; where phi is the PowerToHeat Ratio
        PowerPlants.loc[PowerPlants.index == tech, 'PowerCapacity'] = float(
            PowerPlants.at[tech, 'PowerCapacity']) * PowerToHeatRatio

    # --------------- Changes only for P2HT Units  --------------- TO CHECK
    #      - Efficiency - it's just 1
    #      - COP
    #      - CHPType : P2H
    #      - TO CHECK/FINISH

    # for each P2HT_tech, we will extract the COP Ratio and add it to the PowerPlants dataFrame
    for tech in P2HT_tech:
        tech_ressource = mapping['FUEL_ES'][tech]
        # gets the correct column heat to look up per CHP tech
        tech_heat = mapping['P2HT_HEAT'][tech]

        # Efficiency = layers_in_out.at[tech,'ELECTRICITY']/layers_in_out.at[tech,tech_ressource]
        Efficiency = 1  # by default - TO CHECK
        PowerPlants.loc[PowerPlants.index == tech, 'Efficiency'] = Efficiency

        try:
            COP = abs(layers_in_out.at[tech, tech_heat] / layers_in_out.at[tech, 'ELECTRICITY'])
        except:
            print('[WARNING] : technology P2HT', tech, 'has not been found in layers_in_out')

        PowerPlants.loc[PowerPlants.index == tech, 'COP'] = COP

        # Power Capacity of the plant is defined in ES regarding Heat..
        # But in DS, it is defined regarding Elec. Hence PowerCap_DS = PowerCap_ES/COP
        PowerPlants.loc[PowerPlants.index == tech, 'PowerCapacity'] = float(PowerPlants.at[tech, 'PowerCapacity']) / COP

    # ----------------------------------THERMAL STORAGE FOR P2HT AND CHP UNITS -----------------------------------------
    # tech_sto can be of 2 cases :
    #    1) either the CHP tech is DEC_TECH, then it has its own personal storage named TS_DEC_TECH
    #    2) or the CHP tech is DHN_TECH. these tech are associated with TS_DHN_DAILY and TS_DHN_SEASONAL ;
    #       we need to investigate several cases:
    #      a) TS_DHN_DAILY/SEASONAL has no capacity installed : it's like DHN_TECH has no storage
    #      b) one of the two TS_DHN_DAILY/SEASONAL has some capacity installed ; we can split this among the COGEN units
    #      c) the two TS_DHN_DAILY/SEASONAL has some capacity installed ; what do we do ? - TO DO

    # get the dhn_daily and dhn_seasonal before the for loop
    # the list used CHP_tech could be brought to a smaller number reducing computation time - through the use of
    # tech.startswith('DHN_') ? - TO DO
    sto_dhn_daily = sto_dhn(Zone, heat_tech, 'DAILY', n_TD)
    sto_dhn_seasonal = sto_dhn(Zone, heat_tech, 'SEASONAL', n_TD)
    tot_sto_dhn_daily = sto_dhn_daily.sum()
    tot_sto_dhn_seasonal = sto_dhn_seasonal.sum()

    for tech in heat_tech:
        try:
            if tech.startswith('DEC_'):
                tech_sto = 'TS_' + tech
                STOCapacity = OriginalPP.at[tech_sto, 'PowerCapacity']

                PowerPlants.at[tech, 'STOCapacity'] = STOCapacity  # in GWh

                STOSelfDischarge = STO_caracteristics.at[tech_sto, 'storage_losses']
                PowerPlants.at[tech, 'STOSelfDischarge'] = STOSelfDischarge  # in GWh
                PowerPlants.at[tech, 'STOMaxChargingPower'] = float(STOCapacity) / STO_caracteristics.at[
                    tech_sto, 'storage_charge_time'] * 1000  # GW to MW
                PowerPlants.at[tech, 'StoChargingEfficiency'] = STO_eff_in.at[tech_sto, 'HEAT_LOW_T_DECEN']

                # Regarding heat coupling - assign to different heat nodes depending on the type of heat produced
                PowerPlants.at[tech, 'Zone_th'] = Zone + '_DEC'  # in GWh

            elif tech.startswith('DHN_'):

                # Regarding heat coupling - assign to different heat nodes depending on the type of heat produced
                PowerPlants.at[tech, 'Zone_th'] = Zone + '_DHN'  # in GWh

                # Investigate case a,b and c
                if (sto_daily_cap < STO_THRESHOLD) & (sto_seasonal_cap < STO_THRESHOLD):  # case a
                    print('[INFO] : neither of TS_DHN_DAILY or TS_DHN_SEASONAL has capacity installed in EnergyScope')
                    PowerPlants.at[tech, 'STOCapacity'] = 0  # in GWh
                    PowerPlants.at[tech, 'STOSelfDischarge'] = 0  # in GWh

                elif (sto_daily_cap > STO_THRESHOLD) | (sto_seasonal_cap > STO_THRESHOLD):
                    if (sto_daily_cap > STO_THRESHOLD) & (sto_seasonal_cap > STO_THRESHOLD):  # case c
                        print('[ERROR] : case NOT HANDLED for the moment : TS_DHN_DAILY and TS_DHN_SEASONAL are '
                              'implemented both above THMS Threshold in EnergyScope')
                        # This case is still to do, to know if we double the tech and split the power capacity among
                        # the two techs

                    else:  # case b
                        if sto_daily_cap > STO_THRESHOLD:

                            # To set the STOCapacity, it is not so trivial - see Guillaume's Function
                            STOCapacity = sto_dhn_daily[tech]
                            PowerPlants.at[tech, 'STOCapacity'] = STOCapacity  # in GWh

                            print('[INFO] : THMS', tech_sto_daily, 'has a capacity installed of', sto_daily_cap,
                                  'split for', tech, 'at the value of', float(STOCapacity))
                            # print('[ERROR] : case NOT HANDLED for the moment : TS_DHN_DAILY and TS_DHN_SEASONAL
                            # are implemented above THMS Threshold in EnergyScope')

                            # STOSelfDischarge = STO_characteristics.at[tech_sto_daily,'storage_losses']
                            PowerPlants.at[tech, 'STOSelfDischarge'] = sto_daily_losses  # in GWh
                            PowerPlants.at[tech, 'STOMaxChargingPower'] = float(STOCapacity) / STO_caracteristics.at[
                                tech_sto_daily, 'storage_charge_time'] * 1000  # GW to MW
                            PowerPlants.at[tech, 'StoChargingEfficiency'] = STO_eff_in.at[
                                tech_sto_daily, 'HEAT_LOW_T_DHN']

                        elif sto_seasonal_cap > STO_THRESHOLD:
                            # To set the STOCapacity, it is not so trivial - Check guillaume's function
                            STOCapacity = sto_dhn_seasonal[tech]
                            PowerPlants.at[tech, 'STOCapacity'] = STOCapacity  # in GWh

                            print('[INFO] : THMS', tech_sto_seasonal, 'has a capacity installed of', sto_seasonal_cap,
                                  'split for', tech, 'at the value of', float(STOCapacity))
                            # print('[ERROR] : case NOT HANDLED for the moment : TS_DHN_DAILY and TS_DHN_SEASONAL
                            # are implemented above THMS Threshold in EnergyScope')

                            # STOSelfDischarge = STO_characteristics.at[tech_sto_seasonal,'storage_losses']
                            # TS_DHN_SEASONAL
                            PowerPlants.at[tech, 'STOSelfDischarge'] = sto_seasonal_losses  # in GWh
                            PowerPlants.at[tech, 'STOMaxChargingPower'] = float(STOCapacity) / STO_caracteristics.at[
                                tech_sto_seasonal, 'storage_charge_time'] * 1000  # GW to MW
                            PowerPlants.at[tech, 'StoChargingEfficiency'] = STO_eff_in.at[
                                tech_sto_seasonal, 'HEAT_LOW_T_DHN']

            elif tech.startswith('IND_'):  # If the unit is IND - so making HIGH TEMPERATURE - no Thermal Storage
                # Regarding heat coupling - assign to different heat nodes depending on the type of heat produced
                PowerPlants.at[tech, 'Zone_th'] = Zone + '_IND'  # in GWh

        except:
            print('[DEBUGGING] : technology ', tech, 'bugs with Thermal Storage')

    # -------------- STO UNITS --------------------- ==> Only units storing ELECTRICITY - TO CHECK
    #      - STOCapacity
    #      - STOSelfDischarge
    #      - PowerCapacity
    #      - STOMaxChargingPower
    #      - STOChargingEfficiency
    #      - Efficiency
    #      - TO CHECK/FINISH

    for tech in STO_tech:

        try:
            # GW to MW is done further #For other Tech ' f' in ES = PowerCapacity,
            # whereas for STO_TECH ' f' = STOCapacity
            STOCapacity = PowerPlants.at[tech, 'PowerCapacity']
            # In ES, the units are [%/s] whereas in DS the units are [%/h]
            STOSelfDischarge = STO_caracteristics.at[tech, 'storage_losses']
            # Characteristics of charging and discharging
            # PowerCapacity = Discharging Capacity for STO_TECH in DS #GW to MW is done further
            PowerCapacity = float(STOCapacity) / STO_caracteristics.at[tech, 'storage_discharge_time']
            STOMaxChargingPower = float(STOCapacity) / STO_caracteristics.at[
                tech, 'storage_charge_time'] * 1000  # GW to MW

            # Because STO_TECH in my dictionaries only concerns Storing giving back to ELECTTRICITY
            StoChargingEfficiency = STO_eff_in.at[tech, 'ELECTRICITY']
            Efficiency = STO_eff_out.at[tech, 'ELECTRICITY']

            PowerPlants.loc[
                PowerPlants.index == tech, ['STOCapacity', 'STOSelfDischarge', 'PowerCapacity', 'STOMaxChargingPower',
                                            'STOChargingEfficiency', 'Efficiency']] = [STOCapacity, STOSelfDischarge,
                                                                                       PowerCapacity,
                                                                                       STOMaxChargingPower,
                                                                                       StoChargingEfficiency,
                                                                                       Efficiency]
        except:
            print('[WARNING] : technology ', tech, 'has not been found in STO_eff_out/eff_in/_characteristics')

    # ------------ TYPICAL UNITS MAKING ----------
    # Part of the code where you fill in DATA coming from typical units

    # ------------------- STILL NEEDED ??? --------------------- - TO CHECK Adding the typical units DATA for (see
    # under) 'MinUpTime', 'MinDownTime', 'RampUpRate', 'RampDownRate', 'StartUpCost_pu', 'NoLoadCost_pu',
    # 'RampingCost', 'PartLoadMin', 'MinEfficiency', 'StartUpTime', 'CO2Intensity',
    Technology_Fuel_in_system = PowerPlants[['Technology', 'Fuel']].copy()
    Technology_Fuel_in_system = Technology_Fuel_in_system.drop_duplicates(subset=['Technology', 'Fuel'], keep='first')
    Technology_Fuel_in_system = Technology_Fuel_in_system.values.tolist()

    #    #Handle NaN - TO CHANGE
    #    PowerPlants.fillna(0,inplace = True)

    # Typical Units : run through Typical_Units with existing Technology_Fuel pairs in ES simulation

    # Characteristics is a list over which we need to iterate for typical Units
    Caracteristics = ['MinUpTime', 'MinDownTime', 'RampUpRate', 'RampDownRate', 'StartUpCost_pu', 'NoLoadCost_pu',
                      'RampingCost', 'PartLoadMin', 'MinEfficiency', 'StartUpTime', 'CO2Intensity',
                      'CHPPowerLossFactor']

    # Get Indexes to iterate over them
    index_list = list(
        PowerPlants.loc[(PowerPlants['Sort'] != 'CHP') & (PowerPlants['Sort'] != 'P2GS')].index.values.tolist())
    index_CHP_list = list(PowerPlants.loc[PowerPlants['Sort'] == 'CHP'].index.values.tolist())
    index_P2GS_list = list(PowerPlants.loc[PowerPlants['Sort'] == 'P2GS'].index.values.tolist())

    # ------------------------------------------------ For non-CHP & non-P2GS units ------------------------------------
    for index in index_list:
        Series = PowerPlants.loc[index]
        Tech = Series['Technology']
        Fuel = Series['Fuel']

        Typical_row = Typical_Units.loc[
            (Typical_Units['Technology'] == Tech) & (Typical_Units['Fuel'] == Fuel)]  # TO CHECK

        # If there is no correspondence in Typical_row
        if Typical_row.empty:
            print('[ERROR] : There was no correspondence for the Technology', Tech, 'and fuel', Fuel,
                  'in the Typical_Units file', '(', index, ')')

            # IS THIS the best way to handle the lack of presence in Typical_Units ? - TO IMPROVE
            print('[WARNING] : So the Technology', Tech, 'and fuel', Fuel, 'will be dropped from dataset')
            PowerPlants.drop(index, inplace=True)

        # If the unit is present in Typical_Units.csv
        else:
            for carac in Caracteristics:
                value = Typical_row[carac].values

                # Adding the needed characteristics of typical units
                # Take into account the cases where the array is of length :
                #    1) nul : no value, the thing is empty
                #    2) 1 : then everything is fine
                #    3) > 1 : then .. What do we do ?
                if len(value) == 0:
                    print('[ERROR] : for characteristics', carac,
                          ' no correspondence has been found for the Technology ', Tech, ' and Fuel ', Fuel, '(', index,
                          ')')
                elif len(value) == 1:  # Normal case
                    value = float(value)
                    PowerPlants.loc[index, carac] = value
                elif len(value) > 1:
                    print('[WARNING] : for characteristics', carac, 'size of value is > 1 for the Technology ', Tech,
                          ' and Fuel ', Fuel)

                # END of the carac loop

            # TO DO LIST :
            # 1) f from EnergyScope is in GW/GWh -> set in MW/MWh
            tmp_PowerCap = float(PowerPlants.loc[index, 'PowerCapacity'])
            PowerPlants.loc[index, 'PowerCapacity'] = tmp_PowerCap * 1000
            tmp_Sto = float(PowerPlants.loc[index, 'STOCapacity'])
            PowerPlants.loc[index, 'STOCapacity'] = tmp_Sto * 1000

            # 2) Divide the capacity in assets into N_Units

            # Take into account the case where PowerCapacity in TypicalUnits is 0 - (e.g for BEVS, P2HT)
            # The solution is to set the PowerCapacity as the one given by EnergyScope and set 1 NUnits
            if (Typical_row['PowerCapacity'].values == 0.):
                Number_units = 1
                PowerPlants.loc[index, 'Nunits'] = Number_units

                # If the technology is not implemented in ES, PowerCapacity will be 0
            elif (float(Typical_row['PowerCapacity'].values) != 0) & (float(Series['PowerCapacity']) == 0.):
                Number_units = 0
                PowerPlants.loc[index, 'Nunits'] = Number_units

            elif (float(Typical_row['PowerCapacity'].values) != 0) & (float(Series['PowerCapacity']) > 0.):
                Number_units = math.ceil(
                    float(PowerPlants.loc[index, 'PowerCapacity']) / float(Typical_row['PowerCapacity']))
                PowerPlants.loc[index, 'Nunits'] = math.ceil(Number_units)
                PowerPlants.loc[index, 'PowerCapacity'] = float(PowerPlants.loc[index, 'PowerCapacity']) / math.ceil(
                    Number_units)

            # 3) P2HT Storage Finish the correspondence for Heat Storage - divide it by the number of units to have
            # it equally shared among the cluster of units If there is a Thermal Storage and then a STOCapacity at
            # the index
            if float(PowerPlants.loc[index, 'STOCapacity']) > 0:
                # Access the row and column of a dataframe : to get to STOCapacity of the checked tech
                if Number_units >= 1:
                    PowerPlants.loc[index, 'STOCapacity'] = float(PowerPlants.loc[index, 'STOCapacity']) / Number_units
                    PowerPlants.loc[index, 'STOMaxChargingPower'] = float(
                        PowerPlants.loc[index, 'STOMaxChargingPower']) / Number_units

        # END of Typical_row.empty loop

    # ------------------------------------------------ For CHP units ------------------------------------------------
    for index in index_CHP_list:
        Series = PowerPlants.loc[index]
        Tech = Series['Technology']
        Fuel = Series['Fuel']
        CHPType = Series['CHPType']

        Typical_row = Typical_Units.loc[(Typical_Units['Technology'] == Tech) & (Typical_Units['Fuel'] == Fuel) & (
                Typical_Units['CHPType'] == CHPType)]

        if (Typical_row.empty) & (CHPType == 'back-pressure'):
            print('[ERROR] : There was no correspondence for the COGEN', (Tech, Fuel, CHPType),
                  'in the Typical_Units file', '(', index, ')')
            print('[INFO] : try to find information for', (Tech, Fuel), 'and CHPType : Extraction')

            CHPType2 = 'Extraction'
            Typical_row = Typical_Units.loc[
                (Typical_Units['Technology'] == Tech) & (Typical_Units['Fuel'] == Fuel) & (
                        Typical_Units['CHPType'] == CHPType2)]
            if not (Typical_row.empty):
                print('[INFO] : Data has been found for', (Tech, Fuel),
                      ' the CHPType Extraction ; will be set as back-pressure for DS model though')

        # If there is no correspondence in Typical_row
        if Typical_row.empty:
            print('[ERROR] : There was no correspondence for the COGEN', (Tech, Fuel, CHPType),
                  'in the Typical_Units file', '(', index, ')')

            # IS THIS the best way to handle the lack of presence in Typical_Units ? - TO IMPROVE
            print('[WARNING] : So the Technology', (Tech, Fuel, CHPType), 'will be dropped from dataset')
            PowerPlants.drop(index, inplace=True)

        # If the unit is present in Typical_Units.csv
        else:
            for carac in Caracteristics:
                value = Typical_row[carac].values

                # Adding the needed characteristics of typical units
                # Take into account the cases where the array is of length :
                #    1) nul : no value, the thing is empty
                #    2) 1 : then everything is fine
                #    3) > 1 : then .. What do we do ?
                if len(value) == 0:
                    print('[ERROR] : for characteristics', carac, ' no correspondence has been found for the COGEN',
                          (Tech, Fuel, CHPType), 'in the Typical_Units file', '(', index, ')')
                elif len(value) == 1:  # Normal case
                    value = float(value)
                    PowerPlants.loc[index, carac] = value
                elif len(value) > 1:
                    print('[WARNING] : for caracteristics', carac, 'size of value is > 1 for the Technology ', Tech,
                          ' and Fuel ', Fuel)

                # Fine-tuning depending on the carac and different types of TECH
                if (carac == 'CHPPowerLossFactor') & (CHPType == 'back-pressure'):
                    if value > 0:
                        print('[WARNING] the CHP back-pressure unit', Tech, Fuel,
                              'has been assigned a non-0 CHPPowerLossFactor. This value has to be forced to 0 to work '
                              'with DISPA-SET')
                        PowerPlants.loc[index, carac] = 0

                # END of the carac loop

            # 1) f from EnergyScope is in GW/GWh -> set in MW/MWh
            tmp_PowerCap = float(PowerPlants.loc[index, 'PowerCapacity'])
            PowerPlants.loc[index, 'PowerCapacity'] = tmp_PowerCap * 1000
            tmp_Sto = float(PowerPlants.loc[index, 'STOCapacity'])
            PowerPlants.loc[index, 'STOCapacity'] = tmp_Sto * 1000

            # 2) Divide the capacity in assets into N_Units

            # Take into account the case where PowerCapacity in TypicalUnits is 0 - (e.g for BEVS, P2HT)
            # The solution is to leave the PowerCapacity as the one given by EnergyScope and set 1 NUnits
            if (Typical_row['PowerCapacity'].values == 0.):
                Number_units = 1
                PowerPlants.loc[index, 'Nunits'] = Number_units

                # If the technology is not implemented in ES, PowerCapacity will be 0
            elif (Typical_row['PowerCapacity'].values != 0) & (float(Series['PowerCapacity']) == 0.):
                Number_units = 0
                PowerPlants.loc[index, 'Nunits'] = Number_units

            elif (Typical_row['PowerCapacity'].values != 0) & (float(Series['PowerCapacity']) > 0.):
                Number_units = math.ceil(
                    float(PowerPlants.loc[index, 'PowerCapacity']) / float(Typical_row['PowerCapacity']))

                PowerPlants.loc[index, 'Nunits'] = math.ceil(Number_units)
                PowerPlants.loc[index, 'PowerCapacity'] = float(PowerPlants.loc[index, 'PowerCapacity']) / math.ceil(
                    Number_units)

            # 3) Thermal Storage Finish the correspondence for Thermal Storage - divide it by the number of units to
            # have it equally shared among the cluster of units

            # If there is a Thermal Storage and then a STOCapacity at the index
            if float(PowerPlants.loc[index, 'STOCapacity']) > 0:
                # Access the row and column of a dataframe : to get to STOCapacity of the checked tech
                if Number_units >= 1:
                    PowerPlants.loc[index, 'STOCapacity'] = float(PowerPlants.loc[index, 'STOCapacity']) / Number_units
                    PowerPlants.loc[index, 'STOMaxChargingPower'] = float(
                        PowerPlants.loc[index, 'STOMaxChargingPower']) / Number_units

    # ------------------------------------------------ For P2GS units ------------------------------------------------
    for index in index_P2GS_list:
        Series = PowerPlants.loc[index]
        Tech = Series['Technology']
        Fuel = Series['Fuel']

        Typical_row = Typical_Units.loc[(Typical_Units['Technology'] == Tech) & (Typical_Units['Fuel'] == Fuel)]

        # If there is no correspondence in Typical_row
        if Typical_row.empty:
            print('[ERROR] : There was no correspondence for the Unit', (Tech, Fuel),
                  'in the Typical_Units file', '(', index, ')')

            # IS THIS the best way to handle the lack of presence in Typical_Units ? - TO IMPROVE
            print('[WARNING] : So the Technology', (Tech, Fuel), 'will be dropped from dataset')
            PowerPlants.drop(index, inplace=True)

        # If the unit is present in Typical_Units.csv
        else:
            for carac in Caracteristics:
                value = Typical_row[carac].values

                # Adding the needed characteristics of typical units
                # Take into account the cases where the array is of length :
                #    1) nul : no value, the thing is empty
                #    2) 1 : then everything is fine
                #    3) > 1 : then .. What do we do ?
                if len(value) == 0:
                    print('[ERROR] : for characteristics', carac, ' no correspondence has been found for the Unit',
                          (Tech, Fuel), 'in the Typical_Units file', '(', index, ')')
                elif len(value) == 1:  # Normal case
                    value = float(value)
                    PowerPlants.loc[index, carac] = value
                elif len(value) > 1:
                    print('[WARNING] : for characteristics', carac, 'size of value is > 1 for the Technology ', Tech,
                          ' and Fuel ', Fuel)

                # END of the carac loop

            # 1) f from EnergyScope is in GW/GWh -> set in MW/MWh
            tmp_PowerCap = float(PowerPlants.loc[index, 'PowerCapacity'])
            PowerPlants.loc[index, 'PowerCapacity'] = tmp_PowerCap * 1000
            tmp_Sto = float(PowerPlants.loc[index, 'STOCapacity'])
            PowerPlants.loc[index, 'STOCapacity'] = tmp_Sto * 1000

            # 2) Divide the capacity in assets into N_Units

            # Take into account the case where PowerCapacity in TypicalUnits is 0 - (e.g for BEVS, P2HT)
            # The solution is to leave the PowerCapacity as the one given by EnergyScope and set 1 NUnits
            if (Typical_row['PowerCapacity'].values == 0.):
                Number_units = 1
                PowerPlants.loc[index, 'Nunits'] = Number_units

                # If the technology is not implemented in ES, PowerCapacity will be 0
            elif (Typical_row['PowerCapacity'].values != 0) & (float(Series['PowerCapacity']) == 0.):
                Number_units = 0
                PowerPlants.loc[index, 'Nunits'] = Number_units

            elif (Typical_row['PowerCapacity'].values != 0) & (float(Series['PowerCapacity']) > 0.):
                Number_units = math.ceil(
                    float(PowerPlants.loc[index, 'PowerCapacity']) / float(Typical_row['PowerCapacity']))
                PowerPlants.loc[index, 'Nunits'] = math.ceil(Number_units)
                PowerPlants.loc[index, 'PowerCapacity'] = float(PowerPlants.loc[index, 'PowerCapacity']) / math.ceil(
                    Number_units)

            # 3) P2GS Storage Finish the correspondence for Thermal Storage - divide it by the number of units to
            # have it equally shared among the cluster of units

            # If there is a Thermal Storage and then a STOCapacity at the index
            if (float(PowerPlants.loc[index, 'STOCapacity']) > 0):
                # Access the row and column of a dataframe : to get to STOCapacity of the checked tech
                if Number_units >= 1:
                    PowerPlants.loc[index, 'STOCapacity'] = float(PowerPlants.loc[index, 'STOCapacity']) / Number_units
                    PowerPlants.loc[index, 'STOMaxChargingPower'] = float(
                        PowerPlants.loc[index, 'STOMaxChargingPower']) / Number_units

    # ------------ Last stuff to do ------------
    # Change the value of the Zone - TO IMPROVE WITH SEVERAL COUNTRIES
    PowerPlants['Zone'] = Zone

    # Put the index as the Units
    PowerPlants['Unit'] = Zone + '_' + PowerPlants.index

    # Sort columns as they should be
    PowerPlants = PowerPlants[column_names]

    # Assign water consumption
    PowerPlants.loc[:, 'WaterWithdrawal'] = 0
    PowerPlants.loc[:, 'WaterConsumption'] = 0

    return PowerPlants


def write_csv_files(file_name, demand, country, write_csv=None):
    filename = file_name + '.csv'
    if write_csv:
        make_dir(output_folder)
        make_dir(output_folder + 'Database')
        folder = output_folder + 'Database/PowerPlants/'
        make_dir(folder)
        make_dir(folder + country)
        demand.to_csv(folder + country + '/' + filename, header=True, index=False)
    else:
        print('[WARNING ]: ' + 'WRITE_CSV_FILES = False, unable to write .csv files')


# loop to write the powerplants for each country
for c in countries:
    allunits = define_PP(c)
    allunits = allunits[allunits['PowerCapacity'] !=0]
    write_csv_files('PowerPlants',allunits, c, True)

# allunits = define_PP(ZONE[0])
# allunits.to_csv(output_folder + 'Database/PowerPlants/' + 'PowerPlants_th_H2.csv', index=False)
