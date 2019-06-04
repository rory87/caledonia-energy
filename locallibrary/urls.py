"""locallibrary URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls import include
from django.views.generic import RedirectView
from django.conf.urls.static import static
from django.conf import settings
from . import views
from django.core.urlresolvers import reverse_lazy
from django.views.static import serve


urlpatterns = [
    url(r'^admin/', admin.site.urls), 
    url(r'^', include('transport.urls')),
    url(r'^', include('heat.urls')),
    url(r'^', include('home.urls')),
    url(r'^', include('electrical.urls')),
    url(r'^', include('energyStorage.urls')),
    #url(r'^', include('maps.urls')),
    url(r'^', include('generation.urls')),
    url(r'^', include('electricHeat.urls')),
    url(r'^', include('whole.urls')),
    url(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}),
    url(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),
        ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


