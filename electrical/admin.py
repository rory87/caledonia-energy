from django.contrib import admin

# Register your models here.

from .models import electricalGSP

class electricalGSPAdmin(admin.ModelAdmin):
    list_display = ('hour', 'GSP', 'electricalDemand')

admin.site.register(electricalGSP, electricalGSPAdmin)
