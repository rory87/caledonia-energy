import pandas as pd
import numpy as np
from scipy.interpolate import griddata

def formatWeather(pointOneTotal, pointTwoTotal, pointThreeTotal, pointFourTotal, latitude, longitude, lats, lons, alt,days,month):
    
    dS=pd.date_range(start='2015-04-01', end='2016-03-31', freq='H', columns=['Time'])
    dS1=pd.DataFrame(dS, columns=['Time'])
    pointOneTotal.index= dS1['Time'].iloc[0:8760]
    pointTwoTotal.index= dS1['Time'].iloc[0:8760]
    pointThreeTotal.index=dS1['Time'].iloc[0:8760]
    pointFourTotal.index=dS1['Time'].iloc[0:8760]

    if month == 1:
        pointOneProxy = pointOneTotal.loc['2016-01-01':'2016-01-31']
        pointTwoProxy = pointTwoTotal.loc['2016-01-01':'2016-01-31']
        pointThreeProxy = pointThreeTotal.loc['2016-01-01':'2016-01-31']
        pointFourProxy = pointFourTotal.loc['2016-01-01':'2016-01-31']
    elif month == 2:
        pointOneProxy = pointOneTotal.loc['2016-02-01':'2016-02-28']
        pointTwoProxy = pointTwoTotal.loc['2016-02-01':'2016-02-28']
        pointThreeProxy = pointThreeTotal.loc['2016-02-01':'2016-02-28']
        pointFourProxy = pointFourTotal.loc['2016-02-01':'2016-02-28']
    elif month == 3:
        pointOneProxy = pointOneTotal.loc['2016-03-01':'2016-03-31']
        pointTwoProxy = pointTwoTotal.loc['2016-03-01':'2016-03-31']
        pointThreeProxy = pointThreeTotal.loc['2016-03-01':'2016-03-31']
        pointFourProxy = pointFourTotal.loc['2016-03-01':'2016-03-31']
    elif month == 4:
        pointOneProxy = pointOneTotal.loc['2015-04-01':'2015-04-30']
        pointTwoProxy = pointTwoTotal.loc['2015-04-01':'2015-04-30']
        pointThreeProxy = pointThreeTotal.loc['2015-04-01':'2015-04-30']
        pointFourProxy = pointFourTotal.loc['2015-04-01':'2015-04-30']
    elif month == 5:
        pointOneProxy = pointOneTotal.loc['2015-05-01':'2015-05-31']
        pointTwoProxy = pointTwoTotal.loc['2015-05-01':'2015-05-31']
        pointThreeProxy = pointThreeTotal.loc['2015-05-01':'2015-05-31']
        pointFourProxy = pointFourTotal.loc['2015-05-01':'2015-05-31']
    elif month ==6:
        pointOneProxy = pointOneTotal.loc['2015-06-01':'2015-06-30']
        pointTwoProxy = pointTwoTotal.loc['2015-06-01':'2015-06-30']
        pointThreeProxy = pointThreeTotal.loc['2015-06-01':'2015-06-30']
        pointFourProxy = pointFourTotal.loc['2015-06-01':'2015-06-30']
    elif month == 7:
        pointOneProxy = pointOneTotal.loc['2015-07-01':'2015-07-31']
        pointTwoProxy = pointTwoTotal.loc['2015-07-01':'2015-07-31']
        pointThreeProxy = pointThreeTotal.loc['2015-07-01':'2015-07-31']
        pointFourProxy = pointFourTotal.loc['2015-07-01':'2015-07-31']
    elif month == 8:
        pointOneProxy = pointOneTotal.loc['2015-08-01':'2015-08-31']
        pointTwoProxy = pointTwoTotal.loc['2015-08-01':'2015-08-31']
        pointThreeProxy = pointThreeTotal.loc['2015-08-01':'2015-08-31']
        pointFourProxy = pointFourTotal.loc['2015-08-01':'2015-08-31']
    elif month == 9:
        pointOneProxy = pointOneTotal.loc['2015-09-01':'2015-09-30']
        pointTwoProxy = pointTwoTotal.loc['2015-09-01':'2015-09-30']
        pointThreeProxy = pointThreeTotal.loc['2015-09-01':'2015-09-30']
        pointFourProxy = pointFourTotal.loc['2015-09-01':'2015-09-30']
    elif month == 10:
        pointOneProxy = pointOneTotal.loc['2015-10-01':'2015-10-31']
        pointTwoProxy = pointTwoTotal.loc['2015-10-01':'2015-10-31']
        pointThreeProxy = pointThreeTotal.loc['2015-10-01':'2015-10-31']
        pointFourProxy = pointFourTotal.loc['2015-10-01':'2015-10-31']
    elif month == 11:
        pointOneProxy = pointOneTotal.loc['2015-11-01':'2015-11-30']
        pointTwoProxy = pointTwoTotal.loc['2015-11-01':'2015-11-30']
        pointThreeProxy = pointThreeTotal.loc['2015-11-01':'2015-11-30']
        pointFourProxy = pointFourTotal.loc['2015-11-01':'2015-11-30']
    elif month == 12:
        pointOneProxy = pointOneTotal.loc['2015-12-01':'2015-12-31']
        pointTwoProxy = pointTwoTotal.loc['2015-12-01':'2015-12-31']
        pointThreeProxy = pointThreeTotal.loc['2015-12-01':'2015-12-31']
        pointFourProxy = pointFourTotal.loc['2015-12-01':'2015-12-31']
    elif month==13:
        pointOneProxy = pointOneTotal
        pointTwoProxy = pointTwoTotal
        pointThreeProxy = pointThreeTotal
        pointFourProxy = pointFourTotal
        
    pointOne=pointOneProxy.as_matrix()  
    pointTwo=pointTwoProxy.as_matrix()
    pointThree=pointThreeProxy.as_matrix()
    pointFour=pointFourProxy.as_matrix()
    
    pointOne = pointOne[0:(24*days),0:]
    pointTwo = pointTwo[0:(24*days),0:]
    pointThree = pointThree[0:(24*days),0:]
    pointFour = pointFour[0:(24*days),0:]

    pointWeather = np.zeros([len(pointOne),9])
    for i in range(0,len(pointOne)):
        for k in range(1,10):
            weatherVars = list([pointOne[i,k], pointTwo[i,k], pointThree[i,k], pointFour[i,k]])
            pointWeather[i,(k-1)] = griddata((lats, lons), weatherVars, (latitude, longitude), method='linear')
    
    
    finalData = pd.DataFrame(pointWeather, columns=['DryBulb', 'Humidity','GHI','DNI', 'DHI', 'Infra', 'windS', 'windD','Pressure'] )
    finalData.index = pointOneProxy.index[0:(24*days)]
    
    altitude = griddata((lats, lons), alt, (latitude, longitude), method='linear')
    
    return finalData, altitude
