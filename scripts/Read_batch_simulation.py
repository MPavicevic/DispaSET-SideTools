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
    
import pandas as pd

# Add the root folder of Dispa-SET to the path so that the library can be loaded:
import sys,os
sys.path.append(os.path.abspath('..'))

# Import Dispa-SET
import dispaset as ds

# Define the folder in which all simulations should be stored:
#sim_folder = '..\\Simulations\\batch_simulation\\'
sim_folder = os.path.pardir + os.sep + 'Simulations' + os.sep + 'batch' + os.sep

#%%
# Read all the simulation folders one by one and store key results in dataframe:
paths = os.listdir(sim_folder)
# Only take into account the ones for which a valid dispa-set result file is present and not infeasible
paths_ok = [x for x in paths if os.path.isfile(sim_folder + x + os.sep + 'Results.gdx')]
paths_ok = [x for x in paths_ok if not os.path.isfile(sim_folder + x + os.sep + 'debug.gdx')]
paths_ok.remove('reference')


N = len(paths_ok)
data = pd.DataFrame(index = range(N))

for i,path in enumerate(paths_ok):
    
    # Load the simulation results:
    inputs,results = ds.get_sim_results(path=sim_folder + path,cache=True)
    
    # Power generation for each hour by fuel:
    FuelPower = ds.aggregate_by_fuel(results['OutputPower'], inputs, SpecifyFuels=None)
    
    # Installed capacities for each country by fuel:
    cap = ds.plot_zone_capacities(inputs,results,plot=False)
    
    # Capacity factors:
    CF = {}
    #CF={'GAS':CF, 'NUC':CF}
    for f in ['GAS','NUC','WAT','WIN','SUN']:
        CF[f] = FuelPower[f].sum()/ (cap['PowerCapacity'][f].sum()*8760)
    
    # Analyse the results for each country and provide quantitative indicators:
    r = ds.get_result_analysis(inputs,results)
    
    # Compute total lost load
    LostLoad=0
    for key in ['LostLoad_MaxPower','LostLoad_MinPower','LostLoad_2D','LostLoad_2U','LostLoad_3U', 'LostLoad_RampDown','LostLoad_RampUp']:
    #for key in ['Out_LostLoad_MaxPower','Out_LostLoad_MinPower','Out_LostLoad_Reserve2D','Out_LostLoad_Reserve2U']:
        if key in results:
            LostLoad = results[key].sum().sum()
    
    #Add inputs
    ovcap,flex,hours,sto,wind,pv,net=path.split(' - ')
    
    data.loc[i,'Overcapacity']=ovcap
    data.loc[i,'Share flex']=flex
    data.loc[i,'Hours sto']=hours
    data.loc[i,'Share sto']=sto
    data.loc[i,'Share wind']=wind
    data.loc[i,'Share pv']=pv
    data.loc[i,'rNTC']=net

    data.loc[i,'Cost [E/Mwh]'] = r['Cost_kwh'] #tbc
    data.loc[i,'Congestion [h]']=sum(r['Congestion'].values())
    
    data.loc[i,'PeakLoad [MW]'] = r['PeakLoad']
    
    data.loc[i,'MaxCurtailment [MW]'] = r['MaxCurtailment']
    data.loc[i,'MaxLoadShedding [MW]'] = r['MaxShedLoad']
    
    data.loc[i,'Demand [Twh]'] = r['TotalLoad']/1E6
    data.loc[i,'NetImports [Twh]']=r['NetImports']/1E6
    
    data.loc[i,'Curtailment [MWh]'] = r['Curtailment']/1E6
    data.loc[i,'Shedding [MWh]'] = r['ShedLoad']/1E6
    
    data.loc[i,'LostLoad'] = LostLoad
    data.loc[i,'CF_gas'] = CF['GAS']
    data.loc[i,'CF_nuc'] = CF['NUC']
    data.loc[i,'CF_wat'] = CF['WAT']
    data.loc[i,'CF_win'] = CF['WIN']
    data.loc[i,'CF_sun'] = CF['SUN']

data.fillna(0,inplace=True)
data.to_csv(sim_folder + 'dispaset_results.csv',index=False)