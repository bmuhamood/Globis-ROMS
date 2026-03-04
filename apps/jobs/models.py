from django.db import models
from django.contrib.auth.models import User
from django_ckeditor_5.fields import CKEditor5Field
import os

class JobCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Job Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Job(models.Model):
    JOB_TYPES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
        ('remote', 'Remote'),
        ('temporary', 'Temporary'),
    ]
    
    EXPERIENCE_LEVELS = [
        ('entry', 'Entry Level'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior Level'),
        ('executive', 'Executive Level'),
    ]
    
    title = models.CharField(max_length=200)
    reference = models.CharField(max_length=50, unique=True, blank=True, help_text="Job reference code")
    category = models.ForeignKey(JobCategory, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Job details
    job_type = models.CharField(max_length=20, choices=JOB_TYPES, default='full_time')
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVELS, default='entry')
    location = models.CharField(max_length=200)
    salary_range = models.CharField(max_length=100, blank=True, help_text="e.g., UGX 1,500,000 - 2,500,000")
    
    # Dates
    posted_date = models.DateField(auto_now_add=True)
    closing_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    # Rich text descriptions (using CKEditor5)
    summary = models.TextField(max_length=500, help_text="Brief summary of the job (max 500 characters)")
    description = CKEditor5Field(config_name='extends', help_text="Full job description with formatting")
    requirements = CKEditor5Field(config_name='default', blank=True)
    benefits = CKEditor5Field(config_name='default', blank=True)
    how_to_apply = CKEditor5Field(config_name='default', blank=True)
    
    # Contact information
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20, blank=True)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='jobs_created')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='jobs_updated')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # View tracking
    views_count = models.PositiveIntegerField(default=0)
    applications_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-posted_date', 'title']
    
    def __str__(self):
        return f"{self.reference} - {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.reference:
            # Generate a unique reference
            import random
            import string
            prefix = ''.join(random.choices(string.ascii_uppercase, k=3))
            number = ''.join(random.choices(string.digits, k=5))
            self.reference = f"JOB-{prefix}-{number}"
        super().save(*args, **kwargs)
    
    @property
    def is_closing_soon(self):
        from django.utils import timezone
        from datetime import timedelta
        return self.closing_date <= timezone.now().date() + timedelta(days=7)

class JobAttachment(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='job_attachments/')
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return self.filename
    
    def save(self, *args, **kwargs):
        if not self.filename:
            self.filename = os.path.basename(self.file.name)
        super().save(*args, **kwargs)