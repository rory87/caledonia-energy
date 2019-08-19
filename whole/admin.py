from django.contrib import admin
from .models import gspStats
from .models import primarySSEStats
from .models import evFES
from .models import hpFES
from .models import pvFES
from .models import storageFES
from .models import subPVFES
from .models import subStorageFES
from .models import subWindFES
from .models import windFES

# Register your models here.

class gspStatsAdmin(admin.ModelAdmin):
    list_display=('index', 'rating', 'lat', 
                  'lon', 'totalHouses', 'detached', 'semiD',
                  'terraced', 'flat', 'totCars', 'noCH', 'gas',
                  'electric', 'oil', 'solid', 'other')

admin.site.register(gspStats, gspStatsAdmin)

class primarySSEStatsAdmin(admin.ModelAdmin):
    list_display=('index', 'name', 'gsp', 'rating', 'customers')

admin.site.register(primarySSEStats, primarySSEStatsAdmin)

class evFESAdmin(admin.ModelAdmin):
    list_display=('index', 'scenario', 
    'year18', 'year19', 'year20', 'year21',
    'year22', 'year23', 'year24', 'year25',
    'year26', 'year27', 'year28', 'year29', 
    'year30', 'year31', 'year32', 'year33',
    'year34', 'year35', 'year36', 'year37',
    'year38', 'year39', 'year40')

admin.site.register(evFES, evFESAdmin)

class hpFESAdmin(admin.ModelAdmin):
    list_display=('index', 'scenario', 
    'year18', 'year19', 'year20', 'year21',
    'year22', 'year23', 'year24', 'year25',
    'year26', 'year27', 'year28', 'year29', 
    'year30', 'year31', 'year32', 'year33',
    'year34', 'year35', 'year36', 'year37',
    'year38', 'year39', 'year40')

admin.site.register(hpFES, hpFESAdmin)

class pvFESAdmin(admin.ModelAdmin):
    list_display=('index', 'scenario', 
    'year18', 'year19', 'year20', 'year21',
    'year22', 'year23', 'year24', 'year25',
    'year26', 'year27', 'year28', 'year29', 
    'year30', 'year31', 'year32', 'year33',
    'year34', 'year35', 'year36', 'year37',
    'year38', 'year39', 'year40')

admin.site.register(pvFES, pvFESAdmin)

class storageFESAdmin(admin.ModelAdmin):
    list_display=('index', 'scenario', 
    'year18', 'year19', 'year20', 'year21',
    'year22', 'year23', 'year24', 'year25',
    'year26', 'year27', 'year28', 'year29', 
    'year30', 'year31', 'year32', 'year33',
    'year34', 'year35', 'year36', 'year37',
    'year38', 'year39', 'year40')

admin.site.register(storageFES, storageFESAdmin)

class subPVFESAdmin(admin.ModelAdmin):
    list_display=('index', 'scenario', 
    'year18', 'year19', 'year20', 'year21',
    'year22', 'year23', 'year24', 'year25',
    'year26', 'year27', 'year28', 'year29', 
    'year30', 'year31', 'year32', 'year33',
    'year34', 'year35', 'year36', 'year37',
    'year38', 'year39', 'year40')

admin.site.register(subPVFES, subPVFESAdmin)

class subStorageFESAdmin(admin.ModelAdmin):
    list_display=('index', 'scenario', 
    'year18', 'year19', 'year20', 'year21',
    'year22', 'year23', 'year24', 'year25',
    'year26', 'year27', 'year28', 'year29', 
    'year30', 'year31', 'year32', 'year33',
    'year34', 'year35', 'year36', 'year37',
    'year38', 'year39', 'year40')

admin.site.register(subStorageFES, subStorageFESAdmin)

class subWindFESAdmin(admin.ModelAdmin):
    list_display=('index', 'scenario', 
    'year18', 'year19', 'year20', 'year21',
    'year22', 'year23', 'year24', 'year25',
    'year26', 'year27', 'year28', 'year29', 
    'year30', 'year31', 'year32', 'year33',
    'year34', 'year35', 'year36', 'year37',
    'year38', 'year39', 'year40')

admin.site.register(subWindFES, subWindFESAdmin)

class windFESAdmin(admin.ModelAdmin):
    list_display=('index', 'scenario', 
    'year18', 'year19', 'year20', 'year21',
    'year22', 'year23', 'year24', 'year25',
    'year26', 'year27', 'year28', 'year29', 
    'year30', 'year31', 'year32', 'year33',
    'year34', 'year35', 'year36', 'year37',
    'year38', 'year39', 'year40')

admin.site.register(windFES, windFESAdmin)




