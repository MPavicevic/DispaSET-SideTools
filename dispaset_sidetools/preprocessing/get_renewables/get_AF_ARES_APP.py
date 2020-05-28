# -*- coding: utf-8 -*-
"""
This script generates the PowerPlant Dispa-SET data for the JRC-EU-TIMES runs

@authors: Matija Pavičević, KU Leuven
          Sylvain Quoilin, KU Leuven
"""
from __future__ import division

import pandas as pd
import glob
import enlopy as el
import logging

# Local source tree imports
from ...common import date_range, get_country_codes, write_csv_files, commons, get_ktoe_to_mwh, make_dir, leap_year
from ..get_capacities.get_Capacities_ARES_APP import get_hydro_units

def get_renewables(codes_CEN, solar_AF, wind_AF, hydro_dam_data, EFFICIENCY, path, YEAR_InFlow, generation, capacity_factors, write_csv=False, SOURCE='JRC', SOURCE_Hydro='LISFLOOD'):
    codes = get_country_codes(list(solar_AF.columns))

    # Assign proper index and column names
    solar_AF.rename(columns=dict(zip(solar_AF.columns, codes)), inplace=True)
    wind_AF.rename(columns=dict(zip(wind_AF.columns, codes)), inplace=True)
    solar_AF.drop(columns=['Unknown code'], inplace=True)
    wind_AF.drop(columns=['Unknown code'], inplace=True)
    solar_AF.set_index(date_range('1/1/2005', '1/1/2017', freq='H'), inplace=True)
    wind_AF.set_index(date_range('1/1/2005', '1/1/2017', freq='H'), inplace=True)

    # Filter wind and solar for selected zones
    wind_AF = wind_AF[codes_CEN]
    solar_AF = solar_AF[codes_CEN]

    # Get hydro units in dispa-set format
    hydro_units = get_hydro_units(hydro_dam_data, EFFICIENCY)

    # unit_names = list(hydro_units['Unit'])
    unit_hdam = list(hydro_units['Zone'].loc[hydro_units['Technology'] == 'HDAM'].unique())
    unit_hror = list(hydro_units['Zone'].loc[hydro_units['Technology'] == 'HROR'].unique())

    # Read river inflows and adjust (upscale) to hourly values
    all_files = glob.glob(path + "/*.csv")
    river_in_flows = pd.DataFrame()
    for filename in all_files:
        tmp = pd.read_csv(filename, index_col=0, header=0, parse_dates=[0])
        river_in_flows = pd.concat([river_in_flows, tmp], axis=1)
    river_in_flows.columns = list(hydro_units['Unit'])
    river_in_flows = river_in_flows.resample('H').interpolate(method='linear')

    # Analyze inflows for specific year
    start_date = str(YEAR_InFlow) + '-01-01'
    end_date = str(YEAR_InFlow) + '-12-31'
    # tmp_flow = pd.DataFrame(river_in_flows.loc[start_date:end_date])
    tmp_flow = pd.DataFrame(river_in_flows)

    # Gather unit specific data for further analysis
    data = pd.DataFrame(hydro_dam_data['Dam height (m)']).fillna(1)
    data['PowerCapacity'] = hydro_units['PowerCapacity']
    data['Zone'] = hydro_dam_data['Country Code']
    data['Technology'] = hydro_units['Technology']
    data['Area'] = hydro_dam_data['Reservoir area (km2)']
    data['Area'] = data['Area'].fillna(0)
    data['FlowMax'] = data['PowerCapacity'] * 1e6 / 9.81 / 1000 / data['Dam height (m)'] / 0.8
    data['FlowMin'] = data['FlowMax'] * 0.1
    data.index = list(hydro_units['Unit'])

    # Annual generation in MWh
    generation = get_ktoe_to_mwh(generation, ['Biofuels', 'Fosil', 'Hydro', 'Geothermal', 'RES'])

    # Identify annual generation per zone and share of installed capacity
    for c in list(data['Zone'].unique()):
        if c in list(generation.index):
            data.loc[data['Zone'] == c, 'Share'] = data['PowerCapacity'].loc[data['Zone'] == c] / \
                                                   data['PowerCapacity'].loc[data['Zone'] == c].sum()
            data.loc[data['Zone'] == c, 'Generation_Historic'] = generation['Hydro'][c]
        else:
            data.loc[data['Zone'] == c, 'Generation_Historic'] = 0
    # Assign annual generation for each individual unit based on shares
    data['Generation_Historic'] = data['Generation_Historic'] * data['Share']
    # Compute annual generation for proposed inflows
    data['Generation_From_Flows'] = tmp_flow.loc[start_date:end_date].sum() * 9.81 / 1e6 * 1000 * data[
        'Dam height (m)'] * 0.8
    # Identify capacity factors
    data['CF'] = data['Generation_Historic'] / data['PowerCapacity'] / 8760

    # Initial Inflow adjustment for all units
    data['Correction'] = (data['Generation_Historic'] - data['Generation_From_Flows']) / data['Generation_From_Flows']
    # Assign AF for HDAM's
    af_hdam = tmp_flow.loc[:, data['Technology'] == 'HDAM'] * 9.81 / 1e6 * 1000 * \
              data['Dam height (m)'].loc[data['Technology'] == 'HDAM'] * \
              (1 + data['Correction'].loc[data['Technology'] == 'HDAM']) / \
              data['PowerCapacity'].loc[data['Technology'] == 'HDAM']

    # Helper functions
    def get_hror_cf(data, CF, generation):
        """
        Iterative method for adjusting the annual generation based on flows
        :param data:    Unit specific input data (Generation and Technology)
        :param CF:      Initial correction factor
        :param generation:    pd.DataFrame
        :returns:       Updated capacity factor and new flows
        """
        tmp_flow_HROR = generation * (1 + CF)
        spill_HROR = tmp_flow_HROR - data['PowerCapacity'].loc[data['Technology'] == 'HROR']
        spill_HROR[spill_HROR < 0] = 0
        flow_HROR = tmp_flow_HROR - spill_HROR
        flow_HROR.fillna(4, inplace=True)
        CF = (data['Generation_Historic'].loc[data['Technology'] == 'HROR'] - flow_HROR.loc[start_date:end_date].sum()) / \
             flow_HROR.loc[start_date:end_date].sum()
        CF.fillna(0, inplace=True)
        return CF, flow_HROR, tmp_flow_HROR


    def get_res_cf(availability, CF, total):
        """
        Iterative method for adjusting annual generation based on RES
        :param generation:  RES timeseries
        :param CF:          Correction factor
        :param total:       Total generation with new CF
        :return:            Updated availability timeseries
        """
        tmp_res = availability * (1 + CF)
        spill_res = tmp_res - 1
        spill_res[spill_res < 0] = 0
        res = tmp_res - spill_res
        CF = (total - res.sum()) / res.sum()
        CF.fillna(0, inplace=True)
        return CF, res, tmp_res


    def get_wind_AF(start_date, end_date, CF):
        """
        Wind CF from enlopy module
        :param start_date:  Start date for the timeseries
        :param end_date:    End date for the time series
        :param CF:          List of Capacity factors in diferent zones
        :return:            Availability for selected regions
        """
        lp_year = leap_year(int(start_date.split("-", 1)[0].strip()))
        if lp_year is True:
            prds = 8784
        else:
            prds = 8760
        tmp = pd.DataFrame()
        for c in list(capacity_factors.index):
            aa = el.gen_load_from_LDC(el.generate.gen_analytical_LDC((1, CF[c], 0, prds), bins=prds), N=prds)
            tmp[c] = aa
        tmp.set_index(date_range(start_date, end_date, freq='H'), inplace=True)
        return tmp


    # Initial correction factors for wind and sun
    cor_res = pd.DataFrame(index=list(solar_AF.columns))
    cor_res['PV'] = 0.5
    # Iterations
    for i in range(20):
        tmp_sun = get_res_cf(solar_AF, cor_res['PV'], capacity_factors['CF_PV'] * solar_AF.count(axis=0))
        cor_res['PV'] = tmp_sun[0]
        solar_AF = tmp_sun[1]
        if i % 10 == 0:
            logging.info('iteration #' + str(i) + ' max correction for solar PV: ' + str(tmp_sun[0].max()))

    # Get generation for HROR units
    generation = tmp_flow.loc[:, data['Technology'] == 'HROR'] * 9.81 / 1e6 * 1000 * \
                 data['Dam height (m)'].loc[data['Technology'] == 'HROR'] * 0.8

    # Initial inflow adjustment for HROR units
    correction_factor = data['Correction'].loc[data['Technology'] == 'HROR']
    # Iterations
    for i in range(100):
        tmp_data = get_hror_cf(data, correction_factor, generation)
        correction_factor = tmp_data[0]
        generation = tmp_data[1]
        if i % 10 == 0:
            logging.info('iteration #' + str(i) + ' max correction: ' + str(tmp_data[0].max()))

    # New AF for HROR units
    af_hror = tmp_data[1] / data['PowerCapacity'].loc[data['Technology'] == 'HROR']
    # Merger of HDAM and HROR AF/Scaled InFlows
    tmp_af = pd.concat([af_hdam, af_hror], axis=1, sort=False)


    def get_res_for_year(zones, start_date, end_date):
        """
        Function that prepares data for export
        :param zones:
        :param start_date:
        :param end_date:
        :return:
        """
        hdam_timeseries = {}
        res_timeseries = {}
        # Predefined all 0 DataFrame. Used to fill missing AF and Hydro data
        zero_df = pd.DataFrame(af_hror.index, columns=['HROR', 'PHOT', 'WTON', 'WTOF', 'HDAM']).fillna(0)
        # Create new wind timeseries
        year = start_date.split("-", 1)[0].strip()
        wind_AF = get_wind_AF(start_date, str(int(year) + 1) + '-01-01', capacity_factors['CF_Wind'])
        for region in zones:
            # Solar PV
            if region in solar_AF:
                if leap_year(year) is True:
                    tmp_PV = pd.DataFrame(solar_AF[region].loc['2016-01-01':'2016-12-31'])
                    logging.info(region + ' PHOT timseries created from PHOT dataset and year 2016')
                else:
                    tmp_PV = pd.DataFrame(solar_AF[region].loc['2015-01-01':'2015-12-31'])
                    logging.info(region + ' PHOT timseries created from PHOT dataset and year 2015')
                tmp_PV.reset_index(inplace=True, drop=True)
                tmp_PV.set_index(date_range(start_date, str(int(year) + 1) + '-01-01', 'H'), inplace=True)
                tmp_PV.rename(columns={region: 'PHOT'}, inplace=True)

            else:
                logging.warning(region + ' PHOT timeseries doesnt exist')
                tmp_PV = pd.DataFrame(zero_df['PHOT'].loc[start_date:end_date])
            # Wind onshore
            if region in wind_AF:
                tmp_WTON = pd.DataFrame(wind_AF[region].loc[start_date:end_date])
                tmp_WTON.rename(columns={region: 'WTON'}, inplace=True)
                logging.info(region + ' WTON timseries created from WTON dataset')
            else:
                logging.warning(region + ' WTON timeseries doesnt exist')
                tmp_WTON = pd.DataFrame(zero_df['WTON'].loc[start_date:end_date])
            # Wind offshore
            if region in wind_AF:
                tmp_WTOF = pd.DataFrame(wind_AF[region].loc[start_date:end_date])
                tmp_WTOF.rename(columns={region: 'WTOF'}, inplace=True)
                logging.info(region + ' WTOF timseries created from WTON dataset')
            else:
                logging.warning(region + ' WTOF timeseries doesnt exist')
                tmp_WTOF = pd.DataFrame(zero_df['WTOF'].loc[start_date:end_date])
            # Hydro run-of-river
            tmp_HROR = zero_df
            if region in unit_hror:
                tmp_HROR = tmp_af.loc[start_date:end_date, list(hydro_units['Unit'].loc[(hydro_units['Zone'] == region) &
                                                                                        (hydro_units[
                                                                                             'Technology'] == 'HROR')])]
                tmp_hr = tmp_HROR * data['PowerCapacity'].loc[(data['Technology'] == 'HROR') & (data['Zone'] == region)]
                tmp_hr = tmp_hr.sum(axis=1) / data['PowerCapacity'].loc[
                    (data['Technology'] == 'HROR') & (data['Zone'] == region)].sum()
                tmp_HROR['HROR'] = tmp_hr
            else:
                logging.warning(region + ' there is no HROR timeseries present in the availability factors')
                tmp_HROR = pd.DataFrame(zero_df['HROR'].loc[start_date:end_date])
            # Hydro dam
            tmp_HDAM = zero_df
            if region in unit_hdam:
                tmp_HDAM = tmp_af.loc[start_date:end_date, list(hydro_units['Unit'].loc[(hydro_units['Zone'] == region) &
                                                                                        (hydro_units[
                                                                                             'Technology'] == 'HDAM')])]
                tmp_hd = tmp_HDAM * data['PowerCapacity'].loc[(data['Technology'] == 'HDAM') & (data['Zone'] == region)]
                tmp_hd = tmp_hd.sum(axis=1) / data['PowerCapacity'].loc[
                    (data['Technology'] == 'HDAM') & (data['Zone'] == region)].sum()
                tmp_HDAM['HDAM'] = tmp_hd
            else:
                logging.warning(region + ' there is no HDAM timeseries present in the availability factors')
                tmp_HDAM = pd.DataFrame(zero_df['HDAM'].loc[start_date:end_date])

            # Combine it all together
            tmp_res_timeseries = [tmp_WTON, tmp_WTOF, tmp_PV, tmp_HROR]
            res_timeseries[region] = pd.concat(tmp_res_timeseries, axis=1)
            # Separate HDAM's
            hdam_timeseries[region] = tmp_HDAM.copy()
        return res_timeseries, hdam_timeseries

    def write_csv_hydro(file_name_IF=None, inflow_timeseries=None, write_csv=False):
        """
        Specific function for hydro inflows
        :param file_name_IF:
        :param inflow_timeseries:
        :param write_csv:
        :return:
        """
        if write_csv is True:
            if isinstance(inflow_timeseries, dict):
                filename_IF = file_name_IF + '.csv'
                for c in inflow_timeseries:
                    make_dir('../../Outputs/')
                    make_dir('../../Outputs/' + 'ARES_APP')
                    make_dir('../../Outputs/' + 'ARES_APP' + '/Database/')
                    make_dir('../../Outputs/' + 'ARES_APP' + '/Database/' + 'HydroData/')
                    folder_1 = '../../Outputs/' + 'ARES_APP' + '/Database/' + 'HydroData/' + 'ScaledInflows/'
                    make_dir(folder_1)
                    make_dir(folder_1 + c)
                    inflow_timeseries[c].to_csv(folder_1 + c + '/' + filename_IF)
                    logging.info('ScaledInFlows' + ' database was created for zone: ' + c + '.')
        else:
            logging.warning('[WARNING ]: ' + 'WRITE_CSV_FILES = False, unable to write .csv files')


    for year in list(af_hror.index.year.unique()):
        if year < 2019:
            start_date = str(year) + '-01-01'
            end_date = str(year) + '-12-31'
            selected_year = get_res_for_year(codes_CEN, start_date, end_date)
            tmp = {}
            for k in selected_year[1]:
                if not selected_year[1][k].empty:
                    tmp[k] = selected_year[1][k]
            write_csv_files(selected_year[0], 'ARES_APP', SOURCE, 'AvailabilityFactors', str(year), write_csv, 'Zonal')
            write_csv_hydro('IF_' + SOURCE_Hydro + '_' + str(year), tmp, write_csv)
        else:
            logging.info(str(year) + ' is out of bounds')





