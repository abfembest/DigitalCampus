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
            
            # Apply late penalty
            if self.score and not self.assignment.allow_late_submission:
                penalty = (self.assignment.late_penalty_percent / 100) * self.score
                self.score = max(0, self.score - penalty)
        
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
    
    def __str__(self):
        return f"{self.student.username} - {self.course.title} - {self.certificate_id}"
    
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
    """Academic programs/courses for admissions"""
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
    available_study_modes = models.JSONField(default=list, help_text="List of available study modes")
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
    entry_requirements = models.JSONField(default=list)
    
    # Financial Information
    application_fee = models.DecimalField(max_digits=10, decimal_places=2)
    tuition_fee = models.DecimalField(max_digits=12, decimal_places=2)
    
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
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class CourseIntake(models.Model):
    """Course intake periods"""
    INTAKE_PERIOD_CHOICES = [
        ('january', 'January'),
        ('may', 'May'),
        ('september', 'September'),
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='intakes')
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
        unique_together = [['course', 'intake_period', 'year']]
    
    def __str__(self):
        return f"{self.course.name} - {self.intake_period.title()} {self.year}"


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
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='applications')
    intake = models.ForeignKey(CourseIntake, on_delete=models.CASCADE, related_name='applications')
    study_mode = models.CharField(max_length=20, choices=Course.STUDY_MODE_CHOICES)
    
    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')])
    nationality = models.CharField(max_length=100)

    payment_status = models.TextField(default="pending")
    
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
        """Check if payment is complete"""
        if not hasattr(self, 'payment'):
            return False
        return self.payment.status == 'success'

    def can_upload_documents(self):
        """Check if application allows document uploads"""
        allowed_statuses = ['payment_complete', 'documents_uploaded', 'under_review']
        return self.status in allowed_statuses and self.is_paid

    def can_submit(self):
        """Check if application can be submitted"""
        allowed_statuses = ['payment_complete', 'documents_uploaded']
        has_documents = self.documents.exists()
        return self.is_paid and has_documents and self.status in allowed_statuses
    
    def mark_as_submitted(self):
        """Mark application as submitted"""
        if self.can_submit():
            self.status = 'under_review'
            self.submitted_at = timezone.now()
            self.save(update_fields=['status', 'submitted_at'])
            return True
        return False 
    
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
            self.amount = self.application.course.application_fee
        
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
    course = models.ForeignKey('LMSCourse', on_delete=models.CASCADE, related_name='discussions')
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
    instructor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='courses_teaching')
    instructor_name = models.CharField(max_length=100, blank=True)
    instructor_bio = models.TextField(blank=True)
    
    # Media
    thumbnail = models.ImageField(upload_to='courses/thumbnails/', blank=True, null=True)
    promo_video_url = models.URLField(blank=True)
    
    # Pricing
    is_free = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Enrollment
    max_students = models.IntegerField(null=True, blank=True)
    enrollment_start_date = models.DateField(null=True, blank=True)
    enrollment_end_date = models.DateField(null=True, blank=True)
    
    # Status
    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    
    # Certificate
    has_certificate = models.BooleanField(default=False)
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
    
    # Video Content
    video_url = models.URLField(blank=True, help_text="YouTube, Vimeo URL or local storage path")
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