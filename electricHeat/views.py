from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse
from django.views.generic.list import ListView
import csv
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm

#model/view imports
from heat.models import Family
from heat.models import GSP
from heat.models import industrialHeat
from heat.views import processData, format_inputs, month
from electricHeat.storageHeater import *
from electrical.models import electricalGSP
from generation.views import extract_weather
from generation.models import Weather
from generation . interpolateLatLon import *
from generation . formatWeather import *
from whole.models import gspStats

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

# Create your views here.

@login_required(login_url='/login/')
def storage_heater_input_form(request):
    return render(request, 'electricHeat/storage_heater_input_form.html')

@login_required(login_url='/login/')
def industrial_electric_input_form(request):
    return render(request, 'electricHeat/industrial_electric_input_form.html')

def storage_heater_plot(request):

    #get user input data from browser
    small = request.GET['small']
    medium = request.GET['medium']
    large = request.GET['large']
    smallHP = request.GET['smallHP']
    mediumHP = request.GET['mediumHP']
    largeHP = request.GET['largeHP']
    supplyPoint=request.GET['supplyPoint']
    m = int(request.GET['month'])
    d = request.GET['days']
    gspName=GSP.objects.get(idx=supplyPoint)

    if small == '':
        small = int(0)
    else:
        small = int(small)

    if smallHP == '':
        smallHP = int(0)
    else:
        smallHP = int(smallHP)

    if medium == '':
        medium = int(0)
    else:
        medium = int(medium)

    if mediumHP == '':
        mediumHP = int(0)
    else:
        mediumHP = int(mediumHP)

    if large == '':
        large = int(0)
    else:
        large = int(large)

    if largeHP == '':
        largeHP = int(0)
    else:
        largeHP = int(largeHP)

    if d =='':
        d=int(0)
    else:
        d = int(d)
    
    if m==3 and d>30:
        d=30
    
    if m==13:
        d=365

    ##
    h40 = small/2
    h60 = small/2
    h100 = medium/2
    h140 = medium/2
    h160 = large

    if isinstance(h40, float):
        h40 = h40 + 0.5
        h60 = h60 - 0.5

    if isinstance(h100, float):
        h100 = h100 + 0.5
        h140 = h140 - 0.5        
        
    numSmall=h40+h60
    numMedium=h100+h140
    numLarge=h160
    ##

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
    hourSmall, totalDemandSmall = format_inputs(rawData, h40, h60, 0, 0, 0) # output in Watts
    hourMedium, totalDemandMedium = format_inputs(rawData, 0, 0, h100, h140, 0)
    hourLarge, totalDemandLarge = format_inputs(rawData, 0, 0, 0, 0, h160)


    # add time element to data
    dS=pd.date_range(start='2015-04-01', end='2016-04-01', freq='H')

    ##small sized property##

    proDataSmall=pd.DataFrame({'Time':dS[0:8784], 'Data':(totalDemandSmall/1000)})
    dataSmall=proDataSmall.set_index('Time')
    d1, d2, smallS = month(m, dataSmall)
    reSmall = pd.DataFrame(smallS['Data'], index=smallS.index)
    reSmall.columns=['Demand']
    finalDataSmall = reSmall.iloc[0:(24*d)]
    chargeSmall=np.zeros(d*24)
    indSmall= finalDataSmall/numSmall

    if numSmall != 0:
        for i in range(1, (d+1)):
            intraSmall= pd.DataFrame(indSmall.iloc[((24*i)-24):(24*i),0].as_matrix(), index=list(range(0, 24)), columns=['Demand'])
            if i==1:
                chg, chT, gone= storageHeater(intraSmall,  'Small', (19.3*0.2))
                chargeSmall[((24*i)-24):(24*i)] = chT.iloc[0:,0].as_matrix()
            else:
                chg, chT, gone= storageHeater(intraSmall,  'Small', (19.3*gone[0]) )
                chargeSmall[((24*i)-24):(24*i)] = chT.iloc[0:,0].as_matrix()
        smallChargeTotal = chargeSmall*numSmall
    else:
        smallChargeTotal = np.zeros(d*24)



    ##medium sized property##

    proDataMedium=pd.DataFrame({'Time':dS[0:8784], 'Data':(totalDemandMedium/1000)})
    dataMedium=proDataMedium.set_index('Time')
    d1, d2, mediumS = month(m, dataMedium)
    reMedium = pd.DataFrame(mediumS['Data'], index=mediumS.index)
    reMedium.columns=['Demand']
    finalDataMedium = reMedium.iloc[0:(24*d)]
    chargeMedium=np.zeros(d*24)
    indMedium= finalDataMedium/numMedium

    if numMedium != 0:
        for i in range(1, (d+1)):
            intraMedium= pd.DataFrame(indMedium.iloc[((24*i)-24):(24*i),0].as_matrix(), index=list(range(0, 24)), columns=['Demand'])
            if i==1:
                chg, chT, gone= storageHeater(intraMedium,  'Medium', (19.3*0.2))
                chargeMedium[((24*i)-24):(24*i)] = chT.iloc[0:,0].as_matrix()
            else:
                chg, chT, gone= storageHeater(intraMedium,  'Medium', (19.3*gone[0]) )
                chargeMedium[((24*i)-24):(24*i)] = chT.iloc[0:,0].as_matrix()    

        mediumChargeTotal = chargeMedium*numMedium
    else:
        mediumChargeTotal = np.zeros(d*24)
    
        

    ##Large sized property##
    proDataLarge=pd.DataFrame({'Time':dS[0:8784], 'Data':(totalDemandLarge/1000)})
    dataLarge=proDataLarge.set_index('Time')
    d1, d2, largeS = month(m, dataLarge)
    reLarge = pd.DataFrame(largeS['Data'], index=largeS.index)
    reLarge.columns=['Demand']
    finalDataLarge = reLarge.iloc[0:(24*d)]
    chargeLarge=np.zeros(d*24)
    indLarge= finalDataLarge/numLarge

    if numLarge != 0:
        for i in range(1, (d+1)):
            intraLarge= pd.DataFrame(indLarge.iloc[((24*i)-24):(24*i),0].as_matrix(), index=list(range(0, 24)), columns=['Demand'])
            if i==1:
                chg, chT, gone= storageHeater(intraLarge,  'Large', (23.1*0.2))
                chargeLarge[((24*i)-24):(24*i)] = chT.iloc[0:,0].as_matrix()
            else:
                chg, chT, gone= storageHeater(intraLarge,  'Large', (23.1*gone[0]) )
                chargeLarge[((24*i)-24):(24*i)] = chT.iloc[0:,0].as_matrix()   
        
        largeChargeTotal = chargeLarge*numLarge
    else:
        largeChargeTotal = np.zeros(d*24)

        
    ###########################################################################################################
    ##heat pumps
    hourSmallHP, totalDemandSmallHP = format_inputs(rawData, h40HP, h60HP, 0, 0, 0)
    hourMediumHP, totalDemandMediumHP = format_inputs(rawData, 0, 0, h100HP, h140HP, 0)
    hourLargeHP, totalDemandLargeHP = format_inputs(rawData, 0, 0, 0, 0, h160HP)

    statHP = process_data_normal((gspStats.objects.filter(index=supplyPoint)), gspStats, 16)
    firm=statHP[0,1]
    latitude=statHP[0,2]
    longitude=statHP[0,3]
    tmy_data, altitude = extract_weather(d,m, latitude, longitude)
    temp=tmy_data['DryBulb']


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










    #############################################################################################################   
    electricalData = process_data_normal((electricalGSP.objects.filter(GSP = supplyPoint)), electricalGSP, 3)
    electricalData=electricalData[0:,2]/2
    dS=pd.date_range(start='2015-04-01', end='2016-04-01', freq='H')
    proData=pd.DataFrame({'Time':dS[0:8784], 'Data':electricalData})
    data=proData.set_index('Time')
    d1, d2, S = month(m, data)    
    elec=S['Data']
    elec=elec.iloc[0:(24*d)]

    totCharge = (smallChargeTotal[0:]/1000) + (mediumChargeTotal[0:]/1000) + (largeChargeTotal[0:]/1000 + smallHPTotal[0:]/1000 + mediumHPTotal[0:]/1000 + largeHPTotal[0:]/1000)

