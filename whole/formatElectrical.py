#numpy and pandas imports
import numpy as np
import pandas as pd

#heat models/modules
from heat.models import GSP
from heat.views import processData
from heat.views import format_inputs
from heat.views import month

#electrical models/modules
from electrical.models import electricalGSP

#electricalHeat models/modules
from electricHeat.views import process_data_normal

def gspDemand(supplyPoint, m, d):
    electricalData = process_data_normal((electricalGSP.objects.filter(GSP = supplyPoint)), electricalGSP, 3)
    electricalData=electricalData[0:,2]/2
    dS=pd.date_range(start='2015-04-01', end='2016-04-01', freq='H')
    proData=pd.DataFrame({'Time':dS[0:8784], 'Data':electricalData})
    data=proData.set_index('Time')
    d1, d2, S = month(m, data)    
    elec=S['Data']
    elec=elec.iloc[0:(24*d)]

    return elec
