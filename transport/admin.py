from django.contrib import admin

# Register your models here.

from .models import Journey
from .models import gspLocalAuthority

#admin.site.register(Journey)

class JourneyAdmin(admin.ModelAdmin):
    list_display=('start_journey','journey_distance', 'second_journey_distance','speed','localAuthority','Area','typeEV')


admin.site.register(Journey, JourneyAdmin)

class gspLocalAuthorityAdmin(admin.ModelAdmin):
    list_display=('gsp','localAuthority')

admin.site.register(gspLocalAuthority, gspLocalAuthorityAdmin)
