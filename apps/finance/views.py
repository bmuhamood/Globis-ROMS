from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q, Count
from django.utils import timezone
from datetime import timedelta, datetime
from django.views.decorators.http import require_POST
from apps.accounts.decorators import permission_required
from apps.accounts.models import log_activity
from .models import Income, Expense, CapitalInjection, CashPosition
from apps.clients.models import Client
from apps.candidate_payments.models import CandidatePayment

# ============ FINANCE DASHBOARD ============

@login_required
@permission_required('view_finance')
def finance_dashboard(request):
    today = timezone.now().date()
    first_day_of_month = today.replace(day=1)
    
    # Candidate payments
    total_candidate_payments = CandidatePayment.objects.aggregate(total=Sum('amount'))['total'] or 0
    today_candidate_payments = CandidatePayment.objects.filter(date=today).aggregate(total=Sum('amount'))['total'] or 0
    monthly_candidate_payments = CandidatePayment.objects.filter(date__gte=first_day_of_month).aggregate(total=Sum('amount'))['total'] or 0
    
    # Client payments (income from clients)
    total_client_income = Income.objects.filter(income_type='client_payment').aggregate(total=Sum('amount'))['total'] or 0
    today_client_income = Income.objects.filter(date=today, income_type='client_payment').aggregate(total=Sum('amount'))['total'] or 0
    monthly_client_income = Income.objects.filter(date__gte=first_day_of_month, income_type='client_payment').aggregate(total=Sum('amount'))['total'] or 0
    
    # Capital injections (separate model)
    total_capital = CapitalInjection.objects.aggregate(total=Sum('amount'))['total'] or 0
    today_capital = CapitalInjection.objects.filter(date=today).aggregate(total=Sum('amount'))['total'] or 0
    monthly_capital = CapitalInjection.objects.filter(date__gte=first_day_of_month).aggregate(total=Sum('amount'))['total'] or 0
    
    # OTHER INCOME TYPES - Add this!
    total_other_income = Income.objects.exclude(income_type='client_payment').aggregate(total=Sum('amount'))['total'] or 0
    today_other_income = Income.objects.filter(date=today).exclude(income_type='client_payment').aggregate(total=Sum('amount'))['total'] or 0
    monthly_other_income = Income.objects.filter(date__gte=first_day_of_month).exclude(income_type='client_payment').aggregate(total=Sum('amount'))['total'] or 0
    
    # Total income (ALL money from Income model + Capital)
    total_income_from_income_model = Income.objects.aggregate(total=Sum('amount'))['total'] or 0
    total_income = total_income_from_income_model + total_capital
    
    # Total money in (all sources)
    total_money_in = total_income_from_income_model + total_capital + total_candidate_payments
    
    # Today's totals
    today_income_from_income = Income.objects.filter(date=today).aggregate(total=Sum('amount'))['total'] or 0
    today_income = today_income_from_income + today_capital
    
    # Monthly totals
    monthly_income_from_income = Income.objects.filter(date__gte=first_day_of_month).aggregate(total=Sum('amount'))['total'] or 0
    monthly_income = monthly_income_from_income + monthly_capital
    
    # Expenses
    total_expenses = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0
    today_expenses = Expense.objects.filter(date=today).aggregate(total=Sum('amount'))['total'] or 0
    monthly_expenses = Expense.objects.filter(date__gte=first_day_of_month).aggregate(total=Sum('amount'))['total'] or 0
    
    # Cash in hand
    cash_in_hand = total_money_in - total_expenses
    
    # Net profit/loss
    net_profit = total_income - total_expenses
    
    # Recent transactions
    recent_candidate_payments = CandidatePayment.objects.select_related('candidate').all().order_by('-date')[:5]
    recent_income = Income.objects.select_related('client', 'received_by').all().order_by('-date')[:5]
    recent_expenses = Expense.objects.select_related('paid_by').all().order_by('-date')[:5]
    
    # Chart data (update to include all income)
    months = []
    income_data = []
    expense_data = []
    capital_data = []
    candidate_payment_data = []
    client_income_data = []
    
    for i in range(5, -1, -1):
        month_date = today - timedelta(days=30*i)
        month_start = datetime(month_date.year, month_date.month, 1).date()
        if month_date.month == 12:
            month_end = datetime(month_date.year + 1, 1, 1).date() - timedelta(days=1)
        else:
            month_end = datetime(month_date.year, month_date.month + 1, 1).date() - timedelta(days=1)
        
        month_income = Income.objects.filter(date__range=[month_start, month_end]).aggregate(total=Sum('amount'))['total'] or 0
        month_expense = Expense.objects.filter(date__range=[month_start, month_end]).aggregate(total=Sum('amount'))['total'] or 0
        month_capital = CapitalInjection.objects.filter(date__range=[month_start, month_end]).aggregate(total=Sum('amount'))['total'] or 0
        month_candidate = CandidatePayment.objects.filter(date__range=[month_start, month_end]).aggregate(total=Sum('amount'))['total'] or 0
        month_client = Income.objects.filter(date__range=[month_start, month_end], income_type='client_payment').aggregate(total=Sum('amount'))['total'] or 0
        
        months.append(month_date.strftime('%b %Y'))
        income_data.append(float(month_income))
        expense_data.append(float(month_expense))
        capital_data.append(float(month_capital))
        candidate_payment_data.append(float(month_candidate))
        client_income_data.append(float(month_client))
    
    # Expense breakdown
    expense_by_category = Expense.objects.values('category').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    context = {
        'cash_in_hand': cash_in_hand,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'total_capital': total_capital,
        'total_client_income': total_client_income,
        'total_candidate_payments': total_candidate_payments,
        'total_other_income': total_other_income,  # Add this
        'total_money_in': total_money_in,
        'net_profit': net_profit,
        'today_income': today_income,
        'today_expenses': today_expenses,
        'today_capital': today_capital,
        'today_candidate_payments': today_candidate_payments,
        'today_client_income': today_client_income,
        'today_other_income': today_other_income,  # Add this
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'monthly_capital': monthly_capital,
        'monthly_candidate_payments': monthly_candidate_payments,
        'monthly_client_income': monthly_client_income,
        'monthly_other_income': monthly_other_income,  # Add this
        'recent_income': recent_income,
        'recent_expenses': recent_expenses,
        'recent_candidate_payments': recent_candidate_payments,
        'months': months,
        'income_data': income_data,
        'expense_data': expense_data,
        'capital_data': capital_data,
        'candidate_payment_data': candidate_payment_data,
        'client_income_data': client_income_data,
        'expense_by_category': expense_by_category,
    }
    return render(request, 'finance/dashboard.html', context)

