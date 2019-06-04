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
from .models import Family
from .models import GSP
from .models import industrialHeat

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

#user registration/login imports



#####################################################

@login_required(login_url='/login/')
def heat_form(request):
    return render(request, 'heat/input_form.html')

@login_required(login_url='/login/')
def heat_form_compare(request):
    return render(request, 'heat/input_form_compare.html')

@login_required(login_url='/login/')
def heat_form_industrial(request):
    return render(request, 'heat/input_form_industrial.html')

@login_required(login_url='/login/')
def house_sizes(request):
    return render(request, 'heat/house_sizes.html')


def data_heat(request):

    #get user input data from browser
    small = request.GET['small']
    medium = request.GET['medium']
    large = request.GET['large']
    supplyPoint=request.GET['supplyPoint']
    m = int(request.GET['month'])
    d = request.GET['days']

    if small == '':
        small = int(0)
    else:
        small = int(small)

    if medium == '':
        medium = int(0)
    else:
        medium = int(medium)

    if large == '':
        large = int(0)
    else:
        large = int(large)

    if d =='':
        d=int(0)
    else:
        d = int(d)
    
    if m==13:
        d=366
    
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
        

    #change data type
    rawData = processData(supplyPoint)
    hour, totalDemand = format_inputs(rawData, h40, h60, h100, h140, h160)

    # add time element to data
    dS=pd.date_range(start='2015-04-01', end='2016-04-01', freq='H')
    proData=pd.DataFrame({'Time':dS[0:8784], 'Data':(totalDemand/1000)})
    data=proData.set_index('Time')
    d1, d2, S = month(m, data)

    S = S.reset_index()
    columnsTitles=["Time","Data"]
    proData=S.reindex(columns=columnsTitles)
    finalData = proData.iloc[0:(24*d)]
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="heat_demand.csv"'
    
    writer = csv.writer(response)
    
    with open('heat_demand.csv','w') as csvfile:
        writer.writerow(['', 'Heat Demand (KWh)'])
        for i in range(0,len(finalData)):
            writer.writerow(finalData.iloc[i,0:])
    
    return response




def plot_heat(request): 


    #get user input data from browser
    small = request.GET['small']
    medium = request.GET['medium']
    large = request.GET['large']
    supplyPoint=request.GET['supplyPoint']
    gspName=GSP.objects.get(idx=supplyPoint)
    m=int(request.GET['month'])
    d=request.GET['days']

    if small == '':
        small = int(0)
    else:
        small = int(small)

    if medium == '':
        medium = int(0)
    else:
        medium = int(medium)

    if large == '':
        large = int(0)
    else:
        large = int(large)

    if d =='':
        d=int(0)
    else:
        d = int(d)

    if m==13:
        d=366

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

    #change data type
    rawData = processData(supplyPoint)
    hour, totalDemand = format_inputs(rawData, h40, h60, h100, h140, h160)

    dS=pd.date_range(start='2015-04-01', end='2016-04-01', freq='H')
    proData=pd.DataFrame({'Time':dS[0:8784], 'Data':totalDemand/1000})
    data=proData.set_index('Time')
    d1, d2, S = month(m, data)
    heat=S['Data']
    finalData = heat.iloc[0:(24*d)]
    maxHeat=max(finalData)
    
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

    ax.plot_date(finalDates,finalData, linestyle='-', marker='None', label=gspName.name)
    ax.xaxis.set_major_formatter(formatter)
    ax.xaxis.set_major_locator(loc)
    ax.legend()
    plt.ylabel('Heat Demand (KWh)')
    plt.grid(True)
    plt.title(str(small) + ' Small Properties, ' + str(medium) + ' Medium Properties, '+ str(large) + ' Large Properties')
  
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
    return render(request, 'heat/show_plot.html', {'graphic':graphic, 'maxHeat':maxHeat})





def compare_heat_plot(request):


    #get user input data from browser
    small = request.GET['small']
    medium = request.GET['medium']
    large = request.GET['large']
    m = int(request.GET['month'])
    d=request.GET['days']

    if small == '':
        small = int(0)
    else:
        small = int(small)

    if medium == '':
        medium = int(0)
    else:
        medium = int(medium)

    if large == '':
        large = int(0)
    else:
        large = int(large)

    if d =='':
        d=int(0)
    else:
        d = int(d)

    if m==13:
        d=366

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

    
    supplyPoint=request.GET['supplyPoint']
    gspName=GSP.objects.get(idx=supplyPoint)

    supplyPoint2=request.GET['supplyPoint2']
    gspName2=GSP.objects.get(idx=supplyPoint2)


    #change data type
    rawData = processData(supplyPoint)
    hour, totalDemand = format_inputs(rawData, h40, h60, h100, h140, h160)

    rawData2 = processData(supplyPoint2)
    hour2, totalDemand2 = format_inputs(rawData2, h40, h60, h100, h140, h160)

    ###
    dS=pd.date_range(start='2015-04-01', end='2016-04-01', freq='H')
    proData1=pd.DataFrame({'Time':dS[0:8784], 'Data':(totalDemand/1000)})
    proData2=pd.DataFrame({'Time':dS[0:8784], 'Data':(totalDemand2/1000)})

    data1=proData1.set_index('Time')
    data2=proData2.set_index('Time')

    #sort month
    d1, d2, S1 = month(m, data1)
    d1, d2, S2 = month(m, data2)

    heat1=S1['Data']
    finalData1 = heat1.iloc[0:(24*d)]
    maxGSP1=max(finalData1)

    heat2=S2['Data']
    finalData2 = heat2.iloc[0:(24*d)]
    maxGSP2=max(finalData2)

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

    ax.plot_date(finalDates,finalData1, linestyle='-', marker='None', label=gspName.name)
    ax.plot_date(finalDates,finalData2, linestyle='-', marker='None', label=gspName2.name)
    ax.xaxis.set_major_formatter(formatter)
    ax.xaxis.set_major_locator(loc)
    ax.legend()
    plt.ylabel('Heat Demand (KWh)')
    plt.title(str(small) + ' Small Properties, ' + str(medium) + ' Medium Properties, '+ str(large) + ' Large Properties')
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

    return render(request, 'heat/show_plot_compare.html', {'graphic':graphic, 'GSP1':gspName.name, 'GSP2':gspName2.name, 'maxGSP1': maxGSP1, 'maxGSP2':maxGSP2 })

