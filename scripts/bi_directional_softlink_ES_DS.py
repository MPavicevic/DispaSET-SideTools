# Add the root folder of Dispa-SET-side tools to the path so that the library can be loaded:
import sys,os
sys.path.append(os.path.abspath('..'))

import pandas as pd
import numpy as np
import dispaset as ds
import dispaset_sidetools as dst
import energyscope as es

#%% ###################################
############## Path setup #############
#######################################
# Typical units
typical_units_folder = '../Inputs/EnergyScope/'

# Energy Scope
ES_folder = '../../EnergyScope_Github/EnergyScope_pythonUI'
DST_folder = '../../DispaSET-SideTools'

data_folders = [ES_folder + '/Data/User_data', ES_folder + '/Data/Developer_data']
ES_path = ES_folder + '/STEP_2_Energy_Model'
step1_output = ES_folder + '/STEP_1_TD_selection/TD_of_days.out'

#%% ###################################
########### Editable inputs ###########
#######################################
config_es = {'run_ES': False,
          'importing': True,
          'printing': False,
          'printing_td': False,
          'GWP_limit': 70000,  # [ktCO2-eq./year]	# Minimum GWP reduction
          'data_folders': data_folders,
          'ES_path': ES_path,
          'step1_output': step1_output,
          'all_data': pd.DataFrame(),
          'Working_directory': os.getcwd(),
          'import_reserves': '',
          'reserves': pd.DataFrame()}

#%% ####################################
#### Update and Execute EnergyScope ####
########################################

# Reading the data
config_es['all_data'] = es.run_ES(config_es)
# No electricity imports
config_es['all_data'][1].loc['ELECTRICITY', 'avail'] = 0
# Printing and running
config_es['importing'] = False
config_es['printing'] = True
config_es['printing_td'] = True
config_es['run_ES'] = True
config_es['all_data'] = es.run_ES(config_es)




# Static Data - to be created only once
el_demand = dst.get_demand_from_es(ES_folder=ES_folder + '/')
th_demand = dst.get_heat_demand_from_es(ES_folder=ES_folder + '/')
af = dst.get_availability_factors_from_es(ES_folder=ES_folder + '/')

inputs = dict()
results = dict()
GWP_op = dict()
capacities = dict()
reserves = dict()
shed_load = dict()

for i in range(2):
    # Dynamic Data - to be modified in a loop
    # compute the actual average annual emission factors for each resource
    GWP_op[i] = es.compute_gwp_op(config_es['data_folders'], config_es['ES_path'])
    GWP_op[i].to_csv(ES_path+'\output\GWP_op.txt', sep='\t') #TODO automate
    capacities[i] = dst.get_capacities_from_es(ES_folder=ES_folder + '/', typical_units_folder=typical_units_folder)

    #%% ###################################
    ########## Execute Dispa-SET ##########
    #######################################
    # Load the configuration file
    config = ds.load_config('../ConfigFiles/Config_EnergyScope.xlsx')

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
    reserves[i] = pd.DataFrame(inputs[i]['param_df']['Demand'].loc[:,'2U'].values/1000, columns=['end_uses_reserve'],
                                                    index=np.arange(1, 8761, 1))

    if i>=1:
        shed_load[i] = pd.DataFrame(results[i]['OutputShedLoad'].values/1000, columns=['end_uses_reserve'],
                                                        index=np.arange(1, 8761, 1))

        config_es['reserves'] = config_es['reserves'] + shed_load[i]
    else:
        config_es['reserves'] = reserves[i]

    config_es['all_data'] = es.run_ES(config_es)


# # Plots
# # import pandas as pd
# import pandas as pd
# rng = pd.date_range('2015-1-01','2015-12-31', freq='H')
# # Generate country-specific plots
# ds.plot_zone(inputs, results, rng=rng, z_th='ES_DHN')
#
# # Bar plot with the installed capacities in all countries:
# cap = ds.plot_zone_capacities(inputs, results)
#
# # Bar plot with installed storage capacity
# sto = ds.plot_tech_cap(inputs)
#
# # Violin plot for CO2 emissions
# ds.plot_co2(inputs, results, figsize=(9,6), width=0.9)
#
# # Bar plot with the energy balances in all countries:
# ds.plot_energy_zone_fuel(inputs,results,ds.get_indicators_powerplant(inputs,results))
#
# # Analyse the results for each country and provide quantitative indicators:
# r = ds.get_result_analysis(inputs,results)
#
