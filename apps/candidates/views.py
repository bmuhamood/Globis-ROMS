from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.utils import timezone
from django.db import IntegrityError
from .models import Candidate
from apps.clients.models import Client
from apps.agents.models import Agent
from apps.documents.models import DocumentStatus
from apps.visa_process.models import VisaProcess
from apps.accounts.decorators import permission_required
from datetime import datetime, timedelta

@login_required
def candidate_list(request):
    candidates = Candidate.objects.select_related('agent', 'client').all()
    
    # Check if user is admin or staff
    is_admin = request.user.is_superuser or request.user.groups.filter(name='Administrator').exists()
    is_staff = request.user.groups.filter(name='Staff').exists()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        candidates = candidates.filter(
            Q(full_name__icontains=search_query) |
            Q(passport_no__icontains=search_query) |
            Q(position__icontains=search_query) |
            Q(contact_number__icontains=search_query)
        )
    
    # Filters - Only apply payment filters for admin
    if is_admin:
        payment_plan = request.GET.get('payment_plan', '')
        if payment_plan:
            candidates = candidates.filter(payment_plan=payment_plan)
        
        fully_paid = request.GET.get('fully_paid', '')
        if fully_paid:
            candidates = candidates.filter(fully_paid=(fully_paid == 'yes'))
    else:
        payment_plan = ''
        fully_paid = ''
    
    agent_id = request.GET.get('agent', '')
    if agent_id:
        candidates = candidates.filter(agent_id=agent_id)
    
    client_id = request.GET.get('client', '')
    if client_id:
        candidates = candidates.filter(client_id=client_id)
    
    # Calculate statistics
    total_count = candidates.count()
    
    # For admin, calculate payment stats
    if is_admin:
        paid_count = candidates.filter(fully_paid=True).count()
        loan_count = candidates.filter(payment_plan='loan').count()
        installment_count = candidates.filter(payment_plan='installment').count()
        
        # This month count for staff alternative view
        today = timezone.now().date()
        first_day = today.replace(day=1)
        month_count = candidates.filter(created_at__date__gte=first_day).count()
    else:
        paid_count = 0
        loan_count = 0
        installment_count = 0
        # For staff, calculate non-payment stats
        today = timezone.now().date()
        first_day = today.replace(day=1)
        month_count = candidates.filter(created_at__date__gte=first_day).count()
        active_count = candidates.filter(placements__isnull=True).count()
        placements_count = candidates.filter(placements__isnull=False).count()
    
    context = {
        'candidates': candidates,
        'search_query': search_query,
        'payment_plan': payment_plan if is_admin else '',
        'agent_id': agent_id,
        'client_id': client_id,
        'fully_paid': fully_paid if is_admin else '',
        'agents': Agent.objects.all(),
        'clients': Client.objects.all(),
        'total_count': total_count,
        'paid_count': paid_count,
        'loan_count': loan_count,
        'installment_count': installment_count,
        'month_count': month_count,
        'active_count': active_count if not is_admin else 0,
        'placements_count': placements_count if not is_admin else 0,
        'is_admin': is_admin,
        'is_staff': is_staff,
    }
    return render(request, 'candidates/list.html', context)

@login_required
def candidate_add(request):
    # Check if user has permission to add candidates
    if not (request.user.is_superuser or request.user.groups.filter(name='Administrator').exists() or request.user.has_perm('candidates.add_candidate')):
        messages.error(request, 'You do not have permission to add candidates.')
        return redirect('candidate_list')
    
    is_admin = request.user.is_superuser or request.user.groups.filter(name='Administrator').exists()
    
    if request.method == 'POST':
        try:
            from decimal import Decimal
            
            # For non-admin users, set default payment values
            if not is_admin:
                initial_amount = Decimal('0')
                payment_plan = 'cash'
                loan_provider = ''
                loan_reference = ''
            else:
                initial_amount = Decimal(request.POST.get('initial_amount', 0))
                payment_plan = request.POST.get('payment_plan', 'cash')
                loan_provider = request.POST.get('loan_provider', '')
                loan_reference = request.POST.get('loan_reference', '')
            
            # Check if passport number already exists
            passport_no = request.POST.get('passport_no')
            if Candidate.objects.filter(passport_no=passport_no).exists():
                messages.error(request, f'Candidate with passport number {passport_no} already exists.')
                return redirect('candidate_add')
            
            candidate = Candidate.objects.create(
                full_name=request.POST.get('full_name'),
                passport_no=passport_no,
                passport_expiry=request.POST.get('passport_expiry'),
                nationality=request.POST.get('nationality', 'UG'),
                position=request.POST.get('position'),
                contact_number=request.POST.get('contact_number'),
                mother_name=request.POST.get('mother_name', ''),
                father_name=request.POST.get('father_name', ''),
                blood_group=request.POST.get('blood_group', ''),
                salary=request.POST.get('salary'),
                agent_id=request.POST.get('agent') or None,
                client_id=request.POST.get('client') or None,
                initial_amount=initial_amount,
                remaining_balance=initial_amount,
                payment_plan=payment_plan,
                loan_provider=loan_provider,
                loan_reference=loan_reference,
                remarks=request.POST.get('remarks', '')
            )
            
            # Create related records
            DocumentStatus.objects.create(candidate=candidate)
            VisaProcess.objects.create(candidate=candidate)
            
            messages.success(request, f'Candidate {candidate.full_name} added successfully.')
            return redirect('candidate_list')
            
        except IntegrityError:
            messages.error(request, 'A candidate with this passport number already exists.')
        except Exception as e:
            messages.error(request, f'Error adding candidate: {str(e)}')
    
    clients = Client.objects.all()
    agents = Agent.objects.all()
    
    return render(request, 'candidates/form.html', {
        'clients': clients, 
        'agents': agents,
        'is_admin': is_admin,
    })

