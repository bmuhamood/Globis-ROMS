from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, ActivityLog
from django.utils.html import format_html

class UserProfileInline(admin.StackedInline):
    """Inline for UserProfile in User admin"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fieldsets = (
        ('Basic Information', {
            'fields': ('role', 'phone', 'department'),
            'classes': ('wide',),
        }),
        ('Staff Permissions', {
            'fields': (
                'can_add_candidates', 'can_edit_candidates', 'can_delete_candidates',
                'can_add_agents', 'can_edit_agents', 'can_delete_agents',
                'can_add_clients', 'can_edit_clients', 'can_delete_clients',
            ),
            'classes': ('wide', 'collapse'),
        }),
        ('Financial Permissions', {
            'fields': (
                'can_view_finance', 'can_add_income', 'can_add_expense',
                'can_delete_finance',
            ),
            'classes': ('wide', 'collapse'),
        }),
        ('Report Permissions', {
            'fields': ('can_view_reports', 'can_view_finance_reports'),
            'classes': ('wide', 'collapse'),
        }),
        ('Other Permissions', {
            'fields': ('can_import', 'can_export'),
            'classes': ('wide', 'collapse'),
        }),
    )

class CustomUserAdmin(BaseUserAdmin):
    """Custom User admin with profile inline"""
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'profile__role')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    
    def get_role(self, obj):
        """Get user role from profile"""
        try:
            return obj.profile.get_role_display()
        except:
            return '-'
    get_role.short_description = 'Role'
    get_role.admin_order_field = 'profile__role'

# Unregister default User admin and register custom
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin for UserProfile"""
    list_display = ('user', 'get_role', 'phone', 'department', 'created_at')
    list_filter = ('role', 'can_add_candidates', 'can_view_finance')
    search_fields = ('user__username', 'user__email', 'phone')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_role(self, obj):
        return obj.get_role_display()
    get_role.short_description = 'Role'
    get_role.admin_order_field = 'role'
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'role', 'phone', 'department'),
        }),
        ('Staff Permissions', {
            'fields': (
                ('can_add_candidates', 'can_edit_candidates', 'can_delete_candidates'),
                ('can_add_agents', 'can_edit_agents', 'can_delete_agents'),
                ('can_add_clients', 'can_edit_clients', 'can_delete_clients'),
            ),
            'classes': ('collapse',),
        }),
        ('Financial Permissions', {
            'fields': (
                'can_view_finance', 'can_add_income', 'can_add_expense',
                'can_delete_finance',
            ),
            'classes': ('collapse',),
        }),
        ('Report & Other Permissions', {
            'fields': (
                'can_view_reports', 'can_view_finance_reports',
                'can_import', 'can_export',
            ),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    """Admin for ActivityLog"""
    list_display = ('created_at', 'username', 'get_action_colored', 'model_type', 'object_repr', 'ip_address')
    list_filter = ('action', 'model_type', 'created_at')
    search_fields = ('username', 'object_repr', 'details', 'ip_address')
    readonly_fields = ('user', 'username', 'action', 'model_type', 'object_id', 
                      'object_repr', 'details', 'ip_address', 'user_agent', 'created_at')
    date_hierarchy = 'created_at'
    
    def get_action_colored(self, obj):
        """Return action with color coding"""
        colors = {
            'CREATE': 'green',
            'UPDATE': 'orange',
            'DELETE': 'red',
            'VIEW': 'blue',
            'LOGIN': 'teal',
            'LOGOUT': 'gray',
        }
        color = colors.get(obj.action, 'black')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', 
                          color, obj.get_action_display())
    get_action_colored.short_description = 'Action'
    
    def has_add_permission(self, request):
        """Prevent manual addition of logs"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent editing of logs"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Allow superusers to delete logs"""
        return request.user.is_superuser