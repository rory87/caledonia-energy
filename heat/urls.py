from django.conf.urls import url
from . import views



urlpatterns = [
    url(r'heat/input-form/$',views.heat_form, name='heatInput'),
    url(r'heat/display/$', views.data_heat, name='heatData'),
    url(r'heat/demand-plots.png$', views.plot_heat, name='heatPlot'),
    url(r'heat/compare-plots/$', views.heat_form_compare, name='comparePlots'),
    url(r'heat/demand-plots-2.png/$',views.compare_heat_plot, name='heatPlot2'),
    url(r'heat/industrial-input-form/$', views.heat_form_industrial, name='heatInputIndustrial'),
    url(r'heat/display-industrial/$', views.data_heat_industrial, name='heatDataIndustrial'),
    url(r'heat/industial-demand-plots/$', views.plot_heat_industrial, name='heatPlotIndustrial'),
    url(r'heat/house-sizes/$', views.house_sizes, name='houseSizes')
    ]
