from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg, Sum, Q, F
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import TruncDate, TruncMonth
from django.contrib.auth import update_session_auth_hash
from django.core.mail import send_mail
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST

from eduweb.models import (
    LMSCourse, Lesson, LessonSection, Quiz, QuizQuestion,
    QuizAnswer, Assignment, AssignmentSubmission, Enrollment,
    Announcement, Review
)
from .forms import (
    CourseForm, CourseObjectivesForm, LessonForm, SectionForm,
    QuizForm, QuizQuestionForm, QuizAnswerForm, AssignmentForm,
    AnnouncementForm, InstructorProfileForm, InstructorSettingsForm, PasswordChangeForm, SupportTicketForm
)
from eduweb.decorators import instructor_required


# ==================== DASHBOARD ====================
@login_required(login_url='auth')
@instructor_required
def dashboard(request):
    """Instructor dashboard with comprehensive statistics"""
    courses = LMSCourse.objects.filter(
        instructor=request.user
    ).annotate(
        enrollments_count=Count('enrollments')
    ).select_related('category').prefetch_related('enrollments')[:5]
    
    # Statistics
    total_courses = LMSCourse.objects.filter(
        instructor=request.user
    ).count()
    
    published_courses = LMSCourse.objects.filter(
        instructor=request.user,
        is_published=True
    ).count()
    
    total_students = Enrollment.objects.filter(
        course__instructor=request.user
    ).values('student').distinct().count()
    
    pending_submissions = AssignmentSubmission.objects.filter(
        assignment__lesson__course__instructor=request.user,
        status='submitted'
    ).count()
    
    # Recent enrollments
    recent_enrollments = Enrollment.objects.filter(
        course__instructor=request.user
    ).select_related(
        'student',
        'course'
    ).order_by('-enrolled_at')[:10]
    
    context = {
        'courses': courses,
        'total_courses': total_courses,
        'published_courses': published_courses,
        'total_students': total_students,
        'pending_submissions': pending_submissions,
        'recent_enrollments': recent_enrollments,
    }
    return render(request, 'instructor/dashboard.html', context)


# ==================== COURSE MANAGEMENT ====================
@login_required(login_url='auth')
@instructor_required
def course_list(request):
    """List all instructor courses with statistics"""
    courses = LMSCourse.objects.filter(
        instructor=request.user
    ).annotate(
        enrollment_count=Count('enrollments')
    ).select_related('category').order_by('-created_at')
    
    return render(request, 'instructor/course_list.html', {
        'courses': courses
    })


@login_required(login_url='auth')
@instructor_required
def course_create(request):
    """Create new course"""
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.instructor = request.user
            course.save()
            messages.success(
                request,
                f'Course "{course.title}" created successfully!'
            )
            return redirect('instructor:course_edit', slug=course.slug)
    else:
        form = CourseForm()
    
    return render(request, 'instructor/course_form.html', {
        'form': form,
        'course': None
    })


@login_required(login_url='auth')
@instructor_required
def course_edit(request, slug):
    """Edit course using slug"""
    course = get_object_or_404(
        LMSCourse,
        slug=slug,
        instructor=request.user
    )
    
    if request.method == 'POST':
        form = CourseForm(
            request.POST,
            request.FILES,
            instance=course
        )
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Course "{course.title}" updated successfully!'
            )
            return redirect('instructor:course_edit', slug=course.slug)
    else:
        form = CourseForm(instance=course)
    
    # Course statistics
    stats = {
        'total_students': course.enrollments.count(),
        'total_lessons': course.lessons.count(),
        'total_sections': course.sections.count(),
    }
    
    return render(request, 'instructor/course_form.html', {
        'form': form,
        'course': course,
        'stats': stats,
    })


@login_required(login_url='auth')
@instructor_required
def course_objectives(request, slug):
    """Manage course objectives using slug"""
    course = get_object_or_404(
        LMSCourse,
        slug=slug,
        instructor=request.user
    )
    
    if request.method == 'POST':
        form = CourseObjectivesForm(request.POST, instance=course)
        if form.is_valid():
            # Process objectives
            objectives_text = form.cleaned_data.get('objectives', '')
            prerequisites_text = form.cleaned_data.get('prerequisites', '')
            
            # Split and filter empty lines
            course.learning_objectives = [
                obj.strip()
                for obj in objectives_text.split('\n')
                if obj.strip()
            ]
            course.prerequisites = [
                req.strip()
                for req in prerequisites_text.split('\n')
                if req.strip()
            ]
            course.save()
            
            messages.success(request, 'Learning objectives updated!')
            return redirect('instructor:course_edit', slug=course.slug)
    else:
        initial = {
            'objectives': '\n'.join(course.learning_objectives or []),
            'prerequisites': '\n'.join(course.prerequisites or []),
        }
        form = CourseObjectivesForm(initial=initial)
    
    return render(request, 'instructor/course_objectives.html', {
        'form': form,
        'course': course,
    })


