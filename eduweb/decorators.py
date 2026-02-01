from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from .models import CourseApplication


def check_for_auth(view_func):
    """
    Prevents admin/staff/instructor/student users from accessing public pages.
    Redirects each role to their respective destination.
    Anonymous users can proceed to public pages.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return view_func(request, *args, **kwargs)

        role = request.user.profile.role

        if role == 'administrator' or request.user.is_superuser:
            messages.info(request, 'Admin users should use the admin dashboard.')
            return redirect('management:dashboard')

        elif role == 'instructor':
            messages.info(request, 'Instructor users should use the instructor dashboard.')
            return redirect('instructor:dashboard')

        elif role == 'student':
            # Student: redirect based on application status
            has_application = CourseApplication.objects.filter(user=request.user).exists()

            if has_application:
                messages.info(request, 'You have an active application. Check your status below.')
                return redirect('eduweb:application_status')
            else:
                messages.info(request, 'Complete your application to get started.')
                return redirect('eduweb:apply')

        # Any other unrecognised role — let them through to public pages
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def applicant_required(view_func):
    """
    For pages that require student role authentication (apply, application_status).
    - Unauthenticated: Redirect to login
    - Admin/Instructor: Redirect to their dashboard
    - Student: Allow access
    - Any other role: Denied
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to access this page.')
            return redirect('eduweb:auth_page')

        role = request.user.profile.role

        if role == 'administrator' or request.user.is_superuser:
            messages.info(request, 'Admin users should use the admin dashboard.')
            return redirect('management:dashboard')

        elif role == 'instructor':
            messages.info(request, 'Instructor users should use the instructor dashboard.')
            return redirect('instructor:dashboard')

        elif role == 'student':
            return view_func(request, *args, **kwargs)

        # Fallback — unrecognised role
        messages.warning(request, 'Access denied.')
        return redirect('eduweb:auth_page')

    return _wrapped_view


def smart_redirect_applicant(view_func):
    """
    Smart redirect for student applicants on specific pages.
    - If on 'apply' page and has application -> redirect to status
    - If on 'application_status' and no application -> redirect to apply
    - Only students should access these pages
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to access this page.')
            return redirect('eduweb:auth_page')

        role = request.user.profile.role

        if role == 'administrator' or request.user.is_superuser:
            messages.info(request, 'Admin users should use the admin dashboard.')
            return redirect('management:dashboard')

        elif role == 'instructor':
            messages.info(request, 'Instructor users should use the instructor dashboard.')
            return redirect('instructor:dashboard')

        elif role == 'student':
            has_application = CourseApplication.objects.filter(user=request.user).exists()
            current_view = request.resolver_match.url_name

            if current_view == 'apply' and has_application:
                messages.info(request, 'You already have an application. View your status below.')
                return redirect('eduweb:application_status')

            if current_view == 'application_status' and not has_application:
                messages.info(request, 'Please submit your application first.')
                return redirect('eduweb:apply')

            return view_func(request, *args, **kwargs)

        # Fallback — unrecognised role
        messages.warning(request, 'Access denied.')
        return redirect('eduweb:auth_page')

    return _wrapped_view