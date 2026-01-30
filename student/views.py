from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from functools import wraps

from eduweb.models import (
    LMSCourse, Enrollment, Lesson, LessonProgress, 
    CourseCategory, Assignment, AssignmentSubmission,
    Certificate, Announcement
)


def student_required(view_func):
    """Decorator to ensure only students can access"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(
                request, 
                'Please login to access this page.'
            )
            return redirect('eduweb:auth_page')
        
        if request.user.profile.role != 'student':
            messages.error(
                request, 
                'Access denied. Students only.'
            )
            return redirect(
                'management:dashboard' 
                if request.user.is_staff 
                else 'eduweb:index'
            )
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


@login_required
@student_required
def dashboard(request):
    """Student dashboard with overview"""
    user = request.user
    
    # Active enrollments (limit to 5)
    enrollments = Enrollment.objects.filter(
        student=user,
        status='active'
    ).select_related('course')[:5]
    
    # Pending assignments
    pending_assignments = Assignment.objects.filter(
        lesson__course__enrollments__student=user,
        lesson__course__enrollments__status='active',
        due_date__gte=timezone.now(),
        is_active=True
    ).exclude(
        submissions__student=user,
        submissions__status__in=['submitted', 'graded']
    ).select_related(
        'lesson__course'
    ).order_by('due_date')[:5]
    
    # Recent announcements
    announcements = Announcement.objects.filter(
        Q(announcement_type='system') |
        Q(
            course__enrollments__student=user, 
            announcement_type='course'
        ),
        is_active=True,
        publish_date__lte=timezone.now()
    ).distinct().order_by('-publish_date')[:5]
    
    # Statistics
    total_enrolled = Enrollment.objects.filter(
        student=user
    ).count()
    
    completed_courses = Enrollment.objects.filter(
        student=user,
        status='completed'
    ).count()
    
    certificates_earned = Certificate.objects.filter(
        student=user
    ).count()
    
    context = {
        'page_title': 'My Dashboard',
        'enrollments': enrollments,
        'pending_assignments': pending_assignments,
        'announcements': announcements,
        'total_enrolled': total_enrolled,
        'completed_courses': completed_courses,
        'certificates_earned': certificates_earned,
    }
    
    return render(request, 'students/dashboard.html', context)


@login_required
@student_required
def my_courses(request):
    """List student's enrolled courses - Active and Completed only"""
    status_filter = request.GET.get('status', 'active')
    
    # Only allow 'active' or 'completed' filters
    if status_filter not in ['active', 'completed']:
        status_filter = 'active'
    
    # Filter enrollments by status
    enrollments = Enrollment.objects.filter(
        student=request.user,
        status=status_filter
    ).select_related(
        'course', 
        'course__category'
    ).order_by('-enrolled_at')
    
    context = {
        'page_title': 'My Courses',
        'enrollments': enrollments,
        'status_filter': status_filter,
    }
    
    return render(request, 'students/my_courses.html', context)


@login_required
@student_required
def course_catalog(request):
    """Browse available courses (NOT enrolled)"""
    category_slug = request.GET.get('category')
    search_query = request.GET.get('q')
    difficulty = request.GET.get('difficulty')
    
    # Get published courses
    courses = LMSCourse.objects.filter(
        is_published=True,
    )
    
    # Apply filters
    if category_slug:
        courses = courses.filter(
            category__slug=category_slug
        )
    
    if search_query:
        courses = courses.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(short_description__icontains=search_query)
        )
    
    if difficulty:
        courses = courses.filter(
            difficulty_level=difficulty
        )
    
    # Optimize queries
    courses = courses.select_related(
        'category', 
        'instructor'
    ).order_by('-created_at')
    
    # Get enrolled course IDs
    enrolled_ids = list(
        Enrollment.objects.filter(
            student=request.user
        ).values_list('course_id', flat=True)
    )
    
    # Get active categories
    categories = CourseCategory.objects.filter(
        is_active=True
    ).order_by('name')
    
    context = {
        'page_title': 'Course Catalog',
        'courses': courses,
        'categories': categories,
        'enrolled_ids': enrolled_ids,
        'search_query': search_query,
    }
    
    return render(
        request, 
        'students/course_catalog.html', 
        context
    )


