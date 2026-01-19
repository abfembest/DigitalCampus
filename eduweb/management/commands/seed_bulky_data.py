import random
import uuid
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from faker import Faker
from eduweb.models import (
    UserProfile, ContactMessage, CourseApplication, CourseApplicationFile,
    Application, Payment, Vendor, Faculty, Course
)

fake = Faker()

class Command(BaseCommand):
    help = 'Seeds the database with 10 records per table using massive, realistic data'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Clearing existing data for a clean bulky seed..."))
        
        # Clear tables to prevent UNIQUE constraint errors
        CourseApplicationFile.objects.all().delete()
        CourseApplication.objects.all().delete()
        Payment.objects.all().delete()
        Application.objects.all().delete()
        Course.objects.all().delete()
        Faculty.objects.all().delete()
        ContactMessage.objects.all().delete()
        Vendor.objects.all().delete()
        # Keep admin users, delete generated ones
        User.objects.filter(is_superuser=False).delete()

        self.stdout.write(self.style.SUCCESS("Database cleared. Starting heavy data seed..."))

        # 1. Create 10 Users
        users = []
        for i in range(10):
            user = User.objects.create_user(
                username=fake.unique.user_name(),
                email=fake.unique.email(),
                password='Password123!',
                first_name=fake.first_name(),
                last_name=fake.last_name()
            )
            users.append(user)
        self.stdout.write("- Created 10 Users")

        # 2. Bulky Contact Messages
        for _ in range(10):
            ContactMessage.objects.create(
                name=fake.name(),
                email=fake.email(),
                subject=random.choice(['admissions', 'programs', 'financial']),
                message=fake.text(max_nb_chars=3000), 
                is_read=fake.boolean()
            )
        self.stdout.write("- Created 10 Bulky Contact Messages")

        # 3. Bulky Faculties
        faculties = []
        # Using a list but adding a random suffix to ensure slug uniqueness if run multiple times
        f_names = ["Engineering", "Business", "Medicine", "Arts", "Law", "Tech", "Science", "Music", "Nursing", "Design"]
        for name in f_names:
            fac = Faculty.objects.create(
                name=f"Faculty of {name}",
                code=f"{name[:3].upper()}{random.randint(100, 999)}",
                tagline=fake.catch_phrase(),
                description=fake.paragraphs(nb=12), 
                mission=fake.text(max_nb_chars=1000),
                vision=fake.text(max_nb_chars=1000),
                student_count=random.randint(1000, 5000),
                accreditation=fake.text(max_nb_chars=800),
                special_features=[fake.sentence() for _ in range(6)]
            )
            faculties.append(fac)
        self.stdout.write("- Created 10 Detailed Faculties")

        # 4. Bulky Courses
        for fac in faculties:
            # One course per faculty to keep it to 10 total
            Course.objects.create(
                name=f"Advanced {fac.name.split()[-1]} Degree",
                faculty=fac,
                code=f"{fac.code}-X{random.randint(10, 99)}",
                degree_levels=["bachelor", "master"],
                study_modes=["full-time", "online", "hybrid"],
                overview=fake.text(max_nb_chars=1500),
                description=fake.paragraphs(nb=20),
                learning_outcomes=[fake.paragraph(nb_sentences=3) for _ in range(8)],
                career_paths=[fake.job() for _ in range(10)],
                core_courses=[{"title": fake.catch_phrase(), "desc": fake.sentence(nb_words=20)} for _ in range(12)],
                undergraduate_requirements=[fake.sentence(nb_words=15) for _ in range(5)],
                intake_periods=["Fall 2025", "Spring 2026"]
            )
        self.stdout.write("- Created 10 Massive Course Programs")

        # 5. Complex Course Applications
        for user in users:
            app = CourseApplication.objects.create(
                user=user,
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                phone=fake.phone_number(),
                date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=30),
                country='US',
                gender='male',
                address=fake.address(),
                academic_history=[{"institution": fake.company(), "gpa": "3.8", "narrative": fake.text(max_nb_chars=500)}],
                additional_qualifications=fake.text(max_nb_chars=2000),
                program='computer-science',
                degree_level='bachelor',
                intake='fall-2025'
            )
            CourseApplicationFile.objects.create(
                application=app,
                file_type='personal_statement',
                original_filename=f"statement_{user.username}.pdf",
                file_size=random.randint(1024, 1048576)
            )
        self.stdout.write("- Created 10 Complex Applications & Files")

        # 6. Payments
        for _ in range(10):
            Vendor.objects.create(name=fake.company(), email=fake.company_email())

        for user in users:
            pay_app = Application.objects.create(
                user=user,
                full_name=f"{user.first_name} {user.last_name}",
                email=user.email,
                amount=random.randint(50, 500),
                status='paid'
            )
            Payment.objects.create(
                application=pay_app,
                amount=pay_app.amount,
                status='succeeded',
                stripe_payment_intent_id=f"pi_{uuid.uuid4().hex[:16]}",
                card_last4="4242",
                card_brand="Visa"
            )

        self.stdout.write(self.style.SUCCESS("Bulky data seeding completed!"))