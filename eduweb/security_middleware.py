"""
eduweb/security_middleware.py

SessionSecurityMiddleware — handles:
  1. Inactivity timeout  (SESSION_INACTIVITY_TIMEOUT minutes, default 15)
  2. Browser-close detection — session_key no longer exists → clear profile flag
  3. Single-device consistency — if session_key drifted, reset profile flag

Django already handles browser-close expiry via session.set_expiry(0) set at
login time. This middleware enforces the inactivity timeout on top of that.
"""

import logging
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import logout
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

INACTIVITY_TIMEOUT = getattr(settings, 'SESSION_INACTIVITY_TIMEOUT', 15)  # minutes

# Paths that must never trigger a redirect loop
_PASSTHROUGH_PATHS = {
    '/auth/',
    '/logout/',
    '/verify-email/',
    '/resend-verification/',
    '/forgot-password/',
    '/reset-password/',
    '/static/',
    '/media/',
}


def _is_passthrough(path):
    return any(path.startswith(p) for p in _PASSTHROUGH_PATHS)


class SessionSecurityMiddleware(MiddlewareMixin):
    """
    Enforces inactivity timeout and syncs the UserProfile login-status flag
    when a session disappears (browser close or natural expiry).
    """

    def process_request(self, request):
        if not request.user.is_authenticated:
            return None

        if _is_passthrough(request.path_info):
            return None

        now = timezone.now()

        # ── 1. Inactivity timeout ─────────────────────────────────────────────
        last_activity = request.session.get('last_activity')
        if last_activity:
            try:
                idle_seconds = (now - timezone.datetime.fromisoformat(last_activity)).total_seconds()
                if idle_seconds > INACTIVITY_TIMEOUT * 60:
                    self._terminate_session(request, reason='inactivity timeout')
                    return None
            except (ValueError, TypeError):
                pass  # malformed timestamp — let it through; will be reset below

        # Update last_activity on every passing request
        request.session['last_activity'] = now.isoformat()

        # ── 2. Sync profile flag if session disappeared ───────────────────────
        #    (covers browser-close: Django expires the session cookie,
        #     but the DB row may linger briefly until clearsessions runs)
        self._sync_profile_flag(request)

        return None

    # ── helpers ───────────────────────────────────────────────────────────────

    def _terminate_session(self, request, reason=''):
        """Flush this session, log out the user, and reset profile flag."""
        user = request.user
        logger.info('Session terminated for user=%s reason=%s', user.username, reason)

        try:
            if hasattr(user, 'profile'):
                user.profile.is_logged_in = False
                user.profile.active_session_key = ''
                user.profile.save(update_fields=['is_logged_in', 'active_session_key'])
        except Exception:
            logger.exception('Failed to reset profile flag for user=%s', user.username)

        request.session.flush()
        logout(request)

    def _sync_profile_flag(self, request):
        """
        If the profile says the user is logged in on a different session key
        than the current one, that old session has gone (browser close / expiry).
        Clear the stale flag so the user can log in again.
        """
        try:
            profile = request.user.profile
            if not profile.is_logged_in:
                return

            current_key = request.session.session_key

            if profile.active_session_key and profile.active_session_key != current_key:
                # The stored key is different — check if it still lives in the DB
                stale_still_alive = Session.objects.filter(
                    session_key=profile.active_session_key,
                    expire_date__gte=timezone.now(),
                ).exists()
                if not stale_still_alive:
                    profile.is_logged_in = True  # keep True — current session is valid
                    profile.active_session_key = current_key
                    profile.save(update_fields=['is_logged_in', 'active_session_key'])
        except Exception:
            logger.exception('_sync_profile_flag failed for user=%s', request.user.username)


'''class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' https://js.stripe.com; "
            "style-src 'self' https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://api.stripe.com;"
        )
        
        return response'''