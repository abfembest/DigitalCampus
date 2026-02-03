from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg, Sum
from django.utils import timezone
from eduweb.models import (
    LMSCourse, Lesson, LessonSection, Quiz, QuizQuestion,
    QuizAnswer, Assignment, AssignmentSubmission, Enrollment,
    Announcement
)
from .forms import (
    CourseForm, CourseObjectivesForm, LessonForm, SectionForm,
    QuizForm, QuizQuestionForm, QuizAnswerForm, AssignmentForm,
    AnnouncementForm
)


# ==================== DASHBOARD ====================
@login_required
def dashboard(request):
    """Instructor dashboard with comprehensive statistics"""
    courses = LMSCourse.objects.filter(
        instructor=request.user
    ).annotate(
        total_enrollments=Count('enrollments')
    ).select_related().prefetch_related('enrollments')[:5]
    
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
@login_required
def course_list(request):
    """List all instructor courses with statistics"""
    courses = LMSCourse.objects.filter(
        instructor=request.user
    ).annotate(
        enrollment_count=Count('enrollments'),
        average_rating=Avg('reviews__rating')
    ).order_by('-created_at')
    
    return render(request, 'instructor/course_list.html', {
        'courses': courses
    })


@login_required
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


@login_required
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


@login_required
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


@login_required
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
@login_required
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


@login_required
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


@login_required
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
    
    if request.method == 'POST':
        section.delete()
        messages.success(request, 'Section deleted successfully!')
        return redirect(
            'instructor:lesson_list',
            course_slug=course.slug
        )
    
    return render(request, 'instructor/section_confirm_delete.html', {
        'course': course,
        'section': section,
    })


# ==================== LESSON MANAGEMENT ====================
@login_required
def lesson_list(request, course_slug):
    """List lessons using course slug"""
    course = get_object_or_404(
        LMSCourse,
        slug=course_slug,
        instructor=request.user
    )
    
    sections = course.sections.all().prefetch_related('lessons')
    
    return render(request, 'instructor/lesson_list.html', {
        'course': course,
        'sections': sections,
    })


@login_required
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


@login_required
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


@login_required
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
    
    if request.method == 'POST':
        lesson.delete()
        messages.success(request, 'Lesson deleted successfully!')
        return redirect(
            'instructor:lesson_list',
            course_slug=course.slug
        )
    
    return render(request, 'instructor/lesson_confirm_delete.html', {
        'course': course,
        'lesson': lesson,
    })


# ==================== QUIZ MANAGEMENT ====================
@login_required
def quiz_list(request, course_slug, lesson_id):
    """List quizzes using course slug"""
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
    
    quizzes = lesson.quizzes.all().annotate(
        question_count=Count('questions')
    )
    
    return render(request, 'instructor/quiz_list.html', {
        'course': course,
        'lesson': lesson,
        'quizzes': quizzes,
    })


@login_required
def quiz_create(request, course_slug, lesson_id):
    """Create quiz using course slug"""
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
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.lesson = lesson
            quiz.save()
            messages.success(request, 'Quiz created successfully!')
            return redirect(
                'instructor:quiz_list',
                course_slug=course.slug,
                lesson_id=lesson.id
            )
    else:
        form = QuizForm()
    
    return render(request, 'instructor/quiz_form.html', {
        'form': form,
        'course': course,
        'lesson': lesson,
        'quiz': None,
    })


@login_required
def quiz_edit(request, course_slug, lesson_id, quiz_id):
    """Edit quiz using course slug"""
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
    quiz = get_object_or_404(
        Quiz,
        id=quiz_id,
        lesson=lesson
    )
    
    if request.method == 'POST':
        form = QuizForm(request.POST, instance=quiz)
        if form.is_valid():
            form.save()
            messages.success(request, 'Quiz updated successfully!')
            return redirect(
                'instructor:quiz_list',
                course_slug=course.slug,
                lesson_id=lesson.id
            )
    else:
        form = QuizForm(instance=quiz)
    
    return render(request, 'instructor/quiz_form.html', {
        'form': form,
        'course': course,
        'lesson': lesson,
        'quiz': quiz,
    })


@login_required
def quiz_questions(request, course_slug, lesson_id, quiz_id):
    """Manage quiz questions using course slug"""
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
    quiz = get_object_or_404(
        Quiz,
        id=quiz_id,
        lesson=lesson
    )
    
    questions = quiz.questions.all().prefetch_related('answers')
    
    return render(request, 'instructor/quiz_questions.html', {
        'course': course,
        'lesson': lesson,
        'quiz': quiz,
        'questions': questions,
    })


