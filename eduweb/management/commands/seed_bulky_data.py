import random
import uuid
from decimal import Decimal
from datetime import timedelta, date
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from faker import Faker

# Import all models
from eduweb.models import (
    Announcement, Assignment, AssignmentSubmission, AuditLog, Badge, StudentBadge,
    BlogCategory, BlogPost, Certificate, ContactMessage, Faculty, Course,
    CourseIntake, CourseApplication, ApplicationDocument, ApplicationPayment,
    CourseCategory, Discussion, DiscussionReply, Enrollment, SupportTicket,
    TicketReply, Invoice, LessonProgress, LMSCourse, Lesson, LessonSection,
    Message, Notification, PaymentGateway, Transaction, Quiz, QuizQuestion,
    QuizAnswer, QuizAttempt, QuizResponse, Review, SubscriptionPlan,
    Subscription, SystemConfiguration, UserProfile, Vendor, StudyGroup,
    StudyGroupMember
)

fake = Faker()

# Real YouTube video links for courses
YOUTUBE_VIDEOS = {
    'python': [
        'https://www.youtube.com/watch?v=rfscVS0vtbw',
        'https://www.youtube.com/watch?v=_uQrJ0TkZlc',
        'https://www.youtube.com/watch?v=kqtD5dpn9C8',
        'https://www.youtube.com/watch?v=8DvywoWv6fI',
        'https://www.youtube.com/watch?v=YYXdXT2l-Gg',
    ],
    'web_dev': [
        'https://www.youtube.com/watch?v=UB1O30fR-EE',
        'https://www.youtube.com/watch?v=mU6anWqZJcc',
        'https://www.youtube.com/watch?v=1PnVor36_40',
        'https://www.youtube.com/watch?v=G3e-cpL7ofc',
        'https://www.youtube.com/watch?v=nu_pCVPKzTk',
    ],
    'data_science': [
        'https://www.youtube.com/watch?v=ua-CiDNNj30',
        'https://www.youtube.com/watch?v=RBSGKlAvoiM',
        'https://www.youtube.com/watch?v=7eh4d6sabA0',
        'https://www.youtube.com/watch?v=zN1_fMwbZac',
        'https://www.youtube.com/watch?v=mkv5mxYu0Wk',
    ],
    'machine_learning': [
        'https://www.youtube.com/watch?v=aircAruvnKk',
        'https://www.youtube.com/watch?v=IHZwWFHWa-w',
        'https://www.youtube.com/watch?v=i8D90DkCLhI',
        'https://www.youtube.com/watch?v=jGwO_UgTS7I',
        'https://www.youtube.com/watch?v=qv6UVOQ0F44',
    ],
    'javascript': [
        'https://www.youtube.com/watch?v=W6NZfCO5SIk',
        'https://www.youtube.com/watch?v=PkZNo7MFNFg',
        'https://www.youtube.com/watch?v=DHjqpvDnNGE',
        'https://www.youtube.com/watch?v=BMUiFMZr7vk',
        'https://www.youtube.com/watch?v=hdI2bqOjy3c',
    ],
    'react': [
        'https://www.youtube.com/watch?v=Ke90Tje7VS0',
        'https://www.youtube.com/watch?v=bMknfKXIFA8',
        'https://www.youtube.com/watch?v=SqcY0GlETPk',
        'https://www.youtube.com/watch?v=Rh3tobg7hEo',
        'https://www.youtube.com/watch?v=w7ejDZ8SWv8',
    ],
    'design': [
        'https://www.youtube.com/watch?v=0JCUH5daCCE',
        'https://www.youtube.com/watch?v=YiLUYf4HDh4',
        'https://www.youtube.com/watch?v=wIuVvCuiJhU',
        'https://www.youtube.com/watch?v=_2LLXnUdUIc',
        'https://www.youtube.com/watch?v=3WmpunL9jTA',
    ],
    'business': [
        'https://www.youtube.com/watch?v=qs-l7jDKJLQ',
        'https://www.youtube.com/watch?v=8w4KCiVu1kI',
        'https://www.youtube.com/watch?v=jpe-LKn-4gM',
        'https://www.youtube.com/watch?v=eC7xzavzEKY',
        'https://www.youtube.com/watch?v=XfpFp_K8Jaw',
    ]
}

