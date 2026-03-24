from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.core.exceptions import ValidationError
from django.db.models import Avg
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.text import slugify
import uuid
import os
from decimal import Decimal


DEGREE_LEVEL_CHOICES = [
    ('certificate', 'Certificate'),
    ('diploma', 'Diploma'),
    ('undergraduate', 'Undergraduate'),
    ('postgraduate', 'Postgraduate'),
    ('masters', 'Masters'),
    ('phd', 'PhD')
]

# ==================== HELPER FUNCTIONS ====================
def validate_file_size(file, max_size_mb=10):
    """Validate file size"""
    if file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f'File size cannot exceed {max_size_mb}MB')


def get_video_upload_path(instance, filename):
    """Generate upload path for course videos"""
    course_slug = instance.lesson.course.slug if hasattr(instance, 'lesson') else 'misc'
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4().hex}.{ext}"
    return f'courses/{course_slug}/videos/{filename}'


def get_document_upload_path(instance, filename):
    """Generate upload path for course documents"""
    course_slug = instance.lesson.course.slug if hasattr(instance, 'lesson') else instance.course.slug
    ext = filename.split('.')[-1]
    safe_filename = f"{slugify(os.path.splitext(filename)[0])}.{ext}"
    return f'courses/{course_slug}/documents/{safe_filename}'


def get_assignment_upload_path(instance, filename):
    """Generate upload path for assignment submissions"""
    ext = filename.split('.')[-1]
    safe_filename = f"{instance.student.username}_{uuid.uuid4().hex[:8]}.{ext}"
    return f'courses/{instance.assignment.lesson.course.slug}/submissions/{safe_filename}'


def get_certificate_upload_path(instance, filename):
    """Generate upload path for certificates"""
    ext = filename.split('.')[-1]
    filename = f"{instance.student.username}_{uuid.uuid4().hex}.{ext}"
    return f'certificates/{filename}'


def blog_image_upload_path(instance, filename):
    """Generate upload path for blog images"""
    name, ext = os.path.splitext(filename)
    safe_filename = f"{slugify(name)}{ext}"
    return f'blog/{instance.slug}/{safe_filename}'

class SiteConfig(models.Model):
    """
    Singleton model — drives the nav header, footer, and all embed codes
    (promo video, campus map, virtual tour) across all pages.

    In views:      site_config = SiteConfig.get()
    In templates:  {{ site_config.field_name }}
    """

    # =========================================================================
    # IDENTITY  —  nav logo, footer copyright, og/twitter meta tags
    # =========================================================================
    school_name = models.CharField(
        max_length=200,
        default='Melchisedec International University',
        help_text="Full legal name shown in nav, footer, og tags"
    )
    school_short_name = models.CharField(
        max_length=50, blank=True, default='MIU',
        help_text="Abbreviation used in footer copyright, og tags e.g. 'MIU'"
    )
    tagline = models.CharField(
        max_length=300, blank=True,
        help_text="Short tagline used in footer and og description fallback"
    )
    logo = models.ImageField(
        upload_to='site/logos/', blank=True, null=True,
        help_text="Nav bar and footer logo"
    )
    logo_dark = models.ImageField(
        upload_to='site/logos/', blank=True, null=True,
        help_text="Dark-background variant of the logo"
    )
    favicon = models.ImageField(
        upload_to='site/favicons/', blank=True, null=True,
        help_text="Browser tab favicon"
    )
    og_image = models.ImageField(
        upload_to='site/og/', blank=True, null=True,
        help_text="Default Open Graph / Twitter share image (1200×630 px recommended)"
    )
    theme_color = models.CharField(
        max_length=20, blank=True, default='#840384',
        help_text="Browser theme-color meta tag hex value e.g. '#840384'"
    )

    # =========================================================================
    # CONTACT  —  footer bottom bar (phone, email)
    # =========================================================================
    email = models.EmailField(
        blank=True,
        help_text="Primary contact email — footer bottom bar"
    )
    phone_primary = models.CharField(
        max_length=30, blank=True,
        help_text="Primary phone — footer bottom bar"
    )
    phone_secondary    = models.CharField(max_length=30, blank=True)
    phone_ng_primary   = models.CharField(max_length=30, blank=True,
                                          help_text="Primary Nigeria phone number")
    phone_ng_secondary = models.CharField(max_length=30, blank=True,
                                          help_text="Secondary Nigeria phone number")
    whatsapp = models.CharField(
        max_length=30, blank=True,
        help_text="WhatsApp number — digits only e.g. 15551234567"
    )

    # =========================================================================
    # CONTACT PAGE — department-specific emails
    # =========================================================================
    email_admissions = models.EmailField(
        blank=True,
        help_text="Admissions department email — contact page"
    )
    email_info = models.EmailField(
        blank=True,
        help_text="General info email — contact page"
    )
    email_international = models.EmailField(
        blank=True,
        help_text="International enquiries email — contact page"
    )

    # =========================================================================
    # CONTACT PAGE — labelled phone lines
    # =========================================================================
    phone_admissions = models.CharField(
        max_length=30, blank=True,
        help_text="Admissions phone line — contact page e.g. '+1 (555) 123-4567'"
    )
    phone_general = models.CharField(
        max_length=30, blank=True,
        help_text="General enquiries phone line — contact page"
    )
    phone_international = models.CharField(
        max_length=30, blank=True,
        help_text="International office phone line — contact page"
    )

    # =========================================================================
    # OFFICE HOURS  —  contact page office hours block
    # =========================================================================
    office_hours_weekday = models.CharField(
        max_length=100, blank=True,
        default='Monday - Friday: 8:00 AM - 6:00 PM',
        help_text="Weekday office hours e.g. 'Monday - Friday: 8:00 AM - 6:00 PM'"
    )
    office_hours_saturday = models.CharField(
        max_length=100, blank=True,
        default='Saturday: 9:00 AM - 1:00 PM',
        help_text="Saturday office hours e.g. 'Saturday: 9:00 AM - 1:00 PM'"
    )
    office_hours_sunday = models.CharField(
        max_length=100, blank=True,
        default='Sunday: Closed',
        help_text="Sunday office hours e.g. 'Sunday: Closed'"
    )

    # =========================================================================
    # ADDRESSES  —  footer address block
    # =========================================================================
    address_usa = models.TextField(
        blank=True,
        help_text="US campus address — footer"
    )
    address_nigeria = models.TextField(
        blank=True,
        help_text="Nigeria campus address — footer"
    )

    # =========================================================================
    # SOCIAL MEDIA  —  footer social icons + nav mega-menu Connect section
    # =========================================================================
    facebook  = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    youtube   = models.URLField(blank=True)
    twitter   = models.URLField(blank=True)
    tiktok    = models.URLField(blank=True)
    linkedin  = models.URLField(blank=True)

    # =========================================================================
    # FOOTER COPY  —  footer tagline paragraph + copyright line
    # =========================================================================
    footer_tagline = models.TextField(
        blank=True,
        default='Empowering global education since 1995 with innovative learning experiences and world-class faculty.',
        help_text="Short paragraph shown under the logo in the footer"
    )
    copyright_year = models.CharField(
        max_length=10, blank=True, default='2025',
        help_text="Year in the footer copyright line e.g. '2025'"
    )

    # =========================================================================
    # SEO  —  base.html meta/og/twitter tags inherited by all pages
    # =========================================================================
    meta_description = models.TextField(
        blank=True,
        help_text="Default SEO meta description — also og:description and twitter:description"
    )
    meta_keywords = models.TextField(
        blank=True,
        help_text="Default SEO meta keywords (comma separated)"
    )

    # =========================================================================
    # EMBED CODES
    # These are kept here because they are shared across multiple pages:
    #   promo_video_url    → index.html about section + about.html Who We Are
    #   campus_map_embed_url → index.html campus map section
    #   virtual_tour_url   → about.html Campus & Facilities section
    # =========================================================================
    promo_video_url = models.TextField(
        blank=True,
        help_text="Full iframe embed code from YouTube/Vimeo for the promo video"
    )
    campus_map_embed_url = models.TextField(
        blank=True,
        help_text="Full iframe embed code from Google Maps for the campus map section"
    )
    campus_map_address = models.CharField(
        max_length=300, blank=True,
        help_text="Address shown on the map overlay card and used for the Get Directions link"
    )
    virtual_tour_url = models.TextField(
        blank=True,
        help_text="Full iframe embed code for the virtual campus tour on the about page"
    )

    # =========================================================================
    # HERO SLIDES  —  index.html rotating hero background (up to 3 slides)
    # Each slide is either an image OR a video — not both.
    # If image is set, it is used. If video_url is set instead, video plays.
    # duration = how many seconds the slide stays before advancing.
    # =========================================================================
    hero_slide_1_image    = models.ImageField(
        upload_to='site/hero/', blank=True, null=True,
        help_text="Slide 1 background image"
    )
    hero_slide_1_video    = models.FileField(
        upload_to='site/hero/', blank=True, null=True,
        help_text="Slide 1 background video (.mp4). Used instead of image if set."
    )
    hero_slide_1_alt      = models.CharField(
        max_length=200, blank=True,
        default='Students collaborating on campus',
        help_text="Accessibility label for slide 1"
    )
    hero_slide_1_duration = models.PositiveSmallIntegerField(
        default=6,
        help_text="Seconds slide 1 stays visible before advancing"
    )

    hero_slide_2_image    = models.ImageField(
        upload_to='site/hero/', blank=True, null=True,
        help_text="Slide 2 background image"
    )
    hero_slide_2_video    = models.FileField(
        upload_to='site/hero/', blank=True, null=True,
        help_text="Slide 2 background video (.mp4). Used instead of image if set."
    )
    hero_slide_2_alt      = models.CharField(
        max_length=200, blank=True,
        default='Graduates celebrating commencement',
        help_text="Accessibility label for slide 2"
    )
    hero_slide_2_duration = models.PositiveSmallIntegerField(
        default=6,
        help_text="Seconds slide 2 stays visible before advancing"
    )

    hero_slide_3_image    = models.ImageField(
        upload_to='site/hero/', blank=True, null=True,
        help_text="Slide 3 background image"
    )
    hero_slide_3_video    = models.FileField(
        upload_to='site/hero/', blank=True, null=True,
        help_text="Slide 3 background video (.mp4). Used instead of image if set."
    )
    hero_slide_3_alt      = models.CharField(
        max_length=200, blank=True,
        default='Students using technology in class',
        help_text="Accessibility label for slide 3"
    )
    hero_slide_3_duration = models.PositiveSmallIntegerField(
        default=6,
        help_text="Seconds slide 3 stays visible before advancing"
    )

    # =========================================================================
    # ABOUT PAGE — Mission, Vision & Values
    # =========================================================================
    about_mission = models.TextField(
        blank=True,
        default='To provide accessible, innovative, and transformative education that empowers individuals from all backgrounds to achieve their full potential and make meaningful contributions to society.',
        help_text="Our Mission text — about page Mission card"
    )
    about_vision = models.TextField(
        blank=True,
        default='To be a globally recognized leader in higher education, known for innovation, inclusivity, and preparing future-ready graduates who drive positive change worldwide.',
        help_text="Our Vision text — about page Vision card"
    )
    about_values = models.JSONField(
        default=list,
        blank=True,
        help_text=(
            'List of core values shown in the Values card. '
            'Store as a JSON array of strings, e.g. '
            '["Excellence in Education", "Diversity & Inclusion", "Innovation & Creativity", "Global Citizenship"]'
        )
    )

    class Meta:
        verbose_name        = 'Site Configuration'
        verbose_name_plural = 'Site Configuration'

    def __str__(self):
        return self.school_name

    @classmethod
    def get(cls):
        """Fetch the single site config. Use this in all views."""
        return cls.objects.first()

