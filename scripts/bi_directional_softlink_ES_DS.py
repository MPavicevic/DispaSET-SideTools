# Add the root folder of Dispa-SET-side tools to the path so that the library can be loaded:
import sys, os

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
import dispaset as ds
import dispaset_sidetools as dst
import energyscope as es

sys.path.append(os.path.abspath('..'))

# %% ###################################
############## Path setup #############
#######################################
dst_path = Path(__file__).parents[1]
# Typical units
typical_units_folder = dst_path/'Inputs'/'EnergyScope'
scenario = 45000

# Energy Scope
ES_folder = dst_path.parent/'glimpens_EnergyScope'
DST_folder = dst_path.parent/'DispaSET-SideTools'

data_folders = [ES_folder/'Data'/'User_data', ES_folder/'Data'/'Developer_data']
ES_path = ES_folder/'energyscope'/'STEP_2_Energy_Model'
step1_output = ES_folder/'energyscope'/'STEP_1_TD_selection'/'TD_of_days.out'

# %% ###################################
########### Editable inputs ###########
#######################################
config_es = {'case_study': 'test3',
          # Name of the case study. The outputs will be printed into : config['ES_path']+'\output_'+config['case_study']
          'comment': 'This is a test of versionning',
          'run_ES': False,
          'import_reserves': '',
          'importing': True,
          'printing': False,
          'printing_td': False,
          'GWP_limit': scenario,  # [ktCO2-eq./year]	# Minimum GWP reduction
          'import_capacity': 9.72,  # [GW] Electrical interconnections with neighbouring countries
          'data_folders': data_folders,  # Folders containing the csv data files
             'ES_folder': ES_folder, # Path to th directory of energyscope
          'ES_path': ES_path,  # Path to the energy model (.mod and .run files)
          'step1_output': step1_output,  # Output of the step 1 selection of typical days
          'all_data': dict(),
          'Working_directory': os.getcwd(),
          'reserves': pd.DataFrame()}

# %% ####################################
#### Update and Execute EnergyScope ####
########################################

# Reading the data
config_es['all_data'] = es.run_ES(config_es)
# No electricity imports
config_es['all_data']['Resources'].loc['ELECTRICITY', 'avail'] = 0
# Printing and running
config_es['importing'] = False
config_es['printing'] = True
config_es['printing_td'] = True
config_es['run_ES'] = True
config_es['all_data'] = es.run_ES(config_es)

# Static Data - to be created only once
el_demand = dst.get_demand_from_es(config_es)
th_demand = dst.get_heat_demand_from_es(config_es)
af = dst.get_availability_factors_from_es(config_es)

inputs = dict()
results = dict()
GWP_op = dict()
capacities = dict()
reserves = dict()
shed_load = dict()
Price_CO2 = dict()

LL = pd.DataFrame()
Curtailment = pd.DataFrame()
end = 4
iteration = {}

for i in range(end):
    print('loop number', i)
    # Dynamic Data - to be modified in a loop
    # compute the actual average annual emission factors for each resource
    GWP_op[i] = es.compute_gwp_op(config_es['data_folders'], ES_folder/'case_studies'/config_es['case_study'])
    GWP_op[i].to_csv(ES_folder/'case_studies'/config_es['case_study']/'output'/'GWP_op.txt', sep='\t')  # TODO automate
    # TODO update with new possibility of changing output folder
    capacities[i] = dst.get_capacities_from_es(config_es, typical_units_folder=typical_units_folder)
    Price_CO2[i] = pd.read_csv(ES_folder/'case_studies'/config_es['case_study']/'output'/'CO2_cost.txt', delimiter='\t')
    Price_CO2[i] = [float(i) for i in list(Price_CO2[i].columns)]

    # %% ###################################
    ########## Execute Dispa-SET ##########
    #######################################
    # Load the configuration file
    config = ds.load_config('../ConfigFiles/Config_EnergyScope.xlsx')
    config['default']['PriceOfCO2'] = abs(Price_CO2[i][0] * 1000)

    # Build the simulation environment:
    SimData = ds.build_simulation(config)

    # Solve using GAMS:
    _ = ds.solve_GAMS(config['SimulationDirectory'], config['GAMS_folder'])

    # Load the simulation results:
    inputs[i], results[i] = ds.get_sim_results(config['SimulationDirectory'], cache=False)

    # TODO : reading and storing ESTD results

    # run ES with reserves (2nd run)
    config_es['printing'] = False
    config_es['import_reserves'] = 'from_df'
    reserves[i] = pd.DataFrame(inputs[i]['param_df']['Demand'].loc[:, '2U'].values / 1000, columns=['end_uses_reserve'],
                               index=np.arange(1, 8761, 1))

    if i >= 1:
        shed_load[i] = pd.DataFrame(results[i]['OutputShedLoad'].values / 1000, columns=['end_uses_reserve'],
                                    index=np.arange(1, 8761, 1))

        config_es['reserves'] = config_es['reserves'] + shed_load[i].max()
    else:
        config_es['reserves'] = reserves[i]

    if i == end - 1:
        print('Last opt')
    else:
        config_es['all_data'] = es.run_ES(config_es)

    LL = pd.concat([LL, results[i]['OutputShedLoad']], axis=1)
    Curtailment = pd.concat([Curtailment, results[i]['OutputCurtailedPower']], axis=1)