@login_required(login_url='auth')
@instructor_required
def course_delete(request, slug):
    """Delete course using slug"""
    course = get_object_or_404(
        LMSCourse,
        slug=slug,
        instructor=request.user
    )
    
    if request.method == 'POST':
        course_title = course.title
        course.delete()
        messages.success(
            request,
            f'Course "{course_title}" deleted successfully!'
        )
        return redirect('instructor:course_list')
    
    return render(request, 'instructor/course_confirm_delete.html', {
        'course': course
    })


# ==================== SECTION MANAGEMENT ====================
@login_required(login_url='auth')
@instructor_required
def section_create(request, course_slug):
    """Create section using course slug"""
    course = get_object_or_404(
        LMSCourse,
        slug=course_slug,
        instructor=request.user
    )
    
    if request.method == 'POST':
        form = SectionForm(request.POST)
        if form.is_valid():
            section = form.save(commit=False)
            section.course = course
            section.save()
            messages.success(request, 'Section created successfully!')
            return redirect(
                'instructor:lesson_list',
                course_slug=course.slug
            )
    else:
        form = SectionForm()
    
    return render(request, 'instructor/section_form.html', {
        'form': form,
        'course': course,
    })


@login_required(login_url='auth')
@instructor_required
def section_edit(request, course_slug, section_id):
    """Edit section using course slug"""
    course = get_object_or_404(
        LMSCourse,
        slug=course_slug,
        instructor=request.user
    )
    section = get_object_or_404(
        LessonSection,
        id=section_id,
        course=course
    )
    
    if request.method == 'POST':
        form = SectionForm(request.POST, instance=section)
        if form.is_valid():
            form.save()
            messages.success(request, 'Section updated successfully!')
            return redirect(
                'instructor:lesson_list',
                course_slug=course.slug
            )
    else:
        form = SectionForm(instance=section)
    
    return render(request, 'instructor/section_form.html', {
        'form': form,
        'course': course,
        'section': section,
    })


@login_required(login_url='auth')
@instructor_required
def section_delete(request, course_slug, section_id):
    """Delete section using course slug"""
    course = get_object_or_404(
        LMSCourse,
        slug=course_slug,
        instructor=request.user
    )
    section = get_object_or_404(
        LessonSection,
        id=section_id,
        course=course
    )
    
    section_title = section.title
    section.delete()
    messages.success(request, f'Section "{section_title}" deleted successfully!')
    return redirect('instructor:lesson_list', course_slug=course.slug)


# ==================== LESSON MANAGEMENT ====================
@login_required(login_url='auth')
@instructor_required
def lesson_list(request, course_slug):
    """List lessons using course slug"""
    course = get_object_or_404(
        LMSCourse,
        slug=course_slug,
        instructor=request.user
    )
    
    sections = course.sections.all().prefetch_related(
        'lessons'
    ).order_by('display_order')
    
    # Get lesson type counts
    all_lessons = course.lessons.all()
    video_count = all_lessons.filter(lesson_type='video').count()
    quiz_count = all_lessons.filter(lesson_type='quiz').count()
    
    context = {
        'course': course,
        'sections': sections,
        'video_count': video_count,
        'quiz_count': quiz_count,
    }
    
    return render(request, 'instructor/lesson_list.html', context)


@login_required(login_url='auth')
@instructor_required
def lesson_create(request, course_slug):
    """Create lesson using course slug"""
    course = get_object_or_404(
        LMSCourse,
        slug=course_slug,
        instructor=request.user
    )
    
    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES, course=course)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.course = course
            lesson.save()
            messages.success(request, 'Lesson created successfully!')
            return redirect(
                'instructor:lesson_list',
                course_slug=course.slug
            )
    else:
        form = LessonForm(course=course)
    
    return render(request, 'instructor/lesson_form.html', {
        'form': form,
        'course': course,
        'lesson': None,
    })


@login_required(login_url='auth')
@instructor_required
def lesson_edit(request, course_slug, lesson_id):
    """Edit lesson using course slug"""
    course = get_object_or_404(
        LMSCourse,
        slug=course_slug,
        instructor=request.user
    )
    lesson = get_object_or_404(
        Lesson,
        id=lesson_id,
        course=course
    )
    
    if request.method == 'POST':
        form = LessonForm(
            request.POST,
            request.FILES,
            instance=lesson,
            course=course
        )
        if form.is_valid():
            form.save()
            messages.success(request, 'Lesson updated successfully!')
            return redirect(
                'instructor:lesson_list',
                course_slug=course.slug
            )
    else:
        form = LessonForm(instance=lesson, course=course)
    
    return render(request, 'instructor/lesson_form.html', {
        'form': form,
        'course': course,
        'lesson': lesson,
    })


@login_required(login_url='auth')
@instructor_required
def lesson_delete(request, course_slug, lesson_id):
    """Delete lesson using course slug"""
    course = get_object_or_404(
        LMSCourse,
        slug=course_slug,
        instructor=request.user
    )
    lesson = get_object_or_404(
        Lesson,
        id=lesson_id,
        course=course
    )
    
    lesson_title = lesson.title
    lesson.delete()
    messages.success(request, f'Lesson "{lesson_title}" deleted successfully!')
    return redirect('instructor:lesson_list', course_slug=course.slug)