class SiteHistoryMilestone(models.Model):
    """
    One entry in the About page 'Our History' timeline.
    Add as many as needed; order by `year`.
    """
    site = models.ForeignKey(
        SiteConfig,
        on_delete=models.CASCADE,
        related_name='history_milestones',
    )
    year = models.PositiveSmallIntegerField(
        help_text="e.g. 1995"
    )
    title = models.CharField(
        max_length=150,
        help_text="e.g. 'Founding' — displayed as '1995 – Founding'"
    )
    description = models.TextField(
        help_text="One or two sentences describing what happened that year"
    )
    display_order = models.PositiveSmallIntegerField(
        default=0,
        help_text="Lower numbers appear first. Leave 0 to sort by year instead."
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'History Milestone'
        verbose_name_plural = 'History Milestones'
        ordering = ['display_order', 'year']

    def __str__(self):
        return f"{self.year} – {self.title}"

# ==================== TESTIMONIALS ====================
class Testimonial(models.Model):
    quote       = models.TextField()
    author_name = models.CharField(max_length=100)
    author_role = models.CharField(max_length=150, help_text="e.g. 'MBA Graduate, 2023'")
    avatar      = models.ImageField(
        upload_to='testimonials/avatars/',
        blank=True,
        null=True,
        help_text="Author photo. If left blank, initials will be shown instead."
    )
    is_active   = models.BooleanField(default=True)
    order       = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ['order']
        verbose_name = 'Testimonial'
        verbose_name_plural = 'Testimonials'

    def __str__(self):
        return f"{self.author_name} – {self.author_role}"

# ==================== ANNOUNCEMENTS ====================
class Announcement(models.Model):
    """System-wide or course-specific announcements"""
    ANNOUNCEMENT_TYPE_CHOICES = [
        ('system', 'System-wide'),
        ('course', 'Course-specific'),
        ('category', 'Category-specific'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    content = models.TextField()
    announcement_type = models.CharField(max_length=20, choices=ANNOUNCEMENT_TYPE_CHOICES, default='system')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    
    # Targeting
    course = models.ForeignKey('LMSCourse', on_delete=models.CASCADE, null=True, blank=True, related_name='announcements')
    category = models.ForeignKey('CourseCategory', on_delete=models.CASCADE, null=True, blank=True, related_name='announcements')
    
    # Author
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='announcements_created')
    
    # Publishing
    is_active = models.BooleanField(default=True)
    publish_date = models.DateTimeField(default=timezone.now)
    expiry_date = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-priority', '-publish_date']
        verbose_name = 'Announcement'
        verbose_name_plural = 'Announcements'
        indexes = [
            models.Index(fields=['-publish_date', 'is_active']),
            models.Index(fields=['announcement_type']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            original_slug = self.slug
            counter = 1
            while Announcement.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """Check if announcement has expired"""
        if self.expiry_date:
            return timezone.now() > self.expiry_date
        return False


# ==================== ASSIGNMENTS ====================
class Assignment(models.Model):
    """Assignments for lessons"""
    lesson = models.ForeignKey('Lesson', on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    description = models.TextField()
    instructions = models.TextField(blank=True)
    
    # Grading
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=100.00, validators=[MinValueValidator(0)])
    passing_score = models.DecimalField(max_digits=5, decimal_places=2, default=50.00, validators=[MinValueValidator(0)])
    
    # Attachments
    attachment = models.FileField(
        upload_to=get_document_upload_path,
        blank=True,
        null=True,
        validators=[FileExtensionValidator(['pdf', 'doc', 'docx', 'txt', 'zip'])]
    )
    
    # Deadlines
    due_date = models.DateTimeField()
    allow_late_submission = models.BooleanField(default=False)
    late_penalty_percent = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Settings
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['lesson', 'display_order', 'due_date']
        verbose_name = 'Assignment'
        verbose_name_plural = 'Assignments'
        unique_together = [['lesson', 'slug']]
        indexes = [
            models.Index(fields=['lesson', 'is_active']),
            models.Index(fields=['due_date']),
        ]
    
    def __str__(self):
        return f"{self.lesson.course.title} - {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    @property
    def is_overdue(self):
        """Check if assignment is overdue"""
        return timezone.now() > self.due_date


class AssignmentSubmission(models.Model):
    """Student assignment submissions"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('graded', 'Graded'),
        ('returned', 'Returned for Revision'),
    ]
    
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignment_submissions')
    
    # Submission
    submission_text = models.TextField(blank=True)
    attachment = models.FileField(
        upload_to=get_assignment_upload_path,
        blank=True,
        null=True,
        validators=[FileExtensionValidator(['pdf', 'doc', 'docx', 'txt', 'zip'])]
    )
    
    # Grading
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    feedback = models.TextField(blank=True)
    graded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='graded_assignments')
    graded_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_late = models.BooleanField(default=False)
    
    # Timestamps
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'Assignment Submission'
        verbose_name_plural = 'Assignment Submissions'
        unique_together = [['assignment', 'student']]
        indexes = [
            models.Index(fields=['assignment', 'student']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.assignment.title}"
    
    def save(self, *args, **kwargs):
        # Check if late submission
        if self.submitted_at and self.submitted_at > self.assignment.due_date:
            self.is_late = True
            
            # Apply late penalty only when late submission is allowed but penalized
            if self.score and self.assignment.allow_late_submission and self.assignment.late_penalty_percent > 0:
                penalty = (self.assignment.late_penalty_percent / 100) * float(self.score)
                self.score = max(Decimal('0.00'), self.score - Decimal(str(penalty)))
        
        # Set submitted_at when status changes to submitted
        if self.status == 'submitted' and not self.submitted_at:
            self.submitted_at = timezone.now()
        
        # Set graded_at when graded
        if self.status == 'graded' and not self.graded_at:
            self.graded_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def passed(self):
        """Check if student passed the assignment"""
        if self.score:
            return self.score >= self.assignment.passing_score
        return False


# ==================== AUDIT LOGS ====================
class AuditLog(models.Model):
    """System audit logs for security and tracking"""
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('access', 'Access'),
        ('export', 'Export'),
        ('permission_change', 'Permission Change'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    extra_data = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action']),
        ]
    
    def __str__(self):
        return f"{self.user.username if self.user else 'System'} - {self.action} - {self.model_name} - {self.timestamp}"


# ==================== BADGES ====================
class Badge(models.Model):
    """Achievement badges for students"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='award')
    color = models.CharField(max_length=20, default='gold')
    
    # Criteria
    criteria = models.TextField(help_text="Criteria to earn this badge")
    points = models.IntegerField(default=10, help_text="Points awarded for earning this badge")
    
    # Settings
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Badge'
        verbose_name_plural = 'Badges'
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class StudentBadge(models.Model):
    """Badges earned by students"""
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='earned_badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='awarded_to')
    awarded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='badges_awarded')
    reason = models.TextField(blank=True)
    awarded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-awarded_at']
        verbose_name = 'Student Badge'
        verbose_name_plural = 'Student Badges'
        unique_together = [['student', 'badge']]
    
    def __str__(self):
        return f"{self.student.username} - {self.badge.name}"


# ==================== BLOG SYSTEM ====================
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
    category = models.ForeignKey(BlogCategory, on_delete=models.SET_NULL, null=True, related_name='blog_posts')
    tags = models.JSONField(default=list, blank=True)
    
    # Author & Attribution
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='blog_posts')
    author_name = models.CharField(max_length=100)
    author_title = models.CharField(max_length=100, blank=True)
    author_photo = models.ImageField(upload_to='blog/authors/', blank=True, null=True)
    author_bio = models.TextField(blank=True)
    
    # Media
    featured_image = models.ImageField(upload_to=blog_image_upload_path, blank=True, null=True)
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


# ==================== CERTIFICATES ====================
class Certificate(models.Model):
    """Course completion certificates"""
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certificates')
    course = models.ForeignKey('LMSCourse', on_delete=models.CASCADE, related_name='certificates')
    certificate_id = models.CharField(max_length=50, unique=True, editable=False)
    
    # Certificate Details
    issued_date = models.DateField(auto_now_add=True)
    completion_date = models.DateField()
    grade = models.CharField(max_length=5, blank=True)
    
    # File
    certificate_file = models.FileField(upload_to=get_certificate_upload_path, blank=True, null=True)
    
    # Verification
    verification_code = models.UUIDField(default=uuid.uuid4, editable=False)
    is_verified = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-issued_date']
        verbose_name = 'Certificate'
        verbose_name_plural = 'Certificates'
        unique_together = [['student', 'course']]
        indexes = [
            models.Index(fields=['certificate_id']),
            models.Index(fields=['verification_code']),
        ]
    
    def has_paid_certificate_fee(self, user):
        """Return True if the student has a successful FeePayment for a certificate fee."""
        from .models import FeePayment
        return FeePayment.objects.filter(
            user=user,
            status='success',
            fee__purpose__icontains='certificate',
        ).exists()
    
    def save(self, *args, **kwargs):
        if not self.certificate_id:
            self.certificate_id = f"CERT-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)


# ==================== CONTACT ====================
class ContactMessage(models.Model):
    SUBJECT_CHOICES = [
        ('admissions', 'Admissions Inquiry'),
        ('programs', 'Program Information'),
        ('campus', 'Campus Visit'),
        ('financial', 'Financial Aid'),
        ('support', 'Technical Support'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='contact_messages',
        help_text="User who submitted this message (if logged in)"
    )
    
    name = models.CharField(max_length=200)
    email = models.EmailField()
    subject = models.CharField(max_length=50, choices=SUBJECT_CHOICES)
    message = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    responded = models.BooleanField(default=False)
    responded_at = models.DateTimeField(null=True, blank=True)
    responded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='contact_responses')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'
    
    def __str__(self):
        return f"{self.name} - {self.subject} ({self.created_at.strftime('%Y-%m-%d')})"


# ==================== COURSE APPLICATION SYSTEM ====================
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

    # Dean Information
    dean_name = models.CharField(max_length=100, blank=True)
    dean_role = models.CharField(max_length=100, blank=True, default='Dean')
    dean_faculty_label = models.CharField(max_length=150, blank=True)
    dean_photo = models.ImageField(upload_to='faculties/deans/', blank=True, null=True)
    
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

class InstitutionMember(models.Model):
    """Board members and institutional staff for About page"""
    MEMBER_TYPE_CHOICES = [
        ('admin_board',      'Administrative / Management Board'),
        ('academic_board',   'Academic Board'),
        ('advisorate_board', 'Advisorate Board'),
        ('staff',            'Staff'),
    ]
    member_type   = models.CharField(max_length=30, choices=MEMBER_TYPE_CHOICES, db_index=True)
    name          = models.CharField(max_length=150)
    role          = models.CharField(max_length=200)
    photo         = models.ImageField(upload_to='institution/members/', blank=True, null=True)
    bio           = models.TextField(blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active     = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = 'Institution Member'
        verbose_name_plural = 'Institution Members'

    def __str__(self):
        return f'{self.name} — {self.get_member_type_display()}'

#################### DEPARTMENTS #####################

class Department(models.Model):
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.CASCADE,
        related_name="departments"
    )

    name = models.CharField(
        max_length=200,
        help_text="Department name (e.g., Electrical Engineering)"
    )
    slug = models.SlugField(max_length=200, unique=True)
    code = models.CharField(
        max_length=20,
        help_text="Department code (e.g., EEE)"
    )

    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("faculty", "code")
        ordering = ["display_order", "name"]

    def __str__(self):
        return f"{self.name} ({self.faculty.code})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            original_slug = self.slug
            counter = 1
            while Department.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)



    ############################# PROGRAMS ########

# ==============================================================================
# PROGRAM
# Represents the academic qualification / degree offering within a Department.
# e.g. "BSc Computer Science", "MBA", "Diploma in Nursing"
# ==============================================================================

class Program(models.Model):

    STUDY_MODE_CHOICES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('online', 'Online'),
        ('blended', 'Blended'),
    ]

    # ── Hierarchy ──────────────────────────────────────────────────────────────
    department = models.ForeignKey(
        "Department",
        on_delete=models.CASCADE,
        related_name="programs",
        help_text="Department this program belongs to"
    )

    # ── Identity ───────────────────────────────────────────────────────────────
    name = models.CharField(
        max_length=200,
        help_text="Program name (e.g., BSc Electrical Engineering)"
    )
    slug = models.SlugField(max_length=200, unique=True)
    code = models.CharField(
        max_length=30,
        help_text="Program code (e.g., BSC-EEE)"
    )

    # ── Academic Structure ─────────────────────────────────────────────────────
    degree_level = models.CharField(
        max_length=50,
        choices=DEGREE_LEVEL_CHOICES,
        help_text="The level of qualification awarded"
    )
    duration_years = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        help_text="Total duration of the program in years (e.g., 4.0)"
    )
    credits_required = models.IntegerField(
        default=120,
        help_text="Total credit units required to complete the program"
    )
    available_study_modes = models.JSONField(
        default=list,
        blank=True,
        help_text="Study modes available: full_time, part_time, online, blended"
    )
    max_students = models.IntegerField(
        null=True,
        blank=True,
        help_text="Maximum student capacity per intake (leave blank for unlimited)"
    )

    # ── Marketing / Display Content ────────────────────────────────────────────
    tagline = models.CharField(
        max_length=200,
        blank=True,
        help_text="Short marketing tagline shown on program cards and hero sections"
    )
    overview = models.TextField(
        blank=True,
        help_text="Short overview paragraph (used on listing pages)"
    )
    description = models.TextField(
        blank=True,
        help_text="Full program description (used on detail page)"
    )

    # ── Curriculum ─────────────────────────────────────────────────────────────
    entry_requirements = models.JSONField(
        default=list,
        blank=True,
        help_text="List of admission/entry requirements"
    )
    core_courses = models.JSONField(
        default=list,
        blank=True,
        help_text="List of compulsory course names/codes in this program"
    )
    specialization_tracks = models.JSONField(
        default=list,
        blank=True,
        help_text="List of available specialization tracks or majors"
    )

    # ── Outcomes & Career ──────────────────────────────────────────────────────
    learning_outcomes = models.JSONField(
        default=list,
        blank=True,
        help_text="What graduates will know and be able to do"
    )
    career_paths = models.JSONField(
        default=list,
        blank=True,
        help_text="Typical careers graduates pursue"
    )
    avg_starting_salary = models.CharField(
        max_length=50,
        blank=True,
        help_text="Average starting salary for graduates (e.g., '$45,000 - $60,000')"
    )
    job_placement_rate = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Graduate job placement rate as a percentage (0–100)"
    )

    # ── Financial ──────────────────────────────────────────────────────────────
    application_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Fee to apply for this program"
    )
    tuition_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text="Tuition fee per academic year"
    )

    # ── Media ──────────────────────────────────────────────────────────────────
    hero_image = models.ImageField(
        upload_to='programs/heroes/',
        blank=True,
        null=True,
        help_text="Hero/banner image for the program detail page"
    )

    # ── SEO ────────────────────────────────────────────────────────────────────
    meta_description = models.CharField(
        max_length=160,
        blank=True,
        help_text="SEO meta description (max 160 characters)"
    )
    meta_keywords = models.CharField(
        max_length=255,
        blank=True,
        help_text="SEO meta keywords (comma separated)"
    )

    # ── Status & Display ───────────────────────────────────────────────────────
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("department", "code")
        ordering = ["display_order", "name"]
        verbose_name = "Program"
        verbose_name_plural = "Programs"
        indexes = [
            models.Index(fields=["department", "is_active"]),
            models.Index(fields=["degree_level"]),
            models.Index(fields=["slug"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            original_slug = self.slug
            counter = 1
            while Program.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    # ── Convenience Properties ─────────────────────────────────────────────────
    @property
    def faculty(self):
        """Access faculty directly without storing a redundant FK."""
        return self.department.faculty

    def get_active_courses(self):
        """Return all active courses under this program."""
        return self.courses.filter(is_active=True).order_by('year_of_study', 'semester', 'display_order')

    def get_total_credit_units(self):
        """Sum of credit units across all active courses."""
        return self.courses.filter(is_active=True).aggregate(
            total=models.Sum('credit_units')
        )['total'] or 0

# ==============================================================================
# ACADEMIC SESSION
# Represents a single academic year and its semester breakdown.
# e.g. "2024/2025" with First Semester: Sep–Jan, Second Semester: Feb–Jun
# ==============================================================================

class AcademicSession(models.Model):

    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('active',   'Active'),
        ('closed',   'Closed'),
    ]

    # ── Identity ───────────────────────────────────────────────────────────
    name = models.CharField(
        max_length=20,
        unique=True,
        help_text="Academic year label (e.g., 2024/2025)"
    )

    # ── Semester 1 ─────────────────────────────────────────────────────────
    first_semester_start  = models.DateField(help_text="First semester start date")
    first_semester_end    = models.DateField(help_text="First semester end date")

    # ── Semester 2 ─────────────────────────────────────────────────────────
    second_semester_start = models.DateField(help_text="Second semester start date")
    second_semester_end   = models.DateField(help_text="Second semester end date")

    # ── Registration Windows ───────────────────────────────────────────────
    registration_start    = models.DateField(
        null=True, blank=True,
        help_text="When student course registration opens"
    )
    registration_end      = models.DateField(
        null=True, blank=True,
        help_text="When student course registration closes"
    )

    # ── Status ─────────────────────────────────────────────────────────────
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='upcoming',
        help_text="Only one session should be 'active' at a time"
    )
    is_current = models.BooleanField(
        default=False,
        help_text="Mark this as the current running session"
    )

    # ── Timestamps ─────────────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-name']
        verbose_name = 'Academic Session'
        verbose_name_plural = 'Academic Sessions'
        indexes = [
            models.Index(fields=['is_current']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Ensure only one session is marked as current at a time
        if self.is_current:
            AcademicSession.objects.exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_current(cls):
        """Fetch the active session. Use this everywhere instead of hardcoding."""
        return cls.objects.filter(is_current=True).first()

class Course(models.Model):

    COURSE_TYPE_CHOICES = [
        ('core', 'Core'),
        ('elective', 'Elective'),
        ('general', 'General Studies'),
        ('prerequisite', 'Prerequisite'),
    ]

    SEMESTER_CHOICES = [
        ('first', 'First Semester'),
        ('second', 'Second Semester'),
        ('annual', 'Annual'),
    ]

    # ── Hierarchy ──────────────────────────────────────────────────────────────
    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name="courses",
        help_text="Program this course belongs to"
    )

    # ── Identity ───────────────────────────────────────────────────────────────
    name = models.CharField(max_length=200, help_text="Course name")
    slug = models.SlugField(max_length=200, unique=True)
    code = models.CharField(max_length=20, help_text="Course code (e.g., CS101)")

    # ── Academic Structure ─────────────────────────────────────────────────────
    course_type = models.CharField(
        max_length=20,
        choices=COURSE_TYPE_CHOICES,
        default='core',
        help_text="Whether this is a core requirement, elective, or general studies unit"
    )
    credit_units = models.IntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="Credit units this course carries"
    )
    year_of_study = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(7)],
        help_text="Which year of the program this course is taught in (e.g., 1, 2, 3)"
    )
    semester = models.CharField(
        max_length=20,
        choices=SEMESTER_CHOICES,
        default='first',
        help_text="Which semester this course runs in"
    )

    # ── Session Link ───────────────────────────────────────────────────────────
    academic_session = models.ForeignKey(
        'AcademicSession',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses',
        help_text="The academic session/year this course offering is tied to"
    )

    # ── Instructor ─────────────────────────────────────────────────────────────
    lecturer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='academic_courses_teaching',
        help_text="Primary lecturer/instructor for this course"
    )

    # ── Content ────────────────────────────────────────────────────────────────
    description = models.TextField(
        blank=True,
        help_text="What this course covers"
    )
    learning_outcomes = models.JSONField(
        default=list,
        blank=True,
        help_text="Specific learning outcomes for this course unit"
    )

    # ── Display ────────────────────────────────────────────────────────────────
    icon = models.CharField(
        max_length=50,
        default='book-open',
        help_text="Lucide icon name for display"
    )
    color_primary = models.CharField(max_length=20, default='blue')
    color_secondary = models.CharField(max_length=20, default='cyan')

    # ── Status & Display ───────────────────────────────────────────────────────
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['program', 'code']]
        ordering = ['year_of_study', 'semester', 'display_order', 'name']
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
        indexes = [
            models.Index(fields=['program', 'is_active']),
            models.Index(fields=['year_of_study', 'semester']),
            models.Index(fields=['course_type']),
            models.Index(fields=['academic_session']),
        ]

    def __str__(self):
        return f"{self.code} — {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.code}-{self.name}")
            original_slug = self.slug
            counter = 1
            while Course.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    # ── Convenience Properties ─────────────────────────────────────────────────
    @property
    def department(self):
        """Derived from program — no redundant FK needed."""
        return self.program.department

    @property
    def faculty(self):
        """Derived from program → department — no redundant FK needed."""
        return self.program.department.faculty

