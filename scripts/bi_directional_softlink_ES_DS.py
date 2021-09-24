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
config = {'run_ES': False,
          'import_reserves': '',
          'importing': True,
          'printing': False,
          'printing_td': False,
          'GWP_limit': 70000,  # [ktCO2-eq./year]	# Minimum GWP reduction
          'data_folders': data_folders,
          'ES_path': ES_path,
          'step1_output': step1_output,
          'all_data': pd.DataFrame(),
          'Working_directory': os.getcwd()}

#%% ####################################
#### Update and Execute EnergyScope ####
########################################

# Reading the data
config['all_data'] = es.run_ES(config)
# No electricity imports
config['all_data'][1].loc['ELECTRICITY', 'avail'] = 0
# Printing and running
config['importing'] = False
config['printing'] = True
config['printing_td'] = True
config['run_ES'] = True
config['all_data'] = es.run_ES(config)

# compute the actual average annual emission factors for each resource
GWP_op = es.compute_gwp_op(config['data_folders'], config['ES_path'])
GWP_op.to_csv(ES_path+'\output\GWP_op.txt', sep='\t')


# Static Data - to be created only once
el_demand = dst.get_demand_from_es(ES_folder=ES_folder + '/')
th_demand = dst.get_heat_demand_from_es(ES_folder=ES_folder + '/')
af = dst.get_availability_factors_from_es(ES_folder=ES_folder + '/')

# Dynamic Data - to be modified in a loop
capacities = dst.get_capacities_from_es(ES_folder=ES_folder + '/', typical_units_folder=typical_units_folder)

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
inputs, results = ds.get_sim_results(config['SimulationDirectory'], cache=False)