def data_heat_industrial(request):
    supplyPoint=request.GET['supplyPoint']
    m=int(request.GET['month'])
    d=request.GET['days']

    if d =='':
        d=int(0)
    else:
        d = int(d)

    if m==13:
        d=366
        

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

    S = S.reset_index()
    columnsTitles=["Time","Data"]
    proData=S.reindex(columns=columnsTitles)
    finalData = proData.iloc[0:(24*d)]
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="heat_demand_industrial.csv"'
    
    writer = csv.writer(response)
    
    with open('heat_demand.csv','w') as csvfile:
        writer.writerow(['', 'Heat Demand (MWh)'])
        for i in range(0,len(finalData)):
            writer.writerow(finalData.iloc[i,0:])
    
    return response

def plot_heat_industrial(request):
    supplyPoint=request.GET['supplyPoint']
    m=int(request.GET['month'])
    d=request.GET['days']
    gspName=GSP.objects.get(idx=supplyPoint)

    if d =='':
        d=int(0)
    else:
        d = int(d)

    if m==13:
        d=366


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
    finalData = heat.iloc[0:(24*d)]


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

    ax.plot_date(finalDates,finalData, linestyle='-', marker='None', label=gspName.name)
    ax.xaxis.set_major_formatter(formatter)
    ax.xaxis.set_major_locator(loc)
    ax.legend()
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
    return render(request, 'heat/show_plot.html', {'graphic':graphic})
    

######**Local Functions**######

def processData(supplyPoint):

    heatData = Family.objects.filter(GSP = supplyPoint)

    # process queries into an iterable tuple
    vlqs = heatData.values_list()
    r = np.core.records.fromrecords(vlqs, names=[f.name for f in Family._meta.fields])
    l=np.array(r)

    return l


def format_inputs(rawData, h40, h60, h100, h140, h160):
    process = np.zeros([len(rawData),7])
    
    for i in range(0,len(process)): # extract the information we need for inputs.
        change = rawData[i]
        for j in range(1,8):
            process[i,(j-1)] = change[j]

    g=np.array(process)

    hour = g[0:,0]
    d40 = g[0:,2]*int(h40)
    d60 = g[0:,3]*int(h60)
    d100 = g[0:,4]*int(h100)
    d140 = g[0:,5]*int(h140)
    d160 =  g[0:,6]*int(h160)

    totalDemand=np.array(d40 + d60 + d100 + d140 + d160)

    return hour, totalDemand

def month(m, data):

    if m == 1:
        d1 = datetime.date(2016,m,1)
        d2 = datetime.date(2016,(m+1),1)
        S = data.loc['2016-01-01':'2016-01-31']
    elif m == 2: 
        d1 = datetime.date(2016,m,1)
        d2 = datetime.date(2016,(m+1),1)
        S = data.loc['2016-02-01':'2016-02-29']
    elif m == 3: 
        d1 = datetime.date(2016,m,1)
        d2 = datetime.date(2016,(m+1),1)
        S = data.loc['2016-03-01':'2016-03-31']
    elif m == 4: 
        d1 = datetime.date(2015,m,1)
        d2 = datetime.date(2015,(m+1),1)
        S = data.loc['2015-04-01':'2015-04-30']
    elif m ==5:
        d1 = datetime.date(2015,m,1)
        d2 = datetime.date(2015,(m+1),1)
        S = data.loc['2015-05-01':'2015-05-31']
    elif m ==6:
        d1 = datetime.date(2015,m,1)
        d2 = datetime.date(2015,(m+1),1)
        S = data.loc['2015-06-01':'2015-06-30']
    elif m == 7:
        d1 = datetime.date(2015,m,1)
        d2 = datetime.date(2015,(m+1),1)
        S = data.loc['2015-07-01':'2015-07-31']
    elif m == 8:
        d1 = datetime.date(2015,m,1)
        d2 = datetime.date(2015,(m+1),1)
        S = data.loc['2015-08-01':'2015-08-31']
    elif m ==9:
        d1 = datetime.date(2015,m,1)
        d2 = datetime.date(2015,(m+1),1)
        S = data.loc['2015-09-01':'2015-09-30']
    elif m == 10:
        d1 = datetime.date(2015,m,1)
        d2 = datetime.date(2015,(m+1),1)
        S = data.loc['2015-10-01':'2015-10-31']
    elif m == 11:
        d1 = datetime.date(2015,m,1)
        d2 = datetime.date(2015,(m+1),1)
        S = data.loc['2015-11-01':'2015-11-30']
    elif m == 12:
        d1 = datetime.date(2015,m,1)
        d2 = datetime.date(2016,1,1)
        S = data.loc['2015-12-01':'2015-12-31']
    elif m==13:
        d1 = datetime.date(2015,4,1)
        d2 = datetime.date(2016,4,1)
        S = data.loc['2015-04-01':'2016-03-31']

    return d1, d2, S


    

    
