from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse
from django.views.generic.list import ListView
import csv
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm

#numpy and pandas imports
import numpy as np
import pandas as pd

#matplot imports
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import pylab
from pylab import *
import PIL, PIL.Image
from io import BytesIO
import matplotlib.pyplot as plt
matplotlib.use('Agg')
from matplotlib.dates import (YEARLY, MONTHLY, DAILY, DateFormatter,rrulewrapper, RRuleLocator, drange)
import datetime
import base64

##########################################################
#model/view imports

#transport models/modules
from transport.models import Journey
from transport.models import gspLocalAuthority
from transport.transportFunctions import *
from transport.RunTransportModel import *
from transport.Vehicle import *
from transport.views import process_data

#heat models/modules
from heat.models import GSP
from heat.views import processData
from heat.views import format_inputs
from heat.views import month

#electrical models/modules
from electrical.models import electricalGSP

#electricalHeat models/modules
from electricHeat.views import process_data_normal
from electricHeat.storageHeater import *

#generation models/modules
from generation.models import Weather
from generation.views import extract_weather
from generation.interpolateLatLon import *
from generation.formatWeather import *
from generation.pvPowerOut import *

#energy storage models/modules
from energyStorage.esBalance import *
from energyStorage.esRenewable import *
from energyStorage.runOptimizer import *

# whole models/modules
from whole.models import gspStats
from whole.formatEV import *
from whole.formatElectrical import *
from whole.formatHeatPumps import *
from whole.formatStorgaeHeaters import *
from whole.formatIndustrialHeatPump import *
from whole.formatWind import *

##########################################################
# Create your views here.

@login_required(login_url='/login/')
def whole_input_form(request):
    return render(request, 'whole/whole_input_form.html')

def whole_input_form_num(request):
    return render(request, 'whole/whole_input_form_num.html')


#############################


