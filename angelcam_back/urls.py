from django.contrib import admin
from django.urls import path
from cameras import views

urlpatterns = [
    path('', views.home),
    path('api/login/', views.login),
    path('api/cameras/', views.get_cameras),
    path('api/stream/<int:camera_id>/', views.get_camera_stream),
    path('api/recording-info/<int:camera_id>/', views.get_recording_info),
    path('api/recording-stream/<int:camera_id>/', views.get_recording_stream),
    path('api/recording-timeline/<int:camera_id>/', views.get_recording_timeline),
    path('admin/', admin.site.urls)
]
