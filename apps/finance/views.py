from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta, datetime
from apps.accounts.decorators import permission_required
from apps.accounts.models import log_activity
from .models import Income, Expense
from apps.clients.models import Client
from apps.candidate_payments.models import CandidatePayment

@login_required
@permission_required('view_finance')  # Staff doesn't have this permission
def finance_dashboard(request):
    # This view is completely blocked for staff
    total_candidate_payments = CandidatePayment.objects.aggregate(total=Sum('amount'))['total'] or 0
    total_income = Income.objects.aggregate(total=Sum('amount'))['total'] or 0
    total_expenses = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0
    cash_in_hand = total_candidate_payments + total_income - total_expenses
    
    today = timezone.now().date()
    today_income = Income.objects.filter(date=today).aggregate(total=Sum('amount'))['total'] or 0
    today_expenses = Expense.objects.filter(date=today).aggregate(total=Sum('amount'))['total'] or 0
    
    recent_income = Income.objects.select_related('client', 'received_by').all()[:5]
    recent_expenses = Expense.objects.all()[:5]
    
    last_30_days = today - timedelta(days=30)
    monthly_income = Income.objects.filter(date__gte=last_30_days).aggregate(total=Sum('amount'))['total'] or 0
    monthly_expenses = Expense.objects.filter(date__gte=last_30_days).aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'cash_in_hand': cash_in_hand,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'today_income': today_income,
        'today_expenses': today_expenses,
        'recent_income': recent_income,
        'recent_expenses': recent_expenses,
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
    }
    
    log_activity(
        user=request.user,
        action='VIEW',
        model_type='Finance',
        details="Viewed finance dashboard",
        request=request
    )
    
    return render(request, 'finance/dashboard.html', context)

@login_required
@permission_required('view_income')  # Staff doesn't have this
def income_list(request):
    incomes = Income.objects.select_related('client', 'received_by').all()
    total = incomes.aggregate(total=Sum('amount'))['total'] or 0
    
    log_activity(
        user=request.user,
        action='VIEW',
        model_type='Finance',
        details="Viewed income list",
        request=request
    )
    
    return render(request, 'finance/income_list.html', {'incomes': incomes, 'total': total})

@login_required
@permission_required('add_income')  # Staff doesn't have this
def income_add(request):
    if request.method == 'POST':
        income = Income.objects.create(
            client_id=request.POST.get('client'),
            amount=request.POST.get('amount'),
            date=request.POST.get('date'),
            description=request.POST.get('description'),
            received_by=request.user
        )
        
        log_activity(
            user=request.user,
            action='CREATE',
            model_type='Finance',
            object_id=income.id,
            object_repr=f"Income UGX{income.amount}",
            details=f"Added income of UGX{income.amount} from client ID {income.client_id}",
            request=request
        )
        
        messages.success(request, 'Income recorded successfully.')
        return redirect('income_list')
    
    clients = Client.objects.all()
    return render(request, 'finance/income_form.html', {'clients': clients})

@login_required
@permission_required('view_expenses')  # Staff doesn't have this
def expense_list(request):
    expenses = Expense.objects.select_related('paid_by').all()
    total = expenses.aggregate(total=Sum('amount'))['total'] or 0
    
    log_activity(
        user=request.user,
        action='VIEW',
        model_type='Finance',
        details="Viewed expense list",
        request=request
    )
    
    return render(request, 'finance/expense_list.html', {'expenses': expenses, 'total': total})

@login_required
@permission_required('add_expense')  # Staff doesn't have this
def expense_add(request):
    if request.method == 'POST':
        expense = Expense.objects.create(
            category=request.POST.get('category'),
            amount=request.POST.get('amount'),
            date=request.POST.get('date'),
            description=request.POST.get('description'),
            paid_by=request.user
        )
        
        log_activity(
            user=request.user,
            action='CREATE',
            model_type='Finance',
            object_id=expense.id,
            object_repr=f"Expense UGX{expense.amount}",
            details=f"Added expense of UGX{expense.amount} for {expense.category}",
            request=request
        )
        
        messages.success(request, 'Expense recorded successfully.')
        return redirect('expense_list')
    
    return render(request, 'finance/expense_form.html')

@login_required
@permission_required('delete_expense')  # Staff doesn't have this
def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    amount = expense.amount
    category = expense.category
    expense.delete()
    
    log_activity(
        user=request.user,
        action='DELETE',
        model_type='Finance',
        object_repr=f"Expense UGX{amount}",
        details=f"Deleted expense of UGX{amount} for {category}",
        request=request
    )
    
    messages.success(request, 'Expense deleted successfully.')
    return redirect('expense_list')