from django.contrib import admin
from django.db.models import Sum
from django.utils.html import format_html
from .models import Candidate
from apps.documents.models import DocumentStatus
from apps.visa_process.models import VisaProcess
from apps.candidate_payments.models import CandidatePayment
from django.utils import timezone

class DocumentStatusInline(admin.StackedInline):
    """Inline for document status"""
    model = DocumentStatus
    can_delete = False
    fieldsets = (
        ('Document Status', {
            'fields': (
                ('medical_report', 'interpol'),
                ('passport_copy', 'passport_photo'),
                ('offer_letter', 'mol_approval'),
            )
        }),
    )

class VisaProcessInline(admin.StackedInline):
    """Inline for visa process"""
    model = VisaProcess
    can_delete = False
    fieldsets = (
        ('Visa Process', {
            'fields': (
                ('interview_status', 'medical_status', 'interpol_status'),
                ('visa_applied', 'visa_stamped', 'ticket_issued'),
            )
        }),
    )

class CandidatePaymentInline(admin.TabularInline):
    """Inline for candidate payments"""
    model = CandidatePayment
    extra = 0
    fields = ('date', 'payment_type', 'amount', 'payment_method', 'receipt_number')
    readonly_fields = ('receipt_number',)
    can_delete = True
    max_num = 10

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    """Admin for Candidate"""
    list_display = ('full_name', 'passport_no', 'position', 'agent', 'client', 
                   'payment_status', 'payment_progress', 'created_at')
    list_filter = ('payment_plan', 'fully_paid', 'agent', 'client', 'created_at')
    search_fields = ('full_name', 'passport_no', 'contact_number', 'position')
    readonly_fields = ('created_at', 'updated_at', 'payment_progress_display', 
                      'total_paid_display', 'remaining_balance_display')
    inlines = [DocumentStatusInline, VisaProcessInline, CandidatePaymentInline]
    fieldsets = (
        ('Personal Information', {
            'fields': (
                'full_name', 'passport_no', 'passport_expiry',
                ('mother_name', 'father_name'),
                ('contact_number', 'blood_group'),
            )
        }),
        ('Employment Details', {
            'fields': ('position', 'salary', 'agent', 'client', 'remarks')
        }),
        ('Payment Information', {
            'fields': (
                'payment_plan', 'initial_amount', 'remaining_balance_display',
                'total_paid_display', 'payment_progress_display',
                ('loan_provider', 'loan_reference'),
                ('fully_paid', 'fully_paid_date'),
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def payment_status(self, obj):
        """Show payment status badge"""
        if obj.fully_paid:
            return format_html('<span style="color: green; font-weight: bold;">✓ Fully Paid</span>')
        elif obj.remaining_balance > 0:
            return format_html('<span style="color: orange;">⏳ Pending</span>')
        return '-'
    payment_status.short_description = 'Status'
    
    def payment_progress(self, obj):
        """Show payment progress bar"""
        progress = obj.get_payment_progress()
        color = 'green' if progress >= 100 else 'orange'
        return format_html(
            '<div style="width: 100px; background: #eee; border-radius: 3px;">'
            '<div style="width: {}%; background: {}; height: 10px; border-radius: 3px;"></div>'
            '</div> {}%',
            progress, color, progress
        )
    payment_progress.short_description = 'Progress'
    
    def payment_progress_display(self, obj):
        """Display payment progress for readonly field"""
        return f"{obj.get_payment_progress()}%"
    payment_progress_display.short_description = 'Payment Progress'
    
    def total_paid_display(self, obj):
        """Display total paid amount"""
        total_paid = obj.initial_amount - obj.remaining_balance
        return format_html('UGX {:,.0f}', total_paid)
    total_paid_display.short_description = 'Total Paid'
    
    def remaining_balance_display(self, obj):
        """Display remaining balance"""
        return format_html('UGX {:,.0f}', obj.remaining_balance)
    remaining_balance_display.short_description = 'Remaining Balance'
    
    actions = ['mark_as_fully_paid', 'reset_payment_status']
    
    def mark_as_fully_paid(self, request, queryset):
        """Mark selected candidates as fully paid"""
        updated = queryset.update(fully_paid=True, fully_paid_date=timezone.now().date())
        self.message_user(request, f'{updated} candidates marked as fully paid.')
    mark_as_fully_paid.short_description = "Mark selected as fully paid"
    
    def reset_payment_status(self, request, queryset):
        """Reset payment status"""
        updated = queryset.update(fully_paid=False, fully_paid_date=None)
        self.message_user(request, f'{updated} candidates payment status reset.')
    reset_payment_status.short_description = "Reset payment status"