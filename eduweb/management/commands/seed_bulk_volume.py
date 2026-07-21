"""
seed_bulk_volume
=================
Massively expands the dev DB with realistic *volume* across every app, WITHOUT
ever creating a new django.contrib.auth.models.User / eduweb.UserProfile row.
All student-specific depth is generated only for the 7 existing student
accounts (talia, ceceh, gbofag, abfembest2@gmail.com, marcus_repeat,
priya_escalate, jordan_processed) and the existing instructor/admin/finance/
support accounts.

Builds on top of (does not replace) `seed_realistic_data.py` and
`seed_progression_demo.py` — it does not touch the courses/LMSCourses those
commands already created for BSc Artificial Intelligence's first-semester
delivery, and it does not disturb the priya_escalate / marcus_repeat /
jordan_processed progression-demo scenarios (it specifically avoids
re-registering priya into her open carry-over course).

Scope, in order:
  1. AcademicSession   — add a few more sessions (closed/upcoming), leaving
                         is_current alone.
  2. Faculty/Department/Program — broaden the academic catalog.
  3. Course             — populate every previously-empty Program with a
                         small, credit-cap-respecting course load.
  4. CourseIntake       — a couple of intake periods per program.
  5. LMSCourse + Lesson/LessonSection + Quiz/QuizQuestion/QuizAnswer +
     Assignment + Exam/ExamQuestion — bulk LMS delivery content, both for
     the newly created courses AND for the previously-undelivered
     second-semester BSc-AI courses (a real, pre-existing gap in the data).
  6. LibraryItem, BlogPost, Badge catalog, Testimonial — supplementary
     content volume.
  7. Per-student depth for the 7 existing students: Enrollment,
     CourseRegistration, CourseGrade (via the real recompute pipeline),
     QuizAttempt, AssignmentSubmission, StudentExamResponse, Certificate,
     StudentBadge (via the real check_and_award_badges engine),
     Notification, Message, Discussion/DiscussionReply, StudyGroup(s),
     Review.
  8. Finance: AllRequiredPayments, FeePayment, ApplicationPayment (only for
     the 4 students with real CourseApplications), Invoice, StaffPayroll
     (more months of history for the ~6 existing staff).
  9. Support: SLAPolicy, SupportDepartment, KBCategory/KBArticle,
     FAQCategory/FAQ, CannedResponse, SupportAnnouncement, AgentProfile,
     SupportTicket/TicketReply/SupportTicketExtra/TicketHistory/
     TicketFeedback/TicketEscalation.

Idempotency
-----------
Structural data (sessions/faculties/departments/programs/courses/intakes)
uses get_or_create/update_or_create keyed on natural unique fields, so
re-running never duplicates them. Bulk LMS content is guarded per-LMSCourse
(skipped if it already has lessons). Pure-volume content without a natural
key (library items, blog posts, support tickets, quiz attempts, etc.) is
guarded by only topping up to the target count, so re-running tops up
rather than duplicating.

To re-roll the *random* parts (quiz/exam scores, ticket text, etc.) for a
fresh look without duplicating structure: bump the RNG seed below and
re-run — new rows only get created where the topped-up-count guards still
have headroom, so for a full re-roll of content increase the *_TARGET
constants first.
"""
import random
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from eduweb.models import (
    Faculty, Department, Program, Course, AcademicSession, CourseIntake,
    LMSCourse, Lesson, LessonSection,
    Quiz, QuizQuestion, QuizAnswer, QuizAttempt, QuizResponse,
    Assignment, AssignmentSubmission,
    Exam, ExamQuestion, StudentExamResponse,
    Enrollment, CourseRegistration, CourseGrade, CourseCarryOver,
    Certificate, StudentBadge, Badge, check_and_award_badges,
    Notification, Message, Discussion, DiscussionReply,
    StudyGroup, StudyGroupMember, StudyGroupMessage, Review,
    LibraryItem, BlogCategory, BlogPost, Testimonial,
    AllRequiredPayments, FeePayment, ApplicationPayment, Invoice,
    StaffPayroll, PaymentGateway, Transaction, CourseApplication,
    SupportTicket, TicketReply,
)
from support.models import (
    SLAPolicy, SupportDepartment, KBCategory, KBArticle,
    FAQCategory, FAQ, CannedResponse, SupportAnnouncement, AgentProfile,
    SupportTicketExtra, TicketHistory, TicketFeedback, TicketEscalation,
)

random.seed(20260721)

# ─────────────────────────────────────────────────────────────────────────────
# Volume targets — tune here to re-roll / rescale without touching logic
# ─────────────────────────────────────────────────────────────────────────────
LIBRARY_ITEM_TARGET = 180
BLOG_POST_TARGET = 90
SUPPORT_TICKET_TARGET = 80
TESTIMONIAL_TARGET = 14


def subject_from_program_name(name):
    """Strip the leading degree label off a program name to get a bare 'subject'."""
    prefixes = [
        'BSc ', 'BEng ', 'BA ', 'BEd ', 'BPharm ', 'MSc ', 'MBA ',
        'MEng ', 'MA ', 'LLB ', 'LLM ', 'MPharm ', 'PhD ',
    ]
    s = name
    for p in prefixes:
        if s.startswith(p):
            return s[len(p):]
    return s


