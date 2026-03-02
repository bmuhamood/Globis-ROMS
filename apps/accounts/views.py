from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import timedelta, datetime
from .models import UserProfile, ActivityLog, log_activity
from .decorators import admin_required, permission_required, role_required
from apps.agents.models import Agent
from apps.candidates.models import Candidate
from apps.clients.models import Client
from apps.documents.models import DocumentStatus
from apps.visa_process.models import VisaProcess
from apps.candidate_payments.models import CandidatePayment
from apps.placements.models import Placement
from apps.finance.models import Income, Expense
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.debug import sensitive_post_parameters
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

# ==================== AUTHENTICATION VIEWS ====================

@sensitive_post_parameters()
@ensure_csrf_cookie
@never_cache
def login_view(request):
    """Enhanced login view with CSRF token handling"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Log login activity
            log_activity(
                user=user,
                action='LOGIN',
                model_type='User',
                details=f"User logged in",
                request=request
            )
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    # Ensure CSRF token is set even for GET requests
    response = render(request, 'accounts/login.html')
    return response

def logout_view(request):
    if request.user.is_authenticated:
        log_activity(
            user=request.user,
            action='LOGOUT',
            model_type='User',
            details=f"User logged out",
            request=request
        )
    logout(request)
    return redirect('login')

# ==================== DASHBOARD VIEW ====================

@login_required
def dashboard(request):
    # Statistics
    total_candidates = Candidate.objects.count()
    total_clients = Client.objects.count()
    total_agents = Agent.objects.count()
    
    # Candidates per client
    candidates_per_client = Client.objects.annotate(
        candidate_count=Count('candidates')
    ).order_by('-candidate_count')[:5]
    
    # Missing documents
    missing_docs = DocumentStatus.objects.filter(
        medical_report=False
    ) | DocumentStatus.objects.filter(
        interpol=False
    ) | DocumentStatus.objects.filter(
        passport_copy=False
    )
    missing_docs_count = missing_docs.count()
    
    # Visa status
    visa_in_progress = VisaProcess.objects.filter(
        visa_applied=True, visa_stamped=False
    ).count()
    
    ready_to_travel = VisaProcess.objects.filter(
        visa_stamped=True, ticket_issued=True
    ).count()
    
    # Financial calculations (if user has permission)
    if request.user.profile.has_permission('view_finance'):
        total_candidate_payments = CandidatePayment.objects.aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        total_client_payments = Income.objects.aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        total_expenses = Expense.objects.aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        cash_in_hand = total_candidate_payments + total_client_payments - total_expenses
    else:
        total_candidate_payments = 0
        total_client_payments = 0
        total_expenses = 0
        cash_in_hand = 0
    
    # Recent data
    recent_candidates = Candidate.objects.all().select_related('agent', 'client')[:5]
    recent_placements = Placement.objects.select_related('candidate', 'client').all()[:5]
    
    # Monthly data for chart
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    
    monthly_income = Income.objects.filter(date__gte=last_30_days).aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    monthly_expenses = Expense.objects.filter(date__gte=last_30_days).aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # Last 6 months data for chart
    months = []
    income_data = []
    expense_data = []
    
    for i in range(5, -1, -1):
        month = today - timedelta(days=30*i)
        month_start = datetime(month.year, month.month, 1).date()
        if month.month == 12:
            month_end = datetime(month.year + 1, 1, 1).date() - timedelta(days=1)
        else:
            month_end = datetime(month.year, month.month + 1, 1).date() - timedelta(days=1)
        
        month_income = Income.objects.filter(date__range=[month_start, month_end]).aggregate(total=Sum('amount'))['total'] or 0
        month_expense = Expense.objects.filter(date__range=[month_start, month_end]).aggregate(total=Sum('amount'))['total'] or 0
        
        months.append(month.strftime('%b'))
        income_data.append(float(month_income))
        expense_data.append(float(month_expense))
    
    # Log dashboard view
    log_activity(
        user=request.user,
        action='VIEW',
        model_type='Page',
        details="Viewed dashboard",
        request=request
    )
    
    context = {
        'total_candidates': total_candidates,
        'total_clients': total_clients,
        'total_agents': total_agents,
        'candidates_per_client': candidates_per_client,
        'missing_docs_count': missing_docs_count,
        'visa_in_progress': visa_in_progress,
        'ready_to_travel': ready_to_travel,
        'total_candidate_payments': total_candidate_payments,
        'total_client_payments': total_client_payments,
        'total_expenses': total_expenses,
        'cash_in_hand': cash_in_hand,
        'recent_candidates': recent_candidates,
        'recent_placements': recent_placements,
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'months': months,
        'income_data': income_data,
        'expense_data': expense_data,
    }
    
    return render(request, 'dashboard.html', context)

# ==================== USER MANAGEMENT VIEWS (ADMIN ONLY) ====================

@login_required
@admin_required
def user_list(request):
    """List all users - admin only"""
    users = User.objects.select_related('profile').all()
    
    # Filter by role
    role = request.GET.get('role')
    if role:
        users = users.filter(profile__role=role)
    
    # Search
    search = request.GET.get('search')
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    log_activity(
        user=request.user,
        action='VIEW',
        model_type='User',
        details="Viewed user list",
        request=request
    )
    
    context = {
        'page_obj': page_obj,
        'roles': UserProfile.USER_ROLES,
    }
    return render(request, 'accounts/user_list.html', context)

@login_required
@admin_required
def user_create(request):
    """Create a new user - admin only"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        role = request.POST.get('role')
        
        # Validation
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('user_create')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('user_create')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect('user_create')
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=request.POST.get('first_name', ''),
            last_name=request.POST.get('last_name', '')
        )
        
        # Update profile
        profile = user.profile
        profile.role = role
        profile.phone = request.POST.get('phone', '')
        
        # Set permissions based on role or custom settings
        if role == 'staff':
            profile.can_add_candidates = request.POST.get('can_add_candidates') == 'on'
            profile.can_edit_candidates = request.POST.get('can_edit_candidates') == 'on'
            profile.can_add_agents = request.POST.get('can_add_agents') == 'on'
            profile.can_edit_agents = request.POST.get('can_edit_agents') == 'on'
            profile.can_add_clients = request.POST.get('can_add_clients') == 'on'
            profile.can_edit_clients = request.POST.get('can_edit_clients') == 'on'
            profile.can_export = request.POST.get('can_export') == 'on'
            profile.can_view_reports = request.POST.get('can_view_reports') == 'on'
        
        # If role is agent, link to agent
        if role == 'agent' and request.POST.get('agent'):
            profile.agent_id = request.POST.get('agent')
        
        profile.save()
        
        log_activity(
            user=request.user,
            action='CREATE',
            model_type='User',
            object_id=user.id,
            object_repr=user.username,
            details=f"Created user: {user.username} with role {role}",
            request=request
        )
        
        messages.success(request, f'User {username} created successfully.')
        return redirect('user_list')
    
    agents = Agent.objects.all()
    context = {
        'agents': agents,
        'roles': UserProfile.USER_ROLES,
    }
    return render(request, 'accounts/user_form.html', context)

