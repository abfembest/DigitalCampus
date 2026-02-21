import random
import uuid
from decimal import Decimal
from datetime import timedelta, date
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from faker import Faker

from eduweb.models import (
    Announcement, Assignment, AssignmentSubmission, AuditLog, Badge, StudentBadge,
    BlogCategory, BlogPost, Certificate, ContactMessage,
    Faculty, Department, Program, Course, AllRequiredPayments,
    CourseIntake, CourseApplication, ApplicationDocument, ApplicationPayment,
    CourseCategory, Discussion, DiscussionReply, Enrollment, SupportTicket,
    TicketReply, Invoice, LessonProgress, LMSCourse, Lesson, LessonSection,
    Message, Notification, PaymentGateway, Transaction, Quiz, QuizQuestion,
    QuizAnswer, QuizAttempt, QuizResponse, Review, SubscriptionPlan,
    Subscription, SystemConfiguration, UserProfile, Vendor, StudyGroup,
    StudyGroupMember, BroadcastMessage, StaffPayroll,
)

fake = Faker()

YOUTUBE_VIDEOS = {
    'python': [
        'https://www.youtube.com/watch?v=rfscVS0vtbw',
        'https://www.youtube.com/watch?v=_uQrJ0TkZlc',
        'https://www.youtube.com/watch?v=kqtD5dpn9C8',
        'https://www.youtube.com/watch?v=8DvywoWv6fI',
    ],
    'web_dev': [
        'https://www.youtube.com/watch?v=UB1O30fR-EE',
        'https://www.youtube.com/watch?v=mU6anWqZJcc',
        'https://www.youtube.com/watch?v=1PnVor36_40',
        'https://www.youtube.com/watch?v=G3e-cpL7ofc',
    ],
    'data_science': [
        'https://www.youtube.com/watch?v=ua-CiDNNj30',
        'https://www.youtube.com/watch?v=RBSGKlAvoiM',
        'https://www.youtube.com/watch?v=7eh4d6sabA0',
        'https://www.youtube.com/watch?v=zN1_fMwbZac',
    ],
    'machine_learning': [
        'https://www.youtube.com/watch?v=aircAruvnKk',
        'https://www.youtube.com/watch?v=IHZwWFHWa-w',
        'https://www.youtube.com/watch?v=i8D90DkCLhI',
        'https://www.youtube.com/watch?v=jGwO_UgTS7I',
    ],
    'javascript': [
        'https://www.youtube.com/watch?v=W6NZfCO5SIk',
        'https://www.youtube.com/watch?v=PkZNo7MFNFg',
        'https://www.youtube.com/watch?v=DHjqpvDnNGE',
        'https://www.youtube.com/watch?v=BMUiFMZr7vk',
    ],
    'react': [
        'https://www.youtube.com/watch?v=Ke90Tje7VS0',
        'https://www.youtube.com/watch?v=bMknfKXIFA8',
        'https://www.youtube.com/watch?v=SqcY0GlETPk',
        'https://www.youtube.com/watch?v=Rh3tobg7hEo',
    ],
    'design': [
        'https://www.youtube.com/watch?v=0JCUH5daCCE',
        'https://www.youtube.com/watch?v=YiLUYf4HDh4',
        'https://www.youtube.com/watch?v=wIuVvCuiJhU',
        'https://www.youtube.com/watch?v=_2LLXnUdUIc',
    ],
    'business': [
        'https://www.youtube.com/watch?v=qs-l7jDKJLQ',
        'https://www.youtube.com/watch?v=8w4KCiVu1kI',
        'https://www.youtube.com/watch?v=jpe-LKn-4gM',
        'https://www.youtube.com/watch?v=eC7xzavzEKY',
    ],
    'engineering': [
        'https://www.youtube.com/watch?v=yI2oS2hoL0k',
        'https://www.youtube.com/watch?v=2a-tOmHGDI0',
        'https://www.youtube.com/watch?v=JVFNc9GBPRY',
        'https://www.youtube.com/watch?v=dFUlAQZB9Ng',
    ],
}