class AllRequiredPayments(models.Model):
    WHO_TO_PAY_CHOICES = [
        ("student", "Student"),
        ("staff", "Staff"),
        ("applicant", "Applicant"),
        ("other", "Other"),
    ]
    
    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name="required_payments",
        help_text="Program this payment applies to"
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="required_payments",
        help_text="Scope this payment to a specific course (optional)"
    )
    # Correct — proper FK reference
    academic_session = models.ForeignKey(
        'AcademicSession',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='required_payments'
    )
    semester = models.CharField(
        max_length=20,
        blank=True,
        choices=[('first', 'First Semester'), ('second', 'Second Semester'), ('annual', 'Annual')],
        default='annual'
    )

    purpose = models.CharField(
        max_length=255,
        help_text="Purpose of the payment (e.g., School Fees, Library Fees)"
    )

    who_to_pay = models.CharField(
        max_length=20,
        choices=WHO_TO_PAY_CHOICES,
        default="student"
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Amount to be paid"
    )

    due_date = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)

    is_active = models.BooleanField(
        default=True,
        help_text="Controls visibility of this payment"
    )

    class Meta:
        verbose_name = "Required Payment"
        verbose_name_plural = "All Required Payments"
        ordering = ["-created_at"]

    def __str__(self):
        session = self.academic_session.name if self.academic_session else 'No Session'
        program = self.program.code if self.program else 'All Programs'
        return f"{self.purpose} - {program} ({session})"

    @property
    def faculty(self):
        return self.program.department.faculty if self.program else None

    @property
    def department(self):
        return self.program.department if self.program else None


