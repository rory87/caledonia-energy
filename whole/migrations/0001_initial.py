# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2019-03-12 16:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='gspStats',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('index', models.IntegerField()),
                ('lat', models.FloatField()),
                ('lon', models.FloatField()),
                ('totalHouses', models.IntegerField()),
                ('detached', models.IntegerField()),
                ('semiD', models.IntegerField()),
                ('terraced', models.IntegerField()),
                ('flat', models.IntegerField()),
                ('totCars', models.IntegerField()),
                ('noCH', models.IntegerField()),
                ('electric', models.IntegerField()),
                ('oil', models.IntegerField()),
                ('solid', models.IntegerField()),
                ('other', models.IntegerField()),
            ],
        ),
    ]