import pickle

with open('ES_DS_Results.p', 'wb') as handle:
    pickle.dump(inputs, handle, protocol=pickle.HIGHEST_PROTOCOL)
    pickle.dump(results, handle, protocol=pickle.HIGHEST_PROTOCOL)

# with open('ES_DS_Results.p', 'rb') as handle:
#     inputs = pickle.load(handle)
#     results = pickle.load(handle)

# Plots
# import pandas as pd
#
# rng = pd.date_range('2015-1-01', '2015-12-31', freq='H')
# Generate country-specific plots
# ds.plot_zone(inputs[3], results[3], rng=rng, z_th='ES_DHN')
#
# # Bar plot with the installed capacities in all countries:
# cap = ds.plot_zone_capacities(inputs, results)
#
# # Bar plot with installed storage capacity
# sto = ds.plot_tech_cap(inputs[3])
#
# # Violin plot for CO2 emissions
# ds.plot_co2(inputs[3], results[3], figsize=(9, 6), width=0.9)
#
# # Bar plot with the energy balances in all countries:
# ds.plot_energy_zone_fuel(inputs, results, ds.get_indicators_powerplant(inputs, results))
#
# # Analyse the results for each country and provide quantitative indicators:
# r = ds.get_result_analysis(inputs, results)


# Create figure and subplot manually
# fig = plt.figure()
# host = fig.add_subplot(111)

# More versatile wrapper
fig, host = plt.subplots(figsize=(8, 4))  # (width, height) in inches
# (see https://matplotlib.org/3.3.3/api/_as_gen/matplotlib.pyplot.subplots.html)

par1 = host.twinx()
par2 = host.twinx()

host.set_xlim(1, 4)
host.set_ylim(0, 90)
par1.set_ylim(0, 450)
par2.set_ylim(0, 3300)

host.set_xlabel("Iteration")
host.set_ylabel("ENS_mean [MWh]")
par1.set_ylabel("ENS_st.dev. [MWh]")
par2.set_ylabel("ENS_max [MWh]")

color1 = plt.cm.viridis(0.9)
color2 = plt.cm.viridis(0.5)
color3 = plt.cm.viridis(0)

# p1, = host.plot([1, 2, 3, 4], [83.52, 19.99, 0.08, 0.04], color=color1, label="ENS_mean")
# p2, = par1.plot([1, 2, 3, 4], [439.6, 177.7, 2.23, 1.37], color=color2, label="ENS_st.dev.")
# p3, = par2.plot([1, 2, 3, 4], [3216, 3019, 102.74, 76.33], color=color3, label="ENS_max")

p1, = host.plot([1, 2, 3, 4], [84.56, 20.74, 0.07, 0.6], color=color1, label="ENS_mean")
p2, = par1.plot([1, 2, 3, 4], [438.4, 182.11, 5.0, 15.28], color=color2, label="ENS_st.dev.")
p3, = par2.plot([1, 2, 3, 4], [3216, 3019, 455.8, 739.4], color=color3, label="ENS_max")

lns = [p1, p2, p3]
host.legend(handles=lns, loc='best')

# right, left, top, bottom
par2.spines['right'].set_position(('outward', 60))

# no x-ticks
par2.xaxis.set_ticks([1, 2, 3, 4])

# Sometimes handy, same for xaxis
# par2.yaxis.set_ticks_position('right')

# Move "Velocity"-axis to the left
# par2.spines['left'].set_position(('outward', 60))
# par2.spines['left'].set_visible(True)
# par2.yaxis.set_label_position('left')
# par2.yaxis.set_ticks_position('left')

host.yaxis.label.set_color(p1.get_color())
par1.yaxis.label.set_color(p2.get_color())
par2.yaxis.label.set_color(p3.get_color())

plt.axhline(y=850, color='r', linestyle='dashed', label='Optimality treshold')

plt.title('Optimality gap = 0.05%')

# Adjust spacings w.r.t. figsize
fig.tight_layout()
# Alternatively: bbox_inches='tight' within the plt.savefig function
#                (overwrites figsize)

# Best for professional typesetting, e.g. LaTeX
plt.savefig("0.005.png")
# For raster graphics use the dpi argument. E.g. '[...].png", dpi=200)'

plt.show()

bb = pd.DataFrame()
CF = {}
for i in range(0, 4):
    aa = inputs[i]['units'].loc[:, ['PowerCapacity', 'Nunits', 'Fuel', 'Technology']]
    aa.to_csv('Capacity_' + str(scenario) + '_' + str(i) + '.csv')

    CF[i] = results[i]['OutputPower'].sum() / (inputs[i]['units'].loc[:,'PowerCapacity'] * inputs[i]['units'].loc[:,'Nunits']) / 8760
    CF[i].fillna(0, inplace=True)

    CF[i].to_csv('CF_' + str(scenario) + '_' + str(i) + '.csv')
