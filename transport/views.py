from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse
from django.views.generic.list import ListView
import csv
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm

#model/view imports
from . models import Journey
from . models import gspLocalAuthority
from heat.models import GSP
from electrical.models import electricalGSP
from heat.views import processData
from heat.views import format_inputs
from heat.views import month
from transport . transportFunctions import *
from transport . RunTransportModel import *
from transport . Vehicle import *
from whole.models import gspStats
from electricHeat.views import process_data_normal

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
def transport_input_form(request):
    return render(request, 'transport/transport_input_form.html')

@login_required(login_url='/login/')
def input_form_ev_only(request):
    return render(request, 'transport/input_form_ev_only.html')

@login_required(login_url='/login/')
def input_form_ev_compare(request):
    return render(request, 'transport/input_form_ev_compare.html')


def data_charge_demand(request):
    supplyPoint=request.GET['supplyPoint']
    m=int(request.GET['month'])
    d=request.GET['days']

    gspNameProxy=GSP.objects.get(idx=supplyPoint)
    gspName=GSP.objects.filter(idx=supplyPoint)
    na0 = ([p.name for p in gspName])
    gspAuthority=gspLocalAuthority.objects.filter(gsp=na0[0])
    na1 = ([p.localAuthority for p in gspAuthority])
    
    mediumEV=request.GET['mediumEV']
    smallEV=request.GET['smallEV']
    geographicArea=int(request.GET['geographicArea'])

    if geographicArea == 1:
        gA = 'Urban'
    else:
        gA = 'Rural'
    


    if d =='':
        d=int(0)
    else:
        d = int(d)

    if m == 13:
        d=366

    if mediumEV =='':
        mediumEV=int(0)
    else:
        mediumEV=int(mediumEV)

    if smallEV == '':
        smallEV=int(0)
    else:
        smallEV=int(smallEV)


    #electricalData = process_data((electricalGSP.objects.filter(GSP = supplyPoint)), electricalGSP, 3)
    jobElectricalData = process_data.delay((electricalGSP.objects.filter(GSP = supplyPoint)), electricalGSP, 3)
    electricalData= jobElectricalData.perform()

    #chargeDataSmall = process_data((Journey.objects.filter(localAuthority=na1[0], Area=gA, typeEV='Economy')), Journey,7)
    jobChargeDataSmall = process_data.delay((Journey.objects.filter(localAuthority=na1[0], Area=gA, typeEV='Economy')), Journey,7)
    chargeDataSmall = jobChargeDataSmall.perform()

    #chargeDataMedium = process_data((Journey.objects.filter(localAuthority=na1[0], Area=gA, typeEV='Midsize')), Journey, 7)
    jobChargeDataMedium = process_data.delay((Journey.objects.filter(localAuthority=na1[0], Area=gA, typeEV='Midsize')), Journey, 7)
    chargeDataMedium =jobChargeDataMedium.perform()

    # good to here
    electricalData=electricalData[0:,2]/2
    chargeDataSmall = chargeDataSmall[0:,0:4]
    chargeDataMedium = chargeDataMedium[0:,0:4]

    #profileSmall=formatChargeDemand(smallEV, chargeDataSmall, 'Economy',d)
    jobProfileSmall=formatChargeDemand.delay(smallEV, chargeDataSmall, 'Economy',d)
    profileSmall=jobProfileSmall.perform()

    #profileMedium=formatChargeDemand(mediumEV, chargeDataMedium, 'Midsize',d)
    jobProfileMedium=formatChargeDemand.delay(mediumEV, chargeDataMedium, 'Midsize',d)
    profileMedium=jobProfileMedium.perform()

    profileTotal = np.zeros([len(profileSmall),1])
    profileTotal[0:,0]=(profileSmall['Charge'].as_matrix() + profileMedium['Charge'].as_matrix())/1000

    dS=pd.date_range(start='2015-04-01', end='2016-04-01', freq='H')
    proData=pd.DataFrame({'Time':dS[0:8784], 'Data':electricalData})
    data=proData.set_index('Time')
    d1, d2, S = month(m, data)
    
    S = S.reset_index()
    columnsTitles=["Time","Data"]
    proData=S.reindex(columns=columnsTitles)
    base=np.zeros([(24*d),1])
    base[0:,0]=proData.iloc[0:(24*d),1]
    newData = base+profileTotal
    inter = np.append(profileTotal, newData,1)
    finalData = np.append(proData.iloc[0:(24*d)], inter, 1)
    
    ####
    if geographicArea==1:
        file=gspNameProxy.name+'_'+str(mediumEV)+"_MidsizeEV"+'_'+str(smallEV)+"_SmallEV_Urban.csv"
    else:
        file=gspNameProxy.name+'_'+str(mediumEV)+"_MidsizeEV"+'_'+str(smallEV)+"_SmallEV_Rural.csv"
        
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s"' % file
    
    writer = csv.writer(response)
    
    with open('charge_demand.csv','w') as csvfile:
        writer.writerow(['', 'Base GSP Demand (MWh)', 'EV Charging Demand (MWh)', 'Future GSP Demand (MWh)'])
        #writer.writerow([''])
        for i in range(0,len(finalData)):
            writer.writerow(finalData[i,0:])
    
    return response










