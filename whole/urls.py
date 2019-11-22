from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'whole-system/$', views.whole_input_form, name='wholeInput'),
    url(r'whole-system/plot/$', views.whole_plot, name='wholePlot'),
    url(r'whole-system/data/$', views.whole_data, name='wholeData'),
    url(r'whole-system-num/$', views.whole_input_form_num, name='wholeInputNum'),
    url(r'whole-system-num/plot/$', views.whole_plot_num, name='wholePlotNum'),
    url(r'whole-system-num/data', views.whole_data_num, name='wholeDataNum'),
    url(r'whole-system-pri/$', views.whole_primary_form, name='wholePrimary'),
    url(r'whole-system-pri/plot/$', views.whole_primary_plot, name='wholePrimaryPlot'),
    url(r'FES18/$', views.fes18_form, name='fes18Form'),
    url(r'FES18/analysis/$', views.fes18_analysis, name='fes18Analysis'),
    url(r'FES18/annual/$', views.fes18Annual_form, name='fes18AnnualForm'),
    url(r'FES18/annual/analysis/$', views.fes18Annual_analysis, name='fes18AnnualAnalysis'),
    ]
