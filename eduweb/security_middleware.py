"""
eduweb/security_middleware.py
═══════════════════════════════════════════════════════════════════════════════
SessionSecurityMiddleware — Inactivity timeout with secure forced logout.

Design principles (from your requirements):
  • NO frontend ping/extend endpoints — all timing handled server-side
  • NO template changes required — middleware intercepts every request
  • Hard logout at timeout: flush session, clear profile flags, redirect
  • Graceful handling: AJAX gets 401 JSON, browser gets redirect + message
  • Single source of truth: settings.SESSION_INACTIVITY_TIMEOUT (minutes)

Model dependencies (from eduweb/models.py):
  • UserProfile.is_logged_in      → cleared on timeout
  • UserProfile.active_session_key → cleared on timeout
  • UserProfile.is_suspended      → checked each request (kill session)
"""
import json
import logging
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────────────────
INACTIVITY_TIMEOUT_MINUTES = getattr(settings, 'SESSION_INACTIVITY_TIMEOUT', 15)
INACTIVITY_TIMEOUT_SECONDS = INACTIVITY_TIMEOUT_MINUTES * 60

# Paths that bypass the inactivity check entirely (auth flow + static assets)
# NOTE: These are PATH EQUALITY checks, not startswith, to avoid over-matching
_PASSTHROUGH_EXACT = {
    '/auth/',
    '/logout/',
    '/verify-email/',
    '/resend-verification/',
    '/forgot-password/',
    '/reset-password/',
    '/otp-verify/',
}

_PASSTHROUGH_PREFIX = {
    '/static/',
    '/media/',
    '/admin/',
    '__debug__/',
}


def _is_passthrough(path: str) -> bool:
    """True if this path should not trigger inactivity logic."""
    if path in _PASSTHROUGH_EXACT:
        return True
    return any(path.startswith(p) for p in _PASSTHROUGH_PREFIX)


