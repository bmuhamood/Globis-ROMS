from django.urls import path
from . import views

urlpatterns = [
    path('', views.visa_list, name='visa_list'),
    path('progress/', views.visa_progress, name='visa_progress'),
    path('<int:pk>/update/', views.visa_update, name='visa_update'),
]