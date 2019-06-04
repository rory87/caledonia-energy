# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2019-03-04 09:58
from __future__ import unicode_literals

from django.db import migrations
from django.apps import apps
import pandas as pd

def populateGeneration(apps, schema_editor):
    Weather = apps.get_model('generation', 'Weather')
    dataWeather = pd.read_csv(r'weather.csv', header=None).as_matrix()

    latLon = apps.get_model('generation','latLon')
    latLonData = pd.read_csv(r'latLon.csv', header=None).as_matrix()

    for i in range(0, len(dataWeather)):
        w=Weather(index=dataWeather[i,0], temp=dataWeather[i,1], humidity=dataWeather[i,2], ghi=dataWeather[i,3], dni=dataWeather[i,4], dhi=dataWeather[i,5], infra=dataWeather[i,6], windSpeed=dataWeather[i,7], windDirection=dataWeather[i,8], pressure=dataWeather[i,9])
        w.save()

    for i in range(0, len(latLonData)):
        l=latLon(index=latLonData[i,0], latitude=latLonData[i,1], longitude=latLonData[i,2], altitude=latLonData[i,3])
        l.save()    


class Migration(migrations.Migration):

    dependencies = [
        ('generation', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(populateGeneration)
    ]