#
# el.plot_percentiles(river_in_flows['Erraguene'], x='dayofyear', zz='year', color='green')
# plt.show()
#
# # Analyis of historical capacity factors
# cc = tmp_af * data['PowerCapacity']
# flows_napp = cc.loc[:, list(hydro_units['Unit'].loc[hydro_units['Zone'].isin(get_country_codes(countries_NAPP))])]
# flows_capp = cc.loc[:, list(hydro_units['Unit'].loc[hydro_units['Zone'].isin(get_country_codes(countries_CAPP))])]
# flows_eapp = cc.loc[:, list(hydro_units['Unit'].loc[hydro_units['Zone'].isin(get_country_codes(countries_EAPP))])]
#
# historic_cfs_pp = pd.DataFrame()
# historic_cfs_pp['NAPP'] = flows_napp.sum(axis=1)
# historic_cfs_pp['CAPP'] = flows_capp.sum(axis=1)
# historic_cfs_pp['EAPP'] = flows_eapp.sum(axis=1)
#
# # Analyis of historical capacity factors
# historic_cfs = pd.DataFrame()
# historic_unit_cf = pd.DataFrame()
# for i in range(1979, 2019):
#     start_year = str(i) + '-1-1'
#     end_year = str(i) + '-12-31'
#     historic_cfs[str(i)] = historic_cfs_pp.loc[start_year:end_year, :].sum() / historic_cfs_pp.loc[start_year:end_year,
#                                                                                :].count()
#     historic_unit_cf[str(i)] = tmp_af.loc[start_year:end_year, :].sum() / tmp_af.loc[start_year:end_year, :].count()
#
# pp_hist = pd.DataFrame()
# pp_hist['NAPP'] = historic_cfs.loc['NAPP', :] / data['PowerCapacity'].loc[hydro_units['Unit'].loc[
#     hydro_units['Zone'].isin(get_country_codes(countries_NAPP))]].sum()
# pp_hist['EAPP'] = historic_cfs.loc['EAPP', :] / data['PowerCapacity'].loc[hydro_units['Unit'].loc[
#     hydro_units['Zone'].isin(get_country_codes(countries_EAPP))]].sum()
# pp_hist['CAPP'] = historic_cfs.loc['CAPP', :] / data['PowerCapacity'].loc[hydro_units['Unit'].loc[
#     hydro_units['Zone'].isin(get_country_codes(countries_CAPP))]].sum()
#
#
# # Return year closest to a certain percentile
# def get_year_percentile(percentile, power_pool):
#     aa = pp_hist.quantile(percentile)
#     tmp = pp_hist[power_pool].iloc[(pp_hist[power_pool] - aa[power_pool]).abs().argsort()[:1]]
#     return tmp
#
#
# # Years nearest to seleceted min and max percentiles
# min_pp = pd.DataFrame()
# max_pp = pd.DataFrame()
# for pp in ['NAPP', 'EAPP', 'CAPP']:
#     min_pp[pp] = get_year_percentile(0.1, pp).index
#     max_pp[pp] = get_year_percentile(0.9, pp).index
#     if pp == 'NAPP':
#         zones = get_country_codes(countries_NAPP)
#     elif pp == 'EAPP':
#         zones = get_country_codes(countries_EAPP)
#     else:
#         zones = get_country_codes(countries_CAPP)
#     start_date_min = str(min_pp[pp][0]) + '-1-1'
#     end_date_min = str(min_pp[pp][0]) + '-12-31'
#     start_date_max = str(max_pp[pp][0]) + '-1-1'
#     end_date_max = str(max_pp[pp][0]) + '-12-31'
#     min_year = get_res_for_year(zones, start_date_min, end_date_min)
#     max_year = get_res_for_year(zones, start_date_max, end_date_max)
#     write_csv_files(min_year[0], 'ARES_APP', SOURCE, 'AvailabilityFactors', 'DRY_YEAR', WRITE_CSV, 'Zonal')
#     write_csv_hydro('IF_' + SOURCE_Hydro + '_' + 'DRY_YEAR', min_year[1], WRITE_CSV)
#     write_csv_files(max_year[0], 'ARES_APP', SOURCE, 'AvailabilityFactors', 'WET_YEAR', WRITE_CSV, 'Zonal')
#     write_csv_hydro('IF_' + SOURCE_Hydro + '_' + 'WET_YEAR', max_year[1], WRITE_CSV)
#
# # pp_hist.to_csv('Historical_CF_power_pools.csv')
#
# aa = historic_cfs_pp / data['PowerCapacity'].loc[hydro_units['Unit'].loc[
#     hydro_units['Zone'].isin(get_country_codes(countries_NAPP))]].sum()
#
# # Plots all in one diagram
#
# def make_timeseries(x=None, year=None, length=None, startdate=None, freq=None):
#     """Convert numpy array to a pandas series with a timed index. Convenience wrapper around a datetime-indexed pd.DataFrame.
#
#     Parameters:
#         x: (nd.array) raw data to wrap into a pd.Series
#         startdate: pd.datetime
#         year: year of timeseries
#         freq: offset keyword (e.g. 15min, H)
#         length: length of timeseries
#     Returns:
#         pd.Series or pd.Dataframe with datetimeindex
#     """
#
#     if startdate is None:
#         if year is None:
#             logging.info('No info on the year was provided. Using current year')
#             year = pd.datetime.now().year
#         startdate = pd.datetime(year, 1, 1, 0, 0, 0)
#
#     if x is None:
#         if length is None:
#             raise ValueError('The length or the timeseries has to be provided')
#     else:  # if x is given
#         length = len(x)
#         if freq is None:
#             # Shortcuts: Commonly used frequencies are automatically assigned
#             if len(x) == 8760 or len(x) == 8784:
#                 freq = 'H'
#             elif len(x) == 35040:
#                 freq = '15min'
#             elif len(x) == 12:
#                 freq = 'm'
#             else:
#                 raise ValueError('Input vector length must be 12, 8760 or 35040. Otherwise freq has to be defined')
#
#     #enddate = startdate + pd.datetools.timedelta(seconds=_freq_to_sec(freq) * (length - 1) )
#     date_list = pd.date_range(start=startdate, periods=length, freq=freq)
#     if x is None:
#         return pd.Series(np.nan, index=date_list)
#     elif isinstance(x, (pd.DataFrame, pd.Series)):
#         x.index = date_list
#         return x
#     elif isinstance(x, (np.ndarray, list)):
#         if len(x.shape) > 1:
#             return pd.DataFrame(x, index=date_list)
#         else:
#             return pd.Series(x, index=date_list)
#     else:
#         raise ValueError('Unknown type of data passed')
#
# def clean_convert(x, force_timed_index=True, always_df=False, **kwargs):
#     """Converts a list, a numpy array, or a dataframe to pandas series or dataframe, depending on the
#     compatibility and the requirements. Designed for maximum compatibility.
#
#     Arguments:
#         x (list, np.ndarray): Vector or matrix of numbers. it can be pd.DataFrame, pd.Series, np.ndarray or list
#         force_timed_index (bool): if True it will return a timeseries index
#         year (int): Year that will be used for the index
#         always_df (bool): always return a dataframe even if the data is one dimensional
#         **kwargs: Exposes arguments of :meth:`make_timeseries`
#     Returns:
#         pd.Series: Timeseries
#
#     """
#
#     if isinstance(x, list):  # nice recursions
#         return clean_convert(pd.Series(x), force_timed_index, always_df, **kwargs)
#
#     elif isinstance(x, np.ndarray):
#         if len(x.shape) == 1:
#             return clean_convert(pd.Series(x), force_timed_index, always_df, **kwargs)
#         else:
#             return clean_convert(pd.DataFrame(x), force_timed_index, always_df, **kwargs)
#
#     elif isinstance(x, pd.Series):
#         if always_df:
#             x = pd.DataFrame(x)
#         if x.index.is_all_dates:
#             return x
#         else:  # if not datetime index
#             if force_timed_index:
#                 logging.debug('Forcing Datetimeindex into passed timeseries.'
#                               'For more accurate results please pass a pandas time-indexed timeseries.')
#                 return make_timeseries(x, **kwargs)
#             else:  # does not require datetimeindex
#                 return x
#
#     elif isinstance(x, pd.DataFrame):
#         if x.shape[1] == 1 and not always_df:
#             return clean_convert(x.squeeze(), force_timed_index, always_df, **kwargs)
#         else:
#             if force_timed_index and not x.index.is_all_dates:
#                 return make_timeseries(x, **kwargs)
#             else:  # does not require datetimeindex
#                 return x
#     else:
#         raise ValueError(
#             'Unrecognized Type. Has to be one of the following: pd.DataFrame, pd.Series, np.ndarray or list')
#
#
# def reshape_timeseries(Load, x='dayofyear', y=None, aggfunc='sum'):
#     """Returns a reshaped pandas DataFrame that shows the aggregated load for selected
#     timeslices. e.g. time of day vs day of year
#
#     Parameters:
#         Load (pd.Series, np.ndarray): timeseries
#         x (str): x axis aggregator. Has to be an accessor of pd.DatetimeIndex
#          (year, dayoftime, week etc.)
#         y (str): similar to above for y axis
#     Returns:
#         reshaped pandas dataframe according to x,y
#     """
#
#     # Have to convert to dataframe in order for pivottable to work
#     # 1D, Dataframe
#     a = clean_convert(Load.copy(), force_timed_index=True, always_df=True)
#     a.name = 0
#     if len(a.columns) > 1:
#         raise ValueError('Works only with 1D')
#
#     if x is not None:
#         a[x] = getattr(a.index, x)
#     if y is not None:
#         a[y] = getattr(a.index, y)
#     a = a.reset_index(drop=True)
#
#     return a.pivot_table(index=x, columns=y,
#                          values=a.columns[0],
#                          aggfunc=aggfunc).T
#
#
# def plot_heatmap(Load, x='dayofyear', y='hour', aggfunc='sum', bins=8,
#                 figsize=(8,6), edgecolors='none', cmap='Oranges', colorbar=True, ax=None, **pltargs):
#     """ Returns a 2D heatmap of the reshaped timeseries based on x, y
#
#     Arguments:
#         Load: 1D pandas with timed index
#         x: Parameter for :meth:`enlopy.analysis.reshape_timeseries`
#         y: Parameter for :meth:`enlopy.analysis.reshape_timeseries`
#         bins: Number of bins for colormap
#         edgecolors: colour of edges around individual squares. 'none' or 'w' is recommended.
#         cmap: colormap name (from colorbrewer, matplotlib etc.)
#         **pltargs: Exposes matplotlib.plot arguments
#     Returns:
#         2d heatmap
#     """
#     columns = 5
#     rows = int(len(Load.columns) / columns) + (len(Load.columns) % columns > 0)
#     fig = plt.figure(figsize=figsize,constrained_layout=True)
#     # axs = plt.subplots(rows, columns, figsize=figsize, sharex=True, sharey=True, )
#     spec = fig.add_gridspec(nrows= rows, ncols = columns +1)
#     # fig.subplots_adjust(hspace=0.4)
#
#     # axs = axs.ravel()
#     cmap_obj = cm.get_cmap(cmap, bins)
#     i = 0
#     for row in range(rows):
#
#         for col in range(columns):
#             ax = fig.add_subplot(spec[row, col])
#             bb = Load.iloc[:, i]
#             x_y = reshape_timeseries(bb, x=x, y=y, aggfunc=aggfunc)
#             heatmap = ax.pcolor(x_y, cmap=cmap_obj, edgecolors=edgecolors)
#             ax.set_xlim(right=len(x_y.columns))
#             ax.set_ylim(top=len(x_y.index))
#             if i >=20:
#                 ax.set_xlabel(x)
#             if i in [0,5, 10, 15, 20]:
#                 ax.set_ylabel(y)
#             ax.set_title(bb.name)
#             i = i + 1
#     if colorbar:
#         ax2 = fig.add_subplot(spec[:, columns])
#         fig.colorbar(heatmap, ax=ax2, location='right', shrink=0.8)
#         fig.delaxes(ax2)
#     folder_figures = output_folder + source_folder + 'Figures/'
#     fig.savefig(folder_figures + "\Heatmap_Demand.png")
#
#     plt.show()
#
# def plot_percentiles(Load, x='hour', zz='week', perc_list=[[5, 95], [25, 75], 50], columns = 1, ax=None, color='blue',figsize=(15,15),fig_name=None, **kwargs):
#     """Plot predefined percentiles per timestep
#
#     Arguments:
#         Load: 1D pandas with timed index
#         x (str): x axis aggregator. See :meth:`enlopy.analysis.reshape_timeseries`
#         zz (str): similar to above for y axis
#         perc_list(list): List of percentiles to plot. If it is an integer then it will be plotted as a line. If it is list it has to contain two items and it will be plotted using fill_between()
#         **kwargs: exposes arguments of :meth:`matplotlib.pyplot.fill_between`
#     Returns:
#         Plot
#
#     """
#
#     rows = int(len(Load.columns) / columns) + (len(Load.columns) % columns > 0)
#     fig = plt.figure(figsize=figsize, constrained_layout=True)
#     # axs = plt.subplots(rows, columns, figsize=figsize, sharex=True, sharey=True, )
#     spec = fig.add_gridspec(nrows=rows, ncols=columns)
#     # fig.subplots_adjust(hspace=0.4)
#
#     # axs = axs.ravel()
#     j = 0
#     for row in range(rows):
#         for col in range(columns):
#             if j < len(Load.columns):
#                 ax = fig.add_subplot(spec[row, col])
#                 bb = Load.iloc[:, j]
#                 a = reshape_timeseries(bb, x=x, y=zz, aggfunc='mean')
#                 xx = a.columns.values
#                 for i in perc_list:
#                     if len(np.atleast_1d(i)) == 1:
#                         perc = a.apply(lambda x: np.nanpercentile(x.values, i), axis=0)
#                         ax.plot(xx, perc.values, color='black')
#                     elif len(np.atleast_1d(i)) == 2:
#                         perc0 = a.apply(lambda x: np.nanpercentile(x.values, i[0]), axis=0)
#                         perc1 = a.apply(lambda x: np.nanpercentile(x.values, i[1]), axis=0)
#
#                         ax.fill_between(xx, perc0, perc1, lw=.5, alpha=.3, color=color)
#                     else:
#                         raise ValueError('List items should be scalars or 2-item lists')
#
#                 ax.set_xlim(left=min(xx), right=max(xx))
#                 # ax.set_xlabel(x)
#                 if j >= 20:
#                     ax.set_xlabel(x)
#                 if j in [0,5, 10, 15, 20]:
#                     ax.set_ylabel('AF')
#                 ax.set_title(bb.name)
#                 ax.set_ylim(0, 0.4)
#             j = j + 1
#     folder_figures = output_folder + source_folder + 'Figures/'
#     # fig.savefig(folder_figures + "\Hydro_CF_PowerPool.png")
#     fig.savefig(folder_figures + '/' + fig_name + '.png')
#     plt.show()
#
# # plot_percentiles(aa, x='dayofyear', zz='year', color='blue', figsize=(9,3), perc_list=[[0,100], [5, 95], [25, 75], 50])
#
# cc = hydro_units
# cc.set_index('Unit', inplace=True)
# bb = tmp_flow.loc[:, (cc['Technology']=='HDAM') & (cc['Zone'].isin(get_country_codes(countries_EAPP)))]
#
#
# plot_percentiles(bb, x='dayofyear', zz='year', color='blue', columns = 5, figsize=(10,10), perc_list=[[0,100], [5, 95], [25, 75], 50], fig_name='EAPP')
#
# plot_percentiles(tmp_sun[1], x='dayofyear', zz='year', color='yellow', columns = 5, figsize=(10,10), perc_list=[[0,100], [5, 95], [25, 75], 50], fig_name='PHOT')
#
# aa = pd.DataFrame()
# for z in zones:
#     aa[z] = tmp_flow.loc[:,hydro_units['Zone']==z].sum(axis=1)
#
# aa.to_csv('Inflows.csv')