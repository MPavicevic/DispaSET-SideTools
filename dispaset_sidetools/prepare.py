from __future__ import division

import sys, os
sys.path.append(os.path.abspath(r'..'))

from dispaset_sidetools import *
import numpy as np
import pandas as pd
import math

from dispaset_sidetools.common import *
from dispaset_sidetools.search import *
from dispaset_sidetools.constants import *

########################################################################################################################

#Run several functions from search.py
#get_TDFile('CH',input_folder_fromPrepare)

########################################################################################################################

def modify_ES_txt(ES_txtfiles):

    for x in countries:
        for file_name in ES_txtfiles:
            try:
                #open old file and create intermediate one
                oldfile = open(input_folder_fromPrepare + x + '/' + file_name + '.txt', 'r+')
                newfile = open(input_folder_fromPrepare + x + '/' + file_name + '_new.txt','w')

                for line in oldfile:
                    line = line.replace('Capitalf','F')
                    newfile.write(line)

                oldfile.close()
                newfile.close()
                os.remove(input_folder_fromPrepare + x + '/' + file_name + '.txt')

                #create final final and open intermediate one
                finalfile = open(input_folder_fromPrepare + x + '/' + file_name + '.txt', 'w')
                intermfile = open(input_folder_fromPrepare + x + '/' + file_name + '_new.txt','r+')

                for line in intermfile:
                    finalfile.write(line)

                finalfile.close()
                intermfile.close()
                os.remove(input_folder_fromPrepare + x + '/' + file_name + '_new.txt')
            except:
                print('INFO: ' + file_name + ' not in ' + x + ' input folder')

modify_ES_txt(ES_txtfiles)

########################################################################################################################

def get_perc_dhn():
    perc_dhn = list()
    for x in countries:
        Yearbalance_df = pd.read_csv(input_folder_fromPrepare + x + '/' + 'YearBalance.txt', delimiter = '\t')
        Yearbalance_df.set_index('Tech',inplace=True)
        perc_dhn.append( Yearbalance_df.loc[' END_USES_DEMAND ','HEAT_LOW_T_DHN'] / (Yearbalance_df.loc[' END_USES_DEMAND ','HEAT_LOW_T_DHN'] + Yearbalance_df.loc[' END_USES_DEMAND ','HEAT_LOW_T_DECEN']))
    print('Perc_dhn for ' + str(countries) + ':')
    print(perc_dhn)

#get_perc_dhn()


########################################################################################################################



#
#
# Input: - All HeatSlack (AKA boilers) present in Assets.txt
#        - DATA_BRUT.xlsx : 2.1 RESOURCES to get the resources price
#        - DATA_BRUT.xlsx : 3.2 TECH to get the specific tech operating costs
#        -
# Output: - A weighted average of the operating costs of the TECH_FUEL combination in boilers
#
def get_HeatSlackPrice(country, numTD,n_th,c_maint):
    n_TD = numTD

    RESOURCES = from_excel_to_dataFrame(input_folder_fromPrepare + country + '/' + 'DATA_preprocessing.xlsx', 'RESOURCES')          #Possède les prix des ressources dans la colonne c_op [Million_euros/GWh]
    print(RESOURCES)
    TECH = from_excel_to_dataFrame(input_folder_fromPrepare + country + '/' + 'DATA_preprocessing.xlsx', 'TECH')                    #Possède les prix d'opération des technologies dans la colonne c_maint
    layers_in_out = from_excel_to_dataFrame(input_folder_fromPrepare + country + '/' + 'DATA_preprocessing.xlsx', 'layers_in_out')                  #Possède les efficacités des techs boilers
    # Changer les index pour avoir les technologies en Index
    layers_in_out.index = layers_in_out.loc[:, 0]

    #Set Technologies as Index in RESOURCES (RESOURCES) and in TECH(param :)
    RESOURCES.set_index('{RESOURCES}',inplace=True)
    TECH.set_index('param:',inplace=True)

    #get a list with HeatSlack tech
    tech_HeatSlack = [k for k,v in mapping['SORT'].items() if v == 'HeatSlack']
    tech_HeatSlack_original = tech_HeatSlack.copy()
    tech_HeatSlack.append('Td ' )

