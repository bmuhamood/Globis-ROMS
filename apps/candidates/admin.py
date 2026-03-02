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
        try:
            if obj.fully_paid:
                return format_html('<span style="color: green; font-weight: bold;">✓ Fully Paid</span>')
            elif obj.remaining_balance and obj.remaining_balance > 0:
                return format_html('<span style="color: orange;">⏳ Pending</span>')
        except (AttributeError, TypeError):
            pass
        return '-'
    payment_status.short_description = 'Status'
    
    def payment_progress(self, obj):
        """Show payment progress bar"""
        try:
            # Safely get progress value
            progress = obj.get_payment_progress() if hasattr(obj, 'get_payment_progress') else 0
            
            # Ensure we have a valid number
            if progress is None:
                progress_value = 0
            else:
                try:
                    progress_value = int(float(progress))
                except (TypeError, ValueError):
                    progress_value = 0
            
            # Ensure progress_value is within bounds
            progress_value = max(0, min(100, progress_value))
            
            color = 'green' if progress_value >= 100 else 'orange'
            
            # Ensure all values are strings and not empty
            width_str = str(progress_value)
            percent_str = str(progress_value)
            color_str = str(color)
            
            # Only call format_html if we have all arguments
            if width_str and color_str and percent_str:
                return format_html(
                    '<div style="width: 100px; background: #eee; border-radius: 3px;">'
                    '<div style="width: {}%; background: {}; height: 10px; border-radius: 3px;"></div>'
                    '</div> {}%',
                    width_str, color_str, percent_str
                )
            
        except Exception:
            pass
            
        # Return a default if anything goes wrong
        return format_html(
            '<div style="width: 100px; background: #eee; border-radius: 3px;">'
            '<div style="width: 0%; background: gray; height: 10px; border-radius: 3px;"></div>'
            '</div> 0%'
        )
    payment_progress.short_description = 'Progress'
    
    def payment_progress_display(self, obj):
        """Display payment progress for readonly field"""
        try:
            if hasattr(obj, 'get_payment_progress'):
                progress = obj.get_payment_progress()
                if progress is not None:
                    return f"{int(float(progress))}%"
        except (TypeError, ValueError, AttributeError):
            pass
        return "0%"
    payment_progress_display.short_description = 'Payment Progress'
    
    def total_paid_display(self, obj):
        """Display total paid amount"""
        try:
            if hasattr(obj, 'initial_amount') and hasattr(obj, 'remaining_balance'):
                total_paid = float(obj.initial_amount) - float(obj.remaining_balance)
                formatted_amount = "{:,.0f}".format(max(0, total_paid))
                return format_html('UGX {}', formatted_amount)
        except (TypeError, ValueError, AttributeError):
            pass
        return format_html('UGX 0')
    total_paid_display.short_description = 'Total Paid'
    
    def remaining_balance_display(self, obj):
        """Display remaining balance"""
        try:
            if hasattr(obj, 'remaining_balance') and obj.remaining_balance is not None:
                formatted_amount = "{:,.0f}".format(float(obj.remaining_balance))
                return format_html('UGX {}', formatted_amount)
        except (TypeError, ValueError, AttributeError):
            pass
        return format_html('UGX 0')
    remaining_balance_display.short_description = 'Remaining Balance'
    
    actions = ['mark_as_fully_paid', 'reset_payment_status']
    
    def mark_as_fully_paid(self, request, queryset):
        """Mark selected candidates as fully paid"""
        try:
            updated = queryset.update(fully_paid=True, fully_paid_date=timezone.now().date())
            self.message_user(request, f'{updated} candidates marked as fully paid.')
        except Exception as e:
            self.message_user(request, f'Error: {str(e)}', level='ERROR')
    mark_as_fully_paid.short_description = "Mark selected as fully paid"
    
    def reset_payment_status(self, request, queryset):
        """Reset payment status"""
        try:
            updated = queryset.update(fully_paid=False, fully_paid_date=None)
            self.message_user(request, f'{updated} candidates payment status reset.')
        except Exception as e:
            self.message_user(request, f'Error: {str(e)}', level='ERROR')
    reset_payment_status.short_description = "Reset payment status"