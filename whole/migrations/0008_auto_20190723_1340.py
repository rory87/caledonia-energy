# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2019-07-23 12:40
from __future__ import unicode_literals

from django.db import migrations
from django.apps import apps
import pandas as pd


def fillTable(table, data):

    for i in range(0, len(data)):
        s = table(index=data[i,0], scenario=data[i,1],
                            year18=data[i,2], year19=data[i,3],
                            year20=data[i,4], year21=data[i,5],
                            year22=data[i,6],  year23=data[i,7],
                            year24=data[i,8],  year25=data[i,9],
                            year26=data[i,10],  year27=data[i,11],
                            year28=data[i,12],  year29=data[i,13],
                            year30=data[i,14],  year31=data[i,15],
                            year32=data[i,16],  year33=data[i,17],
                            year34=data[i,18],  year35=data[i,19],
                            year36=data[i,20],  year37=data[i,21],
                            year38=data[i,22],  year39=data[i,23],
                            year40=data[i,24])
        s.save()



def populateFES(apps, schema_editor):

    windFES =apps.get_model('whole', 'windFES')
    dataWindFES=pd.read_csv(r'windFES.csv', header=None).as_matrix()
    fillTable(windFES, dataWindFES)
    
    pvFES = apps.get_model('whole','pvFES')
    dataPVFES = pd.read_csv(r'pvFES.csv', header=None).as_matrix()
    fillTable(pvFES, dataPVFES)
    
    storageFES = apps.get_model('whole','storageFES')
    dataStorageFES = pd.read_csv(r'storageFES.csv', header=None).as_matrix()
    fillTable(storageFES, dataStorageFES)

    subWindFES = apps.get_model('whole','subWindFES')
    dataSubWindFES = pd.read_csv(r'subWindFES.csv', header=None).as_matrix()
    fillTable(subWindFES, dataSubWindFES)

    subPVFES = apps.get_model('whole','subPVFES')
    dataSubPVFES = pd.read_csv(r'subPVFES.csv', header=None).as_matrix()
    fillTable(subPVFES, dataSubPVFES)

    subStorageFES = apps.get_model('whole','subStorageFES')
    dataSubStorageFES = pd.read_csv(r'subStorageFES.csv', header=None).as_matrix()
    fillTable(subStorageFES, dataSubStorageFES)

    hpFES = apps.get_model('whole','hpFES')
    datHPFES = pd.read_csv(r'hpFES.csv', header=None).as_matrix()
    fillTable(hpFES, datHPFES)

    evFES = apps.get_model('whole','evFES')
    dataEVFES = pd.read_csv(r'evFES.csv', header=None).as_matrix()
    fillTable(evFES, dataEVFES)


class Migration(migrations.Migration):

    dependencies = [
        ('whole', '0007_evfes_hpfes_pvfes_storagefes_subpvfes_substoragefes_subwindfes_windfes'),
    ]

    operations = [
        migrations.RunPython(populateFES)
    ]
