from django.urls import path
from . import views

urlpatterns = [
    path('', views.candidate_list, name='candidate_list'),
    path('add/', views.candidate_add, name='candidate_add'),
    path('<int:pk>/', views.candidate_detail, name='candidate_detail'),
    path('<int:pk>/edit/', views.candidate_edit, name='candidate_edit'),
    path('<int:pk>/delete/', views.candidate_delete, name='candidate_delete'),
]