# ============ INCOME VIEWS ============

@login_required
@permission_required('view_income')
def income_list(request):
    incomes = Income.objects.select_related('client', 'received_by').all().order_by('-date')
    total = incomes.aggregate(total=Sum('amount'))['total'] or 0
    
    # Filter by income type
    income_type = request.GET.get('income_type')
    if income_type:
        incomes = incomes.filter(income_type=income_type)
    
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
    
    # Calculate monthly total for this view
    today = timezone.now().date()
    first_day_of_month = today.replace(day=1)
    month_total = incomes.filter(date__gte=first_day_of_month).aggregate(total=Sum('amount'))['total'] or 0
    
    # Calculate average per transaction
    avg_per_transaction = total / incomes.count() if incomes.count() > 0 else 0
    
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
        'month_total': month_total,
        'avg_per_transaction': avg_per_transaction,
        'clients': Client.objects.all(),
        'date_from': date_from,
        'date_to': date_to,
        'client_filter': client_filter,
        'income_type': income_type,
        'income_types': Income.INCOME_TYPES,
    }
    return render(request, 'finance/income_list.html', context)


@login_required
@permission_required('view_income')
def income_detail(request, pk):
    """View income details"""
    income = get_object_or_404(Income.objects.select_related('client', 'received_by'), pk=pk)
    
    # Get related records
    related_incomes = Income.objects.filter(
        client=income.client
    ).exclude(pk=income.pk).order_by('-date')[:5] if income.client else []
    
    context = {
        'income': income,
        'related_incomes': related_incomes,
    }
    return render(request, 'finance/income_detail.html', context)


