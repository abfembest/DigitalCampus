"""
Populate realistic, relationally-consistent academic/LMS data using ONLY
existing users (no new User rows are ever created here — see seed.py for
that). Idempotent: safe to re-run, everything is get_or_create/update_or_create
keyed on natural uniqueness constraints.

Scope: the BSc Artificial Intelligence program's current-session course load
(Year 1 First Semester + Year 2 First Semester, matching where the existing
students/instructors already sit), fleshed out with quizzes, assignments,
exams, and real student-generated work (attempts/submissions/responses) so
CourseGrade.recompute_for_student_course has real data to blend — plus a
light layer of supplementary records (certificates, reviews, messages,
payroll, a payment gateway + transactions, blog, library, announcements)
so those features aren't completely empty for testing.
"""
import random
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from eduweb.models import (
    Program, Course, AcademicSession, LMSCourse, Lesson,
    Quiz, QuizQuestion, QuizAnswer, QuizAttempt, QuizResponse,
    Assignment, AssignmentSubmission,
    Exam, ExamQuestion, StudentExamResponse,
    Enrollment, CourseRegistration, CourseGrade,
    Certificate, Review, Message,
    StaffPayroll, PaymentGateway, Transaction,
    BlogCategory, BlogPost, LibraryItem, Announcement,
)

random.seed(42)  # deterministic re-runs


