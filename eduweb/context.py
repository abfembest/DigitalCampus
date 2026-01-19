from .models import Faculty, Course

def navigation_data(request):
    """Provide faculties and courses for navigation"""
    faculties = Faculty.objects.filter(is_active=True).prefetch_related('courses')
    courses = Course.objects.filter(is_active=True).select_related('faculty')
    
    return {
        'all_faculties': faculties,
        'all_courses': courses,
    }