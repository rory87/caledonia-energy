from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'storage/input-form-plot/$', views.storage_form_plot, name='storageInputPlot'),
    url(r'storage/input-form-sizing/$', views.storage_form_sizing, name='storageInputSizing'),
    url(r'storage/storage-gsp-plot/$', views.plot_gsp_storage, name='gspPlot'),
    url(r'storage/sizing-details/$', views.sizing_storage, name='sizingStorage'),
    url(r'storage/storage-gsp-data/$', views.data_gsp_storage, name='gspData'),
    ]
