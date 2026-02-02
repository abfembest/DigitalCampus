import random
import uuid
from decimal import Decimal
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from faker import Faker

# Exact imports based on your models.py
from eduweb.models import (
    Announcement, Assignment, AssignmentSubmission, AuditLog, Badge, StudentBadge,
    BlogCategory, BlogPost, Certificate, ContactMessage, Faculty, Course,
    CourseIntake, CourseApplication, ApplicationDocument, ApplicationPayment,
    CourseCategory, Discussion, DiscussionReply, Enrollment, SupportTicket,
    TicketReply, Invoice, LessonProgress, LMSCourse, Lesson, LessonSection,
    Message, Notification, PaymentGateway, Transaction, Quiz, QuizQuestion,
    QuizAnswer, QuizAttempt, QuizResponse, Review, SubscriptionPlan,
    Subscription, SystemConfiguration, UserProfile, Vendor
)

fake = Faker()

class Command(BaseCommand):
    help = 'Seeds comprehensive realistic data for all tables'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("🚀 Starting comprehensive database seeding..."))

        # --- 1. CLEANUP ---
        self.stdout.write("🧹 Cleaning up existing data...")
        models_to_clear = [
            AuditLog, Notification, Message, TicketReply, SupportTicket, StudentBadge, Badge,
            QuizResponse, QuizAttempt, QuizAnswer, QuizQuestion, Quiz, AssignmentSubmission,
            Assignment, LessonProgress, Certificate, Review, Enrollment, DiscussionReply,
            Discussion, Lesson, LessonSection, LMSCourse, CourseCategory, ApplicationPayment,
            ApplicationDocument, CourseApplication, CourseIntake, Course, Faculty, Invoice,
            Transaction, Subscription, SubscriptionPlan, PaymentGateway, BlogPost, BlogCategory,
            ContactMessage, Vendor, SystemConfiguration, Announcement
        ]
        for model in models_to_clear:
            model.objects.all().delete()
        
        User.objects.filter(is_superuser=False).delete()

        # --- 2. CREATE USERS WITH DIFFERENT ROLES ---
        self.stdout.write("👥 Creating users with different roles...")
        users = {'students': [], 'instructors': [], 'admins': [], 'support': [], 'content_managers': [], 'finance': []}
        
        # Create 30 Students
        for i in range(30):
            u = User.objects.create_user(
                username=f"student_{i}_{uuid.uuid4().hex[:4]}",
                email=fake.unique.email(),
                password="12345",
                first_name=fake.first_name(),
                last_name=fake.last_name()
            )
            users['students'].append(u)
            p = u.profile
            p.role = 'student'
            p.bio = fake.text(max_nb_chars=200)
            p.phone = fake.phone_number()[:20]
            p.date_of_birth = fake.date_of_birth(minimum_age=18, maximum_age=40)
            p.address = fake.street_address()
            p.city = fake.city()
            p.country = fake.country()
            p.website = fake.url() if random.choice([True, False]) else ''
            p.linkedin = f"https://linkedin.com/in/{u.username}" if random.choice([True, False]) else ''
            p.twitter = f"https://twitter.com/{u.username}" if random.choice([True, False]) else ''
            p.email_notifications = random.choice([True, False])
            p.marketing_emails = random.choice([True, False])
            p.email_verified = random.choice([True, True, True, False])  # 75% verified
            p.save()
        
        # Create 10 Instructors
        for i in range(10):
            u = User.objects.create_user(
                username=f"instructor_{i}_{uuid.uuid4().hex[:4]}",
                email=fake.unique.email(),
                password="12345",
                first_name=fake.first_name(),
                last_name=fake.last_name()
            )
            users['instructors'].append(u)
            p = u.profile
            p.role = 'instructor'
            p.bio = f"Experienced instructor with {random.randint(5, 20)} years in {fake.job()}. {fake.text(max_nb_chars=150)}"
            p.phone = fake.phone_number()[:20]
            p.date_of_birth = fake.date_of_birth(minimum_age=28, maximum_age=65)
            p.address = fake.street_address()
            p.city = fake.city()
            p.country = fake.country()
            p.website = fake.url()
            p.linkedin = f"https://linkedin.com/in/{u.username}"
            p.email_verified = True
            p.save()
        
        # Create 3 Admins
        for i in range(3):
            u = User.objects.create_user(
                username=f"admin_{i}_{uuid.uuid4().hex[:4]}",
                email=fake.unique.email(),
                password="12345",
                first_name=fake.first_name(),
                last_name=fake.last_name()
            )
            users['admins'].append(u)
            p = u.profile
            p.role = 'admin'
            p.bio = "System administrator"
            p.phone = fake.phone_number()[:20]
            p.email_verified = True
            p.save()
        
        # Create 3 Support Staff
        for i in range(3):
            u = User.objects.create_user(
                username=f"support_{i}_{uuid.uuid4().hex[:4]}",
                email=fake.unique.email(),
                password="12345",
                first_name=fake.first_name(),
                last_name=fake.last_name()
            )
            users['support'].append(u)
            p = u.profile
            p.role = 'support'
            p.bio = "Customer support specialist"
            p.phone = fake.phone_number()[:20]
            p.email_verified = True
            p.save()
        
        # Create 2 Content Managers
        for i in range(2):
            u = User.objects.create_user(
                username=f"content_mgr_{i}_{uuid.uuid4().hex[:4]}",
                email=fake.unique.email(),
                password="12345",
                first_name=fake.first_name(),
                last_name=fake.last_name()
            )
            users['content_managers'].append(u)
            p = u.profile
            p.role = 'content_manager'
            p.bio = "Content management and curation"
            p.phone = fake.phone_number()[:20]
            p.email_verified = True
            p.save()
        
        # Create 2 Finance Managers
        for i in range(2):
            u = User.objects.create_user(
                username=f"finance_{i}_{uuid.uuid4().hex[:4]}",
                email=fake.unique.email(),
                password="12345",
                first_name=fake.first_name(),
                last_name=fake.last_name()
            )
            users['finance'].append(u)
            p = u.profile
            p.role = 'finance'
            p.bio = "Financial management and accounting"
            p.phone = fake.phone_number()[:20]
            p.email_verified = True
            p.save()

        all_users = users['students'] + users['instructors'] + users['admins'] + users['support'] + users['content_managers'] + users['finance']

        # --- 3. SYSTEM CONFIGURATION ---
        self.stdout.write("⚙️ Creating system configurations...")
        configs = [
            {'key': 'site_name', 'value': 'Digital Learning Academy', 'setting_type': 'text', 'description': 'Website name', 'is_public': True},
            {'key': 'site_email', 'value': 'admin@digitallearning.edu', 'setting_type': 'text', 'description': 'Contact email', 'is_public': True},
            {'key': 'max_upload_size', 'value': '10', 'setting_type': 'number', 'description': 'Max file upload size in MB', 'is_public': False},
            {'key': 'enable_registration', 'value': 'true', 'setting_type': 'boolean', 'description': 'Allow new registrations', 'is_public': True},
            {'key': 'payment_settings', 'value': '{"currency": "USD", "tax_rate": 0.08}', 'setting_type': 'json', 'description': 'Payment configuration', 'is_public': False},
            {'key': 'smtp_settings', 'value': '{"host": "smtp.gmail.com", "port": 587}', 'setting_type': 'json', 'description': 'Email server settings', 'is_public': False},
        ]
        for cfg in configs:
            SystemConfiguration.objects.create(
                key=cfg['key'],
                value=cfg['value'],
                setting_type=cfg['setting_type'],
                description=cfg['description'],
                is_public=cfg['is_public'],
                updated_by=random.choice(users['admins'])
            )

        # --- 4. VENDORS ---
        self.stdout.write("🏢 Creating vendors...")
        vendors = []
        vendor_names = ['TechEdu Partners', 'Global Learning Solutions', 'Academic Publishers Inc', 'Digital Content Pro', 'EduTech Innovations']
        for name in vendor_names:
            v = Vendor.objects.create(
                name=name,
                email=fake.company_email(),
                country=fake.country(),
                stripe_account_id=f"acct_{uuid.uuid4().hex[:16]}" if random.choice([True, False]) else '',
                is_active=random.choice([True, True, True, False])
            )
            vendors.append(v)

        # --- 5. FACULTIES & ACADEMIC COURSES ---
        self.stdout.write("🎓 Creating faculties and academic courses...")
        faculties = []
        faculty_data = [
            {'name': 'Faculty of Engineering', 'code': 'ENG', 'icon': 'cog', 'color_primary': 'blue', 'color_secondary': 'cyan'},
            {'name': 'Faculty of Business', 'code': 'BUS', 'icon': 'briefcase', 'color_primary': 'green', 'color_secondary': 'emerald'},
            {'name': 'Faculty of Computer Science', 'code': 'CS', 'icon': 'laptop', 'color_primary': 'purple', 'color_secondary': 'violet'},
            {'name': 'Faculty of Medicine', 'code': 'MED', 'icon': 'heart-pulse', 'color_primary': 'red', 'color_secondary': 'rose'},
            {'name': 'Faculty of Arts & Humanities', 'code': 'AH', 'icon': 'palette', 'color_primary': 'orange', 'color_secondary': 'amber'},
        ]
        for fd in faculty_data:
            f = Faculty.objects.create(
                name=fd['name'],
                code=fd['code'],
                icon=fd['icon'],
                color_primary=fd['color_primary'],
                color_secondary=fd['color_secondary'],
                tagline=fake.catch_phrase(),
                description=fake.text(max_nb_chars=500),
                mission=fake.text(max_nb_chars=300),
                vision=fake.text(max_nb_chars=300),
                student_count=random.randint(500, 2000),
                placement_rate=random.randint(80, 98),
                partner_count=random.randint(20, 100),
                international_faculty=random.randint(10, 40)
            )
            faculties.append(f)
        
        academic_courses = []
        course_data = [
            ('Bachelor of Software Engineering', 'BSE-101', faculties[2], 'undergraduate', 4, '75.00', '8500.00'),
            ('Master of Business Administration', 'MBA-201', faculties[1], 'postgraduate', 2, '100.00', '15000.00'),
            ('Bachelor of Mechanical Engineering', 'BME-102', faculties[0], 'undergraduate', 4, '75.00', '9000.00'),
            ('Doctor of Medicine', 'MD-301', faculties[3], 'doctorate', 6, '150.00', '25000.00'),
            ('Bachelor of Arts in Psychology', 'BAP-103', faculties[4], 'undergraduate', 3, '50.00', '6000.00'),
            ('Master of Data Science', 'MDS-202', faculties[2], 'postgraduate', 2, '100.00', '12000.00'),
            ('Bachelor of Accounting', 'BAC-104', faculties[1], 'undergraduate', 4, '75.00', '7500.00'),
            ('Master of Electrical Engineering', 'MEE-203', faculties[0], 'postgraduate', 2, '100.00', '11000.00'),
            ('Bachelor of Nursing', 'BN-105', faculties[3], 'undergraduate', 4, '75.00', '8000.00'),
            ('Bachelor of Fine Arts', 'BFA-106', faculties[4], 'undergraduate', 4, '50.00', '6500.00'),
        ]
        
        for title, code, faculty, level, duration, app_fee, tuition in course_data:
            ac = Course.objects.create(
                name=title,
                code=code,
                faculty=faculty,
                degree_level=level,
                duration_years=Decimal(str(duration)),
                application_fee=Decimal(app_fee),
                tuition_fee=Decimal(tuition),
                tagline=fake.catch_phrase(),
                overview=fake.text(max_nb_chars=300),
                description=fake.text(max_nb_chars=800),
                learning_outcomes=[fake.sentence() for _ in range(random.randint(4, 6))],
                career_paths=[fake.job() for _ in range(random.randint(3, 5))],
                core_courses=[f"{fake.word().title()} {random.randint(100, 499)}" for _ in range(random.randint(6, 10))],
                specialization_tracks=[fake.catch_phrase() for _ in range(random.randint(2, 4))],
                entry_requirements=[
                    "High school diploma or equivalent",
                    "Minimum GPA of 3.0",
                    "English language proficiency",
                    fake.sentence()
                ],
                available_study_modes=['full_time', 'part_time'],
                credits_required=random.randint(90, 150),
                avg_starting_salary=f"${random.randint(40, 120)}k",
                job_placement_rate=random.randint(70, 98),
                meta_description=fake.sentence(nb_words=20),
                meta_keywords=', '.join([fake.word() for _ in range(5)]),
                is_active=True,
                is_featured=random.choice([True, False, False]),
                display_order=len(academic_courses)
            )
            academic_courses.append(ac)
            
            # Create 2-3 intakes per course
            for period in random.sample(['january', 'september', 'may'], k=random.randint(2, 3)):
                CourseIntake.objects.create(
                    course=ac,
                    intake_period=period,
                    year=random.choice([2025, 2026]),
                    start_date=timezone.now().date() + timedelta(days=random.randint(30, 365)),
                    application_deadline=timezone.now().date() + timedelta(days=random.randint(15, 180)),
                    available_slots=random.randint(30, 100)
                )

        # --- 6. COURSE APPLICATIONS ---
        self.stdout.write("📝 Creating course applications...")
        statuses = ['draft', 'pending_payment', 'payment_complete', 'under_review', 'approved', 'rejected', 'withdrawn']
        for _ in range(25):
            student = random.choice(users['students'])
            course = random.choice(academic_courses)
            intake = random.choice(list(course.intakes.all()))
            status = random.choice(statuses)
            
            app = CourseApplication.objects.create(
                application_id=f"APP-{uuid.uuid4().hex[:12].upper()}",
                user=student,
                course=course,
                intake=intake,
                study_mode=random.choice(['full_time', 'part_time', 'online']),
                first_name=student.first_name,
                last_name=student.last_name,
                email=student.email,
                phone=student.profile.phone,
                date_of_birth=student.profile.date_of_birth or fake.date_of_birth(minimum_age=18, maximum_age=40),
                gender=random.choice(['male', 'female', 'other']),
                nationality=fake.country(),
                payment_status=random.choice(['pending', 'completed', 'failed']),
                address_line1=fake.street_address(),
                address_line2=fake.secondary_address() if random.choice([True, False]) else '',
                city=fake.city(),
                state=fake.state(),
                postal_code=fake.postcode(),
                country=fake.country(),
                highest_qualification=random.choice(['High School', 'Bachelor', 'Master', 'Diploma']),
                institution_name=fake.company() + ' University',
                graduation_year=str(random.randint(2015, 2024)),
                gpa_or_grade=f"{random.uniform(2.5, 4.0):.2f}",
                language_skill=random.choice(['ielts', 'toefl', 'pte', 'none']) if random.choice([True, False]) else None,
                language_score=Decimal(f"{random.uniform(5.5, 9.0):.1f}") if random.choice([True, False]) else None,
                work_experience_years=random.randint(0, 10),
                personal_statement=fake.text(max_nb_chars=500),
                how_did_you_hear=random.choice(['Google Search', 'Social Media', 'Friend', 'Education Fair', 'Advertisement']),
                scholarship=random.choice([True, False]),
                accept_privacy_policy=True,
                accept_terms_conditions=True,
                marketing_consent=random.choice([True, False]),
                emergency_contact_name=fake.name(),
                emergency_contact_phone=fake.phone_number()[:20],
                emergency_contact_relationship=random.choice(['Parent', 'Sibling', 'Spouse', 'Friend']),
                status=status,
                reviewer=random.choice(users['admins']) if status in ['under_review', 'approved', 'rejected'] else None,
                review_notes=fake.sentence() if status in ['approved', 'rejected'] else '',
                submitted_at=timezone.now() - timedelta(days=random.randint(1, 60)) if status != 'draft' else None,
                reviewed_at=timezone.now() - timedelta(days=random.randint(1, 30)) if status in ['approved', 'rejected'] else None
            )
            
            # Create application payment if status allows
            if status in ['payment_complete', 'under_review', 'approved', 'rejected']:
                ApplicationPayment.objects.create(
                    application=app,
                    amount=course.application_fee,
                    currency='USD',
                    status=random.choice(['success', 'pending']),
                    payment_method=random.choice(['card', 'paypal', 'bank_transfer']),
                    payment_reference=f"PAY-{uuid.uuid4().hex[:12].upper()}",
                    gateway_payment_id=f"pi_{uuid.uuid4().hex[:24]}",
                    card_last4=str(random.randint(1000, 9999)) if random.choice([True, False]) else '',
                    card_brand=random.choice(['Visa', 'Mastercard', 'Amex']) if random.choice([True, False]) else '',
                    paid_at=timezone.now() - timedelta(days=random.randint(1, 50))
                )

        # --- 7. PAYMENT GATEWAYS ---
        self.stdout.write("💳 Creating payment gateways...")
        gateways = []
        gateway_data = [
            ('Stripe', 'stripe', True, False),
            ('PayPal', 'paypal', True, False),
            ('Razorpay', 'razorpay', False, True),
        ]
        for name, gtype, active, test_mode in gateway_data:
            g = PaymentGateway.objects.create(
                name=name,
                gateway_type=gtype,
                api_key=f"pk_test_{uuid.uuid4().hex}" if test_mode else f"pk_live_{uuid.uuid4().hex}",
                api_secret=f"sk_test_{uuid.uuid4().hex}" if test_mode else f"sk_live_{uuid.uuid4().hex}",
                webhook_secret=f"whsec_{uuid.uuid4().hex[:32]}",
                is_active=active,
                is_test_mode=test_mode
            )
            gateways.append(g)

        # --- 8. COURSE CATEGORIES (LMS) ---
        self.stdout.write("📚 Creating LMS course categories...")
        categories = []
        category_data = [
            ('Web Development', 'code', 'blue'),
            ('Data Science', 'chart-line', 'green'),
            ('Mobile Development', 'mobile', 'purple'),
            ('Cloud Computing', 'cloud', 'cyan'),
            ('Cybersecurity', 'shield', 'red'),
            ('Artificial Intelligence', 'brain', 'orange'),
            ('Business & Marketing', 'briefcase', 'yellow'),
            ('Design', 'palette', 'pink'),
        ]
        for name, icon, color in category_data:
            c = CourseCategory.objects.create(
                name=name,
                description=fake.text(max_nb_chars=200),
                icon=icon,
                color=color,
                display_order=len(categories)
            )
            categories.append(c)

        # --- 9. LMS COURSES ---
        self.stdout.write("🎯 Creating LMS courses with lessons, sections, and content...")
        lms_courses = []
        course_titles = [
            'Complete Python Programming Bootcamp',
            'Advanced React and Redux',
            'Machine Learning A-Z',
            'AWS Cloud Practitioner Certification',
            'Ethical Hacking from Scratch',
            'Full Stack Web Development',
            'Data Analysis with Python',
            'Mobile App Development with Flutter',
            'DevOps Engineering Complete Guide',
            'Digital Marketing Mastery',
            'UI/UX Design Fundamentals',
            'Blockchain and Cryptocurrency',
            'Natural Language Processing',
            'Django Web Framework',
            'Docker and Kubernetes',
        ]
        
        for title in course_titles:
            instructor = random.choice(users['instructors'])
            lc = LMSCourse.objects.create(
                title=title,
                code=f"LMS-{random.randint(100, 999)}",
                category=random.choice(categories),
                short_description=fake.sentence(nb_words=15),
                description=fake.text(max_nb_chars=800),
                learning_objectives=[fake.sentence() for _ in range(random.randint(3, 6))],
                prerequisites=[fake.sentence() for _ in range(random.randint(1, 3))] if random.choice([True, False]) else [],
                difficulty_level=random.choice(['beginner', 'intermediate', 'advanced']),
                duration_hours=Decimal(str(random.randint(10, 100))),
                language='English',
                instructor=instructor,
                instructor_name=instructor.get_full_name(),
                instructor_bio=instructor.profile.bio,
                is_free=random.choice([True, False]),
                price=Decimal('0.00') if random.choice([True, False, False]) else Decimal(str(random.randint(49, 299))),
                discount_price=Decimal(str(random.randint(29, 199))) if random.choice([True, False, False]) else None,
                max_students=random.randint(50, 500) if random.choice([True, False]) else None,
                is_published=True,
                is_featured=random.choice([True, False, False, False]),
                has_certificate=random.choice([True, False]),
                meta_description=fake.sentence(nb_words=20),
                meta_keywords=', '.join([fake.word() for _ in range(5)])
            )
            lms_courses.append(lc)
            
            # Create 3-5 sections per course
            for s_idx in range(random.randint(3, 5)):
                section = LessonSection.objects.create(
                    course=lc,
                    title=f"Module {s_idx + 1}: {fake.catch_phrase()}",
                    description=fake.text(max_nb_chars=200),
                    display_order=s_idx
                )
                
                # Create 4-8 lessons per section
                for l_idx in range(random.randint(4, 8)):
                    lesson_type = random.choice(['video', 'video', 'video', 'text', 'file'])
                    lesson = Lesson.objects.create(
                        course=lc,
                        section=section,
                        title=f"Lesson {s_idx + 1}.{l_idx + 1}: {fake.catch_phrase()}",
                        lesson_type=lesson_type,
                        description=fake.text(max_nb_chars=300),
                        content=fake.text(max_nb_chars=1000) if lesson_type == 'text' else '',
                        video_url=f"https://www.youtube.com/watch?v={uuid.uuid4().hex[:11]}" if lesson_type == 'video' else '',
                        video_duration_minutes=random.randint(5, 45) if lesson_type == 'video' else 0,
                        is_preview=random.choice([True, False, False, False]),
                        display_order=l_idx
                    )
                    
                    # Create assignment for some lessons
                    if random.choice([True, False, False]):
                        Assignment.objects.create(
                            lesson=lesson,
                            title=f"Assignment: {fake.catch_phrase()}",
                            description=fake.text(max_nb_chars=400),
                            instructions=fake.text(max_nb_chars=300),
                            max_score=Decimal('100.00'),
                            passing_score=Decimal(str(random.randint(50, 70))),
                            due_date=timezone.now() + timedelta(days=random.randint(7, 30)),
                            allow_late_submission=random.choice([True, False]),
                            late_penalty_percent=random.randint(0, 20)
                        )
                    
                    # Create quiz for some lessons
                    if random.choice([True, False, False]):
                        quiz = Quiz.objects.create(
                            lesson=lesson,
                            title=f"Quiz: {lesson.title}",
                            description=fake.sentence(),
                            instructions="Answer all questions to the best of your ability.",
                            time_limit_minutes=random.randint(10, 60) if random.choice([True, False]) else None,
                            passing_score=Decimal(str(random.randint(60, 80))),
                            max_attempts=random.randint(1, 3),
                            shuffle_questions=random.choice([True, False]),
                            show_correct_answers=random.choice([True, False])
                        )
                        
                        # Create 5-10 questions per quiz
                        for q_idx in range(random.randint(5, 10)):
                            question = QuizQuestion.objects.create(
                                quiz=quiz,
                                question_type=random.choice(['multiple_choice', 'multiple_choice', 'true_false']),
                                question_text=fake.sentence() + "?",
                                explanation=fake.sentence() if random.choice([True, False]) else '',
                                points=Decimal('1.00'),
                                display_order=q_idx
                            )
                            
                            # Create answers for multiple choice
                            if question.question_type == 'multiple_choice':
                                correct_idx = random.randint(0, 3)
                                for a_idx in range(4):
                                    QuizAnswer.objects.create(
                                        question=question,
                                        answer_text=fake.sentence(),
                                        is_correct=(a_idx == correct_idx),
                                        display_order=a_idx
                                    )
                            elif question.question_type == 'true_false':
                                QuizAnswer.objects.create(question=question, answer_text="True", is_correct=random.choice([True, False]), display_order=0)
                                QuizAnswer.objects.create(question=question, answer_text="False", is_correct=random.choice([True, False]), display_order=1)

        # --- 10. ENROLLMENTS & PROGRESS ---
        self.stdout.write("📊 Creating enrollments and progress...")
        for _ in range(40):
            student = random.choice(users['students'])
            course = random.choice(lms_courses)
            
            # Check if enrollment already exists
            if not Enrollment.objects.filter(student=student, course=course).exists():
                enr = Enrollment.objects.create(
                    student=student,
                    course=course,
                    enrolled_by=random.choice(users['admins']) if random.choice([True, False]) else None,
                    progress_percentage=Decimal(str(random.randint(0, 100))),
                    completed_lessons=random.randint(0, course.lessons.count()),
                    current_grade=Decimal(str(random.uniform(60, 100))) if random.choice([True, False]) else None,
                    status=random.choice(['active', 'active', 'active', 'completed', 'dropped']),
                    enrolled_at=timezone.now() - timedelta(days=random.randint(1, 180)),
                    completed_at=timezone.now() - timedelta(days=random.randint(1, 30)) if random.choice([True, False, False]) else None,
                    last_accessed=timezone.now() - timedelta(hours=random.randint(1, 72))
                )
                
                # Create lesson progress for some lessons
                lessons = list(course.lessons.all()[:random.randint(1, min(10, course.lessons.count()))])
                for lesson in lessons:
                    LessonProgress.objects.create(
                        enrollment=enr,
                        lesson=lesson,
                        is_completed=random.choice([True, False]),
                        completion_percentage=Decimal(str(random.randint(0, 100))),
                        time_spent_minutes=random.randint(5, 120),
                        video_progress_seconds=random.randint(60, 1800) if lesson.lesson_type == 'video' else 0,
                        started_at=timezone.now() - timedelta(days=random.randint(1, 60)),
                        completed_at=timezone.now() - timedelta(days=random.randint(1, 30)) if random.choice([True, False]) else None
                    )
                
                # Create assignment submissions
                for assignment in course.lessons.filter(assignments__isnull=False).distinct()[:random.randint(1, 3)]:
                    for assgn in assignment.assignments.all():
                        AssignmentSubmission.objects.create(
                            assignment=assgn,
                            student=student,
                            submission_text=fake.text(max_nb_chars=500),
                            score=Decimal(str(random.uniform(50, 100))) if random.choice([True, False]) else None,
                            feedback=fake.sentence() if random.choice([True, False]) else '',
                            graded_by=course.instructor if random.choice([True, False]) else None,
                            graded_at=timezone.now() - timedelta(days=random.randint(1, 20)) if random.choice([True, False]) else None,
                            status=random.choice(['draft', 'submitted', 'graded', 'returned']),
                            is_late=random.choice([True, False, False]),
                            submitted_at=timezone.now() - timedelta(days=random.randint(1, 30))
                        )
                
                # Create quiz attempts
                for lesson in course.lessons.filter(quizzes__isnull=False).distinct()[:random.randint(1, 3)]:
                    for quiz in lesson.quizzes.all():
                        attempt = QuizAttempt.objects.create(
                            quiz=quiz,
                            student=student,
                            score=Decimal(str(random.uniform(50, 100))),
                            max_score=Decimal(str(quiz.questions.count())),
                            percentage=Decimal(str(random.uniform(50, 100))),
                            is_completed=True,
                            passed=random.choice([True, False]),
                            started_at=timezone.now() - timedelta(days=random.randint(1, 40)),
                            completed_at=timezone.now() - timedelta(days=random.randint(1, 40)),
                            time_taken_minutes=random.randint(10, 60)
                        )
                        
                        # Create quiz responses
                        for question in quiz.questions.all():
                            if question.question_type in ['multiple_choice', 'true_false']:
                                selected = random.choice(list(question.answers.all()))
                                QuizResponse.objects.create(
                                    attempt=attempt,
                                    question=question,
                                    selected_answer=selected,
                                    is_correct=selected.is_correct,
                                    points_earned=question.points if selected.is_correct else Decimal('0.00')
                                )

        # --- 11. REVIEWS ---
        self.stdout.write("⭐ Creating course reviews...")
        for course in lms_courses:
            for _ in range(random.randint(5, 15)):
                student = random.choice(users['students'])
                if not Review.objects.filter(course=course, student=student).exists():
                    Review.objects.create(
                        course=course,
                        student=student,
                        rating=random.randint(3, 5),
                        review_text=fake.text(max_nb_chars=300) if random.choice([True, False]) else '',
                        is_approved=random.choice([True, True, True, False]),
                        created_at=timezone.now() - timedelta(days=random.randint(1, 90))
                    )

        # --- 12. TRANSACTIONS & INVOICES ---
        self.stdout.write("💰 Creating transactions and invoices...")
        for student in users['students'][:20]:
            # Create some transactions
            for _ in range(random.randint(1, 3)):
                Transaction.objects.create(
                    transaction_id=f"TXN-{uuid.uuid4().hex[:12].upper()}",
                    user=student,
                    transaction_type=random.choice(['enrollment', 'subscription', 'refund']),
                    amount=Decimal(str(random.randint(50, 300))),
                    currency='USD',
                    gateway=random.choice(gateways),
                    gateway_transaction_id=f"pi_{uuid.uuid4().hex[:24]}",
                    status=random.choice(['completed', 'completed', 'pending', 'failed']),
                    course=random.choice(lms_courses) if random.choice([True, False]) else None,
                    metadata={'ip_address': fake.ipv4(), 'user_agent': fake.user_agent()},
                    created_at=timezone.now() - timedelta(days=random.randint(1, 90)),
                    completed_at=timezone.now() - timedelta(days=random.randint(1, 90)) if random.choice([True, False]) else None
                )
            
            # Create invoices
            for _ in range(random.randint(1, 2)):
                subtotal = Decimal(str(random.randint(100, 500)))
                tax_rate = Decimal('8.00')
                tax_amount = (subtotal * tax_rate / Decimal('100')).quantize(Decimal('0.01'))
                discount = Decimal(str(random.randint(0, 50)))
                total = (subtotal + tax_amount - discount).quantize(Decimal('0.01'))
                
                Invoice.objects.create(
                    student=student,
                    course=random.choice(lms_courses) if random.choice([True, False]) else None,
                    subtotal=subtotal,
                    tax_rate=tax_rate,
                    tax_amount=tax_amount,
                    discount_amount=discount,
                    total_amount=total,
                    currency='USD',
                    status=random.choice(['draft', 'sent', 'paid', 'overdue', 'cancelled']),
                    due_date=timezone.now().date() + timedelta(days=random.randint(-30, 30)),
                    paid_date=timezone.now().date() - timedelta(days=random.randint(1, 30)) if random.choice([True, False]) else None,
                    notes=fake.sentence() if random.choice([True, False]) else ''
                )

        # --- 13. SUBSCRIPTION PLANS & SUBSCRIPTIONS ---
        self.stdout.write("🎫 Creating subscription plans...")
        plans = []
        plan_data = [
            ('Basic', 'Basic access to all courses', ['Access to 5 courses', 'Basic support'], '29.99', 'monthly'),
            ('Pro', 'Professional learning plan', ['Access to all courses', 'Priority support', 'Certificates'], '79.99', 'monthly'),
            ('Premium', 'Premium unlimited access', ['Unlimited courses', '24/7 support', 'All certificates', 'Career guidance'], '199.99', 'quarterly'),
            ('Annual Pro', 'Best value annual plan', ['Access to all courses', 'Priority support', 'Certificates', '2 free months'], '799.99', 'yearly'),
        ]
        for name, desc, features, price, cycle in plan_data:
            p = SubscriptionPlan.objects.create(
                name=name,
                description=desc,
                features=features,
                price=Decimal(price),
                currency='USD',
                billing_cycle=cycle,
                max_courses=None if 'unlimited' in desc.lower() else random.randint(5, 20),
                is_active=True,
                is_popular=random.choice([True, False, False]),
                display_order=len(plans)
            )
            plans.append(p)
        
        # Create subscriptions
        for student in random.sample(users['students'], k=15):
            plan = random.choice(plans)
            Subscription.objects.create(
                user=student,
                plan=plan,
                status=random.choice(['active', 'active', 'cancelled', 'expired']),
                start_date=timezone.now().date() - timedelta(days=random.randint(1, 180)),
                end_date=timezone.now().date() + timedelta(days=random.randint(30, 365)),
                auto_renew=random.choice([True, False]),
                gateway_subscription_id=f"sub_{uuid.uuid4().hex[:24]}",
                cancelled_at=timezone.now() - timedelta(days=random.randint(1, 30)) if random.choice([True, False, False]) else None
            )

        # --- 14. CERTIFICATES ---
        self.stdout.write("🏆 Creating certificates...")
        for enrollment in Enrollment.objects.filter(status='completed')[:20]:
            Certificate.objects.create(
                student=enrollment.student,
                course=enrollment.course,
                certificate_id=f"CERT-{uuid.uuid4().hex[:12].upper()}",
                completion_date=(enrollment.completed_at or timezone.now()).date(),
                grade=str(int(enrollment.current_grade)) if enrollment.current_grade else 'A',
                verification_code=uuid.uuid4(),
                is_verified=True
            )

        # --- 15. BADGES ---
        self.stdout.write("🏅 Creating badges...")
        badges = []
        badge_data = [
            ('First Course', 'Complete your first course', 'Complete any course', 10, 'award', 'gold'),
            ('Quiz Master', 'Pass 10 quizzes with 100%', 'Score perfect in 10 quizzes', 25, 'trophy', 'gold'),
            ('Dedicated Learner', 'Study for 100 hours', 'Accumulate 100 hours of study time', 50, 'clock', 'blue'),
            ('Assignment Pro', 'Submit 20 assignments', 'Submit 20 assignments on time', 30, 'file-text', 'green'),
            ('Discussion Leader', 'Start 10 discussions', 'Create 10 discussion topics', 20, 'message-circle', 'purple'),
        ]
        for name, desc, criteria, points, icon, color in badge_data:
            b = Badge.objects.create(
                name=name,
                description=desc,
                criteria=criteria,
                points=points,
                icon=icon,
                color=color
            )
            badges.append(b)
        
        # Award badges to students
        for student in random.sample(users['students'], k=15):
            for badge in random.sample(badges, k=random.randint(1, 3)):
                if not StudentBadge.objects.filter(student=student, badge=badge).exists():
                    StudentBadge.objects.create(
                        student=student,
                        badge=badge,
                        awarded_by=random.choice(users['instructors']),
                        reason=fake.sentence()
                    )

        # --- 16. BLOG ---
        self.stdout.write("📝 Creating blog posts...")
        blog_categories = []
        blog_cat_data = ['Technology', 'Education', 'Career Advice', 'Student Life', 'Industry News']
        for cat_name in blog_cat_data:
            bc = BlogCategory.objects.create(
                name=cat_name,
                description=fake.text(max_nb_chars=150),
                icon=random.choice(['folder', 'book', 'briefcase', 'users', 'newspaper']),
                color=random.choice(['blue', 'green', 'purple', 'red', 'orange']),
                display_order=len(blog_categories)
            )
            blog_categories.append(bc)
        
        for _ in range(25):
            author = random.choice(users['instructors'] + users['content_managers'])
            BlogPost.objects.create(
                title=fake.catch_phrase(),
                subtitle=fake.sentence() if random.choice([True, False]) else '',
                excerpt=fake.text(max_nb_chars=200),
                content='\n\n'.join([fake.paragraph() for _ in range(random.randint(3, 8))]),
                category=random.choice(blog_categories),
                tags=[fake.word() for _ in range(random.randint(2, 5))],
                author=author,
                author_name=author.get_full_name(),
                author_title=author.profile.role.replace('_', ' ').title(),
                featured_image_alt=fake.sentence() if random.choice([True, False]) else '',
                read_time=random.randint(3, 15),
                views_count=random.randint(0, 5000),
                status=random.choice(['draft', 'published', 'published', 'published']),
                is_featured=random.choice([True, False, False, False]),
                publish_date=timezone.now() - timedelta(days=random.randint(1, 365)),
                meta_description=fake.sentence(nb_words=20),
                meta_keywords=', '.join([fake.word() for _ in range(5)])
            )

        # --- 17. DISCUSSIONS ---
        self.stdout.write("💬 Creating discussions and replies...")
        for course in random.sample(lms_courses, k=10):
            for _ in range(random.randint(3, 8)):
                discussion = Discussion.objects.create(
                    course=course,
                    title=fake.sentence(),
                    content=fake.text(max_nb_chars=500),
                    author=random.choice(users['students']),
                    is_pinned=random.choice([True, False, False, False]),
                    is_locked=random.choice([True, False, False, False]),
                    views_count=random.randint(5, 500)
                )
                
                # Add replies
                for _ in range(random.randint(1, 8)):
                    DiscussionReply.objects.create(
                        discussion=discussion,
                        author=random.choice(all_users),
                        content=fake.text(max_nb_chars=300),
                        is_solution=random.choice([True, False, False, False])
                    )

        # --- 18. MESSAGES ---
        self.stdout.write("✉️ Creating messages...")
        for _ in range(30):
            sender = random.choice(all_users)
            recipient = random.choice(all_users)
            if sender != recipient:
                Message.objects.create(
                    sender=sender,
                    recipient=recipient,
                    subject=fake.sentence(),
                    body=fake.text(max_nb_chars=400),
                    is_read=random.choice([True, False]),
                    read_at=timezone.now() - timedelta(hours=random.randint(1, 48)) if random.choice([True, False]) else None
                )

        # --- 19. SUPPORT TICKETS ---
        self.stdout.write("🎫 Creating support tickets...")
        for _ in range(20):
            ticket = SupportTicket.objects.create(
                ticket_id=f"TKT-{random.randint(10000, 99999)}",
                user=random.choice(users['students']),
                category=random.choice(['technical', 'account', 'course', 'payment', 'other']),
                subject=fake.sentence(),
                description=fake.text(max_nb_chars=500),
                priority=random.choice(['low', 'normal', 'high', 'urgent']),
                status=random.choice(['open', 'in_progress', 'waiting_response', 'resolved', 'closed']),
                assigned_to=random.choice(users['support']) if random.choice([True, False]) else None,
                resolved_at=timezone.now() - timedelta(days=random.randint(1, 30)) if random.choice([True, False]) else None
            )
            
            # Add ticket replies
            for _ in range(random.randint(1, 5)):
                TicketReply.objects.create(
                    ticket=ticket,
                    author=random.choice([ticket.user, ticket.assigned_to] if ticket.assigned_to else [ticket.user]),
                    message=fake.text(max_nb_chars=300),
                    is_internal_note=random.choice([True, False, False])
                )

        # --- 20. NOTIFICATIONS ---
        self.stdout.write("🔔 Creating notifications...")
        for user in random.sample(all_users, k=30):
            for _ in range(random.randint(3, 10)):
                Notification.objects.create(
                    user=user,
                    notification_type=random.choice(['enrollment', 'assignment', 'grade', 'announcement', 'message', 'certificate', 'system']),
                    title=fake.sentence(),
                    message=fake.text(max_nb_chars=200),
                    link=f"/courses/{random.randint(1, 10)}" if random.choice([True, False]) else '',
                    is_read=random.choice([True, False]),
                    read_at=timezone.now() - timedelta(hours=random.randint(1, 72)) if random.choice([True, False]) else None
                )

        # --- 21. ANNOUNCEMENTS ---
        self.stdout.write("📢 Creating announcements...")
        for _ in range(15):
            ann_type = random.choice(['system', 'course', 'category'])
            Announcement.objects.create(
                title=fake.sentence(),
                content=fake.text(max_nb_chars=500),
                announcement_type=ann_type,
                priority=random.choice(['low', 'normal', 'high', 'urgent']),
                course=random.choice(lms_courses) if ann_type == 'course' else None,
                category=random.choice(categories) if ann_type == 'category' else None,
                created_by=random.choice(users['admins'] + users['instructors']),
                is_active=random.choice([True, True, True, False]),
                publish_date=timezone.now() - timedelta(days=random.randint(1, 60)),
                expiry_date=timezone.now() + timedelta(days=random.randint(30, 90)) if random.choice([True, False]) else None
            )

        # --- 22. CONTACT MESSAGES ---
        self.stdout.write("📧 Creating contact messages...")
        for _ in range(15):
            ContactMessage.objects.create(
                user=random.choice(users['students']) if random.choice([True, False]) else None,
                name=fake.name(),
                email=fake.email(),
                subject=random.choice(['admissions', 'programs', 'campus', 'financial', 'support', 'other']),
                message=fake.text(max_nb_chars=500),
                is_read=random.choice([True, False]),
                responded=random.choice([True, False, False]),
                responded_by=random.choice(users['support']) if random.choice([True, False]) else None,
                responded_at=timezone.now() - timedelta(days=random.randint(1, 30)) if random.choice([True, False]) else None,
                created_at=timezone.now() - timedelta(days=random.randint(1, 90))
            )

        # --- 23. AUDIT LOGS ---
        self.stdout.write("📋 Creating audit logs...")
        for _ in range(50):
            AuditLog.objects.create(
                user=random.choice(all_users),
                action=random.choice(['create', 'update', 'delete', 'login', 'logout', 'access', 'export', 'permission_change']),
                model_name=random.choice(['Course', 'User', 'Enrollment', 'Assignment', 'Payment']),
                object_id=str(random.randint(1, 100)),
                description=fake.sentence(),
                ip_address=fake.ipv4(),
                user_agent=fake.user_agent(),
                extra_data={'browser': fake.user_agent(), 'platform': random.choice(['Windows', 'Mac', 'Linux'])}
            )

        # --- UPDATE STATISTICS ---
        self.stdout.write("📊 Updating course statistics...")
        for course in lms_courses:
            course.update_statistics()

        self.stdout.write(self.style.SUCCESS("✅ SUCCESS: Comprehensive database seeding completed!"))
        self.stdout.write(self.style.SUCCESS(f"📈 Created:"))
        self.stdout.write(f"   - {len(all_users)} Users across all roles")
        self.stdout.write(f"   - {len(faculties)} Faculties")
        self.stdout.write(f"   - {len(academic_courses)} Academic Courses")
        self.stdout.write(f"   - {CourseApplication.objects.count()} Course Applications")
        self.stdout.write(f"   - {len(categories)} LMS Course Categories")
        self.stdout.write(f"   - {len(lms_courses)} LMS Courses")
        self.stdout.write(f"   - {Lesson.objects.count()} Lessons")
        self.stdout.write(f"   - {Assignment.objects.count()} Assignments")
        self.stdout.write(f"   - {Quiz.objects.count()} Quizzes")
        self.stdout.write(f"   - {Enrollment.objects.count()} Enrollments")
        self.stdout.write(f"   - {Review.objects.count()} Reviews")
        self.stdout.write(f"   - {Transaction.objects.count()} Transactions")
        self.stdout.write(f"   - {BlogPost.objects.count()} Blog Posts")
        self.stdout.write(f"   - {Discussion.objects.count()} Discussions")
        self.stdout.write(f"   - {SupportTicket.objects.count()} Support Tickets")
        self.stdout.write(f"   - {Notification.objects.count()} Notifications")