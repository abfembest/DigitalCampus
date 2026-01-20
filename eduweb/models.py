from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify
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
    name = models.CharField(max_length=200, help_text="Course name")
    slug = models.SlugField(max_length=200, unique=True)
    code = models.CharField(max_length=20, unique=True, help_text="Course code")
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='courses')
    
    # Display
    icon = models.CharField(max_length=50, default='book-open', help_text="Lucide icon name")
    color_primary = models.CharField(max_length=20, default='blue')
    color_secondary = models.CharField(max_length=20, default='cyan')
    
    # Program Details
    degree_levels = models.JSONField(default=list)
    study_modes = models.JSONField(default=list)
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
    undergraduate_requirements = models.JSONField(default=list)
    graduate_requirements = models.JSONField(default=list)
    
    # Statistics
    avg_starting_salary = models.CharField(max_length=50, blank=True)
    job_placement_rate = models.IntegerField(default=0)
    intake_periods = models.JSONField(default=list)
    
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
        return f"{self.name} - {self.faculty.name}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


# ==================== APPLICATIONS ====================
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
        ('search-engine', 'Search Engine'),
        ('social-media', 'Social Media'),
        ('friend-family', 'Friend or Family'),
        ('education-fair', 'Education Fair'),
        ('school-counselor', 'School Counselor'),
        ('alumni', 'MIU Alumni'),
        ('other', 'Other'),
    ]
    
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
    
    # Academic History
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
    
    # Additional
    referral_source = models.CharField(max_length=100, blank=True, choices=REFERRAL_CHOICES)
    documents_uploaded = models.JSONField(default=dict)
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    submitted = models.BooleanField(default=False)
    submission_date = models.DateTimeField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    decision = models.CharField(max_length=20, choices=DECISION_CHOICES, default='pending')
    decision_date = models.DateTimeField(null=True, blank=True)
    decision_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_applications')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    is_reviewed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Course Application'
        verbose_name_plural = 'Course Applications'
    
    def __str__(self):
        return f"{self.application_id} - {self.first_name} {self.last_name}"
    
    def save(self, *args, **kwargs):
        if not self.application_id:
            self.application_id = f"TEMP-{uuid.uuid4().hex[:8]}"
            super().save(*args, **kwargs)
            year = timezone.now().year
            self.application_id = f'MIU-{year}-{str(self.id).zfill(4)}'
            CourseApplication.objects.filter(id=self.id).update(application_id=self.application_id)
            return
        super().save(*args, **kwargs)
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_program_display_name(self):
        return dict(self.PROGRAM_CHOICES).get(self.program, self.program)
    
    def get_degree_level_display_name(self):
        return dict(self.DEGREE_LEVEL_CHOICES).get(self.degree_level, self.degree_level)


def application_file_upload_path(instance, filename):
    name, ext = os.path.splitext(filename)
    safe_filename = f"{name}{ext}"
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
    
    application = models.ForeignKey(CourseApplication, related_name='files', on_delete=models.CASCADE)
    file = models.FileField(upload_to=application_file_upload_path)
    file_type = models.CharField(max_length=50, choices=FILE_TYPE_CHOICES, default='other')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    original_filename = models.CharField(max_length=255, blank=True)
    file_size = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Application File'
        verbose_name_plural = 'Application Files'
    
    def __str__(self):
        return f"{self.get_file_type_display()} - {self.application.application_id}"
    
    def save(self, *args, **kwargs):
        if not self.original_filename and self.file:
            self.original_filename = self.file.name
        if not self.file_size and self.file:
            try:
                self.file_size = self.file.size
            except:
                pass
        super().save(*args, **kwargs)
    
    def get_file_size_display(self):
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


# ==================== PAYMENT ====================
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
    stripe_account_id = models.CharField(max_length=255, blank=True, null=True)

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
    name = models.CharField(max_length=100, unique=True, help_text="Category name (e.g., Student Life)")
    slug = models.SlugField(max_length=100, unique=True, help_text="URL-friendly name")
    description = models.TextField(blank=True, help_text="Category description")
    icon = models.CharField(max_length=50, default='folder', help_text="Lucide icon name")
    color = models.CharField(max_length=20, default='blue', help_text="Color theme (e.g., blue, green)")
    display_order = models.IntegerField(default=0, help_text="Order in category list")
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
    title = models.CharField(max_length=200, help_text="Post title")
    slug = models.SlugField(max_length=200, unique=True, help_text="URL-friendly title")
    subtitle = models.CharField(max_length=200, blank=True, help_text="Optional subtitle/excerpt")
    
    # Content
    excerpt = models.TextField(max_length=500, help_text="Short summary (max 500 chars)")
    content = models.TextField(help_text="Full blog post content (supports HTML)")
    
    # Categorization
    category = models.ForeignKey(BlogCategory, on_delete=models.SET_NULL, null=True, related_name='blog_posts')
    tags = models.JSONField(default=list, blank=True, help_text="List of tags (e.g., ['technology', 'innovation'])")
    
    # Author & Attribution
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='blog_posts')
    author_name = models.CharField(max_length=100, help_text="Display name (overrides user)")
    author_title = models.CharField(max_length=100, blank=True, help_text="e.g., 'Communications Director'")
    
    # Media
    featured_image = models.ImageField(
        upload_to=blog_image_upload_path, 
        blank=True, 
        null=True,
        help_text="Main post image (recommended: 1200x630px)"
    )
    featured_image_alt = models.CharField(max_length=200, blank=True, help_text="Alt text for accessibility")
    
    # Metadata
    read_time = models.IntegerField(default=5, help_text="Estimated reading time in minutes")
    views_count = models.IntegerField(default=0, help_text="Number of views")
    
    # Publishing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False, help_text="Show in featured section")
    publish_date = models.DateTimeField(default=timezone.now, help_text="Publication date")
    
    # SEO
    meta_description = models.CharField(max_length=160, blank=True, help_text="SEO meta description")
    meta_keywords = models.CharField(max_length=255, blank=True, help_text="SEO keywords (comma-separated)")
    
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
            # Ensure unique slug
            original_slug = self.slug
            counter = 1
            while BlogPost.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        
        # Auto-generate meta description from excerpt if not provided
        if not self.meta_description and self.excerpt:
            self.meta_description = self.excerpt[:160]
        
        # Set author_name from user if not provided
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