# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2019-03-13 09:30
from __future__ import unicode_literals

from django.db import migrations
from django.apps import apps
import pandas as pd

def populateStats(apps, schema_editor):
    gspStats=apps.get_model('whole', 'gspStats')
    statsData=pd.read_csv(r'gspStats.csv', header=None).as_matrix()

    for i in range(0, len(statsData)):
        s=gspStats(index=statsData[i,0],
                   rating=statsData[i,1],
                   lat=statsData[i,2],
                   lon=statsData[i,3],
                   totalHouses=statsData[i,4],
                   detached=statsData[i,5],
                   semiD=statsData[i,6],
                   terraced=statsData[i,7],
                   flat=statsData[i,8],
                   totCars=statsData[i,9],
                   noCH=statsData[i,10],
                   gas=statsData[i,11],
                   electric=statsData[i,12],
                   oil=statsData[i,13],
                   solid=statsData[i,14],
                   other=statsData[i,15])
        s.save()

class Migration(migrations.Migration):

    dependencies = [
        ('whole', '0003_gspstats_rating'),
    ]

    operations = [
        migrations.RunPython(populateStats)
    ]
