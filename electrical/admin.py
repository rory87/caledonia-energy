from django.contrib import admin

# Register your models here.

from .models import electricalGSP
from .models import electricalPrimarySSE

class electricalGSPAdmin(admin.ModelAdmin):
    list_display = ('hour', 'GSP', 'electricalDemand')

admin.site.register(electricalGSP, electricalGSPAdmin)


class electricalPrimarySSEAdmin(admin.ModelAdmin):
    list_display = ('hour', 'primary', 'electricalDemand')

admin.site.register(electricalPrimarySSE, electricalPrimarySSEAdmin)
    
