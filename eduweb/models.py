from django.db import models
from django.utils import timezone

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    email_verified = models.BooleanField(default=False)
    verification_token = models.UUIDField(default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def generate_verification_token(self):
        """Generate a new verification token"""
        self.verification_token = uuid.uuid4()
        self.save()
        return self.verification_token


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when User is created"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()

class ContactMessage(models.Model):
    SUBJECT_CHOICES = [
        ('admissions', 'Admissions Inquiry'),
        ('programs', 'Program Information'),
        ('campus', 'Campus Visit'),
        ('financial', 'Financial Aid'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=200)
    email = models.EmailField()
    subject = models.CharField(max_length=50, choices=SUBJECT_CHOICES)
    message = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    responded = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'
    
    def __str__(self):
        return f"{self.name} - {self.subject} ({self.created_at.strftime('%Y-%m-%d')})"
    
class CourseApplication(models.Model):
    DEGREE_LEVEL_CHOICES = [
        ('bachelor', "Bachelor's Degree"),
        ('master', "Master's Degree"),
        ('phd', 'PhD/Doctorate'),
    ]
    
    STUDY_MODE_CHOICES = [
        ('full-time', 'Full-time'),
        ('part-time', 'Part-time'),
        ('online', 'Online'),
        ('hybrid', 'Hybrid'),
    ]
    
    INTAKE_CHOICES = [
        ('fall-2025', 'Fall 2025'),
        ('spring-2026', 'Spring 2026'),
        ('fall-2026', 'Fall 2026'),
    ]
    
    PROGRAM_CHOICES = [
        ('business', 'Business Administration (MBA)'),
        ('computer-science', 'Computer Science'),
        ('data-science', 'Data Science'),
        ('engineering', 'Engineering'),
        ('health-sciences', 'Health Sciences'),
        ('psychology', 'Psychology'),
        ('economics', 'Economics'),
        ('law', 'Law'),
        ('arts', 'Arts & Humanities'),
    ]

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('non-binary', 'Non-binary'),
        ('prefer-not-to-say', 'Prefer not to say'),
    ]
    
    COUNTRY_CHOICES = [
        ('US', 'United States'),
        ('UK', 'United Kingdom'),
        ('CA', 'Canada'),
        ('AU', 'Australia'),
        ('IN', 'India'),
        ('CN', 'China'),
        ('NG', 'Nigeria'),
        ('BR', 'Brazil'),
        ('OTHER', 'Other'),
    ]
    
    REFERRAL_CHOICES = [
        ('', 'Select an option'),
        ('search-engine', 'Search Engine (Google, etc.)'),
        ('social-media', 'Social Media'),
        ('friend-family', 'Friend or Family'),
        ('education-fair', 'Education Fair'),
        ('school-counselor', 'School Counselor'),
        ('alumni', 'MIU Alumni'),
        ('other', 'Other'),
    ]
    
    # Personal Information
    application_id = models.CharField(max_length=50, unique=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    date_of_birth = models.DateField()
    country = models.CharField(max_length=100)
    gender = models.CharField(max_length=50)
    address = models.TextField()
    
    # Academic History (stored as JSON)
    academic_history = models.JSONField(default=list)
    english_proficiency = models.CharField(max_length=50, blank=True)
    english_score = models.CharField(max_length=20, blank=True)
    additional_qualifications = models.TextField(blank=True)
    
    # Course Selection
    program = models.CharField(max_length=50, choices=PROGRAM_CHOICES)
    degree_level = models.CharField(max_length=20, choices=DEGREE_LEVEL_CHOICES)
    study_mode = models.CharField(max_length=20, choices=STUDY_MODE_CHOICES)
    intake = models.CharField(max_length=20, choices=INTAKE_CHOICES)
    scholarship = models.BooleanField(default=False)
    
    # Additional Information
    referral_source = models.CharField(max_length=100, blank=True)
    
    # Document Upload Status (stored as JSON)
    documents_uploaded = models.JSONField(default=dict)
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    submitted = models.BooleanField(default=False)
    submission_date = models.DateTimeField(null=True, blank=True)
    is_reviewed = models.BooleanField(default=False)

    country = models.CharField(max_length=100, choices=COUNTRY_CHOICES)
    gender = models.CharField(max_length=50, choices=GENDER_CHOICES)
    referral_source = models.CharField(max_length=100, blank=True, choices=REFERRAL_CHOICES)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Course Application'
        verbose_name_plural = 'Course Applications'
    
    def __str__(self):
        return f"{self.application_id} - {self.first_name} {self.last_name}"
    
    def save(self, *args, **kwargs):
        # Generate application ID if not exists
        if not self.application_id:
            import random
            year = timezone.now().year
            self.application_id = f'MIU-{year}-{random.randint(10000, 99999)}'
        super().save(*args, **kwargs)
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_program_display_name(self):
        return dict(self.PROGRAM_CHOICES).get(self.program, self.program)
    
    def get_degree_level_display_name(self):
        return dict(self.DEGREE_LEVEL_CHOICES).get(self.degree_level, self.degree_level)
    
class CourseApplicationFile(models.Model):
    application = models.ForeignKey(
        CourseApplication, 
        related_name='extra_files', 
        on_delete=models.CASCADE
    )
    file = models.FileField(upload_to='applications/additional/')

    def __str__(self):
        return f"File for {self.application.first_name} {self.application.last_name}"