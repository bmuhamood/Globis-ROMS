from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.http import require_POST
from django.conf import settings
from django.core.files.base import ContentFile
from .models import DocumentStatus, DocumentType, CandidateDocument, MergedDocument
from apps.candidates.models import Candidate
from apps.agents.models import Agent
from apps.clients.models import Client
import os
import PyPDF2
from io import BytesIO
from PIL import Image
import img2pdf
import mimetypes

# ============ EXISTING DOCUMENT STATUS VIEWS ============

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
    paginator = Paginator(documents_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
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
        document.mol_approval = request.POST.get('mol_approval') == 'on'
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
        Q(mol_approval=False)
    ).select_related('candidate').distinct()
    
    for doc in missing_docs:
        doc.missing_count = doc.missing_documents_count()
    
    return render(request, 'documents/missing.html', {'documents': missing_docs})


# ============ UPDATED DOCUMENT UPLOAD VIEWS ============

@login_required
def candidate_documents(request, candidate_id):
    """View all documents for a specific candidate with upload interface"""
    candidate = get_object_or_404(Candidate, pk=candidate_id)
    
    # Get ALL documents - removed is_latest filter to show all uploaded files
    documents = candidate.uploaded_documents.all().select_related(
        'document_type', 'uploaded_by'
    ).order_by('document_type__order', '-uploaded_at')
    
    # Get or create document types
    document_types = DocumentType.objects.all().order_by('order')
    
    # If no document types exist, create default ones
    if not document_types.exists():
        default_types = [
            {'code': 'medical', 'name': 'Medical Report', 'order': 1, 'required': True},
            {'code': 'passport', 'name': 'Passport Copy', 'order': 2, 'required': True},
            {'code': 'interpol', 'name': 'Interpol Clearance', 'order': 3, 'required': True},
            {'code': 'offer', 'name': 'Offer Letter', 'order': 4, 'required': True},
            {'code': 'mol', 'name': 'MOL Approval', 'order': 5, 'required': True},
            {'code': 'photo', 'name': 'Passport Photo', 'order': 6, 'required': True},
            {'code': 'contract', 'name': 'Employment Contract', 'order': 7, 'required': False},
            {'code': 'visa', 'name': 'Visa Document', 'order': 8, 'required': False},
            {'code': 'ticket', 'name': 'Flight Ticket', 'order': 9, 'required': False},
            {'code': 'other', 'name': 'Other Document', 'order': 99, 'required': False},
        ]
        for type_data in default_types:
            DocumentType.objects.get_or_create(
                code=type_data['code'],
                defaults={
                    'name': type_data['name'],
                    'order': type_data['order'],
                    'required': type_data['required']
                }
            )
        document_types = DocumentType.objects.all().order_by('order')
    
    # Get merged document if exists
    merged_doc = MergedDocument.objects.filter(candidate=candidate).first()
    
    # Calculate missing documents - check if at least ONE document exists for each required type
    uploaded_types = documents.values_list('document_type_id', flat=True).distinct()
    missing_types = document_types.exclude(id__in=uploaded_types).filter(required=True)
    
    context = {
        'candidate': candidate,
        'documents': documents,
        'document_types': document_types,
        'merged_doc': merged_doc,
        'missing_types': missing_types,
        'uploaded_count': documents.count(),
        'total_required': document_types.filter(required=True).count(),
    }
    return render(request, 'documents/candidate_documents.html', context)


