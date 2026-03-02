from django.contrib import admin
from django.utils.html import format_html
from .models import Placement

@admin.register(Placement)
class PlacementAdmin(admin.ModelAdmin):
    """Admin for Placement"""
    list_display = ('candidate', 'client', 'date_placed', 'placement_fee_display',
                   'payment_status_badge', 'created_at')
    list_filter = ('payment_status', 'date_placed', 'client')
    search_fields = ('candidate__full_name', 'candidate__passport_no', 
                    'client__company_name', 'notes')
    readonly_fields = ('created_at',)
    date_hierarchy = 'date_placed'
    fieldsets = (
        ('Placement Details', {
            'fields': ('candidate', 'client', 'placement_fee', 'date_placed')
        }),
        ('Payment Information', {
            'fields': ('payment_status', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
    
    def placement_fee_display(self, obj):
        """Display placement fee formatted"""
        try:
            # Convert to float first, then format
            fee_value = float(obj.placement_fee) if obj.placement_fee else 0
            formatted_fee = "{:,.0f}".format(fee_value)
            return format_html('UGX {}', formatted_fee)
        except (TypeError, ValueError, AttributeError):
            return format_html('UGX 0')
    placement_fee_display.short_description = 'Fee'
    
    def payment_status_badge(self, obj):
        """Show payment status with color"""
        try:
            colors = {
                'paid': 'green',
                'partial': 'orange',
                'pending': 'red'
            }
            color = colors.get(obj.payment_status, 'gray')
            status_display = obj.get_payment_status_display() if hasattr(obj, 'get_payment_status_display') else str(obj.payment_status)
            return format_html('<span style="color: {}; font-weight: bold;">●</span> {}',
                              color, status_display)
        except (AttributeError, ValueError):
            return '-'
    payment_status_badge.short_description = 'Status'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('candidate', 'client')