@login_required
@student_required
def course_detail(request, course_id):
    """View course details"""
    course = get_object_or_404(
        LMSCourse.objects.select_related(
            'instructor', 
            'category'
        ),
        id=course_id,
        is_published=True
    )
    
    # Check enrollment
    enrollment = Enrollment.objects.filter(
        student=request.user,
        course=course
    ).first()
    
    # Get course sections
    sections = course.sections.filter(
        is_active=True
    ).order_by('display_order')
    
    # For non-enrolled users, filter lessons to show only previews
    if not enrollment:
        # Create a list to store sections with filtered lessons
        filtered_sections = []
        
        for section in sections:
            # Get only preview lessons for this section
            preview_lessons = section.lessons.filter(
                is_preview=True,
                is_active=True
            )
            
            if preview_lessons.exists():
                section.filtered_lessons = preview_lessons
                filtered_sections.append(section)
        
        sections = filtered_sections
    else:
        # For enrolled users, get all active lessons
        for section in sections:
            section.filtered_lessons = section.lessons.filter(
                is_active=True
            )
    
    context = {
        'page_title': course.title,
        'course': course,
        'enrollment': enrollment,
        'sections': sections,
    }
    
    return render(
        request, 
        'students/course_detail.html', 
        context
    )


@login_required
@student_required
def enroll_course(request, course_id):
    """
    Enroll in a course
    NOTE: Payment logic should be added here
    """
    if request.method != 'POST':
        return redirect('students:course_catalog')
    
    course = get_object_or_404(
        LMSCourse, 
        id=course_id, 
        is_published=True
    )
    
    # Check existing enrollment
    existing = Enrollment.objects.filter(
        student=request.user,
        course=course
    ).first()
    
    if existing:
        messages.info(
            request, 
            'You are already enrolled in this course.'
        )
        return redirect(
            'students:course_detail', 
            course_id=course_id
        )
    
    # TODO: Add payment verification here
    # For now, only allow free courses
    if not course.is_free:
        messages.error(
            request,
            'Payment required. Please complete payment first.'
        )
        # Redirect to payment page (to be implemented)
        return redirect(
            'students:course_detail', 
            course_id=course_id
        )
    
    # Create enrollment for free courses
    Enrollment.objects.create(
        student=request.user,
        course=course,
        enrolled_by=request.user,
        status='active'
    )
    
    messages.success(
        request, 
        f'Successfully enrolled in {course.title}!'
    )
    
    return redirect(
        'students:course_detail', 
        course_id=course_id
    )


@login_required
@student_required
def lesson_view(request, lesson_id):
    """View lesson content"""
    lesson = get_object_or_404(
        Lesson.objects.select_related(
            'course', 
            'section'
        ),
        id=lesson_id,
        is_active=True
    )
    
    # Verify enrollment or preview access
    enrollment = Enrollment.objects.filter(
        student=request.user,
        course=lesson.course
    ).first()
    
    # Check access
    if not enrollment and not lesson.is_preview:
        messages.error(
            request,
            'Please enroll to access this lesson.'
        )
        return redirect(
            'students:course_detail', 
            course_id=lesson.course.id
        )
    
    # Track progress for enrolled students
    progress = None
    if enrollment:
        progress, _ = LessonProgress.objects.get_or_create(
            enrollment=enrollment,
            lesson=lesson
        )
        progress.last_accessed = timezone.now()
        progress.save(update_fields=['last_accessed'])
    
    # Get navigation lessons
    all_lessons = list(
        lesson.course.lessons.filter(
            is_active=True
        ).order_by(
            'section__display_order', 
            'display_order'
        )
    )
    
    try:
        current_idx = all_lessons.index(lesson)
        next_lesson = (
            all_lessons[current_idx + 1] 
            if current_idx < len(all_lessons) - 1 
            else None
        )
        prev_lesson = (
            all_lessons[current_idx - 1] 
            if current_idx > 0 
            else None
        )
    except ValueError:
        next_lesson = None
        prev_lesson = None
    
    context = {
        'page_title': lesson.title,
        'lesson': lesson,
        'enrollment': enrollment,
        'progress': progress,
        'next_lesson': next_lesson,
        'prev_lesson': prev_lesson,
    }
    
    return render(
        request, 
        'students/lesson.html', 
        context
    )


