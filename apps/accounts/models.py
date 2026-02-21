from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

class UserProfile(models.Model):
    USER_ROLES = [
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('staff', 'Staff'),
        ('finance', 'Finance Officer'),
        ('agent', 'Agent'),
        ('viewer', 'Viewer (Read Only)'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=USER_ROLES, default='viewer')
    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)
    
    # Staff specific permissions
    can_add_candidates = models.BooleanField(default=True)
    can_edit_candidates = models.BooleanField(default=True)
    can_delete_candidates = models.BooleanField(default=False)
    can_add_agents = models.BooleanField(default=True)
    can_edit_agents = models.BooleanField(default=True)
    can_delete_agents = models.BooleanField(default=False)
    can_add_clients = models.BooleanField(default=True)
    can_edit_clients = models.BooleanField(default=True)
    can_delete_clients = models.BooleanField(default=False)
    
    # Financial permissions
    can_view_finance = models.BooleanField(default=False)
    can_add_income = models.BooleanField(default=False)
    can_add_expense = models.BooleanField(default=False)
    can_delete_finance = models.BooleanField(default=False)
    
    # Report permissions
    can_view_reports = models.BooleanField(default=True)
    can_view_finance_reports = models.BooleanField(default=False)
    
    # Other permissions
    can_import = models.BooleanField(default=False)
    can_export = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    def has_permission(self, permission):
        """Check if user has specific permission"""
        if self.role == 'admin':
            return True
        
        # Staff role permissions
        if self.role == 'staff':
            staff_permissions = {
                # Candidate permissions
                'view_candidates': True,
                'add_candidate': self.can_add_candidates,
                'edit_candidate': self.can_edit_candidates,
                'delete_candidate': self.can_delete_candidates,
                
                # Agent permissions
                'view_agents': True,
                'add_agent': self.can_add_agents,
                'edit_agent': self.can_edit_agents,
                'delete_agent': self.can_delete_agents,
                
                # Client permissions
                'view_clients': True,
                'add_client': self.can_add_clients,
                'edit_client': self.can_edit_clients,
                'delete_client': self.can_delete_clients,
                
                # Document permissions
                'view_documents': True,
                'edit_documents': True,
                
                # Visa permissions
                'view_visa': True,
                'edit_visa': True,
                
                # Payment permissions
                'view_candidate_payments': True,
                'add_candidate_payment': True,
                'edit_candidate_payment': True,
                'delete_candidate_payment': False,
                
                # Placement permissions
                'view_placements': True,
                'add_placement': True,
                'edit_placement': True,
                'delete_placement': False,
                
                # Financial permissions - ALL FALSE
                'view_finance': False,
                'view_income': False,
                'view_expenses': False,
                'add_income': False,
                'add_expense': False,
                'delete_income': False,
                'delete_expense': False,
                'view_cash_in_hand': False,
                
                # Report permissions
                'view_reports': self.can_view_reports,
                'view_finance_reports': False,
                'view_candidate_reports': True,
                'view_client_reports': True,
                'view_agent_reports': True,
                'view_document_reports': True,
                'view_visa_reports': True,
                
                # Other
                'import_data': self.can_import,
                'export_data': self.can_export,
            }
            return staff_permissions.get(permission, False)
        
        # Other role permissions
        permission_map = {
            'view_candidates': ['manager', 'staff', 'finance', 'agent', 'viewer'],
            'add_candidate': ['manager', 'staff'],
            'edit_candidate': ['manager', 'staff'],
            'delete_candidate': ['manager'],
            
            'view_agents': ['manager', 'staff', 'finance'],
            'add_agent': ['manager', 'staff'],
            'edit_agent': ['manager', 'staff'],
            'delete_agent': ['manager'],
            
            'view_clients': ['manager', 'staff', 'finance'],
            'add_client': ['manager', 'staff'],
            'edit_client': ['manager', 'staff'],
            'delete_client': ['manager'],
            
            'view_finance': ['manager', 'finance'],
            'view_income': ['manager', 'finance'],
            'view_expenses': ['manager', 'finance'],
            'add_income': ['manager', 'finance'],
            'add_expense': ['manager', 'finance'],
            
            'view_reports': ['manager', 'staff', 'finance', 'agent'],
            'view_finance_reports': ['manager', 'finance'],
            
            'import_data': ['manager'],
            'export_data': ['manager', 'staff', 'finance'],
        }
        
        return self.role in permission_map.get(permission, [])


class ActivityLog(models.Model):
    """Model to track all user activities"""
    ACTION_TYPES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('VIEW', 'View'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('IMPORT', 'Import'),
        ('EXPORT', 'Export'),
        ('DOWNLOAD', 'Download'),
    ]
    
    MODEL_TYPES = [
        ('Candidate', 'Candidate'),
        ('Client', 'Client'),
        ('Agent', 'Agent'),
        ('Placement', 'Placement'),
        ('Payment', 'Payment'),
        ('Document', 'Document'),
        ('Visa', 'Visa Process'),
        ('User', 'User'),
        ('Finance', 'Finance'),
        ('Report', 'Report'),
        ('Page', 'Page'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='activities')
    username = models.CharField(max_length=150, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    model_type = models.CharField(max_length=50, choices=MODEL_TYPES)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    object_repr = models.CharField(max_length=200, blank=True)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['model_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.created_at.strftime('%Y-%m-%d %H:%M')} - {self.username} - {self.action} - {self.model_type}"
    
    def save(self, *args, **kwargs):
        if self.user and not self.username:
            self.username = self.user.username
        super().save(*args, **kwargs)


def log_activity(user, action, model_type, object_id=None, object_repr='', details='', request=None):
    """Helper function to log activities"""
    log = ActivityLog(
        user=user,
        username=user.username if user else 'System',
        action=action,
        model_type=model_type,
        object_id=object_id,
        object_repr=object_repr,
        details=details
    )
    
    if request:
        log.ip_address = get_client_ip(request)
        log.user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    log.save()
    return log


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip