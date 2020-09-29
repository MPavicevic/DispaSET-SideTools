# -*- coding: utf-8 -*-
"""
This script generates the PowerPlant Dispa-SET data for the JRC-EU-TIMES runs

@authors: Matija Pavičević, KU Leuven
          Sylvain Quoilin, KU Leuven
"""
from __future__ import division

import logging

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
import pycountry

from random import uniform
from concurrent.futures import ThreadPoolExecutor
from scipy.spatial import cKDTree
from shapely.geometry import Point

# Local source tree imports
from ...common import get_country_codes, commons, alpha3_from_alpha2, used_power_pools

countries = used_power_pools(['NAPP', 'EAPP', 'CAPP', 'SAPP', 'WAPP'])
# load world coastlines
world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
for c in alpha3_from_alpha2(countries):
    world.loc[(world['iso_a3'] == c) & (world['iso_a3'] != '-99') & (world['continent'] == 'Africa'), 'name'] = \
        pycountry.countries.get(alpha_3=c).alpha_2

world_coastlines = gpd.read_file('../Inputs/ARES_Africa/hz772ng0160.shp')
area = pd.read_csv('../Inputs/ARES_Africa/API_AG.SRF.TOTL.K2_DS2_en_csv_v2_1346843.csv', error_bad_lines=False,
                   index_col=1)
for w in area.index:
    world.loc[world['iso_a3'] == w, 'Area'] = area.loc[w, str(2018)]


def distance(country, plot=False, resolution=None):
    """
    Create an image of points and compute the distance to the nearest coast for each one
    :param country:     selected country
    :param plot:        plot the image
    :return:            GeoDataFrame with distance of each point to the nearest coast in km (approximation 1°=110.574km)
    """
    # single geom for a selected country
    geometry = world[world["name"] == country].dissolve(by='name').iloc[0].geometry
    # geometry = world[(world["continent"] == 'Africa') & (world["name"]!='Madagascar')].dissolve(by='continent').iloc[0].geometry

    # single geom for the coastline
    coastline = gpd.clip(world_coastlines.to_crs('EPSG:4326'), geometry.buffer(0)).iloc[0].geometry

    def make_point(id):
        point = None
        while point is None or not geometry.contains(point):
            point = Point(uniform(geometry.bounds[0], geometry.bounds[2]),
                          uniform(geometry.bounds[1], geometry.bounds[3]))
        return {"id": id, "geometry": point}

    def compute_distance(point):
        point['dist_to_coastline'] = point['geometry'].distance(coastline)
        return point

    if resolution is None:
        resolution = 1000

    with ThreadPoolExecutor(max_workers=12) as tpe:
        points = list(tpe.map(make_point, range(resolution)))
        result = list(tpe.map(compute_distance, points))

    gdf = gpd.GeoDataFrame.from_records(result)

    if plot is True:
        ax = gpd.GeoDataFrame.from_records([{"geometry": coastline}]).plot(figsize=(18, 18))
        ax = gdf.plot(ax=ax, column='dist_to_coastline', cmap='rainbow')
        plt.show()
    # Convert to km
    gdf['dist_to_coastline'] = gdf['dist_to_coastline'] * 110.574
    return gdf


# https://gis.stackexchange.com/questions/222315/geopandas-find-nearest-point-in-other-dataframe

def ckdnearest(gdA, gdB):
    nA = np.array(list(gdA.geometry.apply(lambda x: (x.x, x.y))))
    nB = np.array(list(gdB.geometry.apply(lambda x: (x.x, x.y))))
    btree = cKDTree(nB)
    dist, idx = btree.query(nA, k=1)
    gdf = pd.concat(
        [gdA.reset_index(drop=True), gdB.loc[idx, gdB.columns != 'geometry'].reset_index(drop=True),
         pd.Series(dist, name='dist')], axis=1)
    return gdf


