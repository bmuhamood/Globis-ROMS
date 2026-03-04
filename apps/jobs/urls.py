from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    # Public URLs
    path('', views.job_list, name='job_list'),
    path('<int:pk>/', views.job_detail, name='job_detail'),
    path('<int:pk>/print/', views.print_job, name='print_job'),
    path('attachment/<int:pk>/download/', views.download_attachment, name='download_attachment'),
    
    # Admin URLs
    path('admin/list/', views.admin_job_list, name='admin_job_list'),
    path('admin/create/', views.admin_job_create, name='admin_job_create'),
    path('admin/<int:pk>/edit/', views.admin_job_edit, name='admin_job_edit'),
    path('admin/<int:pk>/delete/', views.admin_job_delete, name='admin_job_delete'),
    path('admin/attachment/<int:pk>/delete/', views.admin_delete_attachment, name='admin_delete_attachment'),
]