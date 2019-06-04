from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse
from django.views.generic.list import ListView
import csv
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm


#model imports
from heat.models import GSP
from electrical.models import electricalGSP
from heat.views import processData
from heat.views import format_inputs
from heat.views import month
from whole.models import gspStats
from electricHeat.views import process_data_normal

#function imports
from energyStorage.esBalance import esBalance
from energyStorage.esRenewable import esRenewable
from energyStorage.runOptimizer import runSolutionBalance
from energyStorage.runOptimizer import runSolutionCapacity

#numpy pandas & pulp(linear optimizer) library imports
import numpy as np
import pandas as pd
import pulp

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
def storage_form_plot(request):
    return render(request, 'energyStorage/storage_input_form_plot.html')

@login_required(login_url='/login/')
def storage_form_sizing(request):
    return render(request, 'energyStorage/storage_input_form_sizing.html')

def plot_gsp_storage(request):
    supplyPoint=request.GET['supplyPoint']
    m=int(request.GET['month'])
    d=request.GET['days']
    gspName=GSP.objects.get(idx=supplyPoint)
    esCap=int(request.GET['esCap'])

    if d =='':
        d=int(0)
    else:
        d = int(d)

    if m == 13:
        d=366
    
    electricalData = electricalGSP.objects.filter(GSP = supplyPoint)
    vlqs = electricalData.values_list()
    r = np.core.records.fromrecords(vlqs, names=[f.name for f in electricalGSP._meta.fields])
    l=np.array(r)
    process = np.zeros([len(l),3])

    for i in range(0,len(process)): # extract the information we need for inputs.
        change = l[i]
        for j in range(1,4):
            process[i,(j-1)] = change[j]

    g=np.array(process)/2

    dS=pd.date_range(start='2015-04-01', end='2016-04-01', freq='H')
    proData=pd.DataFrame({'Time':dS[0:8784], 'Data':g[0:,2]})
    data=proData.set_index('Time')
    d1, d2, S = month(m, data)

    elec=S['Data']

    fProxy=np.zeros([24, d])
    cProxy=np.zeros([24, d])
    disProxy=np.zeros([24, d])
    newDemandProxy=np.zeros([24, d])
    
    for i in range(1,(d+1)):
        model, sol, flo, cha, dis, nD = runSolutionBalance(esCap, (elec.iloc[(24*i)-24:(24*i)]))
        fProxy[0:,(i-1)]=flo
        cProxy[0:,(i-1)]=cha
        disProxy[0:,(i-1)]=dis
        newDemandProxy[0:,(i-1)]=nD

    f=fProxy.reshape((d*24), order='F')
    c=cProxy.reshape((d*24),order='F')
    dis=disProxy.reshape((d*24),order='F')
    newDemand=newDemandProxy.reshape((d*24),order='F')

    check=all(i > 0 for i in f)

    if np.absolute(np.amax(f)) > np.absolute(np.amin(f)):
        fMax = np.amax(f)
        newDemandMax = np.amax(newDemand)
        peakReduction = 100 - round(((newDemandMax/fMax)*100),2)
        headroom = round((fMax - newDemandMax), 2)

    else:
        fMax = np.amin(f)
        newDemandMax = np.amin(newDemand)
        peakReduction = 100 - round(((newDemandMax/fMax)*100),2)
        headroom = round((newDemandMax- fMax), 2)

    statHP = process_data_normal((gspStats.objects.filter(index=supplyPoint)), gspStats, 16)
    rating=statHP[0,1]
    
    ####Plotting####
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
    elif d > 15:
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

    ax.plot_date(finalDates, f, linestyle='-', marker='None', label='Base Case (no BES)')
    ax.plot(finalDates, newDemand, linestyle='-', marker='None', label='With BES')
    ax.xaxis.set_major_formatter(formatter)
    ax.xaxis.set_major_locator(loc)
    ax.legend()
    plt.ylabel('Electrical Demand (MWh)')
    plt.title('Electrical Demand Plot for '+ gspName.name + ' GSP' + ' with ' + str(esCap)+ ' MWh BES')
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

    return render(request, 'energyStorage/show_plot.html', {'graphic':graphic, 'fMax':fMax, 'newDemandMax': newDemandMax, 'peakReduction':peakReduction,'esCap':esCap, 'headroom':headroom, 'rating':rating})