# ==================== QUIZ MANAGEMENT ====================
@login_required(login_url='auth')
@instructor_required
def quiz_list(request, course_slug, lesson_slug):
    """List quizzes using slugs"""
    course = get_object_or_404(
        LMSCourse,
        slug=course_slug,
        instructor=request.user
    )
    lesson = get_object_or_404(
        Lesson,
        slug=lesson_slug,
        course=course
    )
    
    quizzes = lesson.quizzes.all().prefetch_related(
        'questions'
    ).order_by('display_order')
    
    return render(request, 'instructor/quiz_list.html', {
        'course': course,
        'lesson': lesson,
        'quizzes': quizzes,
    })


@login_required(login_url='auth')
@instructor_required
def quiz_create(request, course_slug, lesson_slug):
    """Create quiz using slugs"""
    course = get_object_or_404(
        LMSCourse,
        slug=course_slug,
        instructor=request.user
    )
    lesson = get_object_or_404(
        Lesson,
        slug=lesson_slug,
        course=course
    )
    
    if request.method == 'POST':
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.lesson = lesson
            quiz.save()
            messages.success(request, 'Quiz created successfully!')
            return redirect(
                'instructor:quiz_questions',
                course_slug=course.slug,
                lesson_slug=lesson.slug,
                quiz_slug=quiz.slug
            )
    else:
        form = QuizForm()
    
    return render(request, 'instructor/quiz_form.html', {
        'form': form,
        'course': course,
        'lesson': lesson,
        'quiz': None,
    })


@login_required(login_url='auth')
@instructor_required
def quiz_edit(request, course_slug, lesson_slug, quiz_slug):
    """Edit quiz using slugs"""
    course = get_object_or_404(
        LMSCourse,
        slug=course_slug,
        instructor=request.user
    )
    lesson = get_object_or_404(
        Lesson,
        slug=lesson_slug,
        course=course
    )
    quiz = get_object_or_404(
        Quiz,
        slug=quiz_slug,
        lesson=lesson
    )
    
    if request.method == 'POST':
        form = QuizForm(request.POST, instance=quiz)
        if form.is_valid():
            form.save()
            messages.success(request, 'Quiz updated successfully!')
            return redirect(
                'instructor:quiz_questions',
                course_slug=course.slug,
                lesson_slug=lesson.slug,
                quiz_slug=quiz.slug
            )
    else:
        form = QuizForm(instance=quiz)
    
    return render(request, 'instructor/quiz_form.html', {
        'form': form,
        'course': course,
        'lesson': lesson,
        'quiz': quiz,
    })


@login_required(login_url='auth')
@instructor_required
def quiz_questions(request, course_slug, lesson_slug, quiz_slug):
    """Manage quiz questions using slugs"""
    course = get_object_or_404(
        LMSCourse,
        slug=course_slug,
        instructor=request.user
    )
    lesson = get_object_or_404(
        Lesson,
        slug=lesson_slug,
        course=course
    )
    quiz = get_object_or_404(
        Quiz,
        slug=quiz_slug,
        lesson=lesson
    )
    
    questions = quiz.questions.all().prefetch_related(
        'answers'
    ).order_by('display_order')
    
    return render(request, 'instructor/quiz.html', {
        'course': course,
        'lesson': lesson,
        'quiz': quiz,
        'questions': questions,
    })


# ==================== QUESTION MANAGEMENT ====================
@login_required(login_url='auth')
@instructor_required
def question_create(request, course_slug, lesson_slug, quiz_slug):
    """Create question using slugs"""
    course = get_object_or_404(
        LMSCourse,
        slug=course_slug,
        instructor=request.user
    )
    lesson = get_object_or_404(
        Lesson,
        slug=lesson_slug,
        course=course
    )
    quiz = get_object_or_404(
        Quiz,
        slug=quiz_slug,
        lesson=lesson
    )
    
    if request.method == 'POST':
        form = QuizQuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.quiz = quiz
            question.save()
            messages.success(request, 'Question created successfully!')
            
            if question.question_type == 'multiple_choice':
                return redirect(
                    'instructor:question_answers',
                    course_slug=course.slug,
                    lesson_slug=lesson.slug,
                    quiz_slug=quiz.slug,
                    question_id=question.id
                )
            return redirect(
                'instructor:quiz_questions',
                course_slug=course.slug,
                lesson_slug=lesson.slug,
                quiz_slug=quiz.slug
            )
    else:
        form = QuizQuestionForm()
    
    return render(request, 'instructor/question_form.html', {
        'form': form,
        'course': course,
        'lesson': lesson,
        'quiz': quiz,
    })