class CourseIntake(models.Model):
    """Course intake periods"""
    INTAKE_PERIOD_CHOICES = [
        ('january', 'January'),
        ('may', 'May'),
        ('september', 'September'),
    ]
    
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='intakes')
    intake_period = models.CharField(max_length=20, choices=INTAKE_PERIOD_CHOICES)
    year = models.IntegerField()
    start_date = models.DateField()
    application_deadline = models.DateField()
    available_slots = models.IntegerField(default=50, validators=[MinValueValidator(1)])
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-year', 'intake_period']
        verbose_name = 'Course Intake'
        verbose_name_plural = 'Course Intakes'
        unique_together = [['program', 'intake_period', 'year']]
    
    def __str__(self):
        return f"{self.program.name} - {self.intake_period.title()} {self.year}"


class CourseApplication(models.Model):
    """Student application for courses"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_payment', 'Pending Payment'),
        ('payment_complete', 'Payment Complete'),
        ('under_review', 'Under Review'),
        ('documents_uploaded', 'Documents Uploaded'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ]
    LANGUAGE_CHOICES = [
        ('toefl', 'TOEFL'),
        ('ielts', 'IELTS'),
        ('pte', 'PTE Academic'),
        ('duolingo', 'Duolingo English Test'),
        ('cambridge', 'Cambridge English'),
        ('none', 'None'),
    ]
    
    # Application ID
    application_id = models.CharField(max_length=20, unique=True, editable=False)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications', null=True, blank=True)
    
    # Course & Intake
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='applications')
    intake = models.ForeignKey(CourseIntake, on_delete=models.CASCADE, related_name='applications')
    study_mode = models.CharField(max_length=20, choices=Program.STUDY_MODE_CHOICES)
    
    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')])
    nationality = models.CharField(max_length=100)

    payment_status = models.CharField(max_length=20, default='pending')
    
    # Address
    address_line1 = models.CharField(max_length=200)
    address_line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    
    # Academic Background
    highest_qualification = models.CharField(max_length=100)
    institution_name = models.CharField(max_length=200)
    graduation_year = models.TextField()
    gpa_or_grade = models.CharField(max_length=20)
    language_skill = models.CharField(max_length=20, choices=LANGUAGE_CHOICES,blank=True, null=True)
    language_score = models.DecimalField(max_digits=5,decimal_places=2,blank=True,null=True,help_text="Enter test score (e.g. 7.5 for IELTS, 95 for TOEFL)")
    
    # Additional Information
    work_experience_years = models.IntegerField(default=0)
    personal_statement = models.TextField()
    how_did_you_hear = models.CharField(max_length=100, blank=True)
    scholarship = models.BooleanField(default=False)
    # Privacy & Consent
    accept_privacy_policy = models.BooleanField(default=False)
    accept_terms_conditions = models.BooleanField(default=False)
    marketing_consent = models.BooleanField(default=False)

    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=100)
    emergency_contact_phone = models.CharField(max_length=20)
    emergency_contact_relationship = models.CharField(max_length=50)
    
    # Application Status
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_applications')
    review_notes = models.TextField(blank=True)
    
    # Timestamps
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    in_processing = models.BooleanField(default=False)
    how_did_you_hear_other = models.CharField(max_length=255, blank=True)
    emergency_contact_email = models.EmailField(blank=True, null=True)
    emergency_contact_address = models.CharField(max_length=255, blank=True)

    # Admission Acceptance Tracking
    admission_accepted = models.BooleanField(
        default=False,
        help_text="Student accepted the admission offer"
    )
    admission_accepted_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Date when student accepted admission"
    )
    admission_number = models.CharField(
        max_length=20, 
        unique=True, 
        null=True, 
        blank=True,
        help_text="Unique admission number issued to student"
    )
    department_approved = models.BooleanField(
        default=False,
        help_text="Department head approved the admission"
    )
    department_approved_at = models.DateTimeField(
        null=True, 
        blank=True
    )
    department_approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='department_approved_applications'
    )
    
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
        return f"{self.application_id} - {self.first_name} {self.last_name}"

    @property
    def is_paid(self):
        """
        For free-flow applications, all statuses beyond draft are treated as paid.
        This property is kept for backward compatibility with templates.
        """
        # Free flow: draft and above are all "unlocked"
        if self.status in ['draft', 'payment_complete', 'documents_uploaded', 'under_review', 'approved', 'rejected']:
            return True
        # Legacy fallback: check actual payment record if status is pending_payment
        try:
            return self.payment.status == 'success'
        except Exception:
            return False

    def can_upload_documents(self):
        """Check if application allows document uploads (payment-free flow)"""
        allowed_statuses = ['draft', 'payment_complete', 'documents_uploaded', 'under_review']
        return self.status in allowed_statuses

    def can_submit(self):
        """Check if application can be submitted"""
        allowed_statuses = ['draft', 'payment_complete', 'documents_uploaded']
        has_documents = self.documents.exists()
        return has_documents and self.status in allowed_statuses
    
    def mark_as_submitted(self):
        """Mark application as submitted"""
        if self.can_submit():
            self.status = 'under_review'
            self.submitted_at = timezone.now()
            self.save(update_fields=['status', 'submitted_at'])
            return True
        return False

    def accept_admission(self):
        """Student accepts admission offer"""
        if self.status == 'approved' and not self.admission_accepted:
            self.admission_accepted = True
            self.admission_accepted_at = timezone.now()
            self.save(
                update_fields=[
                    'admission_accepted', 
                    'admission_accepted_at'
                ]
            )
            return True
        return False

    def issue_admission_number(self):
        """Generate and assign admission number"""
        if not self.admission_number and self.admission_accepted:
            year = timezone.now().year
            # Generate unique admission number
            self.admission_number = (
                f"ADM-{year}-{uuid.uuid4().hex[:8].upper()}"
            )
            self.save(update_fields=['admission_number'])
            return True
        return False

    def can_access_student_portal(self):
        """Check if student can access student dashboard"""
        return (
            self.status == 'approved' and
            self.admission_accepted and
            self.admission_number and
            self.department_approved
        )

    def get_full_name(self):
        """Return applicant's full name"""
        return f"{self.first_name} {self.last_name}" 
    
    def save(self, *args, **kwargs):
        if not self.application_id:
            self.application_id = f"APP-{uuid.uuid4().hex[:12].upper()}"
        
        if self.status == 'under_review' and not self.reviewed_at:
            self.reviewed_at = timezone.now()
        
        super().save(*args, **kwargs)


