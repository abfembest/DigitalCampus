from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, Avg, Prefetch, Max, Sum, F
from django.utils import timezone
from django.core.paginator import Paginator
from functools import wraps
from datetime import timedelta
from decimal import Decimal

from eduweb.models import (
    LMSCourse, Enrollment, Lesson, LessonProgress, 
    CourseCategory, Assignment, AssignmentSubmission,
    Certificate, Announcement, Quiz, QuizAttempt, 
    QuizAnswer, QuizQuestion, QuizResponse, StudyGroup, StudyGroupMember, 
    Discussion, DiscussionReply, Badge, 
    StudentBadge, LessonSection
)

from .forms import AssignmentSubmissionForm, SettingsForm, ProfileUpdateForm, ReplyCreateForm, ThreadCreateForm, StudyGroupMessageForm, StudentSupportTicketForm

from django.core.mail import send_mail
from django.conf import settings


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
        
        # Check if user has profile
        if not hasattr(request.user, 'profile'):
            messages.error(
                request, 
                'Profile not found. Please contact support.'
            )
            return redirect('eduweb:index')
        
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
    """
    Student dashboard with overview of courses, 
    assignments, and announcements
    """
    user = request.user
    
    try:
        # Get active enrollments with optimized query
        enrollments = (
            Enrollment.objects
            .filter(student=user, status='active')
            .select_related('course', 'course__category')
            .prefetch_related(
                Prefetch(
                    'course__lessons',
                    to_attr='all_lessons'
                )
            )
            .order_by('-last_accessed')[:5]
        )
        
        # Add progress data to each enrollment
        for enrollment in enrollments:
            completed_count = (
                LessonProgress.objects
                .filter(
                    enrollment=enrollment,
                    is_completed=True
                )
                .count()
            )
            enrollment.completed_lessons_count = completed_count
        
        # Get pending assignments - only those not submitted or graded
        pending_assignments = (
            Assignment.objects
            .filter(
                lesson__course__enrollments__student=user,
                lesson__course__enrollments__status='active',
                due_date__gte=timezone.now(),
                is_active=True
            )
            .exclude(
                Q(submissions__student=user) & 
                Q(submissions__status__in=['submitted', 'graded'])
            )
            .select_related('lesson__course')
            .distinct()
            .order_by('due_date')[:5]
        )
        
        # Get recent announcements
        announcements = (
            Announcement.objects
            .filter(
                Q(announcement_type='system') |
                Q(
                    course__enrollments__student=user,
                    announcement_type='course'
                ),
                is_active=True,
                publish_date__lte=timezone.now()
            )
            .filter(
                Q(expiry_date__isnull=True) |
                Q(expiry_date__gte=timezone.now())
            )
            .distinct()
            .order_by('-priority', '-publish_date')[:5]
        )
        
        # Calculate statistics
        stats = {
            'total_enrolled': (
                Enrollment.objects
                .filter(student=user)
                .count()
            ),
            'completed_courses': (
                Enrollment.objects
                .filter(student=user, status='completed')
                .count()
            ),
            'certificates_earned': (
                Certificate.objects
                .filter(student=user)
                .count()
            ),
        }
        
    except Exception as e:
        # Log error in production
        messages.error(
            request,
            'An error occurred loading the dashboard. '
            'Please try again.'
        )
        # Return minimal context
        enrollments = []
        pending_assignments = []
        announcements = []
        stats = {
            'total_enrolled': 0,
            'completed_courses': 0,
            'certificates_earned': 0,
        }
    
    context = {
        'page_title': 'My Dashboard',
        'enrollments': enrollments,
        'pending_assignments': pending_assignments,
        'announcements': announcements,
        'total_enrolled': stats['total_enrolled'],
        'completed_courses': stats['completed_courses'],
        'certificates_earned': stats['certificates_earned'],
    }
    
    return render(request, 'students/dashboard.html', context)



@login_required
@student_required
def my_courses(request):
    """
    Display student's enrolled courses
    Filter by active or completed status
    """
    # Get status filter from request
    status_filter = request.GET.get('status', 'active')
    
    # Validate status filter
    valid_statuses = ['active', 'completed']
    if status_filter not in valid_statuses:
        status_filter = 'active'
    
    try:
        # Optimized query with select/prefetch related
        enrollments = (
            Enrollment.objects
            .filter(
                student=request.user,
                status=status_filter
            )
            .select_related(
                'course',
                'course__category',
                'course__instructor'
            )
            .prefetch_related(
                Prefetch(
                    'course__lessons',
                    queryset=Lesson.objects.filter(is_active=True),
                    to_attr='active_lessons'
                )
            )
            .order_by('-enrolled_at')
        )
        
        # Add completed lesson count to each enrollment
        for enrollment in enrollments:
            completed_count = (
                LessonProgress.objects
                .filter(
                    enrollment=enrollment,
                    is_completed=True
                )
                .count()
            )
            enrollment.completed_lessons_count = completed_count
            
    except Exception as e:
        messages.error(
            request,
            'Error loading courses. Please try again.'
        )
        enrollments = []
    
    context = {
        'page_title': 'My Courses',
        'enrollments': enrollments,
        'status_filter': status_filter,
    }
    
    return render(request, 'students/my_courses.html', context)


@login_required
@student_required
def course_catalog(request):
    """
    Browse available courses with filters and search
    Optimized queries and pagination
    """
    # Get filter parameters
    category_slug = request.GET.get('category', '').strip()
    search_query = request.GET.get('q', '').strip()
    difficulty = request.GET.get('difficulty', '').strip()
    
    try:
        # Start with published courses only
        courses = LMSCourse.objects.filter(is_published=True)
        
        # Apply category filter
        if category_slug:
            courses = courses.filter(category__slug=category_slug)
        
        # Apply search filter
        if search_query:
            courses = courses.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(short_description__icontains=search_query) |
                Q(code__icontains=search_query)
            )
        
        # Apply difficulty filter
        if difficulty and difficulty in dict(LMSCourse.DIFFICULTY_CHOICES):
            courses = courses.filter(difficulty_level=difficulty)
        
        # Optimize query with select_related
        courses = (
            courses
            .select_related('category', 'instructor')
            .order_by('-is_featured', '-created_at')
        )
        
        # Get enrolled course IDs
        enrolled_course_ids = set(
            Enrollment.objects
            .filter(student=request.user)
            .values_list('course_id', flat=True)
        )
        
        # Get active categories
        categories = (
            CourseCategory.objects
            .filter(is_active=True)
            .order_by('name')
        )
        
        # Pagination
        paginator = Paginator(courses, 12)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
    except Exception as e:
        messages.error(
            request,
            'Error loading course catalog. Please try again.'
        )
        page_obj = None
        categories = []
        enrolled_course_ids = set()
    
    context = {
        'page_title': 'Course Catalog',
        'courses': page_obj,
        'categories': categories,
        'enrolled_ids': enrolled_course_ids,
        'search_query': search_query,
        'category_slug': category_slug,
        'difficulty': difficulty,
    }
    
    return render(request, 'students/course_catalog.html', context)


