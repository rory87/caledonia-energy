#numpy and pandas imports
import numpy as np
import pandas as pd

#heat models/modules
from heat.models import GSP
from heat.models import industrialHeat
from heat.views import processData
from heat.views import format_inputs
from heat.views import month

#electricalHeat models/modules
from electricHeat.views import process_data_normal
from electricHeat.storageHeater import *

#generation models/modules
from generation.models import Weather
from generation.views import extract_weather
from generation.interpolateLatLon import *
from generation.formatWeather import *

#industrial models/modules
from industry.models import industrialBreakdown, industrialNumbers




def calculateIndustrialHeatPumpDemand(supplyPoint, d, m, temp,  manufacturingHP, commercialHP, entertainmentHP, educationHP, indicator):
    #heatData = industrialHeat.objects.filter(GSP = supplyPoint)
    heatData = industrialBreakdown.objects.filter(GSP = supplyPoint)

    vlqs = heatData.values_list()
    #r = np.core.records.fromrecords(vlqs, names=[f.name for f in industrialHeat._meta.fields])
    r = np.core.records.fromrecords(vlqs, names=[f.name for f in industrialBreakdown._meta.fields])
    l=np.array(r)
    process = np.zeros([len(l),6])
    
    for i in range(0,len(process)): # extract the information we need for inputs.
        change = l[i]
        for j in range(1,7):
            process[i,(j-1)] = change[j]

    g=np.array(process)

    dS=pd.date_range(start='2015-04-01', end='2016-04-01', freq='H')

    proData1=pd.DataFrame({'Time':dS[0:8784], 'Manufacturing':g[0:,2], 'Commercial':g[0:,3], 'Entertainment': g[0:,4], 'Education':g[0:,5]})
    data1=proData1.set_index('Time')
    d1, d2, S1 = month(m, data1)

    manufacturing=S1['Manufacturing']
    totalDemandManufacturing = manufacturing.iloc[0:(24*d)]

    commercial=S1['Commercial']
    totalDemandCommercial = commercial.iloc[0:(24*d)]

    entertainment=S1['Entertainment']
    totalDemandEntertainment = entertainment.iloc[0:(24*d)]

    education=S1['Education']
    totalDemandEducation = education.iloc[0:(24*d)]

    demandIndustrialHP=np.zeros(d*24)

    if indicator == 1:
        numbs=industrialNumbers.objects.filter(GSP = supplyPoint)
        interNumbs=np.core.records.fromrecords(numbs.values_list(), names=[f.name for f in industrialNumbers._meta.fields])
        totalNumbs=np.array(interNumbs)
        manufacturingHP = int(totalNumbs[0][2] * (manufacturingHP/100))
        commercialHP = int(totalNumbs[0][3] * (commercialHP/100))
        entertainmentHP = int(totalNumbs[0][4] * (entertainmentHP/100))
        educationHP = int(totalNumbs[0][5] * (educationHP/100))
       

    for i in range(1, (d+1)):
                    demMan=(totalDemandManufacturing.iloc[((24*i)-24):(24*i)].as_matrix())*manufacturingHP
                    demCom=(totalDemandCommercial.iloc[((24*i)-24):(24*i)].as_matrix())*commercialHP
                    demEnt=(totalDemandEntertainment.iloc[((24*i)-24):(24*i)].as_matrix())*entertainmentHP
                    demEdu=(totalDemandEducation.iloc[((24*i)-24):(24*i)].as_matrix())*educationHP
                    tempB=temp.iloc[((24*i)-24):(24*i)].as_matrix()
                    demIndustrialB=np.zeros(24)
                    for j in range(0,24):
                            demIndustrialB[j] = (demMan[j] / (tempB[j]*0.04762+3.03283)) + (demCom[j] / (tempB[j]*0.04762+3.03283)) + (demEnt[j] / (tempB[j]*0.04762+3.03283)) + (demEdu[j] / (tempB[j]*0.04762+3.03283))
                    demandIndustrialHP[((24*i)-24):(24*i)]=demIndustrialB
    
    
    totalHeatPumpIndustrial = demandIndustrialHP

    return totalHeatPumpIndustrial
