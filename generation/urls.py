from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'generation/pv-input-form/$', views.pv_form, name='pvInput'),
    url(r'generation/pv-plot/$', views.pv_plot, name='plotPV'),
    url(r'generation/pv-data/$', views.pv_data, name='dataPV'),
    url(r'generation/wind-input-form/$', views.wind_form, name='windInput'),
    url(r'generation/wind-plot/$', views.wind_plot, name='plotWind'),
    url(r'generation/wind-data/$', views.wind_data, name='dataWind'),
    ]
