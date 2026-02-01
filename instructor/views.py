from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q, Avg
from django.utils import timezone
from django.http import JsonResponse
from eduweb.models import (
    LMSCourse, Lesson, LessonSection, Quiz, QuizQuestion,
    QuizAnswer, Assignment, AssignmentSubmission, Enrollment,
    Announcement, CourseCategory
)
from .forms import (
    CourseForm, CourseObjectivesForm, LessonForm, SectionForm,
    QuizForm, QuizQuestionForm, QuizAnswerForm, AssignmentForm,
    AnnouncementForm
)


# ==================== DASHBOARD ====================
@login_required
def dashboard(request):
    """Instructor dashboard view"""
    courses = LMSCourse.objects.filter(instructor=request.user)
    
    # Statistics
    total_courses = courses.count()
    published_courses = courses.filter(is_published=True).count()
    total_students = Enrollment.objects.filter(
        course__instructor=request.user
    ).count()
    
    # Pending submissions
    pending_submissions = AssignmentSubmission.objects.filter(
        assignment__lesson__course__instructor=request.user,
        status='submitted'
    ).count()
    
    # Recent enrollments
    recent_enrollments = Enrollment.objects.filter(
        course__instructor=request.user
    ).select_related('student', 'course')[:10]
    
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
    """List all courses by instructor"""
    courses = LMSCourse.objects.filter(
        instructor=request.user
    ).annotate(
        enrollment_count=Count('enrollments')
    ).order_by('-created_at')
    
    context = {'courses': courses}
    return render(request, 'instructor/course_list.html', context)


@login_required
def course_create(request):
    """Create a new course"""
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.instructor = request.user
            course.save()
            messages.success(request, 'Course created successfully!')
            return redirect('instructor:course_edit', slug=course.slug)
    else:
        form = CourseForm()
    
    context = {'form': form, 'course': None}
    return render(request, 'instructor/course_form.html', context)


@login_required
def course_edit(request, slug):
    """Edit course details"""
    course = get_object_or_404(
        LMSCourse,
        slug=slug,
        instructor=request.user
    )
    
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, 'Course updated successfully!')
            return redirect('instructor:course_edit', slug=course.slug)
    else:
        form = CourseForm(instance=course)
    
    # Statistics
    stats = {
        'total_students': course.enrollments.count(),
        'total_lessons': course.lessons.count(),
        'total_sections': course.sections.count(),
    }
    
    context = {
        'form': form,
        'course': course,
        'stats': stats,
    }
    return render(request, 'instructor/course_form.html', context)


@login_required
def course_objectives(request, slug):
    """Manage course learning objectives"""
    course = get_object_or_404(
        LMSCourse,
        slug=slug,
        instructor=request.user
    )
    
    if request.method == 'POST':
        form = CourseObjectivesForm(request.POST, instance=course)
        if form.is_valid():
            objectives = form.cleaned_data['objectives'].split('\n')
            prerequisites = form.cleaned_data.get('prerequisites', '').split('\n')
            
            # Filter empty lines
            course.learning_objectives = [o.strip() for o in objectives if o.strip()]
            course.prerequisites = [p.strip() for p in prerequisites if p.strip()]
            course.save()
            
            messages.success(request, 'Objectives updated successfully!')
            return redirect('instructor:course_edit', slug=course.slug)
    else:
        # Prepare initial data
        initial = {
            'objectives': '\n'.join(course.learning_objectives),
            'prerequisites': '\n'.join(course.prerequisites),
        }
        form = CourseObjectivesForm(initial=initial)
    
    context = {
        'form': form,
        'course': course,
    }
    return render(request, 'instructor/course_objectives.html', context)


@login_required
def course_delete(request, slug):
    """Delete a course"""
    course = get_object_or_404(
        LMSCourse,
        slug=slug,
        instructor=request.user
    )
    
    if request.method == 'POST':
        course.delete()
        messages.success(request, 'Course deleted successfully!')
        return redirect('instructor:course_list')
    
    context = {'course': course}
    return render(request, 'instructor/course_confirm_delete.html', context)


# ==================== SECTION MANAGEMENT ====================
@login_required
def section_create(request, course_slug):
    """Create a new section"""
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
            return redirect('instructor:lesson_list', course_slug=course.slug)
    else:
        form = SectionForm()
    
    context = {
        'form': form,
        'course': course,
    }
    return render(request, 'instructor/section_form.html', context)


@login_required
def section_edit(request, course_slug, section_id):
    """Edit a section"""
    course = get_object_or_404(
        LMSCourse,
        slug=course_slug,
        instructor=request.user
    )
    section = get_object_or_404(LessonSection, id=section_id, course=course)
    
    if request.method == 'POST':
        form = SectionForm(request.POST, instance=section)
        if form.is_valid():
            form.save()
            messages.success(request, 'Section updated successfully!')
            return redirect('instructor:lesson_list', course_slug=course.slug)
    else:
        form = SectionForm(instance=section)
    
    context = {
        'form': form,
        'course': course,
        'section': section,
    }
    return render(request, 'instructor/section_form.html', context)


