from django.db import models
from django.core.urlresolvers import reverse


# Create your models here.

class Family(models.Model):
    hour=models.IntegerField()
    GSP=models.IntegerField()
    f40=models.IntegerField(default=0)
    f60=models.IntegerField(default=0)
    f100=models.IntegerField(default=0)
    f140=models.IntegerField(default=0)
    f160=models.IntegerField(default=0)


class GSP(models.Model):
    idx=models.IntegerField()
    name=models.CharField(max_length=100)

class industrialHeat(models.Model):
    hour = models.IntegerField()
    GSP = models.IntegerField()
    industrialHeatDemand = models.FloatField()
    

