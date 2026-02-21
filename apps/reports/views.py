from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from datetime import timedelta, datetime
from apps.accounts.decorators import permission_required
from apps.accounts.models import log_activity
from apps.candidates.models import Candidate
from apps.clients.models import Client
from apps.agents.models import Agent
from apps.placements.models import Placement
from apps.finance.models import Income, Expense
from apps.documents.models import DocumentStatus
from apps.visa_process.models import VisaProcess
from apps.candidate_payments.models import CandidatePayment, PaymentHistory

@login_required
@permission_required('view_reports')
def report_list(request):
    """Main reports page - accessible to staff"""
    from apps.candidates.models import Candidate
    
    # Get summary counts for the dashboard
    total_candidates = Candidate.objects.count()
    loan_count = Candidate.objects.filter(payment_plan='loan').count()
    installment_count = Candidate.objects.filter(payment_plan='installment').count()
    paid_count = Candidate.objects.filter(fully_paid=True).count()
    
    log_activity(
        user=request.user,
        action='VIEW',
        model_type='Report',
        details="Viewed reports main page",
        request=request
    )
    
    context = {
        'total_candidates': total_candidates,
        'loan_count': loan_count,
        'installment_count': installment_count,
        'paid_count': paid_count,
    }
    return render(request, 'reports/list.html', context)


@login_required
@permission_required('view_candidate_reports')
def candidate_report(request):
    """Candidate report - accessible to staff"""
    candidates = Candidate.objects.select_related('agent', 'client').annotate(
        payment_total=Sum('payments__amount')
    ).all()
    
    # Filter by agent
    agent_filter = request.GET.get('agent')
    if agent_filter:
        candidates = candidates.filter(agent_id=agent_filter)
    
    # Filter by client
    client_filter = request.GET.get('client')
    if client_filter:
        candidates = candidates.filter(client_id=client_filter)
    
    # Filter by date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        candidates = candidates.filter(created_at__date__gte=date_from)
    if date_to:
        candidates = candidates.filter(created_at__date__lte=date_to)
    
    # Calculate totals for summary cards
    total_payments = candidates.aggregate(total=Sum('payments__amount'))['total'] or 0
    with_agents = candidates.filter(agent__isnull=False).count()
    with_clients = candidates.filter(client__isnull=False).count()
    
    # Get all agents and clients for filter dropdowns
    agents = Agent.objects.all()
    clients = Client.objects.all()
    
    log_activity(
        user=request.user,
        action='VIEW',
        model_type='Report',
        details="Viewed candidate report",
        request=request
    )
    
    context = {
        'candidates': candidates,
        'report_type': 'Candidate Report',
        'total_payments': total_payments,
        'with_agents': with_agents,
        'with_clients': with_clients,
        'agents': agents,
        'clients': clients,
        'agent_filter': agent_filter,
        'client_filter': client_filter,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'reports/candidate_report.html', context)


@login_required
@permission_required('view_client_reports')
def client_report(request):
    """Client report - accessible to staff"""
    clients = Client.objects.annotate(
        candidate_count=Count('candidates'),
        placement_count=Count('placements'),
        total_revenue=Sum('placements__placement_fee')
    ).all()
    
    # Filter by country
    country_filter = request.GET.get('country')
    if country_filter:
        clients = clients.filter(country=country_filter)
    
    # Filter by minimum candidates
    min_candidates = request.GET.get('min_candidates')
    if min_candidates:
        try:
            min_val = int(min_candidates)
            clients = clients.filter(candidate_count__gte=min_val)
        except ValueError:
            pass
    
    # Filter by minimum revenue
    min_revenue = request.GET.get('min_revenue')
    if min_revenue:
        try:
            min_val = float(min_revenue)
            clients = clients.filter(total_revenue__gte=min_val)
        except ValueError:
            pass
    
    # Filter by has placements
    has_placements = request.GET.get('has_placements')
    if has_placements == 'yes':
        clients = clients.filter(placement_count__gt=0)
    elif has_placements == 'no':
        clients = clients.filter(placement_count=0)
    
    # Get unique countries for filter dropdown
    countries = Client.objects.values_list('country', flat=True).distinct().order_by('country')
    
    # Calculate totals for summary cards
    total_revenue_all = clients.aggregate(total=Sum('total_revenue'))['total'] or 0
    total_candidates_all = clients.aggregate(total=Sum('candidate_count'))['total'] or 0
    total_placements_all = clients.aggregate(total=Sum('placement_count'))['total'] or 0
    
    log_activity(
        user=request.user,
        action='VIEW',
        model_type='Report',
        details="Viewed client report",
        request=request
    )
    
    context = {
        'clients': clients,
        'report_type': 'Client Report',
        'countries': countries,
        'country_filter': country_filter,
        'min_candidates': min_candidates,
        'min_revenue': min_revenue,
        'has_placements': has_placements,
        'total_revenue_all': total_revenue_all,
        'total_candidates_all': total_candidates_all,
        'total_placements_all': total_placements_all,
        'filter_type': request.GET.get('filter_type', ''),
    }
    return render(request, 'reports/client_report.html', context)


