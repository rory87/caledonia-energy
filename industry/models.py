from django.db import models

# Create your models here.
class industrialBreakdown(models.Model):
    hour = models.IntegerField()
    GSP = models.IntegerField()
    manufacturing = models.FloatField()
    commercial = models.FloatField(null=True)
    entertainment = models.FloatField()
    education = models.FloatField(null=True)

class industrialNumbers(models.Model):
    GSP = models.IntegerField()
    manufacturing = models.IntegerField()
    commercial = models.IntegerField()
    entertainment = models.IntegerField()
    education = models.IntegerField()