@login_required
@student_required
def course_detail(request, course_slug):
    """
    Display comprehensive course details
    - Uses slug for SEO-friendly URLs
    - Efficient queries with select_related/prefetch_related
    - Different views for enrolled vs non-enrolled students
    - Security: Validates enrollment status
    """
    try:
        # Fetch course with related data in single query
        course = get_object_or_404(
            LMSCourse.objects
            .select_related('instructor', 'category')
            .prefetch_related(
                Prefetch(
                    'sections',
                    queryset=LessonSection.objects
                    .filter(is_active=True)
                    .prefetch_related(
                        Prefetch(
                            'lessons',
                            queryset=Lesson.objects.filter(is_active=True).order_by('display_order'),
                            to_attr='active_lessons'
                        )
                    )
                    .order_by('display_order'),
                    to_attr='active_sections'
                )
            ),
            slug=course_slug,
            is_published=True
        )
        
        # Check if student is enrolled
        enrollment = Enrollment.objects.filter(
            student=request.user,
            course=course
        ).select_related('course').first()
        
        # Prepare sections with filtered lessons
        sections = course.active_sections
        
        for section in sections:
            if enrollment:
                # Enrolled: show all lessons
                section.filtered_lessons = section.active_lessons
            else:
                # Not enrolled: show only preview lessons
                section.filtered_lessons = [
                    lesson for lesson in section.active_lessons 
                    if lesson.is_preview
                ]
        
        # Calculate progress for enrolled students
        if enrollment:
            completed_count = LessonProgress.objects.filter(
                enrollment=enrollment,
                is_completed=True
            ).count()
            enrollment.completed_lessons_count = completed_count
            
            # Get the first incomplete lesson for "Continue Learning" button
            first_incomplete_lesson = None
            for section in sections:
                for lesson in section.filtered_lessons:
                    # Check if lesson is not completed
                    is_completed = LessonProgress.objects.filter(
                        enrollment=enrollment,
                        lesson=lesson,
                        is_completed=True
                    ).exists()
                    
                    if not is_completed:
                        first_incomplete_lesson = lesson
                        break
                if first_incomplete_lesson:
                    break
            
            enrollment.next_lesson = first_incomplete_lesson
        
        context = {
            'page_title': course.title,
            'course': course,
            'enrollment': enrollment,
            'sections': sections,
        }
        
        return render(request, 'students/course_detail.html', context)
        
    except Exception as e:
        # Log error in production
        messages.error(
            request,
            'An error occurred loading the course. Please try again.'
        )
        return redirect('students:course_catalog')


@login_required
@student_required
def enroll_course(request, course_slug):
    """
    Enroll in a course
    Handles free courses immediately, redirects paid courses to payment
    """
    if request.method != 'POST':
        return redirect('students:course_catalog')
    
    # Get course by slug
    course = get_object_or_404(
        LMSCourse, 
        slug=course_slug, 
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
        return redirect('students:course_detail', course_slug=course_slug)
    
    # Create enrollment for free courses
    if course.is_free:
        try:
            enrollment = Enrollment.objects.create(
                student=request.user,
                course=course,
                status='active',
                enrolled_at=timezone.now()
            )
            
            messages.success(
                request,
                f'Successfully enrolled in {course.title}!'
            )
            return redirect('students:course_detail', course_slug=course_slug)
            
        except Exception as e:
            messages.error(
                request,
                'An error occurred during enrollment. Please try again.'
            )
            return redirect('students:course_detail', course_slug=course_slug)
    else:
        # TODO: Handle paid course enrollment
        messages.info(
            request,
            'This is a paid course. Payment processing will be implemented.'
        )
        return redirect('students:course_detail', course_slug=course_slug)


@login_required
@student_required
def lesson_view(request, course_slug, lesson_slug):
    """
    View lesson content using slug
    Tracks progress and provides navigation
    """
    # Get lesson by slug
    lesson = get_object_or_404(
        Lesson.objects.select_related(
            'course', 
            'section'
        ),
        course__slug=course_slug,
        slug=lesson_slug,
        is_active=True
    )
    
    # Verify enrollment
    enrollment = get_object_or_404(
        Enrollment,
        student=request.user,
        course=lesson.course,
        status__in=['active', 'completed']
    )
    
    # Get or create progress
    progress, created = LessonProgress.objects.get_or_create(
        enrollment=enrollment,
        lesson=lesson,
        defaults={
            'last_accessed': timezone.now()
        }
    )
    
    # Update last accessed if not just created
    if not created:
        progress.last_accessed = timezone.now()
        progress.save(update_fields=['last_accessed'])
    
    # Get all lessons in course for navigation
    all_lessons = list(
        Lesson.objects.filter(
            course=lesson.course,
            is_active=True
        ).select_related('section')
        .order_by('section__display_order', 'display_order')
    )
    
    # Get completed lesson IDs for this enrollment
    completed_lesson_ids = set(
        LessonProgress.objects.filter(
            enrollment=enrollment,
            is_completed=True
        ).values_list('lesson_id', flat=True)
    )
    
    # Add completion status to all lessons
    for l in all_lessons:
        l.is_completed = l.id in completed_lesson_ids
    
    # Find current lesson index
    try:
        current_index = next(
            i for i, l in enumerate(all_lessons) 
            if l.id == lesson.id
        )
    except StopIteration:
        current_index = None
    
    # Get previous and next lessons
    prev_lesson = None
    next_lesson = None
    
    if current_index is not None:
        if current_index > 0:
            prev_lesson = all_lessons[current_index - 1]
        if current_index < len(all_lessons) - 1:
            next_lesson = all_lessons[current_index + 1]
    
    # Calculate completed lessons count
    completed_lessons_count = len(completed_lesson_ids)
    enrollment.completed_lessons = completed_lessons_count
    
    context = {
        'page_title': lesson.title,
        'lesson': lesson,
        'enrollment': enrollment,
        'progress': progress,
        'prev_lesson': prev_lesson,
        'next_lesson': next_lesson,
    }
    
    return render(request, 'students/lesson.html', context)

@login_required
@student_required
def mark_lesson_complete(request, course_slug, lesson_slug):
    """
    Mark lesson as complete via AJAX
    Updates enrollment progress
    """
    from django.http import JsonResponse
    
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Invalid request method'
        }, status=400)
    
    # Get lesson
    lesson = get_object_or_404(
        Lesson,
        course__slug=course_slug,
        slug=lesson_slug,
        is_active=True
    )
    
    # Verify enrollment
    enrollment = get_object_or_404(
        Enrollment,
        student=request.user,
        course=lesson.course,
        status__in=['active', 'completed']
    )
    
    try:
        # Get or create progress
        progress, created = LessonProgress.objects.get_or_create(
            enrollment=enrollment,
            lesson=lesson
        )
        
        # Mark as complete
        if not progress.is_completed:
            progress.is_completed = True
            progress.completion_percentage = 100
            progress.completed_at = timezone.now()
            progress.save()
            
            # Update enrollment progress
            if hasattr(enrollment, 'update_progress'):
                enrollment.update_progress()
        
        return JsonResponse({
            'success': True,
            'message': 'Lesson marked as complete',
            'progress': enrollment.progress_percentage
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'An error occurred. Please try again.'
        }, status=500)