@login_required
@require_POST
def upload_document(request, candidate_id):
    """Handle single document upload via AJAX - Updated to allow multiple files of same type"""
    candidate = get_object_or_404(Candidate, pk=candidate_id)
    
    try:
        file = request.FILES['file']
        document_type_id = request.POST.get('document_type')
        
        # Validate file size (10MB max)
        if file.size > 10 * 1024 * 1024:
            return JsonResponse({'success': False, 'error': 'File size exceeds 10MB'}, status=400)
        
        # Validate file type
        allowed_types = ['pdf', 'jpg', 'jpeg', 'png', 'gif', 'bmp', 'doc', 'docx', 'xls', 'xlsx']
        file_ext = file.name.split('.')[-1].lower()
        if file_ext not in allowed_types:
            return JsonResponse({'success': False, 'error': f'File type .{file_ext} not allowed'}, status=400)
        
        # Require document type selection (no auto-detect)
        if not document_type_id or not document_type_id.isdigit():
            return JsonResponse({'success': False, 'error': 'Please select a document type'}, status=400)
        
        document_type = get_object_or_404(DocumentType, pk=document_type_id)
        
        # Get the next version number for this document type
        existing_docs = candidate.uploaded_documents.filter(
            document_type=document_type
        ).count()
        
        next_version = existing_docs + 1
        
        # Save new document - DON'T mark previous ones as not latest
        # This allows multiple documents of the same type to be visible
        doc = CandidateDocument.objects.create(
            candidate=candidate,
            document_type=document_type,
            file=file,
            original_filename=file.name,
            file_size=file.size,
            file_type=file_ext,
            uploaded_by=request.user,
            version=next_version,
            is_latest=True  # All documents are considered "latest" for display
        )
        
        # Update DocumentStatus (mark as true if at least one exists)
        doc_status, created = DocumentStatus.objects.get_or_create(candidate=candidate)
        
        if document_type.code == 'medical':
            doc_status.medical_report = True
        elif document_type.code == 'interpol':
            doc_status.interpol = True
        elif document_type.code == 'passport':
            doc_status.passport_copy = True
        elif document_type.code == 'photo':
            doc_status.passport_photo = True
        elif document_type.code == 'offer':
            doc_status.offer_letter = True
        elif document_type.code == 'mol':
            doc_status.mol_approval = True
        
        doc_status.save()
        
        return JsonResponse({
            'success': True,
            'document_id': doc.id,
            'filename': doc.original_filename,
            'size': doc.get_file_size_display(),
            'type': doc.document_type.name,
            'type_code': doc.document_type.code,
            'version': next_version,
            'uploaded_at': doc.uploaded_at.strftime('%Y-%m-%d %H:%M'),
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
def download_document(request, document_id):
    """Download a single document - Updated to work with any document"""
    doc = get_object_or_404(CandidateDocument, pk=document_id)
    file_path = doc.file.path
    
    if os.path.exists(file_path):
        response = FileResponse(open(file_path, 'rb'))
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Disposition'] = f'attachment; filename="{doc.original_filename}"'
        return response
    else:
        messages.error(request, 'File not found.')
        return redirect('candidate_documents', candidate_id=doc.candidate.id)


@login_required
def view_document(request, document_id):
    """View a document in browser - Updated to work with any document"""
    doc = get_object_or_404(CandidateDocument, pk=document_id)
    file_path = doc.file.path
    
    if os.path.exists(file_path):
        content_type, encoding = mimetypes.guess_type(file_path)
        response = FileResponse(open(file_path, 'rb'))
        response['Content-Type'] = content_type or 'application/octet-stream'
        response['Content-Disposition'] = f'inline; filename="{doc.original_filename}"'
        return response
    else:
        messages.error(request, 'File not found.')
        return redirect('candidate_documents', candidate_id=doc.candidate.id)


@login_required
@require_POST
def delete_document(request, document_id):
    """Delete a document - Updated to properly update status"""
    doc = get_object_or_404(CandidateDocument, pk=document_id)
    candidate = doc.candidate
    document_type = doc.document_type
    
    # Delete file
    if os.path.exists(doc.file.path):
        os.remove(doc.file.path)
    
    doc.delete()
    
    # Update DocumentStatus - check if ANY documents of each type exist
    doc_status = DocumentStatus.objects.get(candidate=candidate)
    
    # Check if at least one document exists for each type
    has_medical = candidate.uploaded_documents.filter(
        document_type__code='medical'
    ).exists()
    has_interpol = candidate.uploaded_documents.filter(
        document_type__code='interpol'
    ).exists()
    has_passport = candidate.uploaded_documents.filter(
        document_type__code='passport'
    ).exists()
    has_photo = candidate.uploaded_documents.filter(
        document_type__code='photo'
    ).exists()
    has_offer = candidate.uploaded_documents.filter(
        document_type__code='offer'
    ).exists()
    has_mol = candidate.uploaded_documents.filter(
        document_type__code='mol'
    ).exists()
    
    doc_status.medical_report = has_medical
    doc_status.interpol = has_interpol
    doc_status.passport_copy = has_passport
    doc_status.passport_photo = has_photo
    doc_status.offer_letter = has_offer
    doc_status.mol_approval = has_mol
    doc_status.save()
    
    messages.success(request, 'Document deleted successfully.')
    return redirect('candidate_documents', candidate_id=candidate.id)


@login_required
@require_POST
def merge_documents(request, candidate_id):
    """Merge all uploaded documents into a single PDF - Updated to merge ALL documents"""
    candidate = get_object_or_404(Candidate, pk=candidate_id)
    
    # Get ALL documents, not just latest
    documents = candidate.uploaded_documents.all().order_by(
        'document_type__order', 'uploaded_at'
    )
    
    if not documents.exists():
        messages.error(request, 'No documents to merge.')
        return redirect('candidate_documents', candidate_id=candidate.id)
    
    try:
        # Create a PDF merger
        merger = PyPDF2.PdfMerger()
        merged_count = 0
        
        for doc in documents:
            file_path = doc.file.path
            file_ext = doc.file_type.lower()
            
            if not os.path.exists(file_path):
                messages.warning(request, f'Skipped {doc.original_filename} - file not found.')
                continue
                
            try:
                if file_ext == 'pdf':
                    # Add PDF directly
                    with open(file_path, 'rb') as f:
                        merger.append(f)
                        merged_count += 1
                elif file_ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
                    # Convert image to PDF and add
                    pdf_bytes = img2pdf.convert(file_path)
                    merger.append(BytesIO(pdf_bytes))
                    merged_count += 1
                else:
                    # Skip unsupported formats
                    messages.warning(request, f'Skipped {doc.original_filename} - unsupported format for merging.')
            except Exception as e:
                messages.warning(request, f'Error processing {doc.original_filename}: {str(e)}')
        
        if merged_count == 0:
            messages.error(request, 'No valid documents to merge.')
            return redirect('candidate_documents', candidate_id=candidate.id)
        
        # Save merged PDF
        safe_name = candidate.full_name.replace(' ', '_').replace('/', '_')
        merged_filename = f"{candidate.passport_no}_{safe_name}_documents.pdf"
        merged_path = os.path.join(settings.MEDIA_ROOT, 'merged_documents', 
                                   str(candidate.id), merged_filename)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(merged_path), exist_ok=True)
        
        # Write merged PDF
        with open(merged_path, 'wb') as f:
            merger.write(f)
        
        # Create or update MergedDocument
        merged_doc, created = MergedDocument.objects.update_or_create(
            candidate=candidate,
            defaults={
                'file': os.path.join('merged_documents', str(candidate.id), merged_filename),
                'created_by': request.user,
            }
        )
        merged_doc.document_types.set(documents.values_list('document_type', flat=True).distinct())
        
        messages.success(request, f'Successfully merged {merged_count} documents into one PDF.')
        
    except Exception as e:
        messages.error(request, f'Error merging documents: {str(e)}')
    
    return redirect('candidate_documents', candidate_id=candidate.id)

@login_required
def download_merged(request, candidate_id):
    """Download the merged PDF with candidate name and passport number"""
    merged = get_object_or_404(MergedDocument, candidate_id=candidate_id)
    file_path = merged.file.path
    
    if os.path.exists(file_path):
        response = FileResponse(open(file_path, 'rb'))
        response['Content-Type'] = 'application/pdf'
        
        # Create clean filename with candidate name and passport
        from django.utils.text import slugify
        safe_name = slugify(merged.candidate.full_name)
        
        # Format: PassportNo_FullName_documents.pdf
        filename = f"{merged.candidate.passport_no}_{safe_name}_documents.pdf"
        
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    else:
        messages.error(request, 'Merged file not found.')
        return redirect('candidate_documents', candidate_id=candidate_id)

@login_required
def initialize_document_types(request):
    """Initialize default document types (admin only)"""
    if not request.user.is_superuser:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')
    
    default_types = [
        {'code': 'medical', 'name': 'Medical Report', 'order': 1, 'required': True},
        {'code': 'passport', 'name': 'Passport Copy', 'order': 2, 'required': True},
        {'code': 'interpol', 'name': 'Interpol Clearance', 'order': 3, 'required': True},
        {'code': 'offer', 'name': 'Offer Letter', 'order': 4, 'required': True},
        {'code': 'mol', 'name': 'MOL Approval', 'order': 5, 'required': True},
        {'code': 'photo', 'name': 'Passport Photo', 'order': 6, 'required': True},
        {'code': 'contract', 'name': 'Employment Contract', 'order': 7, 'required': False},
        {'code': 'visa', 'name': 'Visa Document', 'order': 8, 'required': False},
        {'code': 'ticket', 'name': 'Flight Ticket', 'order': 9, 'required': False},
        {'code': 'other', 'name': 'Other Document', 'order': 99, 'required': False},
    ]
    
    created_count = 0
    for type_data in default_types:
        obj, created = DocumentType.objects.update_or_create(
            code=type_data['code'],
            defaults={
                'name': type_data['name'],
                'order': type_data['order'],
                'required': type_data['required']
            }
        )
        if created:
            created_count += 1
    
    messages.success(request, f'Document types initialized successfully. {created_count} new types created.')
    return redirect('document_list')

@login_required
@require_POST
def bulk_delete_documents(request, candidate_id):
    """Delete multiple documents at once"""
    candidate = get_object_or_404(Candidate, pk=candidate_id)
    document_ids = request.POST.get('document_ids', '').split(',')
    
    if not document_ids or document_ids[0] == '':
        messages.error(request, 'No documents selected for deletion.')
        return redirect('candidate_documents', candidate_id=candidate.id)
    
    deleted_count = 0
    for doc_id in document_ids:
        try:
            doc = CandidateDocument.objects.get(pk=doc_id, candidate=candidate)
            # Delete file
            if os.path.exists(doc.file.path):
                os.remove(doc.file.path)
            doc.delete()
            deleted_count += 1
        except CandidateDocument.DoesNotExist:
            continue
    
    # Update DocumentStatus
    doc_status = DocumentStatus.objects.get(candidate=candidate)
    
    # Check if at least one document exists for each type
    has_medical = candidate.uploaded_documents.filter(
        document_type__code='medical'
    ).exists()
    has_interpol = candidate.uploaded_documents.filter(
        document_type__code='interpol'
    ).exists()
    has_passport = candidate.uploaded_documents.filter(
        document_type__code='passport'
    ).exists()
    has_photo = candidate.uploaded_documents.filter(
        document_type__code='photo'
    ).exists()
    has_offer = candidate.uploaded_documents.filter(
        document_type__code='offer'
    ).exists()
    has_mol = candidate.uploaded_documents.filter(
        document_type__code='mol'
    ).exists()
    
    doc_status.medical_report = has_medical
    doc_status.interpol = has_interpol
    doc_status.passport_copy = has_passport
    doc_status.passport_photo = has_photo
    doc_status.offer_letter = has_offer
    doc_status.mol_approval = has_mol
    doc_status.save()
    
    messages.success(request, f'Successfully deleted {deleted_count} document(s).')
    return redirect('candidate_documents', candidate_id=candidate.id)

@login_required
def download_all_documents(request, candidate_id):
    """Download all documents for a candidate as a zip file"""
    candidate = get_object_or_404(Candidate, pk=candidate_id)
    documents = candidate.uploaded_documents.all()
    
    if not documents.exists():
        messages.error(request, 'No documents found for this candidate.')
        return redirect('candidate_documents', candidate_id=candidate.id)
    
    import zipfile
    from io import BytesIO
    import os
    
    # Create a zip file in memory
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for doc in documents:
            if doc.file and os.path.exists(doc.file.path):
                # Add file to zip with a clean filename
                arcname = f"{doc.document_type.name}_{doc.original_filename}"
                zip_file.write(doc.file.path, arcname)
    
    # Prepare response
    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer, content_type='application/zip')
    safe_name = candidate.full_name.replace(' ', '_')
    response['Content-Disposition'] = f'attachment; filename="{safe_name}_documents.zip"'
    
    return response