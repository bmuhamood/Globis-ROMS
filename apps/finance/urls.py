from django.urls import path
from . import views

urlpatterns = [
    path('', views.finance_dashboard, name='finance_dashboard'),
    
    # Income URLs
    path('income/', views.income_list, name='income_list'),
    path('income/add/', views.income_add, name='income_add'),
    path('income/<int:pk>/edit/', views.income_edit, name='income_edit'),
    path('income/<int:pk>/delete/', views.income_delete, name='income_delete'),
    path('<int:pk>/detail/', views.income_detail, name='income_detail'),
    
    # Expense URLs
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/add/', views.expense_add, name='expense_add'),
    path('expenses/<int:pk>/edit/', views.expense_edit, name='expense_edit'),
    path('expenses/<int:pk>/delete/', views.expense_delete, name='expense_delete'),
    path('expenses/<int:pk>/detail/', views.expense_detail, name='expense_detail'),

    # Capital injection URLs
    path('capital/', views.capital_list, name='capital_list'),
    path('capital/add/', views.capital_add, name='capital_add'),
    path('capital/<int:pk>/edit/', views.capital_edit, name='capital_edit'),
    path('capital/<int:pk>/delete/', views.capital_delete, name='capital_delete'),
    path('capital/<int:pk>/detail/', views.capital_detail, name='capital_detail'),

    # Cash position URL
    path('cash-position/', views.cash_position, name='cash_position'),
]