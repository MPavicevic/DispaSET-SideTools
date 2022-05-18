# -*- coding: utf-8 -*-
"""
This example shows how to run a batch of simulations by varying some of the input parameters or data
A base case is defined by the excel configuration file, then Dispa-SET functions are used to modify the input data
The input space is defined as a latin hypercube in which all the "corners" are simulated 
For each simulation, a separate simulation environment folder is created and the simualtion is run in GAMS 
Finally, all the folders with the result files are read and the results are stored in a dataframe exported to excel

the pyDOE library is required to run this script!

@author: Sylvain Quoilin
"""
#%%
#define function adjust_ntc
import logging
import shutil
from dispaset.misc.gdx_handler import write_variables
#from ..misc.gdx_handler import write_variables
def adjust_ntc(inputs, value=None, write_gdx=False, dest_path=''):
    """
    Function used to modify the net transfer capacities in the Dispa-SET generated input data
    The function update the Inputs.p file in the simulation directory at each call

    :param inputs:      Input data dictionary OR path to the simulation directory containing Inputs.p
    :param value:       Absolute value of the desired capacity (! Applied only if scaling != 1 !)
    :param write_gdx:   boolean defining if Inputs.gdx should be also overwritten with the new data
    :param dest_path:   Simulation environment path to write the new input data. If unspecified, no data is written!
    :return:            New SimData dictionary
    """
    import pickle

    if isinstance(inputs, str):
        path = inputs
        inputfile = path + '/Inputs.p'
        if not os.path.exists(path):
            sys.exit('Path + "' + path + '" not found')
        with open(inputfile, 'rb') as f:
            SimData = pickle.load(f)
    elif isinstance(inputs, dict):
        SimData = inputs
        path = SimData['config']['SimulationDirectory']
    else:
        logging.error('The input data must be either a dictionary or string containing a valid directory')
        sys.exit(1)

    if value is not None:
        SimData['parameters']['FlowMaximum']['val']=SimData['parameters']['FlowMaximum']['val']*value
    else:
        pass

    if dest_path == '':
        logging.info('Not writing any input data to the disk')
    else:
        if not os.path.isdir(dest_path):
            shutil.copytree(path, dest_path)
            logging.info('Created simulation environment directory ' + dest_path)
        logging.info('Writing input files to ' + dest_path)
        with open(os.path.join(dest_path, 'Inputs.p'), 'wb') as pfile:
            pickle.dump(SimData, pfile, protocol=pickle.HIGHEST_PROTOCOL)
        if write_gdx:
            write_variables(SimData['config'], 'Inputs.gdx', [SimData['sets'], SimData['parameters']])
            shutil.copy('Inputs.gdx', dest_path + '/')
            os.remove('Inputs.gdx')
    return SimData

#%%
import numpy as np
import pandas as pd

# Add the root folder of Dispa-SET to the path so that the library can be loaded:
import sys,os
sys.path.append(os.path.abspath('..'))

# Import Dispa-SET
import dispaset as ds

# Define the boundaries of the inputs space:
overcapacity = [0.5,1.5]   # thermal capacity divided by peak load
share_flex = [0.01,0.99]     # share of the thermal capacity that is flexible
share_sto  = [0,0.5]     # Storage Power divided by the peak load
share_wind = [0,0.5]     # Yearly wind generation divided by peak load * CF
share_pv = [0.2,0.5]       # Yearly PV generation divided by peak load *CF
r_ntc = [0,0.7]                   # sum of the flow ntc divided by maximum load * weight

# Define the folder in which all simulations should be stored:
#sim_folder = '..\\Simulations\\batch2\\reference\\'
sim_folder = os.path.pardir + os.sep + 'Simulations' + os.sep + 'batch' + os.sep + 'reference' + os.sep

# Load the configuration file
config = ds.load_config_excel(os.path.pardir + os.sep + 'ConfigFiles' + os.sep + 'ConfigTest_Matijs1.xlsx')
#config = ds.load_config_excel('../ConfigFiles/ConfigTest_Matijs1.xlsx')

config['SimulationDirectory']=sim_folder
                         
# # Limit the simulation period (for testing purposes, comment the line to run the whole year)
# config['StartDate'] = (2019, 1, 1, 0, 0, 0)
# config['StopDate'] = (2019, 1, 2, 0, 0, 0)
 
# #comment when on cluster
# config['GAMS_folder']='C:\\GAMS\\win64\\24.5'

# Build the  reference simulation environment:
SimData = ds.build_simulation(config)

# get a few important values:
load_max = SimData['parameters']['Demand']['val'][0].sum(axis=0).max()      # peak load

h_=SimData['parameters']['AvailabilityFactor']['val'].mean(axis=1)
df_=pd.DataFrame(h_, index=SimData['sets']['au'], columns=['AvFactor_hmean'])

CF_pv=df_.filter(like='PHOT', axis=0).mean().loc['AvFactor_hmean']       # capacity factor of PV
CF_wton=df_.filter(like='WTOF',axis=0).mean().loc['AvFactor_hmean']      # capacity factor of onshore wind (?)
CF_pv_list=df_.filter(like='PHOT', axis=0)       
CF_wton_list=df_.filter(like='WTOF',axis=0)

