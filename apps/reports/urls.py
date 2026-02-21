from django.urls import path
from . import views

urlpatterns = [
    path('', views.report_list, name='report_list'),
    path('candidates/', views.candidate_report, name='candidate_report'),
    path('clients/', views.client_report, name='client_report'),
    path('agents/', views.agent_report, name='agent_report'),
    path('finance/', views.finance_report, name='finance_report'),
    path('missing-documents/', views.missing_documents_report, name='missing_documents_report'),
    path('visa-status/', views.visa_status_report, name='visa_status_report'),
    path('payments/', views.payment_report, name='payment_report'),
    path('loans/', views.loan_report, name='loan_report'),
]