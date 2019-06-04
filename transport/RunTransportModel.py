# -*- coding: utf-8 -*-
"""
Created on Tue Sep  5 10:07:55 2017

@author: ylb10119
"""

import numpy
import pandas
from transport.transportFunctions import compileJourneys
from transport.transportFunctions import inputData
from transport.Vehicle import Economic
from transport.Vehicle import Midsize
import matplotlib.pyplot as plt



#%%
def collectEVSamples(vehicleNums, exemplarData, vehicleType):
      
       completeJourneys=numpy.zeros([vehicleNums,6])
       samples=int(vehicleNums/len(exemplarData))
       Journeys=numpy.zeros([len(exemplarData),6])

       
       for j in range(1,samples+1):
            for i in range(0, len(exemplarData)):
               if vehicleType is 'Economy': 
                   journey=Economic(exemplarData[i,0], exemplarData[i,1], exemplarData[i,2],exemplarData[i,3])
                   Journeys[i,0:]=journey.chargeProfile()
               elif vehicleType is 'Midsize':
                   journey=Midsize(exemplarData[i,0], exemplarData[i,1], exemplarData[i,2],exemplarData[i,3])
                   Journeys[i,0:]=journey.chargeProfile()
            completeJourneys[len(exemplarData)*(j-1):len(exemplarData)*j,0:]=Journeys
               
       
       remainder=vehicleNums-(samples*len(exemplarData))
       leftoverJourneys=numpy.zeros([remainder,6])
      
      
       for i in range(0,remainder):
           if vehicleType is 'Economy':
               remJourney=Economic(exemplarData[i,0], exemplarData[i,1], exemplarData[i,2],exemplarData[i,3])
               leftoverJourneys[i,0:]=remJourney.chargeProfile()
           elif vehicleType is 'Midsize':
               remJourney=Midsize(exemplarData[i,0], exemplarData[i,1], exemplarData[i,2],exemplarData[i,3])
               leftoverJourneys[i,0:]=remJourney.chargeProfile()
       completeJourneys[vehicleNums-remainder:vehicleNums,0:]=leftoverJourneys
          
        
       return completeJourneys
#%%

def formatEVSamples(completeJourneys):
    
    mat=numpy.zeros([0,2])
    
    for i in range(0,len(completeJourneys-1)):  
        jour=compileJourneys(completeJourneys[i,0:])
        jour.extractDetails()
        jour.formatJourney()
        data=jour.getSpecificJourney()
        mat=numpy.append(mat,data,axis=0)
            
    return mat
    

def checkHours(mat):
    for i in range (0,len(mat-1)):
        if mat[i,0]>=24:
            mat[i,0]=mat[i,0]-24
    
    return mat


def formatChargeDemand(vehicleNums, exemplarData, vehicleType,noOfDays):
    
    completeDemand=[0,0]
    
    for i in range(0,noOfDays+1):
        samples=collectEVSamples(vehicleNums, exemplarData, vehicleType)
        journeys=formatEVSamples(samples)
        journeysChange=checkHours(journeys)
        changeToHour=pandas.DataFrame(journeysChange,columns=['Hour','Charge'])
        changeToHour=changeToHour.groupby('Hour').sum()
        realTime=numpy.array(range(0,24))
        l=changeToHour.index.tolist()
        new=numpy.zeros([24,2])
        power=numpy.array(changeToHour)
        for j in range(0,24):
            compare=realTime[j] in l
            if compare==True:
                index=l.index(realTime[j])
                new[j,0]=realTime[j]
                new[j,1]=power[index]
            elif compare==False:
                new[j,0]=realTime[j]
                new[j,1]=0
        final=pandas.DataFrame(new,columns=['Hour','Charge'])                                       
        if i==1:
            completeDemand=final
        elif i!=1:
            completeDemand=completeDemand.append(final)
        
    
    return completeDemand
    
 