@login_required
@admin_required
def user_edit(request, pk):
    """Edit a user - admin only"""
    user_obj = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        user_obj.email = request.POST.get('email')
        user_obj.first_name = request.POST.get('first_name', '')
        user_obj.last_name = request.POST.get('last_name', '')
        user_obj.save()
        
        # Update profile
        profile = user_obj.profile
        profile.role = request.POST.get('role')
        profile.phone = request.POST.get('phone', '')
        
        # Set permissions for staff
        if profile.role == 'staff':
            profile.can_add_candidates = request.POST.get('can_add_candidates') == 'on'
            profile.can_edit_candidates = request.POST.get('can_edit_candidates') == 'on'
            profile.can_add_agents = request.POST.get('can_add_agents') == 'on'
            profile.can_edit_agents = request.POST.get('can_edit_agents') == 'on'
            profile.can_add_clients = request.POST.get('can_add_clients') == 'on'
            profile.can_edit_clients = request.POST.get('can_edit_clients') == 'on'
            profile.can_export = request.POST.get('can_export') == 'on'
            profile.can_view_reports = request.POST.get('can_view_reports') == 'on'
        
        # If role is agent, link to agent
        if request.POST.get('role') == 'agent' and request.POST.get('agent'):
            profile.agent_id = request.POST.get('agent')
        
        # Password change if provided
        new_password = request.POST.get('new_password')
        if new_password:
            user_obj.set_password(new_password)
            user_obj.save()
        
        profile.save()
        
        log_activity(
            user=request.user,
            action='UPDATE',
            model_type='User',
            object_id=user_obj.id,
            object_repr=user_obj.username,
            details=f"Updated user: {user_obj.username}",
            request=request
        )
        
        messages.success(request, f'User {user_obj.username} updated successfully.')
        return redirect('user_list')
    
    agents = Agent.objects.all()
    context = {
        'user_obj': user_obj,
        'profile': user_obj.profile,
        'agents': agents,
        'roles': UserProfile.USER_ROLES,
    }
    return render(request, 'accounts/user_form.html', context)

