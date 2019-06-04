from django.db import models
from django.core.urlresolvers import reverse

# Create your models here.

class electricalGSP(models.Model):
    hour = models.IntegerField()
    GSP = models.IntegerField()
    electricalDemand = models.FloatField()