def whole_plot(request):
    ################GET REQUESTS############################################
    
    #Generic GET Requests
    supplyPoint=request.GET['supplyPoint']
    m = int(request.GET['month'])
    #EV GET Requests
    urbanEV = int(request.GET['urbanEV'])
    ruralEV = int(request.GET['ruralEV'])
    #Heat Pump GET Requests
    smallHP = int(request.GET['smallHP'])
    mediumHP = int(request.GET['mediumHP'])
    largeHP = int(request.GET['largeHP'])
    #Storage Heater GET Requests
    smallSH = int(request.GET['smallSH'])
    mediumSH = int(request.GET['mediumSH'])
    largeSH = int(request.GET['largeSH'])
    #Industrial Heat Pump GET Requests
    manufacturingHP = int(request.GET['manufacturingHP'])
    commercialHP = int(request.GET['commercialHP'])
    entertainmentHP = int(request.GET['entertainmentHP'])
    educationHP = int(request.GET['educationHP'])
    #Renewable Generation GET Requests
    windCapacity = int(request.GET['windCapacity'])
    pvCapacity = int(request.GET['pvCapacity'])
    #Energy Storage GET Requests
    esCapacity = int(request.GET['esCapacity'])

    if m==1 or m==3 or m==5 or m==7 or m==8 or m==10 or m==12:
        d=31
    elif m==4 or m==6 or m==9 or m==11:
        d=30
    elif m==2:
        d=28
    elif m==13:
        d=365

    
    #########################################################################

    #Base GSP Data
    gspBase = gspDemand(supplyPoint, m, d)
    gspBaseData=np.zeros(len(gspBase))
    gspBaseData[0:]=gspBase[0:].as_matrix()
    gspName=GSP.objects.get(idx=supplyPoint)

    #Turn Percentages into Numbers
    statGSP = process_data_normal((gspStats.objects.filter(index=supplyPoint)), gspStats, 16)

    smallHousesHP = int(statGSP[0,8]*(smallHP/100))
    mediumHousesHP = int((statGSP[0,6] + statGSP[0,7]) * (mediumHP/100))
    largeHousesHP =  int(statGSP[0,5] * (largeHP/100))

    smallHousesSH = int(statGSP[0,8]*(smallSH/100))
    mediumHousesSH = int(statGSP[0,8]*(mediumSH/100))
    largeHousesSH = int(statGSP[0,8]*(largeSH/100))

    #Extract Weather Data for GSP Location
    latitude=statGSP[0,2]
    longitude=statGSP[0,3]
    tmy_data, altitude = extract_weather(d,m, latitude, longitude) # tmy_data is weather data for that lat/lon location
    temp=tmy_data['DryBulb']
    

    #EV Charging Data
    if urbanEV == 0:
        profileTotalUrban = np.zeros(d*24)
    else:
        urbanNum=int(statGSP[0,9]*(urbanEV/100))
        profileTotalUrban = calculateEVCharge(supplyPoint,d,urbanNum,'Urban')

    if ruralEV == 0:
        profileTotalRural = np.zeros(d*24)
    else: 
        ruralNum=int(statGSP[0,9]*(ruralEV/100))
        profileTotalRural = calculateEVCharge(supplyPoint,d,ruralNum,'Rural')
    
    evTotal = np.add(profileTotalUrban.reshape((d*24),), profileTotalRural.reshape((d*24),))/1000 # /1000 to turn in to MW


    #Heat Pump Demand
    if smallHousesHP == 0 and mediumHousesHP == 0 and largeHousesHP == 0:
        totHPCharge = np.zeros(d*24)
    else:
        totHPCharge = calculateHeatPumpDemand(supplyPoint, tmy_data, d, m, smallHousesHP, mediumHousesHP, largeHousesHP)

    #Storage Heater Demand
    if smallHousesSH == 0 and mediumHousesSH == 0 and largeHousesSH == 0:
        totSHCharge = np.zeros(d*24)
    else:
        totSHCharge = calculateStorageHeaterDemand(supplyPoint, d, m, smallHousesSH, mediumHousesSH, largeHousesSH)

    #Industrial Heat Pump Demand
    if manufacturingHP == 0 and entertainmentHP ==0 and commercialHP ==0 and educationHP == 0:
        totalHeatPumpIndustrial = np.zeros(d*24)
    else:
        totalHeatPumpIndustrial = calculateIndustrialHeatPumpDemand(supplyPoint, d, m, temp, manufacturingHP, commercialHP, entertainmentHP, educationHP, 1)

    #Renewable Generation Output
    
    ###PV Generation###
    if pvCapacity == 0:
        pvOutput=np.zeros(d*24)
    else:
        ratingPV = 5000 # average PV installation rating, in Watts
        pvNumber = int((pvCapacity*1e6) / ratingPV)
        pvOutputProxy = pvPowerOut(tmy_data, latitude, longitude, altitude, ratingPV)
        pvOutput = ((pvOutputProxy.as_matrix() * pvNumber)/1e6) #Total PV output in MW.
    ###             ###

    ###Wind Generation###
    if windCapacity == 0:
        windOutput=np.zeros(d*24)
    else:
        ratingWind = 1000 # ratingWind has to be put into kW
        windNumber = int((windCapacity*1e3)/ratingWind)
        windOutputProxy = calculateWindOutput(tmy_data, ratingWind)
        windOutput = ((windOutputProxy*windNumber)/1e3) #Total PV output in MW.
    ###             ###
     
        
    #New GSP Demand
    modelledGSP=np.zeros(len(gspBase))
    for i in range(0, len(gspBase)):
        modelledGSP[i]=(evTotal[i]) + (totHPCharge[i]) + (totSHCharge[i]) + (totalHeatPumpIndustrial[i] - pvOutput[i] - windOutput[i]) + gspBase[i]


    #Energy Storage
    if esCapacity == 0:
        demandWithES = np.zeros(d*24)
    else:
        demandWithESProxy=np.zeros([24, d])
        for i in range(1,(d+1)):
            model, sol, flo, cha, dis, nD = runSolutionBalance(esCapacity, (modelledGSP[(24*i)-24:(24*i)]))
            demandWithESProxy[0:,(i-1)]=nD

        demandWithES=demandWithESProxy.reshape((d*24),order='F')

    ##############################################
    #Plotting in Here
    if d == 1:
        formatter = DateFormatter('%H-%M')
        rule = rrulewrapper(HOURLY, interval=6)
    elif d < 4:
        formatter = DateFormatter('%d-%m-%y')
        rule = rrulewrapper(DAILY, interval=1)
    elif d < 10:
         formatter = DateFormatter('%d-%m-%y')
         rule = rrulewrapper(DAILY, interval=2)
    elif d > 9 and d <16:
        formatter = DateFormatter('%d-%m-%y')
        rule = rrulewrapper(DAILY, interval=3)
    elif d > 15 and d < 32:
        formatter = DateFormatter('%d-%m')
        rule = rrulewrapper(DAILY, interval=5)

    if m==13:
        formatter = DateFormatter('%b-%Y')
        rule = rrulewrapper(MONTHLY, interval=3)

    loc = RRuleLocator(rule)
    fig, ax =plt.subplots()
    ax.plot_date(gspBase.index, gspBaseData, linestyle='-', marker='None', label='Base Case')
    
    if esCapacity == 0:
        ax.plot_date(gspBase.index, modelledGSP, linestyle='-', marker='None', label='Modelled GSP Flow')
    else:
        ax.plot_date(gspBase.index, modelledGSP, linestyle='-', marker='None', label='Modelled GSP Flow w/o BES')
        ax.plot_date(gspBase.index, demandWithES, linestyle='-', marker='None', label='Modelled GSP Flow with BES')
        
    ax.xaxis.set_major_formatter(formatter)
    ax.xaxis.set_major_locator(loc)
    ax.legend()
    plt.grid(True)
    title = 'Modelled Flows at ' + gspName.name + ' GSP'
    plt.title(title)

    buffer = BytesIO()
    canvas = pylab.get_current_fig_manager().canvas
    canvas.draw()
    pilImage = PIL.Image.frombytes("RGB", canvas.get_width_height(), canvas.tostring_rgb())
    pilImage.save(buffer, "PNG")
    pylab.close()

    image_png = buffer.getvalue()
    graphic = base64.b64encode(image_png)
    graphic = graphic.decode('utf-8')

    ##Statistics for outputting with the plots
    maxGSP = round(max(gspBaseData, key=abs),2)
    maxNew = round(max(modelledGSP, key=abs),2)

    if esCapacity == 0:
        return render(request, 'whole/show_plot.html',{'graphic':graphic, 'firm': statGSP[0,1], 'maxGSP': maxGSP,'maxNew': maxNew})
    else:
        maxStorage = round(max(demandWithES),2)
        return render(request, 'whole/show_plot_storage.html',{'graphic':graphic, 'firm': statGSP[0,1], 'maxGSP': maxGSP, 'maxNew': maxNew, 'maxStorage': maxStorage})

    


