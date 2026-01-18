from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid
import os

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
        ('website', 'University Website'),
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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications', null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    date_of_birth = models.DateField()
    country = models.CharField(max_length=100, choices=COUNTRY_CHOICES)
    gender = models.CharField(max_length=50, choices=GENDER_CHOICES)
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
    referral_source = models.CharField(max_length=100, blank=True, choices=REFERRAL_CHOICES)
    
    # Document Upload Status (stored as JSON)
    documents_uploaded = models.JSONField(default=dict)
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    submitted = models.BooleanField(default=False)
    submission_date = models.DateTimeField(null=True, blank=True)
        
    # Application Status Fields
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('reviewed', 'Reviewed'),
        ('decision_made', 'Decision Made'),
    ]
        
    DECISION_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('waitlisted', 'Waitlisted'),
    ]
        
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    decision = models.CharField(max_length=20, choices=DECISION_CHOICES, default='pending')
    decision_date = models.DateTimeField(null=True, blank=True)
    decision_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_applications')
    reviewed_at = models.DateTimeField(null=True, blank=True)
        
    # Keep for backwards compatibility
    is_reviewed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Course Application'
        verbose_name_plural = 'Course Applications'
    
    def __str__(self):
        return f"{self.application_id} - {self.first_name} {self.last_name}"
    
    def save(self, *args, **kwargs):
        # Generate application ID if not exists
        if not self.application_id:
            year = timezone.now().year
            # First save to get the auto-generated ID
            super().save(*args, **kwargs)
            # Format: MIU-YEAR-ID (e.g., MIU-2025-0001)
            self.application_id = f'MIU-{year}-{str(self.id).zfill(4)}'
            # Save again with the formatted ID
            super().save(*args, **kwargs)
            return
        super().save(*args, **kwargs)
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_program_display_name(self):
        return dict(self.PROGRAM_CHOICES).get(self.program, self.program)
    
    def get_degree_level_display_name(self):
        return dict(self.DEGREE_LEVEL_CHOICES).get(self.degree_level, self.degree_level)


def application_file_upload_path(instance, filename):
    """
    Generate upload path for application files
    Format: applications/{application_id}/{file_type}/{filename}
    """
    # Clean the filename
    name, ext = os.path.splitext(filename)
    # Create safe filename
    safe_filename = f"{name}{ext}"
    
    # Get file type from instance
    file_type = instance.file_type or 'other'
    
    return f'applications/{instance.application.application_id}/{file_type}/{safe_filename}'


class CourseApplicationFile(models.Model):
    FILE_TYPE_CHOICES = [
        ('transcripts', 'Transcripts'),
        ('english_proficiency', 'English Proficiency Certificate'),
        ('personal_statement', 'Personal Statement'),
        ('cv', 'CV/Resume'),
        ('other', 'Other Document'),
    ]
    
    application = models.ForeignKey(
        CourseApplication, 
        related_name='files', 
        on_delete=models.CASCADE
    )
    file = models.FileField(upload_to=application_file_upload_path)
    file_type = models.CharField(max_length=50, choices=FILE_TYPE_CHOICES, default='other')
    uploaded_at = models.DateTimeField(default=timezone.now())
    original_filename = models.CharField(max_length=255, blank=True)
    file_size = models.IntegerField(default=0)  # in bytes
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Application File'
        verbose_name_plural = 'Application Files'
    
    def __str__(self):
        return f"{self.get_file_type_display()} - {self.application.application_id}"
    
    def save(self, *args, **kwargs):
        # Store original filename if not set
        if not self.original_filename and self.file:
            self.original_filename = self.file.name
        
        # Store file size if not set
        if not self.file_size and self.file:
            try:
                self.file_size = self.file.size
            except:
                pass
        
        super().save(*args, **kwargs)
    
    def get_file_size_display(self):
        """Return human-readable file size"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


   ########## PAYMENT GATEWAY #########

from django.core.validators import MinValueValidator

class Application(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    status = models.CharField(max_length=50, default='pending_payment')
    created_at = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, default='pending')
    stripe_payment_intent_id = models.CharField(max_length=255, null=True, blank=True)
    card_last4 = models.CharField(max_length=4, null=True, blank=True)
    card_brand = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)


class Vendor(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    stripe_account_id = models.CharField(
        max_length=255, blank=True, null=True
    )  # Stripe Connect (future)

    def __str__(self):
        return self.name