@login_required
@student_required
def mark_lesson_complete(request, lesson_id):
    """Mark lesson as completed"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Invalid request method'
        }, status=400)
    
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    enrollment = get_object_or_404(
        Enrollment,
        student=request.user,
        course=lesson.course,
        status='active'
    )
    
    progress, _ = LessonProgress.objects.get_or_create(
        enrollment=enrollment,
        lesson=lesson
    )
    
    progress.is_completed = True
    progress.completion_percentage = 100
    progress.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Lesson marked as complete',
        'progress': enrollment.progress_percentage
    })


@login_required
@student_required
def assignments(request):
    """List all assignments"""
    status_filter = request.GET.get('status', 'pending')
    
    # Base query
    base_query = Assignment.objects.filter(
        lesson__course__enrollments__student=request.user
    )
    
    # Filter by status
    if status_filter == 'pending':
        assignments = base_query.filter(
            lesson__course__enrollments__status='active',
            is_active=True
        ).exclude(
            submissions__student=request.user,
            submissions__status__in=['submitted', 'graded']
        )
    elif status_filter == 'submitted':
        assignments = base_query.filter(
            submissions__student=request.user,
            submissions__status='submitted'
        )
    elif status_filter == 'graded':
        assignments = base_query.filter(
            submissions__student=request.user,
            submissions__status='graded'
        )
    else:
        assignments = base_query
    
    assignments = assignments.select_related(
        'lesson__course'
    ).distinct().order_by('due_date')
    
    context = {
        'page_title': 'My Assignments',
        'assignments': assignments,
        'status_filter': status_filter,
    }
    
    return render(
        request, 
        'students/assignments.html', 
        context
    )


@login_required
@student_required
def assignment_detail(request, assignment_id):
    """View assignment details"""
    assignment = get_object_or_404(
        Assignment.objects.select_related(
            'lesson__course'
        ),
        id=assignment_id
    )
    
    # Verify enrollment
    enrollment = get_object_or_404(
        Enrollment,
        student=request.user,
        course=assignment.lesson.course
    )
    
    # Get submission
    submission = AssignmentSubmission.objects.filter(
        assignment=assignment,
        student=request.user
    ).first()
    
    context = {
        'page_title': assignment.title,
        'assignment': assignment,
        'enrollment': enrollment,
        'submission': submission,
    }
    
    return render(
        request, 
        'students/assignment_detail.html', 
        context
    )


@login_required
@student_required
def submit_assignment(request, assignment_id):
    """Submit assignment"""
    if request.method != 'POST':
        return redirect('students:assignments')
    
    assignment = get_object_or_404(
        Assignment, 
        id=assignment_id
    )
    
    # Verify enrollment
    get_object_or_404(
        Enrollment,
        student=request.user,
        course=assignment.lesson.course,
        status='active'
    )
    
    # Get or create submission
    submission, _ = AssignmentSubmission.objects.get_or_create(
        assignment=assignment,
        student=request.user
    )
    
    # Update submission
    submission.submission_text = request.POST.get(
        'submission_text', 
        ''
    )
    
    if request.FILES.get('attachment'):
        submission.attachment = request.FILES['attachment']
    
    submission.status = 'submitted'
    submission.submitted_at = timezone.now()
    
    # Check if late
    if timezone.now() > assignment.due_date:
        submission.is_late = True
    
    submission.save()
    
    messages.success(
        request, 
        'Assignment submitted successfully!'
    )
    
    return redirect(
        'students:assignment_detail', 
        assignment_id=assignment_id
    )


@login_required
@student_required
def grades(request):
    """View grades"""
    enrollments = Enrollment.objects.filter(
        student=request.user
    ).select_related('course')
    
    submissions = AssignmentSubmission.objects.filter(
        student=request.user,
        status='graded'
    ).select_related('assignment__lesson__course')
    
    context = {
        'page_title': 'Grades & Performance',
        'enrollments': enrollments,
        'submissions': submissions,
    }
    
    return render(request, 'students/grades.html', context)


@login_required
@student_required
def progress(request):
    """View learning progress"""
    enrollments = Enrollment.objects.filter(
        student=request.user
    ).select_related('course').order_by('-enrolled_at')
    
    context = {
        'page_title': 'My Progress',
        'enrollments': enrollments,
    }
    
    return render(request, 'students/progress.html', context)


@login_required
@student_required
def certificates(request):
    """List certificates"""
    certificates = Certificate.objects.filter(
        student=request.user
    ).select_related('course').order_by('-issued_at')
    
    context = {
        'page_title': 'My Certificates',
        'certificates': certificates,
    }
    
    return render(
        request, 
        'students/certificates.html', 
        context
    )


@login_required
@student_required
def profile(request):
    """View/edit profile"""
    if request.method == 'POST':
        user = request.user
        profile = user.profile
        
        # Update user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()
        
        # Update profile
        profile.bio = request.POST.get('bio', '')
        profile.phone = request.POST.get('phone', '')
        profile.city = request.POST.get('city', '')
        profile.country = request.POST.get('country', '')
        
        if request.FILES.get('avatar'):
            profile.avatar = request.FILES['avatar']
        
        profile.save()
        
        messages.success(
            request, 
            'Profile updated successfully!'
        )
        return redirect('students:profile')
    
    context = {
        'page_title': 'My Profile',
    }
    
    return render(request, 'students/profile.html', context)


@login_required
@student_required
def settings(request):
    """Account settings"""
    if request.method == 'POST':
        profile = request.user.profile
        
        # Update preferences
        profile.email_notifications = (
            request.POST.get('email_notifications') == 'on'
        )
        profile.marketing_emails = (
            request.POST.get('marketing_emails') == 'on'
        )
        profile.save()
        
        messages.success(
            request, 
            'Settings updated successfully!'
        )
        return redirect('students:settings')
    
    context = {
        'page_title': 'Settings',
    }
    
    return render(request, 'students/settings.html', context)