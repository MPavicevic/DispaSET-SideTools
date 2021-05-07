# -*- coding: utf-8 -*-
"""
Created on Thu Mar 18 17:27:03 2021

@author: Matijs
"""


import pickle
import sys,os
sys.path.append(os.path.abspath(r'../..')) 

import numpy as np
import pandas as pd

#Input files
location='C:/Users/student/Desktop/Data_Matijs/TotalLoadValue/'
DH_dem=pd.read_csv('C:/Users/student/Desktop/Data_Matijs/HeatDemand_DistrictH/HeatDemand_DH.csv',index_col=0)
heatdem_el=pd.read_excel('C:/Users/student/Desktop/Data_Matijs/HeatDemandTotal/E_demandP2HT.xlsx',index_col=0)
heatdem_tot=pd.read_excel('C:/Users/student/Desktop/Data_Matijs/HeatDemandTotal/HeatDemandTotal.xlsx',index_col=0)

#convert to Mwh
heatdem_tot=heatdem_tot*1000000

countries= list(DH_dem.columns)
scaled_DH=DH_dem.copy()
heatdem_tot_profiles=pd.DataFrame()
heatdem_el_profiles=pd.DataFrame()
#Make DH demand profiles non-dimensional and multiply by total demands (of heating and P2HT units)
for c in countries:
    x=DH_dem[c].sum()
    scaled_DH[c]=DH_dem[c]/x
    heatdem_el_profiles[c]=scaled_DH[c]*heatdem_el.loc[c,'Total_El_demand']
    heatdem_tot_profiles[c]=scaled_DH[c]*heatdem_tot.loc[c,'Total heating demand']

#substract electricity dem from P2HT units from total load    
total_load=pd.DataFrame()   
for c in countries:
    tmp_load=pd.read_csv(location+c+'/2019.csv', usecols=[1])
    total_load.loc[:,c]=tmp_load.iloc[:,0]
total_load.index=DH_dem.index  
total_sub=pd.DataFrame()
total_sub=total_load-heatdem_el_profiles

    
#to csv
#heatdem_tot_profiles.to_csv('C:/Users/student/Desktop/Data2019/HeatDemand/HeatDemand_TOTAL.csv')
#for c in countries:
    #tmp_l=pd.DataFrame()
    #tmp_l=total_sub.loc[:,c]    
    #tmp_l.to_csv('C:/Users/student/Desktop/Data2019/TotalLoadValue_def/'+c+'/2019.csv')



    