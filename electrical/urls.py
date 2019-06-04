from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'electrical/input-form/$', views.electrical_form, name='electricalInput'),
    url(r'electrical/demand-plots/$', views.plot_electrical, name='electricalPlot'),
    url(r'electrical/demand-data/$', views.data_electrical, name='electricalData'),
    url(r'electrical/input-form-compare/$', views.electrical_form_compare, name='electricalInputCompare'),
    url(r'electrical/demand-plots-compare/$', views.plot_electrical_compare, name='electricalPlotCompare'),
    url(r'electrical/demand-data-compare/$', views.data_electrical_compare, name='electricalDataCompare')
    ]
