import pandas as pd
import glob


input_folder = '../Inputs/'  # to access DATA - DATA_brut & Typical_Units(to find installed power f [GW or GWh for storage])
input_PP_folder = '../../Dispa-SET.git/Database/PowerPlants/'  # input file = Assets.txt (to find installed power f [GW or GWh for storage])
output_folder = '../../Outputs/'

Typical_Units = pd.read_csv(input_folder + 'Typical_Units.csv')

#function which loops over DS databse for a given tech_fuel combination, in order to find a typical unit

#Create Dataframe with the DS column names, and as index, all the TECH in DS terminology    
# Are these the right columns ? - TO CHECK
column_names = ['Unit', 'PowerCapacity', 'Nunits', 'Zone', 'Technology', 'Fuel', 'Efficiency', 'MinUpTime',
        'MinDownTime', 'RampUpRate', 'RampDownRate', 'StartUpCost_pu', 'NoLoadCost_pu',
        'RampingCost', 'PartLoadMin', 'MinEfficiency', 'StartUpTime', 'CO2Intensity',
        'CHPType', 'CHPPowerToHeat', 'CHPPowerLossFactor', 'COP', 'Tnominal', 'coef_COP_a', 'coef_COP_b',
        'STOCapacity', 'STOSelfDischarge', 'STOMaxChargingPower', 'STOChargingEfficiency', 'CHPMaxHeat']

#Input :    tech = technology studied
#           feat = feature needed regarding to the technology studied
#Output :   Dataframe with oeline containing the new Typical Unit

def search_TypicalUnits(tech,fuel):
    
    #Créer la liste des fichiers à parcourir
    files = [f for f in glob.glob(input_folder + "**/*.csv", recursive=True)]
    
    #Parcourir les fichiers dans tous les dossiers et sous-dossiers
    for f in files:
        PowerPlants = pd.read_csv(f)
#        print(f)
        
        #Si on tient le bon couple de tech_fuel...
        if (not PowerPlants.loc[(PowerPlants['Technology'] == tech) & (PowerPlants['Fuel'] == fuel)].empty):            
            print('[INFO] : correspondance found for',(tech,fuel),'in file',f)
            # Sort columns as they should be 
            try :
                PowerPlants = PowerPlants[column_names]
                return PowerPlants.loc[(PowerPlants['Technology'] == tech) & (PowerPlants['Fuel'] == fuel)]
            except :
                print('not the right format of column_names in file',f)
                
            return PowerPlants.loc[(PowerPlants['Technology'] == tech) & (PowerPlants['Fuel'] == fuel)]
#            print(PowerPlants.loc[(PowerPlants['Technology'] == tech) & (PowerPlants['Fuel'] == fuel)])
            
            
            
    
#    print(PowerPlants)

    
    return  pd.DataFrame(columns = column_names) #'NOTHING for' + tech + fuel


def search_TypicalUnits_CHP(tech,fuel,CHPType):
    
    #Créer la liste des fichiers à parcourir
    files = [f for f in glob.glob(input_folder + "**/*.csv", recursive=True)]
    
    #Parcourir les fichiers dans tous les dossiers et sous-dossiers
    for f in files:
        PowerPlants = pd.read_csv(f)
#        print(f)
#        print(PowerPlants.loc[(PowerPlants['Technology'] == tech) & (PowerPlants['Fuel'] == fuel),'CHPType'])
        #Si on tient le bon couple de tech_fuel...
        if (not PowerPlants.loc[(PowerPlants['Technology'] == tech) & (PowerPlants['Fuel'] == fuel)  & (PowerPlants['CHPType'] == CHPType)].empty):            
            print('[INFO] : correspondance found for',(tech,fuel,CHPType),'in file',f)
            # Sort columns as they should be 
            try :
                PowerPlants = PowerPlants[column_names]
                return PowerPlants.loc[(PowerPlants['Technology'] == tech) & (PowerPlants['Fuel'] == fuel)  & (PowerPlants['CHPType'] == CHPType)]
            except :
                print('not the right format of column_names in file',f)                
                
            return PowerPlants.loc[(PowerPlants['Technology'] == tech) & (PowerPlants['Fuel'] == fuel)  & (PowerPlants['CHPType'] == CHPType)]
        
        elif (not PowerPlants.loc[(PowerPlants['Technology'] == tech) & (PowerPlants['Fuel'] == fuel)  & (PowerPlants['CHPType'] == 'Extraction')].empty):
                      
            print('[WARNING] : no correspondance found for',(tech,fuel,CHPType),'but well for CHPType = Extraction ; imposed filling typical units with the Extraction type as',CHPType)
            PowerPlants.loc[(PowerPlants['Technology'] == tech) & (PowerPlants['Fuel'] == fuel),'CHPType' ] = 'back-pressure'
            
            return PowerPlants.loc[(PowerPlants['Technology'] == tech) & (PowerPlants['Fuel'] == fuel) ]
            
   
    return  pd.DataFrame(columns = column_names) #'NOTHING for' + tech + fuel


def write_TypicalUnits(missing_tech):
    
    Typical_Units = pd.read_csv(input_folder + 'Typical_Units.csv')
    powerplants = pd.DataFrame(columns = column_names) 
    
    for (i,j) in missing_tech :
#        print(i,j)
        tmp = search_TypicalUnits(i,j)
        if  tmp.empty :
            print('[WARNING] : no correspondance found for the TECH_FUEL :',(i,j))
        else :
#            print(tmp)
            powerplants = pd.concat([powerplants,tmp ])
            
    Typical_Units = pd.concat([Typical_Units,powerplants])
    Typical_Units.to_csv(input_folder + 'Typical_Units_modif.csv',index = False)
#    print(Typical_Units)

def write_TypicalUnits_CHP(missing_tech_CHP):
    
    Typical_Units = pd.read_csv(input_folder + 'Typical_Units.csv')
    powerplants = pd.DataFrame(columns = column_names) 
    
#    print(missing_tech_CHP)
    for (i,j,k) in missing_tech_CHP :
#        print(i,j)
        tmp = search_TypicalUnits_CHP(i,j,k)
        if  tmp.empty :
            print('[WARNING] : no correspondance found for the TECH_FUEL :',(i,j,k))
        else :
#            print(tmp)
            powerplants = pd.concat([powerplants,tmp ])
            
    Typical_Units = pd.concat([Typical_Units,powerplants])
    Typical_Units.to_csv(input_folder + 'Typical_Units_modif.csv',index = False)
#    print(Typical_Units)
            

#List of TECH_FUEL to get : HROR WAT, COMC HRD, STUR BIO/WST/OIL/HYD
missing_tech = [['HROR','WAT'],['COMC','HRD'],['STUR','BIO'],['STUR','WST'],['STUR','OIL'],['STUR','HYD']]
missing_chp = [['STUR','BIO','back-pressure'],['STUR','WST','back-pressure'],['STUR','OIL','back-pressure']]

write_TypicalUnits(missing_tech)
write_TypicalUnits_CHP(missing_chp)
            
    
#print(search_TypicalUnits('HROR','WAT'))
#print(search_TypicalUnits('COMC','HRD'))
#
#print(search_TypicalUnits('STUR','BIO'))
#print(search_TypicalUnits('STUR','WST'))
#print(search_TypicalUnits('STUR','OIL'))
#print(search_TypicalUnits('STUR','HYD'))