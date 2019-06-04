from django.db import models

# Create your models here.

class Weather(models.Model):
    index=models.IntegerField()
    temp=models.FloatField()
    humidity=models.FloatField()
    ghi=models.FloatField()
    dni=models.FloatField()
    dhi=models.FloatField()
    infra=models.FloatField()
    windSpeed=models.FloatField()
    windDirection=models.FloatField()
    pressure=models.FloatField()


class latLon(models.Model):
    index=models.IntegerField()
    latitude=models.FloatField()
    longitude=models.IntegerField()
    altitude=models.IntegerField()

class Turbines(models.Model):
    manufacturer=models.CharField(max_length=100)
    rating=models.IntegerField()
    cutIn=models.FloatField()
    ratedSpeed=models.FloatField()
    cutOut=models.FloatField()
    p1=models.FloatField()
    p2=models.FloatField()
    p3=models.FloatField()
    p4=models.FloatField()
    p5=models.FloatField()
    
