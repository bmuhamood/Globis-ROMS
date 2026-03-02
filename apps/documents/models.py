from django.db import models
from apps.candidates.models import Candidate
import os

class DocumentType(models.Model):
    """Document type categories"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)  # e.g., 'medical', 'passport', etc.
    description = models.TextField(blank=True)
    required = models.BooleanField(default=True)
    order = models.IntegerField(default=0)  # For ordering in merge
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Document Type"
        verbose_name_plural = "Document Types"
    
    def __str__(self):
        return self.name


class CandidateDocument(models.Model):
    """Actual uploaded documents for candidates"""
    candidate = models.ForeignKey(
        Candidate, 
        on_delete=models.CASCADE, 
        related_name='uploaded_documents'  # CHANGED: was 'documents'
    )
    document_type = models.ForeignKey(
        DocumentType, 
        on_delete=models.CASCADE,
        related_name='candidate_documents'
    )
    file = models.FileField(upload_to='candidate_documents/%Y/%m/%d/')
    original_filename = models.CharField(max_length=255)
    file_size = models.IntegerField(default=0)  # in bytes
    file_type = models.CharField(max_length=50)  # pdf, jpg, png, etc.
    
    # Metadata
    uploaded_by = models.ForeignKey(
        'auth.User', 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='uploaded_documents'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Version tracking
    version = models.IntegerField(default=1)
    is_latest = models.BooleanField(default=True)
    previous_version = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='next_versions'
    )
    
    class Meta:
        ordering = ['document_type__order', '-uploaded_at']
        indexes = [
            models.Index(fields=['candidate', 'document_type']),
            models.Index(fields=['is_latest']),
        ]
        verbose_name = "Candidate Document"
        verbose_name_plural = "Candidate Documents"
    
    def __str__(self):
        return f"{self.candidate.full_name} - {self.document_type.name}"
    
    def filename(self):
        return os.path.basename(self.file.name)
    
    def get_file_size_display(self):
        """Return human readable file size"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


class MergedDocument(models.Model):
    """Merged PDF document containing all candidate documents"""
    candidate = models.OneToOneField(
        Candidate, 
        on_delete=models.CASCADE, 
        related_name='merged_document'
    )
    file = models.FileField(upload_to='merged_documents/%Y/%m/%d/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'auth.User', 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='created_merged_documents'
    )
    document_types = models.ManyToManyField(
        DocumentType, 
        related_name='merged_documents'
    )
    
    def __str__(self):
        return f"Merged Document - {self.candidate.full_name}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Merged Document"
        verbose_name_plural = "Merged Documents"


class DocumentStatus(models.Model):
    """Track which document types are present (legacy model)"""
    candidate = models.OneToOneField(
        Candidate, 
        on_delete=models.CASCADE, 
        related_name='document_status'  # CHANGED: was 'documents'
    )
    medical_report = models.BooleanField(default=False)
    interpol = models.BooleanField(default=False)
    passport_copy = models.BooleanField(default=False)
    passport_photo = models.BooleanField(default=False)
    offer_letter = models.BooleanField(default=False)
    mol_approval = models.BooleanField(default=False, verbose_name="MOL Approval Received and Signed")
    updated_at = models.DateTimeField(auto_now=True)
    
    def missing_documents_count(self):
        count = 0
        if not self.medical_report: count += 1
        if not self.interpol: count += 1
        if not self.passport_copy: count += 1
        if not self.passport_photo: count += 1
        if not self.offer_letter: count += 1
        if not self.mol_approval: count += 1
        return count
    
    def __str__(self):
        return f"Document Status - {self.candidate.full_name}"
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = "Document Status"
        verbose_name_plural = "Document Statuses"
        indexes = [
            models.Index(fields=['candidate']),
            models.Index(fields=['updated_at']),
        ]