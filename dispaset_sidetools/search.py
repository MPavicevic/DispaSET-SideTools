import pandas as pd


#function that provides the value contained in the Assets.txt file (output from EnergyScope)

#ATTENTION : Assets.txt file has to be provided when running EnergyScope with AMPL 

#Input :    tech = technology studied
#           feat = feature needed regarding to the technology studied
#Output :   Value of the feature asked

def search_assets(tech,feat):
    
    input_folder = '../../Inputs/'  # input file = Assets.txt (to find installed power f [GW or GWh for storage])
    output_folder = '../../Outputs/'
    assets = pd.read_csv(input_folder + 'Assets.txt', delimiter = '\t')
    
    features = list(assets.head())
    features = [x.strip(' ') for x in features]
    column = features.index(feat) 
    col_names = features[1:]

    col_names.append("end")
    assets.columns = col_names
    

    output = assets.at[tech,feat]

    return output


    