##    if m==13:
##        totChargeNew=np.zeros(366*24)
##        totChargeNew[0:(365*24)]=totCharge
##        totChargeNew[(365*24):(366*24)]=totCharge[(364*24):(365*24)]
        
    elecChange =  pd.DataFrame( (elec + totCharge), index=elec.index)
    rating=np.zeros(d*24)
    rating[0:]=firm

    peakChargeProxy=max(totCharge)*1000
    peakCharge=round(peakChargeProxy)

    if max(elec.as_matrix()) > abs(min(elec.as_matrix())):
        maxGSP_proxy=max(elec.as_matrix())
    else:
        maxGSP_proxy=min(elec.as_matrix())

    maxGSP=round(maxGSP_proxy,2)

    if max((elec + totCharge).as_matrix()) > abs(min((elec + totCharge).as_matrix())):
        maxGSPNew_proxy=max((elec + totCharge).as_matrix())
    else:
        maxGSPNew_proxy=min((elec + totCharge).as_matrix())


    maxGSPNew=round(maxGSPNew_proxy,2)
    
    

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
    title = str(int(numSmall + numMedium + numLarge)) + ' Homes with Storage Heaters \n' + str(int(numSmallHP + numMediumHP + numLargeHP)) + ' Homes with Heat Pumps'
    if max(totCharge > 1):
        ax.plot_date(elec.index, totCharge, linestyle='-', marker='None')
        plt.ylabel('Electrical Demand (MWh)')
    else:
        ax.plot_date(elec.index, totCharge*(1000), linestyle='-', marker='None')
        plt.ylabel('Electrical Demand (kWh)')
    ax.xaxis.set_major_formatter(formatter)
    ax.xaxis.set_major_locator(loc)
    plt.grid(True)
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

    fig2, ax2=plt.subplots()
    ax2.plot_date(elec.index, (elec.iloc[0:].as_matrix()), linestyle='-', marker='None' , label='Base Demand')
    ax2.plot_date(elecChange.index, (elecChange.iloc[0:,0].as_matrix()), linestyle='-', marker='None', label='New Demand')
    ax2.xaxis.set_major_formatter(formatter)
    ax2.xaxis.set_major_locator(loc)
    ax2.legend()
    plt.grid(True)
    plt.ylabel('Electrical Demand (MWh)')
    plt.title(gspName.name + ' GSP Demand')

    buffer2 = BytesIO()
    canvas2 = pylab.get_current_fig_manager().canvas
    canvas2.draw()
    pilImage2 = PIL.Image.frombytes("RGB", canvas2.get_width_height(), canvas2.tostring_rgb())
    pilImage2.save(buffer2, "PNG")
    pylab.close()

    image_png2 = buffer2.getvalue()
    graphic2 = base64.b64encode(image_png2)
    graphic2 = graphic2.decode('utf-8')



    return render(request, 'electricHeat/show_plot.html',{'graphic':graphic, 'graphic2':graphic2, 'firm':firm, 'peakCharge':peakCharge, 'maxGSP':maxGSP, 'maxGSPNew': maxGSPNew})


