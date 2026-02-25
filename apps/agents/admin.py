from django.contrib import admin
from django.db.models import Count, Sum
from django.utils.html import format_html
from .models import Agent
from apps.candidates.models import Candidate

class CandidateInline(admin.TabularInline):
    """Inline for candidates in agent admin"""
    model = Candidate
    extra = 0
    fields = ('full_name', 'passport_no', 'position', 'client', 'created_at')
    readonly_fields = ('full_name', 'passport_no', 'position', 'client', 'created_at')
    can_delete = False
    max_num = 10
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    """Admin for Agent"""
    list_display = ('name', 'email', 'phone', 'commission_rate', 
                   'candidate_count', 'total_payments', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'email', 'phone')
    readonly_fields = ('created_at', 'candidate_count', 'total_payments')
    inlines = [CandidateInline]
    fieldsets = (
        ('Agent Information', {
            'fields': ('name', 'email', 'phone', 'address', 'commission_rate')
        }),
        ('Statistics', {
            'fields': ('candidate_count', 'total_payments'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
    
    def candidate_count(self, obj):
        """Count of candidates for this agent"""
        count = obj.candidates.count()
        url = f"/admin/candidates/candidate/?agent__id__exact={obj.id}"
        return format_html('<a href="{}">{}</a>', url, count)
    candidate_count.short_description = 'Candidates'
    
    def total_payments(self, obj):
        """Total payments collected by agent's candidates"""
        total = obj.candidates.aggregate(
            total=Sum('payments__amount')
        )['total'] or 0
        return format_html('UGX {:,.0f}', total)
    total_payments.short_description = 'Total Payments'
    
    def get_queryset(self, request):
        """Annotate queryset with counts"""
        return super().get_queryset(request).annotate(
            candidate_count=Count('candidates', distinct=True)
        )