@login_required
@permission_required('view_agent_reports')
def agent_report(request):
    """Agent report - accessible to staff"""
    agents = Agent.objects.annotate(
        candidate_count=Count('candidates'),
        total_payments=Sum('candidates__payments__amount')
    ).all()
    
    # Search filter
    search_query = request.GET.get('search', '')
    if search_query:
        agents = agents.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    # Commission range filters
    min_commission = request.GET.get('min_commission')
    if min_commission:
        agents = agents.filter(commission_rate__gte=min_commission)
    
    max_commission = request.GET.get('max_commission')
    if max_commission:
        agents = agents.filter(commission_rate__lte=max_commission)
    
    # Min candidates filter
    min_candidates = request.GET.get('min_candidates')
    if min_candidates:
        try:
            min_val = int(min_candidates)
            agents = agents.filter(candidate_count__gte=min_val)
        except ValueError:
            pass
    
    # Has candidates filter
    has_candidates = request.GET.get('has_candidates')
    if has_candidates == 'yes':
        agents = agents.filter(candidate_count__gt=0)
    elif has_candidates == 'no':
        agents = agents.filter(candidate_count=0)
    
    # Calculate totals for summary cards
    total_payments_all = agents.aggregate(total=Sum('total_payments'))['total'] or 0
    total_candidates_all = agents.aggregate(total=Sum('candidate_count'))['total'] or 0
    avg_commission = agents.aggregate(avg=Avg('commission_rate'))['avg'] or 0
    
    log_activity(
        user=request.user,
        action='VIEW',
        model_type='Report',
        details="Viewed agent report",
        request=request
    )
    
    context = {
        'agents': agents,
        'report_type': 'Agent Report',
        'search_query': search_query,
        'min_commission': min_commission,
        'max_commission': max_commission,
        'min_candidates': min_candidates,
        'has_candidates': has_candidates,
        'total_payments_all': total_payments_all,
        'total_candidates_all': total_candidates_all,
        'avg_commission': round(avg_commission, 1),
        'filter_type': request.GET.get('filter_type', ''),
    }
    return render(request, 'reports/agent_report.html', context)


@login_required
@permission_required('view_finance_reports')
def finance_report(request):
    """Finance report - Only for admin, manager, finance"""
    # Date filtering
    date_from = request.GET.get('from', (timezone.now() - timedelta(days=30)).date())
    date_to = request.GET.get('to', timezone.now().date())
    
    incomes = Income.objects.filter(date__range=[date_from, date_to])
    expenses = Expense.objects.filter(date__range=[date_from, date_to])
    
    total_income = incomes.aggregate(total=Sum('amount'))['total'] or 0
    total_expense = expenses.aggregate(total=Sum('amount'))['total'] or 0
    profit_loss = total_income - total_expense
    
    # Group by category
    expenses_by_category = expenses.values('category').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    log_activity(
        user=request.user,
        action='VIEW',
        model_type='Report',
        details="Viewed finance report",
        request=request
    )
    
    context = {
        'date_from': date_from,
        'date_to': date_to,
        'incomes': incomes,
        'expenses': expenses,
        'total_income': total_income,
        'total_expense': total_expense,
        'profit_loss': profit_loss,
        'expenses_by_category': expenses_by_category,
        'report_type': 'Finance Report'
    }
    return render(request, 'reports/finance_report.html', context)


