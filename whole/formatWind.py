#numpy and pandas imports
import numpy as np
import pandas as pd
from generation.models import Turbines
from generation.views import process_data

def calculateWindOutput(tmy_data, turbineRating):
    if turbineRating > 3000:
        turbineRating = 3000
    
    t=Turbines.objects.all()
    turbineData = process_data(t, Turbines,10)
    turbineData.columns=['manufacturer', 'rating', 'cutIn', 'ratedSpeed', 'cutOut', 'p1','p2','p3','p4','p5']

    ##Find closest turbine
    x=turbineData['rating']- turbineRating
    y=x.where(x>=0).dropna().astype(float)
    closestList=y.where(y == y[y.idxmin()]).dropna()
    turbine=turbineData.iloc[closestList.sample(n=1).index[0]]

    #Extract Wind Data
    windSpeed = tmy_data['windS']

    #Calculate wind wpeed
    p_acs = np.zeros(len(windSpeed))
                     
    for i in range(0, len(windSpeed)):
        if (windSpeed.iloc[i] < turbine['cutIn']) or (windSpeed.iloc[i] > turbine['cutOut']):
            p_acs[i] = 0
        elif (windSpeed.iloc[i] > turbine['ratedSpeed']) and (windSpeed.iloc[i] < turbine['cutOut']):
            p_acs[i] = turbine['ratedSpeed']
        else:
            p_acs[i] = (turbine['p1']*windSpeed.iloc[i]**4) + (turbine['p2']*windSpeed.iloc[i]**3) + (turbine['p3']*windSpeed.iloc[i]**2) + (turbine['p4']*windSpeed.iloc[i]) + turbine['p5']

    for i in range(0, len(p_acs)):
        if p_acs[i] > turbineRating:
            p_acs[i] = turbineRating

    return p_acs