@login_required
@student_required
def assignments(request):
    """
    Display student's assignments with filtering
    Supports: pending, submitted, graded, all
    """
    # Get and validate status filter
    status_filter = request.GET.get('status', 'pending').lower()
    valid_statuses = ['pending', 'submitted', 'graded', 'all']
    
    if status_filter not in valid_statuses:
        status_filter = 'pending'
    
    try:
        # Get user's enrolled course IDs
        enrolled_course_ids = (
            Enrollment.objects
            .filter(
                student=request.user,
                status__in=['active', 'completed']
            )
            .values_list('course_id', flat=True)
        )
        
        # Base query: assignments from enrolled courses
        assignments_query = (
            Assignment.objects
            .filter(
                lesson__course_id__in=enrolled_course_ids,
                is_active=True
            )
            .select_related(
                'lesson__course',
                'lesson__course__category',
                'lesson__section'
            )
            .prefetch_related(
                Prefetch(
                    'submissions',
                    queryset=AssignmentSubmission.objects.filter(
                        student=request.user
                    ).select_related('graded_by'),
                    to_attr='user_submissions'
                )
            )
            .order_by('due_date')
        )
        
        # Apply status filtering
        if status_filter == 'pending':
            # Not submitted OR draft status
            assignments_query = assignments_query.exclude(
                submissions__student=request.user,
                submissions__status__in=['submitted', 'graded']
            ).distinct()
            
        elif status_filter == 'submitted':
            # Submitted but not graded
            assignments_query = assignments_query.filter(
                submissions__student=request.user,
                submissions__status='submitted'
            ).distinct()
            
        elif status_filter == 'graded':
            # Graded assignments
            assignments_query = assignments_query.filter(
                submissions__student=request.user,
                submissions__status='graded'
            ).distinct()
        
        # For 'all', no additional filtering needed
        
        # Execute query
        assignments_list = list(assignments_query)
        
        # Add submission info and overdue status
        for assignment in assignments_list:
            # Get user's submission if exists
            assignment.submission = (
                assignment.user_submissions[0] 
                if assignment.user_submissions 
                else None
            )
            
            # Check if overdue (only for non-submitted)
            if not assignment.submission or assignment.submission.status == 'draft':
                assignment.is_overdue = timezone.now() > assignment.due_date
            else:
                assignment.is_overdue = False
                
    except Exception as e:
        messages.error(
            request,
            'Error loading assignments. Please try again.'
        )
        assignments_list = []
    
    context = {
        'page_title': 'My Assignments',
        'assignments': assignments_list,
        'status_filter': status_filter,
    }
    
    return render(request, 'students/assignments.html', context)


@login_required
@student_required
def assignment_detail(request, course_slug, assignment_slug):
    """
    View assignment details
    Uses course slug and assignment slug for SEO-friendly URLs
    """
    # Get assignment with related data
    assignment = get_object_or_404(
        Assignment.objects.select_related(
            'lesson__course',
            'lesson__section'
        ),
        lesson__course__slug=course_slug,
        slug=assignment_slug,
        is_active=True
    )
    
    # Verify student is enrolled in the course
    enrollment = get_object_or_404(
        Enrollment,
        student=request.user,
        course=assignment.lesson.course,
        status__in=['active', 'completed']
    )
    
    # Get student's submission if exists
    try:
        submission = AssignmentSubmission.objects.select_related(
            'graded_by'
        ).get(
            assignment=assignment,
            student=request.user
        )
    except AssignmentSubmission.DoesNotExist:
        submission = None
    
    # Check if overdue
    is_overdue = (
        timezone.now() > assignment.due_date 
        and not submission
    )
    
    context = {
        'page_title': assignment.title,
        'assignment': assignment,
        'submission': submission,
        'enrollment': enrollment,
        'is_overdue': is_overdue,
    }
    
    return render(request, 'students/assignment_detail.html', context)


