from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify
from django.core.validators import MinValueValidator
import uuid
import os

# ==================== USER PROFILE ====================
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
        self.verification_token = uuid.uuid4()
        self.save()
        return self.verification_token


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()


# ==================== CONTACT ====================
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


# ==================== FACULTIES & COURSES ====================
class Faculty(models.Model):
    name = models.CharField(max_length=200, help_text="Faculty name (e.g., Faculty of Business)")
    slug = models.SlugField(max_length=200, unique=True, help_text="URL-friendly name")
    code = models.CharField(max_length=20, unique=True, help_text="Faculty code (e.g., BUS, ENG)")
    
    # Display Information
    icon = models.CharField(max_length=50, default='graduation-cap', help_text="Lucide icon name")
    color_primary = models.CharField(max_length=20, default='orange', help_text="Primary color")
    color_secondary = models.CharField(max_length=20, default='amber', help_text="Secondary color")
    
    # Content
    tagline = models.CharField(max_length=200, help_text="Short tagline for hero section")
    description = models.TextField(help_text="Main description of the faculty")
    mission = models.TextField(blank=True, help_text="Faculty mission statement")
    vision = models.TextField(blank=True, help_text="Faculty vision statement")
    
    # Media
    hero_image = models.ImageField(upload_to='faculties/heroes/', blank=True, null=True)
    about_image = models.ImageField(upload_to='faculties/about/', blank=True, null=True)
    
    # Statistics
    student_count = models.IntegerField(default=0, help_text="Number of students")
    placement_rate = models.IntegerField(default=0, help_text="Career placement rate (0-100)")
    partner_count = models.IntegerField(default=0, help_text="Number of corporate partners")
    international_faculty = models.IntegerField(default=0, help_text="International faculty percentage")
    
    # Accreditation & Features
    accreditation = models.TextField(blank=True, help_text="Accreditation details")
    special_features = models.JSONField(default=list, blank=True, help_text="List of special features")
    
    # SEO
    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Faculty'
        verbose_name_plural = 'Faculties'
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Course(models.Model):
    """
    Unified course model - represents actual academic programs offered.
    Removed ProspectiveCourse as it was redundant.
    """
    DEGREE_LEVEL_CHOICES = [
        ('certificate', 'Certificate'),
        ('diploma', 'Diploma'),
        ('undergraduate', 'Undergraduate'),
        ('postgraduate', 'Postgraduate'),
        ('masters', 'Masters'),
        ('phd', 'PhD')
    ]

    STUDY_MODE_CHOICES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('online', 'Online'),
        ('blended', 'Blended')
    ]

    # Basic Info
    name = models.CharField(max_length=200, help_text="Course name")
    slug = models.SlugField(max_length=200, unique=True)
    code = models.CharField(max_length=20, unique=True, help_text="Course code")
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='courses')
    
    # Display
    icon = models.CharField(max_length=50, default='book-open', help_text="Lucide icon name")
    color_primary = models.CharField(max_length=20, default='blue')
    color_secondary = models.CharField(max_length=20, default='cyan')
    
    # Program Details
    degree_level = models.CharField(max_length=50, choices=DEGREE_LEVEL_CHOICES)
    available_study_modes = models.JSONField(
        default=list, 
        help_text="List of available study modes for this course"
    )
    duration_years = models.DecimalField(max_digits=3, decimal_places=1, default=4.0)
    credits_required = models.IntegerField(default=120)
    
    # Content
    tagline = models.CharField(max_length=200)
    overview = models.TextField()
    description = models.TextField()
    
    # Learning Outcomes & Career
    learning_outcomes = models.JSONField(default=list)
    career_paths = models.JSONField(default=list)
    
    # Curriculum
    core_courses = models.JSONField(default=list)
    specialization_tracks = models.JSONField(default=list)
    
    # Requirements
    entry_requirements = models.JSONField(
        default=list,
        help_text="General entry requirements for this course"
    )
    
    # Financial Information
    application_fee = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Application processing fee"
    )
    tuition_fee = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        help_text="Annual tuition fee"
    )
    
    # Statistics
    avg_starting_salary = models.CharField(max_length=50, blank=True)
    job_placement_rate = models.IntegerField(default=0, help_text="Percentage (0-100)")
    
    # Media
    hero_image = models.ImageField(upload_to='courses/heroes/', blank=True, null=True)
    
    # SEO
    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
        ordering = ['faculty', 'display_order', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_degree_level_display()})"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.name}-{self.degree_level}")
        super().save(*args, **kwargs)


