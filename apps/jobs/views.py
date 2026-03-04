from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import FileResponse, Http404
from .models import Job, JobCategory, JobAttachment
from .forms import JobForm, JobAttachmentForm
import os

# Public views (no login required)
def job_list(request):
    """Public job listing page"""
    jobs = Job.objects.filter(is_active=True).order_by('-posted_date')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        jobs = jobs.filter(
            Q(title__icontains=search_query) |
            Q(reference__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(summary__icontains=search_query)
        )
    
    # Filter by category
    category_id = request.GET.get('category')
    if category_id:
        jobs = jobs.filter(category_id=category_id)
    
    # Filter by job type
    job_type = request.GET.get('job_type')
    if job_type:
        jobs = jobs.filter(job_type=job_type)
    
    # Pagination
    paginator = Paginator(jobs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = JobCategory.objects.all()
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'search_query': search_query,
        'category_id': int(category_id) if category_id else None,
        'job_type': job_type,
        'job_types': Job.JOB_TYPES,
    }
    return render(request, 'jobs/public_list.html', context)

def job_detail(request, pk):
    """Public job detail page"""
    job = get_object_or_404(Job, pk=pk, is_active=True)
    
    # Increment view count
    job.views_count += 1
    job.save(update_fields=['views_count'])
    
    context = {
        'job': job,
    }
    return render(request, 'jobs/public_detail.html', context)

def download_attachment(request, pk):
    """Download job attachment"""
    attachment = get_object_or_404(JobAttachment, pk=pk)
    
    # Only allow download if job is active or user is staff
    if not attachment.job.is_active and not (request.user.is_authenticated and request.user.is_staff):
        raise Http404("Attachment not available")
    
    file_path = attachment.file.path
    if os.path.exists(file_path):
        response = FileResponse(open(file_path, 'rb'))
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Disposition'] = f'attachment; filename="{attachment.filename}"'
        return response
    else:
        raise Http404("File not found")

# Admin views (login required)
@login_required
def admin_job_list(request):
    """Admin job management"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page")
        return redirect('jobs:job_list')
    
    jobs = Job.objects.all().order_by('-posted_date')
    
    # Filter by status
    status = request.GET.get('status')
    if status == 'active':
        jobs = jobs.filter(is_active=True)
    elif status == 'inactive':
        jobs = jobs.filter(is_active=False)
    
    search_query = request.GET.get('search', '')
    if search_query:
        jobs = jobs.filter(
            Q(title__icontains=search_query) |
            Q(reference__icontains=search_query)
        )
    
    context = {
        'jobs': jobs,
        'status': status,
        'search_query': search_query,
    }
    return render(request, 'jobs/admin_list.html', context)

@login_required
def admin_job_create(request):
    """Create new job"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page")
        return redirect('jobs:job_list')
    
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.created_by = request.user
            job.save()
            
            # Handle file attachments
            files = request.FILES.getlist('attachments')
            for file in files:
                JobAttachment.objects.create(
                    job=job,
                    file=file,
                    uploaded_by=request.user
                )
            
            messages.success(request, f'Job "{job.title}" created successfully!')
            return redirect('jobs:admin_job_list')
    else:
        form = JobForm()
    
    # Add categories to context for debugging (optional)
    categories = JobCategory.objects.all()
    print(f"Categories available: {categories.count()}")  # Check console
    
    context = {
        'form': form,
        'is_edit': False,
        'categories': categories,  # Pass to template if needed
    }
    return render(request, 'jobs/admin_form.html', context)

@login_required
def admin_job_edit(request, pk):
    """Edit existing job"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page")
        return redirect('jobs:job_list')
    
    job = get_object_or_404(Job, pk=pk)
    
    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            job = form.save(commit=False)
            job.updated_by = request.user
            job.save()
            
            # Handle new attachments
            files = request.FILES.getlist('attachments')
            for file in files:
                JobAttachment.objects.create(
                    job=job,
                    file=file,
                    uploaded_by=request.user
                )
            
            messages.success(request, f'Job "{job.title}" updated successfully!')
            return redirect('jobs:admin_job_list')
    else:
        form = JobForm(instance=job)
    
    context = {
        'form': form,
        'job': job,
        'is_edit': True,
    }
    return render(request, 'jobs/admin_form.html', context)

@login_required
def admin_job_delete(request, pk):
    """Delete job"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page")
        return redirect('jobs:job_list')  # Fixed: Added 'jobs:' namespace
    
    job = get_object_or_404(Job, pk=pk)
    job_title = job.title
    job.delete()
    messages.success(request, f'Job "{job_title}" deleted successfully!')
    return redirect('jobs:admin_job_list')  # Fixed: Added 'jobs:' namespace

@login_required
def admin_delete_attachment(request, pk):
    """Delete job attachment"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page")
        return redirect('jobs:job_list')  # Fixed: Added 'jobs:' namespace
    
    attachment = get_object_or_404(JobAttachment, pk=pk)
    job_id = attachment.job.id
    attachment.delete()
    messages.success(request, 'Attachment deleted successfully!')
    return redirect('jobs:admin_job_edit', pk=job_id)  # Fixed: Added 'jobs:' namespace

def print_job(request, pk):
    """Print-friendly job view"""
    job = get_object_or_404(Job, pk=pk)
    
    # Allow printing even if job is inactive for staff
    if not job.is_active and not (request.user.is_authenticated and request.user.is_staff):
        raise Http404("Job not found")
    
    return render(request, 'jobs/print.html', {'job': job})