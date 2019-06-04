from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse
from django.views.generic.list import ListView
import csv
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm

#model/view imports
from . models import Weather
from . models import latLon
from . models import Turbines
from generation . interpolateLatLon import *
from generation . formatWeather import *
from generation . pvPowerOut import *

#numpy and pandas imports
import numpy as np
import pandas as pd
from scipy.interpolate import griddata
import pvlib
import csv

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
def pv_form(request):
    return render(request, 'generation/pv_input_form.html')

@login_required(login_url='/login/')
def wind_form(request):
    return render(request, 'generation/wind_input_form.html')

def pv_plot(request):
    ratingPV = float(request.GET['ratingPV'])*1000
    latitude = float(request.GET['latitude'])
    longitude = float(request.GET['longitude'])
    d = int(request.GET['days'])
    m = int(request.GET['month'])


    tmy_data, altitude = extract_weather(d,m, latitude, longitude)
    p_acs = pvPowerOut(tmy_data, latitude, longitude, altitude, ratingPV)
    #p_acs =p_acs.shift(freq = '30min')
    peakGen = format(max(p_acs['sapm'])/1000, '.2f')
    capacityFactor=format(((sum(p_acs['sapm']))/((len(p_acs)*ratingPV))) * 100, '.2f')

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

    loc = RRuleLocator(rule)
    fig, ax =plt.subplots()
    ax.plot_date(p_acs.index, (p_acs.iloc[0:,0].as_matrix()/1000), linestyle='-', marker='None')
    ax.xaxis.set_major_formatter(formatter)
    ax.xaxis.set_major_locator(loc)
    plt.ylabel('PV Output (kWh)')
    plt.grid(True)
    title = 'Output of a '+ str(ratingPV/1000) + ' kW PV Generator at ' + str(latitude) + ' deg lat and ' + str(longitude) + ' deg lon'
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
    
    return render(request, 'generation/show_plot_pv.html',{'graphic':graphic, 'peakGen':peakGen, 'capacityFactor':capacityFactor})



def pv_data(request):
    ratingPV = float(request.GET['ratingPV'])*1000
    latitude = float(request.GET['latitude'])
    longitude = float(request.GET['longitude'])
    d = int(request.GET['days'])
    m = int(request.GET['month'])


    tmy_data, altitude = extract_weather(d,m, latitude, longitude)
    p_acs = pvPowerOut(tmy_data, latitude, longitude, altitude, ratingPV)
    #p_acs =p_acs.shift(freq = '30min')
    finalData=p_acs.reset_index()

    response = HttpResponse(content_type='text/csv')
    file ='pv_gen_output_'+ str(ratingPV/1000) +'kW_' + str(latitude)+ '_lat, ' + str(longitude) +'_lon.csv'
    response['Content-Disposition'] = 'attachment; filename="%s"' % file
    
    writer = csv.writer(response)

    with open('pv_generation.csv','w') as csvfile:
        writer.writerow(['', 'PV Output(kWh)'])
        for i in range(0,len(finalData)):
            writer.writerow(finalData.iloc[i,0:])
    
    return response

    
def wind_plot(request):
    ratingWind = float(request.GET['ratingWind'])*1000
    latitude = float(request.GET['latitude'])
    longitude = float(request.GET['longitude'])
    d = int(request.GET['days'])
    m = int(request.GET['month'])
    turbineNo=int(request.GET['turbineNo'])

    turbineRating=ratingWind/turbineNo

    if turbineRating > 3000:
        turbineRating = 3000
    
    t=Turbines.objects.all()
    turbineData = process_data(t, Turbines,10)
    turbineData.columns=['manufacturer', 'rating', 'cutIn', 'ratedSpeed', 'cutOut', 'p1','p2','p3','p4','p5']

    ##Find closest turbine
    x=turbineData['rating']- turbineRating
    y=x.where(x>=0).dropna().astype(float)
    closestList=y.where(y == y[y.idxmin()]).dropna()
    turbine=turbineData.iloc[closestList.sample(n=1).index[0]]

    ##Extract TMY weather wata, specifically wind speed
    tmy_data, altitude = extract_weather(d,m, latitude, longitude)
    windSpeed = tmy_data['windS']

    #Calculate wind wpeed
    p_acs = np.zeros(len(windSpeed))
                     
    for i in range(0, len(windSpeed)):
        if (windSpeed.iloc[i] < turbine['cutIn']) or (windSpeed.iloc[i] > turbine['cutOut']):
            p_acs[i] = 0
        elif (windSpeed.iloc[i] > turbine['ratedSpeed']) and (windSpeed.iloc[i] < turbine['cutOut']):
            p_acs[i] = turbine['ratedSpeed']
        else:
            p_acs[i] = (turbine['p1']*windSpeed.iloc[i]**4) + (turbine['p2']*windSpeed.iloc[i]**3) + (turbine['p3']*windSpeed.iloc[i]**2) + (turbine['p4']*windSpeed.iloc[i]) + turbine['p5']

    for i in range(0, len(p_acs)):
        if p_acs[i] > turbineRating:
            p_acs[i] = turbineRating

    pWind=pd.DataFrame(p_acs, index=tmy_data.index, columns=['power'])
    #pWind=pWind.shift(freq = '30min')
    peakGen = format(max(pWind['power']*turbineNo)/1000, '.2f')
    capacityFactor=format((sum(pWind['power'])/(len(pWind)*(turbine['rating']))) * 100, '.2f')

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

    loc = RRuleLocator(rule)
    fig, ax =plt.subplots()
    ax.plot_date(pWind.index, (pWind.iloc[0:,0].as_matrix()/1000)*turbineNo, linestyle='-', marker='None')
    ax.xaxis.set_major_formatter(formatter)
    ax.xaxis.set_major_locator(loc)
    plt.ylabel('Wind Output (MWh)')
    plt.grid(True)
    title=str(turbineNo) +'x'+ str(turbine['rating']/1000) + 'MW ' + turbine['manufacturer'] + 'wind turbines at ' + str(latitude) +' deg lat, ' + str(longitude) + 'deg lon'
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
    
    return render(request, 'generation/show_plot_wind.html',{'graphic':graphic,'capacityFactor':capacityFactor, 'peakGen':peakGen})

