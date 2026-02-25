from django.contrib import admin
from django.db import models  # Add this import
from django.contrib.auth.models import User
from django.utils.html import format_html

# If you want to track imports, create a simple model
class ImportLog(models.Model):
    """Log of file imports"""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    filename = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=[
        ('success', 'Success'),
        ('partial', 'Partial Success'),
        ('failed', 'Failed'),
    ])
    rows_processed = models.IntegerField(default=0)
    rows_imported = models.IntegerField(default=0)
    rows_failed = models.IntegerField(default=0)
    error_log = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.filename} - {self.created_at}"

@admin.register(ImportLog)
class ImportLogAdmin(admin.ModelAdmin):
    """Admin for ImportLog"""
    list_display = ('filename', 'user', 'status_badge', 'rows_processed', 
                   'rows_imported', 'rows_failed', 'created_at')
    list_filter = ('status', 'created_at', 'user')
    search_fields = ('filename', 'user__username', 'error_log')
    readonly_fields = ('user', 'filename', 'status', 'rows_processed', 
                      'rows_imported', 'rows_failed', 'error_log', 'created_at')
    date_hierarchy = 'created_at'
    
    def status_badge(self, obj):
        """Show status with color"""
        colors = {
            'success': 'green',
            'partial': 'orange',
            'failed': 'red'
        }
        color = colors.get(obj.status, 'gray')
        return format_html('<span style="color: {}; font-weight: bold;">●</span> {}',
                          color, obj.get_status_display())
    status_badge.short_description = 'Status'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False