from django.contrib import admin
from django.db.models import Sum
from django.utils.html import format_html
from django.template.response import TemplateResponse
from django.urls import path
from .models import Income, Expense

class IncomeAdmin(admin.ModelAdmin):
    """Admin for Income"""
    list_display = ('date', 'client', 'amount_display', 'description', 'received_by', 'created_at')
    list_filter = ('date', 'client', 'received_by')
    search_fields = ('client__company_name', 'description')
    readonly_fields = ('created_at',)
    date_hierarchy = 'date'
    fieldsets = (
        ('Income Details', {
            'fields': ('client', 'amount', 'date', 'description')
        }),
        ('Received By', {
            'fields': ('received_by',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
    
    def amount_display(self, obj):
        return format_html('UGX {:,.0f}', obj.amount)
    amount_display.short_description = 'Amount'

class ExpenseAdmin(admin.ModelAdmin):
    """Admin for Expense"""
    list_display = ('date', 'category', 'amount_display', 'description', 'paid_by', 'receipt_link')
    list_filter = ('category', 'date', 'paid_by')
    search_fields = ('description',)
    readonly_fields = ('created_at',)
    date_hierarchy = 'date'
    fieldsets = (
        ('Expense Details', {
            'fields': ('category', 'amount', 'date', 'description')
        }),
        ('Paid By', {
            'fields': ('paid_by',)
        }),
        ('Receipt', {
            'fields': ('receipt',),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
    
    def amount_display(self, obj):
        return format_html('UGX {:,.0f}', obj.amount)
    amount_display.short_description = 'Amount'
    
    def receipt_link(self, obj):
        """Link to receipt if exists"""
        if obj.receipt:
            return format_html('<a href="{}" target="_blank">View Receipt</a>', obj.receipt.url)
        return '-'
    receipt_link.short_description = 'Receipt'

# Register models
admin.site.register(Income, IncomeAdmin)
admin.site.register(Expense, ExpenseAdmin)