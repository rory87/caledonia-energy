from django.db import models

# Create your models here.

class gspStats(models.Model):
    index=models.IntegerField()
    rating=models.IntegerField()
    lat=models.FloatField()
    lon=models.FloatField()
    totalHouses=models.IntegerField()
    detached=models.IntegerField()
    semiD=models.IntegerField()
    terraced=models.IntegerField()
    flat=models.IntegerField()
    totCars=models.IntegerField()
    noCH=models.IntegerField()
    gas=models.IntegerField()
    electric=models.IntegerField()
    oil=models.IntegerField()
    solid=models.IntegerField()
    other=models.IntegerField()
    
