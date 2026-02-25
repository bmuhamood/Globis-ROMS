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
        return format_html('UGX {:,.0f}', obj.placement_fee)
    placement_fee_display.short_description = 'Fee'
    
    def payment_status_badge(self, obj):
        """Show payment status with color"""
        colors = {
            'paid': 'green',
            'partial': 'orange',
            'pending': 'red'
        }
        color = colors.get(obj.payment_status, 'gray')
        return format_html('<span style="color: {}; font-weight: bold;">●</span> {}',
                          color, obj.get_payment_status_display())
    payment_status_badge.short_description = 'Status'