@login_required
@permission_required('add_income')
def income_add(request):
    if request.method == 'POST':
        income_type = request.POST.get('income_type')
        client_id = request.POST.get('client') if income_type == 'client_payment' else None
        
        income = Income.objects.create(
            client_id=client_id,
            amount=request.POST.get('amount'),
            date=request.POST.get('date'),
            income_type=income_type,
            payment_method=request.POST.get('payment_method', 'cash'),
            reference=request.POST.get('reference', ''),
            source=request.POST.get('source', ''),
            description=request.POST.get('description', ''),
            received_by=request.user
        )
        
        # Handle receipt upload if provided
        if 'receipt' in request.FILES:
            income.receipt = request.FILES['receipt']
            income.save()
        
        log_activity(
            user=request.user,
            action='CREATE',
            model_type='Income',
            object_id=income.id,
            object_repr=f"Income UGX{income.amount}",
            details=f"Added {income.get_income_type_display()} of UGX{income.amount}",
            request=request
        )
        
        messages.success(request, 'Income recorded successfully.')
        return redirect('income_list')
    
    clients = Client.objects.all()
    context = {
        'clients': clients,
        'income_types': Income.INCOME_TYPES,
        'payment_methods': Income.PAYMENT_METHODS,
    }
    return render(request, 'finance/income_form.html', context)


@login_required
@permission_required('change_income')
def income_edit(request, pk):
    income = get_object_or_404(Income, pk=pk)
    
    if request.method == 'POST':
        old_amount = income.amount
        old_type = income.get_income_type_display()
        
        income_type = request.POST.get('income_type')
        income.client_id = request.POST.get('client') if income_type == 'client_payment' else None
        income.amount = request.POST.get('amount')
        income.date = request.POST.get('date')
        income.income_type = income_type
        income.payment_method = request.POST.get('payment_method', 'cash')
        income.reference = request.POST.get('reference', '')
        income.source = request.POST.get('source', '')
        income.description = request.POST.get('description', '')
        
        # Handle receipt upload if provided
        if 'receipt' in request.FILES:
            # Delete old receipt if exists
            if income.receipt:
                income.receipt.delete(save=False)
            income.receipt = request.FILES['receipt']
        
        income.save()
        
        log_activity(
            user=request.user,
            action='UPDATE',
            model_type='Income',
            object_id=income.id,
            object_repr=f"Income UGX{income.amount}",
            details=f"Updated {old_type} from UGX{old_amount} to UGX{income.amount}",
            request=request
        )
        
        messages.success(request, 'Income updated successfully.')
        return redirect('income_detail', pk=income.id)
    
    clients = Client.objects.all()
    context = {
        'income': income,
        'clients': clients,
        'is_edit': True,
        'income_types': Income.INCOME_TYPES,
        'payment_methods': Income.PAYMENT_METHODS,
    }
    return render(request, 'finance/income_form.html', context)


@login_required
@permission_required('delete_income')
@require_POST
def income_delete(request, pk):
    income = get_object_or_404(Income, pk=pk)
    amount = income.amount
    income_type = income.get_income_type_display()
    
    # Delete receipt file if exists
    if income.receipt:
        income.receipt.delete(save=False)
    
    income.delete()
    
    log_activity(
        user=request.user,
        action='DELETE',
        model_type='Income',
        object_repr=f"Income UGX{amount}",
        details=f"Deleted {income_type} of UGX{amount}",
        request=request
    )
    
    messages.success(request, f'{income_type} of UGX{amount} deleted successfully.')
    return redirect('income_list')


