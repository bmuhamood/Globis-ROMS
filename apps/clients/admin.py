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
                   'candidate_count', 'placement_count', 'total_revenue', 'created_at')
    list_filter = ('country', 'created_at')
    search_fields = ('company_name', 'contact_person', 'email', 'phone')
    readonly_fields = ('created_at', 'candidate_count', 'placement_count', 'total_revenue')
    inlines = [PlacementInline]
    fieldsets = (
        ('Company Information', {
            'fields': ('company_name', ('contact_person', 'email'), 'phone', 'address', 'country')
        }),
        ('Statistics', {
            'fields': ('candidate_count', 'placement_count', 'total_revenue'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
    
    def candidate_count(self, obj):
        """Count of candidates for this client"""
        count = obj.candidates.count()
        url = f"/admin/candidates/candidate/?client__id__exact={obj.id}"
        return format_html('<a href="{}">{}</a>', url, count)
    candidate_count.short_description = 'Candidates'
    
    def placement_count(self, obj):
        """Count of placements for this client"""
        count = obj.placements.count()
        url = f"/admin/placements/placement/?client__id__exact={obj.id}"
        return format_html('<a href="{}">{}</a>', url, count)
    placement_count.short_description = 'Placements'
    
    def total_revenue(self, obj):
        """Total revenue from placements"""
        total = obj.placements.aggregate(total=Sum('placement_fee'))['total'] or 0
        return format_html('UGX {:,.0f}', total)
    total_revenue.short_description = 'Total Revenue'
    
    def get_queryset(self, request):
        """Annotate queryset with counts"""
        return super().get_queryset(request).annotate(
            candidate_count=Count('candidates', distinct=True),
            placement_count=Count('placements', distinct=True)
        )