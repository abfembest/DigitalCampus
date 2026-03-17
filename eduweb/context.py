"""
context.py — Global template context processors for the eduweb app.

All processors listed here must also be registered in settings.py:

    TEMPLATES = [{
        ...
        'OPTIONS': {
            'context_processors': [
                ...
                'eduweb.context.navigation_data',
                'eduweb.context.site_config_context',   # ← ADD THIS
                'eduweb.context.student_counts',
                'eduweb.context.admin_counts',
            ],
        },
    }]
"""

from django.template import Library
from .models import (
    Faculty, Program, CourseApplication,
    Message, Notification, SupportTicket, ContactMessage,
    SiteConfig,
)

register = Library()


# ─────────────────────────────────────────────────────────────────────────────
# 1. SITE CONFIG  ← NEW / THE KEY FIX
#    Injects `site_config` into EVERY template automatically.
#    This is what base.html, index.html, about.html, etc. all read from.
#    Views no longer need to pass 'site' or 'site_config' manually —
#    although it's safe if they still do (template just uses the same name).
# ─────────────────────────────────────────────────────────────────────────────
def site_config_context(request):
    """
    Makes {{ site_config }} available in every template.
    Returns a safe fallback object if no SiteConfig row exists yet,
    so templates never crash on {{ site_config.field|default:"..." }}.
    """
    site = SiteConfig.get()
    if site is None:
        # Return a dummy object so attribute lookups return empty string
        # instead of raising VariableDoesNotExist
        class _EmptySiteConfig:
            def __getattr__(self, name):
                return ''
            def __bool__(self):
                return False
        site = _EmptySiteConfig()
    return {'site_config': site}


# ─────────────────────────────────────────────────────────────────────────────
# 2. NAVIGATION DATA
#    Injects faculties + programs for the nav dropdowns in base.html,
#    plus the `has_pending_application` flag for the CTA button logic.
# ─────────────────────────────────────────────────────────────────────────────
def navigation_data(request):
    """Inject navigation data into every template via base.html."""

    faculties = Faculty.objects.filter(
        is_active=True
    ).only(
        'name', 'slug', 'icon', 'color_primary', 'display_order'
    ).order_by('display_order', 'name')

    # Show first 11 active programs in the nav Programs dropdown
    courses = (
        Program.objects
        .filter(is_active=True)
        .select_related('department__faculty')
        .order_by('display_order', 'name')[:11]
    )

    has_pending_application = False
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        if request.user.profile.role == 'student':
            has_pending_application = CourseApplication.objects.filter(
                user=request.user
            ).exists()

    return {
        'all_faculties': faculties,
        'all_courses': courses,
        'has_pending_application': has_pending_application,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3. STUDENT BADGE COUNTS
#    Unread messages + notifications for the student nav bar badges.
# ─────────────────────────────────────────────────────────────────────────────
def student_counts(request):
    if not request.user.is_authenticated:
        return {}
    if not hasattr(request.user, 'profile'):
        return {}
    if request.user.profile.role != 'student':
        return {}

    return {
        'unread_messages_count': Message.objects.filter(
            recipient=request.user,
            is_read=False,
            parent__isnull=True,
        ).count(),
        'unread_notifications_count': Notification.objects.filter(
            user=request.user,
            is_read=False,
        ).count(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 4. ADMIN BADGE COUNTS
#    Open tickets + unread contact messages for the admin nav bar.
# ─────────────────────────────────────────────────────────────────────────────
def admin_counts(request):
    """Inject admin badge counts into every template."""
    if not request.user.is_authenticated:
        return {}
    if not hasattr(request.user, 'profile'):
        return {}
    if request.user.profile.role not in ('admin',) and not request.user.is_staff:
        return {}

    return {
        'open_tickets_count': SupportTicket.objects.filter(
            status__in=['open', 'in_progress']
        ).count(),
        'unread_contact_count': ContactMessage.objects.filter(
            is_read=False
        ).count(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 5. TEMPLATE FILTER — currency_symbol
#    Usage in templates:  {{ payment.currency|currency_symbol }}
# ─────────────────────────────────────────────────────────────────────────────
@register.filter
def currency_symbol(currency_code):
    """Return currency symbol for a currency code string."""
    symbols = {
        'USD': '$',
        'GBP': '£',
        'EUR': '€',
        'JPY': '¥',
        'CAD': 'C$',
        'AUD': 'A$',
        'NGN': '₦',
    }
    if not currency_code:
        return ''
    return symbols.get(str(currency_code).upper(), currency_code + ' ')