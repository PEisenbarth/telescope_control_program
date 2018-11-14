from django.conf.urls import url
from django.contrib import admin
from django.conf.urls import include
from django.contrib.auth.views import login, logout

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url('login', login, name='login'),
    url('logout', logout, name='logout'),
    url('', include('home.urls'))
]
