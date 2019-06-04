from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'whole-system/$', views.whole_input_form, name='wholeInput'),
    url(r'whole-system/plot/$', views.whole_plot, name='wholePlot'),
    url(r'whole-system/data/$', views.whole_data, name='wholeData'),
    url(r'whole-system-num/$', views.whole_input_form_num, name='wholeInputNum'),
    url(r'whole-system-num/plot/$', views.whole_plot_num, name='wholePlotNum'),
    url(r'whole-system-num/data', views.whole_data_num, name='wholeDataNum'),
    ]
