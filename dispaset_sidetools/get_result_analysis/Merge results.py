
#%% Import results 

import sys,os
sys.path.append(os.path.abspath(r'C:\Users\Andrea\GitHub\Dispa-SET-2.3'))

# Import Dispa-SET
import dispaset as ds

inputs, results = ds.get_sim_results(path=r"C:\Users\Andrea\GitHub\Dispa-SET-2.3\Simulations\Article PROres1 coupling\TIMES_ProRes_2050_EVFLEX_new",cache=False)
inputs0, results_aug = ds.get_sim_results(path=r"C:\Users\Andrea\GitHub\Dispa-SET-2.3\Simulations\Article PROres1 coupling\TIMES_ProRes_2050_EVFLEX_new_aug",cache=False)
#inputs1, results_apr = ds.get_sim_results(path=r"C:\Users\Andrea\GitHub\Dispa-SET-2.3\Simulations\Article PROres1 coupling\TIMES_ProRes_2050_ALLFLEX_new_apr",cache=False)
#inputs2, results_aug = ds.get_sim_results(path=r"C:\Users\Andrea\GitHub\Dispa-SET-2.3\Simulations\Article PROres1 coupling\TIMES_ProRes_2050_ALLFLEX_new_aug",cache=False)
#inputs3, results_oct = ds.get_sim_results(path=r"C:\Users\Andrea\GitHub\Dispa-SET-2.3\Simulations\Article PROres1 coupling\TIMES_ProRes_2050_ALLFLEX_new_oct",cache=False)
#inputs4, results_nov = ds.get_sim_results(path=r"C:\Users\Andrea\GitHub\Dispa-SET-2.3\Simulations\Article PROres1 coupling\TIMES_ProRes_2050_ALLFLEX_new_nov",cache=False)
#

import pandas as pd
start_remove1 = pd.to_datetime('2016-8-28')
end_remove1 = pd.to_datetime('2016-9-5 23')
#start_remove2 = pd.to_datetime('2016-4-3')
#end_remove2 = pd.to_datetime('2016-4-11 23')
#start_remove3 = pd.to_datetime('2016-8-10')
#end_remove3 = pd.to_datetime('2016-8-18 23')
#start_remove4 = pd.to_datetime('2016-10-24')
#end_remove4 = pd.to_datetime('2016-11-1 23')
#start_remove5 = pd.to_datetime('2016-11-14')
#end_remove5 = pd.to_datetime('2016-11-22 23')

#%% Create merged results

results_t = {}
for d in results:
    if d == 'LostLoad_WaterSlack':
        print('Water slack taken from long simmulation')
        results_t[d] = results[d]
    elif d in ['LostLoad_MaxPower', 'LostLoad_2U', 'LostLoad_RampDown', 'LostLoad_RampUp', 'LostLoad_3U',
               'LostLoad_MinPower', 'LostLoad_2D', 'OutputShedLoad']:
        # if (start_remove) and (end_remove) in results[d].index:
        results[d] = pd.concat([results[d][:start_remove1], results[d][end_remove1:]])
#        results[d] = pd.concat([results[d][:start_remove2], results[d][end_remove2:]])
#        results[d] = pd.concat([results[d][:start_remove3], results[d][end_remove3:]])
#        results[d] = pd.concat([results[d][:start_remove4], results[d][end_remove4:]])
#        results[d] = pd.concat([results[d][:start_remove5], results[d][end_remove5:]])
#        tmp = results[d].merge(results_mar[d], how='outer', left_index = True, right_index=True)
#        tmp2 = tmp.merge(results_apr[d], how='outer', left_index = True, right_index=True)
#        tmp3 = tmp2.merge(results_aug[d], how='outer', left_index = True, right_index=True)
#        tmp4 = tmp3.merge(results_oct[d], how='outer', left_index = True, right_index=True)
        results_t[d] = results[d].combine_first(results_aug[d])
#        , how='outer', left_index = True, right_index=True)
        results_t[d].fillna(0,inplace=True)

    else:
#        tmp = results_mar[d].combine_first(results_apr[d])
#        tmp2 = tmp.combine_first(results_aug[d])
#        tmp3 = tmp2.combine_first(results_oct[d])
#        tmp4 = tmp3.combine_first(results_nov[d])
        results_t[d] = results_aug[d].combine_first(results[d])
        results_t[d].fillna(0,inplace=True)

#%% Export results to pickle
        
import pickle

file = open(r"C:\Users\Andrea\OneDrive - Politecnico di Milano\Università\Tesi (OneDrive)\Article PROres1 coupling\Simulations and results\TIMES_ProRes_2050_EVFLEX_new\EVFLEX_new.pkl",'wb')

pickle.dump(inputs, file)
pickle.dump(results_t, file)

file.close()

import pickle
file = open(r"C:\Users\Andrea\OneDrive - Politecnico di Milano\Università\Tesi (OneDrive)\Article PROres1 coupling\Simulations and results\TIMES_ProRes_2050_ALLFLEX_new\ALLFLEX_new.pkl", 'rb')
inputs = pickle.load(file)
results = pickle.load(file)
file.close()