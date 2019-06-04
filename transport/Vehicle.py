# -*- coding: utf-8 -*-
"""
Created on Tue Sep 12 09:31:35 2017

@author: ylb10119
"""
import numpy
#%%
class EV2:
     
    def __init__(self, StartTime, Distance, DistanceAfterRecharge, speed):
        self.StartTime = StartTime
        self.Distance = Distance
        self.DistanceAfterRecharge = DistanceAfterRecharge
        self.speed=speed
                       
    def compileDetails(self): #output exemplar details if required
        details=[self.StartTime, self.Distance, self.DistanceAfterRecharge]
        return details
    
    def drawSamples(self):
        mu_time, sigma_time = self.StartTime,0.5
        mu_distance, sigma_distance =self.Distance, 1 # the disatnce covariance needs to be assessed
        self.__sampleStartTime=float(numpy.random.normal(mu_time, sigma_time,1))
        if self.Distance>2: #this is to ensure we don't get negative distances
            self.__sampleDistance=float(numpy.random.normal(mu_distance, sigma_distance,1))
        elif self.Distance<2:
            self.__sampleDistance=self.Distance
        
        
        return self.__sampleDistance, self.__sampleStartTime
    
    def getDrawnSample(self):
        return self.__sampleStartTime, self.__sampleDistance
      
#%% Economic sub-class of EV
class Economic(EV2):
    
    
    def __init__(self, startTime, Distance, DistanceAfterRecharge,speed):
        EV2.__init__(self,startTime, Distance, DistanceAfterRecharge,speed)
        self.__sampleDistance=self.drawSamples()[0]
        self.__sampleStartTime=self.drawSamples()[1]
      
    
    def chargeProfile(self):   
        batterySize=14
        Range_km=(batterySize/0.35)*1.60394
        charge=(self.__sampleDistance/Range_km)*batterySize
        
        if charge>batterySize:
            charge=batterySize
        
        if self.DistanceAfterRecharge==0:
            chargeTime=charge/3.3 #3.3kw is normal charge mode
            chargeFinish=self.__sampleStartTime+chargeTime
            
            secondCharge=0 #this can be taken out - only in for testing
            secondChargeTime=0
            secondChargeFinish=0
            
        elif self.DistanceAfterRecharge!=0:
            chargeTime=charge/50 #50kW is fast charging mode
            chargeFinish=self.__sampleStartTime+chargeTime
            
            secondCharge=(self.DistanceAfterRecharge/Range_km)*batterySize #have to recharge again
            secondChargeTime=chargeFinish+((self.DistanceAfterRecharge/self.speed)/60)
            secondChargeFinish=secondChargeTime+(secondCharge/3.3)
        
        chargingProfile=[self.__sampleStartTime, chargeFinish, charge, secondChargeTime, \
                         secondChargeFinish, secondCharge]
        
        self.__chargingProfile=chargingProfile
        return chargingProfile
#%%  Midsize sub-class of EV   
class Midsize(EV2):
    
    
    def __init__(self, startTime, Distance, DistanceAfterRecharge, speed):
        EV2.__init__(self, startTime, Distance, DistanceAfterRecharge, speed)
        self.__sampleDistance=self.drawSamples()[0]
        self.__sampleStartTime=self.drawSamples()[1]
    
    def chargeProfile(self):
        batterySize=18
        Range_km=(batterySize/0.45)*1.60394
        charge=(self.__sampleDistance/Range_km)*batterySize
        
        if charge>batterySize:
            charge=batterySize
        
        if self.DistanceAfterRecharge==0:
            chargeTime=charge/3.3
            chargeFinish=self.__sampleStartTime+chargeTime
            secondCharge=0
            secondChargeTime=0
            secondChargeFinish=0
            
        elif self.DistanceAfterRecharge!=0:
            chargeTime=charge/50
            chargeFinish=self.__sampleStartTime+chargeTime
            secondCharge=(self.DistanceAfterRecharge/Range_km)*batterySize
            secondChargeTime=chargeFinish+((self.DistanceAfterRecharge/self.speed)/60)
            secondChargeFinish=secondChargeTime+(secondCharge/3.3)
        

            
        chargingProfile=[self.__sampleStartTime, chargeFinish, charge, secondChargeTime, \
                         secondChargeFinish, secondCharge] 
        
        return chargingProfile