class ApplicationDocument(models.Model):
    """Documents uploaded for course application"""
    FILE_TYPE_CHOICES = [
        ('transcript', 'Academic Transcript'),
        ('certificate', 'Certificate/Diploma'),
        ('id_document', 'ID Document'),
        ('passport', 'Passport'),
        ('cv', 'CV/Resume'),
        ('recommendation', 'Recommendation Letter'),
        ('other', 'Other'),
    ]
    
    application = models.ForeignKey(CourseApplication, on_delete=models.CASCADE, related_name='documents')
    file_type = models.CharField(max_length=30, choices=FILE_TYPE_CHOICES)
    file = models.FileField(upload_to='applications/documents/')
    original_filename = models.CharField(max_length=255)
    file_size = models.IntegerField(help_text="File size in bytes")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Application Document'
        verbose_name_plural = 'Application Documents'
    
    def __str__(self):
        return f"{self.application.application_id} - {self.get_file_type_display()}"
    
    def get_file_size_display(self):
        """Return human-readable file size"""
        size = self.file_size
        for unit in ['bytes', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


class ApplicationPayment(models.Model):
    """Payment for course application"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('card', 'Credit/Debit Card'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    
    application = models.OneToOneField(CourseApplication, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHOD_CHOICES)
    payment_reference = models.CharField(max_length=100, unique=True)
    gateway_payment_id = models.CharField(max_length=255, blank=True)
    card_last4 = models.CharField(max_length=4, blank=True)
    card_brand = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    payment_metadata = models.JSONField(default=dict, blank=True)
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
        if not self.payment_reference:
            self.payment_reference = f"PAY-{uuid.uuid4().hex[:12].upper()}"
        
        if not self.amount:
            self.amount = self.application.program.application_fee
        
        if self.status == 'success' and not self.paid_at:
            self.paid_at = timezone.now()
        
        super().save(*args, **kwargs)
        
        if self.status == 'success' and self.paid_at:
            if self.application.status in ['draft', 'pending_payment']:
                self.application.status = 'payment_complete'
                self.application.save(update_fields=['status'])


# ==================== COURSE CATEGORIES ====================
class CourseCategory(models.Model):
    """Categories for LMS courses"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='folder')
    color = models.CharField(max_length=20, default='blue')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Course Category'
        verbose_name_plural = 'Course Categories'
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


# ==================== DISCUSSIONS ====================
class Discussion(models.Model):
    """Course discussion forum topics"""
    course = models.ForeignKey('LMSCourse', on_delete=models.CASCADE, null=True, blank=True, related_name='discussions')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discussions_started')
    is_pinned = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    views_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_pinned', '-created_at']
        verbose_name = 'Discussion'
        verbose_name_plural = 'Discussions'
        unique_together = [['course', 'slug']]
        indexes = [
            models.Index(fields=['course', '-created_at']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class DiscussionReply(models.Model):
    """Replies to discussion topics"""
    discussion = models.ForeignKey(Discussion, on_delete=models.CASCADE, related_name='replies')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discussion_replies')
    content = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='child_replies')
    is_solution = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Discussion Reply'
        verbose_name_plural = 'Discussion Replies'
    
    def __str__(self):
        return f"Reply by {self.author.username} on {self.discussion.title}"


# ==================== ENROLLMENTS ====================
class Enrollment(models.Model):
    """Student enrollment in LMS courses"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
        ('suspended', 'Suspended'),
    ]
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey('LMSCourse', on_delete=models.CASCADE, related_name='enrollments')
    enrolled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='enrollments_created')
    
    # Progress
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, validators=[MinValueValidator(0), MaxValueValidator(100)])
    completed_lessons = models.IntegerField(default=0)
    
    # Grading
    current_grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Timestamps
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_accessed = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-enrolled_at']
        verbose_name = 'Enrollment'
        verbose_name_plural = 'Enrollments'
        unique_together = [['student', 'course']]
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['course', 'status']),
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.course.title}"
    
    def update_progress(self):
        """Calculate and update progress percentage"""
        total_lessons = self.course.lessons.filter(is_active=True).count()
        if total_lessons > 0:
            completed = LessonProgress.objects.filter(
                enrollment=self,
                is_completed=True
            ).count()
            self.completed_lessons = completed
            self.progress_percentage = (completed / total_lessons) * 100
            
            # Mark as completed if all lessons done
            if self.progress_percentage >= 100 and self.status == 'active':
                self.status = 'completed'
                self.completed_at = timezone.now()
            
            self.save(update_fields=['progress_percentage', 'completed_lessons', 'status', 'completed_at'])


# ==================== HELPDESK / SUPPORT TICKETS ====================
class SupportTicket(models.Model):
    """Support tickets for student/user assistance"""
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('waiting_response', 'Waiting for Response'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    CATEGORY_CHOICES = [
        ('technical', 'Technical Issue'),
        ('account', 'Account Access'),
        ('course', 'Course Content'),
        ('payment', 'Payment/Billing'),
        ('other', 'Other'),
    ]
    
    ticket_id = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='support_tickets')
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='open')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Support Ticket'
        verbose_name_plural = 'Support Tickets'
        indexes = [
            models.Index(fields=['ticket_id']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.ticket_id} - {self.subject}"
    
    def save(self, *args, **kwargs):
        if not self.ticket_id:
            self.ticket_id = f"TKT-{uuid.uuid4().hex[:10].upper()}"
        
        if self.status == 'resolved' and not self.resolved_at:
            self.resolved_at = timezone.now()
        
        super().save(*args, **kwargs)


class TicketReply(models.Model):
    """Replies to support tickets"""
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='replies')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ticket_replies')
    message = models.TextField()
    is_internal_note = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Ticket Reply'
        verbose_name_plural = 'Ticket Replies'
    
    def __str__(self):
        return f"Reply by {self.author.username} on {self.ticket.ticket_id}"


# ==================== INVOICES ====================
class Invoice(models.Model):
    """Invoices for course payments"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    invoice_number = models.CharField(max_length=50, unique=True, editable=False)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invoices')
    course = models.ForeignKey('LMSCourse', on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    
    # Financial Details
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Dates
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    paid_date = models.DateField(null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-issue_date']
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['student', 'status']),
        ]
    
    def __str__(self):
        return f"{self.invoice_number} - {self.student.username}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = f"INV-{uuid.uuid4().hex[:12].upper()}"
        
        # Calculate tax amount
        self.tax_amount = (self.subtotal * self.tax_rate) / 100
        
        # Calculate total
        self.total_amount = self.subtotal + self.tax_amount - self.discount_amount
        
        # Update paid date
        if self.status == 'paid' and not self.paid_date:
            self.paid_date = timezone.now().date()
        
        super().save(*args, **kwargs)


# ==================== LESSON PROGRESS ====================
class LessonProgress(models.Model):
    """Track student progress through lessons"""
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey('Lesson', on_delete=models.CASCADE, related_name='student_progress')
    
    # Progress tracking
    is_completed = models.BooleanField(default=False)
    completion_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, validators=[MinValueValidator(0), MaxValueValidator(100)])
    time_spent_minutes = models.IntegerField(default=0)
    
    # Video progress (if applicable)
    video_progress_seconds = models.IntegerField(default=0)
    
    # Timestamps
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_accessed = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['lesson__display_order']
        verbose_name = 'Lesson Progress'
        verbose_name_plural = 'Lesson Progress'
        unique_together = [['enrollment', 'lesson']]
        indexes = [
            models.Index(fields=['enrollment', 'is_completed']),
        ]
    
    def __str__(self):
        return f"{self.enrollment.student.username} - {self.lesson.title} - {self.completion_percentage}%"
    
    def save(self, *args, **kwargs):
        if not self.started_at:
            self.started_at = timezone.now()
        
        if self.is_completed and not self.completed_at:
            self.completed_at = timezone.now()
            self.completion_percentage = 100.00
        
        super().save(*args, **kwargs)
        
        # Update enrollment progress
        if self.is_completed:
            self.enrollment.update_progress()


# ==================== LMS COURSES ====================
class LMSCourse(models.Model):
    """Learning Management System courses (actual learning content)"""
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    # Basic Information
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    code = models.CharField(max_length=20, unique=True)
    category = models.ForeignKey(CourseCategory, on_delete=models.SET_NULL, null=True, related_name='lms_courses')
    
    # Content
    short_description = models.TextField(max_length=500)
    description = models.TextField()
    learning_objectives = models.JSONField(default=list)
    prerequisites = models.JSONField(default=list)
    
    # Course Details
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='beginner')
    duration_hours = models.DecimalField(max_digits=5, decimal_places=1, help_text="Estimated duration in hours")
    language = models.CharField(max_length=50, default='English')
    
    # Instructor
    instructor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='lms_courses_teaching')
    instructor_name = models.CharField(max_length=100, blank=True)
    instructor_bio = models.TextField(blank=True)
    
    # Media
    thumbnail = models.ImageField(upload_to='courses/thumbnails/', blank=True, null=True)
    promo_video_url = models.URLField(blank=True)
    
    # Enrollment
    max_students = models.IntegerField(null=True, blank=True)
    enrollment_start_date = models.DateField(null=True, blank=True)
    enrollment_end_date = models.DateField(null=True, blank=True)
    
    # Status
    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    
    # Certificate
    has_certificate = models.BooleanField(default=False)
    certificate_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Fee charged to the student to receive their certificate"
    )
    certificate_template = models.CharField(max_length=100, blank=True)
    
    # SEO
    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)
    
    # Statistics
    total_enrollments = models.IntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'LMS Course'
        verbose_name_plural = 'LMS Courses'
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_published', '-created_at']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            original_slug = self.slug
            counter = 1
            while LMSCourse.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        
        if not self.instructor_name and self.instructor:
            self.instructor_name = self.instructor.get_full_name() or self.instructor.username
        
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def update_statistics(self):
        """Update course statistics"""
        self.total_enrollments = self.enrollments.count()
        
        # Calculate average rating
        ratings = self.reviews.aggregate(Avg('rating'))
        self.average_rating = ratings['rating__avg'] or 0.00
        self.total_reviews = self.reviews.count()
        
        self.save(update_fields=['total_enrollments', 'average_rating', 'total_reviews'])


class Lesson(models.Model):
    """Individual lessons within LMS courses"""
    LESSON_TYPE_CHOICES = [
        ('video', 'Video'),
        ('text', 'Text'),
        ('quiz', 'Quiz'),
        ('assignment', 'Assignment'),
        ('file', 'Downloadable File'),
    ]
    
    course = models.ForeignKey(LMSCourse, on_delete=models.CASCADE, related_name='lessons')
    section = models.ForeignKey('LessonSection', on_delete=models.SET_NULL, null=True, blank=True, related_name='lessons')
    
    # Basic Information
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPE_CHOICES, default='video')
    
    # Content
    description = models.TextField(blank=True)
    content = models.TextField(blank=True)
    
    # Video Content - URL or File Upload
    video_url = models.TextField(
        blank=True,
        null=True,
        help_text="Paste the full embed iframe code from YouTube, Vimeo, etc."
    )
    video_file = models.FileField(
        upload_to=get_video_upload_path,
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(['mp4', 'webm', 'ogg', 'avi', 'mov'])
        ],
        help_text="Or upload video file (MP4, WebM, OGG, AVI, MOV)"
    )
    video_duration_minutes = models.IntegerField(default=0)
    
    # File Content
    file = models.FileField(upload_to=get_document_upload_path, blank=True, null=True)
    
    # Settings
    is_preview = models.BooleanField(default=False, help_text="Allow preview without enrollment")
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['course', 'section', 'display_order']
        verbose_name = 'Lesson'
        verbose_name_plural = 'Lessons'
        unique_together = [['course', 'slug']]
        indexes = [
            models.Index(fields=['course', 'is_active', 'display_order']),
        ]
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    def clean(self):
        """Validate video fields"""
        from django.core.exceptions import ValidationError
        
        # For video lessons, ensure either URL or file is provided
        if self.lesson_type == 'video':
            if not self.video_url and not self.video_file:
                raise ValidationError(
                    "Video lessons require either video URL or video file"
                )
            if self.video_url and self.video_file:
                raise ValidationError(
                    "Provide either video URL or video file, not both"
                )

    def get_video_source(self):
        """Return video source (URL or file path)"""
        if self.video_file:
            return self.video_file.url
        return self.video_url or ''
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class LessonSection(models.Model):
    """Sections to organize lessons within a course"""
    course = models.ForeignKey(LMSCourse, on_delete=models.CASCADE, related_name='sections')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    description = models.TextField(blank=True)
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['course', 'display_order']
        verbose_name = 'Lesson Section'
        verbose_name_plural = 'Lesson Sections'
        unique_together = [['course', 'slug']]
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