@login_required(login_url='auth')
@instructor_required
def question_answers(request, course_slug, lesson_slug, quiz_slug, question_id):
    """Manage question answers using slugs"""
    course = get_object_or_404(
        LMSCourse,
        slug=course_slug,
        instructor=request.user
    )
    lesson = get_object_or_404(
        Lesson,
        slug=lesson_slug,
        course=course
    )
    quiz = get_object_or_404(
        Quiz,
        slug=quiz_slug,
        lesson=lesson
    )
    question = get_object_or_404(
        QuizQuestion,
        id=question_id,
        quiz=quiz
    )
    
    if request.method == 'POST':
        form = QuizAnswerForm(request.POST)
        if form.is_valid():
            answer = form.save(commit=False)
            answer.question = question
            answer.save()
            messages.success(request, 'Answer added successfully!')
            return redirect(
                'instructor:question_answers',
                course_slug=course.slug,
                lesson_slug=lesson.slug,
                quiz_slug=quiz.slug,
                question_id=question.id
            )
    else:
        form = QuizAnswerForm()
    
    answers = question.answers.all().order_by('display_order')
    
    return render(request, 'instructor/answer_form.html', {
        'form': form,
        'course': course,
        'lesson': lesson,
        'quiz': quiz,
        'question': question,
        'answers': answers,
    })

# ==================== ASSIGNMENT MANAGEMENT ====================
# ==================== ASSIGNMENT MANAGEMENT ====================
@login_required(login_url='auth')
@instructor_required
def assignment_list(request, course_slug, lesson_slug):
    """List assignments using slugs"""
    course = get_object_or_404(
        LMSCourse,
        slug=course_slug,
        instructor=request.user
    )
    lesson = get_object_or_404(
        Lesson,
        slug=lesson_slug,
        course=course
    )
    
    assignments = lesson.assignments.all().order_by('display_order')
    
    return render(request, 'instructor/assignments.html', {
        'course': course,
        'lesson': lesson,
        'assignments': assignments,
    })


@login_required(login_url='auth')
@instructor_required
def assignment_create(request, course_slug, lesson_slug):
    """Create assignment using slugs"""
    course = get_object_or_404(
        LMSCourse,
        slug=course_slug,
        instructor=request.user
    )
    lesson = get_object_or_404(
        Lesson,
        slug=lesson_slug,
        course=course
    )
    
    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.lesson = lesson
            assignment.save()
            messages.success(request, 'Assignment created successfully!')
            return redirect(
                'instructor:assignment_list',
                course_slug=course.slug,
                lesson_slug=lesson.slug
            )
    else:
        form = AssignmentForm()
    
    return render(request, 'instructor/assignment_form.html', {
        'form': form,
        'course': course,
        'lesson': lesson,
        'assignment': None,
    })


@login_required(login_url='auth')
@instructor_required
def assignment_edit(request, course_slug, lesson_slug, assignment_slug):
    """Edit assignment using slugs"""
    course = get_object_or_404(
        LMSCourse,
        slug=course_slug,
        instructor=request.user
    )
    lesson = get_object_or_404(
        Lesson,
        slug=lesson_slug,
        course=course
    )
    assignment = get_object_or_404(
        Assignment,
        slug=assignment_slug,
        lesson=lesson
    )
    
    if request.method == 'POST':
        form = AssignmentForm(
            request.POST,
            request.FILES,
            instance=assignment
        )
        if form.is_valid():
            form.save()
            messages.success(request, 'Assignment updated successfully!')
            return redirect(
                'instructor:assignment_list',
                course_slug=course.slug,
                lesson_slug=lesson.slug
            )
    else:
        form = AssignmentForm(instance=assignment)
    
    return render(request, 'instructor/assignment_form.html', {
        'form': form,
        'course': course,
        'lesson': lesson,
        'assignment': assignment,
    })


@login_required(login_url='auth')
@instructor_required
def assignment_submissions(request, course_slug, assignment_slug):
    """View submissions using slugs"""
    course = get_object_or_404(
        LMSCourse,
        slug=course_slug,
        instructor=request.user
    )
    assignment = get_object_or_404(
        Assignment,
        slug=assignment_slug,
        lesson__course=course
    )
    
    submissions = assignment.submissions.all().select_related(
        'student'
    ).order_by('-submitted_at')
    
    pending_count = submissions.filter(status='submitted').count()
    graded_count = submissions.filter(status='graded').count()
    late_count = submissions.filter(is_late=True).count()

    return render(request, 'instructor/assignment_submissions.html', {
        'course': course,
        'assignment': assignment,
        'submissions': submissions,
        'pending_count': pending_count,
        'graded_count': graded_count,
        'late_count': late_count,
    })


@login_required(login_url='auth')
@instructor_required
def grade_submission(request, course_slug, submission_id):
    """Grade submission using course slug and submission ID"""
    # Get the submission first
    submission = get_object_or_404(AssignmentSubmission, id=submission_id)
    
    # Get assignment from the submission
    assignment = submission.assignment
    
    # Verify course ownership
    course = get_object_or_404(
        LMSCourse,
        slug=course_slug,
        instructor=request.user
    )
    
    # Verify the assignment belongs to this course
    if assignment.lesson.course != course:
        raise PermissionDenied("This submission does not belong to your course.")
    
    if request.method == 'POST':
        score = request.POST.get('score')
        feedback = request.POST.get('feedback', '')
        
        submission.score = score
        submission.feedback = feedback
        submission.status = 'graded'
        submission.graded_by = request.user
        submission.graded_at = timezone.now()
        submission.save()
        
        messages.success(request, 'Submission graded successfully!')
        return redirect(
            'instructor:assignment_submissions',
            course_slug=course.slug,
            assignment_slug=assignment.slug
        )
    
    return render(request, 'instructor/grade_submission.html', {
        'course': course,
        'assignment': assignment,
        'submission': submission,
    })


