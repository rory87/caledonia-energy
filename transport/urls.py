from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^transport/input-form/$',views.transport_input_form, name='transportInput'),
    url(r'transport/input-form-ev-only/$', views.input_form_ev_only, name='transportInputEV'),
    url(r'transport/charge-plots/$', views.plot_charge_demand, name='transportPlot'),
    url(r'transport/charge-data/$', views.data_charge_demand, name='transportData'),
    url(r'transport/charge-plots-ev/$', views.plot_ev_demand, name='transportPlotEV'),
    url(r'transport/input-form-ev-compare/$',views.input_form_ev_compare, name='transportInputEVCompare'),
    url(r'transport/charge-plots-ev-compare/$', views.plot_ev_demand_compare, name='transportPlotEVCompare'),
    ]