#####################################################################################################
#####################################################################################################










#####################################################################################################
#####################################################################################################

def whole_data(request):

    ################GET REQUESTS############################################
    
    #Generic GET Requests
    supplyPoint=request.GET['supplyPoint']
    m = int(request.GET['month'])
    #EV GET Requests
    urbanEV = int(request.GET['urbanEV'])
    ruralEV = int(request.GET['ruralEV'])
    #Heat Pump GET Requests
    smallHP = int(request.GET['smallHP'])
    mediumHP = int(request.GET['mediumHP'])
    largeHP = int(request.GET['largeHP'])
    #Storage Heater GET Requests
    smallSH = int(request.GET['smallSH'])
    mediumSH = int(request.GET['mediumSH'])
    largeSH = int(request.GET['largeSH'])
    #Industrial Heat Pump GET Requests
    manufacturingHP = int(request.GET['manufacturingHP'])
    commercialHP = int(request.GET['commercialHP'])
    entertainmentHP = int(request.GET['entertainmentHP'])
    educationHP = int(request.GET['educationHP'])
    #Renewable Generation GET Requests
    windCapacity = int(request.GET['windCapacity'])    
    pvCapacity = int(request.GET['pvCapacity'])    
    #Energy Storage GET Requests
    esCapacity = int(request.GET['esCapacity'])

    if m==1 or m==3 or m==5 or m==7 or m==8 or m==10 or m==12:
        d=31
    elif m==4 or m==6 or m==9 or m==11:
        d=30
    elif m==2:
        d=28
    elif m==13:
        d=365
    
    #########################################################################

    #Base GSP Data
    gspBase = gspDemand(supplyPoint, m, d)
    gspBaseData=np.zeros(len(gspBase))
    gspBaseData[0:]=gspBase[0:].as_matrix()
    gspName=GSP.objects.get(idx=supplyPoint)

    #Turn Percentages into Numbers
    statGSP = process_data_normal((gspStats.objects.filter(index=supplyPoint)), gspStats, 16)

    smallHousesHP = int(statGSP[0,8]*(smallHP/100))
    mediumHousesHP = int((statGSP[0,6] + statGSP[0,7]) * (mediumHP/100))
    largeHousesHP =  int(statGSP[0,5] * (largeHP/100))

    smallHousesSH = int(statGSP[0,8]*(smallSH/100))
    mediumHousesSH = int(statGSP[0,8]*(mediumSH/100))
    largeHousesSH = int(statGSP[0,8]*(largeSH/100))

    #Extract Weather Data for GSP Location
    latitude=statGSP[0,2]
    longitude=statGSP[0,3]
    tmy_data, altitude = extract_weather(d,m, latitude, longitude) # tmy_data is weather data for that lat/lon location
    temp=tmy_data['DryBulb']
    

    #EV Charging Data
    if urbanEV == 0:
        profileTotalUrban = np.zeros(d*24)
    else:
        urbanNum=int(statGSP[0,9]*(urbanEV/100))
        profileTotalUrban = calculateEVCharge(supplyPoint,d,urbanNum,'Urban')

    if ruralEV == 0:
        profileTotalRural = np.zeros(d*24)
    else: 
        ruralNum=int(statGSP[0,9]*(ruralEV/100))
        profileTotalRural = calculateEVCharge(supplyPoint,d,ruralNum,'Rural')

    evTotal = np.add(profileTotalUrban.reshape((d*24),), profileTotalRural.reshape((d*24),))/1000 # /1000 to turn in to MW


    #Heat Pump Demand
    if smallHousesHP == 0 and mediumHousesHP == 0 and largeHousesHP == 0:
        totHPCharge = np.zeros(d*24)
    else:
        totHPCharge = calculateHeatPumpDemand(supplyPoint, tmy_data, d, m, smallHousesHP, mediumHousesHP, largeHousesHP)

    #Storage Heater Demand
    if smallHousesSH == 0 and mediumHousesSH == 0 and largeHousesSH == 0:
        totSHCharge = np.zeros(d*24)
    else:
        totSHCharge = calculateStorageHeaterDemand(supplyPoint, d, m, smallHousesSH, mediumHousesSH, largeHousesSH)

    #Industrial Heat Pump Demand
    if manufacturingHP == 0 and entertainmentHP ==0 and commercialHP ==0 and educationHP == 0:
        totalHeatPumpIndustrial = np.zeros(d*24)
    else:
        totalHeatPumpIndustrial = calculateIndustrialHeatPumpDemand(supplyPoint, d, m, temp, manufacturingHP, commercialHP, entertainmentHP, educationHP, 1)

    #Renewable Generation Output
    
    ###PV Generation###
    if pvCapacity == 0:
        pvOutput=np.zeros(d*24)
    else:
        ratingPV = 5000 # average PV installation rating, in Watts
        pvNumber = int((pvCapacity*1e6) / ratingPV)
        pvOutputProxy = pvPowerOut(tmy_data, latitude, longitude, altitude, ratingPV)
        pvOutput = ((pvOutputProxy.as_matrix() * pvNumber)/1e6) #Total PV output in MW.
    ###             ###

    ###Wind Generation###
    if windCapacity == 0:
        windOutput=np.zeros(d*24)
    else:
        ratingWind = 1000 # ratingWind has to be put into kW
        windNumber = int((windCapacity*1e3)/ratingWind) 
        windOutputProxy = calculateWindOutput(tmy_data, ratingWind)
        windOutput = ((windOutputProxy*windNumber)/1e3) #Total PV output in MW.
    ###             ###
        
    #New GSP Demand
    modelledGSP=np.zeros(len(gspBase))
    for i in range(0, len(gspBase)):
        modelledGSP[i]=(evTotal[i]) + (totHPCharge[i]) + (totSHCharge[i]) + (totalHeatPumpIndustrial[i] - pvOutput[i] - windOutput[i]) + gspBase[i]

    #Energy Storage
    if esCapacity == 0:
        demandWithES = np.zeros(d*24)
    else:
        demandWithESProxy=np.zeros([24, d])
        for i in range(1,(d+1)):
            model, sol, flo, cha, dis, nD = runSolutionBalance(esCapacity, (modelledGSP[(24*i)-24:(24*i)]))
            demandWithESProxy[0:,(i-1)]=nD

        demandWithES=demandWithESProxy.reshape((d*24),order='F')

    #Compile Outputs to csv data and write to client
    if esCapacity == 0:
        compiledOutputs = {'a':gspBase.reshape((d*24),), 'b': evTotal.reshape((d*24),), 'c': totHPCharge.reshape((d*24),),
                       'd':totSHCharge.reshape((d*24),), 'e': totalHeatPumpIndustrial.reshape((d*24),), 'f': pvOutput.reshape((d*24),),
                       'g': windOutput.reshape((d*24),), 'h': modelledGSP.reshape((d*24),)}
    else:       
        compiledOutputs = {'a':gspBase.reshape((d*24),), 'b': evTotal.reshape((d*24),), 'c': totHPCharge.reshape((d*24),),
                       'd':totSHCharge.reshape((d*24),), 'e': totalHeatPumpIndustrial.reshape((d*24),), 'f': pvOutput.reshape((d*24),),
                       'g': windOutput.reshape((d*24),), 'h': modelledGSP.reshape((d*24),), 'i':demandWithES.reshape((d*24),)}


    fullModelledData=pd.DataFrame(compiledOutputs, index=gspBase.index)
    fullModelledData=fullModelledData.reset_index()
    
    response = HttpResponse(content_type='text/csv')

    if m == 1:
        file =gspName.name +'GSP_'+'Jan.csv'
    elif m == 2:
        file =gspName.name +'GSP_'+'Feb.csv'
    elif m == 3:    
        file =gspName.name +'GSP_'+'Mar.csv'
    elif m == 4:
        file =gspName.name +'GSP_'+'Apr.csv'
    elif m == 5:
        file =gspName.name +'GSP_'+'May.csv'
    elif m == 6:
        file =gspName.name +'GSP_'+'Jun.csv'
    elif m == 7:
        file =gspName.name +'GSP_'+'Jul.csv'
    elif m == 8:
        file =gspName.name +'GSP_'+'Aug.csv'
    elif m == 9:
        file =gspName.name +'GSP_'+'Sep.csv'
    elif m == 10:
        file =gspName.name +'GSP_'+'Oct.csv'
    elif m == 11:
        file =gspName.name +'GSP_'+'Nov.csv'
    elif m == 12:
        file =gspName.name +'GSP_'+'Dec.csv'
    elif m == 13:
        file = gspName.name +' GSP.csv'

    response['Content-Disposition'] = 'attachment; filename="%s"' % file
    writer = csv.writer(response)
    
    with open('heat_demand.csv','w') as csvfile:
        writer.writerow(['GSP', gspName.name])
        writer.writerow(['Firm Limit (MW)', statGSP[0,1]])
        if esCapacity == 0:
            writer.writerow(['', 'Electrical Demand (MWh)', 'EV Charging Demand(MWh)','Heat Pump Demand(MWh)','Storage Heater Demand (MWh)', 'Industrial Heat Pump Demand (MWh)', 'PV Output(MWh)', 'Wind Output (MWh)', 'Modelled GSP Demand(MWh)'])
            
        else:
            writer.writerow(['', 'Electrical Demand (MWh)', 'EV Charging Demand(MWh)','Heat Pump Demand(MWh)','Storage Heater Demand (MWh)', 'Industrial Heat Pump Demand (MWh)', 'PV Output(MWh)', 'Wind Output (MWh)', 'Modelled GSP Demand w/o Storage(MWh)', 'Modelled GSP Demand with Storage(MWh)'])
        for i in range(0,len(fullModelledData)):
            writer.writerow(fullModelledData.iloc[i,0:])

    
    return response

