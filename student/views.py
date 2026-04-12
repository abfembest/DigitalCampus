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
    StudentBadge, LessonSection,
    Message, Notification, Review, StudyGroupMessage,
    FeePayment, CourseGrade, CourseApplication,Exam, StudentExamResponse
)

from .forms import AssignmentSubmissionForm, SettingsForm, ProfileUpdateForm, ReplyCreateForm, ThreadCreateForm, StudyGroupMessageForm, StudentSupportTicketForm

from django.core.mail import send_mail
from django.conf import settings


def student_required(view_func):
    """Decorator to ensure only students with approved portal access can access"""
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

        # Block access if application hasn't been approved yet
        from eduweb.models import CourseApplication
        application = CourseApplication.objects.filter(user=request.user).first()
        if not application or not application.can_access_student_portal():
            messages.warning(
                request,
                'Your application is still being processed. You cannot access the student portal yet.'
            )
            if application:
                return redirect('eduweb:application_status')
            return redirect('eduweb:apply')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# ==================== NOTIFICATION HELPER ====================

def _notify(user, notification_type, title, message, link=''):
    """
    Create a Notification for a student. Silently fails so it never
    breaks the main action. Auto-purges notifications older than 30 days.
    """
    try:
        Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            link=link,
        )
        cutoff = timezone.now() - timedelta(days=30)
        Notification.objects.filter(user=user, created_at__lt=cutoff).delete()
    except Exception:
        pass

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
        
        # Get pending assignments
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
        
        # ===== NEW: Get admission history =====
        from eduweb.models import CourseApplication
        
        admission_history = (
            CourseApplication.objects
            .filter(
                Q(user=user) | Q(email=user.email)
            )
            .select_related('program', 'program__department__faculty', 'intake')
            .order_by('-created_at')[:5]
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
        admission_history = []
        stats = {
            'total_enrolled': 0,
            'completed_courses': 0,
            'certificates_earned': 0,
        }
    
    # Outstanding fees for the dashboard alert button
    try:
        outstanding_items, _ = _get_outstanding_for_student(user)
        outstanding_count = len(outstanding_items)
        outstanding_total = sum(
            (item['payment']['amount'] if isinstance(item['payment'], dict) else item['payment'].amount)
            for item in outstanding_items
        )
        # Derive currency from first outstanding item; fall back to USD
        _first = outstanding_items[0]['payment'] if outstanding_items else None
        outstanding_currency = (
            _first.get('currency', 'USD') if isinstance(_first, dict)
            else getattr(_first, 'currency', 'USD')
        ) if _first else 'USD'
    except Exception:
        outstanding_count = 0
        outstanding_total = Decimal('0.00')
        outstanding_currency = 'USD'

    context = {
        'page_title': 'My Dashboard',
        'enrollments': enrollments,
        'pending_assignments': pending_assignments,
        'announcements': announcements,
        'admission_history': admission_history,
        'total_enrolled': stats['total_enrolled'],
        'completed_courses': stats['completed_courses'],
        'certificates_earned': stats['certificates_earned'],
        'outstanding_count': outstanding_count,
        'outstanding_total': outstanding_total,
        'outstanding_currency': outstanding_currency,
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
        
        existing_review = None
        if enrollment:
            existing_review = Review.objects.filter(
                course=course,
                student=request.user
            ).first()

        context = {
            'page_title': course.title,
            'course': course,
            'enrollment': enrollment,
            'sections': sections,
            'existing_review': existing_review,
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
    Enroll in a course.
    All LMS courses are free — enrollment is immediate.
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
    
    # All courses are free — enroll directly
    try:
        Enrollment.objects.create(
            student=request.user,
            course=course,
            status='active',
            enrolled_at=timezone.now()
        )
        messages.success(
            request,
            f'Successfully enrolled in {course.title}!'
        )
        _notify(
            user=request.user,
            notification_type='enrollment',
            title=f'Enrolled in {course.title}',
            message=f'You have successfully enrolled in "{course.title}". Start learning now!',
            link=f'/student/courses/{course.slug}/',
        )
    except Exception as e:
        messages.error(
            request,
            'An error occurred during enrollment. Please try again.'
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
    
    # Verify enrollment — preview lessons are accessible without enrollment
    enrollment = Enrollment.objects.filter(
        student=request.user,
        course=lesson.course,
        status__in=['active', 'completed']
    ).first()

    if not enrollment and not lesson.is_preview:
        messages.error(request, 'You must be enrolled to access this lesson.')
        return redirect('students:course_detail', course_slug=course_slug)

    # Track progress only for enrolled students
    progress = None
    if enrollment:
        progress, created = LessonProgress.objects.get_or_create(
            enrollment=enrollment,
            lesson=lesson,
            defaults={'last_accessed': timezone.now()}
        )
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

    # Get completed lesson IDs — only meaningful if enrolled
    completed_lesson_ids = set()
    if enrollment:
        completed_lesson_ids = set(
            LessonProgress.objects.filter(
                enrollment=enrollment,
                is_completed=True
            ).values_list('lesson_id', flat=True)
        )

    # Add completion status to all lessons
    for l in all_lessons:
        l.is_completed = l.id in completed_lesson_ids

    # Find current lesson index for prev/next navigation
    try:
        current_index = next(
            i for i, l in enumerate(all_lessons)
            if l.id == lesson.id
        )
    except StopIteration:
        current_index = None

    prev_lesson = None
    next_lesson = None
    if current_index is not None:
        if current_index > 0:
            prev_lesson = all_lessons[current_index - 1]
        if current_index < len(all_lessons) - 1:
            next_lesson = all_lessons[current_index + 1]

    # Attach completed count to enrollment object if enrolled
    if enrollment:
        enrollment.completed_lessons = len(completed_lesson_ids)

    context = {
        'page_title': lesson.title,
        'lesson': lesson,
        'enrollment': enrollment,
        'progress': progress,
        'prev_lesson': prev_lesson,
        'next_lesson': next_lesson,
    }

    return render(request, 'students/lesson.html', context)

def _score_to_grade(percentage):
    """Convert numeric percentage to letter grade."""
    if percentage >= 70:   return 'A'
    elif percentage >= 60: return 'B'
    elif percentage >= 50: return 'C'
    elif percentage >= 45: return 'D'
    else:                  return 'F'


def _record_academic_grade(user, enrollment, lms_course):
    """
    Automatically record a CourseGrade when a linked LMS course is completed.
    Derives score from quiz attempts and graded assignment submissions
    in this course. Falls back to 0 if no assessments exist yet.
    Uses the current active AcademicSession.
    """
    from eduweb.models import AcademicSession, CourseApplication

    academic_course = lms_course.academic_course
    session = AcademicSession.get_current()
    if not session:
        return  # No active session — grade cannot be pinned to a session yet

    # ── Quiz score: best attempt percentage per quiz in this course ───────
    quiz_attempts = (
        QuizAttempt.objects
        .filter(
            student=user,
            quiz__lesson__course=lms_course,
            is_completed=True,
        )
        .values('quiz_id')
        .annotate(best=Max('percentage'))
    )
    quiz_scores = [float(row['best']) for row in quiz_attempts]

    # ── Assignment score: graded submissions as percentage of max_score ───
    from django.db.models import FloatField
    assignment_scores_qs = (
        AssignmentSubmission.objects
        .filter(
            student=user,
            assignment__lesson__course=lms_course,
            status='graded',
            score__isnull=False,
        )
        .annotate(
            pct=F('score') * 100.0 / F('assignment__max_score')
        )
        .values_list('pct', flat=True)
    )
    assignment_scores = [float(s) for s in assignment_scores_qs]

    # ── Combined average ──────────────────────────────────────────────────
    all_scores = quiz_scores + assignment_scores
    if all_scores:
        avg_score = sum(all_scores) / len(all_scores)
    else:
        # No assessments graded yet — use lesson completion as proxy (100%)
        avg_score = float(enrollment.progress_percentage)

    letter_grade = _score_to_grade(avg_score)
    is_passed = avg_score >= 50  # configurable threshold

    # ── Link to CourseApplication if available ────────────────────────────
    application = (
        CourseApplication.objects
        .filter(user=user, program=academic_course.program)
        .first()
    )

    # ── Create or update CourseGrade ──────────────────────────────────────
    CourseGrade.objects.update_or_create(
        student=user,
        course=academic_course,
        session=session,
        defaults={
            'score':        round(avg_score, 2),
            'grade':        letter_grade,
            'credit_units': academic_course.credit_units,
            'is_passed':    is_passed,
            'application':  application,
            'recorded_by':  None,
        }
    )

    # Check if student has now completed all core courses in the program
    if application:
        application.award_program_certificate()

@login_required
@student_required
def certificate_print(request, certificate_id):
    cert = get_object_or_404(
        Certificate,
        certificate_id=certificate_id,
        student=request.user,
    )
    # Redirect to payment if not yet unlocked
    if cert.payment_status != 'paid':
        messages.warning(request, 'Please complete payment to access your certificate.')
        return redirect('students:my_payments')

    if cert.certificate_type == 'program' and cert.program:
        cert.display_title = cert.program.name
        cert.display_subtitle = (
            cert.program.department.faculty.name
            if cert.program.department else ''
        )
        cert.issuer = 'MIU Academic Office'
        cert.is_program_cert = True
    else:
        cert.display_title = cert.course.title if cert.course else 'Course Certificate'
        cert.display_subtitle = ''
        cert.is_program_cert = False
        cert.issuer = (
            cert.course.instructor.get_full_name()
            if cert.course and cert.course.instructor else 'MIU Staff'
        )

    return render(request, 'students/certificate_print.html', {'cert': cert})

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
    
    # Verify enrollment — allow preview lessons for non-enrolled students
    enrollment = Enrollment.objects.filter(
        student=request.user,
        course=lesson.course,
        status__in=['active', 'completed']
    ).first()

    if not enrollment and not lesson.is_preview:
        messages.error(request, 'You must be enrolled to access this lesson.')
        return redirect('students:course_detail', course_slug=course_slug)
    
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
                enrollment.refresh_from_db()
                # Notify when the entire course is completed
                if enrollment.status == 'completed':
                    lms_course = enrollment.course

                    if lms_course.academic_course_id:
                        # Linked to an academic Course — record grade automatically
                        _record_academic_grade(request.user, enrollment, lms_course)
                        _notify(
                            user=request.user,
                            notification_type='enrollment',
                            title=f'Unit Completed: {lms_course.title}',
                            message=f'You have completed \"{lms_course.title}\". '
                                    f'Your academic grade has been recorded.',
                            link='/student/grades/',
                        )
                    else:
                        # Standalone LMS course — issue individual certificate
                        if lms_course.has_certificate:
                            cert, created = Certificate.objects.get_or_create(
                                student=request.user,
                                course=lms_course,
                                certificate_type='lms_course',
                                defaults={
                                    'completion_date': timezone.now().date(),
                                    'payment_status': 'unpaid' if lms_course.certificate_fee > 0 else 'paid',
                                }
                            )
                            _notify(
                                user=request.user,
                                notification_type='enrollment',
                                title=f'Course Completed: {lms_course.title}',
                                message=f'Congratulations! You have completed \"{lms_course.title}\". '
                                        + ('Pay your certificate fee to download your certificate.' if lms_course.certificate_fee > 0 else 'Your certificate is ready to download.'),
                                link='/student/certificates/',
                            )

        return JsonResponse({
            'success': True,
            'message': 'Lesson marked as complete',
            'progress': float(enrollment.progress_percentage),
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
            
            if not assignment.submission or assignment.submission.status == 'draft':
                assignment._is_overdue_override = timezone.now() > assignment.due_date
            else:
                assignment._is_overdue_override = False
                
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
                _notify(
                    user=request.user,
                    notification_type='assignment',
                    title=f'Assignment Submitted: {assignment.title}',
                    message=(
                        f'Your submission for "{assignment.title}" has been received'
                        + (' (late submission — a penalty may apply).' if is_overdue
                           else '. You will be notified when it is graded.')
                    ),
                    link=f'/student/courses/{course_slug}/assignments/{assignment_slug}/',
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

    passed_label = 'Passed ✓' if attempt.passed else 'Not passed'
    _notify(
        user=request.user,
        notification_type='grade',
        title=f'Quiz Result: {attempt.quiz.title}',
        message=f'You scored {attempt.percentage:.1f}% on "{attempt.quiz.title}" — {passed_label}.',
        link=f'/student/quizzes/attempt/{attempt_id}/result/',
    )
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
        'attempt_count': QuizAttempt.objects.filter(
            quiz=attempt.quiz,
            student=request.user,
            is_completed=True
        ).count(),
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
            # Notify thread author if they are not the one replying
            if thread.author != request.user:
                _notify(
                    user=thread.author,
                    notification_type='message',
                    title=f'New Reply on Your Thread: {thread.title}',
                    message=(
                        f'{request.user.get_full_name() or request.user.username} '
                        f'replied to your discussion "{thread.title}".'
                    ),
                    link=f'/student/community/thread/{thread_id}/',
                )
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
            _notify(
                user=request.user,
                notification_type='announcement',
                title=f'Discussion Created: {thread.title}',
                message=f'Your discussion thread "{thread.title}" is now live in the community.',
                link=f'/student/community/thread/{thread.id}/',
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
            StudyGroupMessage.objects.create(
                study_group=group,
                author=request.user,
                content=form.cleaned_data['message']
            )
            messages.success(request, 'Message posted!')
            # Notify all other group members of a new message
            other_members = StudyGroupMember.objects.filter(
                study_group=group,
                is_active=True,
            ).exclude(user=request.user).select_related('user')
            for member in other_members:
                _notify(
                    user=member.user,
                    notification_type='message',
                    title=f'New Message in {group.name}',
                    message=f'{request.user.get_full_name() or request.user.username} posted in "{group.name}".',
                    link=f'/student/study-groups/{group_id}/',
                )
            return redirect('students:study_group_detail', group_id=group_id)
        messages.error(request, 'Please enter a valid message.')
    else:
        form = StudyGroupMessageForm()

    # Fetch group messages (latest 50)
    group_messages = (
        StudyGroupMessage.objects
        .filter(study_group=group)
        .select_related('author')
        .order_by('created_at')[:50]
    )
    
    member_count = members.count()
    context = {
        'page_title': group.name,
        'group': group,
        'is_member': is_member,
        'members': members,
        'member_count': member_count,
        'available_slots': group.max_members - member_count,
        'message_form': form if is_member else None,
        'group_messages': group_messages if is_member else [],
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
    _notify(
        user=request.user,
        notification_type='system',
        title=f'Joined Study Group: {group.name}',
        message=f'You are now a member of the study group "{group.name}". '
                f'Connect and collaborate with other students.',
        link=f'/student/study-groups/{group_id}/',
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
    
    # Academic course grades (from program — recorded by lecturers)
    academic_grades = (
        CourseGrade.objects
        .filter(student=user)
        .select_related('course', 'course__program', 'session')
        .order_by('session__name', 'course__year_of_study', 'course__semester')
    )

    context = {
        'page_title': 'Grades & Performance',
        'enrollments': enrollments,
        'submissions': submissions,
        'academic_grades': academic_grades,
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

        enrollment.assignment_count = Assignment.objects.filter(
            lesson__course=enrollment.course
        ).count()
        enrollment.quiz_count = Quiz.objects.filter(
            lesson__course=enrollment.course
        ).count()
    
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
        'completed_count': sum(1 for e in enrollments if e.status == 'completed'),
        'active_count': sum(1 for e in enrollments if e.status == 'active'),
    }
    
    return render(request, 'students/progress.html', context)


# ==================== CERTIFICATES ====================
@login_required
@student_required
def certificates(request):
    """
    List all earned certificates (LMS course + academic program).
    Each certificate is gated by its own payment_status field.
    """
    user = request.user

    # Get all certificates — LMS and program — with their related objects
    certificates = (
        Certificate.objects
        .filter(student=user)
        .select_related('course', 'course__instructor', 'program', 'program__department')
        .order_by('-issued_date')
    )

    # Annotate each cert with a display label and instructor name
    for cert in certificates:
        if cert.certificate_type == 'program' and cert.program:
            cert.display_title = cert.program.name
            cert.display_subtitle = (
                cert.program.department.faculty.name
                if cert.program.department else ''
            )
            cert.instructor_name = 'MIU Academic Office'
            cert.is_program_cert = True
        else:
            cert.display_title = cert.course.title if cert.course else 'Course Certificate'
            cert.display_subtitle = ''
            cert.is_program_cert = False
            if cert.course and cert.course.instructor:
                cert.instructor_name = (
                    cert.course.instructor.get_full_name()
                    or cert.course.instructor.username
                )
            else:
                cert.instructor_name = 'MIU Staff'
        cert.is_unlocked = cert.payment_status == 'paid'

    context = {
        'page_title': 'My Certificates',
        'certificates': certificates,
    }

    return render(request, 'students/certificates.html', context)


def _cert_is_unlocked(cert):
    """True if student can view/download this certificate."""
    return cert.payment_status == 'paid'


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
                _notify(
                    user=request.user,
                    notification_type='system',
                    title='Support Ticket Submitted',
                    message=f'Your ticket "{form.cleaned_data["subject"]}" has been received. We will respond within 24-48 hours.',
                    link='/student/help-support/',
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

def _get_outstanding_for_student(user):
    """
    Returns (outstanding, paid) for a student's required fees.

    Includes:
    1. FeePayment rows for the student's program (auto-created on program assignment)
    2. Auto-generated certificate fees for any completed courses that have
       has_certificate=True and no certificate fee has been paid yet.

    outstanding → list of dicts: {'payment': AllRequiredPayments or dict, 'fee_payment': FeePayment or None, 'is_overdue': bool, 'is_certificate_fee': bool}
    paid        → list of AllRequiredPayments instances already settled
    """
    from eduweb.models import AllRequiredPayments, Enrollment, FeePayment, Certificate

    profile = getattr(user, 'profile', None)
    if not profile or not profile.program:
        return [], []

    # ── 1. Read directly from FeePayment rows (auto-created by signal) ───────
    student_payments = (
        FeePayment.objects
        .filter(
            user=user,
            fee__program=profile.program,
            fee__who_to_pay='student',
            fee__is_active=True,
        )
        .select_related('fee', 'fee__program', 'fee__academic_session')
    )

    today = timezone.now().date()
    outstanding, paid = [], []

    for fp in student_payments:
        if fp.status == 'success':
            paid.append(fp.fee)
        else:
            outstanding.append({
                'payment': fp.fee,
                'fee_payment': fp,
                'is_overdue': fp.fee.due_date < today,
                'is_certificate_fee': False,
            })

    # ── 2. Auto certificate fees for completed courses ────────────────────
    # Find all completed enrollments where the course issues a certificate
    completed_enrollments = (
        Enrollment.objects
        .filter(student=user, status='completed', course__has_certificate=True)
        .select_related('course')
    )

    for enrollment in completed_enrollments:
        course = enrollment.course

        # Check payment status per-certificate, not globally
        cert = Certificate.objects.filter(
            student=user, course=course, certificate_type='lms_course'
        ).first()

        if cert and cert.payment_status == 'paid':
            # Already settled — show in paid section
            paid.append({
                'purpose': f'Certificate Fee — {course.title}',
                'amount': course.certificate_fee,
                'is_certificate_fee': True,
                'course': course,
            })
        elif not cert or cert.payment_status == 'unpaid':
            if course.certificate_fee and course.certificate_fee > 0:
                # Outstanding certificate fee entry
                outstanding.append({
                    'payment': {
                        'purpose': f'Certificate Fee — {course.title}',
                        'amount': course.certificate_fee,
                        'due_date': today,
                        'is_certificate_fee': True,
                        'course': course,
                        'pk': f'cert_{course.pk}',
                    },
                    'is_overdue': False,
                    'is_certificate_fee': True,
                })

    return outstanding, paid

# ==================== MY PAYMENTS (outstanding table) ====================

@login_required
@student_required
def my_payments(request):
    """
    Student-facing outstanding fees dashboard.
    Fetches all AllRequiredPayments for the student's faculty/department
    that have not yet been paid.
    """
    outstanding_payments, paid_payments = _get_outstanding_for_student(
        request.user
    )

    total_outstanding = sum(
        (item['payment']['amount'] if isinstance(item['payment'], dict) else item['payment'].amount)
        for item in outstanding_payments
    )

    # Derive display currency from first outstanding item; fall back to USD
    _first = outstanding_payments[0]['payment'] if outstanding_payments else None
    display_currency = (
        _first.get('currency', 'USD') if isinstance(_first, dict)
        else getattr(_first, 'currency', 'USD')
    ) if _first else 'USD'

    context = {
        'page_title': 'My Payments',
        'outstanding_payments': outstanding_payments,
        'paid_payments': paid_payments,
        'total_outstanding': total_outstanding,
        'display_currency': display_currency,
    }
    return render(request, 'students/my_payments.html', context)

# ===========================================================================
# INBOX / MESSAGING
# ===========================================================================

@login_required
@student_required
def inbox(request):
    """
    Student inbox.  Shows received & sent messages (root messages only).
    Marks all unread received messages as read when the page is opened.
    """
    user = request.user

    received = (
        Message.objects
        .filter(recipient=user, parent__isnull=True)
        .select_related('sender')
        .order_by('-created_at')
    )

    sent = (
        Message.objects
        .filter(sender=user, parent__isnull=True)
        .select_related('recipient')
        .order_by('-created_at')
    )

    # Grab the unread count BEFORE we mark them read (for flash badge)
    unread_count = received.filter(is_read=False).count()

    # Mark all unread as read
    Message.objects.filter(
        recipient=user,
        is_read=False,
    ).update(is_read=True, read_at=timezone.now())

    context = {
        'page_title': 'My Inbox',
        'received': received,
        'sent': sent,
        'unread_count': unread_count,
    }
    return render(request, 'students/inbox.html', context)


@login_required
@student_required
def compose_message(request):
    """
    Compose and send a new message to an instructor or admin.
    Accepts ?to=<user_id> query-param to pre-fill the recipient.
    """
    from .forms import MessageComposeForm

    if request.method == 'POST':
        form = MessageComposeForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = request.user
            msg.save()
            messages.success(request, 'Message sent successfully!')
            _notify(
                user=msg.recipient,
                notification_type='message',
                title=f'New Message from {request.user.get_full_name() or request.user.username}',
                message=f'You have a new message: "{msg.subject}"',
                link=f'/student/inbox/{msg.id}/',
            )
            from eduweb.emailservices import send_new_message_email
            send_new_message_email(msg.recipient, request.user, msg)
            return redirect('students:inbox')
        messages.error(request, 'Please fix the errors below.')
    else:
        initial = {}
        to_id = request.GET.get('to')
        if to_id:
            try:
                from django.contrib.auth.models import User as AuthUser
                initial['recipient'] = AuthUser.objects.get(pk=to_id)
            except Exception:
                pass
        form = MessageComposeForm(initial=initial)

    return render(request, 'students/compose_message.html', {
        'page_title': 'Compose Message',
        'form': form,
    })


@login_required
@student_required
def message_thread(request, message_id):
    """
    View a full message thread and reply to it.
    Only the sender or recipient can access.
    """
    msg = get_object_or_404(
        Message.objects.select_related('sender', 'recipient'),
        pk=message_id,
    )

    # Security: only sender or recipient may view
    if msg.sender != request.user and msg.recipient != request.user:
        messages.error(request, 'You do not have permission to view this message.')
        return redirect('students:inbox')

    # Mark as read if current user is the recipient
    if msg.recipient == request.user and not msg.is_read:
        msg.mark_as_read()

    thread_replies = (
        Message.objects
        .filter(parent=msg)
        .select_related('sender', 'recipient')
        .order_by('created_at')
    )

    if request.method == 'POST':
        body = request.POST.get('body', '').strip()
        if len(body) >= 5:
                reply_to = msg.sender if msg.recipient == request.user else msg.recipient
                Message.objects.create(
                    sender=request.user,
                    recipient=reply_to,
                    subject=f'Re: {msg.subject}',
                    body=body,
                    parent=msg,
                )
                messages.success(request, 'Reply sent!')
                _notify(
                    user=reply_to,
                    notification_type='message',
                    title=f'Reply from {request.user.get_full_name() or request.user.username}',
                    message=f'New reply on: "{msg.subject}"',
                    link=f'/student/inbox/{msg.id}/',
                )
                from eduweb.emailservices import send_new_message_email
                send_new_message_email(reply_to, request.user, msg)
                return redirect('students:message_thread', message_id=message_id)
        messages.error(request, 'Reply must be at least 5 characters.')

    return render(request, 'students/message_thread.html', {
        'page_title': msg.subject,
        'message': msg,
        'thread_replies': thread_replies,
    })


# ===========================================================================
# NOTIFICATIONS
# ===========================================================================

@login_required
@student_required
def notifications_view(request):
    """
    Student notifications page.
    - Shows last 30 days only (older ones auto-purged by _notify).
    - Paginated at 15 per page.
    - Marks ALL as read if ?mark_all=1 is passed.
    """
    if request.GET.get('mark_all') == '1':
        Notification.objects.filter(
            user=request.user, is_read=False
        ).update(is_read=True, read_at=timezone.now())
        return redirect('students:notifications_view')

    notifs = (
        Notification.objects
        .filter(user=request.user)
        .order_by('-created_at')
    )
    unread_count = notifs.filter(is_read=False).count()
    page_obj = Paginator(notifs, 15).get_page(request.GET.get('page', 1))

    return render(request, 'students/notifications.html', {
        'page_title': 'Notifications',
        'notifications': page_obj,
        'unread_count': unread_count,
    })


@login_required
@student_required
def mark_notification_read(request, notification_id):
    notif = get_object_or_404(
        Notification,
        pk=notification_id,
        user=request.user,
    )
    notif.mark_as_read()
    return JsonResponse({'success': True})


# ===========================================================================
# COURSE REVIEW
# ===========================================================================

@login_required
@student_required
def submit_review(request, course_slug):
    """
    Submit or update a star rating + text review for a course.
    Student must be enrolled. POST-only; redirects back to course detail.
    """
    if request.method != 'POST':
        return redirect('students:course_detail', course_slug=course_slug)

    course = get_object_or_404(LMSCourse, slug=course_slug, is_published=True)

    # Must be enrolled
    get_object_or_404(Enrollment, student=request.user, course=course)

    try:
        rating = int(request.POST.get('rating', 0))
        if not 1 <= rating <= 5:
            raise ValueError
    except (TypeError, ValueError):
        messages.error(request, 'Please select a rating between 1 and 5.')
        return redirect('students:course_detail', course_slug=course_slug)

    review_text = request.POST.get('review_text', '').strip()

    _, created = Review.objects.update_or_create(
        course=course,
        student=request.user,
        defaults={'rating': rating, 'review_text': review_text},
    )

    if created:
        messages.success(request, 'Thank you! Your review has been submitted.')
        _notify(
            user=request.user,
            notification_type='enrollment',
            title=f'Review Submitted: {course.title}',
            message=f'You rated "{course.title}" {rating}/5 stars. Thank you for your feedback!',
            link=f'/student/courses/{course_slug}/',
        )
    else:
        messages.success(request, 'Your review has been updated.')

    return redirect('students:course_detail', course_slug=course_slug)


# ===========================================================================
# CREATE STUDY GROUP
# ===========================================================================

@login_required
@student_required
def create_study_group(request):
    """
    Create a new study group. The creator is automatically joined as admin.
    """
    from .forms import StudyGroupCreateForm

    if request.method == 'POST':
        form = StudyGroupCreateForm(user=request.user, data=request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.created_by = request.user
            group.save()

            StudyGroupMember.objects.create(
                study_group=group,
                user=request.user,
                role='admin',
            )

            messages.success(request, f'Study group "{group.name}" created!')
            _notify(
                user=request.user,
                notification_type='system',
                title=f'Study Group Created: {group.name}',
                message=f'Your study group "{group.name}" is live. Share it with others to grow your group!',
                link=f'/student/study-groups/{group.id}/',
            )
            return redirect('students:study_group_detail', group_id=group.id)
        messages.error(request, 'Please fix the errors below.')
    else:
        form = StudyGroupCreateForm(user=request.user)

    return render(request, 'students/create_study_group.html', {
        'page_title': 'Create Study Group',
        'form': form,
    })

@login_required
@student_required
def academic_records(request):
    """
    Student academic records page.
 
    Surfaces:
    • Program info + admission metadata (from CourseApplication)
    • Program requirements breakdown — core vs elective, credits needed vs earned
    • Graduation progress bar
    • Academic history grouped by session/year with letter grades & GPA
    • Links to transcript export request and certificate
    """
    from eduweb.models import Course, AcademicSession
 
    user = request.user
 
    # ── 1. Application / Admission info ─────────────────────────────────────
    application = (
        CourseApplication.objects
        .filter(user=user, status='approved')
        .select_related(
            'program',
            'program__department__faculty',
            'intake',
        )
        .order_by('-created_at')
        .first()
    )
 
    program = application.program if application else None
 
    # ── 2. Program requirements (all academic Course rows) ───────────────────
    program_courses = []
    if program:
        program_courses = list(
            Course.objects
            .filter(program=program, is_active=True)
            .select_related('academic_session')
            .order_by('year_of_study', 'semester', 'display_order')
        )
 
    core_courses     = [c for c in program_courses if c.course_type == 'core']
    elective_courses = [c for c in program_courses if c.course_type == 'elective']
    other_courses    = [c for c in program_courses if c.course_type not in ('core', 'elective')]
 
    total_credits_required = program.credits_required if program else 0
 
    # ── 3. Student's grade records ───────────────────────────────────────────
    academic_grades = list(
        CourseGrade.objects
        .filter(student=user)
        .select_related('course', 'course__program', 'session')
        .order_by('session__name', 'course__year_of_study', 'course__semester')
    )
 
    # Map course_id → grade for quick lookup in requirements table
    graded_course_ids = {g.course_id: g for g in academic_grades}
 
    # Annotate each program course with the student's grade (if any)
    for course in program_courses:
        course.student_grade = graded_course_ids.get(course.id)
 
    # ── 4. Credits earned (passed only) ─────────────────────────────────────
    credits_earned = sum(
        g.credit_units for g in academic_grades if g.is_passed
    )
    credits_remaining = max(0, total_credits_required - credits_earned)
    graduation_pct = (
        round(credits_earned / total_credits_required * 100, 1)
        if total_credits_required > 0 else 0
    )
 
    # ── 5. GPA calculation (4.0 scale) ───────────────────────────────────────
    GRADE_POINTS = {'A': 4.0, 'B': 3.0, 'C': 2.0, 'D': 1.0, 'F': 0.0, 'I': 0.0, 'W': 0.0}
    weighted_sum   = sum(GRADE_POINTS.get(g.grade, 0) * g.credit_units for g in academic_grades if g.grade)
    total_gpa_units = sum(g.credit_units for g in academic_grades if g.grade and g.grade not in ('W',))
    gpa = round(weighted_sum / total_gpa_units, 2) if total_gpa_units > 0 else None
 
    # ── 6. Group grades by session for the history table ────────────────────
    sessions_dict = {}
    for g in academic_grades:
        key = g.session.name if g.session else 'Unassigned'
        sessions_dict.setdefault(key, []).append(g)
 
    # Per-session GPA
    session_summaries = []
    for session_name, grades_list in sessions_dict.items():
        sess_weighted = sum(GRADE_POINTS.get(g.grade, 0) * g.credit_units for g in grades_list if g.grade)
        sess_units    = sum(g.credit_units for g in grades_list if g.grade and g.grade not in ('W',))
        sess_gpa      = round(sess_weighted / sess_units, 2) if sess_units > 0 else None
        session_summaries.append({
            'name': session_name,
            'grades': grades_list,
            'gpa': sess_gpa,
            'credits': sum(g.credit_units for g in grades_list if g.is_passed),
        })
 
    # ── 7. Enrollment summary (LMS courses, for completeness) ────────────────
    lms_enrollments = (
        Enrollment.objects
        .filter(student=user)
        .select_related('course')
        .order_by('-enrolled_at')
    )
 
    # ── 8. Certificates ──────────────────────────────────────────────────────
    certificates = (
        Certificate.objects
        .filter(student=user)
        .select_related('course', 'program')
        .order_by('-issued_date')
    )
 
    context = {
        'page_title': 'Academic Records',
        'application': application,
        'program': program,
        # Requirements
        'program_courses': program_courses,
        'core_courses': core_courses,
        'elective_courses': elective_courses,
        'other_courses': other_courses,
        # Progress
        'total_credits_required': total_credits_required,
        'credits_earned': credits_earned,
        'credits_remaining': credits_remaining,
        'graduation_pct': graduation_pct,
        # Grades
        'academic_grades': academic_grades,
        'session_summaries': session_summaries,
        'gpa': gpa,
        # Misc
        'lms_enrollments': lms_enrollments,
        'certificates': certificates,
    }
 
    return render(request, 'students/academic_records.html', context)

# ══════════════════════════════════════════════════════════════════════════════
#  EXAM VIEWS  —  drop-in replacements for the exam section in views.py
#
#  Changes from previous version:
#   - exam_instructions: passes standard_rules list + exam_end_iso
#   - start_exam:        passes exam_end_iso (needed by exams.html timer)
#   - exam_list:         unchanged (still correct)
#   - get_exam_data:     unchanged
#   - save_answer:       unchanged
#   - flag_tab_switch:   unchanged
#   - submit_exam:       unchanged
# ══════════════════════════════════════════════════════════════════════════════

import json
import random

from django.contrib.auth.decorators import login_required
from django.http                    import JsonResponse
from django.shortcuts               import get_object_or_404, redirect, render
from django.utils                   import timezone


# ─── Standard exam rules shown on instructions page ───────────────────────────
STANDARD_EXAM_RULES = [
    "Do not refresh or close the browser window during the exam.",
    "All answers are auto-saved as you select them.",
    "The timer will automatically submit your answers when time runs out.",
    "Switching browser tabs is logged and may be reported to your invigilator.",
    "Ensure you have a stable internet connection before starting.",
    "Do not communicate with other candidates during the exam.",
    "The Back button on your browser is disabled once the exam begins.",
]


# ─────────────────────────────────────────────────────────────────────────────
#  EXAM LIST / TIMETABLE
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def exam_list(request):
    now = timezone.now()

    exams = (
        Exam.objects
        .filter(status=Exam.PUBLISHED, is_active=True)
        .select_related('course', 'academic_session', 'department')
        .order_by('exam_date', 'start_time')
    )

    context_items = []
    for exam in exams:
        if now < exam.visible_from:
            continue
        if now > exam.visible_until:
            continue

        instructions_at = exam.instructions_open_at
        start_dt        = exam.exam_start_datetime
        end_dt          = exam.exam_end_datetime

        can_read  = now >= instructions_at
        can_start = now >= start_dt
        is_live   = start_dt <= now < end_dt

        student_status = 'not_started'
        response = StudentExamResponse.objects.filter(
            exam=exam, student=request.user
        ).first()
        if response:
            student_status = response.status

        context_items.append({
            'exam':                     exam,
            'can_read':                 can_read,
            'can_start':                can_start,
            'is_live':                  is_live,
            'student_status':           student_status,
            'instructions_open_at_iso': instructions_at.isoformat(),
            'exam_start_datetime_iso':  start_dt.isoformat(),
            'exam_end_datetime_iso':    end_dt.isoformat(),
        })

    return render(request, 'students/examlist.html', {'exams': context_items})


# ─────────────────────────────────────────────────────────────────────────────
#  INSTRUCTION PAGE
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def exam_instructions(request, slug):
    exam = get_object_or_404(Exam, slug=slug)
    now  = timezone.now()

    if now < exam.instructions_open_at:
        return redirect('students:exam_list')

    if now >= exam.exam_end_datetime:
        return redirect('students:exam_list')

    response, _ = StudentExamResponse.objects.get_or_create(
        exam=exam,
        student=request.user,
        defaults={'status': StudentExamResponse.INSTRUCTIONS},
    )
    if response.status == StudentExamResponse.NOT_STARTED:
        response.status = StudentExamResponse.INSTRUCTIONS
    if not response.instructions_opened_at:
        response.instructions_opened_at = now
    response.save(update_fields=['status', 'instructions_opened_at'])

    secs = max(0, int((exam.exam_start_datetime - now).total_seconds()))
    h, m, s = min(secs // 3600, 99), (secs % 3600) // 60, secs % 60

    # Pre-render units as (value_str, label) pairs for the template
    countdown_units = [
        (str(h).zfill(2), 'hrs'),
        (str(m).zfill(2), 'min'),
        (str(s).zfill(2), 'sec'),
    ]

    return render(request, 'students/examinstructions.html', {
        'exam':            exam,
        'exam_start_iso':  exam.exam_start_datetime.isoformat(),
        'exam_end_iso':    exam.exam_end_datetime.isoformat(),
        'countdown_units': countdown_units,
        'standard_rules':  STANDARD_EXAM_RULES,
    })


# ─────────────────────────────────────────────────────────────────────────────
#  START EXAM  (assigns questions, then renders CBT page)
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def start_exam(request, slug):
    exam = get_object_or_404(Exam, slug=slug)
    now  = timezone.now()

    if now < exam.exam_start_datetime:
        return redirect('students:exam_instructions', slug=slug)
    if now >= exam.exam_end_datetime:
        return redirect('students:exam_list')

    response, _ = StudentExamResponse.objects.get_or_create(
        exam=exam,
        student=request.user,
        defaults={'status': StudentExamResponse.INSTRUCTIONS},
    )
    if response.status in (StudentExamResponse.SUBMITTED, StudentExamResponse.GRADED):
        return redirect('students:exam_list')

    if not response.assigned_question_ids:
        questions = list(exam.questions.filter(is_active=True))
        if exam.shuffle_questions:
            random.shuffle(questions)
        if exam.questions_per_student:
            questions = questions[:exam.questions_per_student]

        options_map = {}
        for q in questions:
            opts = q.options.copy()
            if exam.shuffle_options:
                random.shuffle(opts)
            options_map[str(q.id)] = [opt['id'] for opt in opts]

        response.assigned_question_ids  = [q.id for q in questions]
        response.assigned_options_order = options_map
        response.status                 = StudentExamResponse.IN_PROGRESS
        response.exam_started_at        = now
        response.save(update_fields=[
            'assigned_question_ids', 'assigned_options_order',
            'status', 'exam_started_at',
        ])
    elif response.status != StudentExamResponse.IN_PROGRESS:
        response.status = StudentExamResponse.IN_PROGRESS
        response.save(update_fields=['status'])

    return render(request, 'students/exams.html', {
        'exam':         exam,
        'exam_end_iso': exam.exam_end_datetime.isoformat(),
    })


# ─────────────────────────────────────────────────────────────────────────────
#  GET EXAM DATA  (JSON — questions + server-authoritative time remaining)
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def get_exam_data(request, slug):
    exam     = get_object_or_404(Exam, slug=slug)
    response, _ = StudentExamResponse.objects.get_or_create(
    exam=exam,
    student=request.user,
    defaults={'status': StudentExamResponse.INSTRUCTIONS},
)
    questions_data = []
    for qid in response.assigned_question_ids:
        try:
            q = exam.questions.get(id=qid)
        except Exception:
            continue

        ordered_ids = response.assigned_options_order.get(str(qid), [])
        opt_lookup  = {opt['id']: opt for opt in q.options}
        options     = [
            {'id': oid, 'text': opt_lookup[oid]['text']}
            for oid in ordered_ids
            if oid in opt_lookup
        ]

        questions_data.append({
            'id':        q.id,
            'text':      q.question_text,
            'options':   options,
            'marks':     str(q.marks),
            'image_url': request.build_absolute_uri(q.image.url) if q.image else None,
        })

    now       = timezone.now()
    total_sec = exam.duration_minutes * 60
    wall_secs = max(0, int((exam.exam_end_datetime - now).total_seconds()))

    if response.exam_started_at:
        elapsed   = int((now - response.exam_started_at).total_seconds())
        remaining = max(0, total_sec - elapsed)
    else:
        remaining = total_sec

    remaining = min(remaining, wall_secs)

    return JsonResponse({
        'questions':      questions_data,
        'time_remaining': remaining,
        'duration':       total_sec,
        'saved_answers':  response.answers,
    })


# ─────────────────────────────────────────────────────────────────────────────
#  AUTO-SAVE SINGLE ANSWER
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def save_answer(request, slug):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    data     = json.loads(request.body)
    response = get_object_or_404(StudentExamResponse, exam__slug=slug, student=request.user)

    if response.status not in (
        StudentExamResponse.INSTRUCTIONS, StudentExamResponse.IN_PROGRESS
    ):
        return JsonResponse({'error': 'Exam not in progress'}, status=400)

    response.answers[str(data['question_id'])] = data['answer']
    response.last_autosave_at = timezone.now()
    response.save(update_fields=['answers', 'last_autosave_at'])

    return JsonResponse({'status': 'saved'})


# ─────────────────────────────────────────────────────────────────────────────
#  FLAG TAB SWITCH (security — silent)
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def flag_tab_switch(request, slug):
    if request.method != 'POST':
        return JsonResponse({'ok': False}, status=405)
    try:
        data     = json.loads(request.body)
        response = StudentExamResponse.objects.filter(
            exam__slug=slug, student=request.user
        ).first()
        if response:
            response.tab_switch_count = data.get('count', response.tab_switch_count + 1)
            response.save(update_fields=['tab_switch_count'])
    except Exception:
        pass
    return JsonResponse({'ok': True})


# ─────────────────────────────────────────────────────────────────────────────
#  SUBMIT + AUTO-GRADE
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def submit_exam(request, slug):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    response = get_object_or_404(StudentExamResponse, exam__slug=slug, student=request.user)

    if response.status in (StudentExamResponse.SUBMITTED, StudentExamResponse.GRADED):
        return JsonResponse({'status': 'already_submitted'})

    exam  = response.exam
    total = 0.0

    for qid in response.assigned_question_ids:
        try:
            q = exam.questions.get(id=qid)
        except Exception:
            continue
        answer  = response.answers.get(str(qid))
        correct = [opt['id'] for opt in q.options if opt.get('is_correct')]
        if answer and answer in correct:
            total += float(q.marks)

    now = timezone.now()
    response.total_score    = total
    response.status         = StudentExamResponse.SUBMITTED
    response.submitted_at   = now
    if response.exam_started_at:
        response.time_spent_seconds = int((now - response.exam_started_at).total_seconds())

    response.save(update_fields=[
        'total_score', 'status', 'submitted_at', 'time_spent_seconds'
    ])

    return JsonResponse({'status': 'submitted', 'score': total})