class CourseIntake(models.Model):
    """
    Separate model for intake periods - allows multiple intakes per course
    with different application deadlines and start dates
    """
    INTAKE_PERIOD_CHOICES = [
        ('january', 'January'),
        ('may', 'May'),
        ('september', 'September'),
        ('october', 'October')
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='intakes')
    intake_period = models.CharField(max_length=50, choices=INTAKE_PERIOD_CHOICES)
    year = models.IntegerField()
    start_date = models.DateField()
    application_deadline = models.DateField()
    is_active = models.BooleanField(default=True)
    available_slots = models.IntegerField(default=0, help_text="Maximum number of students")
    
    class Meta:
        unique_together = ['course', 'intake_period', 'year']
        ordering = ['start_date']
        verbose_name = 'Course Intake'
        verbose_name_plural = 'Course Intakes'
    
    def __str__(self):
        return f"{self.course.name} - {self.get_intake_period_display()} {self.year}"


# ==================== APPLICATIONS ====================
class CourseApplication(models.Model):
    """
    Main application model - simplified and properly connected
    """
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
        ('search-engine', 'Search Engine'),
        ('social-media', 'Social Media'),
        ('friend-family', 'Friend or Family'),
        ('education-fair', 'Education Fair'),
        ('school-counselor', 'School Counselor'),
        ('alumni', 'MIU Alumni'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_payment', 'Pending Payment'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('reviewed', 'Reviewed'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('waitlisted', 'Waitlisted'),
        ('withdrawn', 'Withdrawn'),
    ]
    
    # Identification
    application_id = models.CharField(max_length=50, unique=True, blank=True)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='applications', 
        null=True, 
        blank=True
    )
    
    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    date_of_birth = models.DateField(null=True, blank=True)
    country = models.CharField(max_length=100, choices=COUNTRY_CHOICES)
    gender = models.CharField(max_length=50, choices=GENDER_CHOICES)
    address = models.TextField()
    
    # Academic History
    academic_history = models.JSONField(
        default=list,
        help_text="List of previous educational institutions and qualifications"
    )
    english_proficiency_test = models.CharField(max_length=50, blank=True)
    english_proficiency_score = models.CharField(max_length=20, blank=True)
    additional_qualifications = models.TextField(blank=True)
    
    # Course Selection - PROPER FOREIGN KEYS
    course = models.ForeignKey(
        Course, 
        on_delete=models.PROTECT, 
        related_name='applications',
        help_text="The course being applied for"
    )
    intake = models.ForeignKey(
        CourseIntake,
        on_delete=models.PROTECT,
        related_name='applications',
        help_text="Specific intake period"
    )
    study_mode = models.CharField(
        max_length=20, 
        choices=Course.STUDY_MODE_CHOICES,
        help_text="Preferred study mode"
    )
    
    # Financial Aid
    scholarship_requested = models.BooleanField(default=False)
    financial_aid_requested = models.BooleanField(default=False)
    
    # Additional Information
    referral_source = models.CharField(
        max_length=100, 
        blank=True, 
        choices=REFERRAL_CHOICES
    )
    personal_statement = models.TextField(blank=True)
    
    # Application Status
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='draft'
    )
    
    # Review Information
    reviewed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='reviewed_applications'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    submitted_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Course Application'
        verbose_name_plural = 'Course Applications'
        indexes = [
            models.Index(fields=['application_id']),
            models.Index(fields=['email']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.application_id} - {self.get_full_name()}"
    
    def save(self, *args, **kwargs):
        if not self.application_id:
            # Create temporary ID first
            self.application_id = f"TEMP-{uuid.uuid4().hex[:8]}"
            super().save(*args, **kwargs)
            # Generate proper ID after we have the primary key
            year = timezone.now().year
            self.application_id = f'MIU-{year}-{str(self.id).zfill(6)}'
            CourseApplication.objects.filter(id=self.id).update(
                application_id=self.application_id
            )
            return
        super().save(*args, **kwargs)
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def payment_status(self):
        """Check if application fee has been paid"""
        try:
            payment = self.payment
            return payment.status
        except ApplicationPayment.DoesNotExist:
            return 'pending'
    
    @property
    def is_paid(self):
        """Quick check if application is paid"""
        return self.payment_status == 'success'
    
    def can_upload_documents(self):
        """Check if application can upload documents"""
        return self.is_paid and self.status in ['payment_complete', 'documents_uploaded', 'pending_payment']
    
    def can_submit(self):
        """Check if application can be submitted for review"""
        return (
            self.is_paid and 
            self.documents.exists() and 
            self.status in ['payment_complete', 'documents_uploaded']
        )
    
    def mark_as_submitted(self):
        """Mark application as submitted after all requirements met"""
        if self.can_submit():
            self.status = 'submitted'
            self.submitted_at = timezone.now()
            self.save(update_fields=['status', 'submitted_at'])
            return True
        return False


def application_file_upload_path(instance, filename):
    """Generate upload path for application files"""
    name, ext = os.path.splitext(filename)
    safe_filename = f"{slugify(name)}{ext}"
    file_type = instance.file_type or 'other'
    return f'applications/{instance.application.application_id}/{file_type}/{safe_filename}'


class ApplicationDocument(models.Model):
    """
    Documents attached to applications
    Removed payment fields - payment is handled separately
    """
    FILE_TYPE_CHOICES = [
        ('transcript', 'Academic Transcript'),
        ('certificate', 'Certificate/Diploma'),
        ('english_test', 'English Proficiency Test'),
        ('id_document', 'ID Document'),
        ('cv', 'CV/Resume'),
        ('recommendation', 'Letter of Recommendation'),
        ('other', 'Other Document'),
    ]
    
    application = models.ForeignKey(
        CourseApplication, 
        related_name='documents', 
        on_delete=models.CASCADE
    )
    file = models.FileField(upload_to=application_file_upload_path)
    file_type = models.CharField(max_length=50, choices=FILE_TYPE_CHOICES)
    original_filename = models.CharField(max_length=255)
    file_size = models.IntegerField(default=0, help_text="File size in bytes")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Application Document'
        verbose_name_plural = 'Application Documents'
    
    def __str__(self):
        return f"{self.get_file_type_display()} - {self.application.application_id}"
    
    def save(self, *args, **kwargs):
        if self.file and not self.original_filename:
            self.original_filename = os.path.basename(self.file.name)
        if self.file and not self.file_size:
            try:
                self.file_size = self.file.size
            except:
                pass
        super().save(*args, **kwargs)
    
    def get_file_size_display(self):
        """Human-readable file size"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


# ==================== PAYMENT SYSTEM ====================
class ApplicationPayment(models.Model):
    """
    Payment model for application fees
    One-to-one relationship with CourseApplication
    """
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('stripe', 'Stripe'),
        ('paystack', 'Paystack'),
        ('bank_transfer', 'Bank Transfer'),
        ('other', 'Other'),
    ]
    
    # Link to application (one-to-one)
    application = models.OneToOneField(
        CourseApplication,
        on_delete=models.CASCADE,
        related_name='payment'
    )
    
    # Payment Details
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(
        max_length=20, 
        choices=PAYMENT_STATUS_CHOICES, 
        default='pending'
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='stripe'
    )
    
    # Gateway Information
    payment_reference = models.CharField(
        max_length=100, 
        unique=True,
        help_text="Unique payment reference/transaction ID"
    )
    gateway_payment_id = models.CharField(
        max_length=255, 
        blank=True,
        help_text="Payment gateway's transaction ID (e.g., Stripe payment intent)"
    )
    
    # Card Information (if applicable)
    card_last4 = models.CharField(max_length=4, blank=True)
    card_brand = models.CharField(max_length=50, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional Info
    payment_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional payment gateway metadata"
    )
    failure_reason = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Application Payment'
        verbose_name_plural = 'Application Payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['payment_reference']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Payment for {self.application.application_id} - {self.status}"
    
    def save(self, *args, **kwargs):
        # Generate reference if not exists
        if not self.payment_reference:
            self.payment_reference = f"PAY-{uuid.uuid4().hex[:12].upper()}"
        
        # Set amount from course if not set
        if not self.amount:
            self.amount = self.application.course.application_fee
        
        # Update paid_at when status changes to success
        if self.status == 'success' and not self.paid_at:
            self.paid_at = timezone.now()
        
        super().save(*args, **kwargs)
        
        # ✅ UPDATE: Change application status to 'payment_complete' after successful payment
        if self.status == 'success' and self.paid_at:
            if self.application.status in ['draft', 'pending_payment']:
                self.application.status = 'payment_complete'  # Ready to upload documents
                self.application.save(update_fields=['status'])


# ==================== VENDOR MANAGEMENT ====================
class Vendor(models.Model):
    """
    Vendor/Partner institutions
    """
    name = models.CharField(max_length=255)
    email = models.EmailField()
    country = models.CharField(max_length=100, blank=True)
    stripe_account_id = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Vendor'
        verbose_name_plural = 'Vendors'
    
    def __str__(self):
        return self.name


# ==================== BLOG SYSTEM ====================
def blog_image_upload_path(instance, filename):
    """Generate upload path for blog images"""
    name, ext = os.path.splitext(filename)
    safe_filename = f"{slugify(name)}{ext}"
    return f'blog/{instance.slug}/{safe_filename}'


class BlogCategory(models.Model):
    """Blog category model for organizing posts"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='folder')
    color = models.CharField(max_length=20, default='blue')
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Blog Category'
        verbose_name_plural = 'Blog Categories'
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_post_count(self):
        return self.blog_posts.filter(status='published').count()


class BlogPost(models.Model):
    """Main blog post model"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    # Basic Information
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    subtitle = models.CharField(max_length=200, blank=True)
    
    # Content
    excerpt = models.TextField(max_length=500)
    content = models.TextField()
    
    # Categorization
    category = models.ForeignKey(
        BlogCategory, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='blog_posts'
    )
    tags = models.JSONField(default=list, blank=True)
    
    # Author & Attribution
    author = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='blog_posts'
    )
    author_name = models.CharField(max_length=100)
    author_title = models.CharField(max_length=100, blank=True)
    
    # Media
    featured_image = models.ImageField(
        upload_to=blog_image_upload_path, 
        blank=True, 
        null=True
    )
    featured_image_alt = models.CharField(max_length=200, blank=True)
    
    # Metadata
    read_time = models.IntegerField(default=5)
    views_count = models.IntegerField(default=0)
    
    # Publishing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False)
    publish_date = models.DateTimeField(default=timezone.now)
    
    # SEO
    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Blog Post'
        verbose_name_plural = 'Blog Posts'
        ordering = ['-publish_date', '-created_at']
        indexes = [
            models.Index(fields=['-publish_date', 'status']),
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            original_slug = self.slug
            counter = 1
            while BlogPost.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        
        if not self.meta_description and self.excerpt:
            self.meta_description = self.excerpt[:160]
        
        if not self.author_name and self.author:
            self.author_name = self.author.get_full_name() or self.author.username
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('eduweb:blog_detail', kwargs={'slug': self.slug})
    
    def increment_views(self):
        """Increment view count"""
        self.views_count += 1
        self.save(update_fields=['views_count'])
    
    def get_related_posts(self, limit=3):
        """Get related posts from same category"""
        return BlogPost.objects.filter(
            category=self.category,
            status='published'
        ).exclude(id=self.id)[:limit]