@login_required
@student_required
def submit_assignment(request, course_slug, assignment_slug):
    """
    Handle assignment submission
    Uses Django forms for validation
    """
    # Get assignment
    assignment = get_object_or_404(
        Assignment.objects.select_related('lesson__course'),
        lesson__course__slug=course_slug,
        slug=assignment_slug,
        is_active=True
    )
    
    # Verify enrollment
    enrollment = get_object_or_404(
        Enrollment,
        student=request.user,
        course=assignment.lesson.course,
        status__in=['active', 'completed']
    )
    
    # Check if already submitted
    existing_submission = AssignmentSubmission.objects.filter(
        assignment=assignment,
        student=request.user,
        status__in=['submitted', 'graded']
    ).first()
    
    if existing_submission:
        messages.info(
            request,
            'You have already submitted this assignment.'
        )
        return redirect(
            'students:assignment_detail',
            course_slug=course_slug,
            assignment_slug=assignment_slug
        )
    
    # Check if overdue and late submissions not allowed
    is_overdue = timezone.now() > assignment.due_date
    
    if is_overdue and not assignment.allow_late_submission:
        messages.error(
            request,
            'This assignment is past due and no longer accepts submissions.'
        )
        return redirect(
            'students:assignment_detail',
            course_slug=course_slug,
            assignment_slug=assignment_slug
        )
    
    if request.method == 'POST':
        form = AssignmentSubmissionForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                # Create or update submission
                submission, created = AssignmentSubmission.objects.get_or_create(
                    assignment=assignment,
                    student=request.user,
                    defaults={
                        'submission_text': form.cleaned_data['submission_text'],
                        'status': 'submitted',
                        'submitted_at': timezone.now(),
                        'is_late': is_overdue,
                    }
                )
                
                # If not created, update existing draft
                if not created:
                    submission.submission_text = (
                        form.cleaned_data['submission_text']
                    )
                    submission.status = 'submitted'
                    submission.submitted_at = timezone.now()
                    submission.is_late = is_overdue
                
                # Handle file upload
                if 'attachment' in request.FILES:
                    submission.attachment = request.FILES['attachment']
                
                submission.save()
                
                # Success message
                if is_overdue:
                    messages.warning(
                        request,
                        f'Assignment submitted successfully! '
                        f'Note: This is a late submission and may '
                        f'incur a {assignment.late_penalty_percent}% penalty.'
                    )
                else:
                    messages.success(
                        request,
                        'Assignment submitted successfully!'
                    )
                
                return redirect(
                    'students:assignment_detail',
                    course_slug=course_slug,
                    assignment_slug=assignment_slug
                )
                
            except Exception as e:
                messages.error(
                    request,
                    'Error submitting assignment. Please try again.'
                )
        else:
            messages.error(
                request,
                'Please correct the errors in the form.'
            )
    else:
        # GET request - redirect to detail page
        return redirect(
            'students:assignment_detail',
            course_slug=course_slug,
            assignment_slug=assignment_slug
        )
    
    # If form errors, redirect back with messages
    return redirect(
        'students:assignment_detail',
        course_slug=course_slug,
        assignment_slug=assignment_slug
    )


# ==================== QUIZZES ====================
@login_required
@student_required
def quiz_list(request):
    """
    List all quizzes with filtering and status
    """
    # Get filter parameter
    status_filter = request.GET.get('status', 'all')

    # Get enrolled course IDs
    enrolled_courses = Enrollment.objects.filter(
        student=request.user,
        status='active'
    ).values_list('course_id', flat=True)

    # Base queryset with optimization
    quizzes = Quiz.objects.filter(
        lesson__course_id__in=enrolled_courses,
        is_active=True
    ).select_related(
        'lesson',
        'lesson__course',
        'lesson__course__category'
    ).prefetch_related(
        'questions'
    ).order_by('-created_at')

    # Annotate with attempt information
    quiz_list = []
    for quiz in quizzes:
        # Get all attempts for this quiz
        attempts = QuizAttempt.objects.filter(
            quiz=quiz,
            student=request.user,
            is_completed=True
        )

        # Calculate statistics
        attempt_count = attempts.count()
        best_score = (
            attempts.aggregate(Max('percentage'))
            ['percentage__max'] or 0
        )
        latest_attempt = attempts.order_by(
            '-completed_at'
        ).first()

        # Determine status
        has_passed = attempts.filter(passed=True).exists()
        can_attempt = (
            quiz.max_attempts == 0 or
            attempt_count < quiz.max_attempts
        )

        # Determine quiz status
        if has_passed:
            quiz_status = 'passed'
        elif attempt_count > 0 and not can_attempt:
            quiz_status = 'failed'
        elif attempt_count > 0:
            quiz_status = 'pending'
        else:
            quiz_status = 'not_started'

        # Apply status filter
        if status_filter != 'all':
            if status_filter != quiz_status:
                continue

        # Add computed fields
        quiz.attempt_count = attempt_count
        quiz.best_score = best_score
        quiz.latest_attempt = latest_attempt
        quiz.has_passed = has_passed
        quiz.can_attempt = can_attempt
        quiz.quiz_status = quiz_status

        quiz_list.append(quiz)

    context = {
        'page_title': 'Quizzes',
        'quizzes': quiz_list,
        'status_filter': status_filter,
    }

    return render(request, 'students/quiz_list.html', context)


@login_required
@student_required
def quiz_detail(request, course_slug, lesson_slug, quiz_slug):
    """
    View quiz details using slug-based URL
    """
    # Get quiz with related data
    quiz = get_object_or_404(
        Quiz.objects.select_related(
            'lesson',
            'lesson__course',
            'lesson__course__category'
        ).prefetch_related('questions'),
        slug=quiz_slug,
        lesson__slug=lesson_slug,
        lesson__course__slug=course_slug
    )

    # Verify enrollment
    enrollment = get_object_or_404(
        Enrollment,
        student=request.user,
        course=quiz.lesson.course
    )

    # Get previous attempts
    attempts = QuizAttempt.objects.filter(
        quiz=quiz,
        student=request.user,
        is_completed=True
    ).select_related('quiz').order_by('-completed_at')

    # Check if can attempt
    attempt_count = attempts.count()
    can_attempt = (
        quiz.max_attempts == 0 or
        attempt_count < quiz.max_attempts
    )

    # Get best score
    best_score = (
        attempts.aggregate(Max('percentage'))
        ['percentage__max'] or 0
    )

    context = {
        'page_title': quiz.title,
        'quiz': quiz,
        'attempts': attempts,
        'attempt_count': attempt_count,
        'can_attempt': can_attempt,
        'best_score': best_score,
        'enrollment': enrollment,
    }

    return render(request, 'students/quiz_detail.html', context)


