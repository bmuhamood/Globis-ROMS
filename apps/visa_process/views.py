from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import VisaProcess
from apps.candidates.models import Candidate
from django.db.models import Q
from django.core.paginator import Paginator

@login_required
def visa_list(request):
    visas = VisaProcess.objects.select_related('candidate').all()
    
    # Search filter
    search_query = request.GET.get('search', '')
    if search_query:
        visas = visas.filter(
            Q(candidate__full_name__icontains=search_query) |
            Q(candidate__passport_no__icontains=search_query)
        )
    
    # Status filters
    interview_filter = request.GET.get('interview', '')
    if interview_filter:
        visas = visas.filter(interview_status=interview_filter)
    
    medical_filter = request.GET.get('medical', '')
    if medical_filter:
        visas = visas.filter(medical_status=medical_filter)
    
    interpol_filter = request.GET.get('interpol', '')
    if interpol_filter:
        visas = visas.filter(interpol_status=interpol_filter)
    
    # Boolean filters
    visa_applied_filter = request.GET.get('visa_applied', '')
    if visa_applied_filter == 'yes':
        visas = visas.filter(visa_applied=True)
    elif visa_applied_filter == 'no':
        visas = visas.filter(visa_applied=False)
    
    visa_stamped_filter = request.GET.get('visa_stamped', '')
    if visa_stamped_filter == 'yes':
        visas = visas.filter(visa_stamped=True)
    elif visa_stamped_filter == 'no':
        visas = visas.filter(visa_stamped=False)
    
    ticket_filter = request.GET.get('ticket_issued', '')
    if ticket_filter == 'yes':
        visas = visas.filter(ticket_issued=True)
    elif ticket_filter == 'no':
        visas = visas.filter(ticket_issued=False)
    
    # Calculate counts for summary cards
    total_count = visas.count()
    ready_count = visas.filter(visa_stamped=True, ticket_issued=True).count()
    progress_count = visas.filter(visa_applied=True, visa_stamped=False).count()
    stamped_count = visas.filter(visa_stamped=True).count()
    
    # Pagination
    paginator = Paginator(visas, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'visas': page_obj,
        'search_query': search_query,
        'interview_filter': interview_filter,
        'medical_filter': medical_filter,
        'interpol_filter': interpol_filter,
        'visa_applied_filter': visa_applied_filter,
        'visa_stamped_filter': visa_stamped_filter,
        'ticket_filter': ticket_filter,
        'total_count': total_count,
        'ready_count': ready_count,
        'progress_count': progress_count,
        'stamped_count': stamped_count,
        'filter_type': request.GET.get('filter_type', ''),
    }
    return render(request, 'visa/list.html', context)
@login_required
def visa_update(request, pk):
    visa = get_object_or_404(VisaProcess, pk=pk)
    
    if request.method == 'POST':
        visa.interview_status = request.POST.get('interview_status')
        visa.medical_status = request.POST.get('medical_status')
        visa.interpol_status = request.POST.get('interpol_status')
        visa.visa_applied = request.POST.get('visa_applied') == 'on'
        visa.visa_stamped = request.POST.get('visa_stamped') == 'on'
        visa.ticket_issued = request.POST.get('ticket_issued') == 'on'
        visa.save()
        
        messages.success(request, 'Visa process updated successfully.')
        return redirect('visa_list')
    
    return render(request, 'visa/form.html', {'visa': visa})

@login_required
def visa_progress(request):
    in_progress = VisaProcess.objects.filter(visa_applied=True, visa_stamped=False).count()
    ready = VisaProcess.objects.filter(visa_stamped=True, ticket_issued=True).count()
    pending = VisaProcess.objects.filter(visa_applied=False).count()
    
    context = {
        'in_progress': in_progress,
        'ready': ready,
        'pending': pending
    }
    return render(request, 'visa/progress.html', context)