# Assing cooling based on wighted average
def assign_cooling(pp_data, TEMBA=None):
    if TEMBA == True:
        rename = {'PowerCapacity': 'Power'}
        pp_data['Capacity'] = pp_data['PowerCapacity']
    for f in ['BIO', 'GAS', 'OIL', 'WST', 'HRD', 'PEA', 'GEO', 'OTH', 'WIN', 'SUN']:
        if f == 'WIN':
            pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Cooling'].isna()), 'Cooling'] = 'WIN'
        if f == 'SUN':
            for t in ['PHOT', 'STUR']:
                if t == 'PHOT':
                    pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Technology'] == t) &
                                (pp_data['Cooling'].isna()), 'Cooling'] = 'PV'
                if t == 'STUR':
                    pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Technology'] == t) &
                                (pp_data['Cooling'].isna()), 'Cooling'] = 'CSP'
        if (f == 'GEO') or (f == 'WST') or (f == 'BIO'):
            pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Cooling'].isna()) &
                        (pp_data['Capacity'] < 15), 'Cooling'] = 'AIR'
            pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Cooling'].isna()) &
                        (pp_data['Capacity'] >= 15), 'Cooling'] = 'MDT'
        if f == 'PEA':
            pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Cooling'].isna()), 'Cooling'] = 'MDT'
        if f == 'HRD':
            pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Cooling'].isna()) &
                        (pp_data['Capacity'] < 200), 'Cooling'] = 'AIR'
            pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Cooling'].isna()) &
                        (pp_data['Capacity'] >= 200) & (pp_data['Capacity'] < 450), 'Cooling'] = 'MDT'
            pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Cooling'].isna()), 'Cooling'] = 'OTS'
        if f == 'GAS':
            for t in ['STUR', 'COMC', 'GTUR', 'ICEN']:
                if t == 'ICEN':
                    pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Technology'] == t) & (pp_data['Capacity'] < 15) &
                                (pp_data['Cooling'].isna()), 'Cooling'] = 'AIR'
                    pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Technology'] == t) & (pp_data['Capacity'] >= 15) &
                                (pp_data['Cooling'].isna()), 'Cooling'] = 'OTF'
                if t == 'STUR':
                    pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Technology'] == t) &
                                (pp_data['Capacity'] < 20) & (pp_data['Cooling'].isna()), 'Cooling'] = 'MDT'
                    pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Technology'] == t) &
                                (pp_data['Capacity'] >= 20) & (pp_data['Cooling'].isna()), 'Cooling'] = 'OTF'
                if t == 'COMC':
                    pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Technology'] == t) &
                                (pp_data['Capacity'] >= 200) & (pp_data['Capacity'] < 250) &
                                (pp_data['Cooling'].isna()), 'Cooling'] = 'AIR'
                    pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Technology'] == t) &
                                (pp_data['Capacity'] >= 180) & (pp_data['Capacity'] < 720) &
                                (pp_data['Cooling'].isna()), 'Cooling'] = 'OTF'
                    pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Technology'] == t) &
                                (pp_data['Cooling'].isna()), 'Cooling'] = 'MDT'
                if t == 'GTUR':
                    pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Technology'] == t) & (pp_data['Capacity'] < 15) &
                                (pp_data['Cooling'].isna()), 'Cooling'] = 'AIR'
            pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Cooling'].isna()), 'Cooling'] = 'OTF'
        if (f == 'OIL') or (f == 'OTH'):
            for t in ['STUR', 'COMC', 'GTUR', 'ICEN']:
                if (t == 'COMC') or (t == 'STUR'):
                    pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Technology'] == t) & (pp_data['Capacity'] < 15) &
                                (pp_data['Cooling'].isna()), 'Cooling'] = 'AIR'
                    pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Technology'] == t) &
                                (pp_data['Capacity'] >= 15) & (pp_data['Capacity'] < 720) &
                                (pp_data['Cooling'].isna()), 'Cooling'] = 'OTF'
                    pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Technology'] == t) &
                                (pp_data['Cooling'].isna()), 'Cooling'] = 'MDT'
                if (t == 'ICEN') or (t == 'GTUR'):
                    pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Technology'] == t) & (pp_data['Capacity'] > 0) &
                                (pp_data['Cooling'].isna()), 'Cooling'] = 'AIR'
            pp_data.loc[(pp_data['Fuel'] == f) & (pp_data['Cooling'].isna()), 'Cooling'] = 'OTF'
    # Correct cooling technology based on distance from the coast

    pp_data.loc[:, 'iso2'] = get_country_codes(pp_data['Country'])

    resolution = 5000
    aa = {}
    for c in commons['coastal_countries']['Africa']:
        df = pp_data[pp_data['iso2'] == c]
        gpd1 = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.Longitude, df.Latitude))
        logging.info('Computing image of zone: ' + c + ' Depending on the resolution of the image this might take a '
                                                       'while to complete')
        gpd2 = distance(c, plot=True, resolution=resolution)
        aa[c] = ckdnearest(gpd1, gpd2)
        aa[c].loc[(aa[c]['dist_to_coastline'] <= 15) & (aa[c]['Cooling'] == 'OTF'), 'Cooling'] = 'OTS'
        aa[c].loc[(aa[c]['dist_to_coastline'] > 15) & (aa[c]['Cooling'] == 'OTS'), 'Cooling'] = 'OTF'
        for u in aa[c]['Plant']:
            pp_data.loc[pp_data['Plant'] == u, 'Cooling'] = aa[c].loc[aa[c]['Plant'] == u]['Cooling'].values
    return pp_data