@login_required
@student_required
def quiz_take(request, course_slug, lesson_slug, quiz_slug):
    """
    Take quiz using slug-based URL
    """
    # Get quiz
    quiz = get_object_or_404(
        Quiz.objects.select_related(
            'lesson__course'
        ).prefetch_related('questions__answers'),
        slug=quiz_slug,
        lesson__slug=lesson_slug,
        lesson__course__slug=course_slug
    )

    # Verify enrollment
    enrollment = get_object_or_404(
        Enrollment,
        student=request.user,
        course=quiz.lesson.course,
        status='active'
    )

    # Check attempt limits
    attempts_count = QuizAttempt.objects.filter(
        quiz=quiz,
        student=request.user,
        is_completed=True
    ).count()

    if (
        quiz.max_attempts > 0 and
        attempts_count >= quiz.max_attempts
    ):
        messages.error(request, 'Maximum attempts reached.')
        return redirect(
            'students:quiz_detail',
            course_slug=course_slug,
            lesson_slug=lesson_slug,
            quiz_slug=quiz_slug
        )

    # Create new attempt
    attempt = QuizAttempt.objects.create(
        quiz=quiz,
        student=request.user,
        started_at=timezone.now()
    )

    # Get questions
    questions = quiz.questions.filter(
        is_active=True
    ).prefetch_related('answers').order_by('display_order')

    # Shuffle if enabled
    if quiz.shuffle_questions:
        questions = questions.order_by('?')

    context = {
        'page_title': f'Taking: {quiz.title}',
        'quiz': quiz,
        'attempt': attempt,
        'questions': questions,
        'course_slug': course_slug,
        'lesson_slug': lesson_slug,
        'quiz_slug': quiz_slug,
    }

    return render(request, 'students/quiz_take.html', context)


@login_required
@student_required
def quiz_submit(request, attempt_id):
    """
    Submit quiz answers
    """
    if request.method != 'POST':
        return redirect('students:quiz_list')

    # Get attempt
    attempt = get_object_or_404(
        QuizAttempt.objects.select_related(
            'quiz__lesson__course'
        ),
        id=attempt_id,
        student=request.user
    )

    # Check if already completed
    if attempt.is_completed:
        messages.warning(request, 'Quiz already submitted.')
        return redirect(
            'students:quiz_result',
            attempt_id=attempt_id
        )

    # Process answers
    total_score = Decimal('0.00')
    max_score = Decimal('0.00')

    for key, value in request.POST.items():
        if key.startswith('question_'):
            try:
                question_id = int(key.split('_')[1])
                question = attempt.quiz.questions.get(
                    id=question_id
                )
                max_score += question.points

                # Get selected answer
                selected_answer = QuizAnswer.objects.get(
                    id=int(value)
                )

                # Calculate points
                points_earned = (
                    question.points
                    if selected_answer.is_correct
                    else Decimal('0.00')
                )

                # Create response record
                QuizResponse.objects.create(
                    attempt=attempt,
                    question=question,
                    selected_answer=selected_answer,
                    is_correct=selected_answer.is_correct,
                    points_earned=points_earned
                )

                # Add to total score
                if selected_answer.is_correct:
                    total_score += question.points

            except (
                QuizAnswer.DoesNotExist,
                QuizQuestion.DoesNotExist,
                ValueError
            ):
                continue

    # Calculate percentage
    percentage = (
        (total_score / max_score * 100)
        if max_score > 0
        else Decimal('0.00')
    )

    # Calculate time taken
    time_delta = timezone.now() - attempt.started_at
    time_taken = int(time_delta.total_seconds() / 60)

    # Update attempt
    attempt.score = total_score
    attempt.max_score = max_score
    attempt.percentage = percentage
    attempt.passed = percentage >= attempt.quiz.passing_score
    attempt.is_completed = True
    attempt.completed_at = timezone.now()
    attempt.time_taken_minutes = time_taken
    attempt.save()

    messages.success(request, 'Quiz submitted successfully!')
    return redirect('students:quiz_result', attempt_id=attempt_id)


@login_required
@student_required
def quiz_result(request, attempt_id):
    """
    View quiz results
    """
    # Get attempt with related data
    attempt = get_object_or_404(
        QuizAttempt.objects.select_related(
            'quiz',
            'quiz__lesson',
            'quiz__lesson__course'
        ),
        id=attempt_id,
        student=request.user
    )

    # Get all responses with related data
    answers = attempt.responses.select_related(
        'question',
        'selected_answer'
    ).order_by('question__display_order')

    # Calculate statistics
    total_questions = answers.count()
    correct_answers = answers.filter(is_correct=True).count()
    incorrect_answers = total_questions - correct_answers

    context = {
        'page_title': 'Quiz Results',
        'attempt': attempt,
        'answers': answers,
        'total_questions': total_questions,
        'correct_answers': correct_answers,
        'incorrect_answers': incorrect_answers,
        'course_slug': attempt.quiz.lesson.course.slug,
        'lesson_slug': attempt.quiz.lesson.slug,
        'quiz_slug': attempt.quiz.slug,
    }

    return render(request, 'students/quiz_result.html', context)


# ==================== COMMUNITY & DISCUSSIONS ====================
@login_required
@student_required
def community(request):
    """
    Community discussion forum with filtering and search
    """
    user = request.user
    
    # Get filter and search parameters
    filter_type = request.GET.get('filter', 'all')
    search_query = request.GET.get('q', '').strip()
    
    # Base queryset with optimizations
    threads = Discussion.objects.select_related(
        'author',
        'course'
    ).annotate(
        reply_count=Count('replies'),
        views=F('views_count')
    )
    
    # Apply filters
    if filter_type == 'my_courses':
        # Show discussions from user's enrolled courses
        enrolled_course_ids = Enrollment.objects.filter(
            student=user,
            status='active'
        ).values_list('course_id', flat=True)
        threads = threads.filter(course_id__in=enrolled_course_ids)
    elif filter_type == 'my_posts':
        # Show user's own discussions
        threads = threads.filter(author=user)
    
    # Apply search
    if search_query:
        threads = threads.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query)
        )
    
    # Order threads
    threads = threads.order_by('-is_pinned', '-created_at')
    
    # Paginate
    paginator = Paginator(threads, 15)
    page_number = request.GET.get('page', 1)
    
    try:
        threads = paginator.get_page(page_number)
    except Exception:
        threads = paginator.get_page(1)
    
    context = {
        'page_title': 'Community',
        'threads': threads,
        'filter_type': filter_type,
        'search_query': search_query,
    }
    
    return render(request, 'students/community.html', context)


