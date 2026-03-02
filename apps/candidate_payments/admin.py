from django.contrib import admin
from django.utils.html import format_html
from .models import CandidatePayment, PaymentHistory

class PaymentHistoryInline(admin.TabularInline):
    """Inline for payment history"""
    model = PaymentHistory
    extra = 0
    fields = ('due_date', 'amount_due', 'amount_paid', 'status', 'paid_date')
    readonly_fields = ('due_date', 'amount_due', 'amount_paid', 'status', 'paid_date')
    can_delete = False
    max_num = 20

@admin.register(CandidatePayment)
class CandidatePaymentAdmin(admin.ModelAdmin):
    """Admin for CandidatePayment"""
    list_display = ('receipt_number', 'candidate', 'payment_type', 'amount_display',
                   'date', 'payment_method', 'balance_change', 'received_by')
    list_filter = ('payment_type', 'payment_method', 'date', 'received_by')
    search_fields = ('receipt_number', 'candidate__full_name', 'candidate__passport_no')
    readonly_fields = ('receipt_number', 'previous_balance', 'new_balance', 
                      'created_at', 'balance_display')
    date_hierarchy = 'date'
    inlines = [PaymentHistoryInline]
    fieldsets = (
        ('Payment Information', {
            'fields': (
                'receipt_number', 'candidate', 'payment_type', 'amount',
                'date', 'payment_method', 'received_by', 'remarks'
            )
        }),
        ('Balance Tracking', {
            'fields': (
                'previous_balance', 'new_balance',
                ('balance_display',),
            ),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
    
    def amount_display(self, obj):
        """Display amount formatted"""
        # Pre-format the amount and pass as string
        formatted_amount = "{:,.0f}".format(float(obj.amount))
        return format_html('UGX {}', formatted_amount)
    amount_display.short_description = 'Amount'
    
    def balance_display(self, obj):
        """Display balance information"""
        # Pre-format both amounts
        formatted_prev = "{:,.0f}".format(float(obj.previous_balance))
        formatted_new = "{:,.0f}".format(float(obj.new_balance))
        return format_html(
            'Previous: UGX {}<br>New: UGX {}',
            formatted_prev, formatted_new
        )
    balance_display.short_description = 'Balance Change'
    
    def balance_change(self, obj):
        """Show balance change with arrow"""
        change = obj.previous_balance - obj.new_balance
        if change > 0:
            formatted_change = "{:,.0f}".format(float(change))
            return format_html('<span style="color: green;">↓ UGX {}</span>', formatted_change)
        return '-'
    balance_change.short_description = 'Change'

@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    """Admin for PaymentHistory"""
    list_display = ('candidate', 'due_date', 'amount_due_display', 'amount_paid_display',
                   'status_badge', 'paid_date', 'payment_link')
    list_filter = ('status', 'due_date', 'paid_date')
    search_fields = ('candidate__full_name', 'candidate__passport_no', 'remarks')
    readonly_fields = ('candidate', 'payment', 'due_date', 'amount_due', 
                      'amount_paid', 'status', 'paid_date', 'remarks')
    date_hierarchy = 'due_date'
    
    def amount_due_display(self, obj):
        # Pre-format the amount
        formatted_amount = "{:,.0f}".format(float(obj.amount_due))
        return format_html('UGX {}', formatted_amount)
    amount_due_display.short_description = 'Due'
    
    def amount_paid_display(self, obj):
        # Pre-format the amount
        formatted_amount = "{:,.0f}".format(float(obj.amount_paid))
        return format_html('UGX {}', formatted_amount)
    amount_paid_display.short_description = 'Paid'
    
    def status_badge(self, obj):
        """Show status with color"""
        colors = {
            'paid': 'green',
            'partial': 'orange',
            'overdue': 'red',
            'pending': 'gray'
        }
        color = colors.get(obj.status, 'gray')
        # Use string for the color and status
        return format_html('<span style="color: {}; font-weight: bold;">●</span> {}',
                          color, obj.get_status_display())
    status_badge.short_description = 'Status'
    
    def payment_link(self, obj):
        """Link to payment if exists"""
        if obj.payment:
            url = f"/admin/candidate_payments/candidatepayment/{obj.payment.id}/change/"
            return format_html('<a href="{}">Receipt #{}</a>', url, obj.payment.receipt_number)
        return '-'
    payment_link.short_description = 'Payment'
    
    def has_add_permission(self, request):
        """Prevent manual addition - should be created through payment process"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Allow changes only for superusers"""
        return request.user.is_superuser