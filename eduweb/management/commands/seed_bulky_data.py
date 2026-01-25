import random
import uuid
import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from faker import Faker
from eduweb.models import (
    UserProfile, ContactMessage, Faculty, Course, CourseIntake,
    CourseApplication, ApplicationDocument, ApplicationPayment,
    Vendor, BlogCategory, BlogPost
)

fake = Faker()

class Command(BaseCommand):
    help = 'Seeds all database tables with realistic, interconnected data and image paths'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Starting total database reset..."))
        
        # 1. DELETE EXISTING DATA (Order handles ProtectedError)
        ApplicationPayment.objects.all().delete()
        ApplicationDocument.objects.all().delete()
        CourseApplication.objects.all().delete()
        CourseIntake.objects.all().delete()
        BlogPost.objects.all().delete()
        BlogCategory.objects.all().delete()
        Course.objects.all().delete()
        Faculty.objects.all().delete()
        ContactMessage.objects.all().delete()
        Vendor.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

        self.stdout.write(self.style.SUCCESS("Database cleared. Generating comprehensive data..."))

        # --- 2. USERS (Password: 12345) ---
        # UserProfile is created automatically via signals in models.py
        users = []
        for _ in range(15):
            user = User.objects.create_user(
                username=fake.unique.user_name(),
                email=fake.unique.email(),
                password='12345',
                first_name=fake.first_name(),
                last_name=fake.last_name()
            )
            users.append(user)
        self.stdout.write("- Created 15 Users (Profile auto-generated via signals)")

        # --- 3. FACULTIES ---
        faculties = []
        fac_configs = [
            ("School of Business", "BUS", "briefcase", "orange", "amber"),
            ("Engineering & Technology", "ENG", "cpu", "blue", "cyan"),
            ("Medical Sciences", "MED", "heart-pulse", "red", "rose"),
            ("Humanities & Arts", "ART", "palette", "purple", "violet"),
            ("Faculty of Law", "LAW", "scale", "slate", "gray")
        ]

        for name, code, icon, p_col, s_col in fac_configs:
            fac = Faculty.objects.create(
                name=name,
                code=code,
                icon=icon,
                color_primary=p_col,
                color_secondary=s_col,
                tagline=fake.catch_phrase(),
                description=fake.paragraph(nb_sentences=10),
                mission=fake.paragraph(),
                vision=fake.paragraph(),
                hero_image=f"faculties/heroes/{code.lower()}.jpg",
                about_image=f"faculties/about/{code.lower()}.jpg",
                student_count=random.randint(1200, 4500),
                placement_rate=random.randint(88, 99),
                partner_count=random.randint(25, 60),
                international_faculty=random.randint(15, 30),
                special_features=[fake.bs().title() for _ in range(5)],
                meta_description=fake.text(max_nb_chars=150)
            )
            faculties.append(fac)

        # --- 4. COURSES & INTAKES ---
        all_courses = []
        for fac in faculties:
            for i in range(3):
                unique_hex = uuid.uuid4().hex[:4].upper()
                c_name = f"{random.choice(['BSc', 'MSc', 'PhD'])} {fac.name.split(' ')[-1]} {fake.word().capitalize()}"
                
                course = Course.objects.create(
                    name=c_name,
                    code=f"{fac.code}-{100+i}-{unique_hex}",
                    faculty=fac,
                    degree_level=random.choice(['undergraduate', 'masters', 'phd']),
                    available_study_modes=["full_time", "online", "blended"],
                    duration_years=random.choice([1.0, 3.0, 4.0]),
                    credits_required=random.choice([120, 180, 240]),
                    tagline=fake.sentence(),
                    overview=fake.text(max_nb_chars=1000),
                    description="\n\n".join(fake.paragraphs(nb=12)),
                    learning_outcomes=[fake.sentence() for _ in range(6)],
                    career_paths=[fake.job() for _ in range(5)],
                    core_courses=[{"code": f"MOD{j}", "name": fake.catch_phrase(), "cr": 15} for j in range(6)],
                    entry_requirements=[fake.sentence() for _ in range(4)],
                    application_fee=75.00,
                    tuition_fee=random.randint(8000, 25000),
                    avg_starting_salary=f"${random.randint(45, 95)}k",
                    job_placement_rate=random.randint(85, 100),
                    hero_image=f"courses/heroes/c_{unique_hex.lower()}.jpg"
                )
                all_courses.append(course)

                # Create Multiple Intakes
                for p_code, p_name in [('january', 'Jan'), ('september', 'Sep')]:
                    CourseIntake.objects.create(
                        course=course,
                        intake_period=p_code,
                        year=2025,
                        start_date=timezone.now().date() + timezone.timedelta(days=150),
                        application_deadline=timezone.now().date() + timezone.timedelta(days=100),
                        available_slots=60
                    )

        # --- 5. APPLICATIONS, DOCUMENTS & PAYMENTS ---
        for user in users[:10]:
            target_course = random.choice(all_courses)
            target_intake = target_course.intakes.first()

            app = CourseApplication.objects.create(
                user=user,
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                phone=fake.phone_number(),
                country=random.choice(['US', 'UK', 'CA', 'NG', 'AU']),
                gender=random.choice(['male', 'female']),
                address=fake.address(),
                academic_history=[
                    {"inst": fake.company(), "grade": "First Class", "year": "2023"}
                ],
                course=target_course,
                intake=target_intake,
                study_mode='full_time',
                status='submitted',
                referral_source='social-media',
                personal_statement=fake.paragraph(nb_sentences=15)
            )

            # Link Document
            ApplicationDocument.objects.create(
                application=app,
                file_type='transcript',
                file=f'applications/{app.application_id}/transcript/cert.pdf',
                original_filename=f"{user.last_name}_transcript.pdf",
                file_size=512000
            )

            # Link Payment
            ApplicationPayment.objects.create(
                application=app,
                amount=target_course.application_fee,
                status='success',
                payment_method='stripe',
                payment_reference=f"PAY-{uuid.uuid4().hex[:12].upper()}",
                gateway_payment_id=f"pi_{uuid.uuid4().hex[:14]}",
                card_last4="4242",
                card_brand="MasterCard"
            )

        # --- 6. BLOG SYSTEM ---
        categories = []
        for cat_name in ["Research", "Campus Life", "Admissions", "Success Stories"]:
            cat = BlogCategory.objects.create(
                name=cat_name,
                description=fake.sentence(),
                icon=random.choice(['globe', 'users', 'award']),
                color=random.choice(['blue', 'indigo', 'rose'])
            )
            categories.append(cat)

        for _ in range(8):
            BlogPost.objects.create(
                title=fake.sentence(),
                subtitle=fake.sentence(),
                excerpt=fake.text(max_nb_chars=160),
                content="".join([f"<p>{p}</p>" for p in fake.paragraphs(nb=10)]),
                category=random.choice(categories),
                author=random.choice(users),
                status='published',
                is_featured=random.choice([True, False]),
                featured_image=f"blog/seed/post_{random.randint(1,10)}.jpg"
            )

        # --- 7. VENDORS & CONTACTS ---
        for _ in range(4):
            Vendor.objects.create(
                name=fake.company(),
                email=fake.company_email(),
                country=fake.country()
            )

        for _ in range(10):
            ContactMessage.objects.create(
                name=fake.name(),
                email=fake.email(),
                subject=random.choice(['admissions', 'financial', 'programs']),
                message=fake.text(max_nb_chars=800)
            )

        self.stdout.write(self.style.SUCCESS(f"TOTAL SEEDING COMPLETE!"))
        self.stdout.write("- All 11 models populated with real relationships.")
        self.stdout.write("- All image paths set for UI rendering.")
        self.stdout.write("- Password for all generated users: 12345")