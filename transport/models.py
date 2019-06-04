from django.db import models

# Create your models here.

class Journey(models.Model):
    start_journey=models.FloatField()
    journey_distance=models.FloatField()
    second_journey_distance=models.FloatField()
    speed=models.FloatField()
    localAuthority=models.CharField(max_length=100)
    Area=models.CharField(max_length=100)
    typeEV=models.CharField(max_length=100)
    


class gspLocalAuthority(models.Model):
    gsp = models.CharField(max_length=100)
    localAuthority = models.CharField(max_length=100)
