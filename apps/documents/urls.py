from django.urls import path
from . import views

urlpatterns = [
    path('', views.document_list, name='document_list'),
    path('missing/', views.missing_documents, name='missing_documents'),
    path('<int:pk>/update/', views.document_update, name='document_update'),
]