# ============ CAPITAL INJECTION VIEWS ============

@login_required
@permission_required('view_finance')
def capital_list(request):
    capitals = CapitalInjection.objects.select_related('received_by').all().order_by('-date')
    total = capitals.aggregate(total=Sum('amount'))['total'] or 0
    
    # Date range filter
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        capitals = capitals.filter(date__gte=date_from)
    if date_to:
        capitals = capitals.filter(date__lte=date_to)
    
    # Source type filter
    source_type = request.GET.get('source_type')
    if source_type:
        capitals = capitals.filter(source_type=source_type)
    
    log_activity(
        user=request.user,
        action='VIEW',
        model_type='Capital',
        details="Viewed capital injections list",
        request=request
    )
    
    context = {
        'capitals': capitals,
        'total': total,
        'date_from': date_from,
        'date_to': date_to,
        'source_type': source_type,
        'source_types': CapitalInjection.SOURCE_TYPES,
    }
    return render(request, 'finance/capital_list.html', context)


@login_required
@permission_required('add_finance')
def capital_add(request):
    if request.method == 'POST':
        capital = CapitalInjection.objects.create(
            date=request.POST.get('date'),
            amount=request.POST.get('amount'),
            source_type=request.POST.get('source_type', 'owner'),
            source_name=request.POST.get('source_name'),
            reference=request.POST.get('reference', ''),
            description=request.POST.get('description', ''),
            received_by=request.user
        )
        
        # Handle receipt upload if provided
        if 'receipt' in request.FILES:
            capital.receipt = request.FILES['receipt']
            capital.save()
        
        log_activity(
            user=request.user,
            action='CREATE',
            model_type='Capital',
            object_id=capital.id,
            object_repr=f"Capital UGX{capital.amount}",
            details=f"Added capital injection of UGX{capital.amount} from {capital.source_name}",
            request=request
        )
        
        messages.success(request, 'Capital injection recorded successfully.')
        return redirect('capital_list')
    
    context = {
        'source_types': CapitalInjection.SOURCE_TYPES,
    }
    return render(request, 'finance/capital_form.html', context)


@login_required
@permission_required('change_finance')
def capital_edit(request, pk):
    capital = get_object_or_404(CapitalInjection, pk=pk)
    
    if request.method == 'POST':
        old_amount = capital.amount
        
        capital.date = request.POST.get('date')
        capital.amount = request.POST.get('amount')
        capital.source_type = request.POST.get('source_type')
        capital.source_name = request.POST.get('source_name')
        capital.reference = request.POST.get('reference', '')
        capital.description = request.POST.get('description', '')
        
        # Handle receipt upload if provided
        if 'receipt' in request.FILES:
            if capital.receipt:
                capital.receipt.delete(save=False)
            capital.receipt = request.FILES['receipt']
        
        capital.save()
        
        log_activity(
            user=request.user,
            action='UPDATE',
            model_type='Capital',
            object_id=capital.id,
            object_repr=f"Capital UGX{capital.amount}",
            details=f"Updated capital injection from UGX{old_amount} to UGX{capital.amount}",
            request=request
        )
        
        messages.success(request, 'Capital injection updated successfully.')
        return redirect('capital_list')
    
    context = {
        'capital': capital,
        'is_edit': True,
        'source_types': CapitalInjection.SOURCE_TYPES,
    }
    return render(request, 'finance/capital_form.html', context)


@login_required
@permission_required('delete_finance')
@require_POST
def capital_delete(request, pk):
    capital = get_object_or_404(CapitalInjection, pk=pk)
    amount = capital.amount
    source = capital.source_name
    
    if capital.receipt:
        capital.receipt.delete(save=False)
    
    capital.delete()
    
    log_activity(
        user=request.user,
        action='DELETE',
        model_type='Capital',
        object_repr=f"Capital UGX{amount}",
        details=f"Deleted capital injection of UGX{amount} from {source}",
        request=request
    )
    
    messages.success(request, f'Capital injection of UGX{amount} deleted successfully.')
    return redirect('capital_list')


