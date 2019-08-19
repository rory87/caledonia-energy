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
import json

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
from electrical.models import electricalPrimarySSE

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
from whole.models import primarySSEStats
from whole.models import windFES
from whole.models import pvFES
from whole.models import storageFES
from whole.models import subWindFES
from whole.models import subPVFES
from whole.models import subStorageFES
from whole.models import hpFES
from whole.models import evFES 
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

@login_required(login_url='/login/')
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

########

@login_required(login_url='/login/')
def whole_primary_form(request): 
    return render(request, 'whole/show_primary_analysis.html')

@login_required(login_url='/login/')
def fes18_form(request): 
    return render(request, 'whole/fes18_form.html')

def whole_primary_plot(request):
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
    windCapacity = float(request.GET['windCapacity'])
    pvCapacity = float(request.GET['pvCapacity'])
    #Energy Storage GET Requests
    esCapacity = float(request.GET['esCapacity'])

    #Number of Days for Analysis
    d=365

    #Assume that no Manufacturing Industries are connected at or below 11kV
    manufacturingHP = 0

    #Fetch Primary Substation Statistics and Base Demand for the relevant GSP
    pri = process_data_normal((primarySSEStats.objects.filter(gsp = supplyPoint)), primarySSEStats, 5)
    subIndex = pri[0:,0]
    subNames = pri[0:,1]
    subRating = pri[0:,3]
    subCustomers = pri[0:,4]

    baseDemand = np.zeros([8784, len(pri)])
    for i in range(0, len(pri)):
        baseDemand[0:,i] = process_data_normal((electricalPrimarySSE.objects.filter(primary =subIndex[i])), electricalPrimarySSE, 3)[0:,2]

    
    #Turn LCT Percentages into Numbers
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

    newDemand=np.zeros([(baseDemand.shape[0]-24), baseDemand.shape[1]])
    for i in range(0, len(subCustomers)):
        for j in range(0, (len(baseDemand)-24)):
            newDemand[j,i] = ((evTotal[j]) + (totHPCharge[j]) + (totSHCharge[j]) + (totalHeatPumpIndustrial[j] - pvOutput[j] - windOutput[j])*(subCustomers[i]/sum(subCustomers))) + baseDemand[j,i]