# Input data preprocessing
def powerplant_data_preprocessing(pp_data):
    """
    Function used to preprocess raw excel data
    :param pp_data:     Raw excel data
    :return:            Processed power plant data
    """
    pp_data['Country'] = pp_data['Country'].str.title()
    pp_data['Plant'] = pp_data['Plant'].str.title()
    pp_data = pp_data[~pp_data['Country'].isin(["Ascension Island", 'Tristan Da Cunha', 'St Helena'])]
    pp_data = pp_data[pp_data['Status'].str.contains("OPR")]
    pp_data = pp_data[~pp_data['Fuel'].str.contains("WAT")]
    pp_data = pp_data[~pp_data['Fuel'].str.contains("WSTH")]

    # Convert Fuels and Technologies to Dispa-SET readable format
    fuels = {'AGAS': 'GAS', 'BGAS': 'GAS', 'CGAS': 'GAS', 'CSGAS': 'GAS', 'DGAS': 'GAS', 'FGAS': 'GAS', 'LGAS': 'GAS',
             'LNG': 'GAS', 'LPG': 'GAS', 'REFGAS': 'GAS', 'WOODGAS': 'GAS',
             'BAG': 'BIO', 'BIOMASS': 'BIO', 'BL': 'BIO', 'WOOD': 'BIO',
             'COAL': 'HRD',
             'KERO': 'OIL', 'LIQ': 'OIL', 'SHALE': 'OIL', 'NAP': 'OIL',
             'PEAT': 'PEA',
             'REF': 'WST', 'UNK': 'OTH',
             'UR': 'NUC',
             'WIND': 'WIN'}

    technologies = {'CC/D': 'COMC', 'CC': 'COMC', 'CCSS': 'COMC', 'GT/C': 'COMC', 'GT/CP': 'COMC',
                    'GT': 'GTUR', 'GT/D': 'GTUR', 'GT/H': 'GTUR', 'GT/S': 'GTUR', 'ORC': 'GTUR',
                    'IC': 'ICEN', 'IC/CD': 'ICEN', 'IC/CP': 'ICEN', 'IC/H': 'ICEN',
                    'RSE': 'STUR', 'ST': 'STUR', 'ST/D': 'STUR', 'ST/S': 'STUR', 'ST/G': 'STUR',
                    'PV': 'PHOT',
                    'WTG': 'WTON', 'WTG/O': 'WTOF'}

    cooling = {'MDT': 'MDT/NDT', 'NDT': 'MDT/NDT', 'NDT/D': 'MDT/NDT',
               'OTF': 'OTF', 'OTB': 'OTB/OTS', 'OTS': 'OTB/OTS', 'CSP': 'AIR', 'PV': 'AIR', 'WIN': 'AIR'}
    # cooling = {'CSP': 'AIR', 'PV': 'AIR'}

    pp_data['Fuel'] = pp_data['Fuel'].replace(fuels)
    pp_data['Technology'] = pp_data['Technology'].replace(technologies)
    pp_data = assign_cooling(pp_data)
    pp_data['Cooling'] = pp_data['Cooling'].replace(cooling)
    return pp_data


