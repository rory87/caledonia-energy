#numpy and pandas imports
import numpy as np
import pandas as pd

#transport models/modules
from transport . models import Journey
from transport . models import gspLocalAuthority
from transport . transportFunctions import *
from transport . RunTransportModel import *
from transport . Vehicle import *
from transport . views import process_data

#heat models/modules
from heat.models import GSP
from heat.views import processData
from heat.views import format_inputs
from heat.views import month

def calculateEVCharge(supplyPoint,d,evNumbers,area): # area is either 'Urban' or 'Rural'

    if evNumbers > 100:
        evNumbersNew = 100
    else:
        evNumbersNew = evNumbers

    multiplyFactor = evNumbers/evNumbersNew

    gspNameProxy=GSP.objects.get(idx=supplyPoint)
    gspName=GSP.objects.filter(idx=supplyPoint)
    na0 = ([p.name for p in gspName])
    gspAuthority=gspLocalAuthority.objects.filter(gsp=na0[0])
    na1 = ([p.localAuthority for p in gspAuthority])

    if area == 'Urban' and evNumbersNew > 1:
        smallEV=int(evNumbersNew*0.5)
        mediumEV=int(evNumbersNew*0.5)
    elif area == 'Urban' and evNumbersNew == 1:
        smallEV = 1
        mediumEV = 0
    elif area == 'Rural' and evNumbersNew> 1:
        smallEV=int(evNumbersNew*0.1)
        mediumEV=int(evNumbersNew*0.9)
    elif area == 'Rural' and evNumbersNew == 1:
        smallEV = 0
        mediumEV = 1        
    
    chargeDataSmall = process_data((Journey.objects.filter(localAuthority=na1[0], Area=area, typeEV='Economy')), Journey,7)
    chargeDataMedium = process_data((Journey.objects.filter(localAuthority=na1[0], Area=area, typeEV='Midsize')), Journey, 7)

    chargeDataSmall = chargeDataSmall[0:,0:4]
    chargeDataMedium = chargeDataMedium[0:,0:4]

    profileSmall=formatChargeDemand(smallEV, chargeDataSmall, 'Economy',d)
    profileMedium=formatChargeDemand(mediumEV, chargeDataMedium, 'Midsize',d)

    profileTotal = np.zeros([len(profileSmall),1])
    profileTotal[0:,0]=(profileSmall['Charge'].as_matrix() + profileMedium['Charge'].as_matrix())*multiplyFactor

    return profileTotal

    
