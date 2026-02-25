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
        progress = obj.progress_percentage()
        return format_html(
            '<div style="width: 100px; background: #eee; border-radius: 3px;">'
            '<div style="width: {}%; background: linear-gradient(90deg, #0184FC, #5EAAE1); height: 10px; border-radius: 3px;"></div>'
            '</div>',
            progress
        )
    progress_bar.short_description = 'Progress'
    
    def progress_percentage_display(self, obj):
        """Display progress percentage"""
        return f"{obj.progress_percentage()}%"
    progress_percentage_display.short_description = 'Progress'
    
    def interview_badge(self, obj):
        """Show interview status badge"""
        colors = {'completed': 'green', 'in_progress': 'orange', 'pending': 'gray'}
        color = colors.get(obj.interview_status, 'gray')
        return format_html('<span style="color: {};">●</span> {}', 
                          color, obj.get_interview_status_display())
    interview_badge.short_description = 'Interview'
    
    def medical_badge(self, obj):
        """Show medical status badge"""
        colors = {'completed': 'green', 'in_progress': 'orange', 'pending': 'gray'}
        color = colors.get(obj.medical_status, 'gray')
        return format_html('<span style="color: {};">●</span> {}', 
                          color, obj.get_medical_status_display())
    medical_badge.short_description = 'Medical'
    
    def interpol_badge(self, obj):
        """Show interpol status badge"""
        colors = {'completed': 'green', 'in_progress': 'orange', 'pending': 'gray'}
        color = colors.get(obj.interpol_status, 'gray')
        return format_html('<span style="color: {};">●</span> {}', 
                          color, obj.get_interpol_status_display())
    interpol_badge.short_description = 'Interpol'
    
    def visa_applied_icon(self, obj):
        """Show visa applied icon"""
        if obj.visa_applied:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')
    visa_applied_icon.short_description = 'Applied'
    
    def visa_stamped_icon(self, obj):
        """Show visa stamped icon"""
        if obj.visa_stamped:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')
    visa_stamped_icon.short_description = 'Stamped'
    
    def ticket_issued_icon(self, obj):
        """Show ticket issued icon"""
        if obj.ticket_issued:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')
    ticket_issued_icon.short_description = 'Ticket'