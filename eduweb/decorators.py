from functools import wraps
from django.contrib.auth import logout
from django.middleware.csrf import rotate_token

def check_for_auth(view_func):
    """
    If a user is already authenticated:
    - Destroys their session
    - Logs them out
    - Rotates CSRF token
    Then allows access to the page.
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):

        if request.user.is_authenticated:
            # Destroy Django auth session
            logout(request)

            # Delete all session data
            request.session.flush()

            # Rotate CSRF token to prevent session fixation
            rotate_token(request)

        return view_func(request, *args, **kwargs)

    return _wrapped_view