# ==================== MESSAGES ====================
class Message(models.Model):
    """Messages between users (student-instructor, student-admin, etc.)"""
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=200)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.sender.username} to {self.recipient.username}: {self.subject}"
    
    def mark_as_read(self):
        """Mark message as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


# ==================== NOTIFICATIONS ====================
class Notification(models.Model):
    """User notifications"""
    NOTIFICATION_TYPE_CHOICES = [
        ('enrollment', 'Enrollment'),
        ('assignment', 'Assignment'),
        ('quiz', 'Quiz'),
        ('grade', 'Grade'),
        ('announcement', 'Announcement'),
        ('message', 'Message'),
        ('certificate', 'Certificate'),
        ('system', 'System'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


# ==================== PAYMENT GATEWAY ====================
class PaymentGateway(models.Model):
    """Payment gateway configuration"""
    GATEWAY_CHOICES = [
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('razorpay', 'Razorpay'),
    ]
    
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    gateway_type = models.CharField(max_length=50, choices=GATEWAY_CHOICES)
    api_key = models.CharField(max_length=255, blank=True)
    api_secret = models.CharField(max_length=255, blank=True)
    webhook_secret = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=False)
    is_test_mode = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Payment Gateway'
        verbose_name_plural = 'Payment Gateways'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Transaction(models.Model):
    """Financial transactions"""
    TRANSACTION_TYPE_CHOICES = [
        ('enrollment', 'Course Enrollment'),
        ('subscription', 'Subscription'),
        ('refund', 'Refund'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    transaction_id = models.CharField(max_length=100, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=30, choices=TRANSACTION_TYPE_CHOICES)
    
    # Financial Details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    # Gateway Details
    gateway = models.ForeignKey(PaymentGateway, on_delete=models.SET_NULL, null=True)
    gateway_transaction_id = models.CharField(max_length=255, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Related Objects
    course = models.ForeignKey(LMSCourse, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.transaction_id} - {self.user.username} - {self.amount}"
    
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
        
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
        
        super().save(*args, **kwargs)


# ==================== QUIZZES ====================
class Quiz(models.Model):
    """Quizzes for lessons"""
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    description = models.TextField(blank=True)
    instructions = models.TextField(blank=True)
    
    # Settings
    time_limit_minutes = models.IntegerField(null=True, blank=True, help_text="Leave blank for no time limit")
    passing_score = models.DecimalField(max_digits=5, decimal_places=2, default=70.00, validators=[MinValueValidator(0), MaxValueValidator(100)])
    max_attempts = models.IntegerField(default=3, help_text="Maximum number of attempts allowed")
    shuffle_questions = models.BooleanField(default=False)
    show_correct_answers = models.BooleanField(default=True, help_text="Show correct answers after submission")
    
    # Status
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['lesson', 'display_order']
        verbose_name = 'Quiz'
        verbose_name_plural = 'Quizzes'
        unique_together = [['lesson', 'slug']]
    
    def __str__(self):
        return f"{self.lesson.course.title} - {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class QuizQuestion(models.Model):
    """Questions for quizzes"""
    QUESTION_TYPE_CHOICES = [
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('short_answer', 'Short Answer'),
        ('essay', 'Essay'),
    ]
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_type = models.CharField(max_length=30, choices=QUESTION_TYPE_CHOICES)
    question_text = models.TextField()
    explanation = models.TextField(blank=True, help_text="Explanation shown after answering")
    points = models.DecimalField(max_digits=5, decimal_places=2, default=1.00, validators=[MinValueValidator(0)])
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['quiz', 'display_order']
        verbose_name = 'Quiz Question'
        verbose_name_plural = 'Quiz Questions'
    
    def __str__(self):
        return f"{self.quiz.title} - Q{self.display_order}"


class QuizAnswer(models.Model):
    """Answer choices for multiple choice questions"""
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.TextField()
    is_correct = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['question', 'display_order']
        verbose_name = 'Quiz Answer'
        verbose_name_plural = 'Quiz Answers'
    
    def __str__(self):
        return f"{self.question.question_text[:50]} - {self.answer_text[:50]}"


class QuizAttempt(models.Model):
    """Student quiz attempts"""
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    
    # Scoring
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Status
    is_completed = models.BooleanField(default=False)
    passed = models.BooleanField(default=False)
    
    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_taken_minutes = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Quiz Attempt'
        verbose_name_plural = 'Quiz Attempts'
        indexes = [
            models.Index(fields=['quiz', 'student']),
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.quiz.title} - Attempt"
    
    def calculate_score(self):
        """Calculate the score for this attempt"""
        total_score = 0
        max_score = 0
        
        for response in self.responses.all():
            max_score += float(response.question.points)
            if response.is_correct:
                total_score += float(response.question.points)
        
        self.score = Decimal(str(total_score))
        self.max_score = Decimal(str(max_score))
        
        if max_score > 0:
            self.percentage = Decimal(str((total_score / max_score) * 100))
            self.passed = self.percentage >= self.quiz.passing_score
        
        self.save(update_fields=['score', 'max_score', 'percentage', 'passed'])


class QuizResponse(models.Model):
    """Student responses to quiz questions"""
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name='responses')
    selected_answer = models.ForeignKey(QuizAnswer, on_delete=models.CASCADE, null=True, blank=True, related_name='selected_in_responses')
    text_response = models.TextField(blank=True)
    is_correct = models.BooleanField(default=False)
    points_earned = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    class Meta:
        verbose_name = 'Quiz Response'
        verbose_name_plural = 'Quiz Responses'
        unique_together = [['attempt', 'question']]
    
    def __str__(self):
        return f"{self.attempt.student.username} - {self.question.question_text[:50]}"


# ==================== REVIEWS ====================
class Review(models.Model):
    """Course reviews and ratings"""
    course = models.ForeignKey(LMSCourse, on_delete=models.CASCADE, related_name='reviews')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_reviews')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review_text = models.TextField(blank=True)
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        unique_together = [['course', 'student']]
        indexes = [
            models.Index(fields=['course', 'is_approved', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.course.title} - {self.rating}/5"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update course statistics
        self.course.update_statistics()


# ==================== SUBSCRIPTION PLANS ====================
class SubscriptionPlan(models.Model):
    """Subscription plans for premium access"""
    BILLING_CYCLE_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField()
    features = models.JSONField(default=list)
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLE_CHOICES)
    
    # Access
    max_courses = models.IntegerField(null=True, blank=True, help_text="Leave blank for unlimited")
    
    # Status
    is_active = models.BooleanField(default=True)
    is_popular = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', 'price']
        verbose_name = 'Subscription Plan'
        verbose_name_plural = 'Subscription Plans'
    
    def __str__(self):
        return f"{self.name} - {self.price} {self.currency}/{self.billing_cycle}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Subscription(models.Model):
    """User subscriptions"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name='subscriptions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Billing
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField()
    auto_renew = models.BooleanField(default=True)
    
    # Payment
    gateway_subscription_id = models.CharField(max_length=255, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['end_date']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.plan.name} - {self.status}"
    
    def is_active(self):
        """Check if subscription is currently active"""
        return self.status == 'active' and self.end_date >= timezone.now().date()


# ==================== SYSTEM CONFIGURATION ====================
class SystemConfiguration(models.Model):
    """System-wide configuration settings"""
    SETTING_TYPE_CHOICES = [
        ('text', 'Text'),
        ('number', 'Number'),
        ('boolean', 'Boolean'),
        ('json', 'JSON'),
    ]
    
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    setting_type = models.CharField(max_length=20, choices=SETTING_TYPE_CHOICES, default='text')
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=False, help_text="Can be accessed by non-admin users")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'System Configuration'
        verbose_name_plural = 'System Configurations'
        ordering = ['key']
    
    def __str__(self):
        return self.key


# ==================== USER PROFILE ====================
class UserProfile(models.Model):
    """Extended user profile"""
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('instructor', 'Instructor'),
        ('admin', 'Administrator'),
        ('content_manager', 'Content Manager'),
        ('support', 'Support Staff'),
        ('qa', 'QA Reviewer'),
        ('finance', 'Finance Manager'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='student')
    faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name="faculty_students")
    department = models.ForeignKey("Department", on_delete=models.SET_NULL, null=True, blank=True, related_name='department_students')
    program = models.ForeignKey(Program, on_delete=models.SET_NULL, null=True, blank=True, related_name='program_students')
    
    # Personal Information
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)


    
    # Address
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    
    # Social
    website = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    
    # Preferences
    email_notifications = models.BooleanField(default=True)
    marketing_emails = models.BooleanField(default=False)
    
    # Verification
    email_verified = models.BooleanField(default=False)
    verification_token = models.UUIDField(default=uuid.uuid4, editable=False)
    
    # Timestamps
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


   



# ==================== VENDOR MANAGEMENT ====================
class Vendor(models.Model):
    """Vendor/Partner institutions"""
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    email = models.EmailField()
    country = models.CharField(max_length=100, blank=True)
    stripe_account_id = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Vendor'
        verbose_name_plural = 'Vendors'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


# ==================== SIGNALS ====================
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()


@receiver(post_save, sender=Enrollment)
def update_course_enrollment_count(sender, instance, created, **kwargs):
    """Update course enrollment count when new enrollment is created"""
    if created:
        instance.course.update_statistics()