class Command(BaseCommand):
    help = 'Massively expand dev DB volume across every app using only the 13 existing users.'

    # =========================================================================
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('=== seed_bulk_volume starting ===\n'))

        self.admin = User.objects.filter(profile__role='admin', is_superuser=True).first()
        self.femiadmin = User.objects.filter(username='femiadmin').first()
        self.instructors = list(User.objects.filter(profile__role='instructor').order_by('username'))
        self.instr_a, self.instr_b = self.instructors[0], self.instructors[1]
        self.finance_user = User.objects.filter(profile__role='finance').first()
        self.support_user = User.objects.filter(profile__role='support').first()
        self.students = list(User.objects.filter(profile__role='student').order_by('username'))
        self.staff_all = [self.admin, self.femiadmin, self.instr_a, self.instr_b,
                           self.finance_user, self.support_user]
        self.staff_all = [u for u in self.staff_all if u]

        with transaction.atomic():
            self.seed_academic_sessions()
        with transaction.atomic():
            self.seed_faculties_departments_programs()
        with transaction.atomic():
            self.seed_courses()
        with transaction.atomic():
            self.seed_course_intakes()
        with transaction.atomic():
            self.seed_lms_bulk()
        with transaction.atomic():
            self.seed_library()
        with transaction.atomic():
            self.seed_blog()
        with transaction.atomic():
            self.seed_badge_catalog()
        with transaction.atomic():
            self.seed_testimonials()
        with transaction.atomic():
            self.seed_student_depth()
        with transaction.atomic():
            self.seed_finance()
        with transaction.atomic():
            self.seed_support()

        self.stdout.write(self.style.SUCCESS('\n=== seed_bulk_volume complete ==='))

    # =========================================================================
    # 1. ACADEMIC SESSIONS
    # =========================================================================
    def seed_academic_sessions(self):
        self.stdout.write('Seeding additional academic sessions...')
        new_sessions = [
            ('2022/2023', 'closed', [
                {'term': 'first', 'start': '2022-09-05', 'end': '2023-01-20'},
                {'term': 'second', 'start': '2023-01-30', 'end': '2023-06-02'},
            ]),
            ('2023/2024', 'closed', [
                {'term': 'first', 'start': '2023-09-04', 'end': '2024-01-19'},
                {'term': 'second', 'start': '2024-01-29', 'end': '2024-06-01'},
            ]),
            ('2027/2028', 'upcoming', [
                {'term': 'first', 'start': '2027-09-06', 'end': '2028-01-21'},
                {'term': 'second', 'start': '2028-01-31', 'end': '2028-06-05'},
            ]),
        ]
        for name, status, term_dates in new_sessions:
            sess, created = AcademicSession.objects.get_or_create(
                name=name, defaults={'status': status, 'term_dates': term_dates},
            )
            if created:
                self.stdout.write(f'  created session {name} ({status})')
        self.current_session = AcademicSession.objects.get(is_current=True)

    # =========================================================================
    # 2. FACULTIES / DEPARTMENTS / PROGRAMS
    # =========================================================================
    def seed_faculties_departments_programs(self):
        self.stdout.write('Seeding faculties/departments/programs...')

        new_faculty_raw = [
            {
                'name': 'Faculty of Law', 'code': 'LAW', 'icon': 'scale',
                'color_primary': 'slate', 'color_secondary': 'gray',
                'tagline': 'Justice, ethics, and the rule of law',
                'description': 'Rigorous training in legal theory, advocacy, and professional practice.',
                'mission': 'Produce principled legal practitioners who serve justice and society.',
                'vision': 'A faculty recognised for excellence in legal education and research.',
                'accreditation': 'Approved by the Council of Legal Education – 2022',
                'student_count': 640, 'placement_rate': 88, 'partner_count': 20, 'international_faculty': 15,
                'special_features': ['Moot court chambers', 'Legal aid clinic', 'Judicial clerkship programme'],
                'dean_name': 'Prof. Adaeze Nwankwo', 'dean_role': 'Dean',
                'dean_faculty_label': 'Faculty of Law',
            },
            {
                'name': 'Faculty of Education', 'code': 'EDU', 'icon': 'book-open',
                'color_primary': 'teal', 'color_secondary': 'cyan',
                'tagline': 'Shaping the educators of tomorrow',
                'description': 'Preparing reflective, skilled educators and education policy leaders.',
                'mission': 'Advance teaching excellence and equitable access to quality education.',
                'vision': 'A leading centre for education research and teacher training.',
                'accreditation': 'Teachers Registration Council Accredited – 2021',
                'student_count': 520, 'placement_rate': 90, 'partner_count': 18, 'international_faculty': 12,
                'special_features': ['Model demonstration school', 'Curriculum design lab', 'Teaching practicum network'],
                'dean_name': 'Dr. Folake Adisa', 'dean_role': 'Dean',
                'dean_faculty_label': 'Faculty of Education',
            },
            {
                'name': 'Faculty of Environmental Sciences', 'code': 'ENV', 'icon': 'map',
                'color_primary': 'green', 'color_secondary': 'lime',
                'tagline': 'Designing sustainable built environments',
                'description': 'Architecture, planning, and estate management for sustainable cities.',
                'mission': 'Train professionals who design and manage resilient built environments.',
                'vision': 'A faculty at the forefront of sustainable urban development.',
                'accreditation': 'Architects Registration Council Accredited – 2023',
                'student_count': 470, 'placement_rate': 86, 'partner_count': 22, 'international_faculty': 14,
                'special_features': ['Design studio & 3D print lab', 'GIS & planning lab', 'Site-visit partnerships'],
                'dean_name': 'Arc. Tunde Bakare', 'dean_role': 'Dean',
                'dean_faculty_label': 'Faculty of Environmental Sciences',
            },
            {
                'name': 'Faculty of Media & Communication', 'code': 'MED', 'icon': 'radio',
                'color_primary': 'pink', 'color_secondary': 'rose',
                'tagline': 'Telling the stories that shape society',
                'description': 'Journalism, broadcast, and digital media production training.',
                'mission': 'Develop ethical, skilled communicators for a digital-first media world.',
                'vision': 'A regional hub for media innovation and storytelling excellence.',
                'accreditation': 'Nigerian Broadcasting Commission Recognised – 2022',
                'student_count': 390, 'placement_rate': 84, 'partner_count': 16, 'international_faculty': 10,
                'special_features': ['On-campus TV/radio studio', 'Newsroom simulation lab', 'Industry internship pipeline'],
                'dean_name': 'Mrs. Ifeoma Chukwu', 'dean_role': 'Dean',
                'dean_faculty_label': 'Faculty of Media & Communication',
            },
        ]
        new_faculties = {}
        for idx, fd in enumerate(new_faculty_raw):
            f, created = Faculty.objects.get_or_create(
                code=fd['code'],
                defaults=dict(
                    name=fd['name'], icon=fd['icon'], color_primary=fd['color_primary'],
                    color_secondary=fd['color_secondary'], tagline=fd['tagline'],
                    description=fd['description'], mission=fd['mission'], vision=fd['vision'],
                    dean_name=fd['dean_name'], dean_role=fd['dean_role'],
                    dean_faculty_label=fd['dean_faculty_label'], accreditation=fd['accreditation'],
                    student_count=fd['student_count'], placement_rate=fd['placement_rate'],
                    partner_count=fd['partner_count'], international_faculty=fd['international_faculty'],
                    special_features=fd['special_features'],
                    meta_description=fd['description'][:160],
                    meta_keywords=f"{fd['name']}, university, degree, {fd['code']}",
                    is_active=True, display_order=5 + idx,
                ),
            )
            new_faculties[fd['code']] = f
            if created:
                self.stdout.write(f"  created faculty {fd['code']}")

        all_faculties = {f.code: f for f in Faculty.objects.all()}

        # (faculty_code, dept_name, dept_code, description)
        new_dept_raw = [
            ('CSIT', 'Department of Data Science', 'DS', 'Data engineering, analytics, and applied statistics.'),
            ('CSIT', 'Department of Information Systems', 'IS', 'Enterprise systems, IT governance, and systems analysis.'),
            ('ENG', 'Department of Chemical Engineering', 'CHE', 'Process design, thermodynamics, and chemical plant operations.'),
            ('ENG', 'Department of Petroleum Engineering', 'PET', 'Reservoir engineering, drilling, and petroleum economics.'),
            ('BUS', 'Department of Human Resource Management', 'HRM', 'Organisational behaviour, talent management, and labour relations.'),
            ('BUS', 'Department of Business Analytics', 'BAN', 'Data-driven decision making and business intelligence.'),
            ('BUS', 'Department of Management', 'MGT', 'General management, strategy, and organisational leadership.'),
            ('HLTH', 'Department of Pharmacy', 'PHM', 'Pharmaceutical sciences, pharmacology, and clinical pharmacy.'),
            ('HLTH', 'Department of Medical Laboratory Science', 'MLS', 'Clinical diagnostics, haematology, and microbiology.'),
            ('ART', 'Department of Performing Arts', 'PRA', 'Theatre, music, and dance performance and production.'),
            ('ART', 'Department of History & International Studies', 'HIS', 'Historical analysis and global affairs.'),
            ('LAW', 'Department of Public Law', 'PUL', 'Constitutional, criminal, and administrative law.'),
            ('LAW', 'Department of Private & Business Law', 'PBL', 'Commercial, property, and corporate law.'),
            ('EDU', 'Department of Educational Foundations', 'EDF', 'Philosophy, sociology, and psychology of education.'),
            ('EDU', 'Department of Curriculum Studies', 'CUR', 'Curriculum design, instructional methods, and assessment.'),
            ('ENV', 'Department of Architecture', 'ARC', 'Architectural design, building technology, and sustainability.'),
            ('ENV', 'Department of Urban & Regional Planning', 'URP', 'Land-use planning, GIS, and regional development.'),
            ('ENV', 'Department of Estate Management', 'EST', 'Property valuation, facilities, and real estate management.'),
            ('MED', 'Department of Mass Communication', 'MCM', 'Journalism, public relations, and broadcast media.'),
            ('MED', 'Department of Film & Media Production', 'FMP', 'Film production, editing, and digital content creation.'),
        ]
        new_departments = {}
        for order, (fac_code, name, code, desc) in enumerate(new_dept_raw):
            d, created = Department.objects.get_or_create(
                faculty=all_faculties[fac_code], code=code,
                defaults=dict(name=name, description=desc, is_active=True, display_order=order),
            )
            new_departments[code] = d
            if created:
                self.stdout.write(f'  created department {code} ({fac_code})')

        all_departments = {d.code: d for d in Department.objects.all()}

        # (dept_code, program_name, program_code, degree_level, duration_years)
        new_program_raw = [
            ('DS', 'BSc Data Science', 'BSC-DS', 'undergraduate', Decimal('3.0')),
            ('IS', 'BSc Information Systems', 'BSC-IS', 'undergraduate', Decimal('3.0')),
            ('MEE', 'BEng Mechanical Engineering', 'BENG-MEE', 'undergraduate', Decimal('4.0')),
            ('CHE', 'BEng Chemical Engineering', 'BENG-CHE', 'undergraduate', Decimal('4.0')),
            ('PET', 'BEng Petroleum Engineering', 'BENG-PET', 'undergraduate', Decimal('4.0')),
            ('MKS', 'BSc Marketing', 'BSC-MKS', 'undergraduate', Decimal('3.0')),
            ('ENT', 'BSc Entrepreneurship', 'BSC-ENT', 'undergraduate', Decimal('3.0')),
            ('HRM', 'BSc Human Resource Management', 'BSC-HRM', 'undergraduate', Decimal('3.0')),
            ('BAN', 'BSc Business Analytics', 'BSC-BAN', 'undergraduate', Decimal('3.0')),
            ('MGT', 'MBA General Management', 'MBA-GEN', 'masters', Decimal('1.0')),
            ('PHE', 'BSc Public Health', 'BSC-PHE', 'undergraduate', Decimal('3.0')),
            ('PHM', 'BPharm Pharmacy', 'BPHARM', 'undergraduate', Decimal('4.0')),
            ('MLS', 'BSc Medical Laboratory Science', 'BSC-MLS', 'undergraduate', Decimal('4.0')),
            ('PRA', 'BA Performing Arts', 'BA-PRA', 'undergraduate', Decimal('3.0')),
            ('HIS', 'BA History & International Studies', 'BA-HIS', 'undergraduate', Decimal('3.0')),
            ('PUL', 'LLB Public Law', 'LLB-PUL', 'undergraduate', Decimal('4.0')),
            ('PBL', 'LLB Private & Business Law', 'LLB-PBL', 'undergraduate', Decimal('4.0')),
            ('EDF', 'BEd Educational Foundations', 'BED-EDF', 'undergraduate', Decimal('4.0')),
            ('CUR', 'BEd Curriculum Studies', 'BED-CUR', 'undergraduate', Decimal('4.0')),
            ('ARC', 'BSc Architecture', 'BSC-ARC', 'undergraduate', Decimal('5.0')),
            ('URP', 'BSc Urban & Regional Planning', 'BSC-URP', 'undergraduate', Decimal('4.0')),
            ('EST', 'BSc Estate Management', 'BSC-EST', 'undergraduate', Decimal('4.0')),
            ('MCM', 'BSc Mass Communication', 'BSC-MCM', 'undergraduate', Decimal('4.0')),
            ('FMP', 'BSc Film & Media Production', 'BSC-FMP', 'undergraduate', Decimal('3.0')),
            ('DS', 'MSc Data Science', 'MSC-DS', 'masters', Decimal('1.0')),
            ('PHE', 'MSc Public Health', 'MSC-PHE', 'masters', Decimal('1.0')),
            ('PUL', 'LLM Law', 'LLM-LAW', 'masters', Decimal('1.0')),
            ('AI', 'MSc Artificial Intelligence', 'MSC-AI', 'masters', Decimal('1.0')),
            ('CYS', 'MSc Cybersecurity', 'MSC-CYS', 'masters', Decimal('1.0')),
            ('CVE', 'MEng Civil Engineering', 'MENG-CVE', 'masters', Decimal('1.0')),
            ('ECW', 'MA English & Creative Writing', 'MA-ECW', 'masters', Decimal('1.0')),
        ]
        fee_by_level = {
            'undergraduate': (Decimal('50.00'), Decimal('9250.00'), 18),
            'masters': (Decimal('75.00'), Decimal('14500.00'), 15),
            'phd': (Decimal('100.00'), Decimal('18000.00'), 12),
        }
        credits_by_duration = {
            Decimal('3.0'): 120, Decimal('4.0'): 160, Decimal('5.0'): 200, Decimal('1.0'): 60,
        }
        created_count = 0
        for order, (dept_code, name, code, degree, dur) in enumerate(new_program_raw):
            dept = all_departments[dept_code]
            app_fee, tuition, sem_cap = fee_by_level[degree]
            base_name = subject_from_program_name(name)
            _, created = Program.objects.get_or_create(
                department=dept, code=code,
                defaults=dict(
                    name=name, degree_level=degree, duration_years=dur,
                    credits_required=credits_by_duration.get(dur, 120),
                    application_fee=app_fee, tuition_fee=tuition,
                    max_students=random.randint(35, 90),
                    max_credits_per_semester=sem_cap,
                    is_featured=(order % 6 == 0), is_active=True, display_order=order,
                    tagline=f"Shape your future with {name}",
                    overview=f"{name} equips students with the theory and practical skills needed for {base_name}.",
                    description=(
                        f"The {name} programme at MIU combines rigorous coursework with practical "
                        f"application, preparing graduates for careers in {base_name.lower()} and related fields."
                    ),
                    available_study_modes=['full_time', 'online', 'blended'],
                    entry_requirements=[
                        "Minimum 5 GCSEs at grade C/4 or above including English and Maths",
                        "A-Levels: AAB or equivalent BTEC" if degree == 'undergraduate' else "A recognised bachelor's degree in a related field",
                        "English proficiency: IELTS 6.0 or equivalent",
                        f"Strong interest in {base_name}",
                    ],
                    core_courses=[f"{code}-101 Foundations of {base_name}", f"{code}-201 Intermediate {base_name}"],
                    specialization_tracks=[f"{base_name} & Innovation", f"Applied {base_name}"],
                    learning_outcomes=[
                        f"Demonstrate comprehensive knowledge of {base_name}",
                        "Apply theoretical knowledge to real-world problems",
                        "Communicate complex ideas effectively in professional contexts",
                    ],
                    career_paths=[f"{base_name} Specialist", f"{base_name} Consultant", f"{base_name} Analyst"],
                    avg_starting_salary="$40,000 - $65,000",
                    job_placement_rate=random.randint(78, 96),
                    meta_description=f"Study {name} at MIU — accredited, flexible, globally recognised.",
                    meta_keywords=f"{name}, {code}, MIU, university degree",
                ),
            )
            if created:
                created_count += 1
        self.stdout.write(f'  created {created_count} new programs (of {len(new_program_raw)} defined)')

    # =========================================================================
    # 3. COURSES — for every program that has none yet
    # =========================================================================
    def seed_courses(self):
        self.stdout.write('Seeding courses for previously-empty programs...')

        undergrad_template = [
            ('general', 1, 'first', 'Academic & Professional Skills in {s}', 2),
            ('core', 1, 'first', 'Introduction to {s}', 3),
            ('core', 1, 'second', 'Foundations of {s} II', 3),
            ('core', 1, 'second', 'Research Methods in {s}', 3),
            ('core', 2, 'first', 'Intermediate {s}', 4),
            ('elective', 2, 'first', 'Contemporary Issues in {s}', 3),
        ]
        masters_template = [
            ('core', 1, 'first', 'Advanced {s} Theory', 4),
            ('elective', 1, 'first', 'Research Methods for {s} Professionals', 4),
            ('core', 1, 'second', '{s} Practicum', 4),
            ('core', 1, 'second', 'Dissertation in {s}', 8),
        ]
        phd_template = [
            ('core', 1, 'first', 'Doctoral Research Methodology', 6),
            ('elective', 1, 'second', 'Research Seminar Series I', 4),
            ('core', 1, 'second', 'PhD Thesis (Year 1 Progress)', 8),
        ]

        total_created = 0
        for program in Program.objects.all():
            if Course.objects.filter(program=program).exists():
                continue  # BSC-AI already has its full catalog — leave untouched

            subject = subject_from_program_name(program.name)
            if program.degree_level == 'masters' or program.degree_level == 'postgraduate':
                template = masters_template
            elif program.degree_level == 'phd':
                template = phd_template
            else:
                template = undergrad_template

            dept_code = program.department.code
            year_seq = {}
            for course_type, year, semester, name_tpl, credits in template:
                year_seq[year] = year_seq.get(year, 0) + 1
                code = f"{dept_code}{year * 100 + year_seq[year]}"
                name = name_tpl.replace('{s}', subject)
                Course.objects.get_or_create(
                    program=program, code=code,
                    defaults=dict(
                        name=name, course_type=course_type, credit_units=credits,
                        year_of_study=year, semester=semester,
                        description=f"{name} — a {course_type} course for {program.name} students.",
                        learning_outcomes=[
                            f"Understand the core principles of {name}",
                            "Apply concepts through assessed coursework",
                        ],
                        is_active=True,
                    ),
                )
                total_created += 1
        self.stdout.write(f'  created up to {total_created} course rows (idempotent — actual new count may be lower on rerun)')

    # =========================================================================
    # 4. COURSE INTAKES
    # =========================================================================
    def seed_course_intakes(self):
        self.stdout.write('Seeding course intakes...')
        count = 0
        for program in Program.objects.all():
            for period, year, start, deadline in [
                ('september', 2026, date(2026, 9, 1), date(2026, 8, 15)),
                ('january', 2027, date(2027, 1, 6), date(2026, 12, 15)),
            ]:
                _, created = CourseIntake.objects.get_or_create(
                    program=program, intake_period=period, year=year,
                    defaults=dict(
                        start_date=start, application_deadline=deadline,
                        available_slots=random.randint(30, 100), is_active=True,
                    ),
                )
                if created:
                    count += 1
        self.stdout.write(f'  created {count} course intakes')

    # =========================================================================
    # 5. LMS BULK CONTENT
    # =========================================================================
    LESSON_TEMPLATE = [
        ('Course Overview and Learning Objectives',
         'An orientation to the scope, structure, and assessment methods of this course.'),
        ('Core Concepts and Terminology',
         'Foundational definitions and terminology used throughout the course.'),
        ('Theoretical Frameworks',
         'The major theoretical frameworks and models underpinning this subject.'),
        ('Practical Applications',
         'Worked examples applying the theory to real-world scenarios.'),
        ('Case Studies and Analysis',
         'Analysis of real case studies relevant to this course.'),
        ('Summary and Assessment Preparation',
         'A recap of key themes and guidance on preparing for assessment.'),
    ]

    def _build_lesson_content(self, title, course_name):
        return (
            f"<h2>{title}</h2>"
            f"<p>This lesson is part of {course_name} and covers key material students are "
            f"expected to master before progressing to assessment.</p>"
            f"<h3>Key Points</h3>"
            f"<ul><li>Core definitions and terminology</li>"
            f"<li>Worked examples with step-by-step explanations</li>"
            f"<li>Common misconceptions and how to avoid them</li></ul>"
        )

    def _create_lms_content(self, lc, is_end_of_semester_biased=True):
        """Create sections/lessons/quiz/assignment/exam for one LMSCourse. Idempotent per-course."""
        if lc.lessons.exists():
            return

        # ── 2 sections, 3 lessons each ──────────────────────────────────────
        lessons = []
        for sec_idx in range(2):
            sec_title = 'Introduction & Foundations' if sec_idx == 0 else 'Applied Practice & Review'
            section = LessonSection.objects.create(
                course=lc, title=sec_title,
                description=f"{sec_title} for {lc.title}.",
                display_order=sec_idx,
            )
            for les_idx in range(3):
                title, desc = self.LESSON_TEMPLATE[sec_idx * 3 + les_idx]
                lesson = Lesson.objects.create(
                    course=lc, section=section, title=title, lesson_type='text',
                    description=desc, content=self._build_lesson_content(title, lc.title),
                    is_preview=(sec_idx == 0 and les_idx == 0),
                    display_order=sec_idx * 3 + les_idx,
                )
                lessons.append(lesson)

        first_lesson, second_lesson = lessons[0], lessons[1]

        # ── Quiz: 3 mcq + 1 true_false + 1 short_answer + 1 essay ──────────
        quiz = Quiz.objects.create(
            lesson=first_lesson, title=f'{lc.code} Knowledge Check',
            description="A short check on this course's core concepts.",
            passing_score=Decimal('50.00'), max_attempts=3,
        )
        for i in range(3):
            q = QuizQuestion.objects.create(
                quiz=quiz, question_type='multiple_choice',
                question_text=f'Which statement best reflects concept #{i + 1} covered in {lc.title}?',
                points=Decimal('2.00'), display_order=i,
            )
            QuizAnswer.objects.create(question=q, answer_text='Correct application of the concept', is_correct=True, display_order=0)
            QuizAnswer.objects.create(question=q, answer_text='A common misconception', is_correct=False, display_order=1)
            QuizAnswer.objects.create(question=q, answer_text='An unrelated distractor', is_correct=False, display_order=2)
        tf = QuizQuestion.objects.create(
            quiz=quiz, question_type='true_false',
            question_text=f'{lc.title} includes at least one assessed practical component.',
            points=Decimal('1.00'), display_order=3,
        )
        QuizAnswer.objects.create(question=tf, answer_text='True', is_correct=True, display_order=0)
        QuizAnswer.objects.create(question=tf, answer_text='False', is_correct=False, display_order=1)
        QuizQuestion.objects.create(
            quiz=quiz, question_type='short_answer',
            question_text=f'In one sentence, summarise the main goal of {lc.title}.',
            points=Decimal('2.00'), display_order=4,
        )
        QuizQuestion.objects.create(
            quiz=quiz, question_type='essay',
            question_text=f'Discuss how the concepts in {lc.title} apply to a real-world scenario of your choosing.',
            points=Decimal('4.00'), display_order=5,
        )

        # ── Assignment(s) ───────────────────────────────────────────────────
        n_assignments = random.choice([1, 1, 2])
        due = timezone.now() + timedelta(days=random.randint(10, 21))
        Assignment.objects.create(
            lesson=first_lesson, title=f'{lc.code} Practical Assignment 1',
            description=f'Apply the concepts covered in {lc.title} to a short practical task.',
            instructions='Submit a written response covering the points discussed in class.',
            max_score=Decimal('100.00'), passing_score=Decimal('50.00'),
            due_date=due, allow_late_submission=True, late_penalty_percent=10,
        )
        if n_assignments == 2:
            Assignment.objects.create(
                lesson=second_lesson, title=f'{lc.code} Practical Assignment 2',
                description=f'A second applied task extending the material from {lc.title}.',
                instructions='Submit a written response or short report covering the required points.',
                max_score=Decimal('100.00'), passing_score=Decimal('50.00'),
                due_date=due + timedelta(days=14), allow_late_submission=True, late_penalty_percent=10,
            )

        # ── Exam ─────────────────────────────────────────────────────────────
        if is_end_of_semester_biased:
            exam_type = random.choices(
                [Exam.END_OF_SEMESTER, Exam.CA, Exam.MID_SEMESTER, Exam.SUPPLEMENTARY, Exam.PRACTICAL, Exam.ORAL],
                weights=[70, 10, 10, 4, 4, 2], k=1,
            )[0]
        else:
            exam_type = Exam.END_OF_SEMESTER
        start = timezone.now() + timedelta(days=random.randint(25, 60))
        start = start.replace(hour=9, minute=0, second=0, microsecond=0)
        status = random.choices([Exam.PUBLISHED, Exam.SUBMITTED, Exam.DRAFT], weights=[85, 10, 5], k=1)[0]
        exam = Exam.objects.create(
            title=f'{lc.title} — {dict(Exam.EXAM_TYPE_CHOICES)[exam_type]}',
            course=lc, instructor=lc.instructor, exam_type=exam_type,
            start_datetime=start, end_datetime=start + timedelta(hours=2),
            questions_per_student=5, total_marks=Decimal('10.00'), pass_mark=Decimal('5.00'),
            show_result_immediately=True, status=status,
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
                question_text=f'{lc.code} Q{i + 1}: which statement correctly applies the covered concept?',
                marks=Decimal('2.00'), options=opts,
            )

    def seed_lms_bulk(self):
        self.stdout.write('Seeding bulk LMS content (LMSCourse, lessons, quizzes, assignments, exams)...')
        instr_cycle = [self.instr_a, self.instr_b]
        created_lms = 0

        # (a) core courses of every newly-created (non-AI) program
        ai_program = Program.objects.get(code='BSC-AI')
        new_core_courses = Course.objects.filter(course_type='core').exclude(program=ai_program).order_by('program_id', 'code')
        for idx, course in enumerate(new_core_courses):
            code = f"LMS-{course.code}"[:20]
            if LMSCourse.objects.filter(academic_course=course).exists():
                continue
            if LMSCourse.objects.filter(code=code).exists():
                code = f"LMS-{course.code}-{course.id}"[:20]
            instructor = instr_cycle[idx % 2]
            lc = LMSCourse.objects.create(
                title=f"{course.name} ({course.program.name} — {course.get_semester_display()} Yr{course.year_of_study})",
                code=code,
                short_description=f"{course.name} — core delivery for {course.program.name}.",
                description=(
                    f"This LMS course delivers '{course.name}' ({course.code}), a "
                    f"{course.get_course_type_display().lower()} course carrying {course.credit_units} "
                    f"credit unit(s) for {course.program.name} students."
                ),
                learning_objectives=[
                    f"Understand and apply the foundational principles of {course.name}",
                    "Demonstrate competence through assessed assignments and exams",
                ],
                academic_course=course, session=self.current_session, term=course.semester,
                lecturer=instructor, instructor=instructor,
                difficulty_level=min(course.year_of_study * 100, 800),
                is_published=True,
                meta_description=f"Online delivery of {course.name}.",
            )
            self._create_lms_content(lc)
            created_lms += 1

        # (b) previously-undelivered BSc-AI second-semester courses
        ai_second_sem = Course.objects.filter(program=ai_program, semester='second')
        for idx, course in enumerate(ai_second_sem):
            if LMSCourse.objects.filter(academic_course=course).exists():
                continue
            code = f"LMS-{course.code}"[:20]
            if LMSCourse.objects.filter(code=code).exists():
                code = f"LMS-{course.code}-{course.id}"[:20]
            instructor = instr_cycle[idx % 2]
            lc = LMSCourse.objects.create(
                title=f"{course.name} ({ai_program.name} — {course.get_semester_display()} Yr{course.year_of_study})",
                code=code,
                short_description=f"{course.name} — delivery for {ai_program.name}.",
                description=f"This LMS course delivers '{course.name}' ({course.code}) for {ai_program.name} students.",
                learning_objectives=[f"Understand and apply the foundational principles of {course.name}"],
                academic_course=course, session=self.current_session, term=course.semester,
                lecturer=instructor, instructor=instructor,
                difficulty_level=min(course.year_of_study * 100, 800),
                is_published=True,
            )
            self._create_lms_content(lc)
            created_lms += 1

        self.stdout.write(f'  created {created_lms} new LMSCourse deliveries with full content')

    # =========================================================================
    # 6. LIBRARY / BLOG / BADGES / TESTIMONIALS
    # =========================================================================
    def seed_library(self):
        self.stdout.write('Seeding library items...')
        current = LibraryItem.objects.count()
        if current >= LIBRARY_ITEM_TARGET:
            self.stdout.write(f'  already at {current} (target {LIBRARY_ITEM_TARGET}) — skipping')
            return

        categories = {
            'Books': ['Computer Science', 'Engineering', 'Business & Management', 'Health Sciences',
                      'Law', 'Arts & Humanities', 'Education', 'Environmental Design'],
            'Periodicals': ['Journal of Applied Computing', 'Business Review Quarterly',
                            'International Law Digest', 'Health Sciences Bulletin'],
            'References': ['Dictionaries', 'Encyclopedias', 'Style Guides', 'Handbooks'],
            'Other': ['Past Exam Papers', 'Study Guides', 'Research Datasets'],
        }
        authors = [
            'A. Okafor', 'M. Ibrahim', 'S. Adebayo', 'J. Chen', 'R. Patel', 'L. Fernandez',
            'K. Johnson', 'T. Nakamura', 'C. Osei', 'B. Ndubuisi', 'F. Garcia', 'D. Williams',
        ]
        publishers = ['MIT Press', 'Oxford University Press', 'Cambridge University Press',
                      'Pearson', 'Wiley', 'Springer', 'Elsevier', 'MIU Press']

        needed = LIBRARY_ITEM_TARGET - current
        created = 0
        n = current
        while created < needed:
            n += 1
            category = random.choice(list(categories.keys()))
            subcategory = random.choice(categories[category])
            title = f"{subcategory}: Topic Volume {n}" if category != 'Periodicals' else f"{subcategory} — Issue {n}"
            LibraryItem.objects.create(
                category=category, subcategory=subcategory, title=title,
                author=random.choice(authors) if category != 'Periodicals' else '',
                publisher=random.choice(publishers),
                year=random.randint(2005, 2025),
                description=f"A resource covering {subcategory.lower()} topics relevant to MIU coursework.",
                access=random.choice(['public', 'public', 'members']),
                allow_download=random.choice([True, False]),
                allow_read_online=True,
                external_url=f'https://example.com/library/item-{n}',
                created_by=self.admin,
            )
            created += 1
        self.stdout.write(f'  created {created} library items (total now {LibraryItem.objects.count()})')

    def seed_blog(self):
        self.stdout.write('Seeding blog posts...')
        cats_raw = [
            ('campus-news', 'Campus News', 'newspaper', 'blue'),
            ('academics', 'Academics', 'graduation-cap', 'indigo'),
            ('student-life', 'Student Life', 'users', 'green'),
            ('research', 'Research & Innovation', 'flask', 'purple'),
            ('careers', 'Careers & Alumni', 'briefcase', 'amber'),
        ]
        cats = []
        for slug, name, icon, color in cats_raw:
            c, _ = BlogCategory.objects.get_or_create(slug=slug, defaults=dict(name=name, icon=icon, color=color))
            cats.append(c)

        current = BlogPost.objects.count()
        if current >= BLOG_POST_TARGET:
            self.stdout.write(f'  already at {current} (target {BLOG_POST_TARGET}) — skipping')
            return

        topics = [
            'Registration Now Open', 'New Research Grant Awarded', 'Student Wins National Award',
            'Faculty Spotlight', 'Campus Sustainability Initiative Launched', 'Alumni Success Story',
            'New Partnership Announced', 'Upcoming Career Fair', 'Guest Lecture Series Begins',
            'Library Resources Expanded', 'New Degree Programme Approved', 'Sports Day Highlights',
            'Innovation Hub Opens', 'Scholarship Applications Open', 'Graduation Ceremony Recap',
        ]
        authors = [self.admin, self.femiadmin, self.instr_a, self.instr_b]
        authors = [a for a in authors if a]

        needed = BLOG_POST_TARGET - current
        created = 0
        n = current
        while created < needed:
            n += 1
            topic = random.choice(topics)
            title = f"{topic} — {2020 + (n % 6)}/{2021 + (n % 6)} Update {n}"
            author = random.choice(authors)
            days_ago = random.randint(1, 900)
            BlogPost.objects.create(
                title=title,
                subtitle=f"An update from the MIU community on {topic.lower()}.",
                excerpt=f"{topic}: read on for the full story and what it means for students and staff.",
                content=(
                    f"<p>{topic} is the latest development at MIU. This post covers the background, "
                    f"what changed, and how it affects the wider campus community.</p>"
                    f"<p>Students and staff are encouraged to reach out to their department office "
                    f"with any questions about this update.</p>"
                ),
                category=random.choice(cats), author=author,
                status='published', publish_date=timezone.now() - timedelta(days=days_ago),
                read_time=random.randint(2, 8),
            )
            created += 1
        self.stdout.write(f'  created {created} blog posts (total now {BlogPost.objects.count()})')

    BADGE_CATALOG = [
        ('first-lesson', 'First Step', 'Complete your first lesson', 'play-circle', 'blue', 5),
        ('lessons-10', 'Lesson Learner', 'Complete 10 lessons', 'book-open', 'blue', 10),
        ('lessons-25', 'Dedicated Student', 'Complete 25 lessons', 'book-open', 'blue', 15),
        ('lessons-50', 'Knowledge Seeker', 'Complete 50 lessons', 'book-open', 'blue', 20),
        ('lessons-100', 'Century Learner', 'Complete 100 lessons', 'book-open', 'blue', 30),
        ('first-enrollment', 'First Course Enrolled', 'Enroll in your first course', 'bookmark', 'purple', 5),
        ('first-course', 'First Course Completed', 'Complete your first course', 'graduation-cap', 'green', 20),
        ('courses-3', 'Course Collector', 'Complete 3 or more courses', 'graduation-cap', 'gold', 20),
        ('courses-5', 'Marathon Learner', 'Complete 5 or more courses', 'graduation-cap', 'gold', 30),
        ('courses-10', 'Super Achiever', 'Complete 10 or more courses', 'graduation-cap', 'gold', 50),
        ('first-assignment', 'First Submission', 'Submit your first assignment', 'file-text', 'orange', 5),
        ('assignments-5', 'Assignment Starter', 'Submit 5 assignments', 'file-check', 'orange', 10),
        ('assignments-10', 'Hard Worker', 'Submit 10 assignments', 'file-check', 'orange', 15),
        ('assignments-20', 'Assignment Pro', 'Submit 20 assignments', 'file-check', 'orange', 25),
        ('assignments-50', 'Assignment Master', 'Submit 50 assignments', 'file-check', 'orange', 40),
        ('perfect-score', 'Perfect Score', 'Achieve 100% on a course final assessment', 'star', 'gold', 20),
        ('first-quiz', 'Quiz Taker', 'Complete your first quiz', 'help-circle', 'teal', 5),
        ('quizzes-5', 'Quiz Regular', 'Pass 5 quizzes', 'check-circle', 'teal', 10),
        ('quizzes-10', 'Quiz Veteran', 'Pass 10 quizzes', 'check-circle', 'teal', 20),
        ('quizzes-25', 'Quiz Master', 'Pass 25 quizzes', 'check-circle', 'teal', 35),
        ('quiz-perfect', 'Quiz Perfectionist', 'Score 100% on a quiz', 'award', 'gold', 15),
        ('quiz-perfect-5', 'Quiz Master', 'Score 100% on 5 quizzes', 'award', 'gold', 30),
        ('first-post', 'Conversationalist', 'Start your first discussion', 'message-circle', 'purple', 5),
        ('community-10', 'Community Helper', 'Contribute 10 discussions or replies', 'users', 'purple', 15),
        ('community-25', 'Community Star', 'Contribute 25 discussions or replies', 'users', 'purple', 25),
        ('community-50', 'Community Legend', 'Contribute 50 discussions or replies', 'users', 'purple', 40),
        ('early-bird', 'Early Bird', 'Complete lessons before 8 AM for 7 consecutive days', 'sun', 'yellow', 20),
        ('quick-learner', 'Quick Learner', 'Complete a course in under 7 days', 'zap', 'yellow', 25),
        ('streak-7', '7-Day Streak', 'Learn every day for 7 days in a row', 'flame', 'red', 20),
        ('streak-30', '30-Day Streak', 'Learn every day for 30 days in a row', 'flame', 'red', 50),
        ('first-certificate', 'Certified!', 'Earn your first certificate', 'award', 'green', 30),
        ('certificates-3', 'Certificate Collector', 'Earn 3 certificates', 'award', 'green', 45),
    ]

    def seed_badge_catalog(self):
        self.stdout.write('Seeding badge catalog...')
        created = 0
        for slug, name, description, icon, color, points in self.BADGE_CATALOG:
            _, was_created = Badge.objects.get_or_create(
                slug=slug,
                defaults=dict(name=name, description=description, icon=icon, color=color,
                               points=points, criteria=description, is_active=True),
            )
            if was_created:
                created += 1
        self.stdout.write(f'  created {created} badge definitions (total now {Badge.objects.count()})')

    def seed_testimonials(self):
        self.stdout.write('Seeding testimonials...')
        current = Testimonial.objects.count()
        if current >= TESTIMONIAL_TARGET:
            self.stdout.write(f'  already at {current} — skipping')
            return
        samples = [
            ('Amaka O.', 'BSc Data Science Graduate', 'MIU gave me the analytical skills I use every day in my job.'),
            ('Chidi E.', 'BEng Mechanical Engineering, Year 3', 'The hands-on labs made the theory click for me.'),
            ('Rita N.', 'MBA General Management Alumna', 'The faculty genuinely cared about my growth as a leader.'),
            ('Segun A.', 'BSc Public Health Graduate', 'The placement programme opened doors I did not expect.'),
            ('Halima Y.', 'LLB Public Law, Year 2', 'The moot court experience prepared me for real advocacy.'),
            ('Ifeanyi K.', 'BA Performing Arts Graduate', 'A truly supportive creative community.'),
            ('Grace T.', 'BSc Architecture, Year 4', 'The design studio culture pushed my work to a new level.'),
            ('Daniel M.', 'MSc Data Science Alumnus', 'The programme balanced rigor with real industry relevance.'),
            ('Blessing U.', 'BSc Mass Communication Graduate', 'I landed my first internship through a faculty connection.'),
            ('Tunde F.', 'BSc Entrepreneurship Graduate', 'The venture lab helped me launch my first startup.'),
        ]
        created = 0
        n = current
        while current + created < TESTIMONIAL_TARGET and created < len(samples):
            name, role, quote = samples[created]
            Testimonial.objects.create(quote=quote, author_name=name, author_role=role,
                                        is_active=True, order=current + created + 1)
            created += 1
        self.stdout.write(f'  created {created} testimonials (total now {Testimonial.objects.count()})')

    # =========================================================================
    # 7. PER-STUDENT DEPTH (the 7 existing students)
    # =========================================================================
    def _register_course(self, student, lms_course, session, term):
        Enrollment.objects.get_or_create(
            student=student, course=lms_course,
            defaults=dict(enrolled_by=self.admin, status='active'),
        )
        reg = CourseRegistration.objects.filter(
            student=student, course=lms_course.academic_course, session=session, term=term,
        ).first()
        if not reg:
            reg = CourseRegistration(
                student=student, course=lms_course.academic_course, session=session, term=term,
                status='approved',
            )
            reg.save(skip_clean=True)

    def _generate_quiz_attempt(self, student, lms_course, base_score):
        quiz = Quiz.objects.filter(lesson__course=lms_course).first()
        if not quiz or QuizAttempt.objects.filter(quiz=quiz, student=student).exists():
            return
        attempt = QuizAttempt.objects.create(
            quiz=quiz, student=student, is_completed=True,
            completed_at=timezone.now(), time_taken_minutes=random.randint(5, 20),
        )
        total_pts = Decimal('0.00')
        earned_pts = Decimal('0.00')
        still_pending = False
        for q in quiz.questions.all():
            total_pts += q.points
            is_right = random.randint(1, 100) <= base_score
            if q.question_type in ('short_answer', 'essay'):
                if random.random() >= 0.35:
                    pts = q.points if is_right else Decimal('0.00')
                    QuizResponse.objects.create(
                        attempt=attempt, question=q,
                        text_response='A concise, well-structured response covering the required points.',
                        is_correct=is_right, points_earned=pts,
                        graded_by=lms_course.instructor, graded_at=timezone.now(),
                    )
                    if is_right:
                        earned_pts += q.points
                else:
                    QuizResponse.objects.create(
                        attempt=attempt, question=q,
                        text_response='A concise, well-structured response covering the required points.',
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

    def _generate_assignment_submission(self, student, lms_course, base_score):
        assignment = Assignment.objects.filter(lesson__course=lms_course).first()
        if not assignment or AssignmentSubmission.objects.filter(assignment=assignment, student=student).exists():
            return
        graded = random.random() < 0.7
        late = random.random() < 0.2
        score = (assignment.max_score * Decimal(base_score) / Decimal(100)).quantize(Decimal('0.01')) if graded else None
        submitted_at = timezone.now() - timedelta(days=random.randint(1, 15))
        if late:
            submitted_at = assignment.due_date + timedelta(days=random.randint(1, 5))
        AssignmentSubmission.objects.create(
            assignment=assignment, student=student,
            submission_text=f"Submission by {student.get_full_name() or student.username} for {assignment.title}.",
            status='graded' if graded else 'submitted',
            score=score,
            feedback='Solid work overall; keep refining clarity in your written responses.' if graded else '',
            graded_by=lms_course.instructor if graded else None,
            graded_at=timezone.now() if graded else None,
            submitted_at=submitted_at,
        )

    def _generate_exam_response(self, student, lms_course, base_score):
        exam = Exam.objects.filter(course=lms_course).first()
        if not exam or StudentExamResponse.objects.filter(exam=exam, student=student).exists():
            return
        questions = list(exam.questions.all())
        if not questions:
            return
        answers, scores = {}, {}
        total_score = Decimal('0.00')
        total_marks = Decimal('0.00')
        for q in questions:
            total_marks += q.marks
            correct_opt = next((o for o in q.options if o['is_correct']), None)
            if not correct_opt:
                continue
            is_right = random.randint(1, 100) <= base_score
            chosen_opt = correct_opt if is_right else next(o for o in q.options if not o['is_correct'])
            answers[str(q.pk)] = chosen_opt['id']
            marks_awarded = q.marks if is_right else Decimal('0.00')
            scores[str(q.pk)] = {'marks_awarded': str(marks_awarded), 'max_marks': str(q.marks), 'is_correct': is_right}
            total_score += marks_awarded

        outcome = random.random()
        graded_fields = {}
        if outcome < 0.75:
            status = StudentExamResponse.GRADED
            pct = (total_score / total_marks * 100).quantize(Decimal('0.01')) if total_marks else Decimal('0.00')
            passed = total_score >= (exam.pass_mark or 0)
            graded_fields = dict(total_score=total_score, score_percentage=pct, passed=passed,
                                  graded_by=exam.instructor, graded_at=timezone.now())
        else:
            status = StudentExamResponse.SUBMITTED

        StudentExamResponse.objects.create(
            exam=exam, student=student,
            assigned_question_ids=[q.pk for q in questions],
            answers=answers, question_scores=scores, status=status,
            submitted_at=timezone.now() - timedelta(days=random.randint(1, 10)),
            **graded_fields,
        )

    def seed_student_depth(self):
        self.stdout.write('Seeding per-student depth for the 7 existing students...')
        session = self.current_session
        ai_program = Program.objects.get(code='BSC-AI')

        # Exclude priya's open carry-over course from any new registration.
        priya = User.objects.filter(username='priya_escalate').first()
        priya_carry_course_ids = set(
            CourseCarryOver.objects.filter(student=priya, is_cleared=False).values_list('course_id', flat=True)
        ) if priya else set()

        year1_ai_second = LMSCourse.objects.filter(
            academic_course__program=ai_program, academic_course__semester='second',
            academic_course__year_of_study=1,
        )
        year2_ai_second = LMSCourse.objects.filter(
            academic_course__program=ai_program, academic_course__semester='second',
            academic_course__year_of_study=2,
        )

        aptitude = {}
        touched_pairs = []  # (student, academic_course) for recompute

        def register_batch(student, lms_courses, term):
            core_and_general = [
                lc for lc in lms_courses
                if lc.academic_course.course_type in ('core', 'general')
                and lc.academic_course_id not in priya_carry_course_ids
            ]
            electives = [
                lc for lc in lms_courses
                if lc.academic_course.course_type == 'elective'
                and lc.academic_course_id not in priya_carry_course_ids
            ]
            chosen = list(core_and_general)
            if electives:
                chosen.append(random.choice(electives))
            for lc in chosen:
                self._register_course(student, lc, session, term)
                touched_pairs.append((student, lc.academic_course))
            return chosen

        for student in self.students:
            profile = student.profile
            base = random.randint(55, 92)
            aptitude[student.id] = base

            if profile.program_id == ai_program.id:
                if profile.year_of_study == 1:
                    chosen = register_batch(student, list(year1_ai_second), 'second')
                elif profile.year_of_study == 2:
                    chosen = register_batch(student, list(year2_ai_second), 'second')
                else:
                    chosen = []
            elif profile.program_id:
                # e.g. ceceh -> BSC-CYS. Register her across her program's whole
                # first-year catalog (both semesters) since it's a brand-new
                # empty program with no prior delivery at all.
                own_courses = LMSCourse.objects.filter(
                    academic_course__program=profile.program, academic_course__year_of_study=profile.year_of_study,
                )
                chosen = []
                for term in ('first', 'second'):
                    term_courses = [lc for lc in own_courses if lc.term == term]
                    chosen += register_batch(student, term_courses, term)
            else:
                chosen = []

            for lc in chosen:
                self._generate_quiz_attempt(student, lc, base)
                self._generate_assignment_submission(student, lc, base)
                self._generate_exam_response(student, lc, base)

        # ── Recompute grades via the real pipeline, then randomize result_status
        recomputed = 0
        for student, course in set(touched_pairs):
            grade = CourseGrade.recompute_for_student_course(student, course, session, course.semester)
            if grade:
                recomputed += 1
                # Only touch rows we just created/updated in this run; keep the
                # progression-demo sessions' released grades untouched.
                new_status = random.choices(['released', 'pending', 'withheld'], weights=[55, 30, 15], k=1)[0]
                if grade.result_status != new_status:
                    grade.result_status = new_status
                    grade.save(update_fields=['result_status'])
        self.stdout.write(f'  recomputed {recomputed} CourseGrade rows via the real pipeline')

        # ── Certificates: award for one released, passed grade per student ───
        for student in self.students:
            released_pass = CourseGrade.objects.filter(
                student=student, is_passed=True, result_status='released', lms_course__isnull=False,
            ).exclude(lms_course__isnull=True).first()
            if released_pass and released_pass.lms_course:
                Certificate.objects.get_or_create(
                    student=student, course=released_pass.lms_course, certificate_type='lms_course',
                    defaults=dict(
                        certificate_id=f"CERT-{student.username[:6].upper()}-{released_pass.lms_course.code}",
                        completion_date=timezone.now().date(), grade=released_pass.grade or 'A',
                        payment_status=random.choice(['paid', 'unpaid']),
                    ),
                )

        # ── Badges via the real award engine ──────────────────────────────────
        for student in self.students:
            check_and_award_badges(student)

        # ── Notifications ──────────────────────────────────────────────────────
        notif_templates = [
            ('grade', 'New grade released', 'A course grade has just been released for your review.'),
            ('assignment', 'Assignment graded', 'One of your assignment submissions has been graded.'),
            ('announcement', 'New announcement', 'Check the announcements board for the latest campus update.'),
            ('enrollment', 'Enrollment confirmed', 'You have been enrolled in a new course delivery.'),
        ]
        for student in self.students:
            existing = Notification.objects.filter(user=student).count()
            for i in range(max(0, 5 - existing)):
                ntype, title, msg = random.choice(notif_templates)
                Notification.objects.create(
                    user=student, notification_type=ntype, title=title, message=msg,
                    is_read=random.choice([True, False]),
                )

        # ── Messages (student <-> instructor threads) ──────────────────────────
        for student in self.students:
            instr = self.instr_a if student.id % 2 == 0 else self.instr_b
            if not Message.objects.filter(sender=student, recipient=instr).exists():
                Message.objects.create(
                    sender=student, recipient=instr, subject='Question about course material',
                    body='Hi, could you clarify a point from the last lesson? I want to make sure I understood it correctly.',
                )
            if not Message.objects.filter(sender=instr, recipient=student).exists():
                Message.objects.create(
                    sender=instr, recipient=student, subject='Re: upcoming deadlines',
                    body='Just a reminder that your next assignment deadline is approaching — let me know if you need an extension.',
                )

        # ── Discussions / replies on a few newly-delivered courses ─────────────
        sample_courses = list(year1_ai_second[:3]) + list(year2_ai_second[:3])
        for lc in sample_courses:
            if Discussion.objects.filter(course=lc).exists():
                continue
            starter = random.choice(self.students)
            disc = Discussion.objects.create(
                course=lc, title=f'Question about {lc.title}', author=starter,
                content=f'Does anyone have tips for the upcoming assessment in {lc.title}?',
            )
            for _ in range(random.randint(1, 3)):
                replier = random.choice(self.students)
                DiscussionReply.objects.create(
                    discussion=disc, author=replier,
                    content='I found reviewing the lesson notes and doing the practice questions really helped.',
                )

        # ── Study groups ────────────────────────────────────────────────────────
        for lc in sample_courses[:2]:
            group, created = StudyGroup.objects.get_or_create(
                name=f'{lc.code} Study Circle', defaults=dict(
                    description=f'A peer study group for {lc.title}.', course=lc,
                    created_by=self.students[0], max_members=10,
                ),
            )
            members = random.sample(self.students, k=min(4, len(self.students)))
            for m in members:
                StudyGroupMember.objects.get_or_create(study_group=group, user=m)
            if created:
                StudyGroupMessage.objects.create(
                    study_group=group, author=members[0],
                    content=f'Welcome to the {lc.title} study circle! Let\'s share notes and quiz each other.',
                )

        # ── Reviews ──────────────────────────────────────────────────────────────
        for lc in sample_courses:
            enr = Enrollment.objects.filter(course=lc).select_related('student').first()
            if enr and not Review.objects.filter(course=lc, student=enr.student).exists():
                Review.objects.create(
                    course=lc, student=enr.student, rating=random.randint(3, 5),
                    review_text=f'A well-structured delivery of {lc.academic_course.name if lc.academic_course else lc.title}.',
                )

        self.stdout.write('  seeded student depth (registration, grades, quiz/assignment/exam work, certificates, badges, notifications, messages, discussions, study groups, reviews)')

    # =========================================================================
    # 8. FINANCE
    # =========================================================================
    def seed_finance(self):
        self.stdout.write('Seeding finance/payment volume...')
        session = self.current_session

        # ── AllRequiredPayments: tuition + library fee per faculty-bearing program ──
        purposes = [('Tuition Fee', Decimal('500.00')), ('Library Fee', Decimal('25.00')),
                    ('ICT Fee', Decimal('15.00'))]
        created_fees = 0
        for program in Program.objects.filter(is_active=True)[:20]:
            for purpose, amount in purposes:
                _, created = AllRequiredPayments.objects.get_or_create(
                    program=program, academic_session=session, purpose=purpose,
                    semester='first', level=None,
                    defaults=dict(who_to_pay='student', amount=amount, due_date=date(2026, 9, 30)),
                )
                if created:
                    created_fees += 1
        self.stdout.write(f'  created {created_fees} required-payment definitions')

        # ── FeePayment for the 7 students, tied to their real program's fees ──
        created_fee_payments = 0
        for student in self.students:
            profile = student.profile
            if not profile.program_id:
                continue
            fees = AllRequiredPayments.objects.filter(program=profile.program, academic_session=session)
            for fee in fees:
                _, created = FeePayment.objects.get_or_create(
                    user=student, fee=fee,
                    defaults=dict(
                        amount=fee.amount, status=random.choice(['success', 'success', 'pending']),
                        payment_method='card',
                    ),
                )
                if created:
                    created_fee_payments += 1
        self.stdout.write(f'  created {created_fee_payments} fee payments')

        # ── ApplicationPayment for the 4 students with real applications ──────
        created_app_payments = 0
        for app in CourseApplication.objects.filter(user__in=self.students):
            _, created = ApplicationPayment.objects.get_or_create(
                application=app,
                defaults=dict(
                    amount=app.program.application_fee, status='success',
                    payment_method='card', paid_at=timezone.now() - timedelta(days=random.randint(30, 200)),
                ),
            )
            if created:
                created_app_payments += 1
        self.stdout.write(f'  created {created_app_payments} application payments')

        # ── Invoices ─────────────────────────────────────────────────────────────
        created_invoices = 0
        for student in self.students:
            enr = Enrollment.objects.filter(student=student).select_related('course').first()
            if not enr:
                continue
            for i in range(2):
                subtotal = Decimal(random.choice(['150.00', '200.00', '95.00', '300.00']))
                due = date.today() + timedelta(days=14 * (i + 1))
                status = random.choice(['paid', 'sent', 'overdue'])
                inv = Invoice.objects.create(
                    student=student, course=enr.course, subtotal=subtotal, tax_rate=Decimal('0.00'),
                    discount_amount=Decimal('0.00'),
                    status=status, due_date=due,
                    notes=f'Invoice for {enr.course.title}.',
                )
                created_invoices += 1
        self.stdout.write(f'  created {created_invoices} invoices')

        # ── StaffPayroll: 24 months of history for the ~6 staff ────────────────
        today = date.today()
        created_payroll = 0
        for staff in self.staff_all:
            for months_back in range(24):
                m = today.month - months_back
                y = today.year
                while m <= 0:
                    m += 12
                    y -= 1
                _, created = StaffPayroll.objects.get_or_create(
                    staff=staff, month=m, year=y,
                    defaults=dict(
                        base_salary=Decimal('250000.00'), allowances=Decimal('50000.00'),
                        bonuses=Decimal('10000.00') if months_back % 6 == 0 else Decimal('0.00'),
                        tax_deduction=Decimal('15000.00'), other_deductions=Decimal('0.00'),
                        payment_status='paid' if months_back > 0 else random.choice(['paid', 'processing']),
                        payment_method='bank_transfer', currency='NGN',
                        bank_name='GTBank', account_number='0123456789',
                    ),
                )
                if created:
                    created_payroll += 1
        self.stdout.write(f'  created {created_payroll} payroll rows')

        # ── Payment gateway + a couple of transactions ──────────────────────────
        gateway, _ = PaymentGateway.objects.get_or_create(
            slug='stripe-test', defaults=dict(name='Stripe (Test)', gateway_type='stripe',
                                               is_active=True, is_test_mode=True),
        )
        for student in self.students:
            if not Transaction.objects.filter(user=student, transaction_type='enrollment').exists():
                Transaction.objects.create(
                    user=student, transaction_type='enrollment', amount=Decimal('0.00'),
                    currency='NGN', gateway=gateway, status='completed',
                )

    # =========================================================================
    # 9. SUPPORT
    # =========================================================================
    def seed_support(self):
        self.stdout.write('Seeding support-app volume...')

        # ── SLA Policies ─────────────────────────────────────────────────────────
        sla_defs = [
            ('Low Priority SLA', 'low', 24, 72, 48),
            ('Normal Priority SLA', 'normal', 8, 48, 24),
            ('High Priority SLA', 'high', 4, 24, 8),
            ('Urgent Priority SLA', 'urgent', 1, 8, 4),
        ]
        slas = {}
        for name, priority, resp, resol, esc in sla_defs:
            sla, _ = SLAPolicy.objects.get_or_create(
                priority=priority, defaults=dict(name=name, first_response_hours=resp,
                                                  resolution_hours=resol, escalation_hours=esc),
            )
            slas[priority] = sla

        # ── Departments ──────────────────────────────────────────────────────────
        dept_defs = [
            ('Technical Support', 'fas fa-headset'), ('Billing & Payments', 'fas fa-credit-card'),
            ('Academic Records', 'fas fa-graduation-cap'), ('General Enquiries', 'fas fa-question-circle'),
        ]
        depts = []
        for name, icon in dept_defs:
            d, _ = SupportDepartment.objects.get_or_create(
                name=name, defaults=dict(icon=icon, head=self.support_user, is_active=True),
            )
            if self.support_user:
                d.members.add(self.support_user)
            depts.append(d)

        # ── Agent profile for the support user ──────────────────────────────────
        if self.support_user:
            AgentProfile.objects.get_or_create(
                user=self.support_user, defaults=dict(
                    department=depts[0], is_available=True, max_tickets=30,
                    specializations='Technical issues, account access, billing',
                    bio='Primary support agent for MIU student and staff enquiries.',
                ),
            )

        # ── FAQ ──────────────────────────────────────────────────────────────────
        faq_cats_raw = [
            ('Account & Login', 'fa-user-lock'), ('Course Registration', 'fa-book'),
            ('Payments & Fees', 'fa-money-bill'), ('Exams & Grading', 'fa-file-alt'),
            ('Technical Issues', 'fa-laptop'),
        ]
        faq_cats = []
        for order, (name, icon) in enumerate(faq_cats_raw):
            c, _ = FAQCategory.objects.get_or_create(name=name, defaults=dict(icon=icon, order=order))
            faq_cats.append(c)
        faq_pairs = [
            ('How do I reset my password?', 'Use the "Forgot password" link on the login page to receive a reset email.'),
            ('How do I register for courses?', 'Go to Student > Course Registration during the open registration window for your session.'),
            ('When are fees due?', 'Fee due dates are shown on your Finance dashboard and vary by session and payment type.'),
            ('How is my final grade calculated?', 'Grades blend exam, quiz, and assignment scores using each course\'s configured weights.'),
            ('Who do I contact for technical issues?', 'Submit a support ticket under the Technical Issue category and an agent will respond per SLA.'),
            ('How do I view my transcript?', 'Request your transcript from the Academic Records section of your student dashboard.'),
            ('Can I change my program?', 'Contact the registrar via a support ticket to discuss program transfer eligibility.'),
            ('How do I appeal a grade?', 'Submit a support ticket under Academic Records with your course code and grounds for appeal.'),
        ]
        created_faqs = 0
        for i, (q, a) in enumerate(faq_pairs):
            _, created = FAQ.objects.get_or_create(
                question=q, defaults=dict(category=faq_cats[i % len(faq_cats)], answer=a,
                                           is_published=True, created_by=self.support_user),
            )
            if created:
                created_faqs += 1
        self.stdout.write(f'  created {created_faqs} FAQs')

        # ── Knowledge Base ───────────────────────────────────────────────────────
        kb_cat, _ = KBCategory.objects.get_or_create(name='Student Help Centre', defaults=dict(icon='fa-life-ring'))
        kb_titles = [
            'Getting Started with the Student Portal', 'Understanding Your Grade Breakdown',
            'How Course Registration Windows Work', 'Submitting Assignments Correctly',
            'Troubleshooting Login Issues', 'Understanding Your Invoice',
            'How to Request a Transcript', 'Using the Digital Library',
            'Navigating the Exam CBT Interface', 'Contacting Your Instructor',
        ]
        created_kb = 0
        for title in kb_titles:
            _, created = KBArticle.objects.get_or_create(
                title=title, defaults=dict(
                    category=kb_cat, summary=f'A guide covering {title.lower()}.',
                    body=f'<p>This article explains {title.lower()} step by step, with screenshots and tips.</p>',
                    status='published', author=self.support_user or self.admin,
                ),
            )
            if created:
                created_kb += 1
        self.stdout.write(f'  created {created_kb} KB articles')

        # ── Canned Responses ─────────────────────────────────────────────────────
        canned_defs = [
            ('Password Reset Instructions', 'account', 'Please use the "Forgot password" link on the login page. Let us know if you still have trouble.'),
            ('Registration Window Closed', 'course', 'The registration window for this term has closed. Please contact your department for a late-registration exception.'),
            ('Payment Received Confirmation', 'payment', 'We can confirm your payment has been received and applied to your account.'),
            ('Escalating to Technical Team', 'technical', 'Thank you for the details — I am escalating this to our technical team for further investigation.'),
            ('Grade Appeal Process', 'course', 'To appeal a grade, please provide the course code and specific grounds for review, and we will forward this to the registrar.'),
            ('Closing Resolved Ticket', 'other', 'Glad we could help! We are marking this ticket as resolved — feel free to reopen if the issue recurs.'),
        ]
        created_canned = 0
        for title, category, body in canned_defs:
            _, created = CannedResponse.objects.get_or_create(
                title=title, defaults=dict(category=category, body=body, created_by=self.support_user or self.admin),
            )
            if created:
                created_canned += 1
        self.stdout.write(f'  created {created_canned} canned responses')

        # ── Support Announcements ────────────────────────────────────────────────
        announcement_defs = [
            ('Scheduled Maintenance This Weekend', 'The student portal will be briefly unavailable for maintenance this Saturday from 1–3 AM.'),
            ('New Support Hours', 'Support desk hours have been extended to 8 AM – 8 PM on weekdays.'),
            ('Live Chat Coming Soon', 'We are piloting a live chat option for faster support responses.'),
        ]
        for title, body in announcement_defs:
            SupportAnnouncement.objects.get_or_create(
                title=title, defaults=dict(body=body, created_by=self.support_user or self.admin, is_active=True),
            )

        # ── Support Tickets + Replies ────────────────────────────────────────────
        current_tickets = SupportTicket.objects.count()
        if current_tickets >= SUPPORT_TICKET_TARGET:
            self.stdout.write(f'  already at {current_tickets} tickets — skipping ticket generation')
            return

        ticket_pool = self.students + [self.instr_a, self.instr_b]
        ticket_pool = [u for u in ticket_pool if u]
        categories = ['technical', 'account', 'course', 'payment', 'other']
        subjects = [
            'Cannot log in to my account', 'Course registration not saving', 'Invoice shows incorrect amount',
            'Quiz submission failed to save', 'Video lesson will not load', 'Need help understanding my grade',
            'Certificate download not working', 'Assignment upload keeps failing', 'Password reset email not received',
            'Exam countdown timer froze', 'Study group invite not working', 'Library item link is broken',
        ]

        needed = SUPPORT_TICKET_TARGET - current_tickets
        created_tickets = 0
        n = current_tickets
        while created_tickets < needed:
            n += 1
            user = random.choice(ticket_pool)
            category = random.choice(categories)
            priority = random.choices(['low', 'normal', 'high', 'urgent'], weights=[20, 50, 25, 5], k=1)[0]
            status = random.choices(
                ['open', 'in_progress', 'waiting_response', 'resolved', 'closed'],
                weights=[20, 20, 15, 25, 20], k=1,
            )[0]
            subject = random.choice(subjects)
            created_at = timezone.now() - timedelta(days=random.randint(0, 180))
            ticket = SupportTicket.objects.create(
                user=user, category=category, subject=subject,
                description=f"{subject}. This has been happening for a little while and I would appreciate help resolving it.",
                priority=priority, status=status,
                assigned_to=self.support_user if status != 'open' else None,
            )
            SupportTicket.objects.filter(pk=ticket.pk).update(created_at=created_at)
            ticket.refresh_from_db()

            SupportTicketExtra.objects.get_or_create(
                ticket=ticket, defaults=dict(
                    department=random.choice(depts), sla_policy=slas.get(priority),
                    source=random.choice(['portal', 'email', 'portal', 'portal']),
                    tags=category, is_escalated=(priority == 'urgent' and random.random() < 0.5),
                ),
            )

            if self.support_user and status != 'open':
                TicketReply.objects.create(
                    ticket=ticket, author=self.support_user,
                    message='Thanks for reaching out — could you confirm which browser/device you are using so we can dig in further?',
                )
                if status in ('resolved', 'closed'):
                    TicketReply.objects.create(
                        ticket=ticket, author=user,
                        message='That worked, thank you for your help!',
                    )
                    TicketReply.objects.create(
                        ticket=ticket, author=self.support_user,
                        message='Glad to hear it — marking this as resolved. Reach out again if anything else comes up.',
                    )
                TicketHistory.objects.create(
                    ticket=ticket, changed_by=self.support_user, field_name='status',
                    old_value='open', new_value=status, note='Status updated during triage.',
                )

            if status in ('resolved', 'closed') and random.random() < 0.4:
                TicketFeedback.objects.get_or_create(
                    ticket=ticket, defaults=dict(
                        submitted_by=user, rating=random.randint(3, 5),
                        comment='Support was responsive and helpful.',
                    ),
                )

            if priority == 'urgent' and random.random() < 0.3 and self.support_user:
                TicketEscalation.objects.create(
                    ticket=ticket, escalated_by=self.support_user, escalated_to=self.admin,
                    reason='sla_breach', notes='Escalated due to approaching SLA deadline.',
                )

            created_tickets += 1
        self.stdout.write(f'  created {created_tickets} support tickets with replies/history')
