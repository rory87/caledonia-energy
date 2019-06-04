from django.contrib import admin

# Register your models here.

from .models import industrialBreakdown
from .models import industrialNumbers

class industrialBreakdownAdmin(admin.ModelAdmin):
    list_display=('hour', 'GSP', 'manufacturing', 'commercial', 'entertainment', 'education')

admin.site.register(industrialBreakdown, industrialBreakdownAdmin)

class industrialNumbersAdmin(admin.ModelAdmin):
    list_display=('GSP', 'manufacturing', 'commercial', 'entertainment', 'education')

admin.site.register(industrialNumbers, industrialNumbersAdmin)