############################################################



def storage_heater_data(request):

    #get user input data from browser
    small = request.GET['small']
    medium = request.GET['medium']
    large = request.GET['large']
    smallHP = request.GET['smallHP']
    mediumHP = request.GET['mediumHP']
    largeHP = request.GET['largeHP']
    supplyPoint=request.GET['supplyPoint']
    m = int(request.GET['month'])
    d = request.GET['days']
    gspName=GSP.objects.get(idx=supplyPoint)

    if small == '':
        small = int(0)
    else:
        small = int(small)

    if smallHP == '':
        smallHP = int(0)
    else:
        smallHP = int(smallHP)

    if medium == '':
        medium = int(0)
    else:
        medium = int(medium)

    if mediumHP == '':
        mediumHP = int(0)
    else:
        mediumHP = int(mediumHP)

    if large == '':
        large = int(0)
    else:
        large = int(large)

    if largeHP == '':
        largeHP = int(0)
    else:
        largeHP = int(largeHP)

    if d =='':
        d=int(0)
    else:
        d = int(d)
    
    if m==13:
        d=366

    ##
    h40 = small/2
    h60 = small/2
    h100 = medium/2
    h140 = medium/2
    h160 = large

    if isinstance(h40, float):
        h40 = h40 + 0.5
        h60 = h60 - 0.5

    if isinstance(h100, float):
        h100 = h100 + 0.5
        h140 = h140 - 0.5        
        
    numSmall=h40+h60
    numMedium=h100+h140
    numLarge=h160
    ##

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
    hourSmall, totalDemandSmall = format_inputs(rawData, h40, h60, 0, 0, 0) # output in Watts
    hourMedium, totalDemandMedium = format_inputs(rawData, 0, 0, h100, h140, 0)
    hourLarge, totalDemandLarge = format_inputs(rawData, 0, 0, 0, 0, h160)


    # add time element to data
    dS=pd.date_range(start='2015-04-01', end='2016-04-01', freq='H')

    ##small sized property##

    proDataSmall=pd.DataFrame({'Time':dS[0:8784], 'Data':(totalDemandSmall/1000)})
    dataSmall=proDataSmall.set_index('Time')
    d1, d2, smallS = month(m, dataSmall)
    reSmall = pd.DataFrame(smallS['Data'], index=smallS.index)
    reSmall.columns=['Demand']
    finalDataSmall = reSmall.iloc[0:(24*d)]
    chargeSmall=np.zeros(d*24)
    indSmall= finalDataSmall/numSmall

    if numSmall != 0:
        for i in range(1, (d+1)):
            intraSmall= pd.DataFrame(indSmall.iloc[((24*i)-24):(24*i),0].as_matrix(), index=list(range(0, 24)), columns=['Demand'])
            if i==1:
                chg, chT, gone= storageHeater(intraSmall,  'Small', (19.3*0.2))
                chargeSmall[((24*i)-24):(24*i)] = chT.iloc[0:,0].as_matrix()
            else:
                chg, chT, gone= storageHeater(intraSmall,  'Small', (19.3*gone[0]) )
                chargeSmall[((24*i)-24):(24*i)] = chT.iloc[0:,0].as_matrix()
        smallChargeTotal = chargeSmall*numSmall
    else:
        smallChargeTotal = np.zeros(d*24)



    ##medium sized property##

    proDataMedium=pd.DataFrame({'Time':dS[0:8784], 'Data':(totalDemandMedium/1000)})
    dataMedium=proDataMedium.set_index('Time')
    d1, d2, mediumS = month(m, dataMedium)
    reMedium = pd.DataFrame(mediumS['Data'], index=mediumS.index)
    reMedium.columns=['Demand']
    finalDataMedium = reMedium.iloc[0:(24*d)]
    chargeMedium=np.zeros(d*24)
    indMedium= finalDataMedium/numMedium

    if numMedium != 0:
        for i in range(1, (d+1)):
            intraMedium= pd.DataFrame(indMedium.iloc[((24*i)-24):(24*i),0].as_matrix(), index=list(range(0, 24)), columns=['Demand'])
            if i==1:
                chg, chT, gone= storageHeater(intraMedium,  'Medium', (19.3*0.2))
                chargeMedium[((24*i)-24):(24*i)] = chT.iloc[0:,0].as_matrix()
            else:
                chg, chT, gone= storageHeater(intraMedium,  'Medium', (19.3*gone[0]) )
                chargeMedium[((24*i)-24):(24*i)] = chT.iloc[0:,0].as_matrix()    

        mediumChargeTotal = chargeMedium*numMedium
    else:
        mediumChargeTotal = np.zeros(d*24)
    
        

    ##Large sized property##
    proDataLarge=pd.DataFrame({'Time':dS[0:8784], 'Data':(totalDemandLarge/1000)})
    dataLarge=proDataLarge.set_index('Time')
    d1, d2, largeS = month(m, dataLarge)
    reLarge = pd.DataFrame(largeS['Data'], index=largeS.index)
    reLarge.columns=['Demand']
    finalDataLarge = reLarge.iloc[0:(24*d)]
    chargeLarge=np.zeros(d*24)
    indLarge= finalDataLarge/numLarge

    if numLarge != 0:
        for i in range(1, (d+1)):
            intraLarge= pd.DataFrame(indLarge.iloc[((24*i)-24):(24*i),0].as_matrix(), index=list(range(0, 24)), columns=['Demand'])
            if i==1:
                chg, chT, gone= storageHeater(intraLarge,  'Large', (23.1*0.2))
                chargeLarge[((24*i)-24):(24*i)] = chT.iloc[0:,0].as_matrix()
            else:
                chg, chT, gone= storageHeater(intraLarge,  'Large', (23.1*gone[0]) )
                chargeLarge[((24*i)-24):(24*i)] = chT.iloc[0:,0].as_matrix()   
        
        largeChargeTotal = chargeLarge*numLarge
    else:
        largeChargeTotal = np.zeros(d*24)

        
    ###########################################################################################################
    ##heat pumps
    hourSmallHP, totalDemandSmallHP = format_inputs(rawData, h40HP, h60HP, 0, 0, 0)
    hourMediumHP, totalDemandMediumHP = format_inputs(rawData, 0, 0, h100HP, h140HP, 0)
    hourLargeHP, totalDemandLargeHP = format_inputs(rawData, 0, 0, 0, 0, h160HP)

    statHP = process_data_normal((gspStats.objects.filter(index=supplyPoint)), gspStats, 16)
    latitude=statHP[0,2]
    longitude=statHP[0,3]
    tmy_data, altitude = extract_weather(d,m, latitude, longitude)
    temp=tmy_data['DryBulb']


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




    #############################################################################################################   
    electricalData = process_data_normal((electricalGSP.objects.filter(GSP = supplyPoint)), electricalGSP, 3)
    electricalData=electricalData[0:,2]/2
    dS=pd.date_range(start='2015-04-01', end='2016-04-01', freq='H')
    proData=pd.DataFrame({'Time':dS[0:8784], 'Data':electricalData})
    data=proData.set_index('Time')
    d1, d2, S = month(m, data)    
    elec=S['Data']
    elec=elec.iloc[0:(24*d)]

    totCharge = (smallChargeTotal[0:]/1000) + (mediumChargeTotal[0:]/1000) + (largeChargeTotal[0:]/1000 + smallHPTotal[0:]/1000 + mediumHPTotal[0:]/1000 + largeHPTotal[0:]/1000)
    elecChange =  pd.DataFrame( (elec + totCharge), index=elec.index)

    chargeOut = pd.DataFrame(totCharge, index=elec.index)
    finalData = chargeOut.reset_index()

    response = HttpResponse(content_type='text/csv')
    file =gspName.name +'GSP_'+str(int(numSmall + numMedium + numLarge))+'_storage_heaters_'+str(int(numSmallHP + numMediumHP + numLargeHP))+'_heat_pumps.csv'
    response['Content-Disposition'] = 'attachment; filename="%s"' % file

    writer = csv.writer(response)

    with open('pv_generation.csv','w') as csvfile:
        writer.writerow(['', 'Electric Heat Demand(MWh)'])
        for i in range(0,len(finalData)):
            writer.writerow(finalData.iloc[i,0:])
    
    return response
    

    


