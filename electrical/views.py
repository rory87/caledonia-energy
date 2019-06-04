#django library imports
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse
from django.views.generic.list import ListView
import csv
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm

#model imports
from .models import electricalGSP
from heat.models import GSP
from heat.views import processData
from heat.views import format_inputs
from heat.views import month
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
##def electrical_form_plot(request):
##    return render(request, 'electrical/electrical_input_form_plot.html')

def electrical_form(request):
    return render(request, 'electrical/electrical_input_form_data.html')

def electrical_form_compare(request):
    return render(request, 'electrical/electrical_input_compare.html')

def plot_electrical(request):
    supplyPoint=request.GET['supplyPoint']
    m=int(request.GET['month'])
    d=request.GET['days']
    gspName=GSP.objects.get(idx=supplyPoint)


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

    g=np.array(process)
    

    dS=pd.date_range(start='2015-04-01', end='2016-04-01', freq='H')
    proData=pd.DataFrame({'Time':dS[0:8784], 'Data':g[0:,2]})
    data=proData.set_index('Time')
    d1, d2, S = month(m, data)

    elec=S['Data']
    finalData = elec.iloc[0:(24*d)]/2
    if max(finalData) > abs(min(finalData)):
        maxGSP_proxy=max(finalData)
    else:
        maxGSP_proxy=min(finalData)

    maxGSP=round(maxGSP_proxy,2)

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

    ax.plot_date(finalDates,finalData, linestyle='-', marker='None', label='Demand')

##    if (finalData<0).any() == True and (finalData>0).any() == False:
##        ax.plot_date(finalDates,ratingNeg, linestyle='-', marker='None', color='r', label='GSP Rating')
##    elif (finalData<0).any() == False and (finalData>0).any() == True:
##        ax.plot_date(finalDates,rating, linestyle='-', marker='None', color='r', label='GSP Rating')
##    elif (finalData<0).any() == True and (finalData>0).any() == True:
##        ax.plot_date(finalDates,ratingNeg, linestyle='-', marker='None', color='r', label='GSP Rating')
##        ax.plot_date(finalDates,rating, linestyle='-', marker='None', color='r')
        
    ax.xaxis.set_major_formatter(formatter)
    ax.xaxis.set_major_locator(loc)
    plt.ylabel('Electrical Demand (MWh)')
    plt.title('Electrical Demand Plot for '+ gspName.name + ' GSP')
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
    return render(request, 'electrical/show_plot.html', {'graphic':graphic, 'maxGSP':maxGSP, 'rating': rating})
    
def data_electrical(request):
    supplyPoint=request.GET['supplyPoint']
    m=int(request.GET['month'])
    d=request.GET['days']
    gspName=GSP.objects.get(idx=supplyPoint)

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
    
    S = S.reset_index()
    columnsTitles=["Time","Data"]
    proData=S.reindex(columns=columnsTitles)
    finalData = proData.iloc[0:(24*d)]
    
    response = HttpResponse(content_type='text/csv')
    if m ==13:
        file =gspName.name +'GSP_0104_3103.csv'
    elif m<10:
        file =gspName.name +'GSP_0'+str(int(m))
    else:
        file =gspName.name +'GSP_'+str(int(m))
        
    response['Content-Disposition'] = 'attachment; filename="%s"' % file
    
    writer = csv.writer(response)
    
    with open('heat_demand.csv','w') as csvfile:
        writer.writerow(['', 'Electrical Demand (MWh)'])
        for i in range(0,len(finalData)):
            writer.writerow(finalData.iloc[i,0:])
    
    return response

