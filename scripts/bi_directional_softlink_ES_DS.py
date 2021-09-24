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
ES_folder = '../../EnergyScope'
DST_folder = '../../DispaSET-SideTools'

data_folders = [ES_folder + '/Data/User_data', ES_folder + '/Data/Developer_data']
ES_path = ES_folder + '/STEP_2_Energy_Model'
step1_output = ES_folder + '/STEP_1_TD_selection/TD_of_days.out'

#%% ###################################
########### Editable inputs ###########
#######################################
import_reserves = False
run_ES = True

GWP_limit = 70000  # [ktCO2-eq./year]	# Minimum GWP reduction

#%% ####################################
#### Update and Execute EnergyScope ####
########################################

# Reading the data
(Eud, Resources, Technologies, End_uses_categories, Layers_in_out, Storage_characteristics, Storage_eff_in,
 Storage_eff_out, Time_Series) = es.import_data(data_folders)

# Data changes
Resources.loc['ELECTRICITY', 'avail'] = 0

# Printing ESTD_data.dat
all_df = (Eud, Resources, Technologies, End_uses_categories, Layers_in_out, Storage_characteristics, Storage_eff_in,
          Storage_eff_out, Time_Series)

es.print_data(all_df, ES_path, GWP_limit)

# Printing ESD_12TD.dat
if import_reserves:
    # TODO: Make more elegant without so much processing and generalize country names (not only ES)
    reserves = pd.read_csv('Reserves.csv')
    reserves.index = range(1, len(reserves) + 1)
    reserves = reserves.loc[:, 'ES']
    reserves = pd.DataFrame(reserves/1000 + 3)
    reserves.rename(columns={'ES': 'end_uses_reserve'}, inplace=True)
    es.print_td_data(Time_Series, ES_path, step1_output, end_uses_reserve=reserves)
else:
    es.print_td_data(Time_Series, ES_path, step1_output)

# run the energy system optimisation model with AMPL
if run_ES:
    os.chdir(ES_folder + '/STEP_2_Energy_Model')
    os.system('cmd /c "ampl ESTD_main.run"')
    os.chdir(DST_folder + '/scripts')

    # compute the actual average annual emission factors for each resource
    GWP_op = es.compute_gwp_op(data_folders, ES_path)
    GWP_op.to_csv(ES_folder + '/STEP_2_Energy_Model/output/GWP_op.txt', sep='\t')


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
