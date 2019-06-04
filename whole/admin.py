from django.contrib import admin
from .models import gspStats

# Register your models here.

class gspStatsAdmin(admin.ModelAdmin):
    list_display=('index', 'rating', 'lat', 
                  'lon', 'totalHouses', 'detached', 'semiD',
                  'terraced', 'flat', 'totCars', 'noCH', 'gas',
                  'electric', 'oil', 'solid', 'other')

admin.site.register(gspStats, gspStatsAdmin)
