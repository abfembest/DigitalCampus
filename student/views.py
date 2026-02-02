from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.core.paginator import Paginator
from functools import wraps
from datetime import timedelta

from eduweb.models import (
    LMSCourse, Enrollment, Lesson, LessonProgress, 
    CourseCategory, Assignment, AssignmentSubmission,
    Certificate, Announcement, Quiz, QuizAttempt, 
    QuizAnswer, QuizQuestion, QuizResponse, StudyGroup, StudyGroupMember, 
    Discussion, DiscussionReply, Badge, 
    StudentBadge
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
    
    # Active enrollments
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
    """List student's enrolled courses"""
    status_filter = request.GET.get('status', 'active')
    
    if status_filter not in ['active', 'completed']:
        status_filter = 'active'
    
    enrollments = Enrollment.objects.filter(
        student=request.user,
        status=status_filter
    ).select_related(
        'course', 
        'course__category'
    ).prefetch_related(
        'course__lessons'
    ).order_by('-enrolled_at')
    
    # Add completed lesson count
    for enrollment in enrollments:
        enrollment.completed_lessons = LessonProgress.objects.filter(
            enrollment=enrollment,
            is_completed=True
        ).count()
    
    context = {
        'page_title': 'My Courses',
        'enrollments': enrollments,
        'status_filter': status_filter,
    }
    
    return render(request, 'students/my_courses.html', context)


@login_required
@student_required
def course_catalog(request):
    """Browse available courses"""
    category_slug = request.GET.get('category')
    search_query = request.GET.get('q')
    difficulty = request.GET.get('difficulty')
    
    # Get published courses
    courses = LMSCourse.objects.filter(
        is_published=True,
    )
    
    # Apply filters
    if category_slug:
        courses = courses.filter(category__slug=category_slug)
    
    if search_query:
        courses = courses.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(short_description__icontains=search_query)
        )
    
    if difficulty:
        courses = courses.filter(difficulty_level=difficulty)
    
    # Optimize queries
    courses = courses.select_related(
        'category', 
        'instructor'
    ).annotate(
        total_enrollments=Count('enrollments')
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
    
    # Pagination
    paginator = Paginator(courses, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'Course Catalog',
        'courses': page_obj,
        'categories': categories,
        'enrolled_ids': enrolled_ids,
        'search_query': search_query,
    }
    
    return render(request, 'students/course_catalog.html', context)


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
    ).prefetch_related('lessons').order_by('display_order')
    
    # Filter lessons based on enrollment
    if not enrollment:
        for section in sections:
            section.filtered_lessons = section.lessons.filter(
                is_preview=True,
                is_active=True
            ).order_by('display_order')
    else:
        for section in sections:
            section.filtered_lessons = section.lessons.filter(
                is_active=True
            ).order_by('display_order')
    
    context = {
        'page_title': course.title,
        'course': course,
        'enrollment': enrollment,
        'sections': sections,
    }
    
    return render(request, 'students/course_detail.html', context)


@login_required
@student_required
def enroll_course(request, course_id):
    """Enroll in a course"""
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
        return redirect('students:course_detail', course_id=course_id)
    
    # Create enrollment (for free courses)
    if course.is_free:
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
        return redirect('students:course_detail', course_id=course_id)
    else:
        # TODO: Handle paid course enrollment
        messages.error(
            request,
            'Payment required. This feature is coming soon.'
        )
        return redirect('students:course_detail', course_id=course_id)


@login_required
@student_required
def lesson_view(request, lesson_id):
    """View lesson content"""
    lesson = get_object_or_404(
        Lesson.objects.select_related(
            'course', 
            'section'
        ),
        id=lesson_id
    )
    
    # Verify enrollment
    enrollment = get_object_or_404(
        Enrollment,
        student=request.user,
        course=lesson.course,
        status='active'
    )
    
    # Get or create progress
    progress, created = LessonProgress.objects.get_or_create(
        enrollment=enrollment,
        lesson=lesson
    )
    
    # Update last accessed
    progress.last_accessed = timezone.now()
    progress.save()
    
    # Get previous and next lessons
    all_lessons = Lesson.objects.filter(
        course=lesson.course,
        is_active=True
    ).order_by('section__display_order', 'display_order')
    
    lesson_list = list(all_lessons)
    current_index = next(
        (i for i, l in enumerate(lesson_list) if l.id == lesson.id), 
        None
    )
    
    prev_lesson = lesson_list[current_index - 1] if current_index and current_index > 0 else None
    next_lesson = lesson_list[current_index + 1] if current_index is not None and current_index < len(lesson_list) - 1 else None
    
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
def mark_lesson_complete(request, lesson_id):
    """Mark lesson as complete"""
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
    progress.completed_at = timezone.now()
    progress.save()
    
    # Update enrollment progress
    enrollment.update_progress()
    
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
    
    # Get assignments for enrolled courses
    enrolled_courses = Enrollment.objects.filter(
        student=request.user
    ).values_list('course_id', flat=True)
    
    base_query = Assignment.objects.filter(
        lesson__course_id__in=enrolled_courses,
        is_active=True
    )
    
    # Filter by status
    if status_filter == 'pending':
        assignments = base_query.exclude(
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
    ).prefetch_related(
        'submissions'
    ).distinct().order_by('due_date')
    
    context = {
        'page_title': 'My Assignments',
        'assignments': assignments,
        'status_filter': status_filter,
    }
    
    return render(request, 'students/assignments.html', context)