@receiver(post_save, sender=Review)
def update_course_rating(sender, instance, created, **kwargs):
    """Update course rating when review is added/modified"""
    instance.course.update_statistics()

# ==================== STUDY GROUPS ====================
class StudyGroup(models.Model):
    """Study groups for collaborative learning"""
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    course = models.ForeignKey(
        'LMSCourse', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='study_groups'
    )
    
    # Settings
    max_members = models.IntegerField(default=10)
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=True)
    
    # Creator
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='study_groups_created'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Study Group'
        verbose_name_plural = 'Study Groups'
        indexes = [
            models.Index(fields=['course', 'is_active']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            original_slug = self.slug
            counter = 1
            while StudyGroup.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)
    
    def member_count(self):
        """Get current member count"""
        return self.members.filter(is_active=True).count()
    
    def is_full(self):
        """Check if group is at max capacity"""
        return self.member_count() >= self.max_members


class StudyGroupMember(models.Model):
    """Members of study groups"""
    ROLE_CHOICES = [
        ('member', 'Member'),
        ('moderator', 'Moderator'),
        ('admin', 'Admin'),
    ]
    
    study_group = models.ForeignKey(
        StudyGroup, 
        on_delete=models.CASCADE, 
        related_name='members'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='study_group_memberships'
    )
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='member'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-joined_at']
        verbose_name = 'Study Group Member'
        verbose_name_plural = 'Study Group Members'
        unique_together = [['study_group', 'user']]
        indexes = [
            models.Index(fields=['study_group', 'is_active']),
            models.Index(fields=['user', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.username} in {self.study_group.name}"

class StudyGroupMessage(models.Model):
    """Messages posted in a study group chat"""
    study_group = models.ForeignKey(
        StudyGroup,
        on_delete=models.CASCADE,
        related_name='group_messages'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='study_group_messages'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Study Group Message'
        verbose_name_plural = 'Study Group Messages'
        indexes = [
            models.Index(fields=['study_group', 'created_at']),
        ]

    def __str__(self):
        return f"{self.author.username} in {self.study_group.name}: {self.content[:50]}"
    
# ==================== BROADCAST CENTER ====================
class BroadcastMessage(models.Model):
    """Email broadcasts to filtered recipients"""
    FILTER_TYPE_CHOICES = [
        ('all_users', 'All Users'),
        ('role', 'By User Role'),
        ('faculty', 'By Faculty'),
        ('course', 'By Course (Admission)'),
        ('lms_course', 'By LMS Course'),
        ('application_status', 'By Application Status'),
        ('enrollment_status', 'By Enrollment Status'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]
    
    # Message Details
    subject = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    message = models.TextField()
    
    # Filtering
    filter_type = models.CharField(
        max_length=30, 
        choices=FILTER_TYPE_CHOICES
    )
    
    # Filter Values (JSON for flexibility)
    filter_values = models.JSONField(
        default=dict,
        help_text="Stores selected filters"
    )
    
    # Recipients
    recipient_count = models.IntegerField(default=0)
    recipient_emails = models.JSONField(
        default=list,
        help_text="List of recipient emails"
    )
    
    # Status
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='draft'
    )
    
    # Metadata
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='broadcasts_created'
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Error tracking
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Broadcast Message'
        verbose_name_plural = 'Broadcast Messages'
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['filter_type']),
        ]
    
    def __str__(self):
        return f"{self.subject} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        # Auto-generate slug from subject
        if not self.slug:
            base_slug = slugify(self.subject)
            slug = base_slug
            counter = 1
            while BroadcastMessage.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

class StaffPayroll(models.Model):
    """
    Consolidated payroll model with integrated file storage
    Combines salary information and attachments in one table
    """
    
    # Status choices
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('on_hold', 'On Hold'),
    ]
    
    # Payment method choices
    PAYMENT_METHOD_CHOICES = [
        ('bank_transfer', 'Bank Transfer'),
        ('check', 'Check'),
        ('cash', 'Cash'),
        ('mobile_money', 'Mobile Money'),
    ]
    
    # Month choices
    MONTH_CHOICES = [
        (1, 'January'), (2, 'February'), (3, 'March'),
        (4, 'April'), (5, 'May'), (6, 'June'),
        (7, 'July'), (8, 'August'), (9, 'September'),
        (10, 'October'), (11, 'November'), (12, 'December'),
    ]
    
    # =========================================================================
    # CORE FIELDS
    # =========================================================================
    
    payroll_reference = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        db_index=True
    )
    
    staff = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payrolls',
        limit_choices_to={
            'profile__role__in': [
                'instructor',
                'support',
                'admin',
                'content_manager',
                'finance'
            ]
        },
        help_text='Select staff member (non-students only)'
    )
    
    month = models.IntegerField(choices=MONTH_CHOICES)
    year = models.IntegerField()
    
    # =========================================================================
    # SALARY FIELDS
    # =========================================================================
    
    base_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    allowances = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Housing, transport, etc.'
    )
    
    bonuses = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Performance bonuses'
    )
    
    gross_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        editable=False
    )
    
    # =========================================================================
    # DEDUCTION FIELDS
    # =========================================================================
    
    tax_deduction = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Income tax'
    )
    
    other_deductions = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Insurance, loans, etc.'
    )
    
    net_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        editable=False
    )
    
    # =========================================================================
    # PAYMENT FIELDS
    # =========================================================================
    
    payment_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='bank_transfer'
    )
    
    payment_date = models.DateField(null=True, blank=True)
    
    bank_name = models.CharField(
        max_length=100,
        blank=True,
        default=''
    )
    
    account_number = models.CharField(
        max_length=50,
        blank=True,
        default=''
    )
    
    # =========================================================================
    # FILE ATTACHMENTS - CONSOLIDATED
    # =========================================================================
    
    attachment_1 = models.FileField(
        upload_to='payroll/attachments/%Y/%m/',
        blank=True,
        null=True,
        help_text='Salary slip, contract, etc.'
    )
    
    attachment_1_name = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='Display name for attachment 1'
    )
    
    attachment_2 = models.FileField(
        upload_to='payroll/attachments/%Y/%m/',
        blank=True,
        null=True,
        help_text='Additional document'
    )
    
    attachment_2_name = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='Display name for attachment 2'
    )
    
    attachment_3 = models.FileField(
        upload_to='payroll/attachments/%Y/%m/',
        blank=True,
        null=True,
        help_text='Additional document'
    )
    
    attachment_3_name = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='Display name for attachment 3'
    )
    
    attachment_4 = models.FileField(
        upload_to='payroll/attachments/%Y/%m/',
        blank=True,
        null=True,
        help_text='Additional document'
    )
    
    attachment_4_name = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='Display name for attachment 4'
    )
    
    attachment_5 = models.FileField(
        upload_to='payroll/attachments/%Y/%m/',
        blank=True,
        null=True,
        help_text='Additional document'
    )
    
    attachment_5_name = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='Display name for attachment 5'
    )
    
    # =========================================================================
    # METADATA FIELDS
    # =========================================================================
    
    notes = models.TextField(blank=True, default='')
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='payrolls_created'
    )
    
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payrolls_approved'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-year', '-month', 'staff__username']
        unique_together = ['staff', 'month', 'year']
        verbose_name = 'Staff Payroll'
        verbose_name_plural = 'Staff Payrolls'
        indexes = [
            models.Index(fields=['payroll_reference']),
            models.Index(fields=['staff', 'month', 'year']),
            models.Index(fields=['payment_status']),
        ]
    
    def __str__(self):
        return f"{self.staff.get_full_name()} - {self.get_month_name()} {self.year}"
    
    def save(self, *args, **kwargs):
        # Generate unique reference
        if not self.payroll_reference:
            self.payroll_reference = self.generate_reference()
        
        # Calculate gross salary
        self.gross_salary = (
            self.base_salary +
            self.allowances +
            self.bonuses
        )
        
        # Calculate net salary
        self.net_salary = (
            self.gross_salary -
            self.tax_deduction -
            self.other_deductions
        )
        
        # Auto-set attachment names from filename if not set
        for i in range(1, 6):
            file_field = getattr(self, f'attachment_{i}')
            name_field = getattr(self, f'attachment_{i}_name')
            
            if file_field and not name_field:
                setattr(
                    self,
                    f'attachment_{i}_name',
                    file_field.name.split('/')[-1]
                )
        
        super().save(*args, **kwargs)
    
    def generate_reference(self):
        """Generate unique payroll reference"""
        prefix = f"PAY{self.year}{self.month:02d}"
        unique_id = str(uuid.uuid4().hex)[:8].upper()
        return f"{prefix}-{unique_id}"
    
    def get_month_name(self):
        """Get month name from number"""
        months = [
            'January', 'February', 'March', 'April',
            'May', 'June', 'July', 'August',
            'September', 'October', 'November', 'December'
        ]
        return months[self.month - 1] if 1 <= self.month <= 12 else ''
    
    def get_attachments(self):
        """
        Get list of all attachments with metadata
        Returns list of dicts with 'file', 'name', 'number'
        """
        attachments = []
        for i in range(1, 6):
            file_field = getattr(self, f'attachment_{i}')
            if file_field:
                attachments.append({
                    'number': i,
                    'file': file_field,
                    'name': getattr(self, f'attachment_{i}_name') or file_field.name.split('/')[-1],
                    'url': file_field.url,
                    'size': file_field.size if hasattr(file_field, 'size') else 0,
                })
        return attachments
    
    def has_attachments(self):
        """Check if payroll has any attachments"""
        return any([
            self.attachment_1,
            self.attachment_2,
            self.attachment_3,
            self.attachment_4,
            self.attachment_5,
        ])
    
    def get_attachment_count(self):
        """Get count of attachments"""
        return len(self.get_attachments())
    
    def can_delete(self):
        """Check if payroll can be deleted"""
        return self.payment_status != 'paid'
    
    def delete_attachment(self, number):
        """
        Delete specific attachment by number (1-5)
        """
        if 1 <= number <= 5:
            file_field = getattr(self, f'attachment_{number}')
            if file_field:
                # Delete the file from storage
                file_field.delete(save=False)
                # Clear the fields
                setattr(self, f'attachment_{number}', None)
                setattr(self, f'attachment_{number}_name', '')
                self.save()
                return True
        return False

class ListOfCountry(models.Model):
    country = models.CharField(max_length=150, unique=True)
    country_code = models.CharField(max_length=10, unique=True)
    country_phonecode = models.CharField(max_length=10)
    nationality = models.CharField(max_length=160, blank=True)

    class Meta:
        verbose_name = "Country"
        verbose_name_plural = "List of Countries"
        ordering = ["country"]

    def __str__(self):
        return f"{self.country} ({self.country_phonecode})"

