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
                   'candidate_count', 'total_payments_display', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'email', 'phone')
    readonly_fields = ('created_at', 'candidate_count', 'total_payments_display')
    inlines = [CandidateInline]
    fieldsets = (
        ('Agent Information', {
            'fields': ('name', 'email', 'phone', 'address', 'commission_rate')
        }),
        ('Statistics', {
            'fields': ('candidate_count', 'total_payments_display'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
    
    def candidate_count(self, obj):
        """Count of candidates for this agent"""
        try:
            count = obj.candidates.count()
            url = f"/admin/candidates/candidate/?agent__id__exact={obj.id}"
            return format_html('<a href="{}">{}</a>', url, str(count))
        except Exception:
            return '0'
    candidate_count.short_description = 'Candidates'
    
    def total_payments_display(self, obj):
        """Total payments collected by agent's candidates - formatted properly"""
        try:
            # Get the total from the queryset annotation if available
            if hasattr(obj, 'total_payments') and obj.total_payments:
                total = float(obj.total_payments)
            else:
                # Fallback to aggregate query
                total = float(obj.candidates.aggregate(
                    total=Sum('payments__amount')
                )['total'] or 0)
            
            # Format the number first, then pass as string to format_html
            formatted_total = "{:,.0f}".format(total)
            return format_html('UGX {}', formatted_total)
        except (TypeError, ValueError, AttributeError):
            return format_html('UGX 0')
    total_payments_display.short_description = 'Total Payments'
    
    def get_queryset(self, request):
        """Annotate queryset with counts and total payments"""
        return super().get_queryset(request).annotate(
            candidate_count=Count('candidates', distinct=True),
            total_payments=Sum('candidates__payments__amount')
        )