@login_required
@student_required
def assignment_detail(request, assignment_id):
    """View assignment details"""
    assignment = get_object_or_404(
        Assignment.objects.select_related('lesson__course'),
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
    
    return render(request, 'students/assignment_detail.html', context)


@login_required
@student_required
def submit_assignment(request, assignment_id):
    """Submit assignment"""
    if request.method != 'POST':
        return redirect('students:assignments')
    
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
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
    submission.submission_text = request.POST.get('submission_text', '')
    
    if request.FILES.get('attachment'):
        submission.attachment = request.FILES['attachment']
    
    submission.status = 'submitted'
    submission.submitted_at = timezone.now()
    
    # Check if late
    if timezone.now() > assignment.due_date:
        submission.is_late = True
    
    submission.save()
    
    messages.success(request, 'Assignment submitted successfully!')
    return redirect('students:assignment_detail', assignment_id=assignment_id)


# ==================== QUIZZES ====================
@login_required
@student_required
def quiz_list(request):
    """List all quizzes"""
    enrolled_courses = Enrollment.objects.filter(
        student=request.user
    ).values_list('course_id', flat=True)
    
    quizzes = Quiz.objects.filter(
        lesson__course_id__in=enrolled_courses,
        is_active=True
    ).select_related(
        'lesson__course'
    ).order_by('-created_at')
    
    # Add attempt info
    for quiz in quizzes:
        quiz.user_attempts = QuizAttempt.objects.filter(
            quiz=quiz,
            student=request.user
        ).count()
        quiz.best_score = QuizAttempt.objects.filter(
            quiz=quiz,
            student=request.user
        ).aggregate(Avg('score'))['score__avg'] or 0
    
    context = {
        'page_title': 'Quizzes',
        'quizzes': quizzes,
    }
    
    return render(request, 'students/quiz_list.html', context)


@login_required
@student_required
def quiz_detail(request, quiz_id):
    """View quiz details"""
    quiz = get_object_or_404(
        Quiz.objects.select_related('lesson__course'),
        id=quiz_id
    )
    
    # Verify enrollment
    get_object_or_404(
        Enrollment,
        student=request.user,
        course=quiz.lesson.course
    )
    
    # Get previous attempts
    attempts = QuizAttempt.objects.filter(
        quiz=quiz,
        student=request.user
    ).order_by('-started_at')
    
    # Check attempt limits
    can_attempt = True
    if quiz.max_attempts > 0:
        if attempts.count() >= quiz.max_attempts:
            can_attempt = False
    
    context = {
        'page_title': quiz.title,
        'quiz': quiz,
        'attempts': attempts,
        'can_attempt': can_attempt,
    }
    
    return render(request, 'students/quiz_detail.html', context)


@login_required
@student_required
def quiz_take(request, quiz_id):
    """Take quiz"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
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
        student=request.user
    ).count()
    
    if quiz.max_attempts > 0 and attempts_count >= quiz.max_attempts:
        messages.error(request, 'Maximum attempts reached.')
        return redirect('students:quiz_detail', quiz_id=quiz_id)
    
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
    
    context = {
        'page_title': f'Taking: {quiz.title}',
        'quiz': quiz,
        'attempt': attempt,
        'questions': questions,
    }
    
    return render(request, 'students/quiz_take.html', context)


@login_required
@student_required
def quiz_submit(request, attempt_id):
    """Submit quiz answers"""
    if request.method != 'POST':
        return redirect('students:quiz_list')
    
    attempt = get_object_or_404(
        QuizAttempt,
        id=attempt_id,
        student=request.user
    )
    
    if attempt.completed_at:
        messages.warning(request, 'Quiz already submitted.')
        return redirect('students:quiz_result', attempt_id=attempt_id)
    
    # Process answers
    total_score = 0
    max_score = 0
    
    for key, value in request.POST.items():
        if key.startswith('question_'):
            question_id = int(key.split('_')[1])
            question = attempt.quiz.questions.get(id=question_id)
            max_score += float(question.points)
            
            # Get selected answer
            try:
                selected_answer = QuizAnswer.objects.get(id=int(value))
                
                # Create response record
                response = QuizResponse.objects.create(
                    attempt=attempt,
                    question=question,
                    selected_answer=selected_answer,
                    is_correct=selected_answer.is_correct,
                    points_earned=question.points if selected_answer.is_correct else 0
                )
                
                # Add to score if correct
                if selected_answer.is_correct:
                    total_score += float(question.points)
            except (QuizAnswer.DoesNotExist, ValueError):
                pass
    
    # Calculate percentage
    percentage = (total_score / max_score * 100) if max_score > 0 else 0
    
    # Update attempt
    attempt.score = percentage
    attempt.passed = percentage >= attempt.quiz.passing_score
    attempt.completed_at = timezone.now()
    attempt.save()
    
    messages.success(request, 'Quiz submitted successfully!')
    return redirect('students:quiz_result', attempt_id=attempt_id)


@login_required
@student_required
def quiz_result(request, attempt_id):
    """View quiz results"""
    attempt = get_object_or_404(
        QuizAttempt.objects.select_related('quiz'),
        id=attempt_id,
        student=request.user
    )
    
    # Get answers with questions
    answers = attempt.responses.select_related(
        'question', 'selected_answer'
    ).all()
    
    context = {
        'page_title': 'Quiz Results',
        'attempt': attempt,
        'answers': answers,
    }
    
    return render(request, 'students/quiz_result.html', context)


# ==================== COMMUNITY ====================
@login_required
@student_required
def community(request):
    """Community discussion board"""
    filter_type = request.GET.get('filter', 'all')
    search_query = request.GET.get('q', '')
    
    threads = Discussion.objects.select_related(
        'author', 
        'course'
    ).annotate(
        reply_count=Count('replies')
    )
    
    # Apply filters
    if filter_type == 'my_courses':
        enrolled_courses = Enrollment.objects.filter(
            student=request.user
        ).values_list('course_id', flat=True)
        threads = threads.filter(course_id__in=enrolled_courses)
    elif filter_type == 'my_posts':
        threads = threads.filter(author=request.user)
    
    if search_query:
        threads = threads.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query)
        )
    
    threads = threads.order_by('-is_pinned', '-created_at')
    
    # Pagination
    paginator = Paginator(threads, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    context = {
        'page_title': 'Community',
        'threads': page_obj,
        'filter_type': filter_type,
        'search_query': search_query,
    }
    
    return render(request, 'students/community.html', context)


@login_required
@student_required
def thread_detail(request, thread_id):
    """View discussion thread"""
    thread = get_object_or_404(
        Discussion.objects.select_related('author', 'course'),
        id=thread_id
    )
    
    # Increment views
    thread.views_count += 1
    thread.save()
    
    # Get replies
    replies = thread.replies.select_related(
        'author'
    ).order_by('created_at')
    
    # Handle reply submission
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            DiscussionReply.objects.create(
                thread=thread,
                author=request.user,
                content=content
            )
            messages.success(request, 'Reply posted successfully!')
            return redirect('students:thread_detail', thread_id=thread_id)
    
    context = {
        'page_title': thread.title,
        'thread': thread,
        'replies': replies,
    }
    
    return render(request, 'students/thread_detail.html', context)


@login_required
@student_required
def create_thread(request):
    """Create new discussion thread"""
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        course_id = request.POST.get('course_id')
        
        if title and content:
            thread = Discussion.objects.create(
                title=title,
                content=content,
                author=request.user,
                course_id=course_id if course_id else None
            )
            messages.success(request, 'Thread created successfully!')
            return redirect('students:thread_detail', thread_id=thread.id)
        else:
            messages.error(request, 'Please fill in all fields.')
    
    # Get user's enrolled courses
    enrolled_courses = LMSCourse.objects.filter(
        enrollments__student=request.user
    )
    
    context = {
        'page_title': 'New Discussion',
        'enrolled_courses': enrolled_courses,
    }
    
    return render(request, 'students/create_thread.html', context)


# ==================== STUDY GROUPS ====================
@login_required
@student_required
def study_groups(request):
    """List study groups"""
    # Groups user is member of
    my_groups = StudyGroup.objects.filter(
        members__user=request.user,
        members__is_active=True,
        is_active=True
    ).distinct()
    
    # Available groups to join
    available_groups = StudyGroup.objects.filter(
        is_active=True
    ).exclude(
        members__user=request.user
    ).annotate(
        member_count=Count('members')
    )
    
    context = {
        'page_title': 'Study Groups',
        'my_groups': my_groups,
        'available_groups': available_groups,
    }
    
    return render(request, 'students/study_groups.html', context)


@login_required
@student_required
def study_group_detail(request, group_id):
    """View study group details"""
    group = get_object_or_404(
        StudyGroup.objects.select_related('course'),
        id=group_id
    )
    
    # Check membership
    is_member = StudyGroupMember.objects.filter(
        study_group=group,
        user=request.user
    ).exists()
    
    members = group.members.select_related('user').all()
    
    context = {
        'page_title': group.name,
        'group': group,
        'is_member': is_member,
        'members': members,
    }
    
    return render(request, 'students/study_group_detail.html', context)


@login_required
@student_required
def join_study_group(request, group_id):
    """Join a study group"""
    if request.method != 'POST':
        return redirect('students:study_groups')
    
    group = get_object_or_404(StudyGroup, id=group_id)
    
    # Check if already member
    if StudyGroupMember.objects.filter(
        study_group=group,
        user=request.user
    ).exists():
        messages.info(request, 'You are already a member.')
        return redirect('students:study_group_detail', group_id=group_id)
    
    # Check capacity
    current_members = group.members.count()
    if current_members >= group.max_members:
        messages.error(request, 'Group is full.')
        return redirect('students:study_groups')
    
    # Add member
    StudyGroupMember.objects.create(
        study_group=group,
        user=request.user,
        role='member'
    )
    
    messages.success(request, f'Joined {group.name} successfully!')
    return redirect('students:study_group_detail', group_id=group_id)


# ==================== ACHIEVEMENTS ====================
@login_required
@student_required
def achievements(request):
    """View achievements and badges"""
    # User's badges
    user_badges = StudentBadge.objects.filter(
        student=request.user
    ).select_related('badge').order_by('-awarded_at')
    
    # All available badges
    all_badges = Badge.objects.filter(is_active=True)
    
    # Separate earned and unearned
    earned_badge_ids = user_badges.values_list('badge_id', flat=True)
    unearned_badges = all_badges.exclude(id__in=earned_badge_ids)
    
    # Calculate statistics
    completed_courses = Enrollment.objects.filter(
        student=request.user,
        status='completed'
    ).count()
    
    # Calculate total points from badges
    total_points = sum(
        badge.badge.points for badge in user_badges
    ) if user_badges else 0
    
    context = {
        'page_title': 'Achievements',
        'user_badges': user_badges,
        'unearned_badges': unearned_badges,
        'completed_courses': completed_courses,
        'total_points': total_points,
    }
    
    return render(request, 'students/achievements.html', context)


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
    ).select_related('course').prefetch_related(
        'course__sections__lessons'
    ).order_by('-enrolled_at')
    
    for enrollment in enrollments:
        enrollment.completed_lessons = LessonProgress.objects.filter(
            enrollment=enrollment,
            is_completed=True
        ).count()
    
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
    ).select_related('course').order_by('-issued_date')
    
    context = {
        'page_title': 'My Certificates',
        'certificates': certificates,
    }
    
    return render(request, 'students/certificates.html', context)


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
        profile.website = request.POST.get('website', '')
        profile.linkedin = request.POST.get('linkedin', '')
        profile.twitter = request.POST.get('twitter', '')
        
        if request.FILES.get('avatar'):
            profile.avatar = request.FILES['avatar']
        
        profile.save()
        
        messages.success(request, 'Profile updated successfully!')
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
        
        # Handle password change if provided
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if current_password and new_password:
            if request.user.check_password(current_password):
                if new_password == confirm_password:
                    request.user.set_password(new_password)
                    request.user.save()
                    messages.success(
                        request, 
                        'Password updated successfully!'
                    )
                else:
                    messages.error(
                        request, 
                        'New passwords do not match.'
                    )
            else:
                messages.error(
                    request, 
                    'Current password is incorrect.'
                )
        
        messages.success(request, 'Settings updated successfully!')
        return redirect('students:settings')
    
    context = {
        'page_title': 'Settings',
    }
    
    return render(request, 'students/settings.html', context)