def sizing_storage(request):
    supplyPoint=request.GET['supplyPoint']
    m=int(request.GET['month'])
    d=request.GET['days']
    gspName=GSP.objects.get(idx=supplyPoint)
    ap=1 -(int(request.GET['demandReduction'])/100)

    if d =='':
        d=int(0)
    else:
        d = int(d)

    if m == 13:
        d=366
    
    electricalData = electricalGSP.objects.filter(GSP = supplyPoint)
    vlqs = electricalData.values_list()
    r = np.core.records.fromrecords(vlqs, names=[f.name for f in electricalGSP._meta.fields])
    l=np.array(r)
    process = np.zeros([len(l),3])

    for i in range(0,len(process)): # extract the information we need for inputs.
        change = l[i]
        for j in range(1,4):
            process[i,(j-1)] = change[j]

    g=np.array(process)/2

    dS=pd.date_range(start='2015-04-01', end='2016-04-01', freq='H')
    proData=pd.DataFrame({'Time':dS[0:8784], 'Data':g[0:,2]})
    data=proData.set_index('Time')
    d1, d2, S = month(m, data)

    elec=S['Data']

    capacityProxy=np.zeros([24, d])
    apProxy=np.zeros([24, d])

    for i in range(1,(d+1)):
        model, sol, capacity, ap = runSolutionCapacity((elec.iloc[(24*i)-24:(24*i)]),ap)
        capacityProxy[0:,(i-1)]=capacity
        apProxy[0:,(i-1)]=ap


    capacityFinal=capacityProxy.reshape((d*24), order='F')
    apFinal=apProxy.reshape((d*24),order='F')

    capacityMax = np.amax(capacityFinal)
    reductionMax = np.amax(apFinal)*100

    return render(request,'energyStorage/sizing_details.html',{'capacityMax':capacityMax, 'reductionMax': reductionMax})

def data_gsp_storage(request):
    supplyPoint=request.GET['supplyPoint']
    m=int(request.GET['month'])
    d=request.GET['days']
    gspName=GSP.objects.get(idx=supplyPoint)
    esCap=int(request.GET['esCap'])

    if d =='':
        d=int(0)
    else:
        d = int(d)

    if m == 13:
        d=366
    
    electricalData = electricalGSP.objects.filter(GSP = supplyPoint)
    vlqs = electricalData.values_list()
    r = np.core.records.fromrecords(vlqs, names=[f.name for f in electricalGSP._meta.fields])
    l=np.array(r)
    process = np.zeros([len(l),3])

    for i in range(0,len(process)): # extract the information we need for inputs.
        change = l[i]
        for j in range(1,4):
            process[i,(j-1)] = change[j]

    g=np.array(process)/2

    dS=pd.date_range(start='2015-04-01', end='2016-04-01', freq='H')
    proData=pd.DataFrame({'Time':dS[0:8784], 'Data':g[0:,2]})
    data=proData.set_index('Time')
    d1, d2, S = month(m, data)

    elec=S['Data']

    fProxy=np.zeros([24, d])
    cProxy=np.zeros([24, d])
    disProxy=np.zeros([24, d])
    newDemandProxy=np.zeros([24, d])
    
    for i in range(1,(d+1)):
        model, sol, flo, cha, dis, nD = runSolutionBalance(esCap, (elec.iloc[(24*i)-24:(24*i)]))
        fProxy[0:,(i-1)]=flo
        cProxy[0:,(i-1)]=cha
        disProxy[0:,(i-1)]=dis
        newDemandProxy[0:,(i-1)]=nD

    f=fProxy.reshape((d*24), order='F')
    c=cProxy.reshape((d*24),order='F')
    dis=disProxy.reshape((d*24),order='F')
    newDemand=newDemandProxy.reshape((d*24),order='F')

    check=all(i > 0 for i in f)

    if np.absolute(np.amax(f)) > np.absolute(np.amin(f)):
        fMax = np.amax(f)
        newDemandMax = np.amax(newDemand)
        peakReduction = 100 - round(((newDemandMax/fMax)*100),2)
        headroom = round((fMax - newDemandMax), 2)

    else:
        fMax = np.amin(f)
        newDemandMax = np.amin(newDemand)
        peakReduction = 100 - round(((newDemandMax/fMax)*100),2)
        headroom = round((newDemandMax- fMax), 2)

    delta = datetime.timedelta(hours=1)
    dates = drange(d1, d2, delta)
    finalDates=elec[0:(24*d)].index


    powerData=np.zeros([len(f),3])
    powerData[0:,0]=f
    powerData[0:,1]=newDemand
    powerData[0:,2]=c+dis
    finalDataProxy=pd.DataFrame(powerData, index=finalDates)
    finalData=finalDataProxy.reset_index()

    response = HttpResponse(content_type='text/csv')
    file =gspName.name +'GSP_'+str(esCap)+'MWh_energy_storage.csv'
    response['Content-Disposition'] = 'attachment; filename="%s"' % file

    writer = csv.writer(response)

    with open('pv_generation.csv','w') as csvfile:
        writer.writerow(['', 'Base Demand(MWh)', 'New Demand(MWh)', 'Energy Storage Flow (MWh)'])
        for i in range(0,len(finalData)):
            writer.writerow(finalData.iloc[i,0:])
    
    return response
