# from functools import wraps
# from django.contrib.auth import logout
# from django.middleware.csrf import rotate_token

# def check_for_auth(view_func):
#     """
#     If a user is already authenticated:
#     - Destroys their session
#     - Logs them out
#     - Rotates CSRF token
#     Then allows access to the page.
#     """

#     @wraps(view_func)
#     def _wrapped_view(request, *args, **kwargs):

#         if request.user.is_authenticated:
#             # Destroy Django auth session
#             logout(request)

#             # Delete all session data
#             request.session.flush()

#             # Rotate CSRF token to prevent session fixation
#             rotate_token(request)

#         return view_func(request, *args, **kwargs)

#     return _wrapped_view

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def check_for_auth(view_func):
    """
    Prevents admin/staff users from accessing public pages.
    If a staff user tries to access a public page, redirect them to admin dashboard.
    Regular users can access freely.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # If user is logged in AND is staff/admin
        if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
            messages.info(request, 'Admin users should use the admin dashboard.')
            return redirect('management:dashboard')
        
        # Regular users and anonymous users can proceed
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view