# ==================== STUDENT MANAGEMENT ====================
@login_required(login_url='auth')
@instructor_required
def students_list(request, course_slug):
    """List students using course slug"""
    course = get_object_or_404(
        LMSCourse,
        slug=course_slug,
        instructor=request.user
    )
    
    enrollments = course.enrollments.all().select_related(
        'student'
    ).order_by('-enrolled_at')
    
    return render(request, 'instructor/students.html', {
        'course': course,
        'enrollments': enrollments,
    })


@login_required(login_url='auth')
@instructor_required
def student_progress(request, course_slug, student_id):
    """View student progress using course slug"""
    course = get_object_or_404(
        LMSCourse,
        slug=course_slug,
        instructor=request.user
    )
    
    enrollment = get_object_or_404(
        Enrollment,
        course=course,
        student_id=student_id
    )
    
    lesson_progress = enrollment.lesson_progress.all().select_related(
        'lesson'
    ).order_by('lesson__display_order')
    
    return render(request, 'instructor/student_detail_progress.html', {
        'course': course,
        'enrollment': enrollment,
        'lesson_progress': lesson_progress,
    })

@login_required(login_url='auth')
@instructor_required
def enroll_student(request, course_slug):
    """Manually enroll a student in a course"""
    course = get_object_or_404(
        LMSCourse,
        slug=course_slug,
        instructor=request.user
    )
    
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        enrollment_date = request.POST.get('enrollment_date')
        send_welcome = request.POST.get('send_welcome_email') == 'on'
        
        try:
            student = User.objects.get(id=student_id)
            
            # Check if already enrolled
            if Enrollment.objects.filter(
                course=course,
                student=student
            ).exists():
                messages.warning(
                    request,
                    f'{student.get_full_name()} is already enrolled in this course.'
                )
            else:
                # Create enrollment
                enrollment = Enrollment.objects.create(
                    course=course,
                    student=student,
                    enrolled_at=enrollment_date if enrollment_date else timezone.now(),
                    status='active'
                )
                
                # Send welcome email if requested
                if send_welcome:
                    # TODO: Implement email sending functionality
                    pass
                
                messages.success(
                    request,
                    f'{student.get_full_name()} has been successfully enrolled in {course.title}!'
                )
        except User.DoesNotExist:
            messages.error(request, 'Student not found.')
    
    return redirect('instructor:students_list', course_slug=course.slug)

# ==================== ANNOUNCEMENTS ====================
@login_required(login_url='auth')
@instructor_required
def announcement_create(request, course_slug):
    """Create announcement using course slug"""
    course = get_object_or_404(
        LMSCourse,
        slug=course_slug,
        instructor=request.user
    )
    
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.course = course
            announcement.announcement_type = 'course'
            announcement.created_by = request.user
            announcement.save()
            messages.success(request, 'Announcement created successfully!')
            return redirect('instructor:course_edit', slug=course.slug)
    else:
        form = AnnouncementForm()
    
    return render(request, 'instructor/announcement_form.html', {
        'form': form,
        'course': course,
    })

# ==================== ASSESSMENT OVERVIEW VIEWS ====================
@login_required(login_url='auth')
@instructor_required
def all_quizzes(request):
    """View all quizzes across all instructor's courses"""
    courses = LMSCourse.objects.filter(instructor=request.user)
    quizzes = Quiz.objects.filter(
        lesson__course__in=courses
    ).select_related(
        'lesson',
        'lesson__course'
    ).prefetch_related('questions').order_by('-created_at')
    
    context = {
        'quizzes': quizzes,
    }
    return render(request, 'instructor/all_quizzes.html', context)


@login_required(login_url='auth')
@instructor_required
def all_assignments(request):
    """View all assignments across all instructor's courses"""
    courses = LMSCourse.objects.filter(instructor=request.user)
    assignments = Assignment.objects.filter(
        lesson__course__in=courses
    ).select_related(
        'lesson',
        'lesson__course'
    ).order_by('-created_at')
    
    context = {
        'assignments': assignments,
    }
    return render(request, 'instructor/all_assignments.html', context)

@login_required(login_url='auth')
@instructor_required
@require_POST
def delete_answer(request, course_slug, lesson_slug, quiz_slug, question_id, answer_id):
    """Delete a quiz answer"""
    course = get_object_or_404(LMSCourse, slug=course_slug, instructor=request.user)
    lesson = get_object_or_404(Lesson, slug=lesson_slug, course=course)
    quiz = get_object_or_404(Quiz, slug=quiz_slug, lesson=lesson)
    question = get_object_or_404(QuizQuestion, id=question_id, quiz=quiz)
    answer = get_object_or_404(QuizAnswer, id=answer_id, question=question)
    
    answer.delete()
    messages.success(request, 'Answer deleted successfully!')
    
    return redirect('instructor:question_answers', 
                    course_slug=course.slug, 
                    lesson_slug=lesson.slug, 
                    quiz_slug=quiz.slug, 
                    question_id=question.id)

