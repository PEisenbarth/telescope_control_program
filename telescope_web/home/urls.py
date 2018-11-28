from django.conf.urls import url
from . import views

urlpatterns = [
    url('home', views.index, name='index'),
    url('track', views.tracks, name='track'),
    url('pointing', views.pointing, name='pointing'),
    url('tel_settings', views.tel_settings, name='tel_settings'),
    url('password', views.change_password, name='change_password'),
    url('lines', views.lines, name='lines'),
    url('select_data', views.select_data, name='data'),
    url('updated_content', views.updated_content, name='update'),
    url('roach_plot', views.roach_plot, name='roach_plot'),
    url(r'^$', views.index, name='index'),
]