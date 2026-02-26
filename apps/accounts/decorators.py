from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps
from .models import log_activity

def role_required(allowed_roles=[]):
    """Decorator to check if user has allowed role"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "Please log in to access this page.")
                return redirect('login')
            
            # Check if user has profile
            if not hasattr(request.user, 'profile'):
                from .models import UserProfile
                UserProfile.objects.create(user=request.user)
            
            user_role = request.user.profile.role
            
            if user_role in allowed_roles or user_role == 'admin':
                return view_func(request, *args, **kwargs)
            else:
                # More descriptive error message
                role_display = dict(request.user.profile.USER_ROLES).get(user_role, user_role)
                allowed_display = [dict(request.user.profile.USER_ROLES).get(r, r) for r in allowed_roles]
                
                messages.error(
                    request, 
                    f"Access Denied: Your role '{role_display}' does not have permission to access this page. "
                    f"Required roles: {', '.join(allowed_display)}"
                )
                # Log unauthorized access attempt
                log_activity(
                    user=request.user,
                    action='VIEW',
                    model_type='Page',
                    details=f"Unauthorized access attempt to {request.path} (role: {user_role})",
                    request=request
                )
                return redirect('dashboard')
        return wrapper
    return decorator

def permission_required(permission):
    """Decorator to check if user has specific permission"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "Please log in to access this page.")
                return redirect('login')
            
            # Check if user has profile
            if not hasattr(request.user, 'profile'):
                from .models import UserProfile
                UserProfile.objects.create(user=request.user)
            
            if request.user.profile.has_permission(permission):
                return view_func(request, *args, **kwargs)
            else:
                # More descriptive error message
                permission_display = permission.replace('_', ' ').title()
                messages.error(
                    request, 
                    f"Access Denied: You don't have the required permission: '{permission_display}'. "
                    f"Please contact your administrator if you need access."
                )
                # Log unauthorized access attempt
                log_activity(
                    user=request.user,
                    action='VIEW',
                    model_type='Page',
                    details=f"Unauthorized access attempt to {request.path} (needed: {permission})",
                    request=request
                )
                return redirect('dashboard')
        return wrapper
    return decorator

def admin_required(view_func):
    """Decorator for admin only access"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to access this page.")
            return redirect('login')
        
        if request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.role == 'admin'):
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "Admin access required. This page is restricted to administrators only.")
            log_activity(
                user=request.user,
                action='VIEW',
                model_type='Page',
                details=f"Admin access attempt to {request.path}",
                request=request
            )
            return redirect('dashboard')
    return wrapper

def staff_or_higher_required(view_func):
    """Decorator for staff and above (staff, manager, admin)"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to access this page.")
            return redirect('login')
        
        if hasattr(request.user, 'profile') and request.user.profile.role in ['admin', 'manager', 'staff']:
            return view_func(request, *args, **kwargs)
        else:
            role_display = dict(request.user.profile.USER_ROLES).get(request.user.profile.role, request.user.profile.role)
            messages.error(
                request, 
                f"Access Denied: Your role '{role_display}' does not have staff privileges. "
                f"This page requires staff, manager, or admin access."
            )
            return redirect('dashboard')
    return wrapper

def manager_or_admin_required(view_func):
    """Decorator for manager and admin only"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to access this page.")
            return redirect('login')
        
        if hasattr(request.user, 'profile') and request.user.profile.role in ['admin', 'manager']:
            return view_func(request, *args, **kwargs)
        else:
            role_display = dict(request.user.profile.USER_ROLES).get(request.user.profile.role, request.user.profile.role)
            messages.error(
                request, 
                f"Access Denied: Your role '{role_display}' does not have manager privileges. "
                f"This page requires manager or admin access."
            )
            return redirect('dashboard')
    return wrapper

def finance_required(view_func):
    """Decorator for finance and above (finance, manager, admin)"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to access this page.")
            return redirect('login')
        
        if hasattr(request.user, 'profile') and request.user.profile.role in ['admin', 'manager', 'finance']:
            return view_func(request, *args, **kwargs)
        else:
            role_display = dict(request.user.profile.USER_ROLES).get(request.user.profile.role, request.user.profile.role)
            messages.error(
                request, 
                f"Access Denied: Your role '{role_display}' does not have finance privileges. "
                f"This page requires finance, manager, or admin access."
            )
            return redirect('dashboard')
    return wrapper

def agent_or_higher_required(view_func):
    """Decorator for agent and above (agent, staff, manager, admin)"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to access this page.")
            return redirect('login')
        
        if hasattr(request.user, 'profile') and request.user.profile.role in ['admin', 'manager', 'staff', 'agent']:
            return view_func(request, *args, **kwargs)
        else:
            role_display = dict(request.user.profile.USER_ROLES).get(request.user.profile.role, request.user.profile.role)
            messages.error(
                request, 
                f"Access Denied: Your role '{role_display}' cannot access agent resources."
            )
            return redirect('dashboard')
    return wrapper