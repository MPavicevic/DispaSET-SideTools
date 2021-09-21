# Add the root folder of Dispa-SET-side tools to the path so that the library can be loaded:
import sys,os
sys.path.append(os.path.abspath('..'))

import pandas as pd
import numpy as np
import dispaset as ds
import dispaset_sidetools as dst

ES_folder = '../../EnergyScope/'
typical_units_folder = '../Inputs/EnergyScope/'

# Data to be created only once
aa = dst.get_demand_from_es(ES_folder=ES_folder)
bb = dst.get_heat_demand_from_es(ES_folder=ES_folder)
cc = dst.get_availability_factors_from_es(ES_folder=ES_folder)

# Data to be modified in a loop
dd = dst.get_capacities_from_es(ES_folder=ES_folder, typical_units_folder=typical_units_folder)

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

#%% ####################################
#### Update and Execute EnergyScope ####
########################################


