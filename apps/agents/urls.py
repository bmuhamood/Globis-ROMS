from django.urls import path
from . import views

urlpatterns = [
    path('', views.agent_list, name='agent_list'),
    path('add/', views.agent_add, name='agent_add'),
    path('<int:pk>/edit/', views.agent_edit, name='agent_edit'),
    path('<int:pk>/delete/', views.agent_delete, name='agent_delete'),
]