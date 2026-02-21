from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.core.paginator import Paginator
from .models import Client
from apps.candidates.models import Candidate
from apps.placements.models import Placement

@login_required
def client_list(request):
    clients = Client.objects.annotate(
        candidate_count=Count('candidates'),
        placement_count=Count('placements'),
        total_revenue=Sum('placements__placement_fee')
    ).all()
    
    # Search filter
    search_query = request.GET.get('search', '')
    if search_query:
        clients = clients.filter(
            Q(company_name__icontains=search_query) |
            Q(contact_person__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    # Country filter
    country_filter = request.GET.get('country', '')
    if country_filter:
        clients = clients.filter(country=country_filter)
    
    # Has placements filter
    has_placements = request.GET.get('has_placements', '')
    if has_placements == 'yes':
        clients = clients.filter(placement_count__gt=0)
    elif has_placements == 'no':
        clients = clients.filter(placement_count=0)
    
    # Min candidates filter
    min_candidates = request.GET.get('min_candidates', '')
    if min_candidates:
        try:
            min_val = int(min_candidates)
            clients = clients.filter(candidate_count__gte=min_val)
        except ValueError:
            pass
    
    # Get unique countries for filter dropdown
    countries = Client.objects.values_list('country', flat=True).distinct().order_by('country')
    
    # Calculate totals
    total_placements = clients.aggregate(total=Sum('placement_count'))['total'] or 0
    active_clients = clients.filter(placement_count__gt=0).count()
    
    # Pagination
    paginator = Paginator(clients, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'clients': page_obj,
        'search_query': search_query,
        'country_filter': country_filter,
        'has_placements': has_placements,
        'min_candidates': min_candidates,
        'countries': countries,
        'total_placements': total_placements,
        'active_clients': active_clients,
        'filter_type': request.GET.get('filter_type', ''),
    }
    return render(request, 'clients/list.html', context)


@login_required
def client_add(request):
    if request.method == 'POST':
        client = Client.objects.create(
            company_name=request.POST.get('company_name'),
            contact_person=request.POST.get('contact_person'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            address=request.POST.get('address'),
            country=request.POST.get('country')
        )
        messages.success(request, 'Client added successfully.')
        return redirect('client_list')
    
    return render(request, 'clients/form.html')


@login_required
def client_edit(request, pk):
    client = get_object_or_404(Client, pk=pk)
    
    if request.method == 'POST':
        client.company_name = request.POST.get('company_name')
        client.contact_person = request.POST.get('contact_person')
        client.email = request.POST.get('email')
        client.phone = request.POST.get('phone')
        client.address = request.POST.get('address')
        client.country = request.POST.get('country')
        client.save()
        
        messages.success(request, 'Client updated successfully.')
        return redirect('client_list')
    
    return render(request, 'clients/form.html', {'client': client})


@login_required
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)
    client_name = client.company_name
    client.delete()
    messages.success(request, f'Client {client_name} deleted successfully.')
    return redirect('client_list')


@login_required
def client_detail(request, pk):
    client = get_object_or_404(Client, pk=pk)
    candidates = Candidate.objects.filter(client=client).select_related('visa_process')
    placements = Placement.objects.filter(client=client).select_related('candidate')
    
    total_revenue = placements.aggregate(total=Sum('placement_fee'))['total'] or 0
    
    context = {
        'client': client,
        'candidates': candidates,
        'placements': placements,
        'total_revenue': total_revenue,
    }
    return render(request, 'clients/detail.html', context)