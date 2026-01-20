import random
import uuid
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from faker import Faker
from eduweb.models import (
    UserProfile, ContactMessage, CourseApplication, CourseApplicationFile,
    Application, Payment, Vendor, Faculty, Course, BlogCategory, BlogPost
)

fake = Faker()

class Command(BaseCommand):
    help = 'Seeds the database with high-quality, unique, and bulky data'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Clearing existing data..."))
        
        # Deletion Order to respect Foreign Keys
        BlogPost.objects.all().delete()
        BlogCategory.objects.all().delete()
        Payment.objects.all().delete()
        Application.objects.all().delete()
        CourseApplicationFile.objects.all().delete()
        CourseApplication.objects.all().delete()
        Course.objects.all().delete()
        Faculty.objects.all().delete()
        ContactMessage.objects.all().delete()
        Vendor.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

        self.stdout.write(self.style.SUCCESS("Database cleared. Generating bulky data..."))

        # --- 1. USERS ---
        users = []
        for _ in range(12):
            user = User.objects.create_user(
                username=fake.unique.user_name(),
                email=fake.unique.email(),
                password='Password123!',
                first_name=fake.first_name(),
                last_name=fake.last_name()
            )
            users.append(user)
        self.stdout.write("- Created 12 Users")

        # --- 2. FACULTIES ---
        faculties = []
        faculty_defs = [
            ("Business & Management", "BUS", "briefcase"), ("Engineering & Tech", "ENG", "cpu"),
            ("Health Sciences", "MED", "heart-pulse"), ("Arts & Humanities", "ART", "palette"),
            ("Social Sciences", "SOC", "users"), ("Law & Governance", "LAW", "scale"),
            ("Natural Sciences", "SCI", "beaker"), ("Environmental Studies", "ENV", "leaf"),
            ("Architecture", "ARC", "layers"), ("Communication", "COM", "megaphone")
        ]

        for name, code, icon in faculty_defs:
            fac = Faculty.objects.create(
                name=name,
                code=code,
                icon=icon,
                tagline=fake.catch_phrase(),
                description="\n\n".join(fake.paragraphs(nb=10)),
                mission=fake.paragraph(nb_sentences=5),
                vision=fake.paragraph(nb_sentences=5),
                student_count=random.randint(1000, 5000),
                placement_rate=random.randint(80, 98),
                partner_count=random.randint(20, 100),
                international_faculty=random.randint(10, 40),
                accreditation=f"Fully accredited by the {fake.company()} and the International Education Board.",
                special_features=[fake.sentence() for _ in range(6)],
                meta_description=fake.text(max_nb_chars=160)
            )
            faculties.append(fac)
        self.stdout.write("- Created 10 Detailed Faculties")

        # --- 3. COURSES (Fixed Unique Code Logic) ---
        for fac in faculties:
            for i in range(2):
                # Using a combination of faculty code, index, and hex to ensure uniqueness
                unique_suffix = uuid.uuid4().hex[:4].upper()
                course_code = f"{fac.code}-{i+100}-{unique_suffix}"
                
                Course.objects.create(
                    name=f"{'Advanced' if i > 0 else 'Bachelor of'} {fac.name.split(' ')[0]} {fake.word().capitalize()}",
                    code=course_code,
                    faculty=fac,
                    degree_levels=["bachelor", "master"] if i == 0 else ["master", "phd"],
                    study_modes=["full-time", "hybrid", "online"],
                    duration_years=random.choice([2.0, 3.0, 4.0]),
                    credits_required=random.choice([120, 180, 240]),
                    tagline=fake.bs().capitalize(),
                    overview=fake.text(max_nb_chars=1200),
                    description="\n\n".join(fake.paragraphs(nb=15)),
                    learning_outcomes=[fake.sentence() for _ in range(10)],
                    career_paths=[fake.job() for _ in range(8)],
                    core_courses=[
                        {"code": f"MOD-{random.randint(10,99)}", "name": fake.catch_phrase(), "credits": 5} 
                        for _ in range(12)
                    ],
                    specialization_tracks=[fake.catch_phrase() for _ in range(5)],
                    undergraduate_requirements=[fake.sentence() for _ in range(5)],
                    intake_periods=["Fall 2025", "Spring 2026", "Fall 2026"],
                    avg_starting_salary=f"${random.randint(50, 120)}k",
                    job_placement_rate=random.randint(85, 100)
                )
        self.stdout.write("- Created 20 Massive Courses (Guaranteed Unique)")

        # --- 4. BLOG SYSTEM ---
        categories = []
        for cat_name in ["Campus News", "Research", "Student Life", "Alumni", "Global"]:
            cat = BlogCategory.objects.create(
                name=cat_name,
                description=fake.paragraph(),
                icon=random.choice(['book', 'globe', 'users', 'award'])
            )
            categories.append(cat)

        for _ in range(12):
            post = BlogPost(
                title=fake.sentence(nb_words=8),
                excerpt=fake.text(max_nb_chars=400),
                content="".join([f"<h3>{fake.sentence()}</h3><p>{p}</p>" for p in fake.paragraphs(nb=12)]),
                category=random.choice(categories),
                author=random.choice(users),
                status='published',
                is_featured=fake.boolean(chance_of_getting_true=25),
                publish_date=timezone.now()
            )
            post.save() # Model save handles unique slugification
        self.stdout.write("- Created 12 Rich-Text Blog Posts")

        # --- 5. APPLICATIONS & PAYMENTS ---
        for user in users[:8]:
            app = CourseApplication.objects.create(
                user=user,
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                phone=fake.phone_number(),
                date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=30),
                country=random.choice(['US', 'UK', 'CA', 'AU', 'IN']),
                gender='male',
                address=fake.address(),
                academic_history=[{
                    "school": fake.company(), 
                    "gpa": "3.9", 
                    "notes": fake.text(max_nb_chars=600)
                }],
                program='computer-science',
                degree_level='bachelor',
                study_mode='full-time',
                intake='fall-2025'
            )
            
            # Create corresponding Payment
            pay_app = Application.objects.create(
                user=user,
                full_name=f"{user.first_name} {user.last_name}",
                email=user.email,
                amount=150.00,
                status='paid'
            )
            Payment.objects.create(
                application=pay_app,
                amount=150.00,
                status='succeeded',
                stripe_payment_intent_id=f"pi_{uuid.uuid4().hex[:16]}",
                card_last4="4242",
                card_brand="Visa"
            )

        self.stdout.write(self.style.SUCCESS("Heavy data seeding successfully completed!"))