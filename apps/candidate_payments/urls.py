from django.urls import path
from . import views

urlpatterns = [
    path('', views.payment_list, name='payment_list'),
    path('add/', views.payment_add, name='payment_add'),
    path('<int:pk>/edit/', views.payment_edit, name='payment_edit'),
    path('<int:pk>/delete/', views.payment_delete, name='payment_delete'),
    path('<int:pk>/receipt/', views.payment_receipt, name='payment_receipt'),
    path('<int:pk>/upload-receipt/', views.payment_receipt_upload, name='payment_receipt_upload'),
    path('<int:pk>/receipt/download/', views.payment_receipt_download, name='payment_receipt_download'),
    path('loan-history/<int:candidate_id>/', views.loan_payment_history, name='loan_payment_history'),
    path('create-schedule/<int:candidate_id>/', views.create_payment_schedule, name='create_payment_schedule'),
]