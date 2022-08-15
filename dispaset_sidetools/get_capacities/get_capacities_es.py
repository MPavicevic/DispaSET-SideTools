import logging
import math
import sys

from ..search import *  # line to import the dictionary
from ..constants import *  # line to import the dictionary
from ..get_timeseries.timeseries_energyscope import get_h2_demand


def get_capacities_from_es(es_outputs, typical_units, td_df, zone=None, write_csv=True, file_name='PowerPlants',
                           technology_threshold=0, storage_threshold=0.5, t_env=273.15 + 35, t_dhn=90, t_ind=120,
                           dispaset_version='2.5', config_link=None):
    """
        Data needed for the Power Plants in DISPA-SET (ES means from ES): 
        - Unit Name
        - Capacity : Power Capacity [MW]    ==>     ES + Up to US [Repartitioning through Typical_Units.csv]
        - Nunits                            ==>     ES Capacity Installed + [Repartitioning through Typical_Units.csv]
        - Year : Comissionning Year         ==>     For each year new powerplant database is needed
        - Technology                        ==>     ES + Dico
        - Fuel : Primary Fuel               ==>     ES + Dico
        - Fuel Prices                       ==>     Set them as constant
        -------- Technology and Fuel in ES correspond to 1 technology in DISPA-SET -------- 
        - Zone :                            ==>     To be implemented based on historical data
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

    # %% Clean data
    es_outputs['assets'] = es_outputs['assets'].groupby(es_outputs['assets'].index).mean()

    # %% Get GWP_op data, this will be used to compute CO2Intensity of different technologies inside DS
    es_outputs['GWP_op'].index = es_outputs['GWP_op'].index.map(mapping['RESOURCE'])

    ###############################################
    # ---- Do the mapping between ES and DS ----- #
    ###############################################

    power_plants = pd.DataFrame(columns=column_names, index=es_outputs['assets'].index)
    # Fill in the capacity value at Power Capacity column
    power_plants['PowerCapacity'] = es_outputs['assets']['f']
    # Watch out for STO_TECH /!\ - PowerCapacity in DS is MW, where f is in GW/GWh
    # Here everything is in GW/GWh

    # Fill in the column Technology, Fuel according to the mapping Dictionary defined here above
    power_plants['Technology'] = power_plants.index.to_series().map(mapping['TECH'])
    logging.info('Mapping of EnergyScope technologies to Dispa-SET technologies complete!')
    power_plants['Fuel'] = power_plants.index.to_series().map(mapping['FUEL'])
    logging.info('Mapping of EnergyScope fuels to Dispa-SET fuels complete!')

    # the column Sort is added to do some conditional changes for CHP and STO units
    power_plants['Sort'] = power_plants.index.to_series().map(mapping['SORT'])

    # Get rid of technology that do not have a Sort category + HeatSlack + Thermal Storage
    index_to_drop = power_plants[
        (power_plants['Sort'].isna()) | (power_plants['Sort'] == 'HeatSlack') | (power_plants['Sort'] == 'THMS') |
        (power_plants['Sort'] == '')].index
    if len(power_plants[power_plants['Sort'].isna()].index.tolist()) != 0:
        logging.warning(
            'Several techs are dropped as they are not referenced in the Dictionary : Sort. Here is the list : ' +
            str(power_plants[power_plants['Sort'].isna()].index.tolist()))
    if len(power_plants[power_plants['Sort'] == 'HeatSlack']) != 0:
        logging.warning('Several techs are dropped as they become HeatSlack in DS. Here is the list : ' +
                        str(power_plants[power_plants['Sort'] == 'HeatSlack'].index.tolist()))

    # Keep the original data just in case
    original_units = power_plants.copy()
    # Assign more technologies to gas units based on occurance in real life
    comc, gt = 4279.6, 1550.7
    power_plants.loc['OCGT', ['PowerCapacity', 'Technology', 'Fuel', 'Sort']] = \
        [power_plants.loc['CCGT', 'PowerCapacity']*gt/(comc+gt), 'GTUR', 'GAS', 'ELEC']
    power_plants.loc['CCGT', 'PowerCapacity'] = power_plants.loc['CCGT', 'PowerCapacity']*comc/(gt+comc)
    power_plants.drop(index_to_drop, inplace=True)

    # Getting all CHP/P2HT/ELEC/STO TECH present in the ES implementation
    chp_tech = list(power_plants.loc[power_plants['Sort'] == 'CHP'].index)
    p2ht_tech = list(power_plants.loc[power_plants['Sort'] == 'P2HT'].index)
    heat_tech = list(power_plants.loc[power_plants['Sort'] == 'HEAT'].index)
    electricity_tech = list(power_plants.loc[power_plants['Sort'] == 'ELEC'].index)
    storage_tech = list(power_plants.loc[power_plants['Sort'] == 'STO'].index)
    p2gs_tech = list(power_plants.loc[power_plants['Sort'] == 'P2GS'].index)
    h2_sto_tech = list(power_plants.loc[power_plants['Sort'] == 'P2GS_STO'].index)
    thms = list(original_units.loc[original_units['Technology'] == 'THMS'].index)
    heat_tech_all = p2ht_tech + chp_tech + heat_tech

    # Variable used later in CHP and P2HT units regarding THMS of DHN units
    tech_sto_daily = 'TS_DHN_DAILY'
    sto_daily_cap = float(original_units.at[tech_sto_daily, 'PowerCapacity'])
    sto_daily_losses = es_outputs['storage_characteristics'].at[tech_sto_daily, 'storage_losses']
    tech_sto_seasonal = 'TS_DHN_SEASONAL'
    sto_seasonal_cap = float(original_units.at[tech_sto_seasonal, 'PowerCapacity'])
    sto_seasonal_losses = es_outputs['storage_characteristics'].at[tech_sto_seasonal, 'storage_losses']

    boundary_sector_inputs = pd.DataFrame(columns=['Sector', 'STOCapacity', 'STOSelfDischarge', 'STOMinSOC',
                                                   'MaxFlexDemand', 'MaxFlexSupply'])

    # %% --------------- Changes only for ELEC Units  --------------- TO CHECK
    #      - Efficiency
    for tech in electricity_tech:
        tech_resource = mapping['FUEL_ES'][tech]  # gets the correct column electricity to look up per CHP tech
        try:
            if tech == 'OCGT':
                efficiency = typical_units.loc[(typical_units['Technology'] == 'GTUR') &
                                               (typical_units['Fuel'] == 'GAS'), 'Efficiency'].values[0]
            # If the TECH is ELEC , Efficiency is simply abs(ELECTRICITY/RESSOURCES)
            else:
                efficiency = abs(es_outputs['layers_in_out'].at[tech, 'ELECTRICITY'] /
                                 es_outputs['layers_in_out'].at[tech, tech_resource])
            power_plants.loc[power_plants.index == tech, 'Efficiency'] = efficiency
        except:
            logging.warning(' Technology ' + tech + 'has not been found in layers_in_out')

    # %% --------------- Changes only for P2GS Units  --------------- TO CHECK
    #      - Efficiency
    #       -
    #       Then comes the associated storage
    #       -
    for tech in p2gs_tech:
        # gets the correct column electricity to look up per CHP tech
        tech_resource = mapping['FUEL_ES'][tech]
        try:
            # If the TECH is ELEC , Efficiency is simply abs(ELECTRICITY/RESSOURCES) - TO CHECK -------------------
            efficiency = abs(es_outputs['layers_in_out'].at[tech, 'H2'] /
                             es_outputs['layers_in_out'].at[tech, tech_resource])
            if dispaset_version == '2.5':
                power_plants.loc[power_plants.index == tech, 'Efficiency'] = efficiency
            elif dispaset_version == '2.5_BS':
                power_plants.loc[power_plants.index == tech, 'Efficiency'] = 1
                power_plants.loc[power_plants.index == tech, 'ChargingEfficiencySector1'] = efficiency
            else:
                logging.error('Wrong Dispa-SET version selected')
                sys.exit(1)
        except:
            logging.warning(' Technology ' + tech + 'has not been found in layers_in_out')

        try:
            # Associate the right P2GS Storage ith the P2GS production unit - TO DO  ----------------------------
            p2gs_sto = mapping['P2GS_STORAGE'][tech]
            # OK
        except:
            logging.warning(' Associated P2GS storage ' + p2gs_sto + 'is not referenced in the dictionary')

        try:
            # For other Tech ' f' in ES = PowerCapacity, whereas for STO_TECH ' f' = STOCapacity
            storage_capacity = power_plants.at[p2gs_sto, 'PowerCapacity']
            storage_self_discharge = es_outputs['storage_characteristics'].at[p2gs_sto, 'storage_losses']
            storage_charging_efficiency = es_outputs['storage_eff_in'].at[p2gs_sto, 'H2']
            # GW to MW
            storage_max_charge_power = float(storage_capacity) / \
                                       es_outputs['storage_characteristics'].at[p2gs_sto, 'storage_charge_time'] * 1000
            if dispaset_version == '2.5':
                power_plants.loc[
                    power_plants.index == tech, ['STOCapacity', 'STOSelfDischarge', 'STOMaxChargingPower',
                                                 'STOChargingEfficiency']] = [storage_capacity, storage_self_discharge,
                                                                              storage_max_charge_power,
                                                                              storage_charging_efficiency]
        except:
            logging.warning(' Technology ' + p2gs_sto + 'has not been found in STO_eff_out/eff_in/_characteristics')

        if dispaset_version == '2.5':

            if zone is None:
                power_plants.at[tech, 'Zone_h2'] = 'ES_H2'
            else:
                power_plants.at[tech, 'Zone_h2'] = zone + '_H2'  # in GWh

        elif dispaset_version == '2.5_BS':

            h2_ts = get_h2_demand(es_outputs['h2_layer'], td_df, config_link['DateRange'], write_csv=False,
                                  dispaset_version='2.5_BS')
            for z in h2_ts.columns:
                boundary_sector_inputs.loc[z, 'MaxFlexDemand'] = h2_ts[z].max()
                boundary_sector_inputs.loc[z, 'Sector'] = z
                boundary_sector_inputs.loc[z, ['STOCapacity', 'STOSelfDischarge']] = [storage_capacity,
                                                                                      storage_self_discharge]
            if zone is None:
                power_plants.loc[tech, 'Sector1'] = 'ES_H2'
            else:
                power_plants.loc[tech, 'Sector1'] = zone + '_H2'

        else:
            logging.error('Wrong Dispa-SET version selected')
            sys.exit(1)

    # %% --------------- Changes only for CHP Units  --------------- TO CHECK
    #      - Efficiency
    #      - PowerToTheatRatio
    #      - CHPType

    # for each CHP_tech, we will extract the PowerToHeat Ratio and add it to the PowerPlants dataFrame
    for tech in chp_tech:
        tech_resource = mapping['FUEL_ES'][tech]  # gets the correct column resources to look up per CHP tech
        tech_heat = mapping['CHP_HEAT'][tech]  # gets the correct column heat to look up per CHP tech
        try:
            power_to_heat_ratio = abs(es_outputs['layers_in_out'].at[tech, 'ELECTRICITY'] /
                                      es_outputs['layers_in_out'].at[tech, tech_heat])
            # If the TECH is CHP  , Efficiency is simply abs(ELECTRICITY/RESSOURCES)
            efficiency = abs(es_outputs['layers_in_out'].at[tech, 'ELECTRICITY'] /
                             es_outputs['layers_in_out'].at[tech, tech_resource])
        except:
            logging.warning(' Technology ' + tech + 'has not been found in layers_in_out')

        power_plants.loc[power_plants.index == tech, 'CHPPowerToHeat'] = power_to_heat_ratio
        power_plants.loc[power_plants.index == tech, 'Efficiency'] = efficiency

        # TODO: Decide how to assign extraction turbines maybe with temperature levels in DH networks
        # CHP units in ES have a constant PowerToHeatRatio which makes them 'back-pressure' units by default - IMPROVE
        if power_plants.loc[tech, 'Technology'] in ['STUR', 'COMC']:
            if tech[0:4] in ['DEC_']:
                power_plants.loc[power_plants.index == tech, 'CHPType'] = 'back-pressure'
            else:
                power_plants.loc[power_plants.index == tech, 'CHPType'] = 'Extraction'
                if tech[0:4] in ['DHN_']:
                    t_extraction = 273.15 + t_dhn
                else:
                    t_extraction = 273.15 + t_ind
                power_plants.loc[power_plants.index == tech, 'CHPPowerLossFactor'] = (t_extraction - t_env) / t_env
        else:
            power_plants.loc[power_plants.index == tech, 'CHPType'] = 'back-pressure'

        # Power Capacity of the plant is defined in ES regarding Heat. But in DS, it is defined regarding Elec.
        # Hence PowerCap_DS = PowerCap_ES*phi ; where phi is the PowerToHeat Ratio
        power_plants.loc[power_plants.index == tech, 'PowerCapacity'] = \
            float(power_plants.at[tech, 'PowerCapacity']) * power_to_heat_ratio

    # %% --------------- Changes only for P2HT Units  --------------- TO CHECK
    #      - Efficiency - it's just 1
    #      - COP

    # for each P2HT_tech, we will extract the COP Ratio and add it to the PowerPlants dataFrame
    for tech in p2ht_tech:
        tech_resource = mapping['FUEL_ES'][tech]
        # gets the correct column heat to look up per CHP tech
        tech_heat = mapping['P2HT_HEAT'][tech]

        # Efficiency = layers_in_out.at[tech,'ELECTRICITY']/layers_in_out.at[tech,tech_ressource]
        power_plants.loc[power_plants.index == tech, 'Efficiency'] = 1.0

        try:
            cop = abs(
                es_outputs['layers_in_out'].at[tech, tech_heat] / es_outputs['layers_in_out'].at[tech, 'ELECTRICITY'])
        except:
            logging.warning(' Technology P2HT' + tech + 'has not been found in layers_in_out')

        power_plants.loc[power_plants.index == tech, 'COP'] = cop

        # Power Capacity of the plant is defined in ES regarding Heat.
        # But in DS, it is defined regarding Elec. Hence PowerCap_DS = PowerCap_ES/COP
        power_plants.loc[power_plants.index == tech, 'PowerCapacity'] = float(
            power_plants.at[tech, 'PowerCapacity']) / cop

    # %% --------------- Changes only for Heat only Units  --------------- TO CHECK
    #      - Efficiency

    for tech in heat_tech:
        tech_resource = mapping['FUEL_ES'][tech]
        heat_type = mapping['HEAT_ONLY_HEAT'][tech]
        # gets the correct column electricity to look up per CHP tech
        try:
            # If the TECH is HEAT , Efficiency is simply abs(HEAT/RESOURCES)
            efficiency = abs(
                es_outputs['layers_in_out'].at[tech, heat_type] / es_outputs['layers_in_out'].at[tech, tech_resource])
            power_plants.loc[power_plants.index == tech, 'Efficiency'] = efficiency
        except:
            logging.warning(' Technology ' + tech + 'has not been found in layers_in_out')

    # %% --------------------------------THERMAL STORAGE FOR P2HT, HEAT and CHP UNITS ----------------------------------
    # tech_sto can be of 2 cases :
    #    1) either the CHP tech is DEC_TECH, then it has its own personal storage named TS_DEC_TECH
    #    2) or the CHP tech is DHN_TECH. these tech are associated with TS_DHN_DAILY and TS_DHN_SEASONAL;

    # get the dhn_daily and dhn_seasonal before the for loop
    # the list used CHP_tech could be brought to a smaller number reducing computation time - through the use of
    # tech.startswith('DHN_') ? - TO DO
    sto_dhn_daily = sto_dhn(heat_tech, 'DAILY', n_TD, es_outputs['assets'], es_outputs['low_t_dhn_Layers'], td_df)
    sto_dhn_seasonal = sto_dhn(heat_tech, 'SEASONAL', n_TD, es_outputs['assets'], es_outputs['low_t_dhn_Layers'], td_df)
    tot_sto_dhn_daily = sto_dhn_daily.sum()
    tot_sto_dhn_seasonal = sto_dhn_seasonal.sum()

    for tech in heat_tech_all:
        try:
            if tech.startswith('DEC_'):
                # Regarding heat coupling - assign to different heat nodes depending on the type of heat produced
                if zone is None:
                    power_plants.at[tech, 'Zone_th'] = 'ES_DEC'
                else:
                    power_plants.at[tech, 'Zone_th'] = zone + '_DEC'  # in GWh

                tech_sto = 'TS_' + tech
                storage_capacity = original_units.at[tech_sto, 'PowerCapacity']

                power_plants.at[tech, 'STOCapacity'] = storage_capacity  # in GWh

                storage_self_discharge = es_outputs['storage_characteristics'].at[tech_sto, 'storage_losses']
                power_plants.at[tech, 'STOSelfDischarge'] = storage_self_discharge  # in GWh
                power_plants.at[tech, 'STOMaxChargingPower'] = float(storage_capacity) / \
                                                               es_outputs['storage_characteristics'].at[
                                                                   tech_sto, 'storage_charge_time'] * 1000  # GW to MW
                power_plants.at[tech, 'StoChargingEfficiency'] = es_outputs['storage_eff_in'].at[
                    tech_sto, 'HEAT_LOW_T_DECEN']

            elif tech.startswith('DHN_'):

                # Regarding heat coupling - assign to different heat nodes depending on the type of heat produced
                if zone is None:
                    power_plants.at[tech, 'Zone_th'] = 'ES_DHN'
                else:  # in GWh
                    power_plants.at[tech, 'Zone_th'] = zone + '_DHN'  # in GWh

            elif tech.startswith('IND_'):  # If the unit is IND - so making HIGH TEMPERATURE - no Thermal Storage
                # Regarding heat coupling - assign to different heat nodes depending on the type of heat produced
                if zone is None:
                    power_plants.at[tech, 'Zone_th'] = 'ES_IND'
                else:
                    power_plants.at[tech, 'Zone_th'] = zone + '_IND'  # in GWh

        except:
            logging.warning('Technology ' + tech + ' doesnt have a thermal storage option in ES')

    # %% -------------- STO UNITS --------------------- ==> Only units storing ELECTRICITY - TO CHECK
    #      - STOCapacity
    #      - STOSelfDischarge
    #      - PowerCapacity
    #      - STOMaxChargingPower
    #      - STOChargingEfficiency
    #      - Efficiency
    #      - TO CHECK/FINISH

    for tech in storage_tech:

        try:
            if tech.startswith('TS_DHN_'):
                # Regarding heat coupling - assign to different heat nodes depending on the type of heat produced
                if zone is None:
                    power_plants.at[tech, 'Zone_th'] = 'ES_DHN'
                else:  # in GWh
                    power_plants.at[tech, 'Zone_th'] = zone + '_DHN'
                storage_charging_efficiency = es_outputs['storage_eff_in'].at[tech, 'HEAT_LOW_T_DHN']
                efficiency = es_outputs['storage_eff_out'].at[tech, 'HEAT_LOW_T_DHN']
            elif tech.startswith('TS_DEC_'):
                if zone is None:
                    power_plants.at[tech, 'Zone_th'] = 'ES_DEC'
                else:  # in GWh
                    power_plants.at[tech, 'Zone_th'] = zone + '_DEC'
                storage_charging_efficiency = es_outputs['storage_eff_in'].at[tech, 'HEAT_LOW_T_DECEN']
                efficiency = es_outputs['storage_eff_out'].at[tech, 'HEAT_LOW_T_DECEN']
            elif tech.startswith('TS_HIGH_'):
                if zone is None:
                    power_plants.at[tech, 'Zone_th'] = 'ES_IND'
                else:  # in GWh
                    power_plants.at[tech, 'Zone_th'] = zone + '_IND'
                storage_charging_efficiency = es_outputs['storage_eff_in'].at[tech, 'HEAT_HIGH_T']
                efficiency = es_outputs['storage_eff_out'].at[tech, 'HEAT_HIGH_T']
            else:
                # Because STO_TECH in my dictionaries only concerns Storing giving back to ELECTTRICITY
                storage_charging_efficiency = es_outputs['storage_eff_in'].at[tech, 'ELECTRICITY']
                efficiency = es_outputs['storage_eff_out'].at[tech, 'ELECTRICITY']

            # GW to MW is done further
            # For other Tech ' f' in ES = PowerCapacity,
            # whereas for STO_TECH ' f' = STOCapacity
            storage_capacity = power_plants.at[tech, 'PowerCapacity']
            # In ES, the units are [%/s] whereas in DS the units are [%/h]
            storage_self_discharge = es_outputs['storage_characteristics'].at[tech, 'storage_losses']
            # Characteristics of charging and discharging
            # PowerCapacity = Discharging Capacity for STO_TECH in DS #GW to MW is done further
            PowerCapacity = float(storage_capacity) / es_outputs['storage_characteristics'].at[
                tech, 'storage_discharge_time']
            storage_max_charge_power = float(storage_capacity) / es_outputs['storage_characteristics'].at[
                tech, 'storage_charge_time'] * 1000  # GW to MW

            power_plants.loc[
                power_plants.index == tech, ['STOCapacity', 'STOSelfDischarge', 'PowerCapacity', 'STOMaxChargingPower',
                                             'STOChargingEfficiency', 'Efficiency']] = [storage_capacity,
                                                                                        storage_self_discharge,
                                                                                        PowerCapacity,
                                                                                        storage_max_charge_power,
                                                                                        storage_charging_efficiency,
                                                                                        efficiency]
        except:
            logging.warning('Technology ' + tech + 'has not been found in STO_eff_out/eff_in/_characteristics')

    # %% ------------ TYPICAL UNITS MAKING ----------
    # Part of the code where you fill in DATA coming from typical units

    technology_fuel_in_system = power_plants[['Technology', 'Fuel']].copy()
    technology_fuel_in_system = technology_fuel_in_system.drop_duplicates(subset=['Technology', 'Fuel'], keep='first')
    technology_fuel_in_system = technology_fuel_in_system.values.tolist()

    # Typical Units : run through Typical_Units with existing Technology_Fuel pairs in ES simulation

    # Characteristics is a list over which we need to iterate for typical Units
    characteristics = ['MinUpTime', 'MinDownTime', 'RampUpRate', 'RampDownRate', 'StartUpCost_pu', 'NoLoadCost_pu',
                       'RampingCost', 'PartLoadMin', 'MinEfficiency', 'StartUpTime', 'CO2Intensity',
                       'CHPPowerLossFactor']

    # Get Indexes to iterate over them
    index_list = list(
        power_plants.loc[(power_plants['Sort'] != 'CHP') & (power_plants['Sort'] != 'P2GS')].index.values.tolist())
    index_chp_list = list(power_plants.loc[power_plants['Sort'] == 'CHP'].index.values.tolist())
    index_p2gs_list = list(power_plants.loc[power_plants['Sort'] == 'P2GS'].index.values.tolist())

    # %% ------------------------------------------------ For non-CHP & non-P2GS units ---------------------------------
    for index in index_list:
        series = power_plants.loc[index]
        tech = series['Technology']
        fuel = series['Fuel']

        typical_row = typical_units.loc[
            (typical_units['Technology'] == tech) & (typical_units['Fuel'] == fuel)]  # TO CHECK

        # If there is no correspondence in Typical_row
        if typical_row.empty:
            logging.error('There was no correspondence for the Technology ' + tech + ' and fuel' + fuel +
                          ' in the Typical_Units file' + '(' + index + '). So the Technology ' + tech + ' and fuel ' +
                          fuel + ' will be dropped from dataset')

            # IS THIS the best way to handle the lack of presence in Typical_Units ? - TO IMPROVE
            power_plants.drop(index, inplace=True)

        # If the unit is present in Typical_Units.csv
        else:
            for carac in characteristics:
                if carac == 'CO2Intensity':
                    if power_plants.loc[index, 'Fuel'] in list(es_outputs['GWP_op'].index):
                        value = np.array([es_outputs['GWP_op'].loc[power_plants.loc[index, 'Fuel']] / power_plants.loc[
                            index, 'Efficiency']])
                    else:
                        value = typical_row[carac].values

                else:
                    value = typical_row[carac].values

                # Adding the needed characteristics of typical units
                # Take into account the cases where the array is of length :
                #    1) nul : no value, the thing is empty
                #    2) 1 : then everything is fine
                #    3) > 1 : then .. What do we do ?
                if len(value) == 0:
                    logging.error(
                        'For characteristics ' + carac + ' no correspondence has been found for the Technology ' +
                        tech + ' and Fuel ' + fuel + '(' + index + ')')
                elif len(value) == 1:  # Normal case
                    value = float(value)
                    power_plants.loc[index, carac] = value
                elif len(value) > 1:
                    power_plants.loc[index, carac] = value.mean()
                    logging.warning(
                        'For characteristics ' + carac + ' size of value is > 1 for the Technology ' + tech +
                        ' and Fuel ' + fuel + '. Mean value will be assigned')

                # END of the carac loop

            # TO DO LIST :
            # 1) f from EnergyScope is in GW/GWh -> set in MW/MWh
            tmp_power_cap = float(power_plants.loc[index, 'PowerCapacity'])
            power_plants.loc[index, 'PowerCapacity'] = tmp_power_cap * 1000
            tmp_Sto = float(power_plants.loc[index, 'STOCapacity'])
            power_plants.loc[index, 'STOCapacity'] = tmp_Sto * 1000

            # 2) Divide the capacity in assets into N_Units

            # Take into account the case where PowerCapacity in TypicalUnits is 0 - (e.g for BEVS, P2HT)
            # The solution is to set the PowerCapacity as the one given by EnergyScope and set 1 NUnits
            if (typical_row['PowerCapacity'].mean() == 0.):
                number_units = 1
                power_plants.loc[index, 'Nunits'] = number_units

                # If the technology is not implemented in ES, PowerCapacity will be 0
            elif (float(typical_row['PowerCapacity'].mean()) != 0) & (float(series['PowerCapacity']) == 0.):
                number_units = 0
                power_plants.loc[index, 'Nunits'] = number_units

            elif (float(typical_row['PowerCapacity'].mean()) != 0) & (float(series['PowerCapacity']) > 0.):
                number_units = math.ceil(
                    float(power_plants.loc[index, 'PowerCapacity']) / float(typical_row['PowerCapacity'].mean()))
                power_plants.loc[index, 'Nunits'] = math.ceil(number_units)
                power_plants.loc[index, 'PowerCapacity'] = float(power_plants.loc[index, 'PowerCapacity']) / math.ceil(
                    number_units)

            # 3) P2HT Storage Finish the correspondence for Heat Storage - divide it by the number of units to have
            # it equally shared among the cluster of units If there is a Thermal Storage and then a STOCapacity at
            # the index
            if float(power_plants.loc[index, 'STOCapacity']) > 0:
                # Access the row and column of a dataframe : to get to STOCapacity of the checked tech
                if number_units >= 1:
                    power_plants.loc[index, 'STOCapacity'] = float(
                        power_plants.loc[index, 'STOCapacity']) / number_units
                    power_plants.loc[index, 'STOMaxChargingPower'] = float(
                        power_plants.loc[index, 'STOMaxChargingPower']) / number_units

        # END of Typical_row.empty loop

    # %% ------------------------------------------------ For CHP units ------------------------------------------------
    for index in index_chp_list:
        series = power_plants.loc[index]
        tech = series['Technology']
        fuel = series['Fuel']
        chp_type = series['CHPType']

        typical_row = typical_units.loc[(typical_units['Technology'] == tech) & (typical_units['Fuel'] == fuel) & (
                typical_units['CHPType'] == chp_type)]

        if (typical_row.empty) & (chp_type == 'back-pressure'):
            logging.error('There was no correspondence for the COGEN ' + tech + '_' + fuel + '_' + chp_type +
                          ' in the Typical_Units file (' + index + ')')
            logging.info('Try to find information for ' + tech + fuel + ' and CHPType : Extraction')

            chp_type2 = 'Extraction'
            typical_row = typical_units.loc[
                (typical_units['Technology'] == tech) & (typical_units['Fuel'] == fuel) & (
                        typical_units['CHPType'] == chp_type2)]
            if not (typical_row.empty):
                logging.info('Data has been found for ' + tech + '_' + fuel +
                             ' the CHPType Extraction ; will be set as back-pressure for DS model though')

        # If there is no correspondence in Typical_row
        if typical_row.empty:
            logging.error('There was no correspondence for the COGEN ' + tech + '_' + fuel + '_' + chp_type +
                          ' in the Typical_Units file (' + index + '). So the Technology ' + tech + '_' + fuel + '_' +
                          chp_type + ' will be dropped from dataset')

            # IS THIS the best way to handle the lack of presence in Typical_Units ? - TO IMPROVE
            power_plants.drop(index, inplace=True)

        # If the unit is present in Typical_Units.csv
        else:
            for carac in characteristics:
                value = typical_row[carac].values

                # Adding the needed characteristics of typical units
                # Take into account the cases where the array is of length :
                #    1) nul : no value, the thing is empty
                #    2) 1 : then everything is fine
                #    3) > 1 : then .. What do we do ?
                if len(value) == 0:
                    logging.error('For characteristics ' + carac + ' no correspondence has been found for the COGEN ' +
                                  tech + '_' + fuel + '_' + chp_type + ' in the Typical_Units file (' + index + ')')
                elif len(value) == 1:  # Normal case
                    value = float(value)
                    power_plants.loc[index, carac] = value
                elif len(value) > 1:
                    power_plants.loc[index, carac] = value.mean()
                    logging.warning(
                        'For characteristics ' + carac + ' size of value is > 1 for the Technology ' + tech +
                        ' and Fuel ' + fuel + '. Mean value will be assigned')

                # Fine-tuning depending on the carac and different types of TECH
                if (carac == 'CHPPowerLossFactor') & (chp_type == 'back-pressure'):
                    if value > 0:
                        logging.warning('The CHP back-pressure unit ' + tech + '_' + fuel +
                                        ' has been assigned a non-0 CHPPowerLossFactor. '
                                        'This value has to be forced to 0 to work with DISPA-SET')
                        power_plants.loc[index, carac] = 0

                # END of the carac loop

            # 1) f from EnergyScope is in GW/GWh -> set in MW/MWh
            tmp_power_cap = float(power_plants.loc[index, 'PowerCapacity'])
            power_plants.loc[index, 'PowerCapacity'] = tmp_power_cap * 1000
            tmp_Sto = float(power_plants.loc[index, 'STOCapacity'])
            power_plants.loc[index, 'STOCapacity'] = tmp_Sto * 1000

            # 2) Divide the capacity in assets into N_Units

            # Take into account the case where PowerCapacity in TypicalUnits is 0 - (e.g for BEVS, P2HT)
            # The solution is to leave the PowerCapacity as the one given by EnergyScope and set 1 NUnits
            if (typical_row['PowerCapacity'].mean() == 0.):
                number_units = 1
                power_plants.loc[index, 'Nunits'] = number_units

                # If the technology is not implemented in ES, PowerCapacity will be 0
            elif (typical_row['PowerCapacity'].mean() != 0) & (float(series['PowerCapacity']) == 0.):
                number_units = 0
                power_plants.loc[index, 'Nunits'] = number_units

            elif (typical_row['PowerCapacity'].mean() != 0) & (float(series['PowerCapacity']) > 0.):
                number_units = math.ceil(
                    float(power_plants.loc[index, 'PowerCapacity']) / float(typical_row['PowerCapacity'].mean()))

                power_plants.loc[index, 'Nunits'] = math.ceil(number_units)
                power_plants.loc[index, 'PowerCapacity'] = float(power_plants.loc[index, 'PowerCapacity']) / math.ceil(
                    number_units)

            # 3) Thermal Storage Finish the correspondence for Thermal Storage - divide it by the number of units to
            # have it equally shared among the cluster of units

            # If there is a Thermal Storage and then a STOCapacity at the index
            if float(power_plants.loc[index, 'STOCapacity']) > 0:
                # Access the row and column of a dataframe : to get to STOCapacity of the checked tech
                if number_units >= 1:
                    power_plants.loc[index, 'STOCapacity'] = float(
                        power_plants.loc[index, 'STOCapacity']) / number_units
                    power_plants.loc[index, 'STOMaxChargingPower'] = float(
                        power_plants.loc[index, 'STOMaxChargingPower']) / number_units

    # %% ------------------------------------------------ For P2GS units -----------------------------------------------
    for index in index_p2gs_list:
        series = power_plants.loc[index]
        tech = series['Technology']
        fuel = series['Fuel']

        typical_row = typical_units.loc[(typical_units['Technology'] == tech) & (typical_units['Fuel'] == fuel)]

        # If there is no correspondence in Typical_row
        if typical_row.empty:
            logging.error('There was no correspondence for the Unit ' + tech + '_' + fuel +
                          'in the Typical_Units file (' + index + '). So the Technology' + tech + '_' + fuel +
                          'will be dropped from dataset')

            # IS THIS the best way to handle the lack of presence in Typical_Units ? - TO IMPROVE
            power_plants.drop(index, inplace=True)

        # If the unit is present in Typical_Units.csv
        else:
            for carac in characteristics:
                value = typical_row[carac].values

                # Adding the needed characteristics of typical units
                # Take into account the cases where the array is of length :
                #    1) nul : no value, the thing is empty
                #    2) 1 : then everything is fine
                #    3) > 1 : then .. What do we do ?
                if len(value) == 0:
                    logging.error('For characteristics' + carac + ' no correspondence has been found for the Unit' +
                                  tech + '_' + fuel + 'in the Typical_Units file (' + index + ')')
                elif len(value) == 1:  # Normal case
                    # value = float(value)
                    power_plants.loc[index, carac] = value.mean()
                elif len(value) > 1:
                    logging.warning('For characteristics' + carac + 'size of value is > 1 for the Technology ' + tech +
                                    ' and Fuel ' + fuel)

                # END of the carac loop

            # 1) f from EnergyScope is in GW/GWh -> set in MW/MWh
            tmp_power_cap = float(power_plants.loc[index, 'PowerCapacity'])
            power_plants.loc[index, 'PowerCapacity'] = tmp_power_cap * 1000
            tmp_Sto = float(power_plants.loc[index, 'STOCapacity'])
            power_plants.loc[index, 'STOCapacity'] = tmp_Sto * 1000

            # 2) Divide the capacity in assets into N_Units

            # Take into account the case where PowerCapacity in TypicalUnits is 0 - (e.g for BEVS, P2HT)
            # The solution is to leave the PowerCapacity as the one given by EnergyScope and set 1 NUnits
            if (typical_row['PowerCapacity'].mean() == 0.):
                number_units = 1
                power_plants.loc[index, 'Nunits'] = number_units

                # If the technology is not implemented in ES, PowerCapacity will be 0
            elif (typical_row['PowerCapacity'].mean() != 0) & (float(series['PowerCapacity']) == 0.):
                number_units = 0
                power_plants.loc[index, 'Nunits'] = number_units

            elif (typical_row['PowerCapacity'].mean() != 0) & (float(series['PowerCapacity']) > 0.):
                number_units = math.ceil(
                    float(power_plants.loc[index, 'PowerCapacity']) / float(typical_row['PowerCapacity'].mean()))
                power_plants.loc[index, 'Nunits'] = math.ceil(number_units)
                power_plants.loc[index, 'PowerCapacity'] = float(power_plants.loc[index, 'PowerCapacity']) / math.ceil(
                    number_units)

            # 3) P2GS Storage Finish the correspondence for Thermal Storage - divide it by the number of units to
            # have it equally shared among the cluster of units

            # If there is a Thermal Storage and then a STOCapacity at the index
            if (float(power_plants.loc[index, 'STOCapacity']) > 0):
                # Access the row and column of a dataframe : to get to STOCapacity of the checked tech
                if number_units >= 1:
                    power_plants.loc[index, 'STOCapacity'] = float(
                        power_plants.loc[index, 'STOCapacity']) / number_units
                    power_plants.loc[index, 'STOMaxChargingPower'] = float(
                        power_plants.loc[index, 'STOMaxChargingPower']) / number_units

    # %% ------------ Last stuff to do ------------
    # Change the value of the Zone - TO IMPROVE WITH SEVERAL COUNTRIES
    if zone is None:
        power_plants['Zone'] = 'ES'
        # Put the index as the Units
        power_plants['Unit'] = 'ES_' + power_plants.index
    else:
        power_plants['Zone'] = zone
        # Put the index as the Units
        power_plants['Unit'] = zone + '_' + power_plants.index

    # Sort columns as they should be
    if dispaset_version == '2.5':
        power_plants = pd.DataFrame(power_plants, columns=column_names)
    if dispaset_version == '2.5_BS':
        power_plants = pd.DataFrame(power_plants, columns=column_names_bs)
        # power_plants = power_plants[column_names_bs]

    # Assign water consumption
    power_plants.loc[:, 'WaterWithdrawal'] = 0
    power_plants.loc[:, 'WaterConsumption'] = 0

    allunits = power_plants
    allunits = allunits[allunits['PowerCapacity'] * allunits['Nunits'] >= technology_threshold]

    if dispaset_version == '2.5':
        if write_csv:
            write_csv_files(file_name, allunits, 'PowerPlants', index=False, write_csv=True)
        return allunits
    if dispaset_version == '2.5_BS':
        boundary_sector_inputs['STOCapacity'] = boundary_sector_inputs['STOCapacity'] * 1000  # to MWh
        boundary_sector_inputs.reset_index(col_level='Sector', drop=True, inplace=True)
        if write_csv:
            write_csv_files(file_name, allunits, 'PowerPlants', index=False, write_csv=True)
            write_csv_files('BoundarySectorInputs', boundary_sector_inputs, 'BoundarySectorInputs', index=True,
                            write_csv=True)
        return allunits, boundary_sector_inputs