@login_required
def section_delete(request, course_slug, section_id):
    """Delete a section"""
    course = get_object_or_404(
        LMSCourse,
        slug=course_slug,
        instructor=request.user
    )
    section = get_object_or_404(LessonSection, id=section_id, course=course)
    
    if request.method == 'POST':
        section.delete()
        messages.success(request, 'Section deleted successfully!')
        return redirect('instructor:lesson_list', course_slug=course.slug)
    
    context = {
        'course': course,
        'section': section,
    }
    return render(request, 'instructor/section_confirm_delete.html', context)


# ==================== LESSON MANAGEMENT ====================
@login_required
def lesson_list(request, course_slug):
    """List all lessons in a course"""
    course = get_object_or_404(
        LMSCourse,
        slug=course_slug,
        instructor=request.user
    )
    
    sections = course.sections.all().prefetch_related('lessons')
    lessons_without_section = course.lessons.filter(
        section__isnull=True
    ).order_by('display_order')
    
    context = {
        'course': course,
        'sections': sections,
        'lessons_without_section': lessons_without_section,
    }
    return render(request, 'instructor/lessons.html', context)


@login_required
def lesson_create(request, course_slug):
    """Create a new lesson"""
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
            return redirect('instructor:lesson_list', course_slug=course.slug)
    else:
        form = LessonForm(course=course)
    
    context = {
        'form': form,
        'course': course,
        'lesson': None,
    }
    return render(request, 'instructor/lesson_form.html', context)


@login_required
def lesson_edit(request, course_slug, lesson_id):
    """Edit a lesson"""
    course = get_object_or_404(
        LMSCourse,
        slug=course_slug,
        instructor=request.user
    )
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    
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
            return redirect('instructor:lesson_list', course_slug=course.slug)
    else:
        form = LessonForm(instance=lesson, course=course)
    
    context = {
        'form': form,
        'course': course,
        'lesson': lesson,
    }
    return render(request, 'instructor/lesson_form.html', context)


@login_required
def lesson_delete(request, course_slug, lesson_id):
    """Delete a lesson"""
    course = get_object_or_404(
        LMSCourse,
        slug=course_slug,
        instructor=request.user
    )
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    
    if request.method == 'POST':
        lesson.delete()
        messages.success(request, 'Lesson deleted successfully!')
        return redirect('instructor:lesson_list', course_slug=course.slug)
    
    context = {
        'course': course,
        'lesson': lesson,
    }
    return render(request, 'instructor/lesson_confirm_delete.html', context)


# ==================== QUIZ MANAGEMENT ====================
@login_required
def quiz_list(request, course_slug, lesson_id):
    """List quizzes for a lesson"""
    course = get_object_or_404(
        LMSCourse,
        slug=course_slug,
        instructor=request.user
    )
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    quizzes = lesson.quizzes.all().order_by('display_order')
    
    context = {
        'course': course,
        'lesson': lesson,
        'quizzes': quizzes,
    }
    return render(request, 'instructor/quiz_list.html', context)


@login_required
def quiz_create(request, course_slug, lesson_id):
    """Create a new quiz"""
    course = get_object_or_404(
        LMSCourse,
        slug=course_slug,
        instructor=request.user
    )
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    
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
                lesson_id=lesson.id,
                quiz_id=quiz.id
            )
    else:
        form = QuizForm()
    
    context = {
        'form': form,
        'course': course,
        'lesson': lesson,
        'quiz': None,
    }
    return render(request, 'instructor/quiz_form.html', context)


@login_required
def quiz_edit(request, course_slug, lesson_id, quiz_id):
    """Edit a quiz"""
    course = get_object_or_404(
        LMSCourse,
        slug=course_slug,
        instructor=request.user
    )
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    quiz = get_object_or_404(Quiz, id=quiz_id, lesson=lesson)
    
    if request.method == 'POST':
        form = QuizForm(request.POST, instance=quiz)
        if form.is_valid():
            form.save()
            messages.success(request, 'Quiz updated successfully!')
            return redirect(
                'instructor:quiz_questions',
                course_slug=course.slug,
                lesson_id=lesson.id,
                quiz_id=quiz.id
            )
    else:
        form = QuizForm(instance=quiz)
    
    context = {
        'form': form,
        'course': course,
        'lesson': lesson,
        'quiz': quiz,
    }
    return render(request, 'instructor/quiz_form.html', context)


@login_required
def quiz_questions(request, course_slug, lesson_id, quiz_id):
    """Manage quiz questions"""
    course = get_object_or_404(
        LMSCourse,
        slug=course_slug,
        instructor=request.user
    )
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    quiz = get_object_or_404(Quiz, id=quiz_id, lesson=lesson)
    questions = quiz.questions.all().prefetch_related('answers')
    
    context = {
        'course': course,
        'lesson': lesson,
        'quiz': quiz,
        'questions': questions,
    }
    return render(request, 'instructor/quiz.html', context)