@login_required(login_url='auth')
@instructor_required
@require_POST
def delete_question(request, course_slug, lesson_slug, quiz_slug, question_id):
    """Delete a quiz question"""
    course = get_object_or_404(LMSCourse, slug=course_slug, instructor=request.user)
    lesson = get_object_or_404(Lesson, slug=lesson_slug, course=course)
    quiz = get_object_or_404(Quiz, slug=quiz_slug, lesson=lesson)
    question = get_object_or_404(QuizQuestion, id=question_id, quiz=quiz)
    
    question.delete()
    messages.success(request, 'Question deleted successfully!')
    
    return redirect('instructor:quiz_questions', 
                    course_slug=course.slug, 
                    lesson_slug=lesson.slug, 
                    quiz_slug=quiz.slug)

@login_required(login_url='auth')
@instructor_required
def course_statistics(request):
    """
    Course statistics overview
    Shows enrollment trends, completion rates, and performance metrics
    """
    courses = LMSCourse.objects.filter(
        instructor=request.user
    ).annotate(
        enrollment_count=Count('enrollments'),
        avg_rating=Avg('reviews__rating'),
        completion_count=Count(
            'enrollments',
            filter=Q(enrollments__status='completed')
        )
    ).order_by('-created_at')
    
    # Overall statistics
    total_enrollments = Enrollment.objects.filter(
        course__instructor=request.user
    ).count()
    
    active_students = Enrollment.objects.filter(
        course__instructor=request.user,
        status='active'
    ).count()
    
    completed_courses = Enrollment.objects.filter(
        course__instructor=request.user,
        status='completed'
    ).count()
    
    avg_course_rating = Review.objects.filter(
        course__instructor=request.user,
        is_approved=True
    ).aggregate(Avg('rating'))['rating__avg'] or 0
    
    # Enrollment trends (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    daily_enrollments = Enrollment.objects.filter(
        course__instructor=request.user,
        enrolled_at__gte=thirty_days_ago
    ).annotate(
        date=TruncDate('enrolled_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    # Convert to list for JSON serialization
    enrollment_data = []
    for item in daily_enrollments:
        enrollment_data.append({
            'date': item['date'].isoformat(),
            'count': item['count']
        })
    
    context = {
        'courses': courses,
        'total_enrollments': total_enrollments,
        'active_students': active_students,
        'completed_courses': completed_courses,
        'avg_course_rating': round(avg_course_rating, 1),
        'daily_enrollments': enrollment_data,
    }
    
    return render(
        request, 
        'instructor/analytics/course_statistics.html', 
        context
    )


@login_required(login_url='auth')
@instructor_required
def student_analytics_progress(request):
    """
    Student progress tracking
    Shows individual student performance across all courses
    """
    # Get all courses taught by instructor
    instructor_courses = LMSCourse.objects.filter(
        instructor=request.user
    )
    
    # Filter by course if specified
    course_id = request.GET.get('course')
    if course_id:
        enrollments = Enrollment.objects.filter(
            course_id=course_id,
            course__instructor=request.user
        )
        selected_course = get_object_or_404(
            LMSCourse, 
            id=course_id, 
            instructor=request.user
        )
    else:
        enrollments = Enrollment.objects.filter(
            course__instructor=request.user
        )
        selected_course = None
    
    # Get enrollments with related data
    enrollments = enrollments.select_related(
        'student', 
        'course'
    ).annotate(
        total_lessons=Count('course__lessons', distinct=True),
        avg_quiz_score=Avg(
            'student__quiz_attempts__percentage',
            filter=Q(student__quiz_attempts__quiz__lesson__course=F('course'))
        )
    ).order_by('-enrolled_at')
    
    # Student performance summary
    total_students = enrollments.count()
    struggling_students = enrollments.filter(
        progress_percentage__lt=30
    ).count()
    high_performers = enrollments.filter(
        progress_percentage__gte=80
    ).count()
    
    context = {
        'enrollments': enrollments,
        'courses': instructor_courses,
        'selected_course': selected_course,
        'total_students': total_students,
        'struggling_students': struggling_students,
        'high_performers': high_performers,
    }
    
    return render(
        request, 
        'instructor/analytics/student_progress.html', 
        context
    )


@login_required(login_url='auth')
@instructor_required
def reviews_ratings(request):
    """
    Course reviews and ratings analysis
    Shows detailed feedback and rating trends
    """
    # Get all reviews for instructor's courses
    reviews = Review.objects.filter(
        course__instructor=request.user,
        is_approved=True
    ).select_related(
        'student', 
        'course'
    ).order_by('-created_at')
    
    # Filter by course if specified
    course_id = request.GET.get('course')
    if course_id:
        reviews = reviews.filter(course_id=course_id)
        selected_course = get_object_or_404(
            LMSCourse, 
            id=course_id, 
            instructor=request.user
        )
    else:
        selected_course = None
    
    # Rating statistics
    total_reviews = reviews.count()
    avg_rating = reviews.aggregate(
        Avg('rating')
    )['rating__avg'] or 0
    
    # Rating distribution
    rating_distribution = {
        5: reviews.filter(rating=5).count(),
        4: reviews.filter(rating=4).count(),
        3: reviews.filter(rating=3).count(),
        2: reviews.filter(rating=2).count(),
        1: reviews.filter(rating=1).count(),
    }
    
    # Course breakdown
    course_ratings = LMSCourse.objects.filter(
        instructor=request.user
    ).annotate(
        review_count=Count('reviews', filter=Q(reviews__is_approved=True)),
        avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True))
    ).filter(
        review_count__gt=0
    ).order_by('-avg_rating')
    
    # Monthly trend (last 6 months)
    six_months_ago = timezone.now() - timedelta(days=180)
    monthly_reviews = reviews.filter(
        created_at__gte=six_months_ago
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        count=Count('id'),
        avg=Avg('rating')
    ).order_by('month')
    
    # Convert to list for JSON serialization
    monthly_data = []
    for item in monthly_reviews:
        monthly_data.append({
            'month': item['month'].isoformat(),
            'count': item['count'],
            'avg': float(item['avg'])
        })
    
    context = {
        'reviews': reviews[:50],  # Limit to recent 50
        'courses': LMSCourse.objects.filter(
            instructor=request.user
        ),
        'selected_course': selected_course,
        'total_reviews': total_reviews,
        'avg_rating': round(avg_rating, 1),
        'rating_distribution': rating_distribution,
        'course_ratings': course_ratings,
        'monthly_reviews': monthly_data,
    }
    
    return render(
        request, 
        'instructor/analytics/reviews_ratings.html', 
        context
    )

