from .models import Faculty, Course

def navigation_data(request):
    """Provide faculties and courses for navigation"""
    faculties = Faculty.objects.filter(is_active=True).prefetch_related('courses')[:11]
    courses = Course.objects.filter(is_active=True).select_related('faculty')[:11]
    
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