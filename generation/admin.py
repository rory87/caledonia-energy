from django.contrib import admin
from .models import Weather
from .models import latLon
from .models import Turbines

# Register your models here.

class WeatherAdmin(admin.ModelAdmin):
    list_display=('index', 'temp', 'humidity', 'ghi','dni','dhi','infra','windSpeed','windDirection','pressure')


admin.site.register(Weather, WeatherAdmin)

class latLonAdmin(admin.ModelAdmin):
    list_display=('index', 'latitude', 'longitude', 'altitude')

admin.site.register(latLon, latLonAdmin)

class TurbinesAdmin(admin.ModelAdmin):
    list_display=('manufacturer', 'rating', 'cutIn', 'ratedSpeed', 'cutOut', 'p1','p2','p3','p4','p5')

admin.site.register(Turbines, TurbinesAdmin)