class FeePayment(models.Model):
    """Payment for student required fees"""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('card', 'Credit/Debit Card'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer'),
    ]

    # 🔥 KEY DIFFERENCE
    fee = models.ForeignKey(
        'AllRequiredPayments',
        on_delete=models.CASCADE,
        related_name='payments'
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE,
        related_name='student_fee_payments'
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='GBP')

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    payment_method = models.CharField(
        max_length=30,
        choices=PAYMENT_METHOD_CHOICES,
        blank=True
    )

    payment_reference = models.CharField(
        max_length=100,
        unique=True,
        blank=True
    )

    gateway_payment_id = models.CharField(max_length=255, blank=True)

    card_last4 = models.CharField(max_length=4, blank=True)
    card_brand = models.CharField(max_length=50, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    payment_metadata = models.JSONField(default=dict, blank=True)

    failure_reason = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Fee Payment'
        verbose_name_plural = 'Fee Payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['payment_reference']),
            models.Index(fields=['status']),
        ]

    def save(self, *args, **kwargs):
        # Generate payment reference
        if not self.payment_reference:
            self.payment_reference = f"FEE-{uuid.uuid4().hex[:12].upper()}"

        # Default amount from fee
        if not self.amount:
            self.amount = self.fee.amount

        # Set paid timestamp
        if self.status == 'success' and not self.paid_at:
            self.paid_at = timezone.now()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} - {getattr(self.fee, 'purpose', 'N/A')} - {self.status}"

def library_file_upload_path(instance, filename):
    ext       = filename.split('.')[-1].lower()
    safe_name = f"{uuid.uuid4().hex}.{ext}"
    cat_slug  = slugify(instance.category or 'misc')
    return f'library/{cat_slug}/{safe_name}'
 
 
def library_cover_upload_path(instance, filename):
    name, ext = os.path.splitext(filename)
    return f'library/covers/{slugify(name)}{ext}'
 
 
class LibraryItem(models.Model):
    """
    Single-table digital library.
 
    category / subcategory are plain text — no extra lookup tables needed.
    Use them exactly as they appear on the front-end:
 
        category = "Books"        subcategory = "Apologetics Books"
        category = "Periodicals"  subcategory = "Acta Theologica"
        category = "References"   subcategory = "Dictionaries"
        category = "References"   subcategory = "Commentaries"
        …
 
    Access modes (pick one or both per record):
        A. Upload a file  (PDF / DOCX / EPUB …)
        B. Paste an external URL  (Google Drive, Project Gutenberg, etc.)
    """
 
    # ── Category (top-bar tabs on the library page) ───────────────────────────
    CATEGORY_CHOICES = [
        ('Books',       'Books'),
        ('Periodicals', 'Periodicals'),
        ('References',  'References'),
        ('Other',       'Other'),
    ]
 
    # ── Access ────────────────────────────────────────────────────────────────
    ACCESS_CHOICES = [
        ('public',  'Public – anyone can access'),
        ('members', 'Members only – must be logged in'),
    ]
 
    # ── Language ──────────────────────────────────────────────────────────────
    LANGUAGE_CHOICES = [
        ('en',    'English'),
        ('es',    'Español (Spanish)'),
        ('fr',    'Français (French)'),
        ('pt_br', 'Português (Brazil)'),
        ('ja',    '日本語 (Japanese)'),
        ('zh',    '简体中文 (Chinese Simplified)'),
        ('ko',    '한국어 (Korean)'),
        ('ur',    'اردو (Urdu)'),
        ('ar',    'العربية (Arabic)'),
        ('hi',    'हिन्दी (Hindi)'),
        ('other', 'Other'),
    ]
 
    # ── Primary key ───────────────────────────────────────────────────────────
    id   = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(max_length=260, unique=True, blank=True)
 
    # ── Taxonomy — two plain text fields, zero extra tables ───────────────────
    category    = models.CharField(
        max_length=50, choices=CATEGORY_CHOICES, default='Books',
        db_index=True,
        help_text="Top-level section: Books | Periodicals | References | Other"
    )
    subcategory = models.CharField(
        max_length=200, db_index=True,
        help_text=(
            "Sub-section label exactly as shown on the front-end, e.g. "
            "'Apologetics Books', 'Dictionaries', 'Acta Theologica', 'Commentaries' …"
        )
    )
 
    # ── Bibliographic metadata ────────────────────────────────────────────────
    title       = models.CharField(max_length=500)
    author      = models.CharField(max_length=300, blank=True,
                                   help_text="Author / Editor full name")
    publisher   = models.CharField(max_length=200, blank=True)
    year        = models.PositiveSmallIntegerField(null=True, blank=True,
                                                   help_text="Year of publication")
    edition     = models.CharField(max_length=50, blank=True,
                                   help_text="e.g. 'Vol. 2', '3rd Edition'")
    isbn        = models.CharField(max_length=30, blank=True,
                                   verbose_name='ISBN / ISSN')
    language    = models.CharField(max_length=10, choices=LANGUAGE_CHOICES,
                                   default='en')
    description = models.TextField(blank=True,
                                   help_text="Abstract, synopsis, or table of contents")
    tags        = models.CharField(max_length=500, blank=True,
                                   help_text="Comma-separated keywords for search")
 
    # ── Cover / thumbnail ─────────────────────────────────────────────────────
    cover_image = models.ImageField(
        upload_to=library_cover_upload_path, blank=True, null=True,
        help_text="Optional thumbnail shown on library cards"
    )
 
    # ── File upload ───────────────────────────────────────────────────────────
    file = models.FileField(
        upload_to=library_file_upload_path, blank=True, null=True,
        validators=[FileExtensionValidator(
            allowed_extensions=['pdf', 'doc', 'docx', 'epub', 'txt', 'pptx', 'xlsx']
        )],
        help_text="Upload PDF, DOCX, EPUB, TXT, PPTX or XLSX"
    )
    file_size_mb = models.DecimalField(max_digits=8, decimal_places=2,
                                       null=True, blank=True, editable=False,
                                       help_text="Auto-filled on save")
    file_type    = models.CharField(max_length=10, blank=True, editable=False,
                                    help_text="Auto-detected extension: pdf, docx …")
 
    # ── External link (alternative or supplement to upload) ───────────────────
    external_url = models.URLField(
        max_length=1000, blank=True,
        help_text=(
            "Paste a URL if the document is hosted externally "
            "(Google Drive, Project Gutenberg, archive.org, etc.)"
        )
    )
    external_url_label = models.CharField(
        max_length=100, blank=True, default='Read / Download',
        help_text="Front-end button label for the external link"
    )
 
    # ── Front-end behaviour flags ─────────────────────────────────────────────
    allow_download    = models.BooleanField(
        default=True,
        help_text="Show a Download button on the front-end"
    )
    allow_read_online = models.BooleanField(
        default=True,
        help_text="Show an embedded PDF viewer (Read Online) on the front-end"
    )
 
    # ── Access control ────────────────────────────────────────────────────────
    access = models.CharField(
        max_length=20, choices=ACCESS_CHOICES, default='public',
        help_text="Who can see and open this item"
    )
 
    # ── Stats & display flags ─────────────────────────────────────────────────
    view_count     = models.PositiveIntegerField(default=0, editable=False)
    download_count = models.PositiveIntegerField(default=0, editable=False)
    featured       = models.BooleanField(
        default=False,
        help_text="Pin this item to the library home / featured shelf"
    )
    is_active = models.BooleanField(default=True)
    order     = models.PositiveSmallIntegerField(
        default=0,
        help_text="Display order within the sub-category (lower number = first)"
    )
 
    # ── Audit ─────────────────────────────────────────────────────────────────
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='library_items_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
 
    class Meta:
        verbose_name        = 'Library Item'
        verbose_name_plural = 'Library Items'
        ordering            = ['category', 'subcategory', 'order', 'title']
        indexes = [
            models.Index(fields=['category', 'subcategory']),
            models.Index(fields=['access', 'is_active']),
            models.Index(fields=['featured']),
            models.Index(fields=['slug']),
        ]
 
    def __str__(self):
        author_str = f" — {self.author}" if self.author else ""
        return f"[{self.category} / {self.subcategory}] {self.title}{author_str}"
 
    def save(self, *args, **kwargs):
        # Auto-generate unique slug
        if not self.slug:
            base    = slugify(f"{self.title} {self.author}")[:250]
            slug    = base
            counter = 1
            while LibraryItem.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug    = f"{base}-{counter}"
                counter += 1
            self.slug = slug
 
        # Auto-fill file metadata
        if self.file:
            try:
                self.file_size_mb = round(self.file.size / (1024 * 1024), 2)
                self.file_type    = self.file.name.split('.')[-1].lower()
            except Exception:
                pass
 
        super().save(*args, **kwargs)
 
    # ── Convenience helpers used in templates / views ─────────────────────────
    def has_file(self):
        return bool(self.file)
 
    def has_external_url(self):
        return bool(self.external_url)
 
    def is_accessible(self):
        """True when at least one of file or external_url is present."""
        return self.has_file() or self.has_external_url()
 
    def increment_views(self):
        LibraryItem.objects.filter(pk=self.pk).update(
            view_count=models.F('view_count') + 1
        )
 
    def increment_downloads(self):
        LibraryItem.objects.filter(pk=self.pk).update(
            download_count=models.F('download_count') + 1
        )
 
    def get_file_icon(self):
        """Return a Bootstrap-icon class matching the detected file type."""
        icons = {
            'pdf':  'bi-file-earmark-pdf text-danger',
            'doc':  'bi-file-earmark-word text-primary',
            'docx': 'bi-file-earmark-word text-primary',
            'epub': 'bi-book text-success',
            'txt':  'bi-file-earmark-text text-secondary',
            'pptx': 'bi-file-earmark-slides text-warning',
            'xlsx': 'bi-file-earmark-spreadsheet text-success',
        }
        return icons.get(self.file_type, 'bi-file-earmark')
 
    @property
    def file_size_display(self):
        """Human-readable file size string."""
        if self.file_size_mb:
            return (f"{int(self.file_size_mb * 1024)} KB"
                    if self.file_size_mb < 1 else f"{self.file_size_mb} MB")
        return ''

    @property
    def tags_list(self):
        """Return tags as a clean list, split on comma."""
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(',') if t.strip()]