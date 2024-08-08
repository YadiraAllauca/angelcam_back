from django.contrib import admin
from django.urls import path
from cameras.views import home, login, get_cameras

urlpatterns = [
    path('', home),
    path('api/login/', login),
    path('api/cameras/', get_cameras),
    path('admin/', admin.site.urls)
]