def plot_charge_demand(request):

    supplyPoint=request.GET['supplyPoint']
    m=int(request.GET['month'])
    d=request.GET['days']
    
    gspName=GSP.objects.filter(idx=supplyPoint)
    na0 = ([p.name for p in gspName])
    gspAuthority=gspLocalAuthority.objects.filter(gsp=na0[0])
    na1 = ([p.localAuthority for p in gspAuthority])
    
    mediumEV=request.GET['mediumEV']
    smallEV=request.GET['smallEV']
    geographicArea=int(request.GET['geographicArea'])

    if geographicArea == 1:
        gA = 'Urban'
    else:
        gA = 'Rural'
    


    if d =='':
        d=int(0)
    else:
        d = int(d)

    if m == 13:
        d=366

    if mediumEV =='':
        mediumEV=int(0)
    else:
        mediumEV=int(mediumEV)

    if smallEV == '':
        smallEV=int(0)
    else:
        smallEV=int(smallEV)


    electricalData = process_data((electricalGSP.objects.filter(GSP = supplyPoint)), electricalGSP, 3)
    chargeDataSmall = process_data((Journey.objects.filter(localAuthority=na1[0], Area=gA, typeEV='Economy')), Journey,7)
    chargeDataMedium = process_data((Journey.objects.filter(localAuthority=na1[0], Area=gA, typeEV='Midsize')), Journey, 7)

    # good to here
    electricalData=electricalData[0:,2]/2
    chargeDataSmall = chargeDataSmall[0:,0:4]
    chargeDataMedium = chargeDataMedium[0:,0:4]

    profileSmall=formatChargeDemand(smallEV, chargeDataSmall, 'Economy',d)
    profileMedium=formatChargeDemand(mediumEV, chargeDataMedium, 'Midsize',d)

    profileTotal = np.zeros([len(profileSmall),1])
    profileTotal[0:,0]=(profileSmall['Charge'].as_matrix() + profileMedium['Charge'].as_matrix())/1000

    dS=pd.date_range(start='2015-04-01', end='2016-04-01', freq='H')
    proData=pd.DataFrame({'Time':dS[0:8784], 'Data':electricalData})
    data=proData.set_index('Time')
    d1, d2, S = month(m, data)    


    elec=S['Data']
    baseData=np.zeros([(24*d),1])
    baseData[0:,0]=elec.iloc[0:(24*d)]

    newData = baseData + profileTotal

    fmax=max(baseData)[0]
    newDemandMax=max(newData)[0]
    fMax=round(fmax, 2)
    newDemandMax = round(newDemandMax, 2)
    
    statHP = process_data_normal((gspStats.objects.filter(index=supplyPoint)), gspStats, 16)
    rating=statHP[0,1]   

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
    delta = datetime.timedelta(hours=1)
    dates = drange(d1, d2, delta)
    finalDates=dates[0:(24*d)]
    fig, ax =plt.subplots()

    ax.plot_date(finalDates,baseData,linestyle='-', marker='None')
    ax.plot_date(finalDates,newData,linestyle='-', marker='None')
    ax.xaxis.set_major_formatter(formatter)
    ax.xaxis.set_major_locator(loc)
    plt.ylabel('Electrical Demand (MWh)')
    plt.grid(True)
    

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
    return render(request, 'transport/show_plot.html', {'graphic':graphic, 'fMax':fMax, 'newDemandMax': newDemandMax, 'rating': rating})

