from django.urls import path
from . import views
urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_file, name='upload'),
    path('export_csv/', views.export_csv, name='export_csv'),
    path('send_email/', views.send_email, name='send_email'),
]
