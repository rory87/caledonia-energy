# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2019-03-06 15:44
from __future__ import unicode_literals

from django.db import migrations
from django.apps import apps
import pandas as pd
import numpy as np


def populateHeatTables(apps, schema_editor):
    industrialHeat = apps.get_model('heat', 'industrialHeat')
    GSP = apps.get_model('heat','GSP')
    
    industrialData = pd.read_csv(r'industrialHeat.csv', header=None).as_matrix()
    dataGSP = pd.read_csv(r'gspIndex.csv', header=None).as_matrix()
    
    for i in range(0, len(industrialData)):
        hI = industrialHeat(hour=industrialData[i,0], GSP=industrialData[i,1], industrialHeatDemand=industrialData[i,2])
        hI.save()
    
    for i in range(0, len(dataGSP)):
        g=GSP(idx=dataGSP[i,0], name=dataGSP[i,1])
        g.save()


class Migration(migrations.Migration):

    dependencies = [
        ('heat', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(populateHeatTables)
    ]