class Command(BaseCommand):
    help = 'Seeds ALL tables with realistic data covering every single field'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING(
            "🚀 Starting FULL database seeding — every table, every field..."
        ))

        # ── CLEANUP ──────────────────────────────────────────────────────────
        self.stdout.write("🧹 Clearing existing data...")
        models_to_clear = [
            AuditLog, Notification, Message, TicketReply, SupportTicket,
            StudentBadge, Badge, QuizResponse, QuizAttempt, QuizAnswer,
            QuizQuestion, Quiz, AssignmentSubmission, Assignment,
            LessonProgress, Certificate, Review, Enrollment, DiscussionReply,
            Discussion, Lesson, LessonSection, LMSCourse, CourseCategory,
            ApplicationPayment, ApplicationDocument, CourseApplication,
            CourseIntake, AllRequiredPayments, StaffPayroll,
            Course, Program, Department, Faculty, Invoice, Transaction,
            Subscription, SubscriptionPlan, PaymentGateway, BlogPost,
            BlogCategory, ContactMessage, Vendor, SystemConfiguration,
            Announcement, StudyGroupMember, StudyGroup, BroadcastMessage,
        ]
        for model in models_to_clear:
            model.objects.all().delete()
        UserProfile.objects.all().delete()
        User.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("   ✅ All data cleared"))

        # ── 1. USERS ─────────────────────────────────────────────────────────
        self.stdout.write("👥 Creating users...")
        users = {
            'students': [], 'instructors': [], 'admins': [],
            'support': [], 'content_managers': [], 'finance': [], 'qa': [],
        }

        def make_users(username_prefix, role_key, count=6, is_staff=False):
            created = []
            for i in range(count):
                uname = f"{username_prefix}{i + 1}" if i > 0 else username_prefix
                u = User.objects.create_user(
                    username=uname,
                    email=f"{uname}@university.edu",
                    password="12345",
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    is_staff=is_staff,
                )
                p = u.profile
                p.role = role_key
                p.bio = fake.text(max_nb_chars=250)
                p.phone = fake.phone_number()[:20]
                p.date_of_birth = fake.date_of_birth(minimum_age=22, maximum_age=55)
                p.address = fake.street_address()
                p.city = fake.city()
                p.country = fake.country()
                p.website = fake.url() if random.random() > 0.5 else ''
                p.linkedin = f"https://linkedin.com/in/{uname}"
                p.twitter = f"https://twitter.com/{uname}" if random.random() > 0.5 else ''
                p.email_notifications = random.choice([True, False])
                p.marketing_emails = random.choice([True, False])
                p.email_verified = i < 4
                p.save()
                created.append(u)
            return created

        users['students'] = make_users('student', 'student', 8)
        users['instructors'] = make_users('instructor', 'instructor', 6)
        users['admins'] = make_users('admin', 'admin', 4, is_staff=True)
        users['content_managers'] = make_users('content_mgr', 'content_manager', 4)
        users['support'] = make_users('support', 'support', 4)
        users['finance'] = make_users('finance', 'finance', 4)
        users['qa'] = make_users('qa', 'qa', 4)

        all_users = sum(users.values(), [])
        verified_students = [u for u in users['students'] if u.profile.email_verified]
        verified_instructors = [u for u in users['instructors'] if u.profile.email_verified]
        verified_admins = [u for u in users['admins'] if u.profile.email_verified]
        verified_support = [u for u in users['support'] if u.profile.email_verified]
        verified_finance = [u for u in users['finance'] if u.profile.email_verified]
        verified_content = [u for u in users['content_managers'] if u.profile.email_verified]
        verified_all = [u for u in all_users if u.profile.email_verified]
        staff_users = (
            users['instructors'] + users['admins'] +
            users['support'] + users['finance'] + users['content_managers']
        )
        self.stdout.write(self.style.SUCCESS(f"   ✅ {len(all_users)} users created"))

        # ── 2. VENDORS ───────────────────────────────────────────────────────
        self.stdout.write("🏢 Creating vendors...")
        vendors = []
        for vd in [
            ('Tech University Partners', 'United States'),
            ('Global Education Alliance', 'United Kingdom'),
            ('Asian Institute Network', 'Singapore'),
            ('European Learning Consortium', 'Germany'),
            ('Australian Education Hub', 'Australia'),
        ]:
            vendors.append(Vendor.objects.create(
                name=vd[0],
                email=fake.company_email(),
                country=vd[1],
                stripe_account_id=f"acct_{uuid.uuid4().hex[:16]}",
                is_active=True,
            ))

        # ── 3. SYSTEM CONFIGURATIONS ─────────────────────────────────────────
        self.stdout.write("⚙️  Creating system configurations...")
        cfg_data = [
            ('site_name', 'MIU Learning Platform', 'text', True),
            ('max_upload_size', '10485760', 'number', False),
            ('email_notifications_enabled', 'true', 'boolean', True),
            ('maintenance_mode', 'false', 'boolean', False),
            ('default_currency', 'GBP', 'text', True),
            ('max_enrollments_per_user', '50', 'number', False),
            ('certificate_enabled', 'true', 'boolean', True),
            ('forum_enabled', 'true', 'boolean', True),
            ('registration_open', 'true', 'boolean', True),
            ('smtp_host', 'smtp.gmail.com', 'text', False),
        ]
        cfg_editors = users['admins'] + users['content_managers']
        for key, val, stype, is_pub in cfg_data:
            SystemConfiguration.objects.create(
                key=key, value=val, setting_type=stype,
                description=f"Controls {key.replace('_', ' ')}",
                is_public=is_pub,
                updated_by=random.choice(cfg_editors),
            )

        # ── 4. PAYMENT GATEWAYS ──────────────────────────────────────────────
        self.stdout.write("💳 Creating payment gateways...")
        gateways = []
        for name, slug, gtype, active in [
            ('Stripe', 'stripe', 'stripe', True),
            ('PayPal', 'paypal', 'paypal', True),
            ('Razorpay', 'razorpay', 'razorpay', False),
        ]:
            gateways.append(PaymentGateway.objects.create(
                name=name, slug=slug, gateway_type=gtype,
                api_key=f"pk_test_{uuid.uuid4().hex}",
                api_secret=f"sk_test_{uuid.uuid4().hex}",
                webhook_secret=f"whsec_{uuid.uuid4().hex}",
                is_active=active, is_test_mode=True,
            ))

        # ── 5. SUBSCRIPTION PLANS ────────────────────────────────────────────
        self.stdout.write("📋 Creating subscription plans...")
        plans = []
        plan_data = [
            ('Free', 'Access to free courses only', Decimal('0.00'), 'yearly',
             ['Free courses', 'Community forums', 'Basic support'], 5, False),
            ('Basic', 'Perfect for individual learners', Decimal('29.99'), 'monthly',
             ['All free features', 'Premium courses', 'Email support', 'Downloadable resources'], 20, False),
            ('Pro', 'Best value for serious learners', Decimal('79.99'), 'monthly',
             ['All Basic features', 'Unlimited courses', 'Priority support', 'Certificates', 'Live Q&A'], None, True),
            ('Enterprise', 'For teams and organisations', Decimal('299.99'), 'monthly',
             ['All Pro features', 'Team management', 'Custom branding', 'Dedicated support', 'API access'], None, False),
        ]
        for idx, (name, desc, price, cycle, features, max_c, popular) in enumerate(plan_data):
            plans.append(SubscriptionPlan.objects.create(
                name=name, description=desc, price=price, currency='GBP',
                billing_cycle=cycle, features=features,
                max_courses=max_c, is_active=True,
                is_popular=popular, display_order=idx,
            ))

        # ── 6. SUBSCRIPTIONS ─────────────────────────────────────────────────
        self.stdout.write("🎫 Creating subscriptions...")
        for student in verified_students:
            plan = random.choice(plans)
            days = 30 if plan.billing_cycle == 'monthly' else 365
            start = timezone.now().date() - timedelta(days=random.randint(0, 60))
            status = random.choice(['active', 'active', 'active', 'cancelled', 'expired'])
            Subscription.objects.create(
                user=student, plan=plan, status=status,
                end_date=start + timedelta(days=days),
                auto_renew=random.choice([True, False]),
                gateway_subscription_id=f"sub_{uuid.uuid4().hex[:24]}",
                cancelled_at=timezone.now() - timedelta(days=random.randint(1, 20))
                if status == 'cancelled' else None,
            )

        # ── 7. FACULTIES ─────────────────────────────────────────────────────
        self.stdout.write("🎓 Creating faculties...")
        faculty_raw = [
            {
                'name': 'Faculty of Computer Science & IT', 'code': 'CSIT',
                'icon': 'cpu', 'color_primary': 'blue', 'color_secondary': 'cyan',
                'tagline': 'Leading the digital revolution',
                'description': 'Leading education in computing, software development, and IT.',
                'mission': 'To produce world-class graduates equipped with cutting-edge technology skills.',
                'vision': 'To be a globally recognised centre of excellence in computing.',
                'accreditation': 'Accredited by British Computer Society (BCS) – 2023',
                'student_count': 1850, 'placement_rate': 94,
                'partner_count': 42, 'international_faculty': 35,
                'special_features': [
                    'State-of-the-art AI & Robotics Lab',
                    'Industry partnerships with Google, Microsoft, Amazon',
                    'International exchange programmes with MIT and Oxford',
                    'Annual Hackathon with £50K prize pool',
                ],
            },
            {
                'name': 'Faculty of Engineering', 'code': 'ENG',
                'icon': 'cog', 'color_primary': 'orange', 'color_secondary': 'amber',
                'tagline': 'Building tomorrow, today',
                'description': 'Excellence in engineering education across multiple disciplines.',
                'mission': 'Develop innovative engineers who solve real-world challenges.',
                'vision': 'A faculty synonymous with engineering excellence and industry impact.',
                'accreditation': 'Accredited by Institution of Engineering and Technology (IET) – 2022',
                'student_count': 1420, 'placement_rate': 91,
                'partner_count': 38, 'international_faculty': 28,
                'special_features': [
                    'Fully equipped civil and structural testing lab',
                    'Partnerships with Arup, Atkins, and Balfour Beatty',
                    'Year in industry placement scheme',
                    'Research collaborations with national infrastructure bodies',
                ],
            },
            {
                'name': 'Faculty of Business & Management', 'code': 'BUS',
                'icon': 'briefcase', 'color_primary': 'green', 'color_secondary': 'emerald',
                'tagline': 'Shaping future leaders',
                'description': 'Preparing future business leaders and entrepreneurs.',
                'mission': 'Develop principled leaders who create sustainable value.',
                'vision': 'A globally ranked business faculty producing transformational leaders.',
                'accreditation': 'AACSB Accredited – 2021',
                'student_count': 2200, 'placement_rate': 89,
                'partner_count': 55, 'international_faculty': 40,
                'special_features': [
                    'Bloomberg Terminal Lab', 'Executive mentorship programme',
                    'Annual Business Plan Competition',
                    'Global study trips to New York, Singapore, and Dubai',
                ],
            },
            {
                'name': 'Faculty of Health Sciences', 'code': 'HLTH',
                'icon': 'heart', 'color_primary': 'red', 'color_secondary': 'rose',
                'tagline': 'Caring for tomorrow',
                'description': 'Comprehensive health education and clinical training.',
                'mission': 'Produce compassionate, competent healthcare professionals.',
                'vision': 'Leading faculty for health sciences education in the region.',
                'accreditation': 'Accredited by Nursing and Midwifery Council (NMC) – 2023',
                'student_count': 980, 'placement_rate': 97,
                'partner_count': 25, 'international_faculty': 20,
                'special_features': [
                    'Simulation wards and high-fidelity clinical mannequins',
                    'NHS Trust placement partnerships',
                    'Interprofessional education programme',
                    'Research links with WHO and Public Health England',
                ],
            },
            {
                'name': 'Faculty of Arts & Humanities', 'code': 'ART',
                'icon': 'palette', 'color_primary': 'purple', 'color_secondary': 'violet',
                'tagline': 'Inspiring creativity and critical thinking',
                'description': 'Fostering creativity and critical thinking in arts and humanities.',
                'mission': 'Nurture creative minds and independent critical thinkers.',
                'vision': 'A faculty that bridges creativity, culture, and commerce.',
                'accreditation': 'Quality Assurance Agency (QAA) Reviewed – 2022',
                'student_count': 1100, 'placement_rate': 82,
                'partner_count': 30, 'international_faculty': 22,
                'special_features': [
                    'Modern art studios and digital design suites',
                    'Annual Arts Festival', 'Partnerships with national museums',
                    'Study abroad links with Sorbonne and Florence Academy',
                ],
            },
        ]
        faculties = []
        for idx, fd in enumerate(faculty_raw):
            f = Faculty.objects.create(
                name=fd['name'], code=fd['code'],
                icon=fd['icon'],
                color_primary=fd['color_primary'],
                color_secondary=fd['color_secondary'],
                tagline=fd['tagline'],
                description=fd['description'],
                mission=fd['mission'],
                vision=fd['vision'],
                accreditation=fd['accreditation'],
                student_count=fd['student_count'],
                placement_rate=fd['placement_rate'],
                partner_count=fd['partner_count'],
                international_faculty=fd['international_faculty'],
                special_features=fd['special_features'],
                meta_description=fd['description'][:160],
                meta_keywords=f"{fd['name']}, university, degree, {fd['code']}",
                is_active=True, display_order=idx,
            )
            faculties.append(f)

        # ── 8. DEPARTMENTS ───────────────────────────────────────────────────
        self.stdout.write("🏛️  Creating departments...")
        dept_raw = [
            (faculties[0], 'Department of Software Engineering', 'SE',
             'Focuses on design, development, and maintenance of software systems.', 0),
            (faculties[0], 'Department of Artificial Intelligence', 'AI',
             'Research and teaching at the frontier of AI and machine learning.', 1),
            (faculties[0], 'Department of Cybersecurity', 'CYS',
             'Specialists in network security, ethical hacking, and digital forensics.', 2),
            (faculties[1], 'Department of Civil Engineering', 'CVE',
             'Structural design, environmental systems, and infrastructure engineering.', 0),
            (faculties[1], 'Department of Electrical Engineering', 'EEE',
             'Power systems, electronics, and telecommunications engineering.', 1),
            (faculties[1], 'Department of Mechanical Engineering', 'MEE',
             'Thermodynamics, manufacturing, and mechanical design.', 2),
            (faculties[2], 'Department of Finance & Accounting', 'FNA',
             'Financial analysis, corporate finance, and accounting standards.', 0),
            (faculties[2], 'Department of Marketing & Strategy', 'MKS',
             'Brand management, consumer behaviour, and corporate strategy.', 1),
            (faculties[2], 'Department of Entrepreneurship', 'ENT',
             'Startup ecosystems, innovation management, and venture creation.', 2),
            (faculties[3], 'Department of Nursing', 'NRS',
             'Adult, child, and mental health nursing education and practice.', 0),
            (faculties[3], 'Department of Public Health', 'PHE',
             'Epidemiology, health policy, and community health management.', 1),
            (faculties[4], 'Department of English & Creative Writing', 'ECW',
             'Literature, linguistics, and creative and professional writing.', 0),
            (faculties[4], 'Department of Digital Media & Design', 'DMD',
             'Graphic design, multimedia production, and digital arts.', 1),
        ]
        departments = []
        for fac, name, code, desc, order in dept_raw:
            d = Department.objects.create(
                faculty=fac, name=name, code=code,
                description=desc, is_active=True, display_order=order,
            )
            departments.append(d)

        # Assign faculty/department to staff and student profiles
        for u in users['students'] + users['instructors'] + users['support']:
            fac = random.choice(faculties)
            fac_depts = [d for d in departments if d.faculty == fac]
            p = u.profile
            p.faculty = fac
            p.department = random.choice(fac_depts) if fac_depts else departments[0]
            p.save()

        # ── 9. PROGRAMS ──────────────────────────────────────────────────────
        self.stdout.write("📖 Creating programs...")
        prog_raw = [
            (departments[0], 'BSc Software Engineering', 'BSC-SE', 'undergraduate',
             Decimal('3.0'), 360, Decimal('50.00'), Decimal('9250.00'), 80, True, 0),
            (departments[0], 'MSc Advanced Software Engineering', 'MSC-ASE', 'masters',
             Decimal('1.0'), 180, Decimal('75.00'), Decimal('14500.00'), 40, False, 1),
            (departments[1], 'BSc Artificial Intelligence', 'BSC-AI', 'undergraduate',
             Decimal('3.0'), 360, Decimal('50.00'), Decimal('9250.00'), 60, True, 0),
            (departments[1], 'PhD Artificial Intelligence', 'PHD-AI', 'phd',
             Decimal('4.0'), 480, Decimal('100.00'), Decimal('18000.00'), 15, False, 1),
            (departments[2], 'BSc Cybersecurity', 'BSC-CYS', 'undergraduate',
             Decimal('3.0'), 360, Decimal('50.00'), Decimal('9250.00'), 50, False, 0),
            (departments[3], 'BEng Civil Engineering', 'BENG-CVE', 'undergraduate',
             Decimal('4.0'), 480, Decimal('50.00'), Decimal('9250.00'), 70, True, 0),
            (departments[4], 'BEng Electrical Engineering', 'BENG-EEE', 'undergraduate',
             Decimal('4.0'), 480, Decimal('50.00'), Decimal('9250.00'), 60, False, 0),
            (departments[6], 'BSc Finance & Accounting', 'BSC-FNA', 'undergraduate',
             Decimal('3.0'), 360, Decimal('50.00'), Decimal('9250.00'), 75, True, 0),
            (departments[6], 'MBA Finance', 'MBA-FIN', 'masters',
             Decimal('1.0'), 180, Decimal('100.00'), Decimal('17500.00'), 35, True, 1),
            (departments[9], 'BSc Nursing', 'BSC-NRS', 'undergraduate',
             Decimal('3.0'), 360, Decimal('50.00'), Decimal('9250.00'), 80, True, 0),
            (departments[11], 'BA English & Creative Writing', 'BA-ECW', 'undergraduate',
             Decimal('3.0'), 360, Decimal('50.00'), Decimal('9250.00'), 60, False, 0),
            (departments[12], 'BA Digital Media & Design', 'BA-DMD', 'undergraduate',
             Decimal('3.0'), 360, Decimal('50.00'), Decimal('9250.00'), 50, False, 0),
        ]
        programs = []
        for (dept, name, code, degree, dur, cred, app_fee, tuit, max_stu, feat, order) in prog_raw:
            p = Program.objects.create(
                department=dept, name=name, code=code,
                degree_level=degree, duration_years=dur,
                credits_required=cred, application_fee=app_fee,
                tuition_fee=tuit, max_students=max_stu,
                is_featured=feat, is_active=True, display_order=order,
                description=fake.text(max_nb_chars=400),
                entry_requirements=[
                    "Minimum 5 GCSEs at grade C/4 or above including English and Maths",
                    "A-Levels: AAB or equivalent BTEC",
                    "English proficiency: IELTS 6.0 or equivalent",
                    f"Strong passion for {name.split()[-1]}",
                ],
            )
            programs.append(p)

        # Assign program to student profiles
        for u in users['students']:
            p = u.profile
            if p.department:
                dept_progs = [pr for pr in programs if pr.department == p.department]
                if dept_progs:
                    p.program = random.choice(dept_progs)
                    p.save()

        # ── 10. ACADEMIC COURSES ─────────────────────────────────────────────
        self.stdout.write("📚 Creating academic courses...")
        ac_raw = [
            (programs[0], departments[0], faculties[0],
             'Bachelor of Science in Software Engineering', 'AC-BSC-SE',
             'undergraduate', ['full_time', 'part_time'], Decimal('3.0'),
             'Build the future with clean code', Decimal('50.00'), Decimal('9250.00'),
             '£35K–£55K', 93, 'blue', 'indigo', 'laptop', True),
            (programs[2], departments[1], faculties[0],
             'Bachelor of Science in Artificial Intelligence', 'AC-BSC-AI',
             'undergraduate', ['full_time'], Decimal('3.0'),
             'Shape the age of intelligent systems', Decimal('50.00'), Decimal('9250.00'),
             '£42K–£70K', 95, 'violet', 'purple', 'brain-circuit', True),
            (programs[5], departments[3], faculties[1],
             'BEng Civil Engineering', 'AC-BENG-CVE',
             'undergraduate', ['full_time'], Decimal('4.0'),
             'Design the world around us', Decimal('50.00'), Decimal('9250.00'),
             '£38K–£60K', 90, 'orange', 'amber', 'building', False),
            (programs[7], departments[6], faculties[2],
             'BSc Finance & Accounting', 'AC-BSC-FNA',
             'undergraduate', ['full_time', 'part_time', 'online'], Decimal('3.0'),
             'Master money and markets', Decimal('50.00'), Decimal('9250.00'),
             '£34K–£60K', 88, 'green', 'emerald', 'pound-sterling', True),
            (programs[8], departments[6], faculties[2],
             'Master of Business Administration (Finance)', 'AC-MBA-FIN',
             'masters', ['full_time', 'part_time'], Decimal('1.0'),
             'Lead with financial intelligence', Decimal('100.00'), Decimal('17500.00'),
             '£65K–£110K', 92, 'emerald', 'teal', 'trending-up', True),
            (programs[9], departments[9], faculties[3],
             'Bachelor of Science in Nursing', 'AC-BSC-NRS',
             'undergraduate', ['full_time'], Decimal('3.0'),
             'Care with compassion and expertise', Decimal('50.00'), Decimal('9250.00'),
             '£28K–£45K', 99, 'red', 'rose', 'heart-pulse', True),
            (programs[10], departments[11], faculties[4],
             'BA English & Creative Writing', 'AC-BA-ECW',
             'undergraduate', ['full_time', 'part_time'], Decimal('3.0'),
             'Find your voice, shape the world', Decimal('50.00'), Decimal('9250.00'),
             '£25K–£40K', 80, 'purple', 'violet', 'pen-line', False),
            (programs[11], departments[12], faculties[4],
             'BA Digital Media & Design', 'AC-BA-DMD',
             'undergraduate', ['full_time', 'blended'], Decimal('3.0'),
             'Create the visual language of tomorrow', Decimal('50.00'), Decimal('9250.00'),
             '£27K–£45K', 84, 'pink', 'rose', 'image', False),
        ]
        academic_courses = []
        for (prog, dept, fac, name, code, degree, modes, dur,
             tagline, app_fee, tuit, salary, placement,
             col1, col2, icon, featured) in ac_raw:
            c = Course.objects.create(
                program=prog, department=dept, faculty=fac,
                name=name, code=code, degree_level=degree,
                available_study_modes=modes, duration_years=dur,
                tagline=tagline, application_fee=app_fee, tuition_fee=tuit,
                overview=fake.text(max_nb_chars=400),
                description=fake.text(max_nb_chars=800),
                learning_outcomes=[
                    f"Demonstrate advanced knowledge of {name.split()[-1]}",
                    "Apply theoretical concepts to practical industry problems",
                    "Develop professional communication and teamwork skills",
                    "Conduct independent research in your discipline",
                    "Meet ethical and professional standards of the field",
                ],
                career_paths=[
                    f"Graduate {name.split()[-1]} Professional",
                    f"Senior {name.split()[-1]} Consultant",
                    f"{name.split()[-1]} Manager",
                    f"Head of {name.split()[-1]}",
                ],
                core_courses=[
                    f"Introduction to {name.split()[-1]}",
                    f"Advanced {name.split()[-2]} Theory",
                    "Research Methods",
                    "Capstone Project",
                    "Professional Ethics and Practice",
                ],
                specialization_tracks=[
                    f"{fake.word().title()} Track",
                    f"{fake.word().title()} Specialisation",
                ],
                entry_requirements=[
                    "UCAS tariff: 112–128 points",
                    "A-Levels: including a relevant subject",
                    "IELTS 6.0 (or equivalent) for international applicants",
                ],
                avg_starting_salary=salary,
                job_placement_rate=placement,
                credits_required=360,
                color_primary=col1, color_secondary=col2, icon=icon,
                meta_description=f"{name} at MIU — {tagline}",
                meta_keywords=f"{name}, {degree}, MIU, university",
                is_active=True, is_featured=featured,
                display_order=len(academic_courses),
            )
            academic_courses.append(c)

        # ── 11. COURSE INTAKES ───────────────────────────────────────────────
        self.stdout.write("📅 Creating course intakes...")
        intakes = []
        period_months = {'january': 1, 'may': 5, 'september': 9}
        for course in academic_courses:
            for period, month in period_months.items():
                for year in [2025, 2026]:
                    deadline = date(year, month, 1) - timedelta(days=45)
                    intakes.append(CourseIntake.objects.create(
                        course=course, intake_period=period, year=year,
                        start_date=date(year, month, 15),
                        application_deadline=deadline,
                        available_slots=random.randint(30, 100),
                        is_active=True,
                    ))

        # ── 12. ALL REQUIRED PAYMENTS ────────────────────────────────────────
        self.stdout.write("💷 Creating required payments...")
        payment_purposes = [
            ('School Fees', 'student', Decimal('9250.00')),
            ('Library Fees', 'student', Decimal('120.00')),
            ('Laboratory Fees', 'student', Decimal('350.00')),
            ('Student Union Fee', 'student', Decimal('80.00')),
            ('Examination Fee', 'student', Decimal('200.00')),
            ('Staff Development Levy', 'staff', Decimal('150.00')),
            ('Application Processing Fee', 'applicant', Decimal('50.00')),
        ]
        for fac in faculties:
            fac_depts = [d for d in departments if d.faculty == fac]
            fac_progs = [p for p in programs if p.department.faculty == fac]
            fac_courses = [c for c in academic_courses if c.faculty == fac]
            for purpose, who, amount in payment_purposes:
                AllRequiredPayments.objects.create(
                    faculty=fac,
                    department=random.choice(fac_depts) if fac_depts else departments[0],
                    program=random.choice(fac_progs) if fac_progs else None,
                    course=random.choice(fac_courses) if fac_courses else None,
                    purpose=purpose, who_to_pay=who, amount=amount,
                    due_date=date(2025, 9, 30),
                    academic_year='2025/2026',
                    semester=random.choice(['first', 'second', 'annual']),
                    is_active=True,
                )

        # ── 13. COURSE APPLICATIONS ──────────────────────────────────────────
        self.stdout.write("📝 Creating course applications...")
        applications = []
        for student in verified_students:
            course = random.choice(academic_courses)
            intake = random.choice([i for i in intakes if i.course == course])
            status = random.choice([
                'draft', 'pending_payment', 'payment_complete',
                'under_review', 'approved', 'rejected',
            ])
            is_approved = status == 'approved'
            admitted = is_approved and random.random() > 0.4
            dept_approved = admitted and random.random() > 0.5
            adm_number = (
                f"ADM-{timezone.now().year}-{uuid.uuid4().hex[:8].upper()}"
                if admitted else None
            )
            app = CourseApplication.objects.create(
                user=student, course=course, intake=intake,
                study_mode=random.choice(course.available_study_modes),
                first_name=student.first_name, last_name=student.last_name,
                email=student.email,
                phone=fake.phone_number()[:20],
                date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=35),
                gender=random.choice(['male', 'female', 'other']),
                nationality=fake.country(),
                address_line1=fake.street_address(),
                address_line2=fake.secondary_address() if random.random() > 0.5 else '',
                city=fake.city(), state=fake.state(), postal_code=fake.postcode(),
                country=fake.country(),
                highest_qualification=random.choice(
                    ['High School', 'Associate Degree', 'Bachelor Degree']
                ),
                institution_name=fake.company(),
                graduation_year=str(random.randint(2015, 2024)),
                gpa_or_grade=f"{random.uniform(2.5, 4.0):.2f}",
                language_skill=random.choice(['ielts', 'toefl', 'pte', 'cambridge', 'none']),
                language_score=Decimal(str(round(random.uniform(5.5, 9.0), 1)))
                if random.random() > 0.3 else None,
                work_experience_years=random.randint(0, 10),
                personal_statement=fake.text(max_nb_chars=800),
                how_did_you_hear=random.choice(
                    ['Social Media', 'Friend', 'Website', 'Advertisement', 'Open Day']
                ),
                scholarship=random.choice([True, False]),
                accept_privacy_policy=True,
                accept_terms_conditions=True,
                marketing_consent=random.choice([True, False]),
                emergency_contact_name=fake.name(),
                emergency_contact_phone=fake.phone_number()[:20],
                emergency_contact_relationship=random.choice(
                    ['Parent', 'Sibling', 'Spouse', 'Guardian']
                ),
                status=status,
                reviewer=random.choice(verified_admins) if random.random() > 0.5 else None,
                review_notes=fake.text(max_nb_chars=200) if random.random() > 0.5 else '',
                submitted_at=timezone.now() - timedelta(days=random.randint(1, 90))
                if status != 'draft' else None,
                payment_status=random.choice(['pending', 'completed', 'failed']),
                admission_accepted=admitted,
                admission_accepted_at=timezone.now() - timedelta(days=random.randint(1, 30))
                if admitted else None,
                admission_number=adm_number,
                department_approved=dept_approved,
                department_approved_at=timezone.now() - timedelta(days=random.randint(1, 15))
                if dept_approved else None,
                department_approved_by=random.choice(verified_admins) if dept_approved else None,
                in_processing=status in ['under_review', 'payment_complete'],
            )
            applications.append(app)

        # ── 14. APPLICATION DOCUMENTS ────────────────────────────────────────
        self.stdout.write("📎 Creating application documents...")
        for app in applications:
            for doc_type in random.sample(
                ['transcript', 'certificate', 'cv', 'passport', 'id_document', 'recommendation'],
                k=random.randint(2, 5)
            ):
                ApplicationDocument.objects.create(
                    application=app, file_type=doc_type,
                    original_filename=f"{doc_type}_{uuid.uuid4().hex[:6]}.pdf",
                    file_size=random.randint(100_000, 5_000_000),
                )

        # ── 15. APPLICATION PAYMENTS ─────────────────────────────────────────
        self.stdout.write("💰 Creating application payments...")
        for app in [a for a in applications
                    if a.status in ['payment_complete', 'under_review', 'approved']]:
            ApplicationPayment.objects.create(
                application=app,
                amount=app.course.application_fee,
                currency='GBP',
                status='success',
                payment_method=random.choice(['card', 'paypal', 'bank_transfer']),
                gateway_payment_id=f"pi_{uuid.uuid4().hex[:24]}",
                card_last4=str(random.randint(1000, 9999)),
                card_brand=random.choice(['Visa', 'Mastercard', 'Amex']),
                paid_at=timezone.now() - timedelta(days=random.randint(1, 60)),
                payment_metadata={
                    'stripe_charge_id': f"ch_{uuid.uuid4().hex[:24]}",
                    'ip_address': fake.ipv4(),
                    'device': random.choice(['desktop', 'mobile', 'tablet']),
                },
                failure_reason='',
            )

        # ── 16. COURSE CATEGORIES (LMS) ──────────────────────────────────────
        self.stdout.write("🗂️  Creating LMS course categories...")
        cat_raw = [
            ('Programming & Development', 'code', 'blue'),
            ('Data Science & Analytics', 'bar-chart', 'green'),
            ('Web Development', 'globe', 'purple'),
            ('Mobile Development', 'smartphone', 'cyan'),
            ('Artificial Intelligence', 'brain', 'pink'),
            ('Cybersecurity', 'shield', 'red'),
            ('Cloud Computing', 'cloud', 'sky'),
            ('DevOps & Infrastructure', 'server', 'gray'),
            ('Design & UX', 'palette', 'orange'),
            ('Business & Marketing', 'trending-up', 'emerald'),
        ]
        categories = []
        for idx, (name, icon, color) in enumerate(cat_raw):
            categories.append(CourseCategory.objects.create(
                name=name, description=fake.text(max_nb_chars=200),
                icon=icon, color=color, display_order=idx, is_active=True,
            ))
        # Sub-categories
        for cat in categories[:3]:
            CourseCategory.objects.create(
                name=f"Advanced {cat.name}", parent=cat,
                description=fake.text(max_nb_chars=150),
                icon=cat.icon, color=cat.color,
                display_order=99, is_active=True,
            )

        # ── 17. LMS COURSES ──────────────────────────────────────────────────
        self.stdout.write("🎥 Creating LMS courses...")
        lms_templates = [
            ('Complete Python Programming Masterclass', categories[0], 'python',
             'beginner', Decimal('89.99'), 45.5,
             'Master Python from basics to advanced. OOP, data structures, file handling.'),
            ('Modern Web Development Bootcamp', categories[2], 'web_dev',
             'intermediate', Decimal('99.99'), 52.0,
             'HTML, CSS, JavaScript, and modern frameworks for professional websites.'),
            ('Data Science & Machine Learning A-Z', categories[1], 'data_science',
             'intermediate', Decimal('119.99'), 68.5,
             'Comprehensive data science with statistics, Python, ML, and real projects.'),
            ('Deep Learning & Neural Networks', categories[4], 'machine_learning',
             'advanced', Decimal('149.99'), 72.0,
             'Advanced deep learning covering CNNs, RNNs, GANs and modern architectures.'),
            ('JavaScript: Zero to Hero', categories[0], 'javascript',
             'beginner', Decimal('79.99'), 38.0,
             'Complete JavaScript for beginners. Fundamentals to interactive web apps.'),
            ('React – The Complete Guide', categories[2], 'react',
             'intermediate', Decimal('94.99'), 48.5,
             'Comprehensive React with hooks, context, Redux, and advanced patterns.'),
            ('UI/UX Design Fundamentals', categories[8], 'design',
             'beginner', Decimal('69.99'), 32.0,
             'User interface and user experience design principles and tools.'),
            ('Business Strategy & Entrepreneurship', categories[9], 'business',
             'intermediate', Decimal('84.99'), 41.0,
             'Business strategy, market analysis, and entrepreneurship fundamentals.'),
            ('Advanced Python for Data Science', categories[1], 'python',
             'advanced', Decimal('129.99'), 55.5,
             'Advanced Python techniques: pandas, numpy, scikit-learn.'),
            ('Full Stack Web Development', categories[2], 'web_dev',
             'advanced', Decimal('139.99'), 78.0,
             'Full-stack development: frontend, backend, databases, and deployment.'),
        ]
        lms_courses = []
        instructor_course_map = {}
        for idx, (title, cat, vtype, diff, price, dur, desc) in enumerate(lms_templates):
            instructor = users['instructors'][idx % len(users['instructors'])]
            lc = LMSCourse.objects.create(
                title=title,
                code=f"LMS{idx + 1:03d}",
                category=cat,
                short_description=desc[:500],
                description='\n\n'.join([fake.text(max_nb_chars=400) for _ in range(4)]),
                learning_objectives=[
                    f"Understand core concepts of {title.split()[0]}",
                    "Apply skills to practical projects",
                    "Write clean, maintainable code/work",
                    "Build a portfolio project from scratch",
                ],
                prerequisites=['Basic computer knowledge'] if diff == 'beginner'
                else ['Completion of beginner course', 'Programming fundamentals'],
                difficulty_level=diff,
                duration_hours=Decimal(str(dur)),
                language='English',
                instructor=instructor,
                instructor_name=instructor.get_full_name(),
                instructor_bio=fake.text(max_nb_chars=300),
                is_free=False,
                price=price,
                discount_price=price - Decimal('15.00') if random.random() > 0.5 else None,
                max_students=random.choice([50, 100, 200, None]),
                enrollment_start_date=date(2025, 1, 1),
                enrollment_end_date=date(2025, 12, 31),
                is_published=True,
                is_featured=random.random() > 0.6,
                has_certificate=True,
                certificate_template=f"template_{random.choice(['gold', 'silver', 'standard'])}",
                meta_description=desc[:160],
                meta_keywords=f"{title}, {diff}, online course, {cat.name}",
            )
            lms_courses.append(lc)
            instructor_course_map.setdefault(instructor, []).append(lc)

        # ── 18. LESSON SECTIONS & LESSONS ────────────────────────────────────
        self.stdout.write("📹 Creating lesson sections and lessons...")
        section_titles = [
            'Getting Started', 'Core Concepts', 'Intermediate Topics',
            'Advanced Techniques', 'Real-World Projects', 'Assessment & Review',
        ]
        lesson_type_pool = ['video', 'video', 'video', 'text', 'quiz', 'assignment']
        for lc in lms_courses:
            vid_key = next(
                (k for k in YOUTUBE_VIDEOS if k in lc.title.lower()), 'python'
            )
            videos = YOUTUBE_VIDEOS.get(vid_key, YOUTUBE_VIDEOS['python'])
            for s_idx, s_title in enumerate(
                random.sample(section_titles, k=random.randint(3, 5))
            ):
                section = LessonSection.objects.create(
                    course=lc, title=s_title,
                    description=fake.text(max_nb_chars=200),
                    display_order=s_idx, is_active=True,
                )
                for l_idx in range(random.randint(3, 7)):
                    ltype = random.choice(lesson_type_pool)
                    Lesson.objects.create(
                        course=lc, section=section,
                        title=f"{s_title} – Part {l_idx + 1}: {fake.catch_phrase()}",
                        lesson_type=ltype,
                        description=fake.text(max_nb_chars=300),
                        content=fake.text(max_nb_chars=1000),
                        video_url=random.choice(videos) if ltype == 'video' else '',
                        video_duration_minutes=random.randint(8, 45) if ltype == 'video' else 0,
                        is_preview=(l_idx == 0),
                        is_active=True,
                        display_order=l_idx,
                    )

        # ── 19. ENROLLMENTS ──────────────────────────────────────────────────
        self.stdout.write("🎓 Creating enrollments...")
        enrollments = []
        for student in verified_students:
            for lc in random.sample(lms_courses, k=random.randint(2, 7)):
                status = random.choice(['active', 'active', 'completed', 'dropped'])
                progress = Decimal(str(round(random.uniform(0, 100), 2)))
                completed_at = (
                    timezone.now() - timedelta(days=random.randint(1, 60))
                    if status == 'completed' else None
                )
                enr = Enrollment.objects.create(
                    student=student, course=lc,
                    enrolled_by=random.choice(users['admins']) if random.random() > 0.5 else None,
                    status=status,
                    progress_percentage=progress,
                    completed_lessons=random.randint(0, 20),
                    current_grade=Decimal(str(round(random.uniform(50, 100), 2)))
                    if random.random() > 0.4 else None,
                    completed_at=completed_at,
                    last_accessed=timezone.now() - timedelta(hours=random.randint(1, 200)),
                )
                enrollments.append(enr)

        # ── 20. LESSON PROGRESS ──────────────────────────────────────────────
        self.stdout.write("📊 Creating lesson progress...")
        for enr in random.sample(enrollments, k=min(len(enrollments), 120)):
            lessons = list(enr.course.lessons.filter(is_active=True))
            n_done = int(len(lessons) * float(enr.progress_percentage) / 100)
            for lesson in lessons[:n_done]:
                LessonProgress.objects.create(
                    enrollment=enr, lesson=lesson,
                    is_completed=True,
                    completion_percentage=Decimal('100.00'),
                    time_spent_minutes=random.randint(10, 90),
                    video_progress_seconds=lesson.video_duration_minutes * 60
                    if lesson.lesson_type == 'video' else 0,
                    started_at=enr.enrolled_at + timedelta(hours=random.randint(1, 48)),
                    completed_at=timezone.now() - timedelta(days=random.randint(1, 30)),
                )
            remaining = lessons[n_done:]
            if remaining:
                lesson = remaining[0]
                LessonProgress.objects.create(
                    enrollment=enr, lesson=lesson,
                    is_completed=False,
                    completion_percentage=Decimal(str(round(random.uniform(10, 80), 2))),
                    time_spent_minutes=random.randint(5, 40),
                    video_progress_seconds=random.randint(60, 900),
                    started_at=timezone.now() - timedelta(hours=random.randint(1, 24)),
                    completed_at=None,
                )

        # ── 21. ASSIGNMENTS ──────────────────────────────────────────────────
        self.stdout.write("📝 Creating assignments...")
        assignments = []
        for instructor, courses in instructor_course_map.items():
            for lc in courses:
                for lesson in random.sample(
                    list(lc.lessons.all()), k=min(3, lc.lessons.count())
                ):
                    asgn = Assignment.objects.create(
                        lesson=lesson,
                        title=f"Assignment: {fake.catch_phrase()}",
                        description=fake.text(max_nb_chars=500),
                        instructions=fake.text(max_nb_chars=300),
                        max_score=Decimal('100.00'),
                        passing_score=Decimal('70.00'),
                        due_date=timezone.now() + timedelta(days=random.randint(7, 45)),
                        allow_late_submission=random.choice([True, False]),
                        late_penalty_percent=random.choice([0, 10, 20, 30]),
                        is_active=True,
                        display_order=len(assignments),
                    )
                    assignments.append(asgn)

        # ── 22. ASSIGNMENT SUBMISSIONS ────────────────────────────────────────
        self.stdout.write("📤 Creating assignment submissions...")
        for asgn in assignments:
            enrolled = list(
                Enrollment.objects.filter(course=asgn.lesson.course, status='active')
            )
            for enr in random.sample(enrolled, k=min(random.randint(2, 8), len(enrolled))):
                status = random.choice(['draft', 'submitted', 'submitted', 'graded', 'graded'])
                is_graded = status == 'graded'
                sub_at = timezone.now() - timedelta(days=random.randint(1, 20))
                AssignmentSubmission.objects.create(
                    assignment=asgn,
                    student=enr.student,
                    submission_text=fake.text(max_nb_chars=600),
                    score=Decimal(str(round(random.uniform(55, 100), 2))) if is_graded else None,
                    feedback=fake.text(max_nb_chars=300) if is_graded else '',
                    graded_by=asgn.lesson.course.instructor if is_graded else None,
                    graded_at=sub_at + timedelta(days=random.randint(1, 7)) if is_graded else None,
                    status=status,
                    is_late=random.random() > 0.8,
                    submitted_at=sub_at if status != 'draft' else None,
                )

        # ── 23. QUIZZES ──────────────────────────────────────────────────────
        self.stdout.write("❓ Creating quizzes...")
        quizzes = []
        for instructor, courses in instructor_course_map.items():
            for lc in courses:
                for lesson in random.sample(
                    list(lc.lessons.all()), k=min(2, lc.lessons.count())
                ):
                    quiz = Quiz.objects.create(
                        lesson=lesson,
                        title=f"Quiz: {fake.catch_phrase()}",
                        description=fake.text(max_nb_chars=200),
                        instructions='Read all questions carefully before answering.',
                        time_limit_minutes=random.choice([15, 30, 45, 60]),
                        passing_score=Decimal('70.00'),
                        max_attempts=random.choice([2, 3, 5]),
                        shuffle_questions=random.choice([True, False]),
                        show_correct_answers=random.choice([True, False]),
                        is_active=True,
                        display_order=len(quizzes),
                    )
                    quizzes.append(quiz)

        # ── 24. QUIZ QUESTIONS & ANSWERS ──────────────────────────────────────
        self.stdout.write("❔ Creating quiz questions and answers...")
        for quiz in quizzes:
            for i in range(random.randint(5, 12)):
                qtype = random.choice(
                    ['multiple_choice', 'multiple_choice', 'true_false', 'short_answer']
                )
                q = QuizQuestion.objects.create(
                    quiz=quiz, question_type=qtype,
                    question_text=fake.sentence() + '?',
                    explanation=fake.text(max_nb_chars=150) if random.random() > 0.4 else '',
                    points=Decimal(str(random.choice([1, 2, 5]))),
                    display_order=i, is_active=True,
                )
                if qtype == 'multiple_choice':
                    correct_idx = random.randint(0, 3)
                    for j in range(4):
                        QuizAnswer.objects.create(
                            question=q,
                            answer_text=fake.sentence(nb_words=6),
                            is_correct=(j == correct_idx),
                            display_order=j,
                        )
                elif qtype == 'true_false':
                    correct = random.choice([True, False])
                    QuizAnswer.objects.create(
                        question=q, answer_text='True',
                        is_correct=correct, display_order=0
                    )
                    QuizAnswer.objects.create(
                        question=q, answer_text='False',
                        is_correct=not correct, display_order=1
                    )

        # ── 25. QUIZ ATTEMPTS & RESPONSES ─────────────────────────────────────
        self.stdout.write("🎯 Creating quiz attempts and responses...")
        for quiz in random.sample(quizzes, k=min(len(quizzes), 40)):
            enrolled = list(
                Enrollment.objects.filter(course=quiz.lesson.course, status='active')
            )
            for enr in random.sample(enrolled, k=min(4, len(enrolled))):
                for _ in range(random.randint(1, 2)):
                    pct = Decimal(str(round(random.uniform(40, 100), 2)))
                    attempt = QuizAttempt.objects.create(
                        quiz=quiz, student=enr.student,
                        score=pct, max_score=Decimal('100.00'), percentage=pct,
                        is_completed=True,
                        passed=pct >= quiz.passing_score,
                        completed_at=timezone.now() - timedelta(days=random.randint(1, 30)),
                        time_taken_minutes=random.randint(5, quiz.time_limit_minutes or 45),
                    )
                    for q in quiz.questions.all():
                        answers = list(q.answers.all())
                        if answers:
                            sel = random.choice(answers)
                            QuizResponse.objects.create(
                                attempt=attempt, question=q,
                                selected_answer=sel,
                                text_response='',
                                is_correct=sel.is_correct,
                                points_earned=q.points if sel.is_correct else Decimal('0.00'),
                            )

        # ── 26. REVIEWS ──────────────────────────────────────────────────────
        self.stdout.write("⭐ Creating reviews...")
        for lc in lms_courses:
            enrolled = list(Enrollment.objects.filter(course=lc))
            for enr in random.sample(enrolled, k=min(random.randint(3, 10), len(enrolled))):
                Review.objects.create(
                    course=lc, student=enr.student,
                    rating=random.randint(3, 5),
                    review_text=fake.text(max_nb_chars=400),
                    is_approved=random.random() > 0.1,
                )

        # ── 27. CERTIFICATES ─────────────────────────────────────────────────
        self.stdout.write("🏆 Creating certificates...")
        completed = [
            e for e in enrollments if e.status == 'completed' and e.course.has_certificate
        ]
        for enr in completed:
            Certificate.objects.create(
                student=enr.student, course=enr.course,
                completion_date=(enr.completed_at or timezone.now()).date(),
                grade=random.choice(['A', 'A*', 'B', 'Merit', 'Distinction']),
                verification_code=uuid.uuid4(),
                is_verified=True,
            )

        # ── 28. TRANSACTIONS ─────────────────────────────────────────────────
        self.stdout.write("💳 Creating transactions...")
        for student in verified_students:
            for _ in range(random.randint(2, 6)):
                gw = random.choice(gateways)
                amt = Decimal(str(round(random.uniform(50, 300), 2)))
                status = random.choice(['pending', 'completed', 'completed', 'completed', 'failed'])
                txn_type = random.choice(['enrollment', 'subscription', 'refund'])
                Transaction.objects.create(
                    user=student, transaction_type=txn_type,
                    amount=amt, currency='GBP',
                    gateway=gw,
                    gateway_transaction_id=f"{gw.slug}_{uuid.uuid4().hex[:20]}",
                    status=status,
                    course=random.choice(lms_courses) if txn_type == 'enrollment' else None,
                    metadata={
                        'payment_method': random.choice(['card', 'paypal', 'bank_transfer']),
                        'card_last4': str(random.randint(1000, 9999)),
                        'card_brand': random.choice(['Visa', 'Mastercard', 'Amex']),
                        'description': f"Payment for {fake.catch_phrase()}",
                    },
                    completed_at=timezone.now() - timedelta(days=random.randint(1, 90))
                    if status == 'completed' else None,
                )

        # ── 29. INVOICES ─────────────────────────────────────────────────────
        self.stdout.write("🧾 Creating invoices...")
        completed_txns = list(Transaction.objects.filter(status='completed'))
        for txn in random.sample(completed_txns, k=min(40, len(completed_txns))):
            subtotal = txn.amount
            Invoice.objects.create(
                student=txn.user,
                course=txn.course if txn.course else None,
                subtotal=subtotal,
                tax_rate=Decimal('5.00'),
                discount_amount=Decimal('0.00'),
                currency='GBP',
                status='paid',
                due_date=(txn.completed_at + timedelta(days=30)).date()
                if txn.completed_at else timezone.now().date() + timedelta(days=30),
                paid_date=txn.completed_at.date() if txn.completed_at else None,
                notes=f"Invoice for transaction {txn.transaction_id}. Thank you for your payment.",
            )

        # ── 30. BADGES ───────────────────────────────────────────────────────
        self.stdout.write("🏅 Creating badges...")
        badge_raw = [
            ('First Course Completed', 'award', 'bronze', 10,
             'Complete your first course'),
            ('Quick Learner', 'zap', 'yellow', 20,
             'Complete a course in under 7 days'),
            ('Quiz Master', 'brain', 'purple', 15,
             'Score 100% on 5 quizzes'),
            ('Perfect Score', 'star', 'gold', 30,
             'Achieve 100% on a course final assessment'),
            ('Marathon Learner', 'flag', 'green', 25,
             'Complete 10 or more courses'),
            ('Assignment Pro', 'file-text', 'blue', 15,
             'Submit 20 assignments on time'),
            ('Community Helper', 'users', 'cyan', 20,
             'Contribute helpful replies to 10 discussions'),
            ('Early Bird', 'sunrise', 'orange', 10,
             'Complete lessons before 8 AM for 7 consecutive days'),
        ]
        badges = []
        for name, icon, color, points, criteria in badge_raw:
            badges.append(Badge.objects.create(
                name=name, icon=icon, color=color, points=points,
                criteria=criteria,
                description=f"Awarded for: {criteria.lower()}",
                is_active=True,
            ))

        # ── 31. STUDENT BADGES ────────────────────────────────────────────────
        self.stdout.write("🎖️  Awarding badges...")
        for student in verified_students:
            for badge in random.sample(badges, k=random.randint(1, 5)):
                StudentBadge.objects.create(
                    student=student, badge=badge,
                    awarded_by=random.choice(users['admins'] + users['instructors']),
                    reason=fake.sentence(),
                )

        # ── 32. BLOG CATEGORIES ───────────────────────────────────────────────
        self.stdout.write("📰 Creating blog categories...")
        blog_cat_raw = [
            ('Technology Trends', 'trending-up', 'blue'),
            ('Learning Tips', 'book-open', 'green'),
            ('Career Advice', 'briefcase', 'purple'),
            ('Student Success Stories', 'award', 'yellow'),
            ('University News', 'newspaper', 'red'),
            ('Research & Innovation', 'flask', 'cyan'),
        ]
        blog_categories = []
        for idx, (name, icon, color) in enumerate(blog_cat_raw):
            blog_categories.append(BlogCategory.objects.create(
                name=name, icon=icon, color=color,
                description=fake.text(max_nb_chars=200),
                display_order=idx, is_active=True,
            ))

        # ── 33. BLOG POSTS ────────────────────────────────────────────────────
        self.stdout.write("✍️  Creating blog posts...")
        authors = users['instructors'] + users['content_managers'] + users['admins']
        for author in authors:
            for _ in range(random.randint(1, 3)):
                status = random.choice(['published', 'published', 'draft', 'archived'])
                BlogPost.objects.create(
                    title=fake.catch_phrase(),
                    subtitle=fake.sentence(),
                    excerpt=fake.text(max_nb_chars=300),
                    content='\n\n'.join([fake.text(max_nb_chars=500) for _ in range(6)]),
                    category=random.choice(blog_categories),
                    tags=[fake.word() for _ in range(random.randint(2, 5))],
                    author=author,
                    author_name=author.get_full_name(),
                    author_title=fake.job(),
                    featured_image_alt=fake.sentence(nb_words=5),
                    read_time=random.randint(3, 15),
                    views_count=random.randint(10, 5000),
                    status=status,
                    is_featured=random.random() > 0.8,
                    publish_date=timezone.now() - timedelta(days=random.randint(1, 180)),
                    meta_keywords=', '.join([fake.word() for _ in range(4)]),
                )

        # ── 34. DISCUSSIONS & REPLIES ─────────────────────────────────────────
        self.stdout.write("💬 Creating discussions...")
        discussions = []
        for lc in lms_courses:
            enrolled_users = list(User.objects.filter(enrollments__course=lc))
            for _ in range(random.randint(2, 6)):
                if not enrolled_users:
                    break
                author = random.choice(enrolled_users)
                disc = Discussion.objects.create(
                    course=lc,
                    title=fake.sentence(),
                    content=fake.text(max_nb_chars=600),
                    author=author,
                    is_pinned=random.random() > 0.85,
                    is_locked=random.random() > 0.9,
                    views_count=random.randint(5, 300),
                )
                discussions.append(disc)
                repliers = [u for u in enrolled_users if u != author]
                for _ in range(random.randint(1, 8)):
                    if repliers:
                        parent_reply = DiscussionReply.objects.create(
                            discussion=disc,
                            author=random.choice(repliers),
                            content=fake.text(max_nb_chars=400),
                            is_solution=random.random() > 0.85,
                        )
                        if random.random() > 0.6 and repliers:
                            DiscussionReply.objects.create(
                                discussion=disc,
                                author=random.choice(repliers),
                                content=fake.text(max_nb_chars=200),
                                parent=parent_reply,
                                is_solution=False,
                            )

        # ── 35. STUDY GROUPS ──────────────────────────────────────────────────
        self.stdout.write("👥 Creating study groups...")
        study_groups = []
        for lc in random.sample(lms_courses, k=min(6, len(lms_courses))):
            for _ in range(random.randint(1, 2)):
                creator = random.choice(verified_students + verified_instructors)
                sg = StudyGroup.objects.create(
                    name=f"{lc.title} – Study Group {uuid.uuid4().hex[:4].upper()}",
                    description=fake.text(max_nb_chars=300),
                    course=lc,
                    max_members=random.randint(6, 20),
                    is_active=True,
                    is_public=random.choice([True, False]),
                    created_by=creator,
                )
                study_groups.append(sg)
                StudyGroupMember.objects.create(
                    study_group=sg, user=creator, role='admin', is_active=True,
                )
                enrolled_ids = list(
                    Enrollment.objects.filter(course=lc).values_list('student', flat=True)
                )
                for sid in random.sample(
                    enrolled_ids, k=min(sg.max_members - 1, len(enrolled_ids))
                ):
                    if sid != creator.id:
                        StudyGroupMember.objects.create(
                            study_group=sg,
                            user=User.objects.get(id=sid),
                            role=random.choice(['member', 'member', 'moderator']),
                            is_active=True,
                        )

        # ── 36. MESSAGES ──────────────────────────────────────────────────────
        self.stdout.write("✉️  Creating messages...")
        for user in verified_all:
            others = [u for u in all_users if u != user]
            for _ in range(random.randint(2, 5)):
                recipient = random.choice(others)
                is_read = random.choice([True, False])
                msg = Message.objects.create(
                    sender=user, recipient=recipient,
                    subject=fake.sentence(),
                    body=fake.text(max_nb_chars=500),
                    is_read=is_read,
                    read_at=timezone.now() - timedelta(hours=random.randint(1, 72))
                    if is_read else None,
                )
                if random.random() > 0.6:
                    Message.objects.create(
                        sender=recipient, recipient=user,
                        subject=f"Re: {msg.subject}",
                        body=fake.text(max_nb_chars=300),
                        parent=msg,
                        is_read=random.choice([True, False]),
                    )

        # ── 37. SUPPORT TICKETS ───────────────────────────────────────────────
        self.stdout.write("🎫 Creating support tickets...")
        tickets = []
        ticket_creators = (
            verified_students +
            random.sample(verified_instructors, k=min(3, len(verified_instructors)))
        )
        for creator in ticket_creators:
            for _ in range(random.randint(1, 3)):
                status = random.choice(
                    ['open', 'in_progress', 'waiting_response', 'resolved', 'closed']
                )
                ticket = SupportTicket.objects.create(
                    user=creator,
                    category=random.choice(['technical', 'account', 'course', 'payment', 'other']),
                    subject=fake.sentence(),
                    description=fake.text(max_nb_chars=600),
                    priority=random.choice(['low', 'normal', 'high', 'urgent']),
                    status=status,
                    assigned_to=random.choice(users['support']),
                    resolved_at=timezone.now() - timedelta(days=random.randint(1, 30))
                    if status in ['resolved', 'closed'] else None,
                )
                tickets.append(ticket)
                for _ in range(random.randint(1, 5)):
                    TicketReply.objects.create(
                        ticket=ticket,
                        author=random.choice([ticket.user, ticket.assigned_to]),
                        message=fake.text(max_nb_chars=400),
                        is_internal_note=random.random() > 0.75,
                    )

        # ── 38. NOTIFICATIONS ─────────────────────────────────────────────────
        self.stdout.write("🔔 Creating notifications...")
        ntypes = ['enrollment', 'assignment', 'grade', 'announcement',
                  'message', 'certificate', 'system']
        for user in verified_all:
            for _ in range(random.randint(4, 14)):
                is_read = random.choice([True, False])
                Notification.objects.create(
                    user=user,
                    notification_type=random.choice(ntypes),
                    title=fake.sentence(),
                    message=fake.text(max_nb_chars=250),
                    link=f"/courses/{random.randint(1, 10)}" if random.random() > 0.4 else '',
                    is_read=is_read,
                    read_at=timezone.now() - timedelta(hours=random.randint(1, 96))
                    if is_read else None,
                )

        # ── 39. ANNOUNCEMENTS ─────────────────────────────────────────────────
        self.stdout.write("📢 Creating announcements...")
        for creator in users['admins'] + users['instructors']:
            ann_type = random.choice(['system', 'course', 'category'])
            Announcement.objects.create(
                title=fake.sentence(),
                content=fake.text(max_nb_chars=600),
                announcement_type=ann_type,
                priority=random.choice(['low', 'normal', 'high', 'urgent']),
                course=random.choice(lms_courses) if ann_type == 'course' else None,
                category=random.choice(categories) if ann_type == 'category' else None,
                created_by=creator,
                is_active=random.random() > 0.15,
                publish_date=timezone.now() - timedelta(days=random.randint(1, 90)),
                expiry_date=timezone.now() + timedelta(days=random.randint(30, 120))
                if random.random() > 0.4 else None,
            )

        # ── 40. CONTACT MESSAGES ──────────────────────────────────────────────
        self.stdout.write("📧 Creating contact messages...")
        for _ in range(30):
            responder = random.choice(users['support']) if random.random() > 0.35 else None
            ContactMessage.objects.create(
                user=random.choice(verified_students) if random.random() > 0.5 else None,
                name=fake.name(), email=fake.email(),
                subject=random.choice(
                    ['admissions', 'programs', 'campus', 'financial', 'support', 'other']
                ),
                message=fake.text(max_nb_chars=600),
                is_read=random.choice([True, False]),
                responded=responder is not None,
                responded_by=responder,
                responded_at=timezone.now() - timedelta(days=random.randint(1, 20))
                if responder else None,
                created_at=timezone.now() - timedelta(days=random.randint(1, 120)),
            )

        # ── 41. AUDIT LOGS ────────────────────────────────────────────────────
        self.stdout.write("📋 Creating audit logs...")
        actions = ['create', 'update', 'delete', 'login', 'logout',
                   'access', 'export', 'permission_change']
        model_names = ['Course', 'User', 'Enrollment', 'Assignment',
                       'Payment', 'Review', 'Discussion', 'Application']
        for user in verified_all:
            for _ in range(random.randint(4, 12)):
                AuditLog.objects.create(
                    user=user,
                    action=random.choice(actions),
                    model_name=random.choice(model_names),
                    object_id=str(random.randint(1, 200)),
                    description=fake.sentence(),
                    ip_address=fake.ipv4(),
                    user_agent=fake.user_agent(),
                    extra_data={
                        'browser': random.choice(['Chrome', 'Firefox', 'Safari', 'Edge']),
                        'platform': random.choice(['Windows', 'Mac', 'Linux', 'iOS', 'Android']),
                        'location': fake.city(),
                        'session_id': uuid.uuid4().hex,
                    },
                )

        # ── 42. BROADCAST MESSAGES ────────────────────────────────────────────
        self.stdout.write("📡 Creating broadcast messages...")
        broadcast_creators = verified_admins + verified_content
        for subject, ftype, fvals, status in [
            ('Welcome to the New Academic Year!', 'all_users', {}, 'sent'),
            ('Important: Upcoming System Maintenance', 'all_users', {}, 'sent'),
            ('Application Deadline Reminder', 'application_status',
             {'application_statuses': ['draft', 'pending_payment']}, 'sent'),
            ('Enrolment Confirmation for New Students', 'enrollment_status',
             {'enrollment_statuses': ['active']}, 'sent'),
            ('Upcoming Events Newsletter', 'all_users', {}, 'draft'),
            ('Course Update Notification for Students', 'role',
             {'roles': ['student']}, 'sent'),
        ]:
            if ftype == 'all_users':
                emails = [u.email for u in verified_all]
            elif ftype == 'role':
                role = fvals.get('roles', ['student'])[0]
                emails = [u.email for u in verified_all if u.profile.role == role]
            elif ftype == 'application_status':
                statuses = fvals.get('application_statuses', [])
                emails = list({a.email for a in applications if a.status in statuses})
            elif ftype == 'enrollment_status':
                statuses = fvals.get('enrollment_statuses', [])
                emails = list({e.student.email for e in enrollments if e.status in statuses})
            else:
                emails = []
            BroadcastMessage.objects.create(
                subject=subject, message=fake.text(max_nb_chars=500),
                filter_type=ftype, filter_values=fvals,
                recipient_emails=emails,
                recipient_count=len(emails),
                status=status,
                created_by=random.choice(broadcast_creators),
                sent_at=timezone.now() - timedelta(days=random.randint(1, 30))
                if status == 'sent' else None,
                error_message='' if status != 'failed' else 'SMTP connection timeout',
            )

        # ── 43. STAFF PAYROLL ─────────────────────────────────────────────────
        self.stdout.write("💰 Creating staff payroll records (full 12-month history)...")
        finance_admin = users['finance'][0]
        approver = users['admins'][0]
        for staff in staff_users:
            for month in range(1, 13):
                base = Decimal(str(round(random.uniform(2500, 8000), 2)))
                allowances = Decimal(str(round(random.uniform(200, 1200), 2)))
                bonuses = Decimal(str(round(random.uniform(0, 1000), 2)))
                tax = Decimal(str(round(float(base + allowances + bonuses) * 0.2, 2)))
                other_ded = Decimal(str(round(random.uniform(50, 300), 2)))
                pstatus = random.choice(['paid', 'paid', 'paid', 'pending', 'processing'])
                StaffPayroll.objects.create(
                    staff=staff,
                    month=month,
                    year=2025,
                    base_salary=base,
                    allowances=allowances,
                    bonuses=bonuses,
                    tax_deduction=tax,
                    other_deductions=other_ded,
                    payment_status=pstatus,
                    payment_method=random.choice(
                        ['bank_transfer', 'check', 'mobile_money']
                    ),
                    payment_date=date(2025, month, random.randint(25, 28))
                    if pstatus == 'paid' else None,
                    bank_name=random.choice(
                        ['Barclays', 'HSBC', 'Lloyds', 'NatWest', 'Santander']
                    ),
                    account_number=str(random.randint(10_000_000, 99_999_999)),
                    notes=(
                        f"Monthly payroll for "
                        f"{date(2025, month, 1).strftime('%B %Y')}. "
                        f"Processed by finance team."
                    ),
                    created_by=finance_admin,
                    approved_by=approver if pstatus == 'paid' else None,
                    approved_at=timezone.now() - timedelta(days=random.randint(1, 28))
                    if pstatus == 'paid' else None,
                )

        # ── FINAL: UPDATE COURSE STATISTICS ──────────────────────────────────
        self.stdout.write("📊 Updating course statistics...")
        for lc in lms_courses:
            lc.update_statistics()

        # ── SUMMARY ───────────────────────────────────────────────────────────
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 70))
        self.stdout.write(self.style.SUCCESS(
            "✅  SEEDING COMPLETE — every table, every field populated"
        ))
        self.stdout.write(self.style.SUCCESS("=" * 70))
        rows = [
            ("Users", User.objects.count()),
            ("Faculties", Faculty.objects.count()),
            ("Departments", Department.objects.count()),
            ("Programs", Program.objects.count()),
            ("Academic Courses", Course.objects.count()),
            ("Required Payments", AllRequiredPayments.objects.count()),
            ("Course Intakes", CourseIntake.objects.count()),
            ("Applications", CourseApplication.objects.count()),
            ("Application Documents", ApplicationDocument.objects.count()),
            ("Application Payments", ApplicationPayment.objects.count()),
            ("LMS Courses", LMSCourse.objects.count()),
            ("Lesson Sections", LessonSection.objects.count()),
            ("Lessons", Lesson.objects.count()),
            ("Enrollments", Enrollment.objects.count()),
            ("Lesson Progress", LessonProgress.objects.count()),
            ("Assignments", Assignment.objects.count()),
            ("Submissions", AssignmentSubmission.objects.count()),
            ("Quizzes", Quiz.objects.count()),
            ("Quiz Questions", QuizQuestion.objects.count()),
            ("Quiz Attempts", QuizAttempt.objects.count()),
            ("Reviews", Review.objects.count()),
            ("Certificates", Certificate.objects.count()),
            ("Transactions", Transaction.objects.count()),
            ("Invoices", Invoice.objects.count()),
            ("Badges", Badge.objects.count()),
            ("Student Badges", StudentBadge.objects.count()),
            ("Blog Posts", BlogPost.objects.count()),
            ("Discussions", Discussion.objects.count()),
            ("Study Groups", StudyGroup.objects.count()),
            ("Messages", Message.objects.count()),
            ("Support Tickets", SupportTicket.objects.count()),
            ("Notifications", Notification.objects.count()),
            ("Announcements", Announcement.objects.count()),
            ("Contact Messages", ContactMessage.objects.count()),
            ("Audit Logs", AuditLog.objects.count()),
            ("Broadcast Messages", BroadcastMessage.objects.count()),
            ("Staff Payrolls", StaffPayroll.objects.count()),
            ("Payment Gateways", PaymentGateway.objects.count()),
            ("Subscription Plans", SubscriptionPlan.objects.count()),
            ("Subscriptions", Subscription.objects.count()),
            ("Vendors", Vendor.objects.count()),
            ("System Configs", SystemConfiguration.objects.count()),
        ]
        for label, count in rows:
            self.stdout.write(f"   {label:<32} {count}")
        self.stdout.write(self.style.SUCCESS("=" * 70 + "\n"))