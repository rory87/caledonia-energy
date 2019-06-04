from django.conf.urls import url
from django.contrib.auth import views as auth_views
from django.conf.urls import include
from django.views.generic import RedirectView
from django.conf.urls.static import static
from django.conf import settings
from . import views
from django.core.urlresolvers import reverse_lazy

urlpatterns = [
    url(r'^$', views.home, name='home'), #this was in transport
    url(r'^signup/$', views.signup, name='signup'), #this was in transport
    url(r'^login/$', auth_views.login, {'template_name': 'home/login.html'}, name='login'),
    url(r'^logout/$', auth_views.logout, {'next_page': reverse_lazy('home')}, name="logout"),
    url(r'^about/$', views.about, name='about'),
               ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

