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
                return redirect('login')
            
            # Check if user has profile
            if not hasattr(request.user, 'profile'):
                from .models import UserProfile
                UserProfile.objects.create(user=request.user)
            
            user_role = request.user.profile.role
            
            if user_role in allowed_roles or user_role == 'admin':
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, "You don't have permission to access this page.")
                # Log unauthorized access attempt
                log_activity(
                    user=request.user,
                    action='VIEW',
                    model_type='Page',
                    details=f"Unauthorized access attempt to {request.path}",
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
                return redirect('login')
            
            # Check if user has profile
            if not hasattr(request.user, 'profile'):
                from .models import UserProfile
                UserProfile.objects.create(user=request.user)
            
            if request.user.profile.has_permission(permission):
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, f"You don't have permission: {permission}")
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
            return redirect('login')
        
        if request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.role == 'admin'):
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "Admin access required.")
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
            return redirect('login')
        
        if hasattr(request.user, 'profile') and request.user.profile.role in ['admin', 'manager', 'staff']:
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "Staff access required.")
            return redirect('dashboard')
    return wrapper

def manager_or_admin_required(view_func):
    """Decorator for manager and admin only"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if hasattr(request.user, 'profile') and request.user.profile.role in ['admin', 'manager']:
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "Manager access required.")
            return redirect('dashboard')
    return wrapper