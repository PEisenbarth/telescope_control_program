from django.conf.urls import url
from . import views

urlpatterns = [
    url('home', views.index, name='index'),
    url('track', views.tracks, name='track'),
    url('pointing', views.pointing, name='pointing'),
    url(r'^$', views.index, name='index'),
    url('updated_content', views.updated_content, name='update')
]