@login_required
@student_required
def thread_detail(request, thread_id):
    """
    View individual discussion thread with replies
    """
    thread = get_object_or_404(
        Discussion.objects.select_related('author', 'course'),
        id=thread_id
    )
    
    # Increment view count
    thread.views_count = F('views_count') + 1
    thread.save(update_fields=['views_count'])
    thread.refresh_from_db()
    
    # Get replies
    replies = thread.replies.select_related(
        'author'
    ).order_by('created_at')
    
    # Handle new reply with form
    if request.method == 'POST':
        form = ReplyCreateForm(request.POST)
        
        if form.is_valid():
            reply = form.save(commit=False)
            reply.discussion = thread
            reply.author = request.user
            reply.save()
            
            messages.success(request, 'Reply posted successfully!')
            return redirect('students:thread_detail', thread_id=thread_id)
    else:
        form = ReplyCreateForm()
    
    context = {
        'page_title': thread.title,
        'thread': thread,
        'replies': replies,
        'reply_form': form,
    }
    
    return render(request, 'students/thread_detail.html', context)


@login_required
@student_required
def create_thread(request):
    """
    Create a new discussion thread using Django form
    """
    if request.method == 'POST':
        form = ThreadCreateForm(
            user=request.user,
            data=request.POST
        )
        
        if form.is_valid():
            thread = form.save(commit=False)
            thread.author = request.user
            thread.save()
            
            messages.success(
                request,
                'Discussion created successfully!'
            )
            return redirect('students:thread_detail', thread_id=thread.id)
    else:
        form = ThreadCreateForm(user=request.user)
    
    context = {
        'page_title': 'Create Discussion',
        'form': form,
    }
    
    return render(request, 'students/create_thread.html', context)


# ==================== STUDY GROUPS ====================
@login_required
@student_required
def study_groups(request):
    """
    List study groups - user's groups and available groups
    """
    user = request.user
    
    # Get user's study groups
    my_group_ids = StudyGroupMember.objects.filter(
        user=user,
        is_active=True
    ).values_list('study_group_id', flat=True)
    
    my_groups = StudyGroup.objects.filter(
        id__in=my_group_ids,
        is_active=True
    ).select_related('course').annotate(
        member_count=Count(
            'members',
            filter=Q(members__is_active=True)
        )
    )
    
    # Get available groups (not full, public, not already joined)
    available_groups = StudyGroup.objects.filter(
        is_active=True,
        is_public=True
    ).exclude(
        id__in=my_group_ids
    ).select_related('course').annotate(
        member_count=Count(
            'members',
            filter=Q(members__is_active=True)
        )
    ).order_by('-created_at')
    
    # Annotate whether each group is full
    for group in available_groups:
        group.is_full = group.member_count >= group.max_members
    
    context = {
        'page_title': 'Study Groups',
        'my_groups': my_groups,
        'available_groups': available_groups,
    }
    
    return render(request, 'students/study_groups.html', context)


@login_required
@student_required
def study_group_detail(request, group_id):
    """
    View study group details and members
    """
    group = get_object_or_404(
        StudyGroup.objects.select_related('course', 'created_by'),
        id=group_id
    )
    
    # Check if user is a member
    is_member = StudyGroupMember.objects.filter(
        study_group=group,
        user=request.user,
        is_active=True
    ).exists()
    
    # Get members
    members = group.members.filter(
        is_active=True
    ).select_related('user')
    
    # Handle message form (only for members)
    if request.method == 'POST' and is_member:
        form = StudyGroupMessageForm(request.POST)
        
        if form.is_valid():
            # Here you would save the message to a GroupMessage model
            # For now, just show success
            messages.success(request, 'Message posted successfully!')
            return redirect(
                'students:study_group_detail',
                group_id=group_id
            )
    else:
        form = StudyGroupMessageForm()
    
    context = {
        'page_title': group.name,
        'group': group,
        'is_member': is_member,
        'members': members,
        'member_count': members.count(),
        'message_form': form if is_member else None,
    }
    
    return render(request, 'students/study_group_detail.html', context)


@login_required
@student_required
def join_study_group(request, group_id):
    """
    Join a study group
    """
    if request.method != 'POST':
        return redirect('students:study_groups')
    
    group = get_object_or_404(
        StudyGroup,
        id=group_id,
        is_active=True
    )
    
    # Check if already a member
    existing = StudyGroupMember.objects.filter(
        study_group=group,
        user=request.user
    ).first()
    
    if existing and existing.is_active:
        messages.info(
            request,
            'You are already a member of this group.'
        )
        return redirect(
            'students:study_group_detail',
            group_id=group_id
        )
    
    # Check if group is full
    current_count = group.members.filter(is_active=True).count()
    if current_count >= group.max_members:
        messages.error(request, 'This study group is full.')
        return redirect('students:study_groups')
    
    # Join group
    if existing:
        existing.is_active = True
        existing.save()
    else:
        StudyGroupMember.objects.create(
            study_group=group,
            user=request.user,
            role='member'
        )
    
    messages.success(
        request,
        f'Successfully joined {group.name}!'
    )
    return redirect('students:study_group_detail', group_id=group_id)

# ==================== ACHIEVEMENTS ====================
@login_required
@student_required
def achievements(request):
    """
    View achievements and badges with statistics
    """
    user = request.user
    
    # Get user's earned badges
    user_badges = (
        StudentBadge.objects
        .filter(student=user)
        .select_related('badge')
        .order_by('-awarded_at')
    )
    
    # Get all available badges
    all_badges = Badge.objects.filter(is_active=True)
    
    # Separate earned and unearned badges
    earned_badge_ids = user_badges.values_list('badge_id', flat=True)
    unearned_badges = all_badges.exclude(id__in=earned_badge_ids)
    
    # Calculate completed courses
    completed_courses = Enrollment.objects.filter(
        student=user,
        status='completed'
    ).count()
    
    # Calculate total points from badges
    total_points = user_badges.aggregate(
        total=Sum('badge__points')
    )['total'] or 0
    
    context = {
        'page_title': 'Achievements',
        'user_badges': user_badges,
        'unearned_badges': unearned_badges,
        'completed_courses': completed_courses,
        'total_points': total_points,
    }
    
    return render(request, 'students/achievements.html', context)


