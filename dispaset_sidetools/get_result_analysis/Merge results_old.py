inputs, results = ds.get_sim_results(config['SimulationDirectory'],cache=False)
inputs, results_j = ds.get_sim_results(config['SimulationDirectory'],cache=False)
inputs, results_f = ds.get_sim_results(config['SimulationDirectory'],cache=False)


import pandas as pd
start_remove1 = pd.to_datetime('2016-1-1')
end_remove1 = pd.to_datetime('2016-1-10 23')
start_remove2 = pd.to_datetime('2016-2-15')
end_remove2 = pd.to_datetime('2016-2-23 23')

results_t = {}
for d in results:
    if d == 'LostLoad_WaterSlack':
        print('Water slack taken from long simmulation')
        results_t[d] = results[d]
    elif d in ['LostLoad_MaxPower', 'LostLoad_2U', 'LostLoad_RampDown', 'LostLoad_RampUp', 'LostLoad_3U',
               'LostLoad_MinPower', 'LostLoad_2D']:
        # if (start_remove) and (end_remove) in results[d].index:
        results[d] = pd.concat([results[d][:start_remove1], results[d][end_remove1:]])
        results[d] = pd.concat([results[d][:start_remove2], results[d][end_remove2:]])
        tmp = results[d].merge(results_j[d], how='outer', left_index = True, right_index=True)
        results_t[d] = tmp.merge(results_f[d], how='outer', left_index=True, right_index=True)
        results_t[d].dropna(inplace=True)

    else:
        tmp = results_j[d].combine_first(results_f[d])
        results_t[d] = tmp.combine_first(results[d])
        results_t[d].fillna(0,inplace=True)

import pickle

file = open('ALLFLEX.pkl','wb')

pickle.dump(inputs, file)
pickle.dump(results_t, file)

file.close()

import pickle
file = open('ALLFLEX.pkl', 'rb')
inputs = pickle.load(file)
results = pickle.load(file)
file.close()