def whole_plot_num(request):
    #Generic GET Requests
    supplyPoint=request.GET['supplyPoint']
    m = int(request.GET['month'])
    #EV GET Requests
    urbanEV = int(request.GET['urbanEV'])
    ruralEV = int(request.GET['ruralEV'])
    #Heat Pump GET Requests
    smallHP = int(request.GET['smallHP'])
    mediumHP = int(request.GET['mediumHP'])
    largeHP = int(request.GET['largeHP'])
    #Storage Heater GET Requests
    smallSH = int(request.GET['smallSH'])
    mediumSH = int(request.GET['mediumSH'])
    largeSH = int(request.GET['largeSH'])
    #Industrial Heat Pump GET Requests
    manufacturingHP = int(request.GET['manufacturingHP'])
    commercialHP = int(request.GET['commercialHP'])
    entertainmentHP = int(request.GET['entertainmentHP'])
    educationHP = int(request.GET['educationHP'])
    #Renewable Generation GET Requests
    windCapacity = int(request.GET['windCapacity'])
    pvCapacity = int(request.GET['pvCapacity'])
    #Energy Storage GET Requests
    esCapacity = int(request.GET['esCapacity'])

    if m==1 or m==3 or m==5 or m==7 or m==8 or m==10 or m==12:
        d=31
    elif m==4 or m==6 or m==9 or m==11:
        d=30
    elif m==2:
        d=28
    elif m==13:
        d=365
        
    #########################################################################
    
    #Base GSP Data
    gspBase = gspDemand(supplyPoint, m, d)
    gspBaseData=np.zeros(len(gspBase))
    gspBaseData[0:]=gspBase[0:].as_matrix()
    gspName=GSP.objects.get(idx=supplyPoint)
    
    #Turn Percentages into Numbers
    statGSP = process_data_normal((gspStats.objects.filter(index=supplyPoint)), gspStats, 16)
    
    
    #Extract Weather Data for GSP Location
    latitude=statGSP[0,2]
    longitude=statGSP[0,3]
    tmy_data, altitude = extract_weather(d,m, latitude, longitude) # tmy_data is weather data for that lat/lon location
    temp=tmy_data['DryBulb']
    
    
    #EV Charging Data
    if urbanEV == 0:
        profileTotalUrban = np.zeros(d*24)
    else:
        profileTotalUrban = calculateEVCharge(supplyPoint,d,urbanEV,'Urban')
    
    if ruralEV == 0:
        profileTotalRural = np.zeros(d*24)
    else:
        profileTotalRural = calculateEVCharge(supplyPoint,d,ruralEV,'Rural')
    
    evTotal = np.add(profileTotalUrban.reshape((d*24),), profileTotalRural.reshape((d*24),))/1000 # /1000 to turn in to MW


    #Heat Pump Demand
    if smallHP == 0 and mediumHP == 0 and largeHP == 0:
        totHPCharge = np.zeros(d*24)
    else:
        totHPCharge = calculateHeatPumpDemand(supplyPoint, tmy_data, d, m, smallHP, mediumHP, largeHP)

    #Storage Heater Demand
    if smallSH == 0 and mediumSH == 0 and largeSH == 0:
        totSHCharge = np.zeros(d*24)
    else:
        totSHCharge = calculateStorageHeaterDemand(supplyPoint, d, m, smallSH, mediumSH, largeSH)

    #Industrial Heat Pump Demand
    if manufacturingHP == 0 and entertainmentHP ==0 and commercialHP ==0 and educationHP == 0:
        totalHeatPumpIndustrial = np.zeros(d*24)
    else:
        totalHeatPumpIndustrial = calculateIndustrialHeatPumpDemand(supplyPoint, d, m, temp, manufacturingHP, commercialHP, entertainmentHP, educationHP, 0)

    #Renewable Generation Output

    ###PV Generation###
    if pvCapacity == 0:
        pvOutput=np.zeros(d*24)
    else:
        ratingPV = 5000 # average PV installation rating, in Watts
        pvNumber = int((pvCapacity*1e6) / ratingPV)
        pvOutputProxy = pvPowerOut(tmy_data, latitude, longitude, altitude, ratingPV)
        pvOutput = ((pvOutputProxy.as_matrix() * pvNumber)/1e6) #Total PV output in MW.
    ###             ###

    ###Wind Generation###
    if windCapacity == 0:
        windOutput=np.zeros(d*24)
    else:
        ratingWind = 1000 # ratingWind has to be put into kW
        windNumber = int((windCapacity*1e3)/ratingWind) 
        windOutputProxy = calculateWindOutput(tmy_data, ratingWind)
        windOutput = ((windOutputProxy*windNumber)/1e3) #Total PV output in MW.
    ###             ###

    #New GSP Demand
    modelledGSP=np.zeros(len(gspBase))
    for i in range(0, len(gspBase)):
        modelledGSP[i]=(evTotal[i]) + (totHPCharge[i]) + (totSHCharge[i]) + (totalHeatPumpIndustrial[i] - pvOutput[i] - windOutput[i]) + gspBase[i]
        
    #Energy Storage
    if esCapacity == 0:
        demandWithES = np.zeros(d*24)
    else:
        demandWithESProxy=np.zeros([24, d])
        for i in range(1,(d+1)):
            model, sol, flo, cha, dis, nD = runSolutionBalance(esCapacity, (modelledGSP[(24*i)-24:(24*i)]))
            demandWithESProxy[0:,(i-1)]=nD

        demandWithES=demandWithESProxy.reshape((d*24),order='F')
        
    ##############################################
    #Plotting in Here
    if d == 1:
        formatter = DateFormatter('%H-%M')
        rule = rrulewrapper(HOURLY, interval=6)
    elif d < 4:
        formatter = DateFormatter('%d-%m-%y')
        rule = rrulewrapper(DAILY, interval=1)
    elif d < 10:
        formatter = DateFormatter('%d-%m-%y')
        rule = rrulewrapper(DAILY, interval=2)
    elif d > 9 and d <16:
        formatter = DateFormatter('%d-%m-%y')
        rule = rrulewrapper(DAILY, interval=3)
    elif d > 15 and d < 32:
        formatter = DateFormatter('%d-%m')
        rule = rrulewrapper(DAILY, interval=5)

    if m==13:
        formatter = DateFormatter('%b-%Y')
        rule = rrulewrapper(MONTHLY, interval=3)

    loc = RRuleLocator(rule)
    fig, ax =plt.subplots()
    ax.plot_date(gspBase.index, gspBaseData, linestyle='-', marker='None')

    if esCapacity == 0:
        ax.plot_date(gspBase.index, modelledGSP, linestyle='-', marker='None', label='Modelled GSP Flow')
    else:
        ax.plot_date(gspBase.index, modelledGSP, linestyle='-', marker='None', label='Modelled GSP Flow w/o BES')
        ax.plot_date(gspBase.index, demandWithES, linestyle='-', marker='None', label='Modelled GSP Flow with BES')

    
    ax.xaxis.set_major_formatter(formatter)
    ax.xaxis.set_major_locator(loc)
    plt.grid(True)
    title = 'Modelled Flows at ' + gspName.name + ' GSP'
    plt.title(title)

    buffer = BytesIO()
    canvas = pylab.get_current_fig_manager().canvas
    canvas.draw()
    pilImage = PIL.Image.frombytes("RGB", canvas.get_width_height(), canvas.tostring_rgb())
    pilImage.save(buffer, "PNG")
    pylab.close()

    image_png = buffer.getvalue()
    graphic = base64.b64encode(image_png)
    graphic = graphic.decode('utf-8')

    ##Statistics for outputting with the plots
    maxGSP = round(max(gspBaseData, key=abs),2)
    maxNew = round(max(modelledGSP, key=abs),2)

    if esCapacity == 0:
        return render(request, 'whole/show_plot.html',{'graphic':graphic, 'firm': statGSP[0,1], 'maxGSP': maxGSP,'maxNew': maxNew})
    else:
        maxStorage = round(max(demandWithES),2)
        return render(request, 'whole/show_plot_storage.html',{'graphic':graphic, 'firm': statGSP[0,1], 'maxGSP': maxGSP, 'maxNew': maxNew, 'maxStorage': maxStorage})

