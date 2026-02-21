from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.utils import timezone
from .models import Candidate
from apps.clients.models import Client
from apps.agents.models import Agent
from apps.documents.models import DocumentStatus
from apps.visa_process.models import VisaProcess
from apps.accounts.decorators import permission_required

@login_required
def candidate_list(request):
    candidates = Candidate.objects.select_related('agent', 'client').all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        candidates = candidates.filter(
            Q(full_name__icontains=search_query) |
            Q(passport_no__icontains=search_query) |
            Q(position__icontains=search_query) |
            Q(contact_number__icontains=search_query)
        )
    
    # Filters
    payment_plan = request.GET.get('payment_plan', '')
    if payment_plan:
        candidates = candidates.filter(payment_plan=payment_plan)
    
    agent_id = request.GET.get('agent', '')
    if agent_id:
        candidates = candidates.filter(agent_id=agent_id)
    
    client_id = request.GET.get('client', '')
    if client_id:
        candidates = candidates.filter(client_id=client_id)
    
    fully_paid = request.GET.get('fully_paid', '')
    if fully_paid:
        candidates = candidates.filter(fully_paid=(fully_paid == 'yes'))
    
    context = {
        'candidates': candidates,
        'search_query': search_query,
        'payment_plan': payment_plan,
        'agent_id': agent_id,
        'client_id': client_id,
        'fully_paid': fully_paid,
        'agents': Agent.objects.all(),
        'clients': Client.objects.all(),
    }
    return render(request, 'candidates/list.html', context)

@login_required
def candidate_add(request):
    if request.method == 'POST':
        try:
            from decimal import Decimal
            initial_amount = Decimal(request.POST.get('initial_amount', 0))
            
            candidate = Candidate.objects.create(
                full_name=request.POST.get('full_name'),
                passport_no=request.POST.get('passport_no'),
                passport_expiry=request.POST.get('passport_expiry'),
                position=request.POST.get('position'),
                contact_number=request.POST.get('contact_number'),
                mother_name=request.POST.get('mother_name', ''),
                father_name=request.POST.get('father_name', ''),
                blood_group=request.POST.get('blood_group', ''),
                salary=request.POST.get('salary'),
                agent_id=request.POST.get('agent') or None,
                client_id=request.POST.get('client') or None,
                initial_amount=initial_amount,
                remaining_balance=initial_amount,  # Set remaining balance equal to initial amount
                payment_plan=request.POST.get('payment_plan', 'cash'),
                loan_provider=request.POST.get('loan_provider', ''),
                loan_reference=request.POST.get('loan_reference', ''),
                remarks=request.POST.get('remarks', '')
            )
            
            # Create related records
            DocumentStatus.objects.create(candidate=candidate)
            VisaProcess.objects.create(candidate=candidate)
            
            messages.success(request, f'Candidate {candidate.full_name} added successfully.')
            return redirect('candidate_list')
            
        except Exception as e:
            messages.error(request, f'Error adding candidate: {str(e)}')
    
    clients = Client.objects.all()
    agents = Agent.objects.all()
    return render(request, 'candidates/form.html', {
        'clients': clients, 
        'agents': agents
    })

@login_required
@permission_required('edit_candidate')
def candidate_edit(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    
    if request.method == 'POST':
        try:
            # Store old values for logging
            old_values = {
                'full_name': candidate.full_name,
                'position': candidate.position,
                'initial_amount': candidate.initial_amount,
            }
            
            # Update candidate fields (passport_no is NOT updated - it's read-only)
            candidate.full_name = request.POST.get('full_name')
            # passport_no is NOT updated in edit mode
            candidate.passport_expiry = request.POST.get('passport_expiry')
            candidate.position = request.POST.get('position')
            candidate.contact_number = request.POST.get('contact_number')
            candidate.mother_name = request.POST.get('mother_name', '')
            candidate.father_name = request.POST.get('father_name', '')
            candidate.blood_group = request.POST.get('blood_group', '')
            candidate.salary = request.POST.get('salary')
            candidate.agent_id = request.POST.get('agent') or None
            candidate.client_id = request.POST.get('client') or None
            
            # Payment info - handle initial amount changes (keep as Decimal)
            from decimal import Decimal
            new_initial = Decimal(request.POST.get('initial_amount', str(candidate.initial_amount)))
            
            if new_initial != candidate.initial_amount:
                # If initial amount changes, recalculate balance based on payments made
                total_paid = candidate.initial_amount - candidate.remaining_balance
                candidate.initial_amount = new_initial
                candidate.remaining_balance = new_initial - total_paid
            
            candidate.payment_plan = request.POST.get('payment_plan', candidate.payment_plan)
            candidate.loan_provider = request.POST.get('loan_provider', '')
            candidate.loan_reference = request.POST.get('loan_reference', '')
            candidate.remarks = request.POST.get('remarks', '')
            
            candidate.save()
            candidate.update_balance()  # Recalculate balance to ensure accuracy
            
            messages.success(request, f'Candidate {candidate.full_name} updated successfully.')
            return redirect('candidate_detail', pk=candidate.id)
            
        except Exception as e:
            messages.error(request, f'Error updating candidate: {str(e)}')
    
    agents = Agent.objects.all()
    clients = Client.objects.all()
    return render(request, 'candidates/form.html', {
        'candidate': candidate,
        'clients': clients,
        'agents': agents,
    })

@login_required
def candidate_delete(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    candidate_name = candidate.full_name
    candidate.delete()
    messages.success(request, f'Candidate {candidate_name} deleted successfully.')
    return redirect('candidate_list')

@login_required
def candidate_detail(request, pk):
    candidate = get_object_or_404(
        Candidate.objects.select_related('agent', 'client'),
        pk=pk
    )
    documents = DocumentStatus.objects.get(candidate=candidate)
    visa = VisaProcess.objects.get(candidate=candidate)
    payments = candidate.payments.all().order_by('-date')
    placements = candidate.placements.all()
    
    # Calculate payment statistics
    total_paid = candidate.initial_amount - candidate.remaining_balance
    payment_progress = candidate.get_payment_progress()
    
    return render(request, 'candidates/detail.html', {
        'candidate': candidate,
        'documents': documents,
        'visa': visa,
        'payments': payments,
        'placements': placements,
        'total_paid': total_paid,
        'payment_progress': payment_progress,
    })