def plot_electrical_compare(request):
    supplyPoint=request.GET['supplyPoint']
    supplyPoint2=request.GET['supplyPoint2']
    m=int(request.GET['month'])
    d=request.GET['days']
    gspName=GSP.objects.get(idx=supplyPoint)
    gspName2=GSP.objects.get(idx=supplyPoint2)


    if d =='':
        d=int(0)
    else:
        d = int(d)

    if m == 13:
        d=366

    ###
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
    ###

    electricalData2 = electricalGSP.objects.filter(GSP = supplyPoint2)
    vlqs = electricalData2.values_list()
    r = np.core.records.fromrecords(vlqs, names=[f.name for f in electricalGSP._meta.fields])
    l=np.array(r)
    process = np.zeros([len(l),3])

    for i in range(0,len(process)): # extract the information we need for inputs.
        change = l[i]
        for j in range(1,4):
            process[i,(j-1)] = change[j]

    g2=np.array(process)/2
    ###

    dS=pd.date_range(start='2015-04-01', end='2016-04-01', freq='H')
    proData=pd.DataFrame({'Time':dS[0:8784], 'Data':g[0:,2]})
    data=proData.set_index('Time')
    d1, d2, S = month(m, data)
    
    elec=S['Data']
    finalData = elec.iloc[0:(24*d)]

    if max(finalData) > abs(min(finalData)):
        maxGSP1_proxy=max(finalData)
    else:
        maxGSP1_proxy=min(finalData)

    maxGSP1=round(maxGSP1_proxy,2)

    ###

    proData2=pd.DataFrame({'Time':dS[0:8784], 'Data':g2[0:,2]})
    data2=proData2.set_index('Time')
    d1, d2, S2 = month(m, data2)

    elec2=S2['Data']
    finalData2 = elec2.iloc[0:(24*d)]

    if max(finalData2) > abs(min(finalData2)):
        maxGSP2_proxy=max(finalData2)
    else:
        maxGSP2_proxy=min(finalData2)

    maxGSP2=round(maxGSP2_proxy,2)

    statHP1 = process_data_normal((gspStats.objects.filter(index=supplyPoint)), gspStats, 16)
    rating1=statHP1[0,1]

    statHP2 = process_data_normal((gspStats.objects.filter(index=supplyPoint2)), gspStats, 16)
    rating2=statHP2[0,1]

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

    ax.plot_date(finalDates,finalData, linestyle='-', marker='None', label=gspName.name + ' GSP')
    ax.plot_date(finalDates, finalData2,linestyle='-', marker='None', label=gspName2.name+ ' GSP')
    ax.xaxis.set_major_formatter(formatter)
    ax.xaxis.set_major_locator(loc)
    plt.ylabel('Electrical Demand (MWh)')
    plt.grid(True)
    ax.legend()
    

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
    return render(request, 'electrical/show_plot_compare.html', {'graphic':graphic, 'GSP1': gspName.name, 'GSP2': gspName2.name, 'maxGSP1': maxGSP1, 'maxGSP2':maxGSP2, 'rating1': rating1, 'rating2': rating2})
    
        
def data_electrical_compare(request):
    supplyPoint=request.GET['supplyPoint']
    supplyPoint2=request.GET['supplyPoint2']
    m=int(request.GET['month'])
    d=request.GET['days']
    gspName=GSP.objects.get(idx=supplyPoint)
    gspName2=GSP.objects.get(idx=supplyPoint2)

    if d =='':
        d=int(0)
    else:
        d = int(d)

    if m == 13:
        d=366

    ###
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
    
    S = S.reset_index()
    columnsTitles=["Time","Data"]
    proData=S.reindex(columns=columnsTitles)
    finalData = proData.iloc[0:(24*d)]

    ###
    electricalData2 = electricalGSP.objects.filter(GSP = supplyPoint2)
    vlqs = electricalData.values_list()
    r = np.core.records.fromrecords(vlqs, names=[f.name for f in electricalGSP._meta.fields])
    l=np.array(r)
    process = np.zeros([len(l),3])

    for i in range(0,len(process)): # extract the information we need for inputs.
        change = l[i]
        for j in range(1,4):
            process[i,(j-1)] = change[j]
        
    g2=np.array(process)/2

    proData2=pd.DataFrame({'Time':dS[0:8784], 'Data':g2[0:,2]})
    data2=proData2.set_index('Time')
    d1, d2, S2 = month(m, data2)

    S2 = S2.reset_index()
    columnsTitles=["Time","Data"]
    proData2=S2.reindex(columns=columnsTitles)
    finalData2 = proData2.iloc[0:(24*d)]
    ###

    completeData = finalData.append(finalData2,1)

    response = HttpResponse(content_type='text/csv')
    if m ==13:
        file =gspName.name +'GSP_0104_3103.csv'
    elif m<10:
        file =gspName.name +'GSP_0'+str(int(m))
    else:
        file =gspName.name +'GSP_'+str(int(m))
        
    response['Content-Disposition'] = 'attachment; filename="%s"' % file
    
    writer = csv.writer(response)
    
    with open('heat_demand.csv','w') as csvfile:
        writer.writerow(['', 'Electrical Demand (MWh)'])
        for i in range(0,len(completeData)):
            writer.writerow(completeData.iloc[i,0:])
    
    return response

    
