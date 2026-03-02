from django.contrib import admin
from django.utils.html import format_html
from .models import DocumentStatus, DocumentType, CandidateDocument, MergedDocument

@admin.register(DocumentStatus)
class DocumentStatusAdmin(admin.ModelAdmin):
    """Admin for DocumentStatus"""
    list_display = ('candidate', 'medical_status', 'interpol_status', 
                   'passport_copy_status', 'passport_photo_status',
                   'offer_letter_status', 'mol_approval_status',
                   'missing_count_display', 'updated_at')
    list_filter = ('medical_report', 'interpol', 'passport_copy', 
                  'passport_photo', 'offer_letter', 'mol_approval')
    search_fields = ('candidate__full_name', 'candidate__passport_no')
    readonly_fields = ('updated_at',)
    fieldsets = (
        ('Candidate', {
            'fields': ('candidate',)
        }),
        ('Document Status', {
            'fields': (
                ('medical_report', 'interpol'),
                ('passport_copy', 'passport_photo'),
                ('offer_letter', 'mol_approval'),
            )
        }),
        ('Timestamps', {
            'fields': ('updated_at',),
            'classes': ('collapse',),
        }),
    )
    
    def medical_status(self, obj):
        """Show medical report status with icon"""
        try:
            if obj.medical_report:
                return "✓ Yes"
            return "✗ No"
        except Exception:
            return "-"
    medical_status.short_description = 'Medical'
    
    def interpol_status(self, obj):
        """Show interpol status with icon"""
        try:
            if obj.interpol:
                return "✓ Yes"
            return "✗ No"
        except Exception:
            return "-"
    interpol_status.short_description = 'Interpol'
    
    def passport_copy_status(self, obj):
        """Show passport copy status with icon"""
        try:
            if obj.passport_copy:
                return "✓ Yes"
            return "✗ No"
        except Exception:
            return "-"
    passport_copy_status.short_description = 'Pass Copy'
    
    def passport_photo_status(self, obj):
        """Show passport photo status with icon"""
        try:
            if obj.passport_photo:
                return "✓ Yes"
            return "✗ No"
        except Exception:
            return "-"
    passport_photo_status.short_description = 'Pass Photo'
    
    def offer_letter_status(self, obj):
        """Show offer letter status with icon"""
        try:
            if obj.offer_letter:
                return "✓ Yes"
            return "✗ No"
        except Exception:
            return "-"
    offer_letter_status.short_description = 'Offer Ltr'
    
    def mol_approval_status(self, obj):
        """Show MOL approval status with icon"""
        try:
            if obj.mol_approval:
                return "✓ Yes"
            return "✗ No"
        except Exception:
            return "-"
    mol_approval_status.short_description = 'MOL'
    
    def missing_count_display(self, obj):
        """Show missing documents count with color"""
        try:
            # Safely get the missing count
            if hasattr(obj, 'missing_documents_count'):
                count = obj.missing_documents_count()
            else:
                count = 0
            
            # Ensure count is a valid number
            if count is None:
                count = 0
            
            # Convert to integer
            count_int = int(count)
            
            # Return simple string based on count value
            if count_int == 0:
                return "0"
            elif count_int <= 2:
                return str(count_int)
            else:
                return str(count_int)
                
        except Exception:
            return "0"
    missing_count_display.short_description = 'Missing'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('candidate')


@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    """Admin for DocumentType"""
    list_display = ('name', 'code', 'order', 'required', 'documents_count')
    list_filter = ('required',)
    search_fields = ('name', 'code')
    
    def documents_count(self, obj):
        """Count of documents of this type"""
        try:
            from .models import CandidateDocument
            count = CandidateDocument.objects.filter(document_type=obj).count()
            return str(count)
        except Exception:
            return '0'
    documents_count.short_description = 'Documents'


@admin.register(CandidateDocument)
class CandidateDocumentAdmin(admin.ModelAdmin):
    """Admin for CandidateDocument"""
    list_display = ('id', 'candidate', 'document_type', 'original_filename', 
                   'file_size_display', 'version', 'uploaded_by', 'uploaded_at')
    list_filter = ('document_type', 'uploaded_at', 'version')
    search_fields = ('candidate__full_name', 'candidate__passport_no', 'original_filename')
    readonly_fields = ('file_size_display', 'uploaded_at', 'file_preview')
    fieldsets = (
        ('Document Information', {
            'fields': ('candidate', 'document_type', 'original_filename', 'file_size_display', 'version')
        }),
        ('File', {
            'fields': ('file', 'file_preview')
        }),
        ('Upload Information', {
            'fields': ('uploaded_by', 'uploaded_at')
        }),
    )
    
    def file_size_display(self, obj):
        """Display file size in human readable format"""
        return obj.get_file_size_display()
    file_size_display.short_description = 'File Size'
    
    def file_preview(self, obj):
        """Show file preview link"""
        try:
            if obj.file and obj.file.url:
                return format_html('<a href="{}" target="_blank">View File</a>', obj.file.url)
        except Exception:
            pass
        return '-'
    file_preview.short_description = 'Preview'


@admin.register(MergedDocument)
class MergedDocumentAdmin(admin.ModelAdmin):
    """Admin for MergedDocument"""
    list_display = ('candidate', 'created_at', 'created_by', 'file_link')
    search_fields = ('candidate__full_name', 'candidate__passport_no')
    readonly_fields = ('created_at', 'file_link')
    
    def file_link(self, obj):
        """Link to download merged file"""
        try:
            if obj.file and obj.file.url:
                return format_html('<a href="{}" target="_blank">Download PDF</a>', obj.file.url)
        except Exception:
            pass
        return '-'
    file_link.short_description = 'File'