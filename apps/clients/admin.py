from django.contrib import admin
from django.db.models import Count, Sum
from django.utils.html import format_html
from .models import Client
from apps.placements.models import Placement
from apps.candidates.models import Candidate

class PlacementInline(admin.TabularInline):
    """Inline for placements in client admin"""
    model = Placement
    extra = 0
    fields = ('candidate', 'placement_fee', 'date_placed', 'payment_status')
    readonly_fields = ('candidate', 'placement_fee', 'date_placed')
    can_delete = False
    max_num = 10
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """Admin for Client"""
    list_display = ('company_name', 'contact_person', 'email', 'phone', 'country', 
                   'candidate_count', 'placement_count', 'total_revenue_display', 'created_at')
    list_filter = ('country', 'created_at')
    search_fields = ('company_name', 'contact_person', 'email', 'phone')
    readonly_fields = ('created_at', 'candidate_count', 'placement_count', 'total_revenue_display')
    inlines = [PlacementInline]
    fieldsets = (
        ('Company Information', {
            'fields': ('company_name', ('contact_person', 'email'), 'phone', 'address', 'country')
        }),
        ('Statistics', {
            'fields': ('candidate_count', 'placement_count', 'total_revenue_display'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
    
    def candidate_count(self, obj):
        """Count of candidates for this client"""
        try:
            count = obj.candidates.count()
            url = f"/admin/candidates/candidate/?client__id__exact={obj.id}"
            return format_html('<a href="{}">{}</a>', url, str(count))
        except (AttributeError, TypeError, ValueError):
            return '0'
    candidate_count.short_description = 'Candidates'
    
    def placement_count(self, obj):
        """Count of placements for this client"""
        try:
            count = obj.placements.count()
            url = f"/admin/placements/placement/?client__id__exact={obj.id}"
            return format_html('<a href="{}">{}</a>', url, str(count))
        except (AttributeError, TypeError, ValueError):
            return '0'
    placement_count.short_description = 'Placements'
    
    def total_revenue_display(self, obj):
        """Total revenue from placements - formatted properly"""
        try:
            # Get the total from the queryset annotation if available
            if hasattr(obj, 'total_revenue') and obj.total_revenue:
                total = float(obj.total_revenue)
            else:
                # Fallback to aggregate query
                total = float(obj.placements.aggregate(total=Sum('placement_fee'))['total'] or 0)
            
            # Format the number first, then pass as string to format_html
            formatted_total = "{:,.0f}".format(total)
            return format_html('UGX {}', formatted_total)
        except (TypeError, ValueError, AttributeError):
            return format_html('UGX 0')
    total_revenue_display.short_description = 'Total Revenue'
    
    def get_queryset(self, request):
        """Annotate queryset with counts and total revenue"""
        return super().get_queryset(request).annotate(
            candidate_count=Count('candidates', distinct=True),
            placement_count=Count('placements', distinct=True),
            total_revenue=Sum('placements__placement_fee')
        )