@login_required
def question_create(request, course_slug, lesson_id, quiz_id):
    """Create a new question"""
    course = get_object_or_404(
        LMSCourse,
        slug=course_slug,
        instructor=request.user
    )
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    quiz = get_object_or_404(Quiz, id=quiz_id, lesson=lesson)
    
    if request.method == 'POST':
        form = QuizQuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.quiz = quiz
            question.save()
            messages.success(request, 'Question created successfully!')
            
            # Redirect to add answers for multiple choice
            if question.question_type == 'multiple_choice':
                return redirect(
                    'instructor:question_answers',
                    course_slug=course.slug,
                    lesson_id=lesson.id,
                    quiz_id=quiz.id,
                    question_id=question.id
                )
            return redirect(
                'instructor:quiz_questions',
                course_slug=course.slug,
                lesson_id=lesson.id,
                quiz_id=quiz.id
            )
    else:
        form = QuizQuestionForm()
    
    context = {
        'form': form,
        'course': course,
        'lesson': lesson,
        'quiz': quiz,
    }
    return render(request, 'instructor/question_form.html', context)


@login_required
def question_answers(request, course_slug, lesson_id, quiz_id, question_id):
    """Manage answers for a question"""
    course = get_object_or_404(
        LMSCourse,
        slug=course_slug,
        instructor=request.user
    )
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    quiz = get_object_or_404(Quiz, id=quiz_id, lesson=lesson)
    question = get_object_or_404(QuizQuestion, id=question_id, quiz=quiz)
    
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
    
    context = {
        'form': form,
        'course': course,
        'lesson': lesson,
        'quiz': quiz,
        'question': question,
        'answers': answers,
    }
    return render(request, 'instructor/question_answers.html', context)


# ==================== ASSIGNMENT MANAGEMENT ====================
@login_required
def assignment_list(request, course_slug, lesson_id):
    """List assignments for a lesson"""
    course = get_object_or_404(
        LMSCourse,
        slug=course_slug,
        instructor=request.user
    )
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    assignments = lesson.assignments.all().order_by('display_order')
    
    context = {
        'course': course,
        'lesson': lesson,
        'assignments': assignments,
    }
    return render(request, 'instructor/assignments.html', context)


@login_required
def assignment_create(request, course_slug, lesson_id):
    """Create a new assignment"""
    course = get_object_or_404(
        LMSCourse,
        slug=course_slug,
        instructor=request.user
    )
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    
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
    
    context = {
        'form': form,
        'course': course,
        'lesson': lesson,
        'assignment': None,
    }
    return render(request, 'instructor/assignment_form.html', context)


@login_required
def assignment_edit(request, course_slug, lesson_id, assignment_id):
    """Edit an assignment"""
    course = get_object_or_404(
        LMSCourse,
        slug=course_slug,
        instructor=request.user
    )
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    assignment = get_object_or_404(
        Assignment,
        id=assignment_id,
        lesson=lesson
    )
    
    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES, instance=assignment)
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
    
    context = {
        'form': form,
        'course': course,
        'lesson': lesson,
        'assignment': assignment,
    }
    return render(request, 'instructor/assignment_form.html', context)


@login_required
def assignment_submissions(request, course_slug, assignment_id):
    """View submissions for an assignment"""
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
    
    submissions = assignment.submissions.all().select_related('student')
    
    context = {
        'course': course,
        'assignment': assignment,
        'submissions': submissions,
    }
    return render(request, 'instructor/assignment_submissions.html', context)


@login_required
def grade_submission(request, course_slug, submission_id):
    """Grade a student submission"""
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
        feedback = request.POST.get('feedback')
        
        submission.score = score
        submission.feedback = feedback
        submission.status = 'graded'
        submission.graded_by = request.user
        submission.save()
        
        messages.success(request, 'Submission graded successfully!')
        return redirect(
            'instructor:assignment_submissions',
            course_slug=course.slug,
            assignment_id=submission.assignment.id
        )
    
    context = {
        'course': course,
        'submission': submission,
    }
    return render(request, 'instructor/grade_submission.html', context)


# ==================== STUDENT MANAGEMENT ====================
@login_required
def students_list(request, course_slug):
    """List all students enrolled in a course"""
    course = get_object_or_404(
        LMSCourse,
        slug=course_slug,
        instructor=request.user
    )
    
    enrollments = course.enrollments.all().select_related('student')
    
    context = {
        'course': course,
        'enrollments': enrollments,
    }
    return render(request, 'instructor/students.html', context)


@login_required
def student_progress(request, course_slug, student_id):
    """View individual student progress"""
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
    
    # Get lesson progress
    lesson_progress = enrollment.lesson_progress.all().select_related('lesson')
    
    context = {
        'course': course,
        'enrollment': enrollment,
        'lesson_progress': lesson_progress,
    }
    return render(request, 'instructor/student_progress.html', context)


# ==================== ANNOUNCEMENTS ====================
@login_required
def announcement_create(request, course_slug):
    """Create a course announcement"""
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
    
    context = {
        'form': form,
        'course': course,
    }
    return render(request, 'instructor/announcement_form.html', context)