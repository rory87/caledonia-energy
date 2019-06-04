# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import numpy

def inputData(file):
    data=numpy.loadtxt(open(file,'rb'), delimiter=',', skiprows=1)
    return data

    
#%%  

class compileJourneys:

    def __init__(self,journey):
        self.journey=numpy.transpose(journey)            
    
    
    def extractDetails(self):     
        self.__specificJourney=numpy.zeros([20,2])
        self.__sampleJourney=self.journey
        self.__sampleJourney=self.__sampleJourney[self.__sampleJourney!=0]
        self.__timeBegin=int(self.__sampleJourney[0])+1
        self.__timeEnd=int(self.__sampleJourney[1])+1
        
        if len(self.__sampleJourney)==6:
            self.__secondTimeBegin=int(self.__sampleJourney[3])+1
            self.__secondTimeEnd=int(self.__sampleJourney[4])+1
            self.__secondTotalTime=self.__sampleJourney[4]-self.__sampleJourney[3]
                   
      
    def formatJourney(self):
        
        if self.__timeBegin==self.__timeEnd:
            self.__specificJourney[0,0]=self.__timeBegin
            self.__specificJourney[0,1]=self.__sampleJourney[2]
        elif self.__timeBegin!=self.__timeEnd:
            self.__specificJourney[0,0]=self.__timeBegin
            self.__specificJourney[(self.__timeEnd-self.__timeBegin),0]=self.__timeEnd    
            self.__specificJourney[0:(self.__timeEnd-self.__timeBegin)+1,0]=numpy.transpose(list(range(self.__timeBegin,self.__timeEnd+1)))
      
            self.__totalTime=self.__sampleJourney[1]-self.__sampleJourney[0]
         
            self.__specificJourney[0,1]=((self.__specificJourney[0,0]-self.__sampleJourney[0])/self.__totalTime)*self.__sampleJourney[2]
      
            self.__specificJourney[len(range(self.__timeBegin, self.__timeEnd)),1]=((self.__sampleJourney[1] - (self.__timeEnd-1))/self.__totalTime)*self.__sampleJourney[2]
                  
            self.__specificJourney[1:len(range(self.__timeBegin, self.__timeEnd)),1]=(1/self.__totalTime)*self.__sampleJourney[2]
      
                                 
                        
        if len(self.__sampleJourney)==6:
            if self.__timeBegin==self.__timeEnd:
                self.__specificJourney[1:1+len(range(self.__secondTimeBegin, self.__secondTimeEnd))+1,0]=numpy.transpose(list(range(self.__secondTimeBegin,self.__secondTimeEnd+1)))
                self.__specificJourney[1,1]=((self.__secondTimeBegin-self.__sampleJourney[3])/self.__secondTotalTime)*self.__sampleJourney[5]
                self.__specificJourney[1+len(range(self.__secondTimeBegin, self.__secondTimeEnd)),1]=((self.__sampleJourney[4]-(self.__secondTimeEnd-1))/self.__secondTotalTime)*self.__sampleJourney[5]
                self.__specificJourney[2:1+len(range(self.__secondTimeBegin, self.__secondTimeEnd)),1]=(1/self.__secondTotalTime)*self.__sampleJourney[5]
                
            elif self.__timeBegin!=self.__timeEnd:
                self.__specificJourney[len(range(self.__timeBegin, self.__timeEnd))+1:len(range(self.__timeBegin, self.__timeEnd))+1+len(range(self.__secondTimeBegin, self.__secondTimeEnd))+1,0]=numpy.transpose(list(range(self.__secondTimeBegin,self.__secondTimeEnd+1)))
                self.__specificJourney[len(range(self.__timeBegin, self.__timeEnd))+1,1]=((self.__secondTimeBegin-self.__sampleJourney[3])/self.__secondTotalTime)*self.__sampleJourney[5]
                self.__specificJourney[len(range(self.__timeBegin, self.__timeEnd))+1+len(range(self.__secondTimeBegin, self.__secondTimeEnd)),1]=((self.__sampleJourney[4]-(self.__secondTimeEnd-1))/self.__secondTotalTime)*self.__sampleJourney[5]
                self.__specificJourney[len(range(self.__timeBegin, self.__timeEnd))+2:len(range(self.__timeBegin, self.__timeEnd))+1+len(range(self.__secondTimeBegin, self.__secondTimeEnd)),1]=(1/self.__secondTotalTime)*self.__sampleJourney[5]

        self.__specificJourney=self.__specificJourney[numpy.all(self.__specificJourney!=0, axis=1)]
                
    def getSpecificJourney(self):
        return(self.__specificJourney)

    def getSampleJourney(self):
        return(self.__sampleJourney)