# ==================== GRADES ====================
@login_required
@student_required
def grades(request):
    """
    View grades and performance across all courses
    """
    user = request.user
    
    # Get all enrollments with optimized queries
    enrollments = (
        Enrollment.objects
        .filter(student=user)
        .select_related('course', 'course__instructor')
        .prefetch_related('course__lessons')
        .order_by('-enrolled_at')
    )
    
    # Add progress data to each enrollment
    for enrollment in enrollments:
        # Get completed lessons count
        completed_count = LessonProgress.objects.filter(
            enrollment=enrollment,
            is_completed=True
        ).count()
        
        total_lessons = enrollment.course.lessons.filter(
            is_active=True
        ).count()
        
        # Calculate progress percentage
        enrollment.completed_lessons = completed_count
        enrollment.progress_percentage = (
            (completed_count / total_lessons * 100) 
            if total_lessons > 0 
            else 0
        )
        
        # Get current grade (average of graded assignments)
        from django.db.models import FloatField
        grade_data = AssignmentSubmission.objects.filter(
            student=user,
            assignment__lesson__course=enrollment.course,
            status='graded',
            score__isnull=False
        ).aggregate(
            avg_score=Avg(
                F('score') * 100.0 / F('assignment__max_score'),
                output_field=FloatField()
            )
        )
        
        enrollment.current_grade = grade_data['avg_score']
    
    # Get graded assignment submissions
    submissions = (
        AssignmentSubmission.objects
        .filter(student=user, status='graded')
        .select_related(
            'assignment',
            'assignment__lesson',
            'assignment__lesson__course'
        )
        .order_by('-graded_at')
    )
    
    # Add passed status to submissions
    for submission in submissions:
        submission.passed = (
            submission.score >= submission.assignment.passing_score
            if submission.score is not None
            else False
        )
    
    context = {
        'page_title': 'Grades & Performance',
        'enrollments': enrollments,
        'submissions': submissions,
    }
    
    return render(request, 'students/grades.html', context)


# ==================== PROGRESS ====================
@login_required
@student_required
def progress(request):
    """
    View detailed learning progress across all courses
    """
    user = request.user
    
    # Get all enrollments with related data
    enrollments = (
        Enrollment.objects
        .filter(student=user)
        .select_related('course', 'course__instructor')
        .prefetch_related(
            'course__sections',
            'course__sections__lessons',
            'course__lessons'
        )
        .order_by('-enrolled_at')
    )
    
    # Add detailed progress data to each enrollment
    for enrollment in enrollments:
        # Get completed lessons
        completed_progress = LessonProgress.objects.filter(
            enrollment=enrollment,
            is_completed=True
        ).values_list('lesson_id', flat=True)
        
        enrollment.completed_lesson_ids = set(completed_progress)
        
        # Count completed lessons
        enrollment.completed_lessons = len(completed_progress)
        
        # Calculate progress percentage
        total_lessons = enrollment.course.lessons.filter(
            is_active=True
        ).count()
        
        enrollment.progress_percentage = (
            (enrollment.completed_lessons / total_lessons * 100) 
            if total_lessons > 0 
            else 0
        )
        
        # Add section progress
        for section in enrollment.course.sections.all():
            section_lessons = section.lessons.filter(is_active=True)
            total = section_lessons.count()
            completed = sum(
                1 for lesson in section_lessons 
                if lesson.id in enrollment.completed_lesson_ids
            )
            section.progress_percentage = (
                (completed / total * 100) if total > 0 else 0
            )
            section.total_lessons = total
    
    # Calculate learning activity for last 28 days
    from datetime import datetime, timedelta
    today = timezone.now().date()
    start_date = today - timedelta(days=27)  # 28 days including today
    
    activity_data = []
    for i in range(28):
        date = start_date + timedelta(days=i)
        
        # Count activities for this day
        lessons_completed = LessonProgress.objects.filter(
            enrollment__student=user,
            completed_at__date=date
        ).count()
        
        assignments_submitted = AssignmentSubmission.objects.filter(
            student=user,
            submitted_at__date=date
        ).count()
        
        quizzes_taken = QuizAttempt.objects.filter(
            student=user,
            started_at__date=date
        ).count()
        
        # Calculate activity level (0-3)
        total_activities = (
            lessons_completed + 
            assignments_submitted + 
            quizzes_taken
        )
        
        if total_activities == 0:
            level = 0
        elif total_activities <= 2:
            level = 1
        elif total_activities <= 5:
            level = 2
        else:
            level = 3
        
        activity_data.append({
            'date': date,
            'level': level,
            'count': total_activities,
            'lessons': lessons_completed,
            'assignments': assignments_submitted,
            'quizzes': quizzes_taken,
        })
    
    context = {
        'page_title': 'My Progress',
        'enrollments': enrollments,
        'activity_data': activity_data,
    }
    
    return render(request, 'students/progress.html', context)


# ==================== CERTIFICATES ====================
@login_required
@student_required
def certificates(request):
    """
    List all earned certificates
    """
    user = request.user
    
    # Get all certificates with course data
    certificates = (
        Certificate.objects
        .filter(student=user)
        .select_related('course', 'course__instructor')
        .order_by('-issued_date')
    )
    
    # Add instructor name to each certificate
    for cert in certificates:
        if hasattr(cert.course, 'instructor'):
            cert.course.instructor_name = (
                cert.course.instructor.get_full_name() 
                or cert.course.instructor.username
            )
        else:
            cert.course.instructor_name = 'MIU Staff'
    
    context = {
        'page_title': 'My Certificates',
        'certificates': certificates,
    }
    
    return render(request, 'students/certificates.html', context)