@login_required(login_url='auth')
@instructor_required
def resources(request):
    """
    Pool and display all resources from courses
    """
    # Get all courses for this instructor
    instructor_courses = LMSCourse.objects.filter(
        instructor=request.user
    ).prefetch_related(
        'lessons',
        'lessons__assignments'
    )
    
    # Pool resources from lessons
    lesson_videos = []
    lesson_docs = []
    
    for course in instructor_courses:
        for lesson in course.lessons.all():
            # Videos
            if lesson.video_url:
                lesson_videos.append({
                    'course': course,
                    'lesson': lesson,
                    'url': lesson.video_url,
                    'type': 'video',
                    'uploaded': lesson.created_at
                })
            
            # Documents
            if lesson.file:
                lesson_docs.append({
                    'course': course,
                    'lesson': lesson,
                    'file': lesson.document,
                    'name': lesson.document.name.split('/')[-1],
                    'type': 'document',
                    'uploaded': lesson.created_at
                })
    
    # Pool assignment files
    assignment_files = []
    for course in instructor_courses:
        for lesson in course.lessons.all():
            for assignment in lesson.assignments.all():
                if assignment.attachment:
                    assignment_files.append({
                        'course': course,
                        'lesson': lesson,
                        'assignment': assignment,
                        'file': assignment.attachment,
                        'name': assignment.attachment.name.split('/')[-1],
                        'type': 'assignment',
                        'uploaded': assignment.created_at
                    })
    
    # Statistics
    stats = {
        'total_videos': len(lesson_videos),
        'total_docs': len(lesson_docs),
        'total_assignments': len(assignment_files),
        'total_courses': instructor_courses.count(),
    }
    
    context = {
        'lesson_videos': lesson_videos,
        'lesson_docs': lesson_docs,
        'assignment_files': assignment_files,
        'stats': stats,
        'courses': instructor_courses,
    }
    
    return render(request, 'instructor/resources.html', context)

# ==================== PROFILE VIEW ====================
@login_required(login_url='auth')
@instructor_required
def instructor_profile(request):
    """View and edit instructor profile"""
    
    # Get instructor statistics
    total_courses = LMSCourse.objects.filter(
        instructor=request.user
    ).count()
    
    total_students = Enrollment.objects.filter(
        course__instructor=request.user
    ).values('student').distinct().count()
    
    avg_rating = LMSCourse.objects.filter(
        instructor=request.user
    ).aggregate(avg_rating=Avg('average_rating'))['avg_rating'] or 0
    
    total_reviews = LMSCourse.objects.filter(
        instructor=request.user
    ).aggregate(
        total=Count('reviews')
    )['total']
    
    if request.method == 'POST':
        form = InstructorProfileForm(
            request.POST,
            request.FILES,
            instance=request.user.profile,
            user=request.user
        )
        
        if form.is_valid():
            # Update User model fields
            user = request.user
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()
            
            # Update Profile model fields
            form.save()
            
            messages.success(
                request,
                'Your profile has been updated successfully!'
            )
            return redirect('instructor:profile')
    else:
        form = InstructorProfileForm(
            instance=request.user.profile,
            user=request.user
        )
    
    context = {
        'form': form,
        'page_title': 'My Profile',
        'total_courses': total_courses,
        'total_students': total_students,
        'avg_rating': round(avg_rating, 1),
        'total_reviews': total_reviews,
    }
    return render(request, 'instructor/profile.html', context)