def wind_data(request):
    ratingWind = float(request.GET['ratingWind'])*1000
    latitude = float(request.GET['latitude'])
    longitude = float(request.GET['longitude'])
    d = int(request.GET['days'])
    m = int(request.GET['month'])
    turbineNo=int(request.GET['turbineNo'])

    turbineRating=ratingWind/turbineNo

    if turbineRating > 3000:
        turbineRating = 3000
    
    t=Turbines.objects.all()
    turbineData = process_data(t, Turbines,10)
    turbineData.columns=['manufacturer', 'rating', 'cutIn', 'ratedSpeed', 'cutOut', 'p1','p2','p3','p4','p5']

    ##Find closest turbine
    x=turbineData['rating']- turbineRating
    y=x.where(x>=0).dropna().astype(float)
    closestList=y.where(y == y[y.idxmin()]).dropna()
    turbine=turbineData.iloc[closestList.sample(n=1).index[0]]

    ##Extract TMY weather wata, specifically wind speed
    tmy_data, altitude = extract_weather(d,m, latitude, longitude)
    windSpeed = tmy_data['windS']

    #Calculate wind wpeed
    p_acs = np.zeros(len(windSpeed))
                     
    for i in range(0, len(windSpeed)):
        if (windSpeed.iloc[i] < turbine['cutIn']) or (windSpeed.iloc[i] > turbine['cutOut']):
            p_acs[i] = 0
        elif (windSpeed.iloc[i] > turbine['ratedSpeed']) and (windSpeed.iloc[i] < turbine['cutOut']):
            p_acs[i] = turbine['ratedSpeed']
        else:
            p_acs[i] = (turbine['p1']*windSpeed.iloc[i]**4) + (turbine['p2']*windSpeed.iloc[i]**3) + (turbine['p3']*windSpeed.iloc[i]**2) + (turbine['p4']*windSpeed.iloc[i]) + turbine['p5']

    for i in range(0, len(p_acs)):
        if p_acs[i] > turbineRating:
            p_acs[i] = turbineRating

    pWind=pd.DataFrame((p_acs/1000)*turbineNo, index=tmy_data.index, columns=['power'])
    #pWind=pWind.shift(freq = '30min')
    finalData = pWind.reset_index()

    response = HttpResponse(content_type='text/csv')
    file ='wind_gen_output_'+ str(ratingWind/1000) +'MW_' + str(latitude)+ '_lat, ' + str(longitude) +'_lon.csv'
    response['Content-Disposition'] = 'attachment; filename="%s"' % file
    
    writer = csv.writer(response)

    with open('pv_generation.csv','w') as csvfile:
        writer.writerow(['', 'Wind Farm Output(MWh)'])
        for i in range(0,len(finalData)):
            writer.writerow(finalData.iloc[i,0:])
    
    return response
    
    

def extract_weather(d,m, latitude, longitude):

    if latitude%0.5 == 0:
        if latitude < 59.5:
            latitude = latitude + 0.001
        else:
            latitude = latitude - 0.001

    if longitude%1 == 0:
        if longitude < -1:
            longitude = longitude + 0.001
        else:
            longitude = longitude - 0.001
    
    ##
    coordDataProxy=latLon.objects.all()
    coordData = process_data(coordDataProxy, latLon, 4)
    num, lats, lons, alt = interpolateLatLon(latitude, longitude, coordData)
    ##

    p1 = Weather.objects.filter(index=num[0])
    p2 = Weather.objects.filter(index=num[1])
    p3 = Weather.objects.filter(index=num[2])
    p4 = Weather.objects.filter(index=num[3])

    pointOneTotal = process_data(p1, Weather, 10)
    pointTwoTotal = process_data(p2, Weather, 10)
    pointThreeTotal = process_data(p3, Weather, 10)
    pointFourTotal = process_data(p4, Weather, 10)

    ##

    tmy_data, altitude=formatWeather(pointOneTotal, pointTwoTotal, pointThreeTotal, pointFourTotal, latitude, longitude, lats, lons, alt,d,m)
    

    return tmy_data, altitude
    


def process_data(data, table, dim):

    vlqs = data.values_list()
    r = np.core.records.fromrecords(vlqs, names=[f.name for f in table._meta.fields])
    l=np.array(r)
    process = pd.DataFrame(index=range(len(l)), columns=range(dim)).as_matrix()             

    for i in range(0,len(process)): # extract the information we need for inputs.
        change = l[i]
        for j in range(1,(dim+1)):
            process[i,(j-1)] = change[j]

    processReal=pd.DataFrame(process)

    return processReal
