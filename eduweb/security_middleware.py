"""
eduweb/security_middleware.py
═══════════════════════════════════════════════════════════════════════════════
SessionSecurityMiddleware  +  PermissionService (internal staff only)

Permission loading runs once per request, after session validation.
Students and instructors are skipped — permissions only apply to:
  admin | content_manager | support | qa | finance

Superusers get all permissions on all modules unconditionally.

Template usage:
  {{ permissions.dashboard.can_view }}
  {{ permissions.finance.can_export }}
"""
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

# Roles that get permissions loaded — students excluded
STAFF_ROLES = {'admin', 'content_manager', 'support', 'qa', 'finance', 'instructor'}

_PASSTHROUGH_EXACT = {
    '/auth/', '/logout/', '/verify-email/', '/resend-verification/',
    '/forgot-password/', '/reset-password/', '/otp-verify/',
}
_PASSTHROUGH_PREFIX = {'/static/', '/media/', '/admin/', '__debug__/'}


def _is_passthrough(path: str) -> bool:
    if path in _PASSTHROUGH_EXACT:
        return True
    return any(path.startswith(p) for p in _PASSTHROUGH_PREFIX)


# ── Permission Service ─────────────────────────────────────────────────────────

def _load_permissions(user) -> dict:
    """
    Build the permissions dict for internal staff users.
    Returns {} for students, instructors, and unauthenticated users.
    Superusers get full access across all modules.
    """
    if not user.is_authenticated:
        return {}

    profile = getattr(user, 'profile', None)
    role = getattr(profile, 'role', None)

    # Skip non-staff roles entirely
    if not user.is_superuser and role not in STAFF_ROLES:
        return {}

    # Import here to avoid circular import at module load
    from eduweb.models import StaffPermissionsMatrix

    # Superuser bypass — full access on every known module
    if user.is_superuser:
        full = {
            'can_view': True, 'can_create': True, 'can_edit': True,
            'can_delete': True, 'can_approve': True, 'can_export': True,
        }
        modules = StaffPermissionsMatrix.objects.values_list('module', flat=True).distinct()
        return {m: full.copy() for m in modules}

    # Initialize all known modules with False permissions
    # so templates never fall through "or not permissions"
    from eduweb.models import StaffPermissionsMatrix as _SPM
    all_modules = [m[0] for m in _SPM.MODULE_CHOICES]
    permissions = {
        mod: {
            'can_view': False, 'can_create': False, 'can_edit': False,
            'can_delete': False, 'can_approve': False, 'can_export': False,
        }
        for mod in all_modules
    }

    # Step 1: role defaults
    for row in StaffPermissionsMatrix.objects.filter(role=role, user__isnull=True):
        permissions[row.module] = {
            'can_view':    row.can_view,
            'can_create':  row.can_create,
            'can_edit':    row.can_edit,
            'can_delete':  row.can_delete,
            'can_approve': row.can_approve,
            'can_export':  row.can_export,
        }

    # Step 2: user-level overrides
    for row in StaffPermissionsMatrix.objects.filter(user=user):
        permissions[row.module] = {
            'can_view':    row.can_view,
            'can_create':  row.can_create,
            'can_edit':    row.can_edit,
            'can_delete':  row.can_delete,
            'can_approve': row.can_approve,
            'can_export':  row.can_export,
        }

    return permissions


# ── Middleware ─────────────────────────────────────────────────────────────────

class SessionSecurityMiddleware(MiddlewareMixin):
    """
    1. Inactivity timeout — hard logout at INACTIVITY_TIMEOUT_MINUTES
    2. Suspension guard — admin can kill live sessions
    3. Permission loading — attaches request.permissions for staff users
    """

    def process_request(self, request):
        if not request.user.is_authenticated:
            return None

        path = request.path_info

        if _is_passthrough(path):
            return None

        now = timezone.now()

        # ── Suspension guard
        profile = getattr(request.user, 'profile', None)
        if profile and getattr(profile, 'is_suspended', False):
            return self._kill_suspended(request, profile)

        # ── Session timer
        last_activity = request.session.get('last_activity')

        if last_activity is None:
            request.session['last_activity'] = now.isoformat()
            request.session.modified = True
            request.permissions = _load_permissions(request.user)
            return None

        idle_seconds = self._calculate_idle(now, last_activity)

        if idle_seconds is None:
            logger.warning(
                'Corrupted last_activity for user=%s, forcing logout',
                request.user.username,
                extra={'user_id': request.user.pk, 'path': path}
            )
            return self._kill_expired(request, idle_seconds=0, corrupted=True)

        if idle_seconds > INACTIVITY_TIMEOUT_SECONDS:
            return self._kill_expired(request, idle_seconds)

        # ── Session alive — refresh + attach permissions
        request.session['last_activity'] = now.isoformat()
        request.session.modified = True
        request.permissions = _load_permissions(request.user)
        return None

    # ── Internal helpers (unchanged from original) ────────────────────────────

    def _calculate_idle(self, now, last_activity_raw):
        if isinstance(last_activity_raw, (int, float)):
            return now.timestamp() - float(last_activity_raw)
        if isinstance(last_activity_raw, str):
            try:
                cleaned = last_activity_raw.strip('"\'')
                parsed = timezone.datetime.fromisoformat(cleaned)
                if timezone.is_naive(parsed):
                    parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
                return (now - parsed).total_seconds()
            except (ValueError, TypeError, OverflowError):
                return None
        return None

    def _kill_expired(self, request, idle_seconds, corrupted=False):
        user = request.user
        username = getattr(user, 'username', 'unknown')
        logger.info(
            'Inactivity timeout: user=%s, idle=%.0fs, path=%s',
            username, idle_seconds if not corrupted else 0, request.path_info,
            extra={'user_id': getattr(user, 'pk', None), 'event': 'session_timeout'}
        )
        self._clear_profile_session(user)
        next_url = request.get_full_path()
        logout(request)
        if self._is_ajax(request):
            return JsonResponse(
                {'success': False, 'error': 'Session expired due to inactivity. Please log in again.',
                 'redirect_url': settings.LOGIN_URL},
                status=401,
            )
        messages.warning(
            request,
            f'Your session expired after {INACTIVITY_TIMEOUT_MINUTES} minutes of inactivity. '
            'Please sign in again to continue.'
        )
        return redirect(f'{settings.LOGIN_URL}?next={next_url}')

    def _kill_suspended(self, request, profile):
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
                {'success': False, 'error': f'Your account has been suspended. {reason}',
                 'redirect_url': settings.LOGIN_URL},
                status=403,
            )
        messages.error(request, f'Your account has been suspended. {reason}')
        return redirect(settings.LOGIN_URL)

    def _clear_profile_session(self, user):
        try:
            profile = user.profile
            if profile.is_logged_in or profile.active_session_key:
                profile.is_logged_in = False
                profile.active_session_key = ''
                profile.save(update_fields=['is_logged_in', 'active_session_key'])
        except Exception:
            logger.exception('Failed to clear profile session flags for user=%s', user.username)

    @staticmethod
    def _is_ajax(request):
        return (
            request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            or request.headers.get('Accept') == 'application/json'
            or request.content_type == 'application/json'
        )