@login_required
def candidate_edit(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    
    # Check if user has edit permission
    is_admin = request.user.is_superuser or request.user.groups.filter(name='Administrator').exists()
    can_edit = is_admin or request.user.has_perm('candidates.change_candidate')
    
    if not can_edit:
        messages.error(request, 'You do not have permission to edit candidates.')
        return redirect('candidate_detail', pk=candidate.id)
    
    if request.method == 'POST':
        try:
            from decimal import Decimal
            
            # Check if passport number is being changed and if it's unique
            new_passport = request.POST.get('passport_no')
            if new_passport != candidate.passport_no:
                if Candidate.objects.filter(passport_no=new_passport).exclude(pk=pk).exists():
                    messages.error(request, f'Another candidate with passport number {new_passport} already exists.')
                    return redirect('candidate_edit', pk=pk)
            
            # Update candidate fields (all non-payment fields are editable by staff)
            candidate.full_name = request.POST.get('full_name')
            candidate.passport_no = new_passport
            candidate.passport_expiry = request.POST.get('passport_expiry')
            candidate.nationality = request.POST.get('nationality', 'UG')
            candidate.position = request.POST.get('position')
            candidate.contact_number = request.POST.get('contact_number')
            candidate.mother_name = request.POST.get('mother_name', '')
            candidate.father_name = request.POST.get('father_name', '')
            candidate.blood_group = request.POST.get('blood_group', '')
            candidate.salary = request.POST.get('salary')  # Salary is now editable for all
            candidate.agent_id = request.POST.get('agent') or None
            candidate.client_id = request.POST.get('client') or None
            
            # Payment info - ONLY ADMIN can edit payment information
            if is_admin:
                new_initial = Decimal(request.POST.get('initial_amount', str(candidate.initial_amount)))
                
                if new_initial != candidate.initial_amount:
                    # If initial amount changes, recalculate balance based on payments made
                    total_paid = candidate.initial_amount - candidate.remaining_balance
                    candidate.initial_amount = new_initial
                    candidate.remaining_balance = new_initial - total_paid
                
                candidate.payment_plan = request.POST.get('payment_plan', candidate.payment_plan)
                candidate.loan_provider = request.POST.get('loan_provider', '')
                candidate.loan_reference = request.POST.get('loan_reference', '')
            # For non-admins, DO NOT update payment fields - keep existing values
            
            candidate.remarks = request.POST.get('remarks', '')
            
            candidate.save()
            candidate.update_balance()  # Recalculate balance to ensure accuracy
            
            messages.success(request, f'Candidate {candidate.full_name} updated successfully.')
            return redirect('candidate_detail', pk=candidate.id)
            
        except IntegrityError:
            messages.error(request, 'A candidate with this passport number already exists.')
        except Exception as e:
            messages.error(request, f'Error updating candidate: {str(e)}')
    
    agents = Agent.objects.all()
    clients = Client.objects.all()
    
    # Check if user can edit and if they're admin
    can_edit = request.user.has_perm('candidates.change_candidate') or request.user.is_superuser
    is_admin = request.user.is_superuser or request.user.groups.filter(name='Administrator').exists()
    
    return render(request, 'candidates/form.html', {
        'candidate': candidate,
        'clients': clients,
        'agents': agents,
        'is_edit': True,
        'can_edit': can_edit,
        'is_admin': is_admin,
    })

@login_required
def candidate_delete(request, pk):
    # Only superusers (admins) can delete candidates
    if not request.user.is_superuser:
        messages.error(request, 'Permission denied. Only administrators can delete candidates.')
        return redirect('candidate_list')
    
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
    
    # Check if user is admin
    is_admin = request.user.is_superuser or request.user.groups.filter(name='Administrator').exists()
    
    # Get related records
    try:
        documents = DocumentStatus.objects.get(candidate=candidate)
    except DocumentStatus.DoesNotExist:
        documents = None
        
    try:
        visa = VisaProcess.objects.get(candidate=candidate)
    except VisaProcess.DoesNotExist:
        visa = None
    
    payments = candidate.payments.all().order_by('-date') if is_admin else []
    placements = candidate.placements.all()
    
    # Calculate payment statistics (only for admin)
    if is_admin:
        total_paid = candidate.initial_amount - candidate.remaining_balance
        payment_progress = candidate.get_payment_progress()
    else:
        total_paid = 0
        payment_progress = 0
    
    # Check if user can edit
    can_edit = request.user.has_perm('candidates.change_candidate') or request.user.is_superuser
    
    return render(request, 'candidates/detail.html', {
        'candidate': candidate,
        'documents': documents,
        'visa': visa,
        'payments': payments,
        'placements': placements,
        'total_paid': total_paid,
        'payment_progress': payment_progress,
        'can_edit': can_edit,
        'is_admin': is_admin,
    })