class SessionSecurityMiddleware(MiddlewareMixin):
    """
    Enforces a hard inactivity timeout on all authenticated requests.

    Flow per request:
      1. Passthrough? → skip entirely
      2. Anonymous?   → skip entirely
      3. Suspended?   → kill session immediately (admin action)
      4. Expired?     → kill session, return redirect/401
      5. Alive?       → bump last_activity, allow request
    """

    # ── Entry point ──────────────────────────────────────────────────────────

    def process_request(self, request):
        if not request.user.is_authenticated:
            return None

        path = request.path_info

        if _is_passthrough(path):
            return None

        now = timezone.now()

        # ── 1. Suspension guard (checked before timeout, admin can kill live sessions)
        profile = getattr(request.user, 'profile', None)
        if profile and getattr(profile, 'is_suspended', False):
            return self._kill_suspended(request, profile)

        # ── 2. Read & validate last_activity
        last_activity = request.session.get('last_activity')

        if last_activity is None:
            # First authenticated request this session — seed the timer
            request.session['last_activity'] = now.isoformat()
            request.session.modified = True
            return None

        # ── 3. Parse & check expiry
        idle_seconds = self._calculate_idle(now, last_activity)

        if idle_seconds is None:
            # Corrupted timestamp — treat as expired for safety
            logger.warning(
                'Corrupted last_activity for user=%s, forcing logout',
                request.user.username,
                extra={'user_id': request.user.pk, 'path': path}
            )
            return self._kill_expired(request, idle_seconds=0, corrupted=True)

        if idle_seconds > INACTIVITY_TIMEOUT_SECONDS:
            return self._kill_expired(request, idle_seconds)

        # ── 4. Session alive — refresh timestamp
        request.session['last_activity'] = now.isoformat()
        request.session.modified = True
        return None

    # ── Internal: expiry calculation ─────────────────────────────────────────

    def _calculate_idle(self, now, last_activity_raw):
        """
        Parse last_activity and return idle seconds, or None if unparseable.
        Handles both ISO strings and legacy float timestamps.
        """
        if isinstance(last_activity_raw, (int, float)):
            # Legacy float timestamp (epoch seconds)
            return (now.timestamp() - float(last_activity_raw))

        if isinstance(last_activity_raw, str):
            try:
                # Django session serializer may add quotes
                cleaned = last_activity_raw.strip('"\'')
                parsed = timezone.datetime.fromisoformat(cleaned)
                # Ensure aware
                if timezone.is_naive(parsed):
                    parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
                return (now - parsed).total_seconds()
            except (ValueError, TypeError, OverflowError):
                return None

        return None

    # ── Internal: kill expired session ───────────────────────────────────────

    def _kill_expired(self, request, idle_seconds, corrupted=False):
        """Force-logout due to inactivity timeout."""
        user = request.user
        username = getattr(user, 'username', 'unknown')
        reason = (
            f'Session expired after {int(idle_seconds // 60)} min {int(idle_seconds % 60)} sec idle. '
            f'Timeout limit: {INACTIVITY_TIMEOUT_MINUTES} min.'
        ) if not corrupted else 'Corrupted session timestamp — forced logout for security.'

        logger.info(
            'Inactivity timeout: user=%s, idle=%.0fs, path=%s',
            username, idle_seconds if not corrupted else 0, request.path_info,
            extra={'user_id': getattr(user, 'pk', None), 'event': 'session_timeout'}
        )

        # Clear UserProfile session tracking (matches your models.py)
        self._clear_profile_session(user)

        # Capture target URL before logout flushes session
        next_url = request.get_full_path()

        # Perform logout (flushes session, rotates key)
        logout(request)

        # Build response based on request type
        if self._is_ajax(request):
            return JsonResponse(
                {
                    'success': False,
                    'error': 'Session expired due to inactivity. Please log in again.',
                    'redirect_url': settings.LOGIN_URL,
                },
                status=401,
            )

        # Browser request — flash message and redirect
        messages.warning(
            request,
            f'Your session expired after {INACTIVITY_TIMEOUT_MINUTES} minutes of inactivity. '
            'Please sign in again to continue.'
        )
        return redirect(f'{settings.LOGIN_URL}?next={next_url}')

    # ── Internal: kill suspended session ───────────────────────────────────

    def _kill_suspended(self, request, profile):
        """Force-logout because admin suspended the account mid-session."""
        user = request.user
        reason = getattr(profile, 'suspension_reason', None) or 'Contact support for details.'

        logger.warning(
            'Suspended session killed: user=%s, path=%s',
            user.username, request.path_info,
            extra={'user_id': user.pk, 'event': 'session_suspended_kill'}
        )

        self._clear_profile_session(user)
        logout(request)

        if self._is_ajax(request):
            return JsonResponse(
                {
                    'success': False,
                    'error': f'Your account has been suspended. {reason}',
                    'redirect_url': settings.LOGIN_URL,
                },
                status=403,
            )

        messages.error(request, f'Your account has been suspended. {reason}')
        return redirect(settings.LOGIN_URL)

    # ── Internal: profile cleanup ──────────────────────────────────────────

    def _clear_profile_session(self, user):
        """
        Mirror the single-device session tracking from your models.py:
        UserProfile.is_logged_in and UserProfile.active_session_key
        """
        try:
            profile = user.profile
            if profile.is_logged_in or profile.active_session_key:
                profile.is_logged_in = False
                profile.active_session_key = ''
                profile.save(update_fields=['is_logged_in', 'active_session_key'])
                logger.debug('Cleared profile session flags for user=%s', user.username)
        except Exception:
            # Profile missing or DB error — non-fatal, session already killed
            logger.exception('Failed to clear profile session flags for user=%s', user.username)

    # ── Internal: AJAX detection ───────────────────────────────────────────

    @staticmethod
    def _is_ajax(request):
        """Reliable AJAX detection (works with modern fetch/XHR)."""
        return (
            request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            or request.headers.get('Accept') == 'application/json'
            or request.content_type == 'application/json'
        )