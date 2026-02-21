from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Agent
from apps.candidates.models import Candidate
from apps.candidate_payments.models import CandidatePayment
from django.db.models import Count, Sum
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count

@login_required
def agent_list(request):
    agents = Agent.objects.annotate(
        candidate_count=Count('candidates')
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
    
    # Has candidates filter
    has_candidates = request.GET.get('has_candidates')
    if has_candidates == 'yes':
        agents = agents.filter(candidate_count__gt=0)
    elif has_candidates == 'no':
        agents = agents.filter(candidate_count=0)
    
    # Calculate averages
    avg_commission = agents.aggregate(avg=Avg('commission_rate'))['avg'] or 0
    total_candidates = Candidate.objects.count()
    
    # Pagination
    paginator = Paginator(agents, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'agents': page_obj,
        'search_query': search_query,
        'min_commission': min_commission,
        'max_commission': max_commission,
        'has_candidates': has_candidates,
        'avg_commission': round(avg_commission, 1),
        'total_candidates': total_candidates,
        'filter_type': request.GET.get('filter_type', ''),
    }
    return render(request, 'agents/list.html', context)

@login_required
def agent_add(request):
    if request.method == 'POST':
        agent = Agent.objects.create(
            name=request.POST.get('name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            address=request.POST.get('address'),
            commission_rate=request.POST.get('commission_rate', 0)
        )
        messages.success(request, 'Agent added successfully.')
        return redirect('agent_list')
    
    return render(request, 'agents/form.html')

@login_required
def agent_edit(request, pk):
    agent = get_object_or_404(Agent, pk=pk)
    
    if request.method == 'POST':
        agent.name = request.POST.get('name')
        agent.email = request.POST.get('email')
        agent.phone = request.POST.get('phone')
        agent.address = request.POST.get('address')
        agent.commission_rate = request.POST.get('commission_rate', 0)
        agent.save()
        
        messages.success(request, 'Agent updated successfully.')
        return redirect('agent_list')
    
    return render(request, 'agents/form.html', {'agent': agent})

@login_required
def agent_delete(request, pk):
    agent = get_object_or_404(Agent, pk=pk)
    agent.delete()
    messages.success(request, 'Agent deleted successfully.')
    return redirect('agent_list')

@login_required
def agent_detail(request, pk):
    agent = get_object_or_404(Agent, pk=pk)
    candidates = Candidate.objects.filter(agent=agent)
    
    # Calculate total payments collected by this agent's candidates
    total_payments = CandidatePayment.objects.filter(
        candidate__agent=agent
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'agent': agent,
        'candidates': candidates,
        'total_payments': total_payments
    }
    return render(request, 'agents/detail.html', context)