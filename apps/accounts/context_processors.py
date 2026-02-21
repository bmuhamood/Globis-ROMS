def user_permissions(request):
    """Add user permissions to template context"""
    if request.user.is_authenticated:
        if hasattr(request.user, 'profile'):
            profile = request.user.profile
            return {
                'user_role': profile.role,
                'can_edit': profile.can_edit_candidates if hasattr(profile, 'can_edit_candidates') else False,
                'can_delete': profile.can_delete_candidates if hasattr(profile, 'can_delete_candidates') else False,
                'can_import': profile.can_import if hasattr(profile, 'can_import') else False,
                'can_export': profile.can_export if hasattr(profile, 'can_export') else False,
                'can_view_finance': profile.can_view_finance if hasattr(profile, 'can_view_finance') else False,
                'is_admin': profile.role == 'admin',
                'is_manager': profile.role == 'manager',
                'is_staff': profile.role == 'staff',
                'is_finance': profile.role == 'finance',
                'is_agent': profile.role == 'agent',
                'is_viewer': profile.role == 'viewer',
            }
    return {}