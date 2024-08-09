from django.contrib import admin
from django.urls import path
from cameras.views import home, login, get_cameras, get_camera_stream

urlpatterns = [
    path('', home),
    path('api/login/', login),
    path('api/cameras/', get_cameras),
    path('api/stream/<int:camera_id>/', get_camera_stream),
    path('admin/', admin.site.urls)
]
