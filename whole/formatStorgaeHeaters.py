#numpy and pandas imports
import numpy as np
import pandas as pd

#heat models/modules
from heat.models import GSP
from heat.views import processData
from heat.views import format_inputs
from heat.views import month

#electricalHeat models/modules
from electricHeat.views import process_data_normal
from electricHeat.storageHeater import *

def calculateStorageHeaterDemand(supplyPoint, d, m, small, medium, large):
    h40 = small/2
    h60 = small/2
    h100 = medium/2
    h140 = medium/2
    h160 = large

    if isinstance(h40, float):
        h40 = h40 + 0.5
        h60 = h60 - 0.5

    if isinstance(h100, float):
        h100 = h100 + 0.5
        h140 = h140 - 0.5        
        
    numSmall=h40+h60
    numMedium=h100+h140
    numLarge=h160

    rawData = processData(supplyPoint)
    hourSmall, totalDemandSmall = format_inputs(rawData, h40, h60, 0, 0, 0) # output in Watts
    hourMedium, totalDemandMedium = format_inputs(rawData, 0, 0, h100, h140, 0)
    hourLarge, totalDemandLarge = format_inputs(rawData, 0, 0, 0, 0, h160)


    # add time element to data
    dS=pd.date_range(start='2015-04-01', end='2016-04-01', freq='H')

    ##small sized property##

    proDataSmall=pd.DataFrame({'Time':dS[0:8784], 'Data':(totalDemandSmall/1000)})
    dataSmall=proDataSmall.set_index('Time')
    d1, d2, smallS = month(m, dataSmall)
    reSmall = pd.DataFrame(smallS['Data'], index=smallS.index)
    reSmall.columns=['Demand']
    finalDataSmall = reSmall.iloc[0:(24*d)]
    chargeSmall=np.zeros(d*24)
    indSmall= finalDataSmall/numSmall

    if numSmall != 0:
        for i in range(1, (d+1)):
            intraSmall= pd.DataFrame(indSmall.iloc[((24*i)-24):(24*i),0].as_matrix(), index=list(range(0, 24)), columns=['Demand'])
            if i==1:
                chg, chT, gone= storageHeater(intraSmall,  'Small', (19.3*0.2))
                chargeSmall[((24*i)-24):(24*i)] = chT.iloc[0:,0].as_matrix()
            else:
                chg, chT, gone= storageHeater(intraSmall,  'Small', (19.3*gone[0]) )
                chargeSmall[((24*i)-24):(24*i)] = chT.iloc[0:,0].as_matrix()
        smallChargeTotal = chargeSmall*numSmall
    else:
        smallChargeTotal = np.zeros(d*24)

    ##medium sized property##

    proDataMedium=pd.DataFrame({'Time':dS[0:8784], 'Data':(totalDemandMedium/1000)})
    dataMedium=proDataMedium.set_index('Time')
    d1, d2, mediumS = month(m, dataMedium)
    reMedium = pd.DataFrame(mediumS['Data'], index=mediumS.index)
    reMedium.columns=['Demand']
    finalDataMedium = reMedium.iloc[0:(24*d)]
    chargeMedium=np.zeros(d*24)
    indMedium= finalDataMedium/numMedium

    if numMedium != 0:
        for i in range(1, (d+1)):
            intraMedium= pd.DataFrame(indMedium.iloc[((24*i)-24):(24*i),0].as_matrix(), index=list(range(0, 24)), columns=['Demand'])
            if i==1:
                chg, chT, gone= storageHeater(intraMedium,  'Medium', (19.3*0.2))
                chargeMedium[((24*i)-24):(24*i)] = chT.iloc[0:,0].as_matrix()
            else:
                chg, chT, gone= storageHeater(intraMedium,  'Medium', (19.3*gone[0]) )
                chargeMedium[((24*i)-24):(24*i)] = chT.iloc[0:,0].as_matrix()    

        mediumChargeTotal = chargeMedium*numMedium
    else:
        mediumChargeTotal = np.zeros(d*24)
    
        

    ##Large sized property##
    proDataLarge=pd.DataFrame({'Time':dS[0:8784], 'Data':(totalDemandLarge/1000)})
    dataLarge=proDataLarge.set_index('Time')
    d1, d2, largeS = month(m, dataLarge)
    reLarge = pd.DataFrame(largeS['Data'], index=largeS.index)
    reLarge.columns=['Demand']
    finalDataLarge = reLarge.iloc[0:(24*d)]
    chargeLarge=np.zeros(d*24)
    indLarge= finalDataLarge/numLarge

    if numLarge != 0:
        for i in range(1, (d+1)):
            intraLarge= pd.DataFrame(indLarge.iloc[((24*i)-24):(24*i),0].as_matrix(), index=list(range(0, 24)), columns=['Demand'])
            if i==1:
                chg, chT, gone= storageHeater(intraLarge,  'Large', (23.1*0.2))
                chargeLarge[((24*i)-24):(24*i)] = chT.iloc[0:,0].as_matrix()
            else:
                chg, chT, gone= storageHeater(intraLarge,  'Large', (23.1*gone[0]) )
                chargeLarge[((24*i)-24):(24*i)] = chT.iloc[0:,0].as_matrix()   
        
        largeChargeTotal = chargeLarge*numLarge
    else:
        largeChargeTotal = np.zeros(d*24)

    totCharge = (smallChargeTotal[0:]/1000) + (mediumChargeTotal[0:]/1000) + (largeChargeTotal[0:]/1000)

    return totCharge

