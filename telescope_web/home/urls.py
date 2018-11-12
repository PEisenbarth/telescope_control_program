from django.conf.urls import url
from . import views

urlpatterns = [
    url('home', views.index, name='index'),
    url('track', views.tracks, name='track'),
    url('pointing', views.pointing, name='pointing'),
    url('tel_settings', views.tel_settings, name='tel_settings'),
    url('password', views.change_password, name='change_password'),
    url(r'^$', views.index, name='index'),
    url('updated_content', views.updated_content, name='update')
]