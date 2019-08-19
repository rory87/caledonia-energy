# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2019-07-16 10:39
from __future__ import unicode_literals

from django.db import migrations
from django.apps import apps
import pandas as pd

def populateSSEStats(apps, schema_editor):
    primarySSEStats =apps.get_model('whole', 'primarySSEStats')
    dataStats=pd.read_csv(r'primaryStatsSSE.csv', header=None).as_matrix()

    for i in range(0, len(dataStats)):
        s = primarySSEStats(index=dataStats[i,0], name=dataStats[i,1],
                            gsp=dataStats[i,2], rating=dataStats[i,3],
                            customers=dataStats[i,4])
        s.save()


class Migration(migrations.Migration):

    dependencies = [
        ('whole', '0005_primaryssestats'),
    ]

    operations = [
        migrations.RunPython(populateSSEStats)
    ]
