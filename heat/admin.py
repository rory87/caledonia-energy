from django.contrib import admin

# Register your models here.

from .models import Family
from .models import GSP
from .models import industrialHeat


class FamilyAdmin(admin.ModelAdmin):
    list_display=('hour','GSP','f40','f60','f100','f140','f160')

admin.site.register(Family, FamilyAdmin)

class GSPAdmin(admin.ModelAdmin):
    list_display=('idx','name')

admin.site.register(GSP, GSPAdmin)

class industrialHeatAdmin(admin.ModelAdmin):
    list_display=('hour', 'GSP', 'industrialHeatDemand')

admin.site.register(industrialHeat, industrialHeatAdmin)


