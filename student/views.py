from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Avg, Q
from functools import wraps

# Role check decorator
def student_required(view_func):
    """Decorator to ensure only students can access the view"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to access this page.')
            return redirect('eduweb:auth_page')
        
        # Check if user is a student
        if request.user.profile.role != 'student':
            messages.error(request, 'Access denied. This page is for students only.')
            return redirect('management:dashboard' if request.user.is_staff else 'eduweb:index')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


# Dashboard
@login_required
@student_required
def dashboard(request):
    """Student dashboard with overview of courses, assignments, and progress"""
    context = {
        'page_title': 'My Dashboard',
        'enrolled_courses_count': 0,  # Placeholder
        'pending_assignments_count': 0,  # Placeholder
        'completed_courses_count': 0,  # Placeholder
        'certificates_count': 0,  # Placeholder
    }
    return render(request, 'students/dashboard.html', context)


# Courses
@login_required
@student_required
def my_courses(request):
    """List of student's enrolled courses"""
    context = {
        'page_title': 'My Courses',
    }
    return render(request, 'students/my_courses.html', context)


@login_required
@student_required
def course_catalog(request):
    """Browse available courses"""
    context = {
        'page_title': 'Course Catalog',
    }
    return render(request, 'students/course_catalog.html', context)


@login_required
@student_required
def course_detail(request, course_id):
    """View course details and lessons"""
    context = {
        'page_title': 'Course Details',
        'course_id': course_id,
    }
    return render(request, 'students/course_detail.html', context)


@login_required
@student_required
def enroll_course(request, course_id):
    """Enroll in a course"""
    if request.method == 'POST':
        messages.success(request, 'Successfully enrolled in the course!')
        return redirect('students:course_detail', course_id=course_id)
    return redirect('students:course_catalog')


# Lessons
@login_required
@student_required
def lesson_view(request, lesson_id):
    """View lesson content"""
    context = {
        'page_title': 'Lesson',
        'lesson_id': lesson_id,
    }
    return render(request, 'students/lesson_view.html', context)


@login_required
@student_required
def mark_lesson_complete(request, lesson_id):
    """Mark a lesson as completed"""
    if request.method == 'POST':
        return JsonResponse({'success': True, 'message': 'Lesson marked as complete'})
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)


# Assignments
@login_required
@student_required
def assignments(request):
    """List all assignments"""
    context = {
        'page_title': 'My Assignments',
    }
    return render(request, 'students/assignments.html', context)


@login_required
@student_required
def assignment_detail(request, assignment_id):
    """View assignment details"""
    context = {
        'page_title': 'Assignment Details',
        'assignment_id': assignment_id,
    }
    return render(request, 'students/assignment_detail.html', context)


@login_required
@student_required
def submit_assignment(request, assignment_id):
    """Submit an assignment"""
    if request.method == 'POST':
        messages.success(request, 'Assignment submitted successfully!')
        return redirect('students:assignment_detail', assignment_id=assignment_id)
    return redirect('students:assignments')


# Quizzes
@login_required
@student_required
def quiz_detail(request, quiz_id):
    """View quiz details"""
    context = {
        'page_title': 'Quiz',
        'quiz_id': quiz_id,
    }
    return render(request, 'students/quiz_detail.html', context)


@login_required
@student_required
def quiz_attempt(request, quiz_id):
    """Attempt a quiz"""
    context = {
        'page_title': 'Quiz Attempt',
        'quiz_id': quiz_id,
    }
    return render(request, 'students/quiz_attempt.html', context)


@login_required
@student_required
def submit_quiz(request, quiz_id):
    """Submit quiz answers"""
    if request.method == 'POST':
        messages.success(request, 'Quiz submitted successfully!')
        return redirect('students:quiz_detail', quiz_id=quiz_id)
    return redirect('students:assignments')


# Grades & Progress
@login_required
@student_required
def grades(request):
    """View grades and performance"""
    context = {
        'page_title': 'Grades & Performance',
    }
    return render(request, 'students/grades.html', context)


@login_required
@student_required
def progress(request):
    """View learning progress"""
    context = {
        'page_title': 'My Progress',
    }
    return render(request, 'students/progress.html', context)


# Certificates
@login_required
@student_required
def certificates(request):
    """List earned certificates"""
    context = {
        'page_title': 'My Certificates',
    }
    return render(request, 'students/certificates.html', context)


@login_required
@student_required
def download_certificate(request, certificate_id):
    """Download a certificate"""
    # Placeholder - would generate/return PDF
    messages.info(request, 'Certificate download feature coming soon!')
    return redirect('students:certificates')


# Messages
@login_required
@student_required
def messages(request):
    """View messages"""
    context = {
        'page_title': 'Messages',
    }
    return render(request, 'students/messages.html', context)


@login_required
@student_required
def message_detail(request, message_id):
    """View message details"""
    context = {
        'page_title': 'Message',
        'message_id': message_id,
    }
    return render(request, 'students/message_detail.html', context)


@login_required
@student_required
def compose_message(request):
    """Compose a new message"""
    if request.method == 'POST':
        messages.success(request, 'Message sent successfully!')
        return redirect('students:messages')
    
    context = {
        'page_title': 'Compose Message',
    }
    return render(request, 'students/compose_message.html', context)


# Profile & Settings
@login_required
@student_required
def profile(request):
    """View/edit profile"""
    context = {
        'page_title': 'My Profile',
    }
    return render(request, 'students/profile.html', context)


@login_required
@student_required
def settings(request):
    """Account settings"""
    if request.method == 'POST':
        messages.success(request, 'Settings updated successfully!')
        return redirect('students:settings')
    
    context = {
        'page_title': 'Settings',
    }
    return render(request, 'students/settings.html', context)