# ==================== SETTINGS VIEW ====================
@login_required(login_url='auth')
@instructor_required
def instructor_settings(request):
    """Manage instructor account settings"""
    
    settings_form = InstructorSettingsForm(
        instance=request.user.profile
    )
    password_form = PasswordChangeForm(user=request.user)
    
    if request.method == 'POST':
        if 'update_settings' in request.POST:
            settings_form = InstructorSettingsForm(
                request.POST,
                instance=request.user.profile
            )
            
            if settings_form.is_valid():
                settings_form.save()
                messages.success(
                    request,
                    'Settings updated successfully!'
                )
                return redirect('instructor:settings')
        
        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(
                user=request.user,
                data=request.POST
            )
            
            if password_form.is_valid():
                # Change password
                new_password = password_form.cleaned_data['new_password']
                request.user.set_password(new_password)
                request.user.save()
                
                # Keep user logged in
                update_session_auth_hash(request, request.user)
                
                messages.success(
                    request,
                    'Your password has been changed successfully!'
                )
                return redirect('instructor:settings')
    
    context = {
        'settings_form': settings_form,
        'password_form': password_form,
        'page_title': 'Settings',
    }
    return render(request, 'instructor/settings.html', context)


# ==================== HELP & SUPPORT VIEW ====================
@login_required(login_url='auth')
@instructor_required
def help_support(request):
    """Help and support page with FAQs and ticket submission"""
    
    if request.method == 'POST':
        form = SupportTicketForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Send email to support team
            subject = f"[{form.cleaned_data['priority'].upper()}] {form.cleaned_data['subject']}"
            message = f"""
New Support Ticket from Instructor

From: {request.user.get_full_name()} ({request.user.email})
Category: {form.cleaned_data['category']}
Priority: {form.cleaned_data['priority']}

Message:
{form.cleaned_data['message']}

---
User ID: {request.user.id}
Role: Instructor
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
                    'Your support ticket has been submitted successfully! '
                    'Our team will get back to you within 24-48 hours.'
                )
                return redirect('instructor:help_support')
            
            except Exception as e:
                messages.error(
                    request,
                    'An error occurred while submitting your ticket. '
                    'Please try again later.'
                )
    else:
        form = SupportTicketForm()
    
    # FAQs data
    faqs = [
        {
            'question': 'How do I create a new course?',
            'answer': 'Navigate to Courses > Create Course from the sidebar menu. '
                     'Fill in the course details, upload a thumbnail, and click Save. '
                     'You can then add sections, lessons, and assessments.'
        },
        {
            'question': 'How do I upload course materials?',
            'answer': 'When creating or editing a lesson, you can upload videos, '
                     'documents, and other materials. Supported formats include '
                     'PDF, DOCX, MP4, and more.'
        },
        {
            'question': 'How do I grade student assignments?',
            'answer': 'Go to Assessments > All Assignments and click on any assignment. '
                     'You\'ll see all submissions. Click on a submission to view, '
                     'provide feedback, and assign a grade.'
        },
        {
            'question': 'Can I track student progress?',
            'answer': 'Yes! Go to Analytics > Student Progress to view detailed '
                     'reports on each student\'s performance, completion rates, '
                     'and engagement metrics.'
        },
        {
            'question': 'How do I communicate with students?',
            'answer': 'You can create announcements for your courses, respond to '
                     'discussion forum posts, and provide feedback on assignments. '
                     'Students can also message you directly.'
        },
        {
            'question': 'What payment methods are supported?',
            'answer': 'We support credit/debit cards, bank transfers, and various '
                     'mobile payment options. Payments are processed securely and '
                     'you receive monthly payouts.'
        },
        {
            'question': 'How do I issue certificates?',
            'answer': 'Certificates are automatically generated when students complete '
                     'all course requirements. You can customize certificate templates '
                     'in your course settings.'
        },
        {
            'question': 'What are the video upload limits?',
            'answer': 'Video files should not exceed 2GB per file. We recommend '
                     'using MP4 format at 1080p resolution for best quality and '
                     'compatibility.'
        },
    ]
    
    # Quick links
    quick_links = [
        {
            'title': 'Getting Started Guide',
            'icon': 'fa-book-open',
            'url': '#',
            'description': 'Learn the basics of creating and managing courses'
        },
        {
            'title': 'Video Tutorials',
            'icon': 'fa-video',
            'url': '#',
            'description': 'Watch step-by-step video guides'
        },
        {
            'title': 'Best Practices',
            'icon': 'fa-lightbulb',
            'url': '#',
            'description': 'Tips for creating engaging course content'
        },
        {
            'title': 'Community Forum',
            'icon': 'fa-users',
            'url': '#',
            'description': 'Connect with other instructors'
        },
    ]
    
    context = {
        'form': form,
        'faqs': faqs,
        'quick_links': quick_links,
        'page_title': 'Help & Support',
    }
    return render(request, 'instructor/help_support.html', context)