def plot_ev_demand(request):
    
    supplyPoint=request.GET['supplyPoint']
    m=int(request.GET['month'])
    d=request.GET['days']
    
    gspName=GSP.objects.filter(idx=supplyPoint)
    na0 = ([p.name for p in gspName])
    gspAuthority=gspLocalAuthority.objects.filter(gsp=na0[0])
    na1 = ([p.localAuthority for p in gspAuthority])
    
    mediumEV=request.GET['mediumEV']
    smallEV=request.GET['smallEV']
    geographicArea=int(request.GET['geographicArea'])

    if geographicArea == 1:
        gA = 'Urban'
    else:
        gA = 'Rural'
    


    if d =='':
        d=int(0)
    else:
        d = int(d)

    if m == 13:
        d=366

    if mediumEV =='':
        mediumEV=int(0)
    else:
        mediumEV=int(mediumEV)

    if smallEV == '':
        smallEV=int(0)
    else:
        smallEV=int(smallEV)


    electricalData = process_data((electricalGSP.objects.filter(GSP = supplyPoint)), electricalGSP, 3)
    chargeDataSmall = process_data((Journey.objects.filter(localAuthority=na1[0], Area=gA, typeEV='Economy')), Journey,7)
    chargeDataMedium = process_data((Journey.objects.filter(localAuthority=na1[0], Area=gA, typeEV='Midsize')), Journey, 7)

    # good to here
    electricalData=electricalData[0:,2]/2
    chargeDataSmall = chargeDataSmall[0:,0:4]
    chargeDataMedium = chargeDataMedium[0:,0:4]

    profileSmall=formatChargeDemand(smallEV, chargeDataSmall, 'Economy',d)
    profileMedium=formatChargeDemand(mediumEV, chargeDataMedium, 'Midsize',d)

    profileTotal = np.zeros([len(profileSmall),1])
    profileTotal[0:,0]=(profileSmall['Charge'].as_matrix() + profileMedium['Charge'].as_matrix())

    dS=pd.date_range(start='2015-04-01', end='2016-04-01', freq='H')
    proData=pd.DataFrame({'Time':dS[0:8784], 'Data':electricalData})
    data=proData.set_index('Time')
    d1, d2, S = month(m, data)    


    elec=S['Data']
    baseData=np.zeros([(24*d),1])
    baseData[0:,0]=elec.iloc[0:(24*d)]

    newData = baseData + profileTotal

    pC=max(profileTotal)[0]
    peakCharge=round(pC, 2)

    
    

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
    delta = datetime.timedelta(hours=1)
    dates = drange(d1, d2, delta)
    finalDates=dates[0:(24*d)]
    fig, ax =plt.subplots()

    ax.plot_date(finalDates,profileTotal,linestyle='-', marker='None')
    ax.xaxis.set_major_formatter(formatter)
    ax.xaxis.set_major_locator(loc)
    plt.ylabel('Charging Demand (kWh)')
    plt.grid(True)
    

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
    return render(request, 'transport/show_plot_ev.html', {'graphic':graphic, 'peakCharge':peakCharge})

