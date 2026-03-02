from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import timedelta, datetime
from django.views.decorators.http import require_POST
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
    
    recent_income = Income.objects.select_related('client', 'received_by').all().order_by('-date')[:5]
    recent_expenses = Expense.objects.select_related('paid_by').all().order_by('-date')[:5]
    
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

# ============ INCOME VIEWS ============

@login_required
@permission_required('view_income')
def income_list(request):
    incomes = Income.objects.select_related('client', 'received_by').all().order_by('-date')
    total = incomes.aggregate(total=Sum('amount'))['total'] or 0
    
    # Date range filter
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        incomes = incomes.filter(date__gte=date_from)
    if date_to:
        incomes = incomes.filter(date__lte=date_to)
    
    # Client filter
    client_filter = request.GET.get('client')
    if client_filter:
        incomes = incomes.filter(client_id=client_filter)
    
    log_activity(
        user=request.user,
        action='VIEW',
        model_type='Income',
        details="Viewed income list",
        request=request
    )
    
    context = {
        'incomes': incomes,
        'total': total,
        'clients': Client.objects.all(),
        'date_from': date_from,
        'date_to': date_to,
        'client_filter': client_filter,
    }
    return render(request, 'finance/income_list.html', context)

@login_required
@permission_required('add_income')
def income_add(request):
    if request.method == 'POST':
        income = Income.objects.create(
            client_id=request.POST.get('client'),
            amount=request.POST.get('amount'),
            date=request.POST.get('date'),
            payment_method=request.POST.get('payment_method', ''),
            category=request.POST.get('category', ''),
            reference=request.POST.get('reference', ''),
            description=request.POST.get('description', ''),
            received_by=request.user
        )
        
        log_activity(
            user=request.user,
            action='CREATE',
            model_type='Income',
            object_id=income.id,
            object_repr=f"Income UGX{income.amount}",
            details=f"Added income of UGX{income.amount} from {income.client.company_name if income.client else 'Unknown'}",
            request=request
        )
        
        messages.success(request, 'Income recorded successfully.')
        return redirect('income_list')
    
    clients = Client.objects.all()
    return render(request, 'finance/income_form.html', {'clients': clients})

@login_required
@permission_required('change_income')
def income_edit(request, pk):
    income = get_object_or_404(Income, pk=pk)
    
    if request.method == 'POST':
        old_amount = income.amount
        old_client = income.client.company_name if income.client else 'Unknown'
        
        income.client_id = request.POST.get('client')
        income.amount = request.POST.get('amount')
        income.date = request.POST.get('date')
        income.payment_method = request.POST.get('payment_method', '')
        income.category = request.POST.get('category', '')
        income.reference = request.POST.get('reference', '')
        income.description = request.POST.get('description', '')
        income.save()
        
        log_activity(
            user=request.user,
            action='UPDATE',
            model_type='Income',
            object_id=income.id,
            object_repr=f"Income UGX{income.amount}",
            details=f"Updated income from UGX{old_amount} to UGX{income.amount} for {old_client}",
            request=request
        )
        
        messages.success(request, 'Income updated successfully.')
        return redirect('income_list')
    
    clients = Client.objects.all()
    context = {
        'income': income,
        'clients': clients,
        'is_edit': True
    }
    return render(request, 'finance/income_form.html', context)

@login_required
@permission_required('delete_income')
@require_POST
def income_delete(request, pk):
    income = get_object_or_404(Income, pk=pk)
    amount = income.amount
    client_name = income.client.company_name if income.client else 'Unknown'
    
    income.delete()
    
    log_activity(
        user=request.user,
        action='DELETE',
        model_type='Income',
        object_repr=f"Income UGX{amount}",
        details=f"Deleted income of UGX{amount} from {client_name}",
        request=request
    )
    
    messages.success(request, f'Income of UGX{amount} deleted successfully.')
    return redirect('income_list')

# ============ EXPENSE VIEWS ============

@login_required
@permission_required('view_expenses')
def expense_list(request):
    expenses = Expense.objects.select_related('paid_by').all().order_by('-date')
    total = expenses.aggregate(total=Sum('amount'))['total'] or 0
    
    # Date range filter
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        expenses = expenses.filter(date__gte=date_from)
    if date_to:
        expenses = expenses.filter(date__lte=date_to)
    
    # Category filter
    category_filter = request.GET.get('category')
    if category_filter:
        expenses = expenses.filter(category=category_filter)
    
    # Get unique categories for filter dropdown
    categories = Expense.objects.values_list('category', flat=True).distinct().order_by('category')
    
    log_activity(
        user=request.user,
        action='VIEW',
        model_type='Expense',
        details="Viewed expense list",
        request=request
    )
    
    context = {
        'expenses': expenses,
        'total': total,
        'categories': categories,
        'date_from': date_from,
        'date_to': date_to,
        'category_filter': category_filter,
    }
    return render(request, 'finance/expense_list.html', context)

@login_required
@permission_required('add_expense')
def expense_add(request):
    if request.method == 'POST':
        expense = Expense.objects.create(
            category=request.POST.get('category'),
            amount=request.POST.get('amount'),
            date=request.POST.get('date'),
            payment_method=request.POST.get('payment_method', ''),
            reference=request.POST.get('reference', ''),
            description=request.POST.get('description', ''),
            paid_by=request.user
        )
        
        log_activity(
            user=request.user,
            action='CREATE',
            model_type='Expense',
            object_id=expense.id,
            object_repr=f"Expense UGX{expense.amount}",
            details=f"Added expense of UGX{expense.amount} for {expense.category}",
            request=request
        )
        
        messages.success(request, 'Expense recorded successfully.')
        return redirect('expense_list')
    
    return render(request, 'finance/expense_form.html')

@login_required
@permission_required('change_expense')
def expense_edit(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    
    if request.method == 'POST':
        old_amount = expense.amount
        old_category = expense.category
        
        expense.category = request.POST.get('category')
        expense.amount = request.POST.get('amount')
        expense.date = request.POST.get('date')
        expense.payment_method = request.POST.get('payment_method', '')
        expense.reference = request.POST.get('reference', '')
        expense.description = request.POST.get('description', '')
        expense.save()
        
        log_activity(
            user=request.user,
            action='UPDATE',
            model_type='Expense',
            object_id=expense.id,
            object_repr=f"Expense UGX{expense.amount}",
            details=f"Updated expense from UGX{old_amount} to UGX{expense.amount} for {old_category}",
            request=request
        )
        
        messages.success(request, 'Expense updated successfully.')
        return redirect('expense_list')
    
    context = {
        'expense': expense,
        'is_edit': True
    }
    return render(request, 'finance/expense_form.html', context)

@login_required
@permission_required('delete_expense')
@require_POST
def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    amount = expense.amount
    category = expense.category
    
    expense.delete()
    
    log_activity(
        user=request.user,
        action='DELETE',
        model_type='Expense',
        object_repr=f"Expense UGX{amount}",
        details=f"Deleted expense of UGX{amount} for {category}",
        request=request
    )
    
    messages.success(request, f'Expense of UGX{amount} deleted successfully.')
    return redirect('expense_list')