def industrial_electric_plot(request):
	
    percent = int(request.GET['percent'])
    supplyPoint=request.GET['supplyPoint']
    m = int(request.GET['month'])
    d = request.GET['days']
    gspName=GSP.objects.get(idx=supplyPoint)


    if d =='':
        d=int(0)
    else:
        d = int(d)
    
    if m==3 and d>30:
        d=30
    
    if m==13:
        d=365

    statHP = process_data_normal((gspStats.objects.filter(index=supplyPoint)), gspStats, 16)
    firm=statHP[0,1]
    latitude=statHP[0,2]
    longitude=statHP[0,3]
    tmy_data, altitude = extract_weather(d,m, latitude, longitude)
    temp=tmy_data['DryBulb']

    heatData = industrialHeat.objects.filter(GSP = supplyPoint)

    vlqs = heatData.values_list()
    r = np.core.records.fromrecords(vlqs, names=[f.name for f in industrialHeat._meta.fields])
    l=np.array(r)
    process = np.zeros([len(l),3])
    
    for i in range(0,len(process)): # extract the information we need for inputs.
        change = l[i]
        for j in range(1,4):
            process[i,(j-1)] = change[j]

    g=np.array(process)
    

    dS=pd.date_range(start='2015-04-01', end='2016-04-01', freq='H')
    proData=pd.DataFrame({'Time':dS[0:8784], 'Data':g[0:,2]})
    data=proData.set_index('Time')
    d1, d2, S = month(m, data)

    heat=S['Data']
    totalDemand = heat.iloc[0:(24*d)]
    demandIndustrialHP=np.zeros(d*24)
    
    for i in range(1, (d+1)):
                    demB=(totalDemand.iloc[((24*i)-24):(24*i)].as_matrix()*1e6)*(percent/100)
                    tempB=temp.iloc[((24*i)-24):(24*i)].as_matrix()
                    demIndustrialB=np.zeros(24)
                    for j in range(0,24):
                            demIndustrialB[j] = demB[j] / (tempB[j]*0.04762+3.03283)
                    demandIndustrialHP[((24*i)-24):(24*i)]=demIndustrialB
    
    
    totalHeatPumpIndustrial = demandIndustrialHP/1e6

    electricalData = process_data_normal((electricalGSP.objects.filter(GSP = supplyPoint)), electricalGSP, 3)
    electricalData=electricalData[0:,2]/2
    dS=pd.date_range(start='2015-04-01', end='2016-04-01', freq='H')
    proData=pd.DataFrame({'Time':dS[0:8784], 'Data':electricalData})
    data=proData.set_index('Time')
    d1, d2, S = month(m, data)    
    elec=S['Data']
    elec=elec.iloc[0:(24*d)]
    elecChange =  pd.DataFrame( (elec + totalHeatPumpIndustrial), index=elec.index)

    peakChargeProxy=max(totalHeatPumpIndustrial)
    peakCharge=round(peakChargeProxy,2)

    if max(elec.as_matrix()) > abs(min(elec.as_matrix())):
        maxGSP_proxy=max(elec.as_matrix())
    else:
        maxGSP_proxy=min(elec.as_matrix())

    maxGSP=round(maxGSP_proxy,2)

    if max((elec + totalHeatPumpIndustrial).as_matrix()) > abs(min((elec + totalHeatPumpIndustrial).as_matrix())):
        maxGSPNew_proxy=max((elec + totalHeatPumpIndustrial).as_matrix())
    else:
        maxGSPNew_proxy=min((elec + totalHeatPumpIndustrial).as_matrix())


    maxGSPNew=round(maxGSPNew_proxy,2)
	
    if d == 1:
        formatter = DateFormatter('%H-%M')
        rule = rrulewrapper(HOURLY, interval=6)
    elif d < 4:
        formatter = DateFormatter('%d-%m-%y')
        rule = rrulewrapper(DAILY, interval=1)
    elif d < 10:
         formatter = DateFormatter('%d-%m-%y')
         rule = rrulewrapper(DAILY, interval=2)
    elif d > 9 and d < 16:
        formatter = DateFormatter('%d-%m-%y')
        rule = rrulewrapper(DAILY, interval=3)
    elif d > 15 and d < 32:
        formatter = DateFormatter('%d-%m-%y')
        rule = rrulewrapper(DAILY, interval=5)
    elif d > 31:
        formatter = DateFormatter('%b-%Y')
        rule = rrulewrapper(MONTHLY, interval=3)
        

    loc = RRuleLocator(rule)
    delta = datetime.timedelta(hours=1)
    dates = drange(d1, d2, delta)
    finalDates=dates[0:(24*d)]
    fig, ax =plt.subplots()

    ax.plot_date(finalDates,totalHeatPumpIndustrial, linestyle='-', marker='None', label=gspName.name)
    ax.xaxis.set_major_formatter(formatter)
    ax.xaxis.set_major_locator(loc)
    ax.legend()
    plt.grid(True)
    plt.ylabel('Heat Demand (MWh)')
    plt.title('Industrial Heat Demand Plot for '+ gspName.name + ' GSP')
  
    buffer = BytesIO()
    canvas = pylab.get_current_fig_manager().canvas
    canvas.draw()
    pilImage = PIL.Image.frombytes("RGB", canvas.get_width_height(), canvas.tostring_rgb())
    pilImage.save(buffer, "PNG")
    pylab.close()

    image_png = buffer.getvalue()
    graphic = base64.b64encode(image_png)
    graphic = graphic.decode('utf-8')
    ##
    fig2, ax2=plt.subplots()
    ax2.plot_date(elec.index, (elec.iloc[0:].as_matrix()), linestyle='-', marker='None' , label='Base Demand')
    ax2.plot_date(elecChange.index, (elecChange.iloc[0:,0].as_matrix()), linestyle='-', marker='None', label='New Demand')
    ax2.xaxis.set_major_formatter(formatter)
    ax2.xaxis.set_major_locator(loc)
    ax2.legend()
    plt.grid(True)
    plt.ylabel('Electrical Demand (MWh)')
    plt.title(gspName.name + ' GSP Demand')

    buffer2 = BytesIO()
    canvas2 = pylab.get_current_fig_manager().canvas
    canvas2.draw()
    pilImage2 = PIL.Image.frombytes("RGB", canvas2.get_width_height(), canvas2.tostring_rgb())
    pilImage2.save(buffer2, "PNG")
    pylab.close()

    image_png2 = buffer2.getvalue()
    graphic2 = base64.b64encode(image_png2)
    graphic2 = graphic2.decode('utf-8')
    return render(request, 'electricHeat/show_plot_industrial.html', {'graphic':graphic, 'graphic2':graphic2, 'firm':firm, 'peakCharge':peakCharge, 'maxGSP':maxGSP, 'maxGSPNew': maxGSPNew})
	