def plot_ev_demand_compare(request):

   
    supplyPoint=request.GET['supplyPoint']
    supplyPoint2=request.GET['supplyPoint2']
    m=int(request.GET['month'])
    d=request.GET['days']
    
    gspName=GSP.objects.filter(idx=supplyPoint)
    na0 = ([p.name for p in gspName])
    gspAuthority=gspLocalAuthority.objects.filter(gsp=na0[0])
    na1 = ([p.localAuthority for p in gspAuthority])

    gspName2=GSP.objects.filter(idx=supplyPoint2)
    na0_2 = ([p.name for p in gspName2])
    gspAuthority2 = gspLocalAuthority.objects.filter(gsp=na0_2[0])
    na1_2 = ([p.localAuthority for p in gspAuthority2])
    
    mediumEV=request.GET['mediumEV']
    smallEV=request.GET['smallEV']
    geographicArea=int(request.GET['geographicArea'])

    if geographicArea == 1:
        gA = 'Urban'
    else:
        gA = 'Rural'
    

    if d =='':
        d=int(0)
    else:
        d = int(d)

    if m == 13:
        d=366

    if mediumEV =='':
        mediumEV=int(0)
    else:
        mediumEV=int(mediumEV)

    if smallEV == '':
        smallEV=int(0)
    else:
        smallEV=int(smallEV)
    


    electricalData = process_data((electricalGSP.objects.filter(GSP = supplyPoint)), electricalGSP, 3)
    chargeDataSmall = process_data((Journey.objects.filter(localAuthority=na1[0], Area=gA, typeEV='Economy')), Journey,7)
    chargeDataMedium = process_data((Journey.objects.filter(localAuthority=na1[0], Area=gA, typeEV='Midsize')), Journey, 7)

    electricalData2 = process_data((electricalGSP.objects.filter(GSP = supplyPoint2)), electricalGSP, 3)
    chargeDataSmall2 = process_data((Journey.objects.filter(localAuthority=na1_2[0], Area=gA, typeEV='Economy')), Journey,7)
    chargeDataMedium2 = process_data((Journey.objects.filter(localAuthority=na1_2[0], Area=gA, typeEV='Midsize')), Journey, 7)

    ###
    electricalData=electricalData[0:,2]/2
    chargeDataSmall = chargeDataSmall[0:,0:4]
    chargeDataMedium = chargeDataMedium[0:,0:4]

    profileSmall=formatChargeDemand(smallEV, chargeDataSmall, 'Economy',d)
    profileMedium=formatChargeDemand(mediumEV, chargeDataMedium, 'Midsize',d)

    profileTotal = np.zeros([len(profileSmall),1])
    profileTotal[0:,0]=(profileSmall['Charge'].as_matrix() + profileMedium['Charge'].as_matrix())

    

    dS=pd.date_range(start='2015-04-01', end='2016-04-01', freq='H')
    proData=pd.DataFrame({'Time':dS[0:8784], 'Data':electricalData})
    data=proData.set_index('Time')
    d1, d2, S = month(m, data)    


    elec=S['Data']

    pC=max(profileTotal)[0]
    peakCharge=round(pC, 2)

    ###
    electricalData2=electricalData2[0:,2]/2
    chargeDataSmall2 = chargeDataSmall2[0:,0:4]
    chargeDataMedium2 = chargeDataMedium2[0:,0:4]

    profileSmall2=formatChargeDemand(smallEV, chargeDataSmall2, 'Economy',d)
    profileMedium2=formatChargeDemand(mediumEV, chargeDataMedium2, 'Midsize',d)

    profileTotal2 = np.zeros([len(profileSmall),1])
    profileTotal2[0:,0]=(profileSmall2['Charge'].as_matrix() + profileMedium2['Charge'].as_matrix())


    pC2=max(profileTotal2)[0]
    peakCharge2=round(pC2, 2)
    ###

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
    delta = datetime.timedelta(hours=1)
    dates = drange(d1, d2, delta)
    finalDates=dates[0:(24*d)]
    fig, ax =plt.subplots()

    ax.plot_date(finalDates,profileTotal,linestyle='-', marker='None', label=na0[0])
    ax.plot_date(finalDates, profileTotal2, linestyle='-', marker='None', label=na0_2[0])
    ax.xaxis.set_major_formatter(formatter)
    ax.xaxis.set_major_locator(loc)
    plt.ylabel('Charging Demand (kWh)')
    plt.grid(True)
    plt.legend()
    

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
    return render(request, 'transport/show_plot_ev_compare.html', {'graphic':graphic, 'name':na0[0], 'name2':na0_2[0], 'peakCharge':peakCharge,'peakCharge2':peakCharge2})    


def process_data(data, table, dim):

    vlqs = data.values_list()
    r = np.core.records.fromrecords(vlqs, names=[f.name for f in table._meta.fields])
    l=np.array(r)
    process = pd.DataFrame(index=range(len(l)), columns=range(dim)).as_matrix()             

    for i in range(0,len(process)): # extract the information we need for inputs.
        change = l[i]
        for j in range(1,(dim+1)):
            process[i,(j-1)] = change[j]

    return process
    
