from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'heat-electric/storage-heater/$', views.storage_heater_input_form, name='storageHeaterInputForm'),
    url(r'heat-electric/storage-plot/$', views.storage_heater_plot, name='storageHeaterPlot'),
    url(r'heat-electric/storage-data/$', views.storage_heater_data,  name='storageHeaterData'),
    url(r'heat-electric/industrial/$', views.industrial_electric_input_form, name='industrialHeaterInputForm'),
    url(r'heat-electric/industrial-plot/$', views.industrial_electric_plot, name='industrialHeaterPlot'),
    url(r'heat-electric/industrial-data/$', views.industrial_electric_data, name='industrialHeaterData'),
    ]
