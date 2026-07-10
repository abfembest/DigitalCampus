"""
support/permissions.py
Role-based access control helpers for the support app.
"""
from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib import messages


def is_support_staff(user):
    """Returns True if user can access support management."""
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    try:
        role = user.profile.role
        return role in ('admin', 'support')
    except Exception:
        return False


def is_support_admin(user):
    """Returns True if user has full support admin access."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    try:
        return user.profile.role == 'admin' or user.is_staff
    except Exception:
        return False


def support_required(view_func):
    """Decorator: require support staff role."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('eduweb:auth_page')
        if not is_support_staff(request.user):
            messages.error(request, "You do not have permission to access the Support Centre.")
            return redirect('eduweb:index')
        return view_func(request, *args, **kwargs)
    return _wrapped


def support_admin_required(view_func):
    """Decorator: require admin role or superuser."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('eduweb:auth_page')
        if not is_support_admin(request.user):
            messages.error(request, "Admin access required.")
            return redirect('support:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped


def get_client_ip(request):
    """Extract real client IP from request."""
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')