units = SimData['units']
flex_units = units[ units.Fuel.isin( ['GAS','HRD','OIL','BIO','LIG','PEA','NUC','GEO'] ) & (units.PartLoadMin < 0.5) & (units.TimeUpMinimum <5)  & (units.RampUpRate > 0.01)  ].index
slow_units = units[ units.Fuel.isin( ['GAS','HRD','OIL','BIO','LIG','PEA','NUC','GEO'] ) & ((units.PartLoadMin >= 0.5) | (units.TimeUpMinimum >=5)  | (units.RampUpRate <= 0.01)   )  ].index
#sto_units =  units[ units.StorageCapacity > 0].index
sto_units =  units[ units.Fuel.isin( ['OTH'] ) ].index
wind_units =  units[ units.Fuel.isin( ['WIN'] ) ].index
pv_units =   units[ units.Technology == 'PHOT'].index   
hror_units = units[ units.Technology == 'HROR'].index   

ref = {}
ref['overcapacity'] = (units.PowerCapacity[flex_units].sum() + units.PowerCapacity[slow_units].sum() + units.PowerCapacity[sto_units].sum())/load_max
ref['share_flex'] = units.PowerCapacity[flex_units].sum() / (units.PowerCapacity[flex_units].sum() + units.PowerCapacity[slow_units].sum())
#ref['hours_sto'] = units.StorageCapacity[sto_units].sum() / units.PowerCapacity[sto_units].sum()
ref['share_sto'] = units.PowerCapacity[sto_units].sum()/load_max
ref['share_wind'] = units.PowerCapacity[wind_units].sum()/load_max*CF_wton
ref['share_pv'] = units.PowerCapacity[pv_units].sum()/load_max*CF_pv

#%%
#  RNTC	
h_mean=SimData['parameters']['FlowMaximum']['val'].mean(axis=1)
NTC = pd.DataFrame(h_mean, index=SimData['sets']['l'], columns=['FlowMax_hmean']).groupby(level=0).sum()

countries=SimData['sets']['n']
#load=(SimData['parameters']['Demand']['val'].sum(axis=0)).sum(axis=1)
max_load=(SimData['parameters']['Demand']['val'].max(axis=0)).max(axis=1)
    
#df_load=pd.DataFrame(load, index=countries, columns=['load'])
df_maxload=pd.DataFrame(max_load, index=countries, columns=['max_load'])
    
for c in countries:
    ntc=0
    for l in NTC.index:
        if c in l: 
            ntc+=NTC.loc[l,'FlowMax_hmean']
    df_maxload.loc[c,'rNTC'] = ntc/2/df_maxload.loc[c,'max_load']

df_maxload['weigthed'] = df_maxload['max_load'] * df_maxload['rNTC']/df_maxload['max_load'].sum()

ref['rNTC'] = df_maxload['weigthed'].sum()     

print(ref)
print(CF_pv, CF_wton)

#%%

#Generate a 6-dimensional latin hypercube varying between 0 and 1:
from pyDOE import lhs
lh = lhs(6, samples=2)

#Add all the corners of the hypercube to the input space:
import itertools
lst = list(itertools.product([0, 1], repeat=6))
lh = np.concatenate((lh,np.array(lst)))

#%%
#Loop through the input space (time consuming !!):
Nruns = lh.shape[0]
for i in range(Nruns):
    print('Run ' + str(i+1) + ' of ' + str(Nruns))
    cap = overcapacity[0] + lh[i,0] * (overcapacity[-1] - overcapacity[0])
    flex = share_flex[0] + lh[i,1] * (share_flex[-1] - share_flex[0])
    sto = share_sto[0] + lh[i,2] * (share_sto[-1] - share_sto[0])
    wind = share_wind[0] + lh[i,3] * (share_wind[-1] - share_wind[0])
    pv = share_pv[0] + lh[i,4] * (share_pv[-1] - share_pv[0])
    net = r_ntc[0] + lh[i,5] * (r_ntc[-1] - r_ntc[0])

    folder = sim_folder + os.path.pardir + os.sep + "%.2f" % cap  + ' - ' + "%.2f" % flex + ' - ' + "%.2f" % sto + ' - ' + "%.2f" % wind + ' - ' + "%.2f" % pv + ' - ' + "%.2f" % net

    # in the first iteration, we load the input data from the original simulation directory:
    SimData = ds.adjust_capacity(sim_folder,('BATS','OTH'),singleunit=True,value=load_max*sto)
    
    # then we use the dispa-set fuction to adjust the installed capacities:
    SimData = ds.adjust_capacity(SimData,('COMC','GAS'),singleunit=True,value=load_max*(1+cap)*flex)
    SimData = ds.adjust_capacity(SimData,('STUR','NUC'),singleunit=True,value=load_max*cap*(1-flex))
    #SimData = ds.adjust_storage(SimData,('HPHS','WAT'),value=hours*load_max)
    
    # dispa-set function to adjust the ntc:
    SimData = adjust_ntc(SimData, value=net)
    
    # For wind and PV, the units should be lumped into a single unit:
    SimData = ds.adjust_capacity(SimData,('WTON','WIN'),value=load_max*cap*wind/CF_wton,singleunit=True)
    
    # In this last iteration, the new gdx file is written to the simulation folder:
    SimData = ds.adjust_capacity(SimData,('PHOT','SUN'),value=load_max*cap*pv/CF_pv,singleunit=True,write_gdx=True,dest_path=folder)
    
    # Finally the modified simulation environment is simulated:
    #h = ds.solve_GAMS(folder, config['GAMS_folder'])