@login_required
def question_create(request, course_slug, lesson_id, quiz_id):
    """Create question using course slug"""
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
    quiz = get_object_or_404(
        Quiz,
        id=quiz_id,
        lesson=lesson
    )
    
    if request.method == 'POST':
        form = QuizQuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.quiz = quiz
            question.save()
            messages.success(request, 'Question created successfully!')
            return redirect(
                'instructor:quiz_questions',
                course_slug=course.slug,
                lesson_id=lesson.id,
                quiz_id=quiz.id
            )
    else:
        form = QuizQuestionForm()
    
    return render(request, 'instructor/question_form.html', {
        'form': form,
        'course': course,
        'lesson': lesson,
        'quiz': quiz,
    })


@login_required
def question_answers(request, course_slug, lesson_id, quiz_id, question_id):
    """Manage question answers using course slug"""
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
    quiz = get_object_or_404(
        Quiz,
        id=quiz_id,
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
                lesson_id=lesson.id,
                quiz_id=quiz.id,
                question_id=question.id
            )
    else:
        form = QuizAnswerForm()
    
    answers = question.answers.all()
    
    return render(request, 'instructor/question_answers.html', {
        'form': form,
        'course': course,
        'lesson': lesson,
        'quiz': quiz,
        'question': question,
        'answers': answers,
    })


# ==================== ASSIGNMENT MANAGEMENT ====================
@login_required
def assignment_list(request, course_slug, lesson_id):
    """List assignments using course slug"""
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
    
    assignments = lesson.assignments.all().annotate(
        submission_count=Count('submissions')
    ).order_by('display_order')
    
    return render(request, 'instructor/assignments.html', {
        'course': course,
        'lesson': lesson,
        'assignments': assignments,
    })


@login_required
def assignment_create(request, course_slug, lesson_id):
    """Create assignment using course slug"""
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
        form = AssignmentForm(request.POST, request.FILES)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.lesson = lesson
            assignment.save()
            messages.success(request, 'Assignment created successfully!')
            return redirect(
                'instructor:assignment_list',
                course_slug=course.slug,
                lesson_id=lesson.id
            )
    else:
        form = AssignmentForm()
    
    return render(request, 'instructor/assignment_form.html', {
        'form': form,
        'course': course,
        'lesson': lesson,
        'assignment': None,
    })


@login_required
def assignment_edit(request, course_slug, lesson_id, assignment_id):
    """Edit assignment using course slug"""
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
    assignment = get_object_or_404(
        Assignment,
        id=assignment_id,
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
                lesson_id=lesson.id
            )
    else:
        form = AssignmentForm(instance=assignment)
    
    return render(request, 'instructor/assignment_form.html', {
        'form': form,
        'course': course,
        'lesson': lesson,
        'assignment': assignment,
    })


@login_required
def assignment_submissions(request, course_slug, assignment_id):
    """View submissions using course slug"""
    course = get_object_or_404(
        LMSCourse,
        slug=course_slug,
        instructor=request.user
    )
    assignment = get_object_or_404(
        Assignment,
        id=assignment_id,
        lesson__course=course
    )
    
    submissions = assignment.submissions.all().select_related(
        'student'
    ).order_by('-submitted_at')
    
    return render(request, 'instructor/assignment_submissions.html', {
        'course': course,
        'assignment': assignment,
        'submissions': submissions,
    })


@login_required
def grade_submission(request, course_slug, submission_id):
    """Grade submission using course slug"""
    course = get_object_or_404(
        LMSCourse,
        slug=course_slug,
        instructor=request.user
    )
    submission = get_object_or_404(
        AssignmentSubmission,
        id=submission_id,
        assignment__lesson__course=course
    )
    
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
            assignment_id=submission.assignment.id
        )
    
    return render(request, 'instructor/grade_submission.html', {
        'course': course,
        'submission': submission,
    })


# ==================== STUDENT MANAGEMENT ====================
@login_required
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


@login_required
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
    
    return render(request, 'instructor/student_progress.html', {
        'course': course,
        'enrollment': enrollment,
        'lesson_progress': lesson_progress,
    })


# ==================== ANNOUNCEMENTS ====================
@login_required
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