def whole_data_num(request):
    ################GET REQUESTS############################################
    
    #Generic GET Requests
    supplyPoint=request.GET['supplyPoint']
    m = int(request.GET['month'])
    #EV GET Requests
    urbanEV = int(request.GET['urbanEV'])
    ruralEV = int(request.GET['ruralEV'])
    #Heat Pump GET Requests
    smallHP = int(request.GET['smallHP'])
    mediumHP = int(request.GET['mediumHP'])
    largeHP = int(request.GET['largeHP'])
    #Storage Heater GET Requests
    smallSH = int(request.GET['smallSH'])
    mediumSH = int(request.GET['mediumSH'])
    largeSH = int(request.GET['largeSH'])
    #Industrial Heat Pump GET Requests
    manufacturingHP = int(request.GET['manufacturingHP'])
    commercialHP = int(request.GET['commercialHP'])
    entertainmentHP = int(request.GET['entertainmentHP'])
    educationHP = int(request.GET['educationHP'])
    #Renewable Generation GET Requests
    windCapacity = int(request.GET['windCapacity'])
    pvCapacity = int(request.GET['pvCapacity'])
    #Energy Storage GET Requests
    esCapacity = int(request.GET['esCapacity'])

    if m==1 or m==3 or m==5 or m==7 or m==8 or m==10 or m==12:
        d=31
    elif m==4 or m==6 or m==9 or m==11:
        d=30
    elif m==2:
        d=28
    elif m==13:
        d=365
    
    #########################################################################
    
    #Base GSP Data
    gspBase = gspDemand(supplyPoint, m, d)
    gspBaseData=np.zeros(len(gspBase))
    gspBaseData[0:]=gspBase[0:].as_matrix()
    gspName=GSP.objects.get(idx=supplyPoint)
    
    #Turn Percentages into Numbers
    statGSP = process_data_normal((gspStats.objects.filter(index=supplyPoint)), gspStats, 16)
    
    
    #Extract Weather Data for GSP Location
    latitude=statGSP[0,2]
    longitude=statGSP[0,3]
    tmy_data, altitude = extract_weather(d,m, latitude, longitude) # tmy_data is weather data for that lat/lon location
    temp=tmy_data['DryBulb']
    
    
    #EV Charging Data
    if urbanEV == 0:
        profileTotalUrban = np.zeros(d*24)
    else:
        profileTotalUrban = calculateEVCharge(supplyPoint,d,urbanEV,'Urban')
    
    if ruralEV == 0:
        profileTotalRural = np.zeros(d*24)
    else:
        profileTotalRural = calculateEVCharge(supplyPoint,d,ruralEV,'Rural')

    evTotal = np.add(profileTotalUrban.reshape((d*24),), profileTotalRural.reshape((d*24),))/1000 # /1000 to turn in to MW


    #Heat Pump Demand
    if smallHP == 0 and mediumHP == 0 and largeHP == 0:
        totHPCharge = np.zeros(d*24)
    else:
        totHPCharge = calculateHeatPumpDemand(supplyPoint, tmy_data, d, m, smallHP, mediumHP, largeHP)

    #Storage Heater Demand
    if smallSH == 0 and mediumSH == 0 and largeSH == 0:
        totSHCharge = np.zeros(d*24)
    else:
        totSHCharge = calculateStorageHeaterDemand(supplyPoint, d, m, smallSH, mediumSH, largeSH)
    
    #Industrial Heat Pump Demand
    if manufacturingHP == 0 and entertainmentHP ==0 and commercialHP ==0 and educationHP == 0:
        totalHeatPumpIndustrial = np.zeros(d*24)
    else:
        totalHeatPumpIndustrial = calculateIndustrialHeatPumpDemand(supplyPoint, d, m, temp, manufacturingHP, commercialHP, entertainmentHP, educationHP, 0)

    #Renewable Generation Output

    ###PV Generation###
    if pvCapacity == 0:
        pvOutput=np.zeros(d*24)
    else:
        ratingPV = 5000 # average PV installation rating, in Watts
        pvNumber = int((pvCapacity*1e6) / ratingPV)
        pvOutputProxy = pvPowerOut(tmy_data, latitude, longitude, altitude, ratingPV)
        pvOutput = ((pvOutputProxy.as_matrix() * pvNumber)/1e6) #Total PV output in MW.
    ###             ###

    ###Wind Generation###
    if windCapacity == 0:
        windOutput=np.zeros(d*24)
    else:
        ratingWind = 1000 # ratingWind has to be put into kW
        windNumber = int((windCapacity*1e3)/ratingWind) 
        windOutputProxy = calculateWindOutput(tmy_data, ratingWind)
        windOutput = ((windOutputProxy*windNumber)/1e3) #Total PV output in MW.
    ###             ###

    #New GSP Demand
    modelledGSP=np.zeros(len(gspBase))
    for i in range(0, len(gspBase)):
        modelledGSP[i]=(evTotal[i]) + (totHPCharge[i]) + (totSHCharge[i]) + (totalHeatPumpIndustrial[i] - pvOutput[i] - windOutput[i]) + gspBase[i]
    
    #Energy Storage
    if esCapacity == 0:
        demandWithES = np.zeros(d*24)
    else:
        demandWithESProxy=np.zeros([24, d])
        for i in range(1,(d+1)):
            model, sol, flo, cha, dis, nD = runSolutionBalance(esCapacity, (modelledGSP[(24*i)-24:(24*i)]))
            demandWithESProxy[0:,(i-1)]=nD

        demandWithES=demandWithESProxy.reshape((d*24),order='F')

    #Compile Outputs to csv data and write to client
    if esCapacity == 0:
        compiledOutputs = {'a':gspBase.reshape((d*24),), 'b': evTotal.reshape((d*24),), 'c': totHPCharge.reshape((d*24),),
                       'd':totSHCharge.reshape((d*24),), 'e': totalHeatPumpIndustrial.reshape((d*24),), 'f': pvOutput.reshape((d*24),),
                       'g': windOutput.reshape((d*24),), 'h': modelledGSP.reshape((d*24),)}
    else:       
        compiledOutputs = {'a':gspBase.reshape((d*24),), 'b': evTotal.reshape((d*24),), 'c': totHPCharge.reshape((d*24),),
                       'd':totSHCharge.reshape((d*24),), 'e': totalHeatPumpIndustrial.reshape((d*24),), 'f': pvOutput.reshape((d*24),),
                       'g': windOutput.reshape((d*24),), 'h': modelledGSP.reshape((d*24),), 'i':demandWithES.reshape((d*24),)}


    fullModelledData=pd.DataFrame(compiledOutputs, index=gspBase.index)
    fullModelledData=fullModelledData.reset_index()
    
    response = HttpResponse(content_type='text/csv')

    if m == 1:
        file =gspName.name +'GSP_'+'Jan.csv'
    elif m == 2:
        file =gspName.name +'GSP_'+'Feb.csv'
    elif m == 3:    
        file =gspName.name +'GSP_'+'Mar.csv'
    elif m == 4:
        file =gspName.name +'GSP_'+'Apr.csv'
    elif m == 5:
        file =gspName.name +'GSP_'+'May.csv'
    elif m == 6:
        file =gspName.name +'GSP_'+'Jun.csv'
    elif m == 7:
        file =gspName.name +'GSP_'+'Jul.csv'
    elif m == 8:
        file =gspName.name +'GSP_'+'Aug.csv'
    elif m == 9:
        file =gspName.name +'GSP_'+'Sep.csv'
    elif m == 10:
        file =gspName.name +'GSP_'+'Oct.csv'
    elif m == 11:
        file =gspName.name +'GSP_'+'Nov.csv'
    elif m == 12:
        file =gspName.name +'GSP_'+'Dec.csv'
    elif m == 13:
        file = gspName.name +' GSP.csv'

    response['Content-Disposition'] = 'attachment; filename="%s"' % file
    writer = csv.writer(response)
    
    with open('heat_demand.csv','w') as csvfile:
        writer.writerow(['GSP', gspName.name])
        writer.writerow(['Firm Limit (MW)', statGSP[0,1]])
        if esCapacity == 0:
            writer.writerow(['', 'Electrical Demand (MWh)', 'EV Charging Demand(MWh)','Heat Pump Demand(MWh)','Storage Heater Demand (MWh)', 'Industrial Heat Pump Demand (MWh)', 'PV Output(MWh)', 'Wind Output (MWh)', 'Modelled GSP Demand(MWh)'])
            
        else:
            writer.writerow(['', 'Electrical Demand (MWh)', 'EV Charging Demand(MWh)','Heat Pump Demand(MWh)','Storage Heater Demand (MWh)', 'Industrial Heat Pump Demand (MWh)', 'PV Output(MWh)', 'Wind Output (MWh)', 'Modelled GSP Demand w/o Storage(MWh)', 'Modelled GSP Demand with Storage(MWh)'])
        for i in range(0,len(fullModelledData)):
            writer.writerow(fullModelledData.iloc[i,0:])

    
    return response

def check_inputs(clientInput):

    if clientInput == '':
        formatInput = int(0)
    else:
        formatInput = int(clientInput)

    return formatInput
    
