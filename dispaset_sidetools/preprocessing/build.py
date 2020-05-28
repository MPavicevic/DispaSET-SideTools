"""
Script for calling all the other ones for forming different parts of the database

@authors: Matija Pavičević, KU Leuven
"""


from .get_capacities.get_Capacities_ARES_APP import get_allunits, get_hydro_units, powerplant_data_preprocessing, \
    get_temba_plants, assign_typical_units
from .get_demand.get_Demand_ARES_APP import get_demands
from .get_fuel_prices.get_FP_ARES_APP import get_fuel_prices
from .get_NTCs.get_NTC_ARES_APP import get_NTCs
from .get_outages.get_OF_ARES_APP import get_outages
from ..common import write_csv_files


def create_powerplants(temba_inputs, pp_data, hydro_data, typical_units, typical_cooling, countries, YEAR,
                               EFFICIENCY, TEMBA=False, scenario=False, write_csv = False):
    """
    Function that calls functions from all the scripts dedicated for individual parts of the database
    :param temba_inputs:        path to the TEMBA outputs
    :param pp_data:             path to the historic power plant data
    :param hydro_data:          path to the hydro data
    :param typical_units:       path to the typical units
    :param typical_cooling:     path to the typical cooling systems
    :param countries:           list of countries for which the database should be created
    :param YEAR:                year for which the database should be created
    :param EFFICIENCY:          efficiency of hydro units
    :param TEMBA:               additional units proposed by the TEMBA model (TRUE / FALSE)
    :param scenario:            selected scenario (TEMBA)
    :return:
    """

    if TEMBA is True:
        SOURCE = 'TEMBA'
    else:
        SOURCE = 'JRC'
        scenario = ''

    allunits = get_allunits(
                            get_temba_plants(temba_inputs,
                                             assign_typical_units(powerplant_data_preprocessing(pp_data),
                                                                  typical_units,
                                                                  typical_cooling),
                                             get_hydro_units(hydro_data, EFFICIENCY),
                                             typical_units,
                                             typical_cooling,
                                             YEAR,
                                             TEMBA=TEMBA,
                                             scenario=scenario),
                            countries)

    if TEMBA is True:
        write_csv_files(allunits, 'ARES_APP', SOURCE + '_' + scenario, 'PowerPlants', str(YEAR), write_csv, 'Zonal')
        # with open(input_folder + source_folder + 'TEMBA_capacities_' + scenario + '_' + str(YEAR) + '.p',
        #           'wb') as handle:
        #     pickle.dump(allunits, handle, protocol=pickle.HIGHEST_PROTOCOL)
        # # with open(input_folder + source_folder + 'Units_from_get_Capacities.p', 'rb') as handle:
        # #     allunits = pickle.load(handle)
    else:
        write_csv_files(allunits, 'ARES_APP', SOURCE, 'PowerPlants', str(YEAR), write_csv, 'Zonal')

    return allunits


def create_demand(data_full, data_annual, YEAR, SOURCE = 'JRC', write_csv=False):
    """

    :param data_full:
    :param data_annual:
    :param YEAR:
    :param SOURCE:
    :param write_csv:
    :return:
    """
    data = get_demands(data_full, data_annual, YEAR, SOURCE)
    write_csv_files(data, 'ARES_APP', SOURCE, 'TotalLoadValue', str(YEAR), write_csv, 'Zonal')
    return data

def create_fuel_prices(data_costs, data_fingerprints, data_distance, YEAR, SOURCE = 'JRC', sensitivity='Avg', write_csv=False):
    fuel_prices = get_fuel_prices(data_costs, data_fingerprints, data_distance, YEAR, sensitivity)

    write_csv_files(fuel_prices, 'ARES_APP', SOURCE, 'FuelPrices', str(YEAR), write_csv, 'Zonal')
    return fuel_prices

def create_ntcs(data, YEAR, SOURCE, write_csv=False):
    ntcs = get_NTCs(data,YEAR)

    write_csv_files(ntcs, 'ARES_APP', SOURCE, 'DayAheadNTC', str(YEAR), write_csv, 'Aggregated')
    return ntcs

def create_outages(allunits, generation, capacity_factors, SOURCE, scenario, YEAR, write_csv=False):
    outages = get_outages(allunits, generation, capacity_factors, SOURCE, YEAR)

    if SOURCE == 'TEMBA':
        write_csv_files(outages, 'ARES_APP', SOURCE + '_' + scenario, 'OutageFactors', str(YEAR), write_csv, 'Zonal')
    else:
        write_csv_files(outages, 'ARES_APP', SOURCE, 'OutageFactors', str(YEAR), write_csv, 'Zonal')
    return outages