@login_required
@admin_required
def user_delete(request, pk):
    """Delete a user - admin only"""
    user_obj = get_object_or_404(User, pk=pk)
    
    if user_obj == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('user_list')
    
    username = user_obj.username
    
    log_activity(
        user=request.user,
        action='DELETE',
        model_type='User',
        object_repr=username,
        details=f"Deleted user: {username}",
        request=request
    )
    
    user_obj.delete()
    messages.success(request, f'User {username} deleted successfully.')
    return redirect('user_list')

# ==================== ACTIVITY LOGS VIEW (ADMIN ONLY) ====================

@login_required
@admin_required
def activity_logs(request):
    """View activity logs - admin only"""
    logs = ActivityLog.objects.select_related('user').all()
    
    # Filter by action
    action = request.GET.get('action')
    if action:
        logs = logs.filter(action=action)
    
    # Filter by model
    model = request.GET.get('model')
    if model:
        logs = logs.filter(model_type=model)
    
    # Filter by user
    user_id = request.GET.get('user')
    if user_id:
        logs = logs.filter(user_id=user_id)
    
    # Date range
    date_from = request.GET.get('from')
    date_to = request.GET.get('to')
    if date_from:
        logs = logs.filter(created_at__date__gte=date_from)
    if date_to:
        logs = logs.filter(created_at__date__lte=date_to)
    
    # Search in details
    search = request.GET.get('search')
    if search:
        logs = logs.filter(
            Q(details__icontains=search) |
            Q(object_repr__icontains=search) |
            Q(username__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get unique users for filter dropdown
    users = User.objects.filter(activities__isnull=False).distinct()
    
    log_activity(
        user=request.user,
        action='VIEW',
        model_type='Report',
        details="Viewed activity logs",
        request=request
    )
    
    context = {
        'page_obj': page_obj,
        'actions': ActivityLog.ACTION_TYPES,
        'models': ActivityLog.MODEL_TYPES,
        'users': users,
    }
    return render(request, 'accounts/activity_logs.html', context)

# ==================== PROFILE VIEW ====================

def custom_403_view(request, exception=None):
    """Custom 403 forbidden page"""
    return render(request, '403.html', status=403)

def custom_404_view(request, exception=None):
    """Custom 404 not found page"""
    return render(request, '404.html', status=404)

def custom_500_view(request):
    """Custom 500 server error page"""
    return render(request, '500.html', status=500)

@login_required
def permission_denied(request):
    """View for when user lacks permission"""
    return render(request, '403.html', {
        'message': "You don't have permission to access this page."
    })

@login_required
def profile(request):
    """View and edit user profile"""
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()
        
        profile = user.profile
        profile.phone = request.POST.get('phone', '')
        profile.save()
        
        # Change password if provided
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if current_password and new_password and confirm_password:
            if user.check_password(current_password):
                if new_password == confirm_password:
                    user.set_password(new_password)
                    user.save()
                    messages.success(request, 'Password changed successfully. Please login again.')
                    return redirect('login')
                else:
                    messages.error(request, 'New passwords do not match.')
            else:
                messages.error(request, 'Current password is incorrect.')
        
        log_activity(
            user=request.user,
            action='UPDATE',
            model_type='User',
            object_id=user.id,
            object_repr=user.username,
            details="Updated own profile",
            request=request
        )
        
        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')
    
    return render(request, 'accounts/profile.html', {'user_obj': request.user})