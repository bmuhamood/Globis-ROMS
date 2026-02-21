from django.urls import path
from . import views

urlpatterns = [
    path('', views.import_excel, name='import_excel'),
    path('download-template/', views.download_template, name='download_template'),
]