@login_required
@permission_required('view_document_reports')
def missing_documents_report(request):
    """Missing documents report - accessible to staff"""
    missing_docs = DocumentStatus.objects.filter(
        Q(medical_report=False) |
        Q(interpol=False) |
        Q(passport_copy=False) |
        Q(passport_photo=False) |
        Q(offer_letter=False) |
        Q(mol_approval=False)
    ).select_related('candidate')
    
    # Search filter
    search_query = request.GET.get('search', '')
    if search_query:
        missing_docs = missing_docs.filter(
            Q(candidate__full_name__icontains=search_query) |
            Q(candidate__passport_no__icontains=search_query)
        )
    
    # Filter by missing count
    missing_count = request.GET.get('missing_count')
    if missing_count:
        if missing_count == '4':
            missing_docs = [d for d in missing_docs if d.missing_documents_count() >= 4]
        else:
            try:
                count = int(missing_count)
                missing_docs = [d for d in missing_docs if d.missing_documents_count() == count]
            except ValueError:
                pass
    
    # Filter by specific missing documents
    missing_medical = request.GET.get('missing_medical')
    if missing_medical == 'yes':
        missing_docs = missing_docs.filter(medical_report=False)
    
    missing_interpol = request.GET.get('missing_interpol')
    if missing_interpol == 'yes':
        missing_docs = missing_docs.filter(interpol=False)
    
    missing_mol = request.GET.get('missing_mol')
    if missing_mol == 'yes':
        missing_docs = missing_docs.filter(mol_approval=False)
    
    # Calculate statistics
    total_candidates = Candidate.objects.count()
    total_missing = sum(d.missing_documents_count() for d in missing_docs)
    max_missing = max([d.missing_documents_count() for d in missing_docs], default=0)
    
    log_activity(
        user=request.user,
        action='VIEW',
        model_type='Report',
        details="Viewed missing documents report",
        request=request
    )
    
    context = {
        'documents': missing_docs,
        'report_type': 'Missing Documents Report',
        'search_query': search_query,
        'missing_count': missing_count,
        'missing_medical': missing_medical,
        'missing_interpol': missing_interpol,
        'missing_mol': missing_mol,
        'total_candidates': total_candidates,
        'total_missing': total_missing,
        'max_missing': max_missing,
        'filter_type': request.GET.get('filter_type', ''),
    }
    return render(request, 'reports/missing_documents.html', context)


@login_required
@permission_required('view_visa_reports')
def visa_status_report(request):
    """Visa status report - accessible to staff"""
    visas = VisaProcess.objects.select_related('candidate').all()
    
    # Search filter
    search_query = request.GET.get('search', '')
    if search_query:
        visas = visas.filter(
            Q(candidate__full_name__icontains=search_query) |
            Q(candidate__passport_no__icontains=search_query)
        )
    
    # Status filters
    interview_filter = request.GET.get('interview')
    if interview_filter:
        visas = visas.filter(interview_status=interview_filter)
    
    medical_filter = request.GET.get('medical')
    if medical_filter:
        visas = visas.filter(medical_status=medical_filter)
    
    interpol_filter = request.GET.get('interpol')
    if interpol_filter:
        visas = visas.filter(interpol_status=interpol_filter)
    
    # Status filter for overall progress
    status_filter = request.GET.get('status')
    if status_filter == 'ready':
        visas = visas.filter(visa_stamped=True, ticket_issued=True)
    elif status_filter == 'applied':
        visas = visas.filter(visa_applied=True, visa_stamped=False)
    elif status_filter == 'stamped':
        visas = visas.filter(visa_stamped=True)
    elif status_filter == 'pending':
        visas = visas.filter(visa_applied=False, visa_stamped=False)
    
    # Calculate statistics
    stats = {
        'total': visas.count(),
        'visa_applied': visas.filter(visa_applied=True).count(),
        'visa_stamped': visas.filter(visa_stamped=True).count(),
        'ticket_issued': visas.filter(ticket_issued=True).count(),
    }
    
    log_activity(
        user=request.user,
        action='VIEW',
        model_type='Report',
        details="Viewed visa status report",
        request=request
    )
    
    context = {
        'visas': visas,
        'stats': stats,
        'report_type': 'Visa Status Report',
        'search_query': search_query,
        'interview_filter': interview_filter,
        'medical_filter': medical_filter,
        'interpol_filter': interpol_filter,
        'status_filter': status_filter,
        'filter_type': request.GET.get('filter_type', ''),
    }
    return render(request, 'reports/visa_status.html', context)