# ==================== PROFILE & SETTINGS ====================
@login_required
@student_required
def profile(request):
    """
    View and edit user profile using Django form
    """
    user = request.user
    profile = user.profile
    
    # Get statistics for sidebar
    stats = {
        'total_enrolled': Enrollment.objects.filter(
            student=user
        ).count(),
        'completed_courses': Enrollment.objects.filter(
            student=user,
            status='completed'
        ).count(),
        'certificates_earned': Certificate.objects.filter(
            student=user
        ).count(),
        'total_hours': 0,  # Calculate from lesson progress
    }
    
    if request.method == 'POST':
        form = ProfileUpdateForm(
            request.POST,
            request.FILES,
            instance=profile
        )
        
        if form.is_valid():
            # Update user fields
            user.first_name = form.cleaned_data.get('first_name', '')
            user.last_name = form.cleaned_data.get('last_name', '')
            user.email = form.cleaned_data.get('email', '')
            user.save()
            
            # Update profile
            form.save()
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('students:profile')
    else:
        # Populate form with current data
        initial_data = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
        }
        form = ProfileUpdateForm(instance=profile, initial=initial_data)
    
    context = {
        'page_title': 'My Profile',
        'form': form,
        **stats,
    }
    
    return render(request, 'students/profile.html', context)


@login_required
@student_required
def settings(request):
    """
    Account settings and preferences using Django form
    """
    user = request.user
    profile = user.profile
    
    if request.method == 'POST':
        form = SettingsForm(request.POST, instance=profile)
        
        if form.is_valid():
            form.save()
            
            # Handle password change
            current_password = request.POST.get(
                'current_password',
                ''
            ).strip()
            new_password = request.POST.get('new_password', '').strip()
            confirm_password = request.POST.get(
                'confirm_password',
                ''
            ).strip()
            
            if current_password and new_password:
                if not user.check_password(current_password):
                    messages.error(
                        request,
                        'Current password is incorrect.'
                    )
                elif new_password != confirm_password:
                    messages.error(
                        request,
                        'New passwords do not match.'
                    )
                elif len(new_password) < 8:
                    messages.error(
                        request,
                        'Password must be at least 8 characters.'
                    )
                else:
                    user.set_password(new_password)
                    user.save()
                    messages.success(
                        request,
                        'Password updated successfully! '
                        'Please login again.'
                    )
                    return redirect('eduweb:auth_page')
            
            if not (current_password and new_password):
                messages.success(
                    request,
                    'Settings updated successfully!'
                )
            
            return redirect('students:settings')
    else:
        form = SettingsForm(instance=profile)
    
    context = {
        'page_title': 'Settings',
        'form': form,
    }
    
    return render(request, 'students/settings.html', context)

@login_required
@student_required
def help_support(request):
    """Help and support page with FAQs and ticket submission"""
    
    if request.method == 'POST':
        form = StudentSupportTicketForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Get current course if student is enrolled
            current_course = None
            enrollments = Enrollment.objects.filter(
                student=request.user,
                status='active'
            ).first()
            
            if enrollments:
                current_course = enrollments.course.title
            
            # Send email to support team
            subject = (
                f"[STUDENT-{form.cleaned_data['priority'].upper()}] "
                f"{form.cleaned_data['subject']}"
            )
            
            message = f"""
New Support Ticket from Student

From: {request.user.get_full_name()} ({request.user.email})
Student ID: {request.user.id}
Current Course: {current_course or 'None'}
Category: {form.cleaned_data['category']}
Priority: {form.cleaned_data['priority']}

Message:
{form.cleaned_data['message']}

---
User Role: Student
Submission Time: {timezone.now()}
            """
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.SUPPORT_EMAIL],
                    fail_silently=False,
                )
                
                messages.success(
                    request,
                    'Your support ticket has been submitted! '
                    'Our team will get back to you within 24-48 hours.'
                )
                return redirect('students:help_support')
            
            except Exception as e:
                messages.error(
                    request,
                    'An error occurred while submitting your ticket. '
                    'Please try again later.'
                )
    else:
        form = StudentSupportTicketForm()
    
    # Student-specific FAQs
    faqs = [
        {
            'question': 'How do I enroll in a course?',
            'answer': (
                'Go to Browse Catalog, find the course you want, '
                'and click the Enroll button. Some courses may '
                'require payment before enrollment.'
            )
        },
        {
            'question': 'How do I submit an assignment?',
            'answer': (
                'Navigate to the Assignments page, select the '
                'assignment, and use the submission form to upload '
                'your work. Make sure to submit before the deadline!'
            )
        },
        {
            'question': 'Can I retake a quiz?',
            'answer': (
                'This depends on the course settings. Some quizzes '
                'allow multiple attempts while others are one-time. '
                'Check the quiz instructions for details.'
            )
        },
        {
            'question': 'How do I track my progress?',
            'answer': (
                'Visit your Dashboard or the Progress page to see '
                'completion rates, grades, and overall performance '
                'across all your enrolled courses.'
            )
        },
        {
            'question': 'When will I receive my certificate?',
            'answer': (
                'Certificates are issued automatically when you '
                'complete all course requirements and achieve the '
                'passing grade. Check the Certificates page.'
            )
        },
        {
            'question': 'How do I contact my instructor?',
            'answer': (
                'You can post questions in the course discussion '
                'forum, or use the messaging feature to contact '
                'your instructor directly.'
            )
        },
        {
            'question': 'What if I miss a deadline?',
            'answer': (
                'Contact your instructor immediately. Some '
                'assignments allow late submissions with a penalty. '
                'Extensions are at the instructor\'s discretion.'
            )
        },
        {
            'question': 'How do I join a study group?',
            'answer': (
                'Go to Study Groups, browse available groups, and '
                'click Join. You can also create your own study '
                'group for others to join.'
            )
        },
    ]
    
    # Quick links for students
    quick_links = [
        {
            'title': 'Getting Started Guide',
            'icon': 'fa-rocket',
            'url': '#',
            'description': 'New to the platform? Start here'
        },
        {
            'title': 'Video Tutorials',
            'icon': 'fa-video',
            'url': '#',
            'description': 'Watch step-by-step guides'
        },
        {
            'title': 'Study Tips',
            'icon': 'fa-lightbulb',
            'url': '#',
            'description': 'Learn effective study strategies'
        },
        {
            'title': 'Community Forum',
            'icon': 'fa-users',
            'url': '#',
            'description': 'Connect with fellow students'
        },
    ]
    
    context = {
        'form': form,
        'faqs': faqs,
        'quick_links': quick_links,
        'page_title': 'Help & Support',
    }
    
    return render(request, 'students/help_support.html', context)