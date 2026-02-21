from .models import Faculty, Program


def navigation_data(request):
    """Inject navigation data into every template via base.html."""

    faculties = Faculty.objects.filter(
        is_active=True
    ).only(
        'name', 'slug', 'icon', 'color_primary', 'display_order'
    ).order_by('display_order', 'name')

    courses = Program.objects.filter(is_active=True).select_related('department__faculty')[:11]
    
    return {
        'all_faculties': faculties,
        'all_courses': courses,
    }

from django import template

register = template.Library()

@register.filter
def currency_symbol(currency_code):
    """Return currency symbol for currency code"""
    symbols = {
        'USD': '$',
        'GBP': '£',
        'EUR': '€',
        'JPY': '¥',
        'CAD': 'C$',
        'AUD': 'A$',
        'NGN': '₦',
    }
    return symbols.get(currency_code.upper(), currency_code + ' ')