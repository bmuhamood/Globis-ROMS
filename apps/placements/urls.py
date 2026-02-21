from django.urls import path
from . import views

urlpatterns = [
    path('', views.placement_list, name='placement_list'),
    path('add/', views.placement_add, name='placement_add'),
    path('<int:pk>/edit/', views.placement_edit, name='placement_edit'),
    path('<int:pk>/delete/', views.placement_delete, name='placement_delete'),
]