def industrial_electric_data(request):

    percent = int(request.GET['percent'])
    supplyPoint=request.GET['supplyPoint']
    m = int(request.GET['month'])
    d = request.GET['days']
    gspName=GSP.objects.get(idx=supplyPoint)


    if d =='':
        d=int(0)
    else:
        d = int(d)
    
    if m==3 and d>30:
        d=30
    
    if m==13:
        d=365

    statHP = process_data_normal((gspStats.objects.filter(index=supplyPoint)), gspStats, 16)
    firm=statHP[0,1]
    latitude=statHP[0,2]
    longitude=statHP[0,3]
    tmy_data, altitude = extract_weather(d,m, latitude, longitude)
    temp=tmy_data['DryBulb']

    heatData = industrialHeat.objects.filter(GSP = supplyPoint)

    vlqs = heatData.values_list()
    r = np.core.records.fromrecords(vlqs, names=[f.name for f in industrialHeat._meta.fields])
    l=np.array(r)
    process = np.zeros([len(l),3])
    
    for i in range(0,len(process)): # extract the information we need for inputs.
        change = l[i]
        for j in range(1,4):
            process[i,(j-1)] = change[j]

    g=np.array(process)
    

    dS=pd.date_range(start='2015-04-01', end='2016-04-01', freq='H')
    proData=pd.DataFrame({'Time':dS[0:8784], 'Data':g[0:,2]})
    data=proData.set_index('Time')
    d1, d2, S = month(m, data)

    heat=S['Data']
    totalDemand = heat.iloc[0:(24*d)]
    demandIndustrialHP=np.zeros(d*24)
    
    for i in range(1, (d+1)):
                    demB=(totalDemand.iloc[((24*i)-24):(24*i)].as_matrix()*1e6)*(percent/100)
                    tempB=temp.iloc[((24*i)-24):(24*i)].as_matrix()
                    demIndustrialB=np.zeros(24)
                    for j in range(0,24):
                            demIndustrialB[j] = demB[j] / (tempB[j]*0.04762+3.03283)
                    demandIndustrialHP[((24*i)-24):(24*i)]=demIndustrialB
    
    
    totalHeatPumpIndustrial = demandIndustrialHP/1e6

    electricalData = process_data_normal((electricalGSP.objects.filter(GSP = supplyPoint)), electricalGSP, 3)
    electricalData=electricalData[0:,2]/2
    dS=pd.date_range(start='2015-04-01', end='2016-04-01', freq='H')
    proData=pd.DataFrame({'Time':dS[0:8784], 'Data':electricalData})
    data=proData.set_index('Time')
    d1, d2, S = month(m, data)    
    elec=S['Data']
    elec=elec.iloc[0:(24*d)]
    elecChange =  pd.DataFrame( (elec + totalHeatPumpIndustrial), index=elec.index)
    dataFinal=np.zeros([(24*d),2])
    dataFinal[0:,0]=totalHeatPumpIndustrial
    dataFinal[0:,1]=elec.as_matrix()+totalHeatPumpIndustrial

    chargeOut = pd.DataFrame(dataFinal, index=elec.index)
    finalData = chargeOut.reset_index()

    response = HttpResponse(content_type='text/csv')
    file =gspName.name +'GSP_'
    response['Content-Disposition'] = 'attachment; filename="%s"' % file

    writer = csv.writer(response)

    with open('pv_generation.csv','w') as csvfile:
        writer.writerow(['', 'Electric Heat Demand(MWh)'])
        for i in range(0,len(finalData)):
            writer.writerow(finalData.iloc[i,0:])
    
    return response
    






def process_data_normal(data, table, dim):

    vlqs = data.values_list()
    r = np.core.records.fromrecords(vlqs, names=[f.name for f in table._meta.fields])
    l=np.array(r)
    process = pd.DataFrame(index=range(len(l)), columns=range(dim)).as_matrix()             

    for i in range(0,len(process)): # extract the information we need for inputs.
        change = l[i]
        for j in range(1,(dim+1)):
            process[i,(j-1)] = change[j]

    return process
