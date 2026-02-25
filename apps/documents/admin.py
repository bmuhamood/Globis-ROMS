from django.contrib import admin
from django.utils.html import format_html
from .models import DocumentStatus

@admin.register(DocumentStatus)
class DocumentStatusAdmin(admin.ModelAdmin):
    """Admin for DocumentStatus"""
    list_display = ('candidate', 'medical_status', 'interpol_status', 
                   'passport_copy_status', 'passport_photo_status',
                   'offer_letter_status', 'mol_approval_status',
                   'missing_count', 'updated_at')
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
        if obj.medical_report:
            return format_html('<span style="color: green;">✓ Yes</span>')
        return format_html('<span style="color: red;">✗ No</span>')
    medical_status.short_description = 'Medical'
    
    def interpol_status(self, obj):
        """Show interpol status with icon"""
        if obj.interpol:
            return format_html('<span style="color: green;">✓ Yes</span>')
        return format_html('<span style="color: red;">✗ No</span>')
    interpol_status.short_description = 'Interpol'
    
    def passport_copy_status(self, obj):
        """Show passport copy status with icon"""
        if obj.passport_copy:
            return format_html('<span style="color: green;">✓ Yes</span>')
        return format_html('<span style="color: red;">✗ No</span>')
    passport_copy_status.short_description = 'Pass Copy'
    
    def passport_photo_status(self, obj):
        """Show passport photo status with icon"""
        if obj.passport_photo:
            return format_html('<span style="color: green;">✓ Yes</span>')
        return format_html('<span style="color: red;">✗ No</span>')
    passport_photo_status.short_description = 'Pass Photo'
    
    def offer_letter_status(self, obj):
        """Show offer letter status with icon"""
        if obj.offer_letter:
            return format_html('<span style="color: green;">✓ Yes</span>')
        return format_html('<span style="color: red;">✗ No</span>')
    offer_letter_status.short_description = 'Offer Ltr'
    
    def mol_approval_status(self, obj):
        """Show MOL approval status with icon"""
        if obj.mol_approval:
            return format_html('<span style="color: green;">✓ Yes</span>')
        return format_html('<span style="color: red;">✗ No</span>')
    mol_approval_status.short_description = 'MOL'
    
    def missing_count(self, obj):
        """Show missing documents count with color"""
        count = obj.missing_documents_count()
        if count == 0:
            return format_html('<span style="color: green;">{}</span>', count)
        elif count <= 2:
            return format_html('<span style="color: orange;">{}</span>', count)
        else:
            return format_html('<span style="color: red; font-weight: bold;">{}</span>', count)
    missing_count.short_description = 'Missing'