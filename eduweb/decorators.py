from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from .models import CourseApplication

def check_for_auth(view_func):
    """
    Prevents admin/staff users from accessing public pages.
    Redirects admin/staff to admin dashboard.
    For regular authenticated users, smart redirects based on application status.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # If user is logged in AND is staff/admin - redirect to admin dashboard
        if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
            messages.info(request, 'Admin users should use the admin dashboard.')
            return redirect('management:dashboard')
        
        # If regular user is authenticated, redirect based on application status
        if request.user.is_authenticated and not (request.user.is_staff or request.user.is_superuser):
            # Check if user has an application
            has_application = CourseApplication.objects.filter(user=request.user).exists()
            
            if has_application:
                # Redirect to application status page
                messages.info(request, 'You have an active application. Check your status below.')
                return redirect('eduweb:application_status')
            else:
                # Redirect to apply page
                messages.info(request, 'Complete your application to get started.')
                return redirect('eduweb:apply')
        
        # Anonymous users can proceed to public pages
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view


def applicant_required(view_func):
    """
    For pages that require authentication (apply, application_status, etc.).
    - Staff/Admin: Redirect to admin dashboard
    - Unauthenticated: Redirect to login
    - Regular authenticated users: Allow access
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # If not authenticated, redirect to login
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to access this page.')
            return redirect('eduweb:auth_page')
        
        # If staff/admin, redirect to admin dashboard
        if request.user.is_staff or request.user.is_superuser:
            messages.info(request, 'Admin users should use the admin dashboard.')
            return redirect('management:dashboard')
        
        # Regular authenticated user - allow access
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view


def smart_redirect_applicant(view_func):
    """
    Smart redirect for authenticated applicants on specific pages.
    - If on 'apply' page and already has application -> redirect to status
    - If on 'application_status' and no application -> redirect to apply
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # If not authenticated, redirect to login
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to access this page.')
            return redirect('eduweb:auth_page')
        
        # If staff/admin, redirect to admin dashboard
        if request.user.is_staff or request.user.is_superuser:
            messages.info(request, 'Admin users should use the admin dashboard.')
            return redirect('management:dashboard')
        
        # Check application status
        has_application = CourseApplication.objects.filter(user=request.user).exists()
        current_view = request.resolver_match.url_name
        
        # Smart redirects based on current page and application status
        if current_view == 'apply' and has_application:
            messages.info(request, 'You already have an application. View your status below.')
            return redirect('eduweb:application_status')
        
        if current_view == 'application_status' and not has_application:
            messages.info(request, 'Please submit your application first.')
            return redirect('eduweb:apply')
        
        # Allow access
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view