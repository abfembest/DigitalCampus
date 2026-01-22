from .models import Faculty, Course

def navigation_data(request):
    """Provide faculties and courses for navigation"""
    faculties = Faculty.objects.filter(is_active=True).prefetch_related('courses')[:11]
    courses = Course.objects.filter(is_active=True).select_related('faculty')[:11]
    
    return {
        'all_faculties': faculties,
        'all_courses': courses,
    }