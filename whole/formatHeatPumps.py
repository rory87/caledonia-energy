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

#generation models/modules
from generation.models import Weather
from generation.views import extract_weather
from generation.interpolateLatLon import *
from generation.formatWeather import *

# whole models/modules
from whole.models import gspStats


def calculateHeatPumpDemand(supplyPoint, tmy_data, d, m, smallHP, mediumHP, largeHP):
    h40HP = smallHP/2
    h60HP = smallHP/2
    h100HP = mediumHP/2
    h140HP = mediumHP/2
    h160HP =largeHP

    if isinstance(h40HP, float):
        h40HP = h40HP + 0.5
        h60HP = h60HP - 0.5

    if isinstance(h100HP, float):
        h100HP = h100HP + 0.5
        h140HP = h140HP - 0.5
    
    numSmallHP=h40HP+h60HP
    numMediumHP=h100HP+h140HP
    numLargeHP=h160HP

    
    #change data type
    rawData = processData(supplyPoint)
    hourSmallHP, totalDemandSmallHP = format_inputs(rawData, h40HP, h60HP, 0, 0, 0)
    hourMediumHP, totalDemandMediumHP = format_inputs(rawData, 0, 0, h100HP, h140HP, 0)
    hourLargeHP, totalDemandLargeHP = format_inputs(rawData, 0, 0, 0, 0, h160HP)

##    latitude=statHP[0,2]
##    longitude=statHP[0,3]
##    tmy_data, altitude = extract_weather(d,m, latitude, longitude)
    temp=tmy_data['DryBulb']

    # add time element to data
    dS=pd.date_range(start='2015-04-01', end='2016-04-01', freq='H')

    ##Small Houses with Heat Pumps
    proDataSmallHP=pd.DataFrame({'Time':dS[0:8784], 'Data':(totalDemandSmallHP/1000)})
    dataSmallHP=proDataSmallHP.set_index('Time')
    d1, d2, smallSHP = month(m, dataSmallHP)
    reSmallHP = pd.DataFrame(smallSHP['Data'], index=smallSHP.index)
    reSmallHP.columns=['Demand']
    finalDataSmallHP = reSmallHP.iloc[0:(24*d)]
    indSmallHP= finalDataSmallHP/numSmallHP
    demandSmallHP=np.zeros(d*24)


    if numSmallHP !=0:
            for i in range(1, (d+1)):
                    demB=indSmallHP.iloc[((24*i)-24):(24*i)].as_matrix()
                    tempB=temp.iloc[((24*i)-24):(24*i)].as_matrix()
                    demSmallB=np.zeros(24)
                    for j in range(0,24):
                        demSmallB[j] = demB[j] / (tempB[j]*0.04762+3.03283)
                    demandSmallHP[((24*i)-24):(24*i)]=demSmallB
            smallHPTotal = demandSmallHP * numSmallHP
    else:
            smallHPTotal = np.zeros(d*24)

    ##Medium houses with heat pumps
    proDataMediumHP=pd.DataFrame({'Time':dS[0:8784], 'Data':(totalDemandMediumHP/1000)})
    dataMediumHP=proDataMediumHP.set_index('Time')
    d1, d2, mediumSHP = month(m, dataMediumHP)
    reMediumHP = pd.DataFrame(mediumSHP['Data'], index=mediumSHP.index)
    reMediumHP.columns=['Demand']
    finalDataMediumHP = reMediumHP.iloc[0:(24*d)]
    indMediumHP= finalDataMediumHP/numMediumHP
    demandMediumHP=np.zeros(d*24)


    if numMediumHP !=0:
            for i in range(1, (d+1)):
                    demB=indMediumHP.iloc[((24*i)-24):(24*i)].as_matrix()
                    tempB=temp.iloc[((24*i)-24):(24*i)].as_matrix()
                    demMediumB=np.zeros(24)
                    for j in range(0,24):
                        demMediumB[j] = demB[j] / (tempB[j]*0.04762+3.03283)
                    demandMediumHP[((24*i)-24):(24*i)]=demMediumB
            mediumHPTotal = demandMediumHP * numMediumHP
    else:
            mediumHPTotal = np.zeros(d*24)

    ##Large houses with heat pumps    
    proDataLargeHP=pd.DataFrame({'Time':dS[0:8784], 'Data':(totalDemandLargeHP/1000)})
    dataLargeHP=proDataLargeHP.set_index('Time')
    d1, d2, largeSHP = month(m, dataLargeHP)
    reLargeHP = pd.DataFrame(largeSHP['Data'], index=largeSHP.index)
    reLargeHP.columns=['Demand']
    finalDataLargeHP = reLargeHP.iloc[0:(24*d)]
    indLargeHP= finalDataLargeHP/numLargeHP
    demandLargeHP=np.zeros(d*24)

    
    if numLargeHP !=0:
            for i in range(1, (d+1)):
                    demB=indLargeHP.iloc[((24*i)-24):(24*i)].as_matrix()
                    tempB=temp.iloc[((24*i)-24):(24*i)].as_matrix()
                    demLargeB=np.zeros(24)
                    for j in range(0,24):
                        demLargeB[j] = demB[j] / (tempB[j]*0.04762+3.03283)
                    demandLargeHP[((24*i)-24):(24*i)]=demLargeB
            largeHPTotal = demandLargeHP * numLargeHP
    else:
            largeHPTotal = np.zeros(d*24)


    totHPCharge = (smallHPTotal[0:]/1000) + (mediumHPTotal[0:]/1000) + (largeHPTotal[0:]/1000)

    return totHPCharge

