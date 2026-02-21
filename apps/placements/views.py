from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Placement
from apps.candidates.models import Candidate
from apps.clients.models import Client
from apps.finance.models import Income
from django.db.models import Sum
from django.db.models import Q, Sum, Avg
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta

@login_required
def placement_list(request):
    placements = Placement.objects.select_related('candidate', 'client').all()
    
    # Search filter
    search_query = request.GET.get('search', '')
    if search_query:
        placements = placements.filter(
            Q(candidate__full_name__icontains=search_query) |
            Q(client__company_name__icontains=search_query)
        )
    
    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        placements = placements.filter(payment_status=status_filter)
    
    # Client filter
    client_filter = request.GET.get('client', '')
    if client_filter:
        placements = placements.filter(client_id=client_filter)
    
    # Date range filters
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if date_from:
        placements = placements.filter(date_placed__gte=date_from)
    if date_to:
        placements = placements.filter(date_placed__lte=date_to)
    
    # Min fee filter
    min_fee = request.GET.get('min_fee', '')
    if min_fee:
        try:
            min_fee_val = float(min_fee)
            placements = placements.filter(placement_fee__gte=min_fee_val)
        except ValueError:
            pass
    
    # Calculate totals
    total_fees = placements.aggregate(total=Sum('placement_fee'))['total'] or 0
    avg_fee = placements.aggregate(avg=Avg('placement_fee'))['avg'] or 0
    
    # Count by status
    pending_count = placements.filter(payment_status='pending').count()
    partial_count = placements.filter(payment_status='partial').count()
    paid_count = placements.filter(payment_status='paid').count()
    
    # Get current month start and end for quick filter
    today = timezone.now().date()
    current_month_start = today.replace(day=1)
    if today.month == 12:
        current_month_end = today.replace(year=today.year+1, month=1, day=1) - timedelta(days=1)
    else:
        current_month_end = today.replace(month=today.month+1, day=1) - timedelta(days=1)
    
    # Get all clients for filter dropdown
    clients = Client.objects.all()
    
    # Pagination
    paginator = Paginator(placements, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'placements': page_obj,
        'total_fees': total_fees,
        'avg_fee': avg_fee,
        'pending_count': pending_count,
        'partial_count': partial_count,
        'paid_count': paid_count,
        'search_query': search_query,
        'status_filter': status_filter,
        'client_filter': client_filter,
        'date_from': date_from,
        'date_to': date_to,
        'min_fee': min_fee,
        'clients': clients,
        'current_month_start': current_month_start.strftime('%Y-%m-%d'),
        'current_month_end': current_month_end.strftime('%Y-%m-%d'),
        'date_filter': request.GET.get('date_filter', ''),
    }
    return render(request, 'placements/list.html', context)

@login_required
def placement_add(request):
    if request.method == 'POST':
        placement = Placement.objects.create(
            candidate_id=request.POST.get('candidate'),
            client_id=request.POST.get('client'),
            placement_fee=request.POST.get('placement_fee'),
            date_placed=request.POST.get('date_placed'),
            payment_status=request.POST.get('payment_status'),
            notes=request.POST.get('notes')
        )
        
        # If payment status is paid, create income record
        if request.POST.get('payment_status') == 'paid':
            Income.objects.create(
                client_id=request.POST.get('client'),
                placement=placement,
                amount=request.POST.get('placement_fee'),
                date=request.POST.get('date_placed'),
                received_by=request.user
            )
        
        messages.success(request, 'Placement created successfully.')
        return redirect('placement_list')
    
    candidates = Candidate.objects.filter(client__isnull=False)
    clients = Client.objects.all()
    return render(request, 'placements/form.html', {
        'candidates': candidates,
        'clients': clients
    })

@login_required
def placement_edit(request, pk):
    placement = get_object_or_404(Placement, pk=pk)
    
    if request.method == 'POST':
        placement.candidate_id = request.POST.get('candidate')
        placement.client_id = request.POST.get('client')
        placement.placement_fee = request.POST.get('placement_fee')
        placement.date_placed = request.POST.get('date_placed')
        placement.payment_status = request.POST.get('payment_status')
        placement.notes = request.POST.get('notes')
        placement.save()
        
        messages.success(request, 'Placement updated successfully.')
        return redirect('placement_list')
    
    candidates = Candidate.objects.all()
    clients = Client.objects.all()
    return render(request, 'placements/form.html', {
        'placement': placement,
        'candidates': candidates,
        'clients': clients
    })

@login_required
def placement_delete(request, pk):
    placement = get_object_or_404(Placement, pk=pk)
    placement.delete()
    messages.success(request, 'Placement deleted successfully.')
    return redirect('placement_list')