def fes18_analysis(request):
 
    #Generic GET Requests
    supplyPoint=int(request.GET['supplyPoint'])
    scenario = int(request.GET['scenario'])

    #Number of Days/Months for Analysis
    d=365
    m=13

    #Assume that no Manufacturing Industries are connected at or below 11kV
    manufacturingHP = 0

    #Fetch Primary Substation Statistics and Base Demand for the relevant GSP
    if supplyPoint > 77:
        pri = process_data_normal((primarySSEStats.objects.filter(gsp = supplyPoint)), primarySSEStats, 5)
        subIndex = pri[0:,0]
        subNames = pri[0:,1]
        subRating = pri[0:,3]
        subCustomers = pri[0:,4]

        baseDemand = np.zeros([8784, len(pri)])
        for i in range(0, len(pri)):
         baseDemand[0:,i] = process_data_normal((electricalPrimarySSE.objects.filter(primary =subIndex[i])), electricalPrimarySSE, 3)[0:,2]

    #Fetch GSP Stat Data
    statGSP = process_data_normal((gspStats.objects.filter(index=supplyPoint)), gspStats, 16)

    #Extract Weather Data for GSP Location
    latitude=statGSP[0,2]
    longitude=statGSP[0,3]
    tmy_data, altitude = extract_weather(d,m, latitude, longitude) # tmy_data is weather data for that lat/lon location
    temp=tmy_data['DryBulb']


    #Fetch Heat Pump FES Data and infer demand across the scenario period
    hp = process_data_normal(hpFES.objects.filter(index=supplyPoint, scenario=scenario),hpFES, 25)[0,2:]
    smallHousesHP=0
    mediumHousesHP = floor((hp[len(hp)-1]*0.9)*0.3)
    largeHousesHP = floor((hp[len(hp)-1]*0.9)*0.7)
    totHPCharge40 = calculateHeatPumpDemand(supplyPoint, tmy_data, d, m, smallHousesHP, mediumHousesHP, largeHousesHP)
    hpTotalRes = np.zeros([totHPCharge40.shape[0], hp.shape[0]])
    hpTotalRes[0:, hp.shape[0]-1] = totHPCharge40
    for i in range(0, hp.shape[0]-1):
     hpTotalRes[0:,i] = (hp[i]/(hp[hp.shape[0]-1]))*totHPCharge40



    manufacturingHP = floor((hp[len(hp)-1]*0.1)*0.05)
    commercialHP = floor((hp[len(hp)-1]*0.1)*0.8)
    entertainmentHP = floor((hp[len(hp)-1]*0.1)*0.1)
    educationHP = floor((hp[len(hp)-1]*0.1)*0.05)

    totalHeatPumpIndustrialGSP = calculateIndustrialHeatPumpDemand(supplyPoint, d, m, temp, manufacturingHP, 0, 0, 0, 0)
    totalHeatPumpIndustrial40 = calculateIndustrialHeatPumpDemand(supplyPoint, d, m, temp, 0, commercialHP, entertainmentHP, educationHP, 0)


    hpTotalInd = np.zeros([totalHeatPumpIndustrial40.shape[0], hp.shape[0]])
    for i in range(0, hp.shape[0]-1):
     hpTotalInd[0:,i] = (hp[i]/(hp[hp.shape[0]-1]))*totalHeatPumpIndustrial40

    hpTotalInd[0:, hp.shape[0]-1]=totalHeatPumpIndustrial40 

    hpTotalIndGSP = np.zeros([totalHeatPumpIndustrialGSP.shape[0], hp.shape[0]])
    for i in range(0, hp.shape[0]-1):
     hpTotalIndGSP[0:, i] = (hp[i]/(hp[hp.shape[0]-1]))*totalHeatPumpIndustrialGSP

    hpTotalIndGSP[0:, hp.shape[0]-1]=totalHeatPumpIndustrialGSP 

    #Fetch EV FES Data and infer the demand across the scenario period
    ev = process_data_normal(evFES.objects.filter(index=supplyPoint, scenario=scenario), evFES, 25)[0,2:]
    urbanEV = floor(ev[len(ev)-1]*0.5)
    ruralEV = floor(ev[len(ev)-1]*0.5)
    profileTotalUrban = calculateEVCharge(supplyPoint,d,urbanEV,'Urban')
    profileTotalRural = calculateEVCharge(supplyPoint,d,ruralEV,'Rural')
    evProfile40 = np.reshape(((profileTotalUrban + profileTotalRural)/1000),8760)

    evTotal = np.zeros([evProfile40.shape[0], ev.shape[0]])
    for i in range(0, ev.shape[0]-1):
     evTotal[0:,i] = (ev[i]/(ev[ev.shape[0]-1]))*evProfile40

    evTotal[0:,ev.shape[0]-1] = evProfile40

    #Fetch Wind FES Data and infer the demand across the sceanrio period
    windLarge = process_data_normal(windFES.objects.filter(index=supplyPoint, scenario=scenario), windFES, 25)[0,2:]
    windSmall = process_data_normal(subWindFES.objects.filter(index=supplyPoint, scenario=scenario), subWindFES, 25)[0,2:]

    yearWL = np.asarray(np.where(windLarge != 0)[0])
    windLargeTotal = np.zeros([8760, windLarge.shape[0]])

    if yearWL.size != 0:
     capWL = windLarge[yearWL[len(yearWL)-1]]
     ratWL = 1000
     numWL = int((capWL*1e3)/ratWL)
     outputWLProxy = calculateWindOutput(tmy_data, ratWL)
     outputWL = ((outputWLProxy*numWL)/1e3)
     for i in range(0, windLarge.shape[0]):
         windLargeTotal[0:,i] = (windLarge[i]/windLarge[yearWL[len(yearWL)-1]])*outputWL

    yearWS = np.asarray(np.where(windSmall != 0)[0])
    windSmallTotal = np.zeros([8760, windSmall.shape[0]])

    if yearWS.size != 0:
     capWS = windSmall[yearWS[len(yearWS)-1]]
     ratWS = 300
     numWS = int((capWS*1e3)/ratWS)
     outputWSProxy =  calculateWindOutput(tmy_data, ratWS)
     outputWS = ((outputWSProxy*numWS)/1e3)
     for i in range(0, windSmall.shape[0]):
         windSmallTotal[0:,i] = (windSmall[i]/windSmall[yearWS[len(yearWS)-1]])*outputWS


    #Fetch PV FES Data
    pvLarge = process_data_normal(pvFES.objects.filter(index=supplyPoint, scenario=scenario), pvFES, 25)[0,2:]
    pvSmall = process_data_normal(subPVFES.objects.filter(index=supplyPoint, scenario=scenario), subPVFES, 25)[0,2:]

    yearPL = np.asarray(np.where(pvLarge != 0)[0])
    pvLargeTotal = np.zeros([8760, pvLarge.shape[0]])

    if yearPL.size != 0:
     capPL = pvLarge[yearPL[len(yearPL)-1]]
     ratPL = 1000000
     numPL = int((capPL*1e6) / ratPL)
     outputPLProxy = pvPowerOut(tmy_data, latitude, longitude, altitude, ratPL)
     outputPL = np.reshape(((outputPLProxy.as_matrix() * numPL)/1e6), 8760)
     for i in range(0, pvLarge.shape[0]):
         pvLargeTotal[0:,i] = (pvLarge[i]/pvLarge[yearPL[len(yearPL)-1]])*outputPL

    yearPS = np.asarray(np.where(pvSmall != 0)[0])
    pvSmallTotal = np.zeros([8760, pvSmall.shape[0]])

    if yearPS.size != 0:
     capPS = pvSmall[yearPS[len(yearPS)-1]]
     ratPS = 5000
     numPS = int((capPS*1e6) / ratPS)
     outputPSProxy = pvPowerOut(tmy_data, latitude, longitude, altitude, ratPS)
     outputPS = np.reshape(((outputPSProxy.as_matrix() * numPS)/1e6), 8760)
     for i in range(0, pvSmall.shape[0]):
         pvSmallTotal[0:,i] = (pvSmall[i]/pvSmall[yearPS[len(yearPS)-1]])*outputPS

    #Fetch Storage FES Data
    storageLarge = process_data_normal(storageFES.objects.filter(index=supplyPoint, scenario=scenario), storageFES, 25)[0,2:]
    storageSmall = process_data_normal(subStorageFES.objects.filter(index=supplyPoint, scenario=scenario), subStorageFES, 25)[0,2:]

    #Sum up Primary Flows
    lowCarbonPrimary = (hpTotalRes + hpTotalInd + evTotal +  hpTotalIndGSP - windSmallTotal - pvSmallTotal)

    if supplyPoint > 77:
        delCustomers = np.where(subCustomers == 0)[0]
        delRating = np.where(subRating == 0)[0]

        priNA = list(subNames[delRating]) + list(subNames[delCustomers])
        priNA = list( dict.fromkeys(priNA))

        priInd = list(delRating) + list(delCustomers)
        priInd = list( dict.fromkeys(priInd))

        subCustomers = np.delete(subCustomers, priInd)
        subRating =  np.delete(subRating, priInd)
        subNames =np.delete(subNames, priInd)
        baseDemand = np.delete(baseDemand, priInd, 1)[0:8760]

        newPrimaryDemand=np.zeros([len(subCustomers), 23])

        for i in range(0, newPrimaryDemand.shape[0]):
         for j in range(0, 23):
             if max((lowCarbonPrimary[0:,j] * (subCustomers[i]/sum(subCustomers))) + baseDemand[0:,i])/subRating[i] > abs(min((lowCarbonPrimary[0:,j] * (subCustomers[i]/sum(subCustomers))) + baseDemand[0:,i])/subRating[i]):
                 newPrimaryDemand[i,j] = max((lowCarbonPrimary[0:,j] * (subCustomers[i]/sum(subCustomers))) + baseDemand[0:,i])/subRating[i]
             else:
                 newPrimaryDemand[i,j] = min((lowCarbonPrimary[0:,j] * (subCustomers[i]/sum(subCustomers))) + baseDemand[0:,i])/subRating[i]


        day=1
        if storageSmall[storageSmall.shape[0]-1] == 0:
            demandWithESPrimary = np.zeros(day*24)
            mainPri = (((subRating[np.argmax(subRating)] / sum(subRating)) * lowCarbonPrimary[0:,22]))[0:24]
            demandWithES = mainPri
        else:
            demandWithESPrimaryProxy=np.zeros([24, day])
            bat = (subRating[np.argmax(subRating)] / sum(subRating)) * storageSmall[22]
            mainPri = ((subRating[np.argmax(subRating)] / sum(subRating)) * lowCarbonPrimary[0:,22])
            for i in range(1,(day+1)):
              model, sol, flo, cha, dis, nD = runSolutionBalance(bat, (mainPri[(24*i)-24:(24*i)]))
              demandWithESPrimaryProxy[0:,(i-1)]=nD
        demandWithES=demandWithESPrimaryProxy.reshape((day*24),order='F')



        if max(mainPri[0:day*24]) > abs(min(mainPri[0:day*24])):
            psRatio = max(demandWithES)/max(mainPri[0:day*24])
        else:
            psRatio = abs(min(demandWithES))/abs(min(mainPri[0:day*24]))

        if psRatio != 1:
            for i in range(0, newPrimaryDemand.shape[0]):
                for j in range(0, newPrimaryDemand.shape[1]):
                    newPrimaryDemand[i,j] = newPrimaryDemand[i,j] * 1 - ((storageSmall[j]/storageSmall[22]) * (1-psRatio))




    #Sum up GSP Flows
    if supplyPoint > 77:
        lowCarbonGSP = ((lowCarbonPrimary*psRatio) - windLargeTotal - pvLargeTotal)
    else:
        lowCarbonGSP = (lowCarbonPrimary - windLargeTotal - pvLargeTotal)

    day = 1
    gspBase = gspDemand(supplyPoint, m, d)
    gspBaseData=np.zeros(len(gspBase))
    gspBaseData[0:]=gspBase[0:].as_matrix()
    statGSP = process_data_normal((gspStats.objects.filter(index=supplyPoint)), gspStats, 16)
    firm = statGSP[0,1]
    gspName=GSP.objects.get(idx=supplyPoint)

    newGSPDemand =  np.zeros([lowCarbonGSP.shape[0], lowCarbonGSP.shape[1]])
    peakGSP = np.zeros(lowCarbonGSP.shape[1])
    for i in range(0, lowCarbonGSP.shape[1]):
        newGSPDemand[0:,i] = gspBaseData + lowCarbonGSP[0:,i]
        if max(newGSPDemand[0:,i]) > abs(min(newGSPDemand[0:,i])):
            peakGSP[i] = max(newGSPDemand[0:,i])/firm
        else: 
            peakGSP[i] = min(newGSPDemand[0:,i])/firm

    if storageLarge[storageLarge.shape[0]-1] == 0:
        gsp40 = newGSPDemand[0:,22]
        demandWithESGSP = gsp40[0:day*24]
    else:
        demandWithESGSPProxy = np.zeros([24, day])
        bat = storageLarge[22]
        gsp40 = newGSPDemand[0:,22]
        model, sol, flo, cha, dis, nD = runSolutionBalance(bat, gsp40[0:day*24])
        demandWithESGSP = nD


    if max(gsp40[0:day*24]) > abs(min(gsp40[0:day*24])):
        gspRatio = max(demandWithESGSP)/max(gsp40[0:day*24])
    else:
        gspRatio = abs(min(demandWithESGSP)) /abs(min(gsp40[0:day*24]))

    if gspRatio != 1:
        for i in range(0, peakGSP.shape[0]):
            peakGSP[i] = peakGSP[i] * 1 - (storageLarge[i]/storageLarge[22]) * (1-gspRatio)



    #Process and Send Data to client

    newYears =list(range(2018, 2041))
    years=list(range(0, len(newYears)))
    for x in range(0, len(newYears)):
         years[x]=str(newYears[x])

    if supplyPoint > 77:
        newP=np.transpose(newPrimaryDemand)

        dataSend=list(range(newP.shape[0]))
        dataSend[0] = list(subNames)

        dataSend=pd.DataFrame(np.zeros([24,(newP.shape[1]+2)]))
        dataSend.iloc[0,0] = 'Year'
        dataSend.iloc[0,1:(newP.shape[1]+1)]=list(subNames)
        dataSend.iloc[0, (newP.shape[1]+1)] = 'GSP'

        dataSend.iloc[1:24, 0]=years

        for i in range(0, newP.shape[0]):
            dataSend.iloc[i+1, 1:(newP.shape[1]+1)] = newP[i,0:]

        dataSend.iloc[1:, (newP.shape[1]+1)] = peakGSP

        dictdata = (dataSend.as_matrix().tolist())

        dataForTable = pd.DataFrame(np.zeros([newP.shape[1]+2, 5]))
        dataForTable.iloc[0,0:] = ['Substation Name', 'Firm Rating (MVA)', 'Require Upgrade', 'Year of Required Upgrade', '2040 Peak Demand (MW)']
        dataForTable.iloc[2:newP.shape[1]+2, 0] = subNames
        dataForTable.iloc[2:newP.shape[1]+2, 1] = subRating




        for i in range(0, newP.shape[1]):
             if any(newP[0:,i] > 1) == True or any(newP[0:,i] < -1) == True:
                     dataForTable.iloc[i+2, 2] = 'Yes'
                     if max((lowCarbonPrimary[0:,j] * (subCustomers[i]/sum(subCustomers))) + baseDemand[0:,i])/subRating[i] > abs(min((lowCarbonPrimary[0:,j] * (subCustomers[i]/sum(subCustomers))) + baseDemand[0:,i])/subRating[i]):
                             dataForTable.iloc[i+2, 3] = str(years[np.where((newP[0:,i] > 1) == True)[0][0]])
                     else:
                             dataForTable.iloc[i+2, 3] = str(years[np.where((newP[0:,i] < -1) == True)[0][0]])
                     dataForTable.iloc[i+2, 4] = newP[newP.shape[0]-1, i] * subRating[i]
             else:
                      dataForTable.iloc[i+2, 2] = 'No'
                      dataForTable.iloc[i+2, 3] = 'N/A'
                      dataForTable.iloc[i+2, 4] = newP[newP.shape[0]-1, i] * subRating[i]
    else:

        dataSend=pd.DataFrame(np.zeros([24,2]))
        dataSend.iloc[0,0] = 'Year'
        dataSend.iloc[0,1] = 'GSP'
        dataSend.iloc[1:24, 0]=years
        dataSend.iloc[1:,1] = peakGSP
        

        dataForTable = pd.DataFrame(np.zeros([2,5]))
        dataForTable.iloc[0,0:] = ['Substation Name', 'Firm Rating (MVA)', 'Require Upgrade', 'Year of Required Upgrade', '2040 Peak Demand (MW)']
        dataForTable.iloc[1,0] = gspName.name + ' (GSP)'
        dataForTable.iloc[1,1] = int(firm)
        if any(peakGSP > 1) or any(peakGSP < -1):
            dataForTable.iloc[1,2] = 'Yes'
            if max(peakGSP) > abs(min(peakGSP)):
               dataForTable.iloc[1,3] = str(years[np.where((peakGSP > 1) == True)[0][0]])
            else:
               dataForTable.iloc[1,3] = str(years[np.where((peakGSP < -1) == True)[0][0]])
        else:
            dataForTable.iloc[1,2] = 'No'
            dataForTable.iloc[1,3] = 'N/A'

        dataForTable.iloc[1,4] = peakGSP[peakGSP.shape[0]-1]*firm

            
    dictdata = (dataSend.as_matrix().tolist())
    djangotable = dataForTable.as_matrix().tolist()

    demandNumbers = pd.DataFrame(np.zeros([24, 6]))
    demandNumbers.iloc[0,0:] = ['Year', 'Heat Pumps', 'EV', 'Wind', 'PV', 'Storage']
    demandNumbers.iloc[1:24,0] = years
    demandNumbers.iloc[1:24,1] = hp
    demandNumbers.iloc[1:24,2] = ev
    demandNumbers.iloc[1:24,3] = windLarge + windSmall
    demandNumbers.iloc[1:24,4] = pvLarge + pvSmall
    demandNumbers.iloc[1:24,5] = storageLarge + storageSmall
    demN = demandNumbers.as_matrix().tolist()

    t2040 = pd.DataFrame(np.zeros([2, 5]))
    t2040.iloc[0,0:] = ['Heat Pumps', 'EV', 'Wind', 'PV', 'Storage']
    t2040.iloc[1,0] = demandNumbers.iloc[23, 1]
    t2040.iloc[1,1] = demandNumbers.iloc[23, 2]
    t2040.iloc[1,2] = demandNumbers.iloc[23, 3]
    t2040.iloc[1,3] = demandNumbers.iloc[23, 4]
    t2040.iloc[1,4] = demandNumbers.iloc[23, 5]
    table2040 = t2040.as_matrix().tolist()

    
    if scenario == 1:
        scen = 'Community Renewables'
    elif scenario == 2:
        scen = 'Two Degrees'
    elif scenario == 3:
        scen = 'Steady Progression'
    elif scenario == 4:
        scen = 'Consumer Evolution'




    return render(request, 'whole/fes18_plot.html', {'djangodict': json.dumps(dictdata), 'djangotable': json.dumps(djangotable), 'demandnumbers':json.dumps(demN) ,'table2040': json.dumps(table2040),'gspName': gspName.name, 'scenario':scen})







    