# --------------------- PART TO DO WITH LTLayer ---------------------------- #
    #Part of the code where we check the ratio of production of all of the boilers
    LTLayers = pd.read_csv(input_folder_fromPrepare + country + '/' + 'LTLayers.txt', delimiter='\t')
    LTLayerscolumns = LTLayers.columns.values.tolist()

    # with this we extract all tech which correspond to a HeatSlack
    LTLayers = LTLayers[tech_HeatSlack]

    #Sum all production of Boilers per typical days - groupBy
    LTLayers = LTLayers.groupby(['Td ']).sum()

    LTLayers['DEC_SOLAR'] =  1 #Temporary, just to be able to make my check

    #Multiply the TD production per the mydistri
    mydistri = distri_TD(country, n_TD)
#    mydistri = [34, 22, 29, 53, 28, 23, 29, 24, 36, 54, 17, 16] #temporary, just to get the idea
    LTLayers = LTLayers.mul(mydistri, axis=0)

    #GroupBy on all typical days, in order to obtain total prod per year of each boiler tech
    LTLayers = LTLayers.sum()


    # --------------------- PART TO DO WITH HTLayer ---------------------------- #
    # Part of the code where we check the ratio of production of all of the boilers
    HTLayers = pd.read_csv(input_folder_fromPrepare + country + '/' + 'HTLayers.txt', delimiter='\t')
    HTLayerscolumns = HTLayers.columns.values.tolist()

    # with this we extract all tech which correspond to a HeatSlack
    HTLayers = HTLayers[tech_HeatSlack]

    # Sum all production of Boilers per typical days - groupBy
    HTLayers = HTLayers.groupby(['Td ']).sum()

    # Multiply the TD production per the mydistri - my distri is already defined above
    HTLayers = HTLayers.mul(mydistri, axis=0)

    # GroupBy on all typical days, in order to obtain total prod per year of each boiler tech
    HTLayers = HTLayers.sum()

    # ---------- NOW combine everything (LTLayers ad HTLayers) --------- #
    Heat = pd.concat([LTLayers,HTLayers])

    #get rid of duplicates ; because in any case no technologies can produce HT and LT at the same time - WATHC OUT : how do I get rid o duplicates that are worth zero
    Heat = Heat.sort_values(ascending=False)
    Heat = Heat.groupby(Heat.index).first()

    Heat_tot = Heat.sum()
    Heat_ratio = Heat / Heat_tot

    #Now we can add column to the dataframe (based on index):
    #       - c_maint for each technology (found in DATA_BRUT < 3.2 TECH)
    #       - c_op for each fuel (found in DATA_BRUT < 2.1 RESOURCES)
    #Note : to add the c_op, we need to have a correspondance with the Fuel
    Heat = Heat.to_frame().join(TECH['c_maint'], how='outer')
    #Heat = Heat.drop(0,axis=1)

    Fuel = pd.DataFrame.from_dict(mapping['FUEL_ES'],orient='index')
    Fuel = Fuel.reset_index().set_index(0) #Reset the index so that we can join properly the c_op
    Fuel = Fuel.join(RESOURCES['c_op [M€/GWh]'], how='outer')
    Fuel = Fuel.reset_index().set_index('index') #reset the technology as Index
    Fuel = Fuel.drop('level_0',axis=1) #drop the column with FUEL_ES
    Heat = Heat.join(Fuel, how='outer') #allows us to join c_op to the rest

    #keep only Boilers tech
    Heat = Heat[Heat.index.isin(tech_HeatSlack_original)]

    #gather the efficiency of LT HeatSlack technologies
    for tech in tech_HeatSlack_original:
        tech_resource = mapping['FUEL_ES'][tech]  # gets the correct column ressources to look up per CHP tech
        tech_heat = mapping['CHP_HEAT'][tech]  # gets the correct column heat to look up per CHP tech
        try:
            Efficiency = abs(layers_in_out.at[tech, tech_heat])/ abs(layers_in_out.at[tech, tech_resource])  # If the TECH is CHP  , Efficiency is simply abs(ELECTRICITY/RESSOURCES)
            Heat.loc[Heat.index == tech, 'Efficiency'] = Efficiency
        except:
            print('[WARNING] : technology ', tech, 'has not been found in layers_in_out')

    #Adjust real resources consumption thanks to the efficiencies
    Heat[0] = Heat[0].div(Heat['Efficiency'], axis='index')



    if n_th :
        Heat_DEC = Heat.loc[Heat.index.str.startswith('DEC')].copy()
        # Get the total prod of all Boilers to then define ratios of production for each tech
        Heat_tot = Heat_DEC[0].sum()
        Heat_DEC[0] = Heat_DEC[0] / Heat_tot
        #treat the NaN => set to 0
        Heat_DEC.fillna(0,inplace=True)

        Heat_DHN = Heat.loc[Heat.index.str.startswith('DHN')].copy()
        # Get the total prod of all Boilers to then define ratios of production for each tech
        Heat_tot = Heat_DHN[0].sum()
        Heat_DHN[0] = Heat_DHN[0] / Heat_tot
        #treat the NaN => set to 0
        Heat_DHN.fillna(0,inplace=True)

        Heat_IND = Heat.loc[Heat.index.str.startswith('IND')].copy()
        # Get the total prod of all Boilers to then define ratios of production for each tech
        Heat_tot = Heat_IND[0].sum()
        Heat_IND[0] = Heat_IND[0] / Heat_tot
        #treat the NaN => set to 0
        Heat_IND.fillna(0,inplace=True)

        if c_maint :
            ## ------- DEC ----------- ##
            #GW(h) in ES -> MW(h) in DS - TO DO
            Heat_DEC['c_maint'] = Heat_DEC['c_maint']/3.6 #go from [M€/GW/y] to [€/MWh] #price of maintenance of the Tech
            Heat_DEC['c_op [M€/GWh]'] = Heat_DEC['c_op [M€/GWh]']* 1000 #go from [M€/GWh] to [€/MWh] #price for the fuel
            #Get the HeatSlack Price : sum(ratio*(c_maint + c_op)) as full OPEX
            Heat_DEC['Price'] = Heat_DEC[0]*(Heat_DEC['c_op [M€/GWh]']+Heat_DEC['c_maint'])
            HeatSlackPrice_DEC = Heat_DEC['Price'].sum()
            ## ------- DHN ----------- ##
            #GW(h) in ES -> MW(h) in DS - TO DO
            Heat_DHN['c_maint'] = Heat_DHN['c_maint']/3.6 #go from [M€/GW/y] to [€/MWh] #price of maintenance of the Tech
            Heat_DHN['c_op [M€/GWh]'] = Heat_DHN['c_op [M€/GWh]']* 1000 #go from [M€/GWh] to [€/MWh] #price for the fuel
            #Get the HeatSlack Price : sum(ratio*(c_maint + c_op)) as full OPEX
            Heat_DHN['Price'] = Heat_DHN[0]*(Heat_DEC['c_op [M€/GWh]']+Heat_DHN['c_maint'])
            HeatSlackPrice_DHN = Heat_DHN['Price'].sum()
            ## ------- IND ----------- ##
            #GW(h) in ES -> MW(h) in DS - TO DO
            Heat_IND['c_maint'] = Heat_IND['c_maint']/3.6 #go from [M€/GW/y] to [€/MWh] #price of maintenance of the Tech
            Heat_IND['c_op [M€/GWh]'] = Heat_IND['c_op [M€/GWh]']* 1000 #go from [M€/GWh] to [€/MWh] #price for the fuel
            #Get the HeatSlack Price : sum(ratio*(c_maint + c_op)) as full OPEX
            Heat_IND['Price'] = Heat_IND[0]*(Heat_DEC['c_op [M€/GWh]']+Heat_IND['c_maint'])
            HeatSlackPrice_IND = Heat_IND['Price'].sum()

        else :
            ## ------- DEC ----------- ##
            #GW(h) in ES -> MW(h) in DS - TO DO
            Heat_DEC['c_op [M€/GWh]'] = Heat_DEC['c_op [M€/GWh]']* 1000 #go from [M€/GWh] to [€/MWh] #price for the fuel
            #Get the HeatSlack Price : sum(ratio*(c_maint + c_op)) as full OPEX
            Heat_DEC['Price'] = Heat_DEC[0]*(Heat_DEC['c_op [M€/GWh]'])
            HeatSlackPrice_DEC = Heat_DEC['Price'].sum()
            ## ------- DHN ----------- ##
            #GW(h) in ES -> MW(h) in DS - TO DO
            Heat_DHN['c_op [M€/GWh]'] = Heat_DHN['c_op [M€/GWh]']* 1000 #go from [M€/GWh] to [€/MWh] #price for the fuel
            #Get the HeatSlack Price : sum(ratio*(c_maint + c_op)) as full OPEX
            Heat_DHN['Price'] = Heat_DHN[0]*(Heat_DHN['c_op [M€/GWh]'])
            HeatSlackPrice_DHN = Heat_DHN['Price'].sum()
            ## ------- IND ----------- ##
            #GW(h) in ES -> MW(h) in DS - TO DO
            Heat_IND['c_op [M€/GWh]'] = Heat_IND['c_op [M€/GWh]']* 1000 #go from [M€/GWh] to [€/MWh] #price for the fuel
            #Get the HeatSlack Price : sum(ratio*(c_maint + c_op)) as full OPEX
            Heat_IND['Price'] = Heat_IND[0]*(Heat_IND['c_op [M€/GWh]'])
            HeatSlackPrice_IND = Heat_IND['Price'].sum()


        print('Heat',Heat_DEC,Heat_DHN,Heat_IND)
        print('HeatSlackPrice',HeatSlackPrice_DEC,HeatSlackPrice_DHN,HeatSlackPrice_IND)
        return [HeatSlackPrice_DEC,HeatSlackPrice_DHN,HeatSlackPrice_IND]

    else :
        # Get the total prod of all Boilers to then define ratios of production for each tech
        Heat_tot = Heat[0].sum()
        Heat[0] = Heat[0] / Heat_tot
        #treat the NaN => set to 0
        Heat.fillna(0,inplace=True)
        if c_maint :
            #GW(h) in ES -> MW(h) in DS - TO DO
            Heat['c_maint'] = Heat['c_maint']/3.6 #go from [M€/GW/y] to [€/MWh] #price of maintenance of the Tech
            Heat['c_op [M€/GWh]'] = Heat['c_op [M€/GWh]']* 1000 #go from [M€/GWh] to [€/MWh] #price for the fuel

            #Get the HeatSlack Price : sum(ratio*(c_maint + c_op)) as full OPEX
            Heat['Price'] = Heat[0]*(Heat['c_op [M€/GWh]']+Heat['c_maint'])
            HeatSlackPrice = Heat['Price'].sum()

        else :
            #GW(h) in ES -> MW(h) in DS - TO DO
            Heat['c_op [M€/GWh]'] = Heat['c_op [M€/GWh]']* 1000 #go from [M€/GWh] to [€/MWh] #price for the fuel

            #Get the HeatSlack Price : sum(ratio*(c_maint + c_op)) as full OPEX
            Heat['Price'] = Heat[0]*(Heat['c_op [M€/GWh]'])
            HeatSlackPrice = Heat['Price'].sum()

        print('HeatSlackPrice',HeatSlackPrice)
        return HeatSlackPrice




get_HeatSlackPrice('BE', n_TD,True,False)
########################################################################################################################

