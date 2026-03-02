from django.contrib import admin
from django.utils.html import format_html
from .models import VisaProcess

@admin.register(VisaProcess)
class VisaProcessAdmin(admin.ModelAdmin):
    """Admin for VisaProcess"""
    list_display = ('candidate', 'progress_bar', 'interview_badge', 'medical_badge', 
                   'interpol_badge', 'visa_applied_icon', 'visa_stamped_icon', 
                   'ticket_issued_icon', 'updated_at')
    list_filter = ('interview_status', 'medical_status', 'interpol_status',
                  'visa_applied', 'visa_stamped', 'ticket_issued')
    search_fields = ('candidate__full_name', 'candidate__passport_no')
    readonly_fields = ('updated_at', 'progress_percentage_display')
    fieldsets = (
        ('Candidate', {
            'fields': ('candidate',)
        }),
        ('Visa Status', {
            'fields': (
                ('interview_status', 'medical_status', 'interpol_status'),
                ('visa_applied', 'visa_stamped', 'ticket_issued'),
            )
        }),
        ('Progress', {
            'fields': ('progress_percentage_display',),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('updated_at',),
            'classes': ('collapse',),
        }),
    )
    
    def progress_bar(self, obj):
        """Show progress bar"""
        try:
            progress = obj.progress_percentage()
            if progress is None:
                progress = 0
            progress_value = int(progress)
            progress_str = str(progress_value)
            
            return format_html(
                '<div style="width: 100px; background: #eee; border-radius: 3px;">'
                '<div style="width: {}%; background: linear-gradient(90deg, #0184FC, #5EAAE1); height: 10px; border-radius: 3px;"></div>'
                '</div>',
                progress_str
            )
        except Exception:
            return '<div style="width: 100px; background: #eee; border-radius: 3px;"><div style="width: 0%; background: #ccc; height: 10px; border-radius: 3px;"></div></div>'
    progress_bar.short_description = 'Progress'
    
    def progress_percentage_display(self, obj):
        """Display progress percentage"""
        try:
            progress = obj.progress_percentage()
            if progress is None:
                return "0%"
            return f"{int(progress)}%"
        except Exception:
            return "0%"
    progress_percentage_display.short_description = 'Progress'
    
    def interview_badge(self, obj):
        """Show interview status badge"""
        try:
            colors = {'completed': 'green', 'in_progress': 'orange', 'pending': 'gray'}
            color = colors.get(obj.interview_status, 'gray')
            status_display = obj.get_interview_status_display() if hasattr(obj, 'get_interview_status_display') else str(obj.interview_status)
            # Use string concatenation instead of format_html for simple strings
            return f'<span style="color: {color};">●</span> {status_display}'
        except Exception:
            return '-'
    interview_badge.short_description = 'Interview'
    interview_badge.allow_tags = True
    
    def medical_badge(self, obj):
        """Show medical status badge"""
        try:
            colors = {'completed': 'green', 'in_progress': 'orange', 'pending': 'gray'}
            color = colors.get(obj.medical_status, 'gray')
            status_display = obj.get_medical_status_display() if hasattr(obj, 'get_medical_status_display') else str(obj.medical_status)
            return f'<span style="color: {color};">●</span> {status_display}'
        except Exception:
            return '-'
    medical_badge.short_description = 'Medical'
    medical_badge.allow_tags = True
    
    def interpol_badge(self, obj):
        """Show interpol status badge"""
        try:
            colors = {'completed': 'green', 'in_progress': 'orange', 'pending': 'gray'}
            color = colors.get(obj.interpol_status, 'gray')
            status_display = obj.get_interpol_status_display() if hasattr(obj, 'get_interpol_status_display') else str(obj.interpol_status)
            return f'<span style="color: {color};">●</span> {status_display}'
        except Exception:
            return '-'
    interpol_badge.short_description = 'Interpol'
    interpol_badge.allow_tags = True
    
    def visa_applied_icon(self, obj):
        """Show visa applied icon"""
        try:
            if obj.visa_applied:
                return '✓'
            return '✗'
        except Exception:
            return '-'
    visa_applied_icon.short_description = 'Applied'
    
    def visa_stamped_icon(self, obj):
        """Show visa stamped icon"""
        try:
            if obj.visa_stamped:
                return '✓'
            return '✗'
        except Exception:
            return '-'
    visa_stamped_icon.short_description = 'Stamped'
    
    def ticket_issued_icon(self, obj):
        """Show ticket issued icon"""
        try:
            if obj.ticket_issued:
                return '✓'
            return '✗'
        except Exception:
            return '-'
    ticket_issued_icon.short_description = 'Ticket'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('candidate')