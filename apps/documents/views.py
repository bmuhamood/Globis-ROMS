from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from .models import DocumentStatus
from apps.candidates.models import Candidate
from apps.agents.models import Agent
from apps.clients.models import Client

@login_required
def document_list(request):
    documents = DocumentStatus.objects.select_related('candidate__agent', 'candidate__client').all()
    
    # Search filter
    search_query = request.GET.get('search', '')
    if search_query:
        documents = documents.filter(
            Q(candidate__full_name__icontains=search_query) |
            Q(candidate__passport_no__icontains=search_query)
        )
    
    # Document status filters
    if request.GET.get('medical') == 'yes':
        documents = documents.filter(medical_report=True)
    elif request.GET.get('medical') == 'no':
        documents = documents.filter(medical_report=False)
    
    if request.GET.get('interpol') == 'yes':
        documents = documents.filter(interpol=True)
    elif request.GET.get('interpol') == 'no':
        documents = documents.filter(interpol=False)
    
    if request.GET.get('passport_copy') == 'yes':
        documents = documents.filter(passport_copy=True)
    elif request.GET.get('passport_copy') == 'no':
        documents = documents.filter(passport_copy=False)
    
    if request.GET.get('passport_photo') == 'yes':
        documents = documents.filter(passport_photo=True)
    elif request.GET.get('passport_photo') == 'no':
        documents = documents.filter(passport_photo=False)
    
    if request.GET.get('offer_letter') == 'yes':
        documents = documents.filter(offer_letter=True)
    elif request.GET.get('offer_letter') == 'no':
        documents = documents.filter(offer_letter=False)
    
    if request.GET.get('mol_approval') == 'yes':
        documents = documents.filter(mol_approval=True)
    elif request.GET.get('mol_approval') == 'no':
        documents = documents.filter(mol_approval=False)
    
    # Agent filter
    agent_filter = request.GET.get('agent')
    if agent_filter:
        documents = documents.filter(candidate__agent_id=agent_filter)
    
    # Client filter
    client_filter = request.GET.get('client')
    if client_filter:
        documents = documents.filter(candidate__client_id=client_filter)
    
    # Date range filter
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        documents = documents.filter(updated_at__date__gte=date_from)
    if date_to:
        documents = documents.filter(updated_at__date__lte=date_to)
    
    # Calculate missing documents count for each record
    documents_list = list(documents)
    for doc in documents_list:
        doc.missing_count = doc.missing_documents_count()
    
    # Missing documents filter
    missing_filter = request.GET.get('missing', '')
    if missing_filter:
        if missing_filter == '0':
            documents_list = [d for d in documents_list if d.missing_count == 0]
        elif missing_filter == '1':
            documents_list = [d for d in documents_list if d.missing_count == 1]
        elif missing_filter == '2':
            documents_list = [d for d in documents_list if d.missing_count == 2]
        elif missing_filter == '3+':
            documents_list = [d for d in documents_list if d.missing_count >= 3]
    
    # Calculate statistics
    total_docs = len(documents_list)
    complete_count = sum(1 for d in documents_list if d.missing_count == 0)
    partial_count = sum(1 for d in documents_list if 1 <= d.missing_count <= 2)
    critical_count = sum(1 for d in documents_list if d.missing_count >= 3)
    
    # Pagination
    paginator = Paginator(documents_list, 20)  # Show 20 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter values for template
    context = {
        'documents': page_obj,
        'search_query': search_query,
        'medical_filter': request.GET.get('medical', ''),
        'interpol_filter': request.GET.get('interpol', ''),
        'passport_copy_filter': request.GET.get('passport_copy', ''),
        'passport_photo_filter': request.GET.get('passport_photo', ''),
        'offer_letter_filter': request.GET.get('offer_letter', ''),
        'mol_approval_filter': request.GET.get('mol_approval', ''),
        'missing_filter': request.GET.get('missing', ''),
        'agent_filter': request.GET.get('agent', ''),
        'client_filter': request.GET.get('client', ''),
        'date_from': date_from,
        'date_to': date_to,
        'total_docs': total_docs,
        'complete_count': complete_count,
        'partial_count': partial_count,
        'critical_count': critical_count,
        'agents': Agent.objects.all(),
        'clients': Client.objects.all(),
    }
    return render(request, 'documents/list.html', context)


@login_required
def document_update(request, pk):
    document = get_object_or_404(DocumentStatus, pk=pk)
    
    if request.method == 'POST':
        document.medical_report = request.POST.get('medical_report') == 'on'
        document.interpol = request.POST.get('interpol') == 'on'
        document.passport_copy = request.POST.get('passport_copy') == 'on'
        document.passport_photo = request.POST.get('passport_photo') == 'on'
        document.offer_letter = request.POST.get('offer_letter') == 'on'
        document.mol_approval = request.POST.get('mol_approval') == 'on'  # Changed from signed_offer_letter
        document.save()
        
        messages.success(request, 'Documents updated successfully.')
        return redirect('document_list')
    
    return render(request, 'documents/form.html', {'document': document})


@login_required
def missing_documents(request):
    missing_docs = DocumentStatus.objects.filter(
        Q(medical_report=False) |
        Q(interpol=False) |
        Q(passport_copy=False) |
        Q(passport_photo=False) |
        Q(offer_letter=False) |
        Q(mol_approval=False)  # Changed from signed_offer_letter
    ).select_related('candidate').distinct()
    
    # Calculate missing count for each
    for doc in missing_docs:
        doc.missing_count = doc.missing_documents_count()
    
    return render(request, 'documents/missing.html', {'documents': missing_docs})