@login_required
@permission_required('view_finance')
def capital_detail(request, pk):
    capital = get_object_or_404(CapitalInjection.objects.select_related('received_by'), pk=pk)
    
    context = {
        'capital': capital,
    }
    return render(request, 'finance/capital_detail.html', context)


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
    
    # Payment method filter
    payment_method = request.GET.get('payment_method')
    if payment_method:
        expenses = expenses.filter(payment_method=payment_method)
    
    # Calculate monthly total
    today = timezone.now().date()
    first_day_of_month = today.replace(day=1)
    month_total = expenses.filter(date__gte=first_day_of_month).aggregate(total=Sum('amount'))['total'] or 0
    
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
        'month_total': month_total,
        'categories': categories,
        'date_from': date_from,
        'date_to': date_to,
        'category_filter': category_filter,
        'payment_method': payment_method,
        'payment_methods': Expense.PAYMENT_METHODS,
    }
    return render(request, 'finance/expense_list.html', context)


@login_required
@permission_required('view_expenses')
def expense_detail(request, pk):
    """View expense details"""
    expense = get_object_or_404(Expense.objects.select_related('paid_by'), pk=pk)
    
    # Get related expenses from same category
    related_expenses = Expense.objects.filter(
        category=expense.category
    ).exclude(pk=expense.pk).order_by('-date')[:5]
    
    context = {
        'expense': expense,
        'related_expenses': related_expenses,
    }
    return render(request, 'finance/expense_detail.html', context)


@login_required
@permission_required('add_expense')
def expense_add(request):
    if request.method == 'POST':
        expense = Expense.objects.create(
            category=request.POST.get('category'),
            amount=request.POST.get('amount'),
            date=request.POST.get('date'),
            payment_method=request.POST.get('payment_method', 'cash'),
            reference=request.POST.get('reference', ''),
            description=request.POST.get('description', ''),
            paid_by=request.user
        )
        
        # Handle receipt upload if provided
        if 'receipt' in request.FILES:
            expense.receipt = request.FILES['receipt']
            expense.save()
        
        log_activity(
            user=request.user,
            action='CREATE',
            model_type='Expense',
            object_id=expense.id,
            object_repr=f"Expense UGX{expense.amount}",
            details=f"Added expense of UGX{expense.amount} for {expense.get_category_display()}",
            request=request
        )
        
        messages.success(request, 'Expense recorded successfully.')
        return redirect('expense_list')
    
    context = {
        'categories': Expense.EXPENSE_CATEGORIES,
        'payment_methods': Expense.PAYMENT_METHODS,
    }
    return render(request, 'finance/expense_form.html', context)


