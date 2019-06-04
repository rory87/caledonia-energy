import pvlib
import pandas as pd

def pvPowerOut(tmy_data, latitude, longitude, altitude, pRating):
    
    tmy_data = tmy_data.shift(freq='-30Min')
    
    # First define some PV system parameters
    surface_tilt = 30
    surface_azimuth = 180 # pvlib uses 0=North, 90=East, 180=South, 270=West convention
    albedo = 0.2
    
    exLoc = pvlib.location.Location(latitude, longitude, tz='GMT', altitude=altitude,
                                    )
                                         
    
    # SOLAR POSITION
    # Calculate the solar position for all times in the TMY file
    solpos = pvlib.solarposition.get_solarposition(tmy_data.index, exLoc.latitude, exLoc.longitude)
    
    
    #DNI ET 
    #calculate extra terrestrial radiation - this is needed for many plane of array diffuse irradiance models
    
    # the extraradiation function returns a simple numpy array
    # instead of a nice pandas series. We will change this
    # in a future version
    dni_extra = pvlib.irradiance.extraradiation(tmy_data.index)
    dni_extra = pd.Series(dni_extra, index=tmy_data.index)
    

    
    #Airmass
    
    airmass = pvlib.atmosphere.relativeairmass(solpos['apparent_zenith'])

    
    #POA Sky diffuse
    
    poa_sky_diffuse = pvlib.irradiance.haydavies(surface_tilt, surface_azimuth,
                                                 tmy_data['DHI'], tmy_data['DNI'], dni_extra,
                                                 solpos['apparent_zenith'], solpos['azimuth'])
    

    
    #POA ground diffuse
    
    poa_ground_diffuse = pvlib.irradiance.grounddiffuse(surface_tilt, tmy_data['GHI'], albedo=albedo)

    
    #Calculate AOI
    
    aoi = pvlib.irradiance.aoi(surface_tilt, surface_azimuth, solpos['apparent_zenith'], solpos['azimuth'])

    
    #POA total
    
    poa_irrad = pvlib.irradiance.total_irrad(surface_tilt, surface_azimuth, solpos['apparent_zenith'], 
                                             solpos['azimuth'],tmy_data['DNI'], 
                                             tmy_data['GHI'],tmy_data['DHI'])

    
    #cell and module temperature
    pvtemps = pvlib.pvsystem.sapm_celltemp(poa_irrad['poa_global'], tmy_data['windS'], tmy_data['DryBulb'])
    
    
    #DC power using SAPM
    sandia_modules = pvlib.pvsystem.retrieve_sam(name='SandiaMod') # This opens up a database called sandia_modules
    sandia_module = sandia_modules.Canadian_Solar_CS5P_220M___2009_ # This selects a particular module from the database
    
    #calculate the effective irradiance
    effective_irradiance = pvlib.pvsystem.sapm_effective_irradiance(poa_irrad.poa_direct, poa_irrad.poa_diffuse, airmass, aoi, sandia_module)
    
    #Run the SAPM using the parameters calculated above
    sapm_out = pvlib.pvsystem.sapm(effective_irradiance, pvtemps.temp_cell, sandia_module)

    
    ##Calculate dc output according to power rating & number of parallel strings
    stringNum = int(pRating/(sandia_module.Impo*sandia_module.Vmpo))+1
    dcOutput=stringNum*sapm_out['p_mp']
    
    #AC Power using SAPM
    sapm_inverters = pvlib.pvsystem.retrieve_sam('sandiainverter') # Again, this opens up a database
    
    
    #Find a suitable rated inverter
    invP=sapm_inverters.loc['Paco']-pRating
    invPNew=invP.where(invP>=0)
    inverterName=invPNew.idxmin()
    sapm_inverter = sapm_inverters[inverterName]
    
    p_acs = pd.DataFrame()
    p_acs['sapm'] = pvlib.pvsystem.snlinverter(sapm_out.v_mp, dcOutput, sapm_inverter)
    
    return p_acs

