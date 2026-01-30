import random
import uuid
from decimal import Decimal
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
    help = 'Seeds every table ensuring Decimal types and required fields are handled'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Starting database injection..."))

        # --- 1. CLEANUP ---
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

        # --- 2. USERS ---
        users = []
        for i in range(25):
            u = User.objects.create_user(
                username=f"user_{i}_{uuid.uuid4().hex[:4]}",
                email=fake.unique.email(),
                password="12345",
                first_name=fake.first_name(), last_name=fake.last_name()
            )
            users.append(u)
            p = u.profile # Created by signal
            p.phone = fake.phone_number()[:20]
            p.city = fake.city()
            p.country = fake.country()
            p.save()

        # --- 3. FACULTIES & COURSES ---
        facs = [Faculty.objects.create(name=fake.unique.company(), code=fake.unique.bothify('??').upper()) for _ in range(5)]
        
        ac_courses = []
        for _ in range(15):
            ac = Course.objects.create(
                name=fake.unique.job(), code=fake.unique.bothify('???-###').upper(),
                faculty=random.choice(facs), degree_level='undergraduate',
                duration_years=4, application_fee=Decimal('50.00'), tuition_fee=Decimal('5000.00')
            )
            ac_courses.append(ac)
            CourseIntake.objects.create(course=ac, intake_period='january', year=2026, 
                                      start_date=timezone.now().date(), application_deadline=timezone.now().date())

        # --- 4. ADMISSIONS ---
        for _ in range(15):
            u, c = random.choice(users), random.choice(ac_courses)
            CourseApplication.objects.create(
                application_id=f"APP-{uuid.uuid4().hex[:8].upper()}",
                user=u, course=c, intake=c.intakes.first(),
                first_name=u.first_name, last_name=u.last_name, email=u.email,
                phone=u.profile.phone, date_of_birth="2000-01-01", gender='male',
                nationality='Nigerian', address_line1=fake.street_address(),
                city=fake.city(), country=fake.country(), study_mode='full_time',
                highest_qualification='High School', institution_name=fake.company(),
                graduation_year=2022, gpa_or_grade="3.5", status='approved',
                emergency_contact_name=fake.name(), emergency_contact_phone=fake.phone_number(),
                emergency_contact_relationship='Parent'
            )

        # --- 5. LMS SYSTEM ---
        lms_cats = [CourseCategory.objects.create(name=fake.unique.word().title()) for _ in range(5)]
        lms_courses = []
        for _ in range(15):
            lc = LMSCourse.objects.create(
                title=fake.unique.sentence(nb_words=4), code=fake.unique.bothify('LMS-###'),
                category=random.choice(lms_cats), instructor=random.choice(users),
                price=Decimal('100.00'), duration_hours=20, is_published=True
            )
            lms_courses.append(lc)
            sec = LessonSection.objects.create(course=lc, title="Module 1", display_order=1)
            les = Lesson.objects.create(course=lc, section=sec, title="Intro", lesson_type='text', display_order=1)
            
            q = Quiz.objects.create(lesson=les, title="Quiz 1", passing_score=70)
            qq = QuizQuestion.objects.create(quiz=q, question_text="Test?", question_type='multiple_choice')
            QuizAnswer.objects.create(question=qq, answer_text="Yes", is_correct=True)

        # --- 6. PROGRESS & FINANCIALS ---
        pg = PaymentGateway.objects.create(name="Stripe", gateway_type="stripe", is_active=True)
        
        for _ in range(20):
            u, c = random.choice(users), random.choice(lms_courses)
            if not Enrollment.objects.filter(student=u, course=c).exists():
                enr = Enrollment.objects.create(student=u, course=c, status='active')
                Review.objects.create(course=c, student=u, rating=5, review_text="Great!")
                
                # IMPORTANT: Passing Decimals to avoid Float vs Decimal error in Invoice.save()
                Invoice.objects.create(
                    student=u, subtotal=Decimal('100.00'), 
                    tax_rate=Decimal('0.00'), 
                    discount_amount=Decimal('0.00'),
                    total_amount=Decimal('100.00'),
                    status='paid', due_date=timezone.now().date()
                )
                
                Transaction.objects.create(
                    transaction_id=str(uuid.uuid4()), user=u, amount=Decimal('100.00'),
                    gateway=pg, status='completed', transaction_type='enrollment'
                )

        # --- 7. BLOG & SUPPORT ---
        bc = BlogCategory.objects.create(name="General")
        for _ in range(10):
            BlogPost.objects.create(title=fake.sentence(), category=bc, author=random.choice(users), status='published')
            SupportTicket.objects.create(ticket_id=f"TKT-{random.randint(100,999)}", user=random.choice(users), subject="Help")
            Announcement.objects.create(title=fake.sentence(), content="Announce")

        # --- 8. SYSTEM CONFIG ---
        SystemConfiguration.objects.create(key="site_name", value="Digital Campus", setting_type="text")
        Vendor.objects.create(name=fake.company(), email=fake.unique.email())

        self.stdout.write(self.style.SUCCESS("SUCCESS: Seeding complete without Decimal/Float errors."))