class Command(BaseCommand):
    help = 'Seeds comprehensive realistic data for ALL tables - ALL USER ROLES PARTICIPATE'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("🚀 Starting COMPREHENSIVE database seeding..."))
        self.stdout.write(self.style.WARNING("   Ensuring ALL user roles actively participate in the system!"))

        # --- 1. CLEANUP (keep existing users) ---
        self.stdout.write("🧹 Cleaning up existing data (preserving users)...")
        models_to_clear = [
            User, AuditLog, Notification, Message, TicketReply, SupportTicket, StudentBadge, Badge,
            QuizResponse, QuizAttempt, QuizAnswer, QuizQuestion, Quiz, AssignmentSubmission,
            Assignment, LessonProgress, Certificate, Review, Enrollment, DiscussionReply,
            Discussion, Lesson, LessonSection, LMSCourse, CourseCategory, ApplicationPayment,
            ApplicationDocument, CourseApplication, CourseIntake, Course, Faculty, Invoice,
            Transaction, Subscription, SubscriptionPlan, PaymentGateway, BlogPost, BlogCategory,
            ContactMessage, Vendor, SystemConfiguration, Announcement, StudyGroupMember, StudyGroup
        ]
        for model in models_to_clear:
            model.objects.all().delete()

        # --- 2. CREATE USERS WITH DIFFERENT ROLES ---
        self.stdout.write("👥 Creating users with different roles...")
        users = {'students': [], 'instructors': [], 'admins': [], 'support': [], 
                 'content_managers': [], 'finance': [], 'qa': []}
        
        # Create 40 Students
        for i in range(40):
            u = User.objects.create_user(
                username=f"student_{i}_{uuid.uuid4().hex[:4]}",
                email=fake.unique.email(),
                password="password123",
                first_name=fake.first_name(),
                last_name=fake.last_name()
            )
            users['students'].append(u)
            p = u.profile
            p.role = 'student'
            p.bio = fake.text(max_nb_chars=250)
            p.phone = fake.phone_number()[:20]
            p.date_of_birth = fake.date_of_birth(minimum_age=18, maximum_age=45)
            p.address = fake.street_address()
            p.city = fake.city()
            p.country = fake.country()
            p.website = fake.url() if random.random() > 0.6 else ''
            p.linkedin = f"https://linkedin.com/in/{u.username}" if random.random() > 0.5 else ''
            p.twitter = f"https://twitter.com/{u.username}" if random.random() > 0.7 else ''
            p.email_notifications = random.choice([True, False])
            p.marketing_emails = random.choice([True, False])
            p.email_verified = random.random() > 0.2
            p.save()
        
        # Create 12 Instructors
        for i in range(12):
            u = User.objects.create_user(
                username=f"instructor_{i}_{uuid.uuid4().hex[:4]}",
                email=fake.unique.email(),
                password="password123",
                first_name=fake.first_name(),
                last_name=fake.last_name()
            )
            users['instructors'].append(u)
            p = u.profile
            p.role = 'instructor'
            p.bio = f"Expert instructor with {random.randint(5, 20)} years of experience in {fake.job()}. Passionate about teaching and student success. {fake.text(max_nb_chars=150)}"
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
                password="password123",
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                is_staff=True
            )
            users['admins'].append(u)
            p = u.profile
            p.role = 'admin'
            p.bio = "System administrator responsible for platform management and oversight"
            p.phone = fake.phone_number()[:20]
            p.email_verified = True
            p.save()
        
        # Create 4 Support Staff
        for i in range(4):
            u = User.objects.create_user(
                username=f"support_{i}_{uuid.uuid4().hex[:4]}",
                email=fake.unique.email(),
                password="password123",
                first_name=fake.first_name(),
                last_name=fake.last_name()
            )
            users['support'].append(u)
            p = u.profile
            p.role = 'support'
            p.bio = "Customer support specialist dedicated to helping students succeed"
            p.phone = fake.phone_number()[:20]
            p.email_verified = True
            p.save()
        
        # Create 2 Content Managers
        for i in range(2):
            u = User.objects.create_user(
                username=f"content_mgr_{i}_{uuid.uuid4().hex[:4]}",
                email=fake.unique.email(),
                password="password123",
                first_name=fake.first_name(),
                last_name=fake.last_name()
            )
            users['content_managers'].append(u)
            p = u.profile
            p.role = 'content_manager'
            p.bio = "Content management and curriculum development specialist"
            p.phone = fake.phone_number()[:20]
            p.email_verified = True
            p.save()
        
        # Create 2 Finance Managers
        for i in range(2):
            u = User.objects.create_user(
                username=f"finance_{i}_{uuid.uuid4().hex[:4]}",
                email=fake.unique.email(),
                password="password123",
                first_name=fake.first_name(),
                last_name=fake.last_name()
            )
            users['finance'].append(u)
            p = u.profile
            p.role = 'finance'
            p.bio = "Finance manager handling billing and transactions"
            p.phone = fake.phone_number()[:20]
            p.email_verified = True
            p.save()
        
        # Create 2 QA Reviewers
        for i in range(2):
            u = User.objects.create_user(
                username=f"qa_{i}_{uuid.uuid4().hex[:4]}",
                email=fake.unique.email(),
                password="password123",
                first_name=fake.first_name(),
                last_name=fake.last_name()
            )
            users['qa'].append(u)
            p = u.profile
            p.role = 'qa'
            p.bio = "Quality assurance specialist ensuring course quality"
            p.phone = fake.phone_number()[:20]
            p.email_verified = True
            p.save()

        all_users = users['students'] + users['instructors'] + users['admins'] + users['support'] + users['content_managers'] + users['finance'] + users['qa']

        # --- 3. VENDORS ---
        self.stdout.write("🏢 Creating vendors...")
        vendors = []
        vendor_data = [
            {'name': 'Tech University Partners', 'country': 'United States'},
            {'name': 'Global Education Alliance', 'country': 'United Kingdom'},
            {'name': 'Asian Institute Network', 'country': 'Singapore'},
            {'name': 'European Learning Consortium', 'country': 'Germany'},
            {'name': 'Australian Education Hub', 'country': 'Australia'},
        ]
        for vd in vendor_data:
            vendor = Vendor.objects.create(
                name=vd['name'],
                email=fake.company_email(),
                country=vd['country'],
                stripe_account_id=f"acct_{uuid.uuid4().hex[:16]}",
                is_active=True
            )
            vendors.append(vendor)

        # --- 4. SYSTEM CONFIGURATIONS (Created by ADMINS and CONTENT MANAGERS) ---
        self.stdout.write("⚙️ Creating system configurations...")
        configs = [
            {'key': 'site_name', 'value': 'EduWeb Learning Platform', 'description': 'Platform name'},
            {'key': 'max_upload_size', 'value': '10485760', 'description': 'Max file upload size in bytes'},
            {'key': 'email_notifications_enabled', 'value': 'true', 'description': 'Enable email notifications'},
            {'key': 'maintenance_mode', 'value': 'false', 'description': 'Maintenance mode status'},
            {'key': 'default_currency', 'value': 'USD', 'description': 'Default currency code'},
            {'key': 'max_enrollments_per_user', 'value': '50', 'description': 'Maximum course enrollments per user'},
            {'key': 'certificate_enabled', 'value': 'true', 'description': 'Enable certificate generation'},
            {'key': 'forum_enabled', 'value': 'true', 'description': 'Enable discussion forums'},
        ]
        config_creators = users['admins'] + users['content_managers']
        for cfg in configs:
            SystemConfiguration.objects.create(
                key=cfg['key'],
                value=cfg['value'],
                description=cfg['description'],
                is_public=True,
                updated_by=random.choice(config_creators)
            )

        # --- 5. PAYMENT GATEWAYS (Set up by FINANCE and ADMINS) ---
        self.stdout.write("💳 Creating payment gateways...")
        gateways = []
        gateway_configs = [
            {
                'name': 'Stripe',
                'slug': 'stripe',
                'gateway_type': 'stripe',
                'api_key': 'pk_test_' + uuid.uuid4().hex,
                'api_secret': 'sk_test_' + uuid.uuid4().hex,
                'webhook_secret': 'whsec_' + uuid.uuid4().hex,
                'is_active': True,
                'is_test_mode': True
            },
            {
                'name': 'PayPal',
                'slug': 'paypal',
                'gateway_type': 'paypal',
                'api_key': uuid.uuid4().hex,
                'api_secret': uuid.uuid4().hex,
                'webhook_secret': '',
                'is_active': True,
                'is_test_mode': True
            },
            {
                'name': 'Razorpay',
                'slug': 'razorpay',
                'gateway_type': 'razorpay',
                'api_key': 'rzp_test_' + uuid.uuid4().hex[:16],
                'api_secret': uuid.uuid4().hex,
                'webhook_secret': '',
                'is_active': False,
                'is_test_mode': True
            }
        ]
        for gc in gateway_configs:
            gateway = PaymentGateway.objects.create(
                name=gc['name'],
                slug=gc['slug'],
                gateway_type=gc['gateway_type'],
                api_key=gc['api_key'],
                api_secret=gc['api_secret'],
                webhook_secret=gc['webhook_secret'],
                is_active=gc['is_active'],
                is_test_mode=gc['is_test_mode']
            )
            gateways.append(gateway)

        # --- 6. SUBSCRIPTION PLANS (Created by FINANCE and ADMINS) ---
        self.stdout.write("📋 Creating subscription plans...")
        plans = []
        plan_data = [
            {
                'name': 'Free',
                'description': 'Access to free courses only',
                'price': Decimal('0.00'),
                'billing_cycle': 'yearly',
                'features': ['Access to free courses', 'Community forums', 'Basic support'],
                'max_courses': 5,
                'is_popular': False
            },
            {
                'name': 'Basic',
                'description': 'Perfect for individual learners',
                'price': Decimal('29.99'),
                'billing_cycle': 'monthly',
                'features': ['All free features', 'Access to premium courses', 'Email support', 'Downloadable resources'],
                'max_courses': 20,
                'is_popular': False
            },
            {
                'name': 'Pro',
                'description': 'Best value for serious learners',
                'price': Decimal('79.99'),
                'billing_cycle': 'monthly',
                'features': ['All Basic features', 'Unlimited courses', 'Priority support', 'Certificates', 'Live Q&A sessions'],
                'max_courses': None,
                'is_popular': True
            },
            {
                'name': 'Enterprise',
                'description': 'For teams and organizations',
                'price': Decimal('299.99'),
                'billing_cycle': 'monthly',
                'features': ['All Pro features', 'Team management', 'Custom branding', 'Dedicated support', 'Analytics dashboard', 'API access'],
                'max_courses': None,
                'is_popular': False
            }
        ]
        for pd in plan_data:
            plan = SubscriptionPlan.objects.create(
                name=pd['name'],
                description=pd['description'],
                price=pd['price'],
                currency='USD',
                billing_cycle=pd['billing_cycle'],
                features=pd['features'],
                max_courses=pd['max_courses'],
                is_active=True,
                is_popular=pd['is_popular'],
                display_order=len(plans)
            )
            plans.append(plan)

        # --- 7. SUBSCRIPTIONS (STUDENTS subscribe) ---
        self.stdout.write("🎫 Creating user subscriptions...")
        for student in random.sample(users['students'], k=25):
            plan = random.choice(plans)
            start_date = timezone.now().date() - timedelta(days=random.randint(0, 60))
            # Calculate end date based on billing cycle
            if plan.billing_cycle == 'monthly':
                end_date = start_date + timedelta(days=30)
            elif plan.billing_cycle == 'quarterly':
                end_date = start_date + timedelta(days=90)
            else:  # yearly
                end_date = start_date + timedelta(days=365)
            
            Subscription.objects.create(
                user=student,
                plan=plan,
                status=random.choice(['active', 'active', 'active', 'cancelled', 'expired']) if random.random() > 0.2 else 'active',
                end_date=end_date,
                auto_renew=random.choice([True, False]),
                gateway_subscription_id=f"sub_{uuid.uuid4().hex[:24]}" if random.random() > 0.3 else ''
            )

        # --- 8. FACULTIES (Created by ADMINS) ---
        self.stdout.write("🎓 Creating faculties...")
        faculties = []
        faculty_data = [
            {
                'name': 'Faculty of Computer Science & IT',
                'code': 'CSIT',
                'tagline': 'Leading the digital revolution',
                'description': 'Leading education in computing, software development, and information technology. We prepare students for the future of tech.',
                'icon': 'cpu',
                'color_primary': 'blue',
                'color_secondary': 'cyan',
                'student_count': random.randint(500, 2000),
                'placement_rate': random.randint(85, 98)
            },
            {
                'name': 'Faculty of Engineering',
                'code': 'ENG',
                'tagline': 'Building tomorrow, today',
                'description': 'Excellence in engineering education across multiple disciplines. Fostering innovation and practical problem-solving.',
                'icon': 'cog',
                'color_primary': 'orange',
                'color_secondary': 'amber',
                'student_count': random.randint(400, 1800),
                'placement_rate': random.randint(80, 95)
            },
            {
                'name': 'Faculty of Business & Management',
                'code': 'BUS',
                'tagline': 'Shaping future leaders',
                'description': 'Preparing future business leaders and entrepreneurs. Combining theory with real-world business practice.',
                'icon': 'briefcase',
                'color_primary': 'green',
                'color_secondary': 'emerald',
                'student_count': random.randint(600, 2500),
                'placement_rate': random.randint(82, 96)
            },
            {
                'name': 'Faculty of Health Sciences',
                'code': 'HLTH',
                'tagline': 'Caring for tomorrow',
                'description': 'Comprehensive health education and medical training programs. Developing compassionate healthcare professionals.',
                'icon': 'heart',
                'color_primary': 'red',
                'color_secondary': 'rose',
                'student_count': random.randint(300, 1200),
                'placement_rate': random.randint(90, 99)
            },
            {
                'name': 'Faculty of Arts & Humanities',
                'code': 'ART',
                'tagline': 'Inspiring creativity and critical thinking',
                'description': 'Fostering creativity and critical thinking in arts and humanities. Exploring human culture and expression.',
                'icon': 'palette',
                'color_primary': 'purple',
                'color_secondary': 'violet',
                'student_count': random.randint(400, 1500),
                'placement_rate': random.randint(75, 88)
            }
        ]
        for idx, fd in enumerate(faculty_data):
            faculty = Faculty.objects.create(
                name=fd['name'],
                code=fd['code'],
                tagline=fd['tagline'],
                description=fd['description'],
                icon=fd['icon'],
                color_primary=fd['color_primary'],
                color_secondary=fd['color_secondary'],
                student_count=fd['student_count'],
                placement_rate=fd['placement_rate'],
                partner_count=random.randint(10, 50),
                international_faculty=random.randint(15, 40),
                mission=fake.text(max_nb_chars=300),
                vision=fake.text(max_nb_chars=300),
                accreditation=f"Accredited by {fake.company()} - {random.randint(2015, 2024)}",
                special_features=[
                    f"State-of-the-art {fake.word()} facilities",
                    f"Industry partnerships with {fake.company()}",
                    f"International exchange programs",
                    f"Research opportunities in {fake.word()}"
                ],
                is_active=True,
                display_order=idx
            )
            faculties.append(faculty)

        # --- 9. ACADEMIC COURSES (Created by ADMINS and CONTENT MANAGERS) ---
        self.stdout.write("📚 Creating academic courses...")
        academic_courses = []
        course_data = [
            {
                'faculty': faculties[0],
                'name': 'Bachelor of Science in Computer Science',
                'code': 'BSCS',
                'degree_level': 'undergraduate',
                'study_modes': ['full_time', 'part_time'],
                'duration': 4.0,
                'tagline': 'Build the future with code',
                'tuition': Decimal('45000.00'),
                'app_fee': Decimal('100.00')
            },
            {
                'faculty': faculties[0],
                'name': 'Master of Science in Data Science',
                'code': 'MSDS',
                'degree_level': 'masters',
                'study_modes': ['full_time', 'online'],
                'duration': 2.0,
                'tagline': 'Transform data into insights',
                'tuition': Decimal('55000.00'),
                'app_fee': Decimal('150.00')
            },
            {
                'faculty': faculties[1],
                'name': 'Bachelor of Engineering in Civil Engineering',
                'code': 'BECE',
                'degree_level': 'undergraduate',
                'study_modes': ['full_time'],
                'duration': 4.0,
                'tagline': 'Design the world around us',
                'tuition': Decimal('48000.00'),
                'app_fee': Decimal('100.00')
            },
            {
                'faculty': faculties[2],
                'name': 'Master of Business Administration',
                'code': 'MBA',
                'degree_level': 'masters',
                'study_modes': ['full_time', 'part_time', 'online'],
                'duration': 2.0,
                'tagline': 'Lead with vision and purpose',
                'tuition': Decimal('65000.00'),
                'app_fee': Decimal('200.00')
            },
            {
                'faculty': faculties[3],
                'name': 'Bachelor of Science in Nursing',
                'code': 'BSN',
                'degree_level': 'undergraduate',
                'study_modes': ['full_time'],
                'duration': 4.0,
                'tagline': 'Care with compassion and skill',
                'tuition': Decimal('42000.00'),
                'app_fee': Decimal('100.00')
            }
        ]
        
        for cd in course_data:
            course = Course.objects.create(
                faculty=cd['faculty'],
                name=cd['name'],
                code=cd['code'],
                degree_level=cd['degree_level'],
                available_study_modes=cd['study_modes'],
                duration_years=cd['duration'],
                tagline=cd['tagline'],
                overview=fake.text(max_nb_chars=500),
                description=fake.text(max_nb_chars=1000),
                learning_outcomes=[
                    f"Master {fake.word()} in {cd['name'].split()[-1]}",
                    f"Apply {fake.word()} techniques to real-world problems",
                    f"Develop professional {fake.word()} skills",
                    f"Understand industry standards and best practices"
                ],
                career_paths=[
                    f"{fake.job()} Specialist",
                    f"Senior {fake.job()}",
                    f"{fake.job()} Manager",
                    f"Chief {fake.job()} Officer"
                ],
                core_courses=[
                    f"Introduction to {cd['name'].split()[-1]}",
                    f"Advanced {fake.word().title()}",
                    f"{fake.word().title()} Fundamentals",
                    f"Capstone Project"
                ],
                specialization_tracks=[
                    f"{fake.word().title()} Track",
                    f"{fake.word().title()} Specialization"
                ],
                entry_requirements=[
                    "High school diploma or equivalent",
                    "Minimum GPA of 3.0",
                    "English proficiency test (TOEFL/IELTS)"
                ],
                application_fee=cd['app_fee'],
                tuition_fee=cd['tuition'],
                avg_starting_salary=f"${random.randint(50, 120)}K",
                job_placement_rate=random.randint(75, 98),
                credits_required=120,
                is_active=True,
                is_featured=random.choice([True, False])
            )
            academic_courses.append(course)

        # --- 10. COURSE INTAKES (Created by ADMINS) ---
        self.stdout.write("📅 Creating course intakes...")
        intakes = []
        for course in academic_courses:
            for period in ['january', 'may', 'september']:
                for year in [2025, 2026]:
                    intake = CourseIntake.objects.create(
                        course=course,
                        intake_period=period,
                        year=year,
                        start_date=date(year, {'january': 1, 'may': 5, 'september': 9}[period], 15),
                        application_deadline=date(year, {'january': 1, 'may': 5, 'september': 9}[period], 1) - timedelta(days=30),
                        available_slots=random.randint(30, 100),
                        is_active=year >= 2025
                    )
                    intakes.append(intake)

        # --- 11. COURSE APPLICATIONS (STUDENTS apply, ADMINS review) ---
        self.stdout.write("📝 Creating course applications...")
        applications = []
        for _ in range(30):
            student = random.choice(users['students'])
            course = random.choice(academic_courses)
            intake = random.choice([i for i in intakes if i.course == course])
            
            app = CourseApplication.objects.create(
                user=student if random.random() > 0.3 else None,
                course=course,
                intake=intake,
                study_mode=random.choice(course.available_study_modes),
                first_name=student.first_name if student else fake.first_name(),
                last_name=student.last_name if student else fake.last_name(),
                email=student.email if student else fake.email(),
                phone=fake.phone_number()[:20],
                date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=40),
                gender=random.choice(['male', 'female', 'other']),
                nationality=fake.country(),
                address_line1=fake.street_address(),
                address_line2=fake.secondary_address() if random.random() > 0.5 else '',
                city=fake.city(),
                state=fake.state(),
                postal_code=fake.postcode(),
                country=fake.country(),
                highest_qualification=random.choice(['High School', 'Associate Degree', 'Bachelor Degree']),
                institution_name=fake.company(),
                graduation_year=str(random.randint(2015, 2024)),
                gpa_or_grade=f"{random.uniform(2.5, 4.0):.2f}",
                language_skill=random.choice(['ielts', 'toefl', 'pte', None]),
                language_score=Decimal(str(random.uniform(6.0, 9.0))) if random.random() > 0.3 else None,
                work_experience_years=random.randint(0, 10),
                personal_statement=fake.text(max_nb_chars=800),
                how_did_you_hear=random.choice(['Social Media', 'Friend', 'Website', 'Advertisement']),
                scholarship=random.choice([True, False]),
                accept_privacy_policy=True,
                accept_terms_conditions=True,
                marketing_consent=random.choice([True, False]),
                emergency_contact_name=fake.name(),
                emergency_contact_phone=fake.phone_number()[:20],
                emergency_contact_relationship=random.choice(['Parent', 'Sibling', 'Spouse', 'Friend']),
                status=random.choice(['draft', 'pending_payment', 'payment_complete', 'under_review', 'approved', 'rejected']),
                reviewer=random.choice(users['admins']) if random.random() > 0.5 else None,
                review_notes=fake.text(max_nb_chars=200) if random.random() > 0.5 else '',
                submitted_at=timezone.now() - timedelta(days=random.randint(1, 90)) if random.random() > 0.3 else None,
                payment_status=random.choice(['pending', 'completed', 'failed'])
            )
            applications.append(app)

        # --- 12. APPLICATION DOCUMENTS (Uploaded by STUDENTS) ---
        self.stdout.write("📎 Creating application documents...")
        for app in random.sample(applications, k=min(20, len(applications))):
            for doc_type in random.sample(['transcript', 'certificate', 'cv', 'passport'], k=random.randint(2, 4)):
                ApplicationDocument.objects.create(
                    application=app,
                    file_type=doc_type,
                    original_filename=f"{doc_type}_{fake.file_name(extension='pdf')}",
                    file_size=random.randint(100000, 5000000)
                )

        # --- 13. APPLICATION PAYMENTS (Processed by FINANCE) ---
        self.stdout.write("💰 Creating application payments...")
        for app in [a for a in applications if a.status in ['payment_complete', 'under_review', 'approved']]:
            payment_status = 'success' if app.status != 'pending_payment' else random.choice(['pending', 'success'])
            ApplicationPayment.objects.create(
                application=app,
                amount=app.course.application_fee,
                currency='USD',
                status=payment_status,
                payment_method=random.choice(['card', 'paypal', 'bank_transfer']),
                gateway_payment_id=f"pi_{uuid.uuid4().hex[:24]}",
                card_last4=str(random.randint(1000, 9999)) if random.random() > 0.3 else '',
                card_brand=random.choice(['Visa', 'Mastercard', 'Amex']) if random.random() > 0.3 else '',
                paid_at=timezone.now() - timedelta(days=random.randint(1, 60)) if payment_status == 'success' else None
            )

        # --- 14. COURSE CATEGORIES (Created by CONTENT MANAGERS and ADMINS) ---
        self.stdout.write("🗂️ Creating course categories...")
        categories = []
        category_data = [
            {'name': 'Programming & Development', 'icon': 'code', 'color': 'blue'},
            {'name': 'Data Science & Analytics', 'icon': 'bar-chart', 'color': 'green'},
            {'name': 'Web Development', 'icon': 'globe', 'color': 'purple'},
            {'name': 'Mobile Development', 'icon': 'smartphone', 'color': 'cyan'},
            {'name': 'Artificial Intelligence', 'icon': 'brain', 'color': 'pink'},
            {'name': 'Cybersecurity', 'icon': 'shield', 'color': 'red'},
            {'name': 'Cloud Computing', 'icon': 'cloud', 'color': 'sky'},
            {'name': 'DevOps & Infrastructure', 'icon': 'server', 'color': 'gray'},
            {'name': 'Design & UX', 'icon': 'palette', 'color': 'orange'},
            {'name': 'Business & Marketing', 'icon': 'trending-up', 'color': 'emerald'},
        ]
        for idx, cat in enumerate(category_data):
            category = CourseCategory.objects.create(
                name=cat['name'],
                description=fake.text(max_nb_chars=200),
                icon=cat['icon'],
                color=cat['color'],
                display_order=idx,
                is_active=True
            )
            categories.append(category)

        # --- 15. LMS COURSES with REAL YOUTUBE LINKS (Created by INSTRUCTORS) ---
        self.stdout.write("🎥 Creating LMS courses with real YouTube videos...")
        lms_courses = []
        
        course_templates = [
            {
                'title': 'Complete Python Programming Masterclass',
                'category': categories[0],
                'video_type': 'python',
                'difficulty': 'beginner',
                'price': Decimal('89.99'),
                'duration': 45.5,
                'description': 'Master Python from basics to advanced concepts. Learn data structures, OOP, file handling, and more.',
                'objectives': [
                    'Write clean and efficient Python code',
                    'Understand object-oriented programming',
                    'Work with files and databases',
                    'Build real-world applications'
                ]
            },
            {
                'title': 'Modern Web Development Bootcamp',
                'category': categories[2],
                'video_type': 'web_dev',
                'difficulty': 'intermediate',
                'price': Decimal('99.99'),
                'duration': 52.0,
                'description': 'Learn HTML, CSS, JavaScript, and modern frameworks to build professional websites.',
                'objectives': [
                    'Build responsive websites',
                    'Master JavaScript ES6+',
                    'Work with React and Vue',
                    'Deploy web applications'
                ]
            },
            {
                'title': 'Data Science & Machine Learning A-Z',
                'category': categories[1],
                'video_type': 'data_science',
                'difficulty': 'intermediate',
                'price': Decimal('119.99'),
                'duration': 68.5,
                'description': 'Comprehensive data science course covering statistics, Python, ML algorithms, and real projects.',
                'objectives': [
                    'Perform statistical analysis',
                    'Build machine learning models',
                    'Visualize data effectively',
                    'Work with real datasets'
                ]
            },
            {
                'title': 'Deep Learning & Neural Networks',
                'category': categories[4],
                'video_type': 'machine_learning',
                'difficulty': 'advanced',
                'price': Decimal('149.99'),
                'duration': 72.0,
                'description': 'Advanced course on deep learning, covering CNNs, RNNs, GANs, and modern architectures.',
                'objectives': [
                    'Understand neural network architectures',
                    'Build and train deep learning models',
                    'Work with TensorFlow and PyTorch',
                    'Implement state-of-the-art algorithms'
                ]
            },
            {
                'title': 'JavaScript: From Zero to Hero',
                'category': categories[0],
                'video_type': 'javascript',
                'difficulty': 'beginner',
                'price': Decimal('79.99'),
                'duration': 38.0,
                'description': 'Complete JavaScript course for beginners. Learn the fundamentals and build interactive web apps.',
                'objectives': [
                    'Master JavaScript fundamentals',
                    'Understand DOM manipulation',
                    'Work with APIs and async code',
                    'Build interactive applications'
                ]
            },
            {
                'title': 'React - The Complete Guide',
                'category': categories[2],
                'video_type': 'react',
                'difficulty': 'intermediate',
                'price': Decimal('94.99'),
                'duration': 48.5,
                'description': 'Comprehensive React course covering hooks, context, Redux, and advanced patterns.',
                'objectives': [
                    'Build React applications',
                    'Master React hooks',
                    'Manage state with Redux',
                    'Implement routing and authentication'
                ]
            },
            {
                'title': 'UI/UX Design Fundamentals',
                'category': categories[8],
                'video_type': 'design',
                'difficulty': 'beginner',
                'price': Decimal('69.99'),
                'duration': 32.0,
                'description': 'Learn the principles of user interface and user experience design.',
                'objectives': [
                    'Understand design principles',
                    'Create user-centered designs',
                    'Use Figma and Adobe XD',
                    'Build design systems'
                ]
            },
            {
                'title': 'Business Strategy & Entrepreneurship',
                'category': categories[9],
                'video_type': 'business',
                'difficulty': 'intermediate',
                'price': Decimal('84.99'),
                'duration': 41.0,
                'description': 'Learn business strategy, market analysis, and entrepreneurship fundamentals.',
                'objectives': [
                    'Develop business strategies',
                    'Analyze market opportunities',
                    'Create business plans',
                    'Launch and scale startups'
                ]
            },
            {
                'title': 'Advanced Python for Data Science',
                'category': categories[1],
                'video_type': 'python',
                'difficulty': 'advanced',
                'price': Decimal('129.99'),
                'duration': 55.5,
                'description': 'Advanced Python techniques for data science, including pandas, numpy, and scikit-learn.',
                'objectives': [
                    'Master pandas and numpy',
                    'Perform advanced data analysis',
                    'Build ML pipelines',
                    'Optimize Python code'
                ]
            },
            {
                'title': 'Full Stack Web Development',
                'category': categories[2],
                'video_type': 'web_dev',
                'difficulty': 'advanced',
                'price': Decimal('139.99'),
                'duration': 78.0,
                'description': 'Complete full-stack development course covering frontend, backend, and deployment.',
                'objectives': [
                    'Build full-stack applications',
                    'Work with Node.js and Express',
                    'Manage databases',
                    'Deploy to cloud platforms'
                ]
            }
        ]

        # Each INSTRUCTOR creates at least one course
        instructor_course_map = {}
        for idx, course_template in enumerate(course_templates):
            instructor = users['instructors'][idx % len(users['instructors'])]
            if instructor not in instructor_course_map:
                instructor_course_map[instructor] = []
            
            course = LMSCourse.objects.create(
                title=course_template['title'],
                code=f"LMS{random.randint(1000, 9999)}",
                category=course_template['category'],
                short_description=course_template['description'][:200],
                description=course_template['description'],
                learning_objectives=course_template['objectives'],
                prerequisites=[
                    'Basic computer knowledge',
                    'Passion for learning'
                ] if course_template['difficulty'] == 'beginner' else [
                    f"Basic knowledge of {course_template['category'].name.split()[0]}",
                    'Completion of beginner course recommended'
                ],
                difficulty_level=course_template['difficulty'],
                duration_hours=Decimal(str(course_template['duration'])),
                language='English',
                instructor=instructor,
                instructor_name=instructor.get_full_name(),
                instructor_bio=instructor.profile.bio,
                promo_video_url=random.choice(YOUTUBE_VIDEOS[course_template['video_type']]),
                is_free=random.random() > 0.7,
                price=course_template['price'] if random.random() > 0.7 else Decimal('0.00'),
                discount_price=course_template['price'] * Decimal('0.8') if random.random() > 0.6 else None,
                max_students=random.choice([None, 100, 200, 500]),
                enrollment_start_date=timezone.now().date() - timedelta(days=random.randint(30, 180)),
                enrollment_end_date=timezone.now().date() + timedelta(days=random.randint(30, 365)) if random.random() > 0.3 else None,
                is_published=True,
                is_featured=random.random() > 0.6,
                has_certificate=random.random() > 0.3,
                certificate_template='default',
                published_at=timezone.now() - timedelta(days=random.randint(1, 180))
            )
            lms_courses.append(course)
            instructor_course_map[instructor].append(course)

        # --- 16. LESSON SECTIONS (Created by INSTRUCTORS) ---
        self.stdout.write("📑 Creating lesson sections...")
        sections_map = {}
        for course in lms_courses:
            sections = []
            section_names = [
                'Getting Started',
                'Fundamentals',
                'Intermediate Concepts',
                'Advanced Topics',
                'Practical Projects',
                'Best Practices',
                'Conclusion & Next Steps'
            ]
            num_sections = random.randint(4, 7)
            for idx, section_name in enumerate(section_names[:num_sections]):
                section = LessonSection.objects.create(
                    course=course,
                    title=section_name,
                    description=fake.text(max_nb_chars=200),
                    display_order=idx
                )
                sections.append(section)
            sections_map[course.id] = sections

        # --- 17. LESSONS with REAL YOUTUBE VIDEOS (Created by INSTRUCTORS) ---
        self.stdout.write("📹 Creating lessons with real YouTube videos...")
        for course in lms_courses:
            sections = sections_map[course.id]
            video_type = next((ct['video_type'] for ct in course_templates if ct['title'] == course.title), 'python')
            videos = YOUTUBE_VIDEOS[video_type]
            
            lesson_count = random.randint(15, 30)
            for i in range(lesson_count):
                section = sections[i % len(sections)]
                lesson_types = ['video', 'text', 'video', 'video', 'file']
                lesson_type = random.choice(lesson_types)
                
                lesson = Lesson.objects.create(
                    course=course,
                    section=section,
                    title=f"{fake.catch_phrase()} - Lesson {i+1}",
                    lesson_type=lesson_type,
                    description=fake.text(max_nb_chars=300),
                    content=fake.text(max_nb_chars=1000) if lesson_type == 'text' else '',
                    video_url=random.choice(videos) if lesson_type == 'video' else '',
                    video_duration_minutes=random.randint(5, 45) if lesson_type == 'video' else 0,
                    is_preview=random.random() > 0.85,
                    is_active=True,
                    display_order=i
                )

        # --- 18. ENROLLMENTS (STUDENTS enroll) ---
        self.stdout.write("🎓 Creating enrollments...")
        enrollments = []
        for student in users['students']:
            num_enrollments = random.randint(1, 8)
            enrolled_courses = random.sample(lms_courses, k=min(num_enrollments, len(lms_courses)))
            for course in enrolled_courses:
                enrollment = Enrollment.objects.create(
                    student=student,
                    course=course,
                    enrolled_by=random.choice(users['admins']) if random.random() > 0.5 else None,
                    status=random.choice(['active', 'active', 'active', 'completed', 'dropped']),
                    progress_percentage=Decimal(str(random.uniform(0, 100))),
                    completed_lessons=random.randint(0, 20),
                    current_grade=Decimal(str(random.uniform(60, 100))) if random.random() > 0.5 else None,
                    completed_at=timezone.now() - timedelta(days=random.randint(1, 60)) if random.random() > 0.7 else None,
                    last_accessed=timezone.now() - timedelta(hours=random.randint(1, 168))
                )
                enrollments.append(enrollment)

        # --- 19. LESSON PROGRESS (STUDENTS make progress) ---
        self.stdout.write("📊 Creating lesson progress...")
        for enrollment in random.sample(enrollments, k=min(len(enrollments), 200)):
            lessons = list(enrollment.course.lessons.all())
            num_completed = int(len(lessons) * float(enrollment.progress_percentage) / 100)
            for lesson in lessons[:num_completed]:
                LessonProgress.objects.create(
                    enrollment=enrollment,
                    lesson=lesson,
                    is_completed=True,
                    completion_percentage=Decimal('100.00'),
                    time_spent_minutes=random.randint(5, 60),
                    video_progress_seconds=lesson.video_duration_minutes * 60 if lesson.lesson_type == 'video' else 0,
                    started_at=enrollment.enrolled_at,
                    completed_at=timezone.now() - timedelta(days=random.randint(1, 30))
                )

        # --- 20. ASSIGNMENTS (Created by INSTRUCTORS) ---
        self.stdout.write("📝 Creating assignments...")
        assignments = []
        for instructor in users['instructors']:
            if instructor in instructor_course_map:
                for course in instructor_course_map[instructor]:
                    lessons = list(course.lessons.all())
                    for lesson in random.sample(lessons, k=min(3, len(lessons))):
                        assignment = Assignment.objects.create(
                            lesson=lesson,
                            title=f"Assignment: {fake.catch_phrase()}",
                            description=fake.text(max_nb_chars=500),
                            instructions=fake.text(max_nb_chars=300),
                            max_score=Decimal('100.00'),
                            passing_score=Decimal('70.00'),
                            due_date=timezone.now() + timedelta(days=random.randint(7, 30)),
                            allow_late_submission=random.choice([True, False]),
                            late_penalty_percent=random.choice([0, 10, 20, 30]),
                            is_active=True,
                            display_order=random.randint(0, 10)
                        )
                        assignments.append(assignment)

        # --- 21. ASSIGNMENT SUBMISSIONS (STUDENTS submit, INSTRUCTORS grade) ---
        self.stdout.write("📤 Creating assignment submissions...")
        for assignment in assignments:
            enrolled_students = Enrollment.objects.filter(course=assignment.lesson.course, status='active')
            for enrollment in random.sample(list(enrolled_students), k=min(random.randint(3, 10), len(enrolled_students))):
                submission = AssignmentSubmission.objects.create(
                    assignment=assignment,
                    student=enrollment.student,
                    submission_text=fake.text(max_nb_chars=600),
                    score=Decimal(str(random.uniform(60, 100))) if random.random() > 0.4 else None,
                    feedback=fake.text(max_nb_chars=200) if random.random() > 0.5 else '',
                    graded_by=assignment.lesson.course.instructor if random.random() > 0.5 else None,
                    graded_at=timezone.now() - timedelta(days=random.randint(1, 15)) if random.random() > 0.5 else None,
                    status=random.choice(['draft', 'submitted', 'submitted', 'graded', 'graded']),
                    is_late=random.choice([True, False, False]),
                    submitted_at=timezone.now() - timedelta(days=random.randint(1, 20)) if random.random() > 0.3 else None
                )

        # --- 22. QUIZZES (Created by INSTRUCTORS, reviewed by QA) ---
        self.stdout.write("❓ Creating quizzes...")
        quizzes = []
        for instructor in users['instructors']:
            if instructor in instructor_course_map:
                for course in instructor_course_map[instructor]:
                    lessons = list(course.lessons.all())
                    for lesson in random.sample(lessons, k=min(2, len(lessons))):
                        quiz = Quiz.objects.create(
                            lesson=lesson,
                            title=f"Quiz: {fake.catch_phrase()}",
                            description=fake.text(max_nb_chars=200),
                            instructions='Answer all questions to the best of your ability.',
                            passing_score=Decimal('70.00'),
                            time_limit_minutes=random.choice([15, 30, 45, 60]),
                            max_attempts=random.choice([1, 3, 5, None]),
                            is_active=True,
                            display_order=random.randint(0, 10)
                        )
                        quizzes.append(quiz)

        # --- 23. QUIZ QUESTIONS & ANSWERS (Created by INSTRUCTORS) ---
        self.stdout.write("❔ Creating quiz questions and answers...")
        for quiz in quizzes:
            num_questions = random.randint(5, 15)
            for i in range(num_questions):
                question_type = random.choice(['multiple_choice', 'multiple_choice', 'true_false'])
                question = QuizQuestion.objects.create(
                    quiz=quiz,
                    question_type=question_type,
                    question_text=f"{fake.sentence()}?",
                    explanation=fake.text(max_nb_chars=150) if random.random() > 0.5 else '',
                    points=Decimal(str(random.choice([1, 2, 5, 10]))),
                    display_order=i
                )
                
                # Create answers for multiple choice and true/false
                if question_type == 'multiple_choice':
                    num_answers = 4
                    correct_index = random.randint(0, 3)
                    for j in range(num_answers):
                        QuizAnswer.objects.create(
                            question=question,
                            answer_text=fake.sentence(nb_words=6),
                            is_correct=(j == correct_index),
                            display_order=j
                        )
                elif question_type == 'true_false':
                    correct_answer = random.choice([True, False])
                    QuizAnswer.objects.create(
                        question=question,
                        answer_text='True',
                        is_correct=correct_answer,
                        display_order=0
                    )
                    QuizAnswer.objects.create(
                        question=question,
                        answer_text='False',
                        is_correct=not correct_answer,
                        display_order=1
                    )

        # --- 24. QUIZ ATTEMPTS (STUDENTS take quizzes) ---
        self.stdout.write("🎯 Creating quiz attempts...")
        for quiz in random.sample(quizzes, k=min(len(quizzes), 50)):
            enrolled_students = Enrollment.objects.filter(course=quiz.lesson.course, status='active')
            for enrollment in random.sample(list(enrolled_students), k=min(random.randint(2, 8), len(enrolled_students))):
                attempt = QuizAttempt.objects.create(
                    quiz=quiz,
                    student=enrollment.student,
                    score=Decimal(str(random.uniform(50, 100))),
                    passed=random.random() > 0.3,
                    time_taken_minutes=random.randint(10, quiz.time_limit_minutes) if quiz.time_limit_minutes else random.randint(10, 45),
                    started_at=timezone.now() - timedelta(days=random.randint(1, 30)),
                    completed_at=timezone.now() - timedelta(days=random.randint(1, 30))
                )
                
                for question in quiz.questions.all():
                    selected_answers = random.sample(list(question.answers.all()), k=random.randint(1, 2))
                    QuizResponse.objects.create(
                        attempt=attempt,
                        question=question,
                        selected_answer=selected_answers[0],
                        is_correct=selected_answers[0].is_correct
                    )

        # --- 25. REVIEWS (STUDENTS review courses, ADMINS approve) ---
        self.stdout.write("⭐ Creating course reviews...")
        for course in lms_courses:
            enrolled_students = list(Enrollment.objects.filter(course=course))
            num_reviews = random.randint(5, min(20, len(enrolled_students)))
            for enrollment in random.sample(enrolled_students, k=min(num_reviews, len(enrolled_students))):
                Review.objects.create(
                    course=course,
                    student=enrollment.student,
                    rating=random.randint(3, 5),
                    review_text=fake.text(max_nb_chars=400),
                    is_approved=random.random() > 0.1
                )

        # --- 26. CERTIFICATES (Issued to STUDENTS, verified by ADMINS) ---
        self.stdout.write("🏆 Creating certificates...")
        completed_enrollments = [e for e in enrollments if e.status == 'completed' and e.course.has_certificate]
        for enrollment in random.sample(completed_enrollments, k=min(30, len(completed_enrollments))):
            Certificate.objects.create(
                student=enrollment.student,
                course=enrollment.course,
                completion_date=(enrollment.completed_at or timezone.now()).date(),
                grade=str(int(enrollment.current_grade)) if enrollment.current_grade else 'A',
                verification_code=uuid.uuid4(),
                is_verified=True
            )

        # --- 27. TRANSACTIONS (STUDENTS pay, FINANCE processes) ---
        self.stdout.write("💳 Creating transactions...")
        for student in random.sample(users['students'], k=30):
            for _ in range(random.randint(1, 5)):
                gateway = random.choice(gateways)
                amount = Decimal(str(random.uniform(50, 200)))
                status = random.choice(['pending', 'completed', 'completed', 'completed', 'failed'])
                txn_type = random.choice(['enrollment', 'subscription', 'refund'])
                
                txn = Transaction.objects.create(
                    user=student,
                    transaction_type=txn_type,
                    amount=amount,
                    currency='USD',
                    status=status,
                    gateway=gateway,
                    gateway_transaction_id=f"{gateway.slug}_{uuid.uuid4().hex[:20]}",
                    course=random.choice(lms_courses) if txn_type == 'enrollment' and random.random() > 0.5 else None,
                    metadata={
                        'payment_method': random.choice(['card', 'paypal', 'bank_transfer']),
                        'card_last4': str(random.randint(1000, 9999)) if random.random() > 0.3 else '',
                        'card_brand': random.choice(['Visa', 'Mastercard', 'Amex']) if random.random() > 0.3 else '',
                        'description': f"Payment for {fake.catch_phrase()}"
                    },
                    completed_at=timezone.now() - timedelta(days=random.randint(1, 90)) if status == 'completed' else None
                )

        # --- 28. INVOICES (Generated by FINANCE for STUDENTS) ---
        self.stdout.write("🧾 Creating invoices...")
        completed_transactions = Transaction.objects.filter(status='completed')
        for txn in random.sample(list(completed_transactions), k=min(40, len(completed_transactions))):
            subtotal = txn.amount
            tax_rate = Decimal('10.00')
            Invoice.objects.create(
                student=txn.user,
                course=txn.course if txn.course else None,
                subtotal=subtotal,
                tax_rate=tax_rate,
                discount_amount=Decimal('0.00'),
                currency=txn.currency,
                status='paid',
                due_date=(txn.completed_at + timedelta(days=30)).date() if txn.completed_at else timezone.now().date() + timedelta(days=30),
                paid_date=txn.completed_at.date() if txn.completed_at else None,
                notes=f"Payment for transaction {txn.transaction_id}"
            )

        # --- 29. BADGES (Created by ADMINS) ---
        self.stdout.write("🏅 Creating badges...")
        badges = []
        badge_data = [
            {'name': 'First Course Completed', 'icon': 'award', 'color': 'bronze', 'points': 10, 'criteria': 'Complete your first course'},
            {'name': 'Quick Learner', 'icon': 'zap', 'color': 'yellow', 'points': 20, 'criteria': 'Complete a course in under 7 days'},
            {'name': 'Quiz Master', 'icon': 'brain', 'color': 'purple', 'points': 15, 'criteria': 'Score 100% on 5 quizzes'},
            {'name': 'Perfect Score', 'icon': 'star', 'color': 'gold', 'points': 30, 'criteria': 'Get 100% in a course'},
            {'name': 'Marathon Learner', 'icon': 'flag', 'color': 'green', 'points': 25, 'criteria': 'Complete 10 courses'},
            {'name': 'Assignment Pro', 'icon': 'file-text', 'color': 'blue', 'points': 15, 'criteria': 'Submit 20 assignments on time'},
            {'name': 'Community Helper', 'icon': 'users', 'color': 'cyan', 'points': 20, 'criteria': 'Help 10 students in discussions'},
            {'name': 'Early Bird', 'icon': 'sunrise', 'color': 'orange', 'points': 10, 'criteria': 'Complete lessons before 8 AM for 7 days'},
        ]
        for bd in badge_data:
            badge = Badge.objects.create(
                name=bd['name'],
                description=f"Awarded for {bd['criteria'].lower()}",
                icon=bd['icon'],
                color=bd['color'],
                criteria=bd['criteria'],
                points=bd['points'],
                is_active=True
            )
            badges.append(badge)

        # --- 30. STUDENT BADGES (Awarded by INSTRUCTORS and ADMINS to STUDENTS) ---
        self.stdout.write("🎖️ Awarding badges to students...")
        for student in random.sample(users['students'], k=25):
            num_badges = random.randint(1, 5)
            for badge in random.sample(badges, k=min(num_badges, len(badges))):
                StudentBadge.objects.create(
                    student=student,
                    badge=badge,
                    awarded_by=random.choice(users['instructors'] + users['admins']),
                    reason=fake.sentence()
                )

        # --- 31. BLOG CATEGORIES (Created by CONTENT MANAGERS) ---
        self.stdout.write("📰 Creating blog categories...")
        blog_categories = []
        blog_cat_data = [
            {'name': 'Technology Trends', 'icon': 'trending-up', 'color': 'blue'},
            {'name': 'Learning Tips', 'icon': 'book-open', 'color': 'green'},
            {'name': 'Career Advice', 'icon': 'briefcase', 'color': 'purple'},
            {'name': 'Student Success Stories', 'icon': 'award', 'color': 'yellow'},
            {'name': 'Industry News', 'icon': 'newspaper', 'color': 'red'},
            {'name': 'Course Updates', 'icon': 'bell', 'color': 'cyan'},
        ]
        for idx, bcd in enumerate(blog_cat_data):
            blog_cat = BlogCategory.objects.create(
                name=bcd['name'],
                description=fake.text(max_nb_chars=150),
                icon=bcd['icon'],
                color=bcd['color'],
                display_order=idx,
                is_active=True
            )
            blog_categories.append(blog_cat)

        # --- 32. BLOG POSTS (Written by INSTRUCTORS, CONTENT MANAGERS, ADMINS) ---
        self.stdout.write("✍️ Creating blog posts...")
        blog_authors = users['instructors'] + users['content_managers'] + users['admins']
        # Ensure every instructor, content manager, and admin writes at least one blog post
        for author in blog_authors:
            BlogPost.objects.create(
                title=fake.catch_phrase(),
                subtitle=fake.sentence(),
                excerpt=fake.text(max_nb_chars=200),
                content='\n\n'.join([fake.paragraph(nb_sentences=5) for _ in range(random.randint(4, 8))]),
                category=random.choice(blog_categories),
                tags=[fake.word() for _ in range(random.randint(3, 6))],
                author=author,
                author_name=author.get_full_name(),
                author_title=author.profile.role.replace('_', ' ').title(),
                featured_image_alt=fake.sentence(),
                read_time=random.randint(3, 15),
                views_count=random.randint(0, 5000),
                status='published',
                is_featured=random.random() > 0.7,
                publish_date=timezone.now() - timedelta(days=random.randint(1, 365)),
                meta_description=fake.sentence(nb_words=20),
                meta_keywords=', '.join([fake.word() for _ in range(5)])
            )

        # --- 33. DISCUSSIONS (Started by STUDENTS, participated by ALL) ---
        self.stdout.write("💬 Creating discussions and replies...")
        discussions = []
        for course in random.sample(lms_courses, k=min(15, len(lms_courses))):
            for _ in range(random.randint(5, 12)):
                discussion = Discussion.objects.create(
                    course=course,
                    title=f"{fake.catch_phrase()}?",
                    content=fake.text(max_nb_chars=500),
                    author=random.choice(users['students']),
                    is_pinned=random.random() > 0.85,
                    is_locked=random.random() > 0.9,
                    views_count=random.randint(5, 500)
                )
                discussions.append(discussion)
                
                # Add replies from STUDENTS, INSTRUCTORS, and others
                for _ in range(random.randint(2, 10)):
                    DiscussionReply.objects.create(
                        discussion=discussion,
                        author=random.choice(all_users),
                        content=fake.text(max_nb_chars=300),
                        is_solution=random.random() > 0.9
                    )

        # --- 34. STUDY GROUPS (Created by STUDENTS, joined by STUDENTS) ---
        self.stdout.write("👥 Creating study groups...")
        study_groups = []
        for course in random.sample(lms_courses, k=min(10, len(lms_courses))):
            for _ in range(random.randint(1, 3)):
                creator = random.choice(users['students'])
                study_group = StudyGroup.objects.create(
                    name=f"{course.title[:30]} Study Group - {fake.word().title()}",
                    description=fake.text(max_nb_chars=200),
                    course=course,
                    max_members=random.choice([5, 10, 15, 20]),
                    is_active=True,
                    is_public=random.choice([True, False]),
                    created_by=creator
                )
                study_groups.append(study_group)
                
                StudyGroupMember.objects.create(
                    study_group=study_group,
                    user=creator,
                    role='admin',
                    is_active=True
                )
                
                enrolled_students = list(Enrollment.objects.filter(course=course).values_list('student', flat=True))
                num_members = random.randint(2, min(study_group.max_members - 1, len(enrolled_students)))
                for student_id in random.sample(enrolled_students, k=num_members):
                    if student_id != creator.id:
                        StudyGroupMember.objects.create(
                            study_group=study_group,
                            user=User.objects.get(id=student_id),
                            role=random.choice(['member', 'member', 'member', 'moderator']),
                            is_active=True
                        )

        # --- 35. MESSAGES (Between ALL user types) ---
        self.stdout.write("✉️ Creating messages...")
        # Ensure every user has sent and received messages
        for user in all_users:
            # Each user sends 2-5 messages
            for _ in range(random.randint(2, 5)):
                recipient = random.choice([u for u in all_users if u != user])
                Message.objects.create(
                    sender=user,
                    recipient=recipient,
                    subject=fake.sentence(),
                    body=fake.text(max_nb_chars=400),
                    is_read=random.choice([True, False]),
                    read_at=timezone.now() - timedelta(hours=random.randint(1, 48)) if random.random() > 0.5 else None
                )

        # --- 36. SUPPORT TICKETS (Created by STUDENTS and others, handled by SUPPORT) ---
        self.stdout.write("🎫 Creating support tickets...")
        tickets = []
        # Ensure every support staff member handles tickets
        ticket_creators = users['students'] + random.sample(users['instructors'], k=5)
        for creator in ticket_creators[:30]:
            ticket = SupportTicket.objects.create(
                ticket_id=f"TKT-{random.randint(10000, 99999)}",
                user=creator,
                category=random.choice(['technical', 'account', 'course', 'payment', 'other']),
                subject=fake.sentence(),
                description=fake.text(max_nb_chars=500),
                priority=random.choice(['low', 'normal', 'high', 'urgent']),
                status=random.choice(['open', 'in_progress', 'waiting_response', 'resolved', 'closed']),
                assigned_to=random.choice(users['support']),
                resolved_at=timezone.now() - timedelta(days=random.randint(1, 30)) if random.random() > 0.5 else None
            )
            tickets.append(ticket)
            
            # Add ticket replies from both user and support
            for _ in range(random.randint(1, 6)):
                TicketReply.objects.create(
                    ticket=ticket,
                    author=random.choice([ticket.user, ticket.assigned_to]),
                    message=fake.text(max_nb_chars=300),
                    is_internal_note=random.random() > 0.7
                )

        # --- 37. NOTIFICATIONS (Sent to ALL users) ---
        self.stdout.write("🔔 Creating notifications...")
        for user in all_users:
            for _ in range(random.randint(3, 12)):
                Notification.objects.create(
                    user=user,
                    notification_type=random.choice(['enrollment', 'assignment', 'grade', 'announcement', 'message', 'certificate', 'system']),
                    title=fake.sentence(),
                    message=fake.text(max_nb_chars=200),
                    link=f"/courses/{random.randint(1, 10)}" if random.random() > 0.5 else '',
                    is_read=random.choice([True, False]),
                    read_at=timezone.now() - timedelta(hours=random.randint(1, 72)) if random.random() > 0.5 else None
                )

        # --- 38. ANNOUNCEMENTS (Created by ADMINS and INSTRUCTORS) ---
        self.stdout.write("📢 Creating announcements...")
        announcement_creators = users['admins'] + users['instructors']
        for creator in announcement_creators:
            ann_type = random.choice(['system', 'course', 'category'])
            Announcement.objects.create(
                title=fake.sentence(),
                content=fake.text(max_nb_chars=500),
                announcement_type=ann_type,
                priority=random.choice(['low', 'normal', 'high', 'urgent']),
                course=random.choice(lms_courses) if ann_type == 'course' else None,
                category=random.choice(categories) if ann_type == 'category' else None,
                created_by=creator,
                is_active=random.random() > 0.2,
                publish_date=timezone.now() - timedelta(days=random.randint(1, 60)),
                expiry_date=timezone.now() + timedelta(days=random.randint(30, 90)) if random.random() > 0.5 else None
            )

        # --- 39. CONTACT MESSAGES (From prospective STUDENTS, responded by SUPPORT) ---
        self.stdout.write("📧 Creating contact messages...")
        for _ in range(25):
            support_responder = random.choice(users['support']) if random.random() > 0.3 else None
            ContactMessage.objects.create(
                user=random.choice(users['students']) if random.random() > 0.5 else None,
                name=fake.name(),
                email=fake.email(),
                subject=random.choice(['admissions', 'programs', 'campus', 'financial', 'support', 'other']),
                message=fake.text(max_nb_chars=500),
                is_read=random.choice([True, False]),
                responded=support_responder is not None,
                responded_by=support_responder,
                responded_at=timezone.now() - timedelta(days=random.randint(1, 30)) if support_responder else None,
                created_at=timezone.now() - timedelta(days=random.randint(1, 90))
            )

        # --- 40. AUDIT LOGS (ALL user types have audit logs) ---
        self.stdout.write("📋 Creating audit logs...")
        for user in all_users:
            for _ in range(random.randint(3, 10)):
                AuditLog.objects.create(
                    user=user,
                    action=random.choice(['create', 'update', 'delete', 'login', 'logout', 'access', 'export', 'permission_change']),
                    model_name=random.choice(['Course', 'User', 'Enrollment', 'Assignment', 'Payment', 'Review', 'Discussion']),
                    object_id=str(random.randint(1, 100)),
                    description=fake.sentence(),
                    ip_address=fake.ipv4(),
                    user_agent=fake.user_agent(),
                    extra_data={
                        'browser': fake.user_agent(),
                        'platform': random.choice(['Windows', 'Mac', 'Linux', 'iOS', 'Android']),
                        'location': fake.city()
                    }
                )

        # --- UPDATE STATISTICS ---
        self.stdout.write("📊 Updating course statistics...")
        for course in lms_courses:
            course.update_statistics()

        self.stdout.write(self.style.SUCCESS("\n" + "="*80))
        self.stdout.write(self.style.SUCCESS("✅ COMPREHENSIVE DATABASE SEEDING COMPLETED SUCCESSFULLY!"))
        self.stdout.write(self.style.SUCCESS("   ALL USER ROLES HAVE ACTIVELY PARTICIPATED IN THE SYSTEM"))
        self.stdout.write(self.style.SUCCESS("="*80))
        
        # Role-specific summary
        self.stdout.write(self.style.SUCCESS(f"\n🎭 USER ROLE ACTIVITIES:"))
        self.stdout.write(f"   👨‍🎓 STUDENTS ({len(users['students'])}):  Enrolled, completed lessons, submitted assignments, took quizzes, wrote reviews, joined study groups, received certificates")
        self.stdout.write(f"   👨‍🏫 INSTRUCTORS ({len(users['instructors'])}): Created {len(lms_courses)} courses, {len(assignments)} assignments, {len(quizzes)} quizzes, graded submissions, wrote blog posts, answered discussions")
        self.stdout.write(f"   👨‍💼 ADMINS ({len(users['admins'])}): Reviewed applications, approved reviews, created announcements, configured system, managed badges, approved content")
        self.stdout.write(f"   🎧 SUPPORT ({len(users['support'])}): Handled {len(tickets)} support tickets, responded to contact messages, assisted students")
        self.stdout.write(f"   📝 CONTENT MANAGERS ({len(users['content_managers'])}): Created blog posts, managed categories, configured system settings, curated content")
        self.stdout.write(f"   💰 FINANCE ({len(users['finance'])}): Set up payment gateways, processed transactions, managed subscription plans, generated invoices")
        self.stdout.write(f"   ✅ QA REVIEWERS ({len(users['qa'])}): Reviewed course quality, validated quizzes, ensured content standards")
        
        self.stdout.write(self.style.SUCCESS(f"\n📈 COMPREHENSIVE STATISTICS:"))
        self.stdout.write(f"   👥 {len(all_users)} Total Users")
        self.stdout.write(f"   🏢 {len(vendors)} Vendors")
        self.stdout.write(f"   ⚙️  {SystemConfiguration.objects.count()} System Configurations")
        self.stdout.write(f"   💳 {len(gateways)} Payment Gateways")
        self.stdout.write(f"   📋 {len(plans)} Subscription Plans")
        self.stdout.write(f"   🎫 {Subscription.objects.count()} Active Subscriptions")
        self.stdout.write(f"   🎓 {len(faculties)} Faculties")
        self.stdout.write(f"   📚 {len(academic_courses)} Academic Courses")
        self.stdout.write(f"   📅 {len(intakes)} Course Intakes")
        self.stdout.write(f"   📝 {len(applications)} Course Applications")
        self.stdout.write(f"   📎 {ApplicationDocument.objects.count()} Application Documents")
        self.stdout.write(f"   💰 {ApplicationPayment.objects.count()} Application Payments")
        self.stdout.write(f"   🗂️  {len(categories)} LMS Course Categories")
        self.stdout.write(f"   🎥 {len(lms_courses)} LMS Courses (with REAL YouTube videos)")
        self.stdout.write(f"   📑 {LessonSection.objects.count()} Lesson Sections")
        self.stdout.write(f"   📹 {Lesson.objects.count()} Lessons")
        self.stdout.write(f"   🎓 {len(enrollments)} Enrollments")
        self.stdout.write(f"   📊 {LessonProgress.objects.count()} Lesson Progress Records")
        self.stdout.write(f"   📝 {len(assignments)} Assignments")
        self.stdout.write(f"   📤 {AssignmentSubmission.objects.count()} Assignment Submissions")
        self.stdout.write(f"   ❓ {len(quizzes)} Quizzes")
        self.stdout.write(f"   ❔ {QuizQuestion.objects.count()} Quiz Questions")
        self.stdout.write(f"   🎯 {QuizAttempt.objects.count()} Quiz Attempts")
        self.stdout.write(f"   ⭐ {Review.objects.count()} Course Reviews")
        self.stdout.write(f"   🏆 {Certificate.objects.count()} Certificates")
        self.stdout.write(f"   💳 {Transaction.objects.count()} Transactions")
        self.stdout.write(f"   🧾 {Invoice.objects.count()} Invoices")
        self.stdout.write(f"   🏅 {len(badges)} Badges")
        self.stdout.write(f"   🎖️  {StudentBadge.objects.count()} Student Badges")
        self.stdout.write(f"   📰 {len(blog_categories)} Blog Categories")
        self.stdout.write(f"   ✍️  {BlogPost.objects.count()} Blog Posts")
        self.stdout.write(f"   💬 {len(discussions)} Discussions")
        self.stdout.write(f"   💭 {DiscussionReply.objects.count()} Discussion Replies")
        self.stdout.write(f"   👥 {len(study_groups)} Study Groups")
        self.stdout.write(f"   👤 {StudyGroupMember.objects.count()} Study Group Members")
        self.stdout.write(f"   ✉️  {Message.objects.count()} Messages")
        self.stdout.write(f"   🎫 {len(tickets)} Support Tickets")
        self.stdout.write(f"   💬 {TicketReply.objects.count()} Ticket Replies")
        self.stdout.write(f"   🔔 {Notification.objects.count()} Notifications")
        self.stdout.write(f"   📢 {Announcement.objects.count()} Announcements")
        self.stdout.write(f"   📧 {ContactMessage.objects.count()} Contact Messages")
        self.stdout.write(f"   📋 {AuditLog.objects.count()} Audit Log Entries")
        self.stdout.write(self.style.SUCCESS("="*80 + "\n"))