def assign_typical_units(pp_data, typical_units, typical_cooling):
    """
    Function to assign typical units
    :param pp_data:         Preprocessed powerplant data
    :param typical_units    Typical units from csv files
    :param typical_cooling  Typical cooling systems
    :return:                Data in dispaset readable format
    """
    # Assign data to Dispa-SET readable format
    data = pd.DataFrame(columns=commons['ColumnNames'])
    data['Unit'] = pp_data['Plant']
    data['Zone'] = get_country_codes(list(pp_data['Country']))
    data['Fuel'] = pp_data['Fuel']
    data['Technology'] = pp_data['Technology']
    data['PowerCapacity'] = pp_data['Capacity']
    data['Cooling'] = pp_data['Cooling']

    # Historic units assign only 1 per unit
    data['Nunits'] = 1

    # Assign missing data from typical units
    cols = ['Efficiency', 'MinUpTime', 'MinDownTime', 'RampUpRate', 'RampDownRate', 'StartUpCost_pu', 'NoLoadCost_pu',
            'RampingCost', 'PartLoadMin', 'MinEfficiency', 'StartUpTime', 'CO2Intensity',
            'COP', 'Tnominal', 'coef_COP_a', 'coef_COP_b',
            'STOCapacity', 'STOSelfDischarge', 'STOMaxChargingPower', 'STOChargingEfficiency']

    # Assign cooling data from typical cooling
    cool_cols = ['WaterWithdrawal', 'WaterConsumption']

    for fuel in commons['Fuels']:
        for technology in commons['Technologies']:
            if data.loc[(data['Technology'] == technology) & (data['Fuel'] == fuel)].empty:
                # logging.info(fuel + ' and ' + technology + ' combination not present in this database.')
                continue
            else:
                data.loc[(data['Technology'] == technology) & (data['Fuel'] == fuel), cols] = \
                    typical_units.loc[
                        (typical_units['Technology'] == technology) & (typical_units['Fuel'] == fuel), cols].values
                logging.info('Typical units assigned to: ' + fuel + ' and ' + technology + ' combination.')
                if fuel != 'OTH':
                    for cooling in ['AIR', 'OTF', 'OTB/OTS', 'MDT/NDT']:
                        if data.loc[(data['Technology'] == technology) & (data['Fuel'] == fuel) &
                                    (pp_data['Cooling'] == cooling)].empty:
                            continue
                        else:
                            data.loc[(data['Technology'] == technology) & (data['Fuel'] == fuel) &
                                     (pp_data['Cooling'] == cooling), cool_cols] = typical_cooling.loc[
                                (typical_cooling['Technology'] == technology) & (typical_cooling['Fuel'] == fuel) &
                                (typical_cooling['Process'] == cooling), cool_cols].values
                            logging.info('Typical cooling assigned to: ' + fuel + ' + ' + technology + ' + ' + cooling +
                                         ' combination.')
                else:
                    logging.warning(
                        'Typical cooling was not assigned to ' + fuel + '. No typical data available for OTH!')
    data.loc[(data['Technology'] == 'SCSP') & (data['Fuel'] == 'SUN'), ['STOCapacity']] = \
        data.loc[(data['Technology'] == 'SCSP') & (data['Fuel'] == 'SUN'), ['PowerCapacity']].values * 15
    data.loc[(data['Technology'] == 'SCSP') & (data['Fuel'] == 'SUN'), ['STOMaxChargingPower']] = \
        data.loc[(data['Technology'] == 'SCSP') & (data['Fuel'] == 'SUN'), ['PowerCapacity']].values

    return data


# Preprocess historic hydro units
def get_hydro_units(data_hydro, EFFICIENCY):
    """
    :param data_hydro:      Raw hydro data from xlsx files
    :param EFFICIENCY:      Efficiency of hydro units
    :return hydro_units:    Hydro units in dispaset format
    """
    # Identify and assign ISO_2 country code
    countries_with_hydro = list(data_hydro['Country'])
    codes_hydro = get_country_codes(countries_with_hydro)
    data_hydro['Country Code'] = codes_hydro
    # Create Dispa-SET readable power plant database format
    hydro_units = pd.DataFrame(columns=commons['ColumnNames'])
    # Assign correct names
    hydro_units['Unit'] = data_hydro['Name of dam']
    # Identify installed power
    hydro_units['PowerCapacity'] = data_hydro['Hydroelectricity (MW)']
    # Set all values that are equal to 1
    for key in ['Nunits']:
        hydro_units[key] = 1
    # Set all values that are equal to 0
    for key in ['MinUpTime', 'MinDownTime', 'StartUpCost_pu', 'NoLoadCost_pu', 'RampingCost', 'PartLoadMin',
                'StartUpTime', 'CO2Intensity']:
        hydro_units[key] = 0
    # Set all values that are equal to efficiency
    for key in ['Efficiency', 'MinEfficiency']:
        hydro_units[key] = EFFICIENCY
    # Set all values that are equal to 0.066667
    for key in ['RampUpRate', 'RampDownRate']:
        hydro_units[key] = 0.066667
    # Assign strings
    hydro_units['Fuel'] = 'WAT'
    hydro_units['Zone'] = data_hydro['Country Code']
    # Calculate storage data
    data_hydro['STOCapacity'] = 9.81 * 1000 * data_hydro['Reservoir capacity (million m3)'] * \
                                data_hydro['Dam height (m)'] * EFFICIENCY / 3.6 / 1e3
    # Assign technology based on minimum number of storage hours
    hydro_units.loc[data_hydro['STOCapacity'] / hydro_units['PowerCapacity'] >= 5, 'Technology'] = 'HDAM'
    hydro_units['Technology'].fillna('HROR', inplace=True)
    hydro_units.loc[data_hydro['STOCapacity'] / hydro_units['PowerCapacity'] >= 5, 'STOCapacity'] = data_hydro[
        'STOCapacity']
    # HROR efficiency is 1
    hydro_units.loc[hydro_units['Technology'] == 'HROR', 'Efficiency'] = 1
    hydro_units.loc[:, 'WaterWithdrawal'] = data_hydro.loc[:, 'WaterWithdrawal (m3/MWh)']
    hydro_units.loc[:, 'WaterConsumption'] = data_hydro.loc[:, 'WaterConsumption (m3/MWh)']
    return hydro_units


