import pandas as pd
import numpy as np
from scipy.interpolate import griddata

def interpolateLatLon(latitude, longitude, latLon):
    diffLatitude=latLon.iloc[0:,1]-latitude
    diffLongitude=latLon.iloc[0:,2]-longitude
    
    latUp=diffLatitude.where(diffLatitude>=0).dropna().astype(float)
    latDown=diffLatitude.where(diffLatitude<=0).dropna().astype(float)
    
    lonUp=diffLongitude.where(diffLongitude>=0).dropna().astype(float)
    lonDown=diffLongitude.where(diffLongitude<=0).dropna().astype(float)

    
    latUpActual = latUp.where(latUp == latUp[latUp.idxmin()]).dropna()
    latDownActual = latDown.where(latDown == latDown[latDown.idxmax()]).dropna()
    
    lonUpActual = lonUp.where(lonUp == lonUp[lonUp.idxmin()]).dropna()
    lonDownActual = lonDown.where(lonDown == lonDown[lonDown.idxmax()]).dropna()
    
    
    idxLatUp=latUpActual.index
    idxLatDown=latDownActual.index
    idxLonUp=lonUpActual.index
    idxLonDown=lonDownActual.index
    
    idx1 = idxLatDown.intersection(idxLonDown)
    idx2 = idxLatDown.intersection(idxLonUp)
    idx3 = idxLatUp.intersection(idxLonDown)
    idx4 = idxLatUp.intersection(idxLonUp)
    
    lats=list([  latLon.iloc[idx1[0],1],   latLon.iloc[idx2[0],1], latLon.iloc[idx3[0],1], latLon.iloc[idx4[0],1] ])
    lons=list([  latLon.iloc[idx1[0],2],   latLon.iloc[idx2[0],2], latLon.iloc[idx3[0],2], latLon.iloc[idx4[0],2] ])
    
    num=list([  int(latLon.iloc[idx1[0],0]),   int(latLon.iloc[idx2[0],0]), int(latLon.iloc[idx3[0],0]), int(latLon.iloc[idx4[0],0]) ])
    alt=list([  latLon.iloc[idx1[0],3],   latLon.iloc[idx2[0],3], latLon.iloc[idx3[0],3], latLon.iloc[idx4[0],3] ])

    return num, lats, lons, alt