class Command(BaseCommand):
    help = "Seed realistic relational academic/LMS data using existing users only."

    def handle(self, *args, **options):
        self.session = AcademicSession.objects.get(is_current=True)
        self.term = 'first'
        self.program = Program.objects.get(name='BSc Artificial Intelligence')
        self.instructors = list(User.objects.filter(profile__role='instructor').order_by('username'))
        self.instr_a, self.instr_b = self.instructors[0], self.instructors[1]
        self.admin = User.objects.filter(profile__role='admin', is_superuser=True).first()
        self.finance_user = User.objects.filter(profile__role='finance').first()
        self.support_user = User.objects.filter(profile__role='support').first()

        with transaction.atomic():
            self.fix_gbofag()
            lms_courses = self.build_lms_courses()
            self.build_assessments(lms_courses)
            enrollments = self.enroll_and_register(lms_courses)
            self.generate_student_work(lms_courses, enrollments)
            self.recompute_grades(lms_courses, enrollments)
            self.seed_supplementary(lms_courses)

        self.stdout.write(self.style.SUCCESS('Realistic data seed complete.'))

    # ------------------------------------------------------------------ #
    # 1. Fix gbofag's missing program
    # ------------------------------------------------------------------ #
    def fix_gbofag(self):
        u = User.objects.filter(username='gbofag').first()
        if u and u.profile.program_id is None:
            p = self.program
            u.profile.program = p
            u.profile.department = p.department
            u.profile.faculty = p.department.faculty
            u.profile.save(update_fields=['program', 'department', 'faculty'])
            self.stdout.write('  fixed gbofag.profile -> BSc Artificial Intelligence')

    # ------------------------------------------------------------------ #
    # 2. LMSCourse coverage: Year1 Sem1 (5 new) + Year2 Sem1 (8 new)
    # ------------------------------------------------------------------ #
    def build_lms_courses(self):
        new_course_map = {
            # code: instructor
            'CSC102': self.instr_a, 'CSC105': self.instr_a, 'CSC106': self.instr_a,
            'GST101': self.instr_b, 'GST102': self.instr_b,
            'CSC201': self.instr_b, 'CSC202': self.instr_b, 'CSC203': self.instr_b,
            'CSC204': self.instr_b, 'CSC205': self.instr_b, 'CSC206': self.instr_b,
            'GST201': self.instr_b, 'GST202': self.instr_b,
        }
        lms_courses = list(LMSCourse.objects.filter(session=self.session, term=self.term))
        existing_codes = {c.code for c in lms_courses}

        for code, instructor in new_course_map.items():
            if code in existing_codes:
                continue
            course = Course.objects.get(code=code, program=self.program)
            lc = LMSCourse.objects.create(
                title=f'{course.name} ({self.program.name} — {course.get_semester_display()} Yr{course.year_of_study})',
                code=code,
                short_description=f'{course.name} — core delivery for {self.program.name}.',
                description=(
                    f'{course.name} covers the core concepts, practical exercises, and '
                    f'assessments for {self.program.name} students at year {course.year_of_study}.'
                ),
                academic_course=course,
                session=self.session,
                term=self.term,
                lecturer=instructor,
                instructor=instructor,
                difficulty_level=course.year_of_study * 100,
                is_published=True,
            )
            for i, (title, content) in enumerate([
                ('Course Overview and Learning Objectives',
                 'An introduction to the scope, objectives, and expected learning outcomes of this course.'),
                ('Core Concepts and Practical Application',
                 'A walkthrough of the core theoretical concepts followed by practical worked examples.'),
            ]):
                Lesson.objects.get_or_create(
                    course=lc, slug=slugify(title),
                    defaults=dict(
                        title=title, lesson_type='text', description=title,
                        content=content, display_order=i, is_preview=(i == 0),
                    ),
                )
            lms_courses.append(lc)
            self.stdout.write(f'  created LMSCourse {code}')

        return lms_courses

    # ------------------------------------------------------------------ #
    # 3. Quizzes / Assignments / Exams for every current-session course
    # ------------------------------------------------------------------ #
    def build_assessments(self, lms_courses):
        for lc in lms_courses:
            first_lesson = lc.lessons.order_by('display_order').first()
            if not first_lesson:
                continue

            # ---- Quiz (1 per course, 3 questions) --------------------------
            quiz, created = Quiz.objects.get_or_create(
                lesson=first_lesson, slug=f'{lc.code.lower()}-knowledge-check',
                defaults=dict(
                    title=f'{lc.code} Knowledge Check',
                    description='A short check on this course\'s core concepts.',
                    passing_score=Decimal('50.00'), max_attempts=3,
                ),
            )
            if created:
                q1 = QuizQuestion.objects.create(
                    quiz=quiz, question_type='multiple_choice',
                    question_text=f'Which of these best describes the focus of {lc.academic_course.name}?',
                    points=Decimal('2.00'), display_order=0,
                )
                QuizAnswer.objects.create(question=q1, answer_text='Core concepts and practical skills', is_correct=True, display_order=0)
                QuizAnswer.objects.create(question=q1, answer_text='Unrelated general trivia', is_correct=False, display_order=1)
                QuizAnswer.objects.create(question=q1, answer_text='Only historical background', is_correct=False, display_order=2)

                q2 = QuizQuestion.objects.create(
                    quiz=quiz, question_type='true_false',
                    question_text=f'{lc.academic_course.name} is a {lc.academic_course.get_course_type_display().lower()} course in this program.',
                    points=Decimal('1.00'), display_order=1,
                )
                QuizAnswer.objects.create(question=q2, answer_text='True', is_correct=True, display_order=0)
                QuizAnswer.objects.create(question=q2, answer_text='False', is_correct=False, display_order=1)

                QuizQuestion.objects.create(
                    quiz=quiz, question_type='short_answer',
                    question_text=f'In one sentence, summarize the main goal of {lc.academic_course.name}.',
                    points=Decimal('2.00'), display_order=2,
                )

            # ---- Assignment (1 per course, if none yet) --------------------
            if not Assignment.objects.filter(lesson__course=lc).exists():
                Assignment.objects.create(
                    lesson=first_lesson,
                    title=f'{lc.code} Practical Assignment',
                    description=f'Apply the concepts covered in {lc.academic_course.name} to a short practical task.',
                    instructions='Submit a written response covering the required points discussed in class.',
                    max_score=Decimal('100.00'), passing_score=Decimal('50.00'),
                    due_date=timezone.now() + timezone.timedelta(days=14),
                )

            # ---- Exam (1 per course, if none yet) ---------------------------
            if not Exam.objects.filter(course=lc).exists():
                start = timezone.now() + timezone.timedelta(days=21)
                exam = Exam.objects.create(
                    title=f'{lc.academic_course.name} End-of-Semester Exam',
                    course=lc, instructor=lc.instructor,
                    exam_type=Exam.END_OF_SEMESTER,
                    start_datetime=start, end_datetime=start + timezone.timedelta(hours=1),
                    questions_per_student=5, total_marks=Decimal('10.00'), pass_mark=Decimal('5.00'),
                    show_result_immediately=True, status=Exam.PUBLISHED,
                )
                for i in range(5):
                    opts = [
                        {'id': f'opt-{exam.slug}-{i}-a', 'text': 'Correct application of the concept', 'is_correct': True},
                        {'id': f'opt-{exam.slug}-{i}-b', 'text': 'A common misconception', 'is_correct': False},
                        {'id': f'opt-{exam.slug}-{i}-c', 'text': 'An unrelated distractor option', 'is_correct': False},
                        {'id': f'opt-{exam.slug}-{i}-d', 'text': 'A partially correct but incomplete answer', 'is_correct': False},
                    ]
                    ExamQuestion.objects.create(
                        exam=exam, question_type=ExamQuestion.MCQ,
                        question_text=f'{lc.academic_course.code} Q{i + 1}: which statement correctly applies the covered concept?',
                        marks=Decimal('2.00'), options=opts,
                    )
                self.stdout.write(f'  created exam for {lc.code}')

        return lms_courses

    # ------------------------------------------------------------------ #
    # 4. Enrollment + CourseRegistration
    # ------------------------------------------------------------------ #
    def enroll_and_register(self, lms_courses):
        level1_students = [
            u for u in User.objects.filter(
                profile__role='student', profile__year_of_study=1,
            ).exclude(profile__progression_status='withdrawn')
        ]
        level2_students = [
            u for u in User.objects.filter(
                profile__role='student', profile__year_of_study=2,
            ).exclude(profile__progression_status='withdrawn')
        ]

        by_level = {100: [], 200: []}
        for lc in lms_courses:
            by_level.setdefault(lc.difficulty_level, []).append(lc)

        enrollments = {}  # (student_id, lms_course_id) -> Enrollment

        def register_student(student, courses):
            core_and_general = [c for c in courses if c.academic_course.course_type in ('core', 'general')]
            electives = [c for c in courses if c.academic_course.course_type == 'elective']
            chosen = list(core_and_general)
            if electives:
                chosen.append(random.choice(electives))

            for lc in chosen:
                enr, _ = Enrollment.objects.get_or_create(
                    student=student, course=lc,
                    defaults=dict(enrolled_by=self.admin, status='active'),
                )
                CourseRegistration.objects.get_or_create(
                    student=student, course=lc.academic_course,
                    session=self.session, term=self.term,
                    defaults=dict(status='approved'),
                )
                enrollments[(student.id, lc.id)] = enr

        for s in level1_students:
            register_student(s, by_level.get(100, []))
        for s in level2_students:
            register_student(s, by_level.get(200, []))

        self.stdout.write(f'  enrolled {len(level1_students)} level-1 + {len(level2_students)} level-2 students')
        return enrollments

    # ------------------------------------------------------------------ #
    # 5. Real student-generated work: quiz attempts, submissions, exam responses
    # ------------------------------------------------------------------ #
    def generate_student_work(self, lms_courses, enrollments):
        # Per-student "aptitude" baseline so grades feel personalized, not uniform.
        aptitude = {}
        for (student_id, _lc_id) in enrollments:
            aptitude.setdefault(student_id, random.randint(55, 92))

        for (student_id, lc_id), enr in enrollments.items():
            student = User.objects.get(pk=student_id)
            lc = LMSCourse.objects.get(pk=lc_id)
            base = aptitude[student_id]

            # ---- Quiz attempt ----------------------------------------------
            quiz = Quiz.objects.filter(lesson__course=lc).first()
            if quiz and not QuizAttempt.objects.filter(quiz=quiz, student=student).exists():
                attempt = QuizAttempt.objects.create(
                    quiz=quiz, student=student, is_completed=True,
                    completed_at=timezone.now(), time_taken_minutes=random.randint(5, 15),
                )
                total_pts = Decimal('0.00')
                earned_pts = Decimal('0.00')
                still_pending = False
                # Most short-answer responses have already been graded by the
                # instructor by now (simulating history) — only ~30% are left
                # sitting in the grading queue, matching the assignment/exam mix.
                short_answer_already_graded = random.random() >= 0.30
                for q in quiz.questions.all():
                    total_pts += q.points
                    is_right = random.randint(1, 100) <= base
                    if q.question_type == 'short_answer':
                        if short_answer_already_graded:
                            points_earned = q.points if is_right else Decimal('0.00')
                            QuizResponse.objects.create(
                                attempt=attempt, question=q,
                                text_response='This course focuses on building practical, applied understanding of the subject matter.',
                                is_correct=is_right, points_earned=points_earned,
                                graded_by=lc.instructor, graded_at=timezone.now(),
                            )
                            if is_right:
                                earned_pts += q.points
                        else:
                            QuizResponse.objects.create(
                                attempt=attempt, question=q,
                                text_response='This course focuses on building practical, applied understanding of the subject matter.',
                                needs_grading=True,
                            )
                            still_pending = True
                        continue
                    correct_answer = q.answers.filter(is_correct=True).first()
                    chosen_answer = correct_answer if is_right else q.answers.exclude(pk=correct_answer.pk).first()
                    QuizResponse.objects.create(
                        attempt=attempt, question=q, selected_answer=chosen_answer,
                        is_correct=is_right, points_earned=q.points if is_right else Decimal('0.00'),
                    )
                    if is_right:
                        earned_pts += q.points
                attempt.pending_manual_grading = still_pending
                if not still_pending:
                    attempt.score = earned_pts
                    attempt.max_score = total_pts
                    attempt.percentage = (earned_pts / total_pts * 100).quantize(Decimal('0.01')) if total_pts else Decimal('0.00')
                    attempt.passed = attempt.percentage >= quiz.passing_score
                attempt.save(update_fields=['score', 'max_score', 'percentage', 'passed', 'pending_manual_grading'])

            # ---- Assignment submission --------------------------------------
            assignment = Assignment.objects.filter(lesson__course=lc).first()
            if assignment and not AssignmentSubmission.objects.filter(assignment=assignment, student=student).exists():
                graded = random.random() < 0.75  # a quarter left ungraded, for instructor queues
                score = (assignment.max_score * Decimal(base) / Decimal(100)).quantize(Decimal('0.01')) if graded else None
                AssignmentSubmission.objects.create(
                    assignment=assignment, student=student,
                    submission_text=(
                        f'Submission by {student.get_full_name() or student.username} covering the required '
                        f'points for {assignment.title}.'
                    ),
                    status='graded' if graded else 'submitted',
                    score=score,
                    feedback='Good grasp of the core concepts; keep refining your written clarity.' if graded else '',
                    graded_by=lc.instructor if graded else None,
                    graded_at=timezone.now() if graded else None,
                    submitted_at=timezone.now() - timezone.timedelta(days=random.randint(1, 10)),
                )

            # ---- Exam response ------------------------------------------------
            exam = Exam.objects.filter(course=lc).first()
            if exam and not StudentExamResponse.objects.filter(exam=exam, student=student).exists():
                questions = list(exam.questions.all())
                assigned_ids = [q.pk for q in questions]
                answers = {}
                scores = {}
                total_score = Decimal('0.00')
                total_marks = Decimal('0.00')
                for q in questions:
                    total_marks += q.marks
                    correct_opt = next(o for o in q.options if o['is_correct'])
                    is_right = random.randint(1, 100) <= base
                    chosen_opt = correct_opt if is_right else next(o for o in q.options if not o['is_correct'])
                    answers[str(q.pk)] = chosen_opt['id']
                    marks_awarded = q.marks if is_right else Decimal('0.00')
                    scores[str(q.pk)] = {'marks_awarded': str(marks_awarded), 'max_marks': str(q.marks), 'is_correct': is_right}
                    total_score += marks_awarded

                outcome = random.random()
                if outcome < 0.75:
                    status = StudentExamResponse.GRADED
                    pct = (total_score / total_marks * 100).quantize(Decimal('0.01')) if total_marks else Decimal('0.00')
                    passed = total_score >= (exam.pass_mark or 0)
                    graded_fields = dict(
                        total_score=total_score, score_percentage=pct, passed=passed,
                        graded_by=exam.instructor, graded_at=timezone.now(),
                    )
                else:
                    # Left submitted-but-ungraded so instructor grading queues have real work.
                    status = StudentExamResponse.SUBMITTED
                    graded_fields = {}

                StudentExamResponse.objects.create(
                    exam=exam, student=student,
                    assigned_question_ids=assigned_ids,
                    answers=answers, question_scores=scores,
                    status=status,
                    submitted_at=timezone.now() - timezone.timedelta(days=random.randint(1, 5)),
                    **graded_fields,
                )

        self.stdout.write('  generated quiz/assignment/exam student work')

    # ------------------------------------------------------------------ #
    # 6. Recompute CourseGrade via the real pipeline
    # ------------------------------------------------------------------ #
    def recompute_grades(self, lms_courses, enrollments):
        pairs = {(User.objects.get(pk=sid), LMSCourse.objects.get(pk=lid).academic_course) for sid, lid in enrollments}
        count = 0
        for student, course in pairs:
            grade = CourseGrade.recompute_for_student_course(student, course, self.session, self.term)
            if grade:
                count += 1
        self.stdout.write(f'  recomputed {count} CourseGrade rows via the real pipeline')

    # ------------------------------------------------------------------ #
    # 7. Supplementary data
    # ------------------------------------------------------------------ #
    def seed_supplementary(self, lms_courses):
        # -- Certificates: for the level-2 "processed" student who has completed courses
        jordan = User.objects.filter(username='jordan_processed').first()
        if jordan:
            completed_lc = lms_courses[0] if lms_courses else None
            if completed_lc and not Certificate.objects.filter(student=jordan, course=completed_lc).exists():
                Certificate.objects.create(
                    student=jordan, course=completed_lc, certificate_type='lms_course',
                    certificate_id=f'CERT-{jordan.username[:6].upper()}-{completed_lc.code}',
                    completion_date=timezone.now().date(), grade='A',
                    payment_status='paid',
                )

        # -- Reviews: a couple of students reviewing courses they're enrolled in
        for lc in lms_courses[:3]:
            reviewer = lc.enrollments.select_related('student').first()
            if reviewer and not Review.objects.filter(course=lc, student=reviewer.student).exists():
                Review.objects.create(
                    course=lc, student=reviewer.student,
                    rating=random.randint(4, 5),
                    review_text=f'Solid introduction to {lc.academic_course.name}. Clear structure and fair assessments.',
                )

        # -- Messages: student <-> instructor, admin <-> instructor
        talia = User.objects.filter(username='talia').first()
        if talia and self.instr_a and not Message.objects.filter(sender=talia, recipient=self.instr_a).exists():
            Message.objects.create(
                sender=talia, recipient=self.instr_a,
                subject='Question about upcoming exam',
                body='Hi, could you clarify which topics the end-of-semester exam will cover?',
            )
        if self.admin and self.instr_a and not Message.objects.filter(sender=self.admin, recipient=self.instr_a).exists():
            Message.objects.create(
                sender=self.admin, recipient=self.instr_a,
                subject='Reminder: submit exam questions for approval',
                body='Please ensure all draft exams are submitted for approval before the end of the week.',
            )

        # -- Staff payroll for instructor/finance/support
        for staff in [self.instr_a, self.instr_b, self.finance_user, self.support_user]:
            if not staff:
                continue
            StaffPayroll.objects.get_or_create(
                staff=staff, month=timezone.now().month, year=timezone.now().year,
                defaults=dict(
                    base_salary=Decimal('250000.00'), allowances=Decimal('50000.00'),
                    bonuses=Decimal('0.00'), tax_deduction=Decimal('15000.00'),
                    other_deductions=Decimal('0.00'), payment_status='paid',
                    payment_method='bank_transfer', currency='NGN',
                    bank_name='GTBank', account_number='0123456789',
                ),
            )

        # -- Payment gateway + a couple of transactions
        gateway, _ = PaymentGateway.objects.get_or_create(
            slug='stripe-test', defaults=dict(
                name='Stripe (Test)', gateway_type='stripe', is_active=True, is_test_mode=True,
            ),
        )
        for student_username in ['talia', 'ceceh']:
            student = User.objects.filter(username=student_username).first()
            if student and not Transaction.objects.filter(user=student, transaction_type='enrollment').exists():
                Transaction.objects.create(
                    user=student, transaction_type='enrollment', amount=Decimal('0.00'),
                    currency='NGN', gateway=gateway, status='completed',
                )

        # -- Blog category + posts
        cat, _ = BlogCategory.objects.get_or_create(
            slug='campus-news', defaults=dict(name='Campus News', icon='newspaper', color='blue'),
        )
        if not BlogPost.objects.filter(category=cat).exists() and self.admin:
            BlogPost.objects.create(
                title='Welcome to the 2026/2027 Academic Session',
                subtitle='A new session begins with new opportunities',
                excerpt='The 2026/2027 academic session is officially underway across all faculties.',
                content='The 2026/2027 academic session has begun. Students are encouraged to register for their courses promptly and reach out to their academic advisors with any questions.',
                category=cat, author=self.admin, status='published',
            )

        # -- Library items
        if not LibraryItem.objects.exists():
            LibraryItem.objects.create(
                category='Books', subcategory='Computer Science',
                title='Introduction to Algorithms', author='Cormen, Leiserson, Rivest, Stein',
                publisher='MIT Press', year=2009,
                description='A comprehensive introduction to algorithms and data structures.',
                access='members', allow_download=False, allow_read_online=True,
                external_url='https://example.com/library/intro-to-algorithms',
            )
            LibraryItem.objects.create(
                category='References', subcategory='Dictionaries',
                title='Oxford Dictionary of Computer Science', publisher='Oxford University Press', year=2016,
                description='Reference dictionary of computing terminology.',
                access='public', allow_download=False, allow_read_online=True,
                external_url='https://example.com/library/oxford-cs-dictionary',
            )

        # -- Announcement
        if self.admin and not Announcement.objects.filter(announcement_type='system').exists():
            Announcement.objects.create(
                title='2026/2027 Session Registration Now Open',
                content='Course registration for the 2026/2027 first semester is now open for all students. Please register before the deadline.',
                announcement_type='system', priority='high', created_by=self.admin,
            )

        self.stdout.write('  seeded supplementary data (certificates, reviews, messages, payroll, payments, blog, library, announcements)')