@login_required
@permission_required('view_reports')
def payment_report(request):
    """Payment report - shows all candidate payments with filters"""
    from apps.candidate_payments.models import CandidatePayment
    
    # Get filter parameters with proper handling of empty values
    date_from = request.GET.get('from', '')
    date_to = request.GET.get('to', '')
    payment_type = request.GET.get('payment_type', '')
    payment_method = request.GET.get('payment_method', '')
    
    # Base queryset - start with all payments
    payments = CandidatePayment.objects.select_related('candidate', 'received_by').all()
    
    # Apply date filters only if values are provided
    if date_from:
        try:
            # Validate date format
            datetime.strptime(date_from, '%Y-%m-%d')
            payments = payments.filter(date__gte=date_from)
        except ValueError:
            # If invalid date, ignore filter
            pass
    
    if date_to:
        try:
            datetime.strptime(date_to, '%Y-%m-%d')
            payments = payments.filter(date__lte=date_to)
        except ValueError:
            # If invalid date, ignore filter
            pass
    
    # If no date filters provided, default to last 30 days
    if not date_from and not date_to:
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        payments = payments.filter(date__gte=thirty_days_ago)
        date_from = thirty_days_ago
        date_to = timezone.now().date()
    
    # Apply other filters
    if payment_type:
        payments = payments.filter(payment_type=payment_type)
    if payment_method:
        payments = payments.filter(payment_method=payment_method)
    
    # Calculate totals
    total_amount = payments.aggregate(total=Sum('amount'))['total'] or 0
    payment_count = payments.count()
    avg_payment = total_amount / payment_count if payment_count > 0 else 0
    
    # Group by payment type
    by_type = payments.values('payment_type').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    # Group by payment method
    by_method = payments.values('payment_method').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    log_activity(
        user=request.user,
        action='VIEW',
        model_type='Report',
        details="Viewed payment report",
        request=request
    )
    
    context = {
        'payments': payments,
        'total_amount': total_amount,
        'avg_payment': avg_payment,
        'by_type': by_type,
        'by_method': by_method,
        'date_from': date_from if date_from else '',
        'date_to': date_to if date_to else '',
        'payment_type': payment_type,
        'payment_method': payment_method,
        'payment_types': CandidatePayment.PAYMENT_TYPES,
        'payment_methods': CandidatePayment.PAYMENT_METHODS,
        'report_type': 'Payment Report'
    }
    return render(request, 'reports/payment_report.html', context)

@login_required
@permission_required('view_reports')
def loan_report(request):
    """Loan report - shows all candidates on loan/payment plans"""
    from apps.candidates.models import Candidate
    from apps.candidate_payments.models import PaymentHistory
    
    # Get filter parameters
    payment_plan = request.GET.get('payment_plan', '')
    status = request.GET.get('status', '')
    
    # Candidates on non-cash payment plans
    candidates = Candidate.objects.filter(
        payment_plan__in=['loan', 'installment']
    ).select_related('agent', 'client')
    
    if payment_plan:
        candidates = candidates.filter(payment_plan=payment_plan)
    
    # Get payment histories
    payment_histories = PaymentHistory.objects.filter(
        candidate__in=candidates
    ).select_related('candidate', 'payment')
    
    if status:
        payment_histories = payment_histories.filter(status=status)
    
    # Calculate totals
    total_loan_amount = candidates.aggregate(total=Sum('initial_amount'))['total'] or 0
    total_paid = PaymentHistory.objects.filter(
        candidate__in=candidates,
        status='paid'
    ).aggregate(total=Sum('amount_paid'))['total'] or 0
    total_outstanding = total_loan_amount - total_paid
    
    log_activity(
        user=request.user,
        action='VIEW',
        model_type='Report',
        details="Viewed loan report",
        request=request
    )
    
    context = {
        'candidates': candidates,
        'payment_histories': payment_histories,
        'total_loan_amount': total_loan_amount,
        'total_paid': total_paid,
        'total_outstanding': total_outstanding,
        'payment_plan': payment_plan,
        'status': status,
        'report_type': 'Loan & Payment Plan Report'
    }
    return render(request, 'reports/loan_report.html', context)