# Merge two series
def merge_power_plants(data_1, data_2):
    """
    Merge two preprocessed powerplant databases
    :param data_1:      First database, conventional units
    :param data_2:      Second database, hydro units
    :return:            Merged data
    """
    data = data_1.append(data_2, ignore_index=True, sort=False)
    data['PowerCapacity'] = data['PowerCapacity'].astype(float)
    return data


# %% TEMBA Processing
def get_temba_plants(temba_inputs, old_units, hydro_units, typical_units, typical_cooling, YEAR, TEMBA=False,
                     scenario=False):
    """
    Function that adds temba capacities to the existing ones
    :param temba_inputs:    TEMBA projections
    :param hydro_units:     Hydro units
    :param old_units:        Old units
    :param typical_units:    Typical units
    :param typical_cooling:  Typical cooling systems
    :param YEAR:            Year from TEMBA scenarios
    :param TEMBA:           TEMBA is true or false
    :param scenario:        TEMBA scenario
    :return:                Database of power plants
    """
    if TEMBA is True:
        temba_fuels = {'Biomass': 'BIO', 'Biomass with ccs': 'BIO',
                       'Coal': 'HRD', 'Coal with ccs': 'HRD',
                       'Gas': 'GAS', 'Gas with ccs': 'GAS',
                       'Geothermal': 'GEO',
                       'Hydro': 'WAT',
                       'Nuclear': 'NUC',
                       'Oil': 'OIL',
                       'Solar CSP': 'SUN', 'Solar PV': 'SUN',
                       'Wind': 'WIN'}

        temba_techs = {'Biomass': 'STUR', 'Biomass with ccs': 'STUR',
                       'Coal': 'STUR', 'Coal with ccs': 'STUR',
                       'Gas': 'COMC', 'Gas with ccs': 'COMC',
                       'Geothermal': 'STUR',
                       'Hydro': 'WAT',
                       'Nuclear': 'STUR',
                       'Oil': 'ICEN',
                       'Solar CSP': 'STUR', 'Solar PV': 'PHOT',
                       'Wind': 'WTON'}
        # Share of HDAM units and tipical number of sotrage hours per zone
        share = {}
        storage = {}
        for c in hydro_units['Zone']:
            share[c] = hydro_units['PowerCapacity'].loc[
                           (hydro_units['Zone'] == c) & (hydro_units['Technology'] == 'HDAM')].sum() / \
                       hydro_units['PowerCapacity'].loc[(hydro_units['Zone'] == c)].sum()
            storage[c] = hydro_units['STOCapacity'].loc[
                             (hydro_units['Zone'] == c) & (hydro_units['Technology'] == 'HDAM')].sum() / \
                         hydro_units['PowerCapacity'].loc[(hydro_units['Zone'] == c)].sum()
        tmp_hydro_data = pd.DataFrame.from_dict(share, orient='index', columns=['HDAM_share'])
        tmp_hydro_data['STO_hours'] = pd.DataFrame.from_dict(storage, orient='index')
        tmp_hydro_data.fillna(0, inplace=True)
        # Process new TEMBA additions (excluding hydro, assigned later)
        aa = temba_inputs[temba_inputs['parameter'].str.contains("New power generation capacity")]
        aa = aa[aa['scenario'].str.contains(scenario)]
        aa.fillna(0, inplace=True)
        selected_years = list(range(2015, YEAR + 1))
        selected_years = [str(i) for i in selected_years]
        col_names = ['variable', 'scenario', 'country', 'parameter'] + selected_years
        bb = aa[selected_years].sum(axis=1)
        aa['Total'] = bb
        aa['Fuel'] = aa['variable']
        aa['Technology'] = aa['variable']
        aa['Fuel'] = aa['Fuel'].replace(temba_fuels)
        aa['Technology'] = aa['Technology'].replace(temba_techs)
        aa['New'] = 'New'
        temba_fosil = aa[~aa['Fuel'].str.contains("WAT")]
        temba_hydro = aa[aa['Fuel'].str.contains("WAT")]
        temba_fosil['variable'].replace(' ', '_', regex=True, inplace=True)
        temba_fosil['Name'] = temba_fosil[['country', 'variable', 'New']].apply(lambda x: '_'.join(x), axis=1)
        temba_HROR = temba_hydro.copy()
        temba_HDAM = temba_hydro.copy()
        temba_HROR.set_index('country', inplace=True, drop=False)
        temba_HDAM.set_index('country', inplace=True, drop=False)
        temba_HROR = temba_HROR[temba_HROR.index.isin(tmp_hydro_data.index)]
        temba_HDAM = temba_HDAM[temba_HDAM.index.isin(tmp_hydro_data.index)]
        temba_HROR['Total'] = temba_HROR['Total'] * (1 - tmp_hydro_data['HDAM_share'])
        temba_HDAM['Total'] = temba_HDAM['Total'] * tmp_hydro_data['HDAM_share']
        tech_hror = {'WAT': 'HROR'}
        tech_hdam = {'WAT': 'HDAM'}
        temba_HROR['Technology'] = temba_HROR['Technology'].replace(tech_hror)
        temba_HDAM['Technology'] = temba_HDAM['Technology'].replace(tech_hdam)
        temba_HROR['Name'] = temba_HROR[['country', 'Fuel', 'Technology', 'New']].apply(lambda x: '_'.join(x), axis=1)
        temba_HDAM['Name'] = temba_HDAM[['country', 'Fuel', 'Technology', 'New']].apply(lambda x: '_'.join(x), axis=1)
        temba_HROR.reset_index(drop=True, inplace=True)
        temba_HDAM.reset_index(drop=True, inplace=True)
        temba_tmp = temba_fosil.append(temba_HROR, ignore_index=True)
        temba_tmp = temba_tmp.append(temba_HDAM, ignore_index=True)
        temba = pd.DataFrame(columns=commons['ColumnNames'])
        temba['Unit'] = temba_tmp['Name']
        temba['Zone'] = temba_tmp['country']
        temba['Fuel'] = temba_tmp['Fuel']
        temba['Technology'] = temba_tmp['Technology']
        temba['PowerCapacity'] = temba_tmp['Total'] * 1e3
        temba = temba[(temba[['PowerCapacity']] != 0).all(axis=1)]
        # merge HROR series

        # Historic units assign only 1 per unit
        temba['Nunits'] = 1

        # Assign missing data from typical units
        cols = ['Efficiency', 'MinUpTime', 'MinDownTime', 'RampUpRate', 'RampDownRate', 'StartUpCost_pu',
                'NoLoadCost_pu',
                'RampingCost', 'MinEfficiency', 'StartUpTime', 'CO2Intensity', 'COP', 'Tnominal',
                'coef_COP_a',
                'coef_COP_b', 'STOCapacity', 'STOSelfDischarge', 'STOMaxChargingPower', 'STOChargingEfficiency']

        for fuel in commons['Fuels']:
            for technology in commons['Technologies']:
                if temba.loc[(temba['Technology'] == technology) & (temba['Fuel'] == fuel)].empty:
                    # logging.info(fuel + ' and ' + technology + ' combination not present in this database.')
                    continue
                else:
                    temba.loc[(temba['Technology'] == technology) & (temba['Fuel'] == fuel), cols] = \
                        typical_units.loc[
                            (typical_units['Technology'] == technology) & (typical_units['Fuel'] == fuel), cols].values
                    temba.loc[(temba['Technology'] == technology) & (temba['Fuel'] == fuel), 'PartLoadMin'] = \
                        typical_units.loc[
                            (typical_units['Technology'] == technology) &
                            (typical_units['Fuel'] == fuel), 'PartLoadMin'].values * typical_units.loc[
                            (typical_units['Technology'] == technology) &
                            (typical_units['Fuel'] == fuel), 'PowerCapacity'].values / temba.loc[
                            (temba['Technology'] == technology) & (temba['Fuel'] == fuel), 'PowerCapacity']
                    temba.loc[(temba['Technology'] == technology) & (temba['Fuel'] == fuel) &
                              (temba['PartLoadMin'] >= 1), 'PartLoadMin'] = typical_units.loc[
                        (typical_units['Technology'] == technology) &
                        (typical_units['Fuel'] == fuel), 'PartLoadMin'].values
                    logging.info('Typical units assigned to: ' + fuel + ' and ' + technology + ' combination.')

        temba['Cooling'] = np.nan
        temba = assign_cooling(temba, TEMBA=True)
        cooling = {'MDT': 'MDT/NDT', 'NDT': 'MDT/NDT', 'NDT/D': 'MDT/NDT',
                   'OTF': 'OTF/OTS', 'OTB': 'OTF/OTS', 'OTS': 'OTF/OTS'}
        temba['Cooling'] = temba['Cooling'].replace(cooling)

        # Assign cooling data from typical cooling
        cool_cols = ['WaterWithdrawal', 'WaterConsumption']

        for fuel in temba['Fuel'].unique():
            for technology in temba['Technology'].unique():
                if temba.loc[(temba['Technology'] == technology) & (temba['Fuel'] == fuel)].empty:
                    # logging.info(fuel + ' and ' + technology + ' combination not present in this database.')
                    continue
                else:
                    if fuel != 'OTH':
                        for cooling in ['AIR', 'WIN', 'PV', 'CSP', 'OTF/OTS', 'MDT/NDT']:
                            if temba.loc[(temba['Technology'] == technology) & (temba['Fuel'] == fuel) &
                                         (temba['Cooling'] == cooling)].empty:
                                continue
                            else:
                                temba.loc[(temba['Technology'] == technology) & (temba['Fuel'] == fuel) &
                                          (temba['Cooling'] == cooling), cool_cols] = typical_cooling.loc[
                                    (typical_cooling['Technology'] == technology) & (typical_cooling['Fuel'] == fuel) &
                                    (typical_cooling['Process'] == cooling), cool_cols].values
                                logging.info(
                                    'Typical cooling assigned to: ' + fuel + ' + ' + technology + ' + ' + cooling +
                                    ' combination.')
                    else:
                        logging.warning(
                            'Typical cooling was not assigned to ' + fuel + '. No typical data available for OTH!')

        temba.drop(['Cooling', 'Capacity'], axis=1, inplace=True)
        for c in temba.loc[(temba['Technology'] == 'HDAM'), 'Zone']:
            temba.loc[(temba['Technology'] == 'HDAM') & (temba['Zone'] == c), 'STOCapacity'] = \
                tmp_hydro_data.at[c, 'STO_hours'] * \
                temba.loc[(temba['Technology'] == 'HDAM') & (temba['Zone'] == c), 'PowerCapacity']

        # data = data.append(temba, ignore_index=True)
        data = merge_power_plants(merge_power_plants(old_units, hydro_units), temba)
    else:
        logging.info('TEMBA model not selected')
        data = merge_power_plants(old_units, hydro_units)
    return data


# Generation of allunits
def get_allunits(data, countries):
    """
    Function that assigns allunits
    :param data:    data sorted
    :return:        return allunits
    """
    allunits = {}
    unique_fuel = {}
    unique_tech = {}
    for c in countries:
        allunits[c] = data.loc[data['Zone'] == c]
        unique_fuel[c] = list(allunits[c]['Fuel'].unique())
        unique_tech[c] = list(allunits[c]['Technology'].unique())
    return allunits


def create_database(temba_inputs, pp_data, hydro_data, typical_units, typical_cooling, countries, YEAR, EFFICIENCY,
                    TEMBA=False, scenario=False):
    """
    Function for creating power plant database
    :param temba_inputs:
    :param pp_data:
    :param hydro_data:
    :param typical_units:
    :param typical_cooling:
    :param countries:
    :param YEAR:
    :param EFFICIENCY:
    :param TEMBA:
    :param scenario:
    :return:
    """
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
    return allunits