@login_required
@permission_required('change_expense')
def expense_edit(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    
    if request.method == 'POST':
        old_amount = expense.amount
        old_category = expense.get_category_display()
        
        expense.category = request.POST.get('category')
        expense.amount = request.POST.get('amount')
        expense.date = request.POST.get('date')
        expense.payment_method = request.POST.get('payment_method', 'cash')
        expense.reference = request.POST.get('reference', '')
        expense.description = request.POST.get('description', '')
        
        # Handle receipt upload if provided
        if 'receipt' in request.FILES:
            if expense.receipt:
                expense.receipt.delete(save=False)
            expense.receipt = request.FILES['receipt']
        
        expense.save()
        
        log_activity(
            user=request.user,
            action='UPDATE',
            model_type='Expense',
            object_id=expense.id,
            object_repr=f"Expense UGX{expense.amount}",
            details=f"Updated {old_category} from UGX{old_amount} to UGX{expense.amount}",
            request=request
        )
        
        messages.success(request, 'Expense updated successfully.')
        return redirect('expense_detail', pk=expense.id)
    
    context = {
        'expense': expense,
        'is_edit': True,
        'categories': Expense.EXPENSE_CATEGORIES,
        'payment_methods': Expense.PAYMENT_METHODS,
    }
    return render(request, 'finance/expense_form.html', context)


@login_required
@permission_required('delete_expense')
@require_POST
def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    amount = expense.amount
    category = expense.get_category_display()
    
    if expense.receipt:
        expense.receipt.delete(save=False)
    
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


# ============ CASH POSITION VIEWS ============

@login_required
@permission_required('view_finance')
def cash_position(request):
    """View cash position over time with detailed breakdown"""
    # Get date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if not date_from:
        date_from = (timezone.now().date() - timedelta(days=30)).isoformat()
    if not date_to:
        date_to = timezone.now().date().isoformat()
    
    # Convert to date objects
    start_date = datetime.strptime(date_from, '%Y-%m-%d').date()
    end_date = datetime.strptime(date_to, '%Y-%m-%d').date()
    
    # Initialize running balance
    running_balance = 0
    
    dates = []
    balances = []
    daily_data = []
    
    total_candidate_payments = 0
    total_client_income = 0
    total_other_income = 0
    total_loans = 0
    total_capital = 0
    total_expenses = 0
    
    current_date = start_date
    
    while current_date <= end_date:
        # Get all transactions for this date
        day_candidate_payments = CandidatePayment.objects.filter(date=current_date).aggregate(total=Sum('amount'))['total'] or 0
        
        # Split income by type
        day_client_income = Income.objects.filter(
            date=current_date, 
            income_type='client_payment'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        day_other_income = Income.objects.filter(
            date=current_date,
            income_type='other'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        day_loans = Income.objects.filter(
            date=current_date,
            income_type='loan'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        day_capital = CapitalInjection.objects.filter(date=current_date).aggregate(total=Sum('amount'))['total'] or 0
        day_expenses = Expense.objects.filter(date=current_date).aggregate(total=Sum('amount'))['total'] or 0
        
        day_total_in = day_candidate_payments + day_client_income + day_other_income + day_loans + day_capital
        day_net_change = day_total_in - day_expenses
        
        # Update running totals
        total_candidate_payments += day_candidate_payments
        total_client_income += day_client_income
        total_other_income += day_other_income
        total_loans += day_loans
        total_capital += day_capital
        total_expenses += day_expenses
        
        # Update running balance
        opening_balance = running_balance
        running_balance += day_net_change
        
        dates.append(current_date.strftime('%Y-%m-%d'))
        balances.append(float(running_balance))
        
        daily_data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'opening_balance': opening_balance,
            'candidate_payments': day_candidate_payments,
            'client_income': day_client_income,
            'other_income': day_other_income,
            'loans': day_loans,
            'capital': day_capital,
            'total_money_in': day_total_in,
            'expenses': day_expenses,
            'net_change': day_net_change,
            'closing_balance': running_balance,
        })
        
        current_date += timedelta(days=1)
    
    chart_data = {
        'dates': dates,
        'balances': balances,
        'opening_balance': balances[0] if balances else 0,
        'closing_balance': balances[-1] if balances else 0,
        'net_change': (balances[-1] - balances[0]) if len(balances) > 1 else 0,
        'total_money_in': total_candidate_payments + total_client_income + total_other_income + total_loans + total_capital,
        'total_candidate_payments': total_candidate_payments,
        'total_client_income': total_client_income,
        'total_other_income': total_other_income,
        'total_loans': total_loans,
        'total_capital': total_capital,
        'total_expenses': total_expenses,
        'daily_data': daily_data,
    }
    
    context = {
        'date_from': date_from,
        'date_to': date_to,
        'chart_data': chart_data,
    }
    
    return render(request, 'finance/cash_position.html', context)