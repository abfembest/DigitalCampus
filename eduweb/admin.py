from django.contrib import admin
from django.utils import timezone
from .models import (
    Announcement, Assignment, AssignmentSubmission, AuditLog,
    Badge, StudentBadge, BlogCategory, BlogPost,
    Certificate, ContactMessage,
    Course, CourseIntake, CourseApplication, ApplicationDocument, ApplicationPayment,
    CourseCategory, Discussion, DiscussionReply,
    Department, Program, AllRequiredPayments,
    Enrollment, Faculty, Invoice, Lesson, LessonSection, LessonProgress,
    LMSCourse, Message, Notification,
    PaymentGateway, Transaction, Quiz, QuizQuestion, QuizAnswer, QuizAttempt, QuizResponse,
    Review, SubscriptionPlan, Subscription, SupportTicket, TicketReply,
    StaffPayroll, StudyGroup, StudyGroupMember,
    SystemConfiguration, UserProfile, Vendor, BroadcastMessage
)


# ==================== ANNOUNCEMENTS ====================
@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'announcement_type', 'priority', 'is_active', 'publish_date', 'created_by')
    list_filter = ('announcement_type', 'priority', 'is_active', 'publish_date')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'publish_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'content', 'announcement_type', 'priority')
        }),
        ('Targeting', {
            'fields': ('course', 'category')
        }),
        ('Publishing', {
            'fields': ('is_active', 'publish_date', 'expiry_date', 'created_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ==================== ASSIGNMENTS ====================
@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson', 'due_date', 'max_score', 'passing_score', 'is_active', 'display_order')
    list_filter = ('lesson__course', 'is_active', 'due_date')
    search_fields = ('title', 'description', 'lesson__title')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('is_active', 'display_order')
    date_hierarchy = 'due_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('lesson', 'title', 'slug', 'description', 'instructions')
        }),
        ('Grading', {
            'fields': ('max_score', 'passing_score')
        }),
        ('Deadlines', {
            'fields': ('due_date', 'allow_late_submission', 'late_penalty_percent')
        }),
        ('Attachment', {
            'fields': ('attachment',)
        }),
        ('Settings', {
            'fields': ('is_active', 'display_order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'assignment', 'status', 'score', 'is_late', 'submitted_at', 'graded_by')
    list_filter = ('status', 'is_late', 'submitted_at')
    search_fields = ('student__username', 'assignment__title')
    readonly_fields = ('submitted_at', 'graded_at', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Submission', {
            'fields': ('assignment', 'student', 'submission_text', 'attachment')
        }),
        ('Grading', {
            'fields': ('score', 'feedback', 'graded_by', 'graded_at')
        }),
        ('Status', {
            'fields': ('status', 'is_late')
        }),
        ('Timestamps', {
            'fields': ('submitted_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ==================== AUDIT LOGS ====================
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'model_name', 'object_id', 'ip_address', 'timestamp')
    list_filter = ('action', 'model_name', 'timestamp')
    search_fields = ('user__username', 'model_name', 'description')
    readonly_fields = ('user', 'action', 'model_name', 'object_id', 'description', 'ip_address', 'user_agent', 'extra_data', 'timestamp')
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


# ==================== BADGES ====================
@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'color', 'points', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'icon', 'color')
        }),
        ('Criteria', {
            'fields': ('criteria', 'points')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(StudentBadge)
class StudentBadgeAdmin(admin.ModelAdmin):
    list_display = ('student', 'badge', 'awarded_by', 'awarded_at')
    list_filter = ('badge', 'awarded_at')
    search_fields = ('student__username', 'badge__name')
    readonly_fields = ('awarded_at',)
    
    fieldsets = (
        ('Badge Award', {
            'fields': ('student', 'badge', 'awarded_by', 'reason')
        }),
        ('Timestamp', {
            'fields': ('awarded_at',)
        }),
    )


# ==================== BLOG ====================
@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'get_post_count', 'icon', 'color', 'display_order', 'is_active')
    list_filter = ('is_active', 'color')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('display_order', 'is_active')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Display Settings', {
            'fields': ('icon', 'color', 'display_order', 'is_active')
        }),
    )
    
    def get_post_count(self, obj):
        return obj.get_post_count()
    get_post_count.short_description = 'Published Posts'


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'author_name', 'category', 'status', 
        'is_featured', 'views_count', 'publish_date', 'created_at'
    )
    list_filter = (
        'status', 'is_featured', 'category', 
        'publish_date', 'created_at'
    )
    search_fields = ('title', 'subtitle', 'content', 'author_name')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('status', 'is_featured')
    readonly_fields = ('created_at', 'updated_at', 'views_count')
    date_hierarchy = 'publish_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'subtitle', 'category')
        }),
        ('Content', {
            'fields': ('excerpt', 'content')
        }),
        ('Author Information', {
            'fields': ('author', 'author_name', 'author_title')
        }),
        ('Media', {
            'fields': ('featured_image', 'featured_image_alt'),
            'classes': ('collapse',)
        }),
        ('Categorization', {
            'fields': ('tags',),
            'classes': ('collapse',)
        }),
        ('Publishing', {
            'fields': ('status', 'is_featured', 'publish_date')
        }),
        ('Metadata', {
            'fields': ('read_time', 'views_count'),
            'classes': ('collapse',)
        }),
        ('SEO', {
            'fields': ('meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['publish_posts', 'unpublish_posts', 'feature_posts']
    
    def publish_posts(self, request, queryset):
        updated = queryset.update(status='published', publish_date=timezone.now())
        self.message_user(request, f'{updated} post(s) published.')
    publish_posts.short_description = "Publish selected posts"
    
    def unpublish_posts(self, request, queryset):
        updated = queryset.update(status='draft')
        self.message_user(request, f'{updated} post(s) unpublished.')
    unpublish_posts.short_description = "Unpublish selected posts"
    
    def feature_posts(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} post(s) featured.')
    feature_posts.short_description = "Feature selected posts"


# ==================== CERTIFICATES ====================
@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('certificate_id', 'student', 'course', 'issued_date', 'completion_date', 'is_verified')
    list_filter = ('is_verified', 'issued_date')
    search_fields = ('certificate_id', 'student__username', 'course__title')
    readonly_fields = ('certificate_id', 'verification_code', 'created_at')
    
    fieldsets = (
        ('Certificate Information', {
            'fields': ('student', 'course', 'certificate_id', 'verification_code')
        }),
        ('Details', {
            'fields': ('issued_date', 'completion_date', 'grade', 'is_verified')
        }),
        ('File', {
            'fields': ('certificate_file',)
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )


# ==================== CONTACT ====================
@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at', 'is_read', 'responded', 'responded_by')
    list_filter = ('subject', 'is_read', 'responded', 'created_at')
    search_fields = ('name', 'email', 'message')
    readonly_fields = ('created_at', 'responded_at')
    list_editable = ('is_read', 'responded')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'subject')
        }),
        ('Message', {
            'fields': ('message',)
        }),
        ('Status', {
            'fields': ('is_read', 'responded', 'responded_by', 'responded_at', 'created_at')
        }),
    )


# ==================== COURSE APPLICATION SYSTEM ====================
@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'student_count', 'is_active', 'display_order', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'code', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active', 'display_order')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'code', 'is_active', 'display_order')
        }),
        ('Display Settings', {
            'fields': ('icon', 'color_primary', 'color_secondary', 'tagline')
        }),
        ('Content', {
            'fields': ('description', 'mission', 'vision')
        }),
        ('Media', {
            'fields': ('hero_image', 'about_image'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('student_count', 'placement_rate', 'partner_count', 'international_faculty')
        }),
        ('Additional Information', {
            'fields': ('accreditation', 'special_features'),
            'classes': ('collapse',)
        }),
        ('SEO', {
            'fields': ('meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'code', 'faculty', 'department', 'program', 'degree_level', 'duration_years', 
        'application_fee', 'tuition_fee', 'is_active', 'is_featured', 'display_order'
    )
    list_filter = ('faculty', 'department', 'degree_level', 'is_active', 'is_featured', 'created_at')
    search_fields = ('name', 'code', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active', 'is_featured', 'display_order')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'code', 'faculty', 'department', 'program', 'is_active', 'is_featured', 'display_order')
        }),
        ('Display Settings', {
            'fields': ('icon', 'color_primary', 'color_secondary', 'tagline')
        }),
        ('Program Details', {
            'fields': (
                'degree_level', 'available_study_modes', 'duration_years', 
                'credits_required'
            )
        }),
        ('Financial Information', {
            'fields': ('application_fee', 'tuition_fee')
        }),
        ('Content', {
            'fields': ('overview', 'description')
        }),
        ('Learning & Career', {
            'fields': ('learning_outcomes', 'career_paths'),
            'classes': ('collapse',)
        }),
        ('Curriculum', {
            'fields': ('core_courses', 'specialization_tracks'),
            'classes': ('collapse',)
        }),
        ('Admission Requirements', {
            'fields': ('entry_requirements',),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('avg_starting_salary', 'job_placement_rate')
        }),
        ('Media', {
            'fields': ('hero_image',),
            'classes': ('collapse',)
        }),
        ('SEO', {
            'fields': ('meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CourseIntake)
class CourseIntakeAdmin(admin.ModelAdmin):
    list_display = (
        'course', 'intake_period', 'year', 'start_date', 
        'application_deadline', 'available_slots', 'is_active'
    )
    list_filter = ('intake_period', 'year', 'is_active', 'course__faculty')
    search_fields = ('course__name', 'course__code')
    list_editable = ('is_active',)
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Course & Period', {
            'fields': ('course', 'intake_period', 'year')
        }),
        ('Dates', {
            'fields': ('start_date', 'application_deadline')
        }),
        ('Capacity', {
            'fields': ('available_slots', 'is_active')
        }),
    )


class ApplicationDocumentInline(admin.TabularInline):
    model = ApplicationDocument
    extra = 0
    readonly_fields = ('file', 'file_type', 'original_filename', 'file_size', 'uploaded_at')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


class ApplicationPaymentInline(admin.StackedInline):
    model = ApplicationPayment
    extra = 0
    readonly_fields = (
        'payment_reference', 'amount', 'currency', 'status', 
        'payment_method', 'gateway_payment_id', 'card_last4', 
        'card_brand', 'created_at', 'paid_at', 'updated_at'
    )
    can_delete = False
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('payment_reference', 'amount', 'currency', 'status', 'payment_method')
        }),
        ('Gateway Details', {
            'fields': ('gateway_payment_id', 'card_last4', 'card_brand'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'paid_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Additional Info', {
            'fields': ('payment_metadata', 'failure_reason'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(CourseApplication)
class CourseApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'application_id', 
        'get_full_name', 
        'email', 
        'course',
        'intake',
        'status',
        'admission_accepted',
        'admission_number',
        'department_approved',
        'submitted_at', 
        'created_at',
        'payment_status',
        'in_processing'
    )
    list_filter = (
        'status',
        'admission_accepted',
        'department_approved',
        'course__faculty',
        'course',
        'intake__year',
        'created_at',
        'payment_status'
    )
    search_fields = (
        'application_id',
        'admission_number',
        'first_name',
        'last_name',
        'email',
        'phone'
    )
    readonly_fields = (
        'application_id',
        'admission_number',
        'submitted_at',
        'reviewed_at',
        'admission_accepted_at',
        'department_approved_at',
        'created_at',
        'updated_at'
    )
    date_hierarchy = 'created_at'
    inlines = [ApplicationDocumentInline, ApplicationPaymentInline]
    
    fieldsets = (
        ('Application Info', {
            'fields': ('application_id', 'status', 'reviewer', 'review_notes')
        }),
        ('Admission Acceptance Tracking', {
            'fields': (
                'admission_accepted',
                'admission_accepted_at',
                'admission_number',
                'department_approved',
                'department_approved_at',
                'department_approved_by'
            ),
            'classes': ('collapse',),
            'description': 'Track student admission acceptance and department approval'
        }),
        ('Course Selection', {
            'fields': ('course', 'intake', 'study_mode')
        }),
        ('Personal Information', {
            'fields': (
                'first_name', 'last_name', 'email', 'phone',
                'date_of_birth', 'gender', 'nationality'
            )
        }),
        ('Address', {
            'fields': (
                'address_line1', 'address_line2', 'city',
                'state', 'postal_code', 'country'
            ),
            'classes': ('collapse',)
        }),
        ('Academic Background', {
            'fields': (
                'highest_qualification', 'institution_name',
                'graduation_year', 'gpa_or_grade'
            )
        }),
        ('Additional Information', {
            'fields': (
                'work_experience_years', 'personal_statement',
                'how_did_you_hear'
            ),
            'classes': ('collapse',)
        }),
        ('Emergency Contact', {
            'fields': (
                'emergency_contact_name', 'emergency_contact_phone',
                'emergency_contact_relationship'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'submitted_at', 
                'reviewed_at', 
                'created_at', 
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    get_full_name.short_description = 'Full Name'
    get_full_name.admin_order_field = 'first_name'


@admin.register(ApplicationDocument)
class ApplicationDocumentAdmin(admin.ModelAdmin):
    list_display = (
        'application',
        'file_type',
        'original_filename',
        'file_size',
        'uploaded_at'
    )
    list_filter = ('file_type', 'uploaded_at')
    search_fields = (
        'application__application_id',
        'application__first_name',
        'application__last_name',
        'original_filename'
    )
    readonly_fields = (
        'application',
        'file',
        'file_type',
        'original_filename',
        'file_size',
        'uploaded_at'
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ApplicationPayment)
class ApplicationPaymentAdmin(admin.ModelAdmin):
    list_display = (
        'payment_reference', 'application', 'amount', 'currency',
        'status', 'payment_method', 'paid_at', 'created_at'
    )
    list_filter = ('status', 'payment_method', 'currency', 'created_at', 'paid_at')
    search_fields = (
        'payment_reference', 'gateway_payment_id',
        'application__application_id', 'application__email'
    )
    readonly_fields = (
        'payment_reference', 'application', 'amount', 'currency',
        'gateway_payment_id', 'card_last4', 'card_brand',
        'created_at', 'paid_at', 'updated_at'
    )
    date_hierarchy = 'created_at'
    
    def has_add_permission(self, request):
        return False
    
    actions = ['mark_as_success', 'mark_as_failed']
    
    def mark_as_success(self, request, queryset):
        updated = queryset.filter(status='processing').update(
            status='success',
            paid_at=timezone.now()
        )
        self.message_user(request, f'{updated} payment(s) marked as successful.')
    mark_as_success.short_description = "Mark selected as Successful"
    
    def mark_as_failed(self, request, queryset):
        updated = queryset.filter(status='processing').update(status='failed')
        self.message_user(request, f'{updated} payment(s) marked as failed.')
    mark_as_failed.short_description = "Mark selected as Failed"


# ==================== COURSE CATEGORIES ====================
@admin.register(CourseCategory)
class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent', 'icon', 'color', 'display_order', 'is_active')
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('display_order', 'is_active')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'parent')
        }),
        ('Display Settings', {
            'fields': ('icon', 'color', 'display_order', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ==================== DISCUSSIONS ====================
@admin.register(Discussion)
class DiscussionAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'author', 'is_pinned', 'is_locked', 'views_count', 'created_at')
    list_filter = ('is_pinned', 'is_locked', 'course', 'created_at')
    search_fields = ('title', 'content', 'author__username')
    readonly_fields = ('views_count', 'created_at', 'updated_at')
    list_editable = ('is_pinned', 'is_locked')
    
    fieldsets = (
        ('Discussion Information', {
            'fields': ('course', 'title', 'slug', 'content', 'author')
        }),
        ('Settings', {
            'fields': ('is_pinned', 'is_locked', 'views_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DiscussionReply)
class DiscussionReplyAdmin(admin.ModelAdmin):
    list_display = ('discussion', 'author', 'is_solution', 'created_at')
    list_filter = ('is_solution', 'created_at')
    search_fields = ('discussion__title', 'author__username', 'content')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Reply Information', {
            'fields': ('discussion', 'author', 'content', 'parent', 'is_solution')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ==================== ENROLLMENTS ====================
@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'status', 'progress_percentage', 'enrolled_at', 'completed_at')
    list_filter = ('status', 'course', 'enrolled_at', 'completed_at')
    search_fields = ('student__username', 'course__title')
    readonly_fields = ('enrolled_at', 'completed_at', 'last_accessed')
    
    fieldsets = (
        ('Enrollment Information', {
            'fields': ('student', 'course', 'enrolled_by', 'status')
        }),
        ('Progress', {
            'fields': ('progress_percentage', 'completed_lessons', 'current_grade')
        }),
        ('Timestamps', {
            'fields': ('enrolled_at', 'completed_at', 'last_accessed'),
            'classes': ('collapse',)
        }),
    )


# ==================== HELPDESK / SUPPORT ====================
@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_id', 'user', 'category', 'subject', 'priority', 'status', 'assigned_to', 'created_at')
    list_filter = ('status', 'priority', 'category', 'created_at')
    search_fields = ('ticket_id', 'user__username', 'subject', 'description')
    readonly_fields = ('ticket_id', 'created_at', 'updated_at', 'resolved_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Ticket Information', {
            'fields': ('ticket_id', 'user', 'category', 'subject', 'description')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority', 'assigned_to')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'resolved_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TicketReply)
class TicketReplyAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'author', 'is_internal_note', 'created_at')
    list_filter = ('is_internal_note', 'created_at')
    search_fields = ('ticket__ticket_id', 'author__username', 'message')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Reply Information', {
            'fields': ('ticket', 'author', 'message', 'is_internal_note')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )


# ==================== INVOICES ====================
@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'student', 'course', 'total_amount', 'status', 'issue_date', 'due_date')
    list_filter = ('status', 'issue_date', 'due_date')
    search_fields = ('invoice_number', 'student__username', 'course__title')
    readonly_fields = ('invoice_number', 'issue_date', 'created_at', 'updated_at', 'tax_amount', 'total_amount')
    
    fieldsets = (
        ('Invoice Information', {
            'fields': ('invoice_number', 'student', 'course', 'status')
        }),
        ('Financial Details', {
            'fields': ('subtotal', 'tax_rate', 'tax_amount', 'discount_amount', 'total_amount', 'currency')
        }),
        ('Dates', {
            'fields': ('issue_date', 'due_date', 'paid_date')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ==================== LESSON PROGRESS ====================
@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'lesson', 'is_completed', 'completion_percentage', 'time_spent_minutes', 'last_accessed')
    list_filter = ('is_completed', 'lesson__course', 'last_accessed')
    search_fields = ('enrollment__student__username', 'lesson__title')
    readonly_fields = ('started_at', 'completed_at', 'last_accessed')
    
    fieldsets = (
        ('Progress Information', {
            'fields': ('enrollment', 'lesson', 'is_completed', 'completion_percentage', 'time_spent_minutes')
        }),
        ('Video Progress', {
            'fields': ('video_progress_seconds',)
        }),
        ('Timestamps', {
            'fields': ('started_at', 'completed_at', 'last_accessed'),
            'classes': ('collapse',)
        }),
    )


# ==================== LMS COURSES ====================
@admin.register(LMSCourse)
class LMSCourseAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'code', 'category', 'instructor_name', 'difficulty_level',
        'price', 'is_free', 'is_published', 'is_featured', 'total_enrollments'
    )
    list_filter = (
        'category', 'difficulty_level', 'is_free', 'is_published',
        'is_featured', 'created_at'
    )
    search_fields = ('title', 'code', 'description', 'instructor_name')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('is_published', 'is_featured')
    readonly_fields = (
        'total_enrollments', 'average_rating', 'total_reviews',
        'created_at', 'updated_at', 'published_at'
    )
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'code', 'category')
        }),
        ('Content', {
            'fields': ('short_description', 'description', 'learning_objectives', 'prerequisites')
        }),
        ('Course Details', {
            'fields': ('difficulty_level', 'duration_hours', 'language')
        }),
        ('Instructor', {
            'fields': ('instructor', 'instructor_name', 'instructor_bio')
        }),
        ('Media', {
            'fields': ('thumbnail', 'promo_video_url'),
            'classes': ('collapse',)
        }),
        ('Pricing', {
            'fields': ('is_free', 'price', 'discount_price')
        }),
        ('Enrollment', {
            'fields': ('max_students', 'enrollment_start_date', 'enrollment_end_date')
        }),
        ('Status', {
            'fields': ('is_published', 'is_featured')
        }),
        ('Certificate', {
            'fields': ('has_certificate', 'certificate_template')
        }),
        ('SEO', {
            'fields': ('meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('total_enrollments', 'average_rating', 'total_reviews'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'section', 'lesson_type', 'is_preview', 'is_active', 'display_order')
    list_filter = ('lesson_type', 'is_preview', 'is_active', 'course')
    search_fields = ('title', 'description', 'course__title')
    list_editable = ('is_active', 'display_order')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('course', 'section', 'title', 'slug', 'lesson_type')
        }),
        ('Content', {
            'fields': ('description', 'content')
        }),
        ('Video Content', {
            'fields': ('video_url', 'video_duration_minutes')
        }),
        ('File Content', {
            'fields': ('file',)
        }),
        ('Settings', {
            'fields': ('is_preview', 'is_active', 'display_order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(LessonSection)
class LessonSectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'display_order', 'is_active')
    list_filter = ('is_active', 'course')
    search_fields = ('title', 'description', 'course__title')
    list_editable = ('display_order', 'is_active')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Section Information', {
            'fields': ('course', 'title', 'slug', 'description')
        }),
        ('Settings', {
            'fields': ('display_order', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ==================== MESSAGES ====================
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'subject', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('sender__username', 'recipient__username', 'subject', 'body')
    readonly_fields = ('created_at', 'read_at')
    
    fieldsets = (
        ('Message Information', {
            'fields': ('sender', 'recipient', 'subject', 'body', 'parent')
        }),
        ('Status', {
            'fields': ('is_read', 'read_at')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )


# ==================== NOTIFICATIONS ====================
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'title', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'title', 'message')
    readonly_fields = ('created_at', 'read_at')
    
    fieldsets = (
        ('Notification Information', {
            'fields': ('user', 'notification_type', 'title', 'message', 'link')
        }),
        ('Status', {
            'fields': ('is_read', 'read_at')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )


# ==================== PAYMENT GATEWAY ====================
@admin.register(PaymentGateway)
class PaymentGatewayAdmin(admin.ModelAdmin):
    list_display = ('name', 'gateway_type', 'is_active', 'is_test_mode', 'created_at')
    list_filter = ('gateway_type', 'is_active', 'is_test_mode')
    search_fields = ('name', 'gateway_type')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'gateway_type')
        }),
        ('Credentials', {
            'fields': ('api_key', 'api_secret', 'webhook_secret')
        }),
        ('Settings', {
            'fields': ('is_active', 'is_test_mode')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'user', 'transaction_type', 'amount', 'status', 'created_at')
    list_filter = ('transaction_type', 'status', 'created_at')
    search_fields = ('transaction_id', 'user__username', 'gateway_transaction_id')
    readonly_fields = ('transaction_id', 'created_at', 'completed_at')
    
    fieldsets = (
        ('Transaction Information', {
            'fields': ('transaction_id', 'user', 'transaction_type', 'status')
        }),
        ('Financial Details', {
            'fields': ('amount', 'currency')
        }),
        ('Gateway Details', {
            'fields': ('gateway', 'gateway_transaction_id')
        }),
        ('Related Objects', {
            'fields': ('course',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )


# ==================== QUIZZES ====================
@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson', 'passing_score', 'max_attempts', 'is_active', 'display_order')
    list_filter = ('lesson__course', 'is_active')
    search_fields = ('title', 'description', 'lesson__title')
    list_editable = ('is_active', 'display_order')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('lesson', 'title', 'slug', 'description', 'instructions')
        }),
        ('Settings', {
            'fields': (
                'time_limit_minutes', 'passing_score', 'max_attempts',
                'shuffle_questions', 'show_correct_answers'
            )
        }),
        ('Status', {
            'fields': ('is_active', 'display_order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'question_type', 'get_question_preview', 'points', 'display_order', 'is_active')
    list_filter = ('question_type', 'is_active', 'quiz__lesson__course')
    search_fields = ('question_text', 'quiz__title')
    list_editable = ('display_order', 'is_active')
    
    fieldsets = (
        ('Question Information', {
            'fields': ('quiz', 'question_type', 'question_text', 'explanation', 'points')
        }),
        ('Settings', {
            'fields': ('display_order', 'is_active')
        }),
    )
    
    def get_question_preview(self, obj):
        return obj.question_text[:50] + "..." if len(obj.question_text) > 50 else obj.question_text
    get_question_preview.short_description = 'Question'


@admin.register(QuizAnswer)
class QuizAnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'get_answer_preview', 'is_correct', 'display_order')
    list_filter = ('is_correct', 'question__quiz__lesson__course')
    search_fields = ('answer_text', 'question__question_text')
    
    fieldsets = (
        ('Answer Information', {
            'fields': ('question', 'answer_text', 'is_correct', 'display_order')
        }),
    )
    
    def get_answer_preview(self, obj):
        return obj.answer_text[:50] + "..." if len(obj.answer_text) > 50 else obj.answer_text
    get_answer_preview.short_description = 'Answer'


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('student', 'quiz', 'score', 'percentage', 'passed', 'is_completed', 'started_at')
    list_filter = ('is_completed', 'passed', 'quiz__lesson__course')
    search_fields = ('student__username', 'quiz__title')
    readonly_fields = ('started_at', 'completed_at')
    
    fieldsets = (
        ('Attempt Information', {
            'fields': ('quiz', 'student')
        }),
        ('Scoring', {
            'fields': ('score', 'max_score', 'percentage', 'passed')
        }),
        ('Status', {
            'fields': ('is_completed', 'time_taken_minutes')
        }),
        ('Timestamps', {
            'fields': ('started_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(QuizResponse)
class QuizResponseAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'question', 'is_correct', 'points_earned')
    list_filter = ('is_correct', 'attempt__quiz__lesson__course')
    search_fields = ('attempt__student__username', 'question__question_text')
    
    fieldsets = (
        ('Response Information', {
            'fields': ('attempt', 'question', 'selected_answer', 'text_response')
        }),
        ('Grading', {
            'fields': ('is_correct', 'points_earned')
        }),
    )


# ==================== REVIEWS ====================
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('course', 'student', 'rating', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved', 'course', 'created_at')
    search_fields = ('course__title', 'student__username', 'review_text')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('is_approved',)
    
    fieldsets = (
        ('Review Information', {
            'fields': ('course', 'student', 'rating', 'review_text')
        }),
        ('Status', {
            'fields': ('is_approved',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ==================== SUBSCRIPTION PLANS ====================
@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'billing_cycle', 'is_active', 'is_popular', 'display_order')
    list_filter = ('billing_cycle', 'is_active', 'is_popular')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active', 'is_popular', 'display_order')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'features')
        }),
        ('Pricing', {
            'fields': ('price', 'currency', 'billing_cycle')
        }),
        ('Access', {
            'fields': ('max_courses',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_popular', 'display_order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'status', 'start_date', 'end_date', 'auto_renew')
    list_filter = ('status', 'auto_renew', 'plan')
    search_fields = ('user__username', 'plan__name', 'gateway_subscription_id')
    readonly_fields = ('created_at', 'updated_at', 'cancelled_at')
    
    fieldsets = (
        ('Subscription Information', {
            'fields': ('user', 'plan', 'status')
        }),
        ('Billing', {
            'fields': ('start_date', 'end_date', 'auto_renew')
        }),
        ('Payment', {
            'fields': ('gateway_subscription_id',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'cancelled_at'),
            'classes': ('collapse',)
        }),
    )


# ==================== SYSTEM CONFIGURATION ====================
@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    list_display = ('key', 'setting_type', 'is_public', 'updated_by', 'updated_at')
    list_filter = ('setting_type', 'is_public')
    search_fields = ('key', 'value', 'description')
    readonly_fields = ('updated_at',)
    
    fieldsets = (
        ('Configuration', {
            'fields': ('key', 'value', 'setting_type', 'description')
        }),
        ('Permissions', {
            'fields': ('is_public', 'updated_by')
        }),
        ('Timestamp', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )


# ==================== USER PROFILE ====================
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'email_verified', 'phone', 'country', 'created_at')
    list_filter = ('role', 'email_verified', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone', 'country')
    readonly_fields = ('verification_token', 'created_at', 'updated_at')
    
    fieldsets = (
        ('User', {
            'fields': ('user', 'role')
        }),
        ('Personal Information', {
            'fields': ('bio', 'avatar', 'phone', 'date_of_birth')
        }),
        ('Address', {
            'fields': ('address', 'city', 'country'),
            'classes': ('collapse',)
        }),
        ('Social', {
            'fields': ('website', 'linkedin', 'twitter'),
            'classes': ('collapse',)
        }),
        ('Preferences', {
            'fields': ('email_notifications', 'marketing_emails')
        }),
        ('Verification', {
            'fields': ('email_verified', 'verification_token')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ==================== VENDOR ====================
@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'country', 'is_active', 'created_at')
    list_filter = ('is_active', 'country', 'created_at')
    search_fields = ('name', 'email', 'stripe_account_id')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active',)
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'email', 'country')
        }),
        ('Integration', {
            'fields': ('stripe_account_id',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'created_at')
        }),
    )

@admin.register(BroadcastMessage)
class BroadcastMessageAdmin(admin.ModelAdmin):
    list_display = (
        'subject',
        'filter_type',
        'recipient_count',
        'status',
        'created_by',
        'created_at',
        'sent_at'
    )
    list_filter = (
        'status',
        'filter_type',
        'created_at',
        'sent_at'
    )
    search_fields = (
        'subject',
        'message',
        'created_by__username'
    )
    readonly_fields = (
        'slug',
        'recipient_count',
        'recipient_emails',
        'sent_at',
        'created_at',
        'updated_at',
        'error_message'
    )
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Message Content', {
            'fields': ('subject', 'slug', 'message')
        }),
        ('Recipients', {
            'fields': (
                'filter_type',
                'filter_values',
                'recipient_count',
                'recipient_emails'
            )
        }),
        ('Status', {
            'fields': ('status', 'sent_at', 'error_message')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Make fields readonly after message is sent"""
        readonly = list(self.readonly_fields)
        if obj and obj.status == 'sent':
            readonly.extend(['subject', 'message', 'filter_type', 'filter_values'])
        return readonly
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of sent messages"""
        if obj and obj.status == 'sent':
            return False
        return super().has_delete_permission(request, obj)


# ==================== DEPARTMENT ====================
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'faculty', 'is_active', 'display_order', 'created_at')
    list_filter = ('faculty', 'is_active', 'created_at')
    search_fields = ('name', 'code', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active', 'display_order')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'code', 'faculty', 'is_active', 'display_order')
        }),
        ('Content', {
            'fields': ('description',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ==================== PROGRAM ====================
@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'code', 'department', 'degree_level', 'duration_years',
        'application_fee', 'tuition_fee', 'is_active', 'is_featured', 'display_order'
    )
    list_filter = ('department__faculty', 'department', 'degree_level', 'is_active', 'is_featured')
    search_fields = ('name', 'code', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active', 'is_featured', 'display_order')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'code', 'department', 'degree_level', 'is_active', 'is_featured', 'display_order')
        }),
        ('Program Details', {
            'fields': ('duration_years', 'credits_required', 'max_students')
        }),
        ('Financial Information', {
            'fields': ('application_fee', 'tuition_fee')
        }),
        ('Content', {
            'fields': ('description', 'entry_requirements'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ==================== ALL REQUIRED PAYMENTS ====================
@admin.register(AllRequiredPayments)
class AllRequiredPaymentsAdmin(admin.ModelAdmin):
    list_display = (
        'purpose', 'faculty', 'department', 'program', 'course',
        'amount', 'who_to_pay', 'semester', 'academic_year', 'is_active', 'due_date'
    )
    list_filter = ('faculty', 'department', 'who_to_pay', 'semester', 'is_active', 'academic_year')
    search_fields = ('purpose', 'faculty__name', 'department__name', 'program__name')
    list_editable = ('is_active',)
    readonly_fields = ('created_at',)

    fieldsets = (
        ('Scope', {
            'fields': ('faculty', 'department', 'program', 'course')
        }),
        ('Payment Details', {
            'fields': ('purpose', 'amount', 'who_to_pay', 'semester', 'academic_year', 'due_date')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


# ==================== STUDY GROUPS ====================
@admin.register(StudyGroup)
class StudyGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'course', 'created_by', 'max_members', 'is_active', 'is_public', 'created_at')
    list_filter = ('is_active', 'is_public', 'course', 'created_at')
    search_fields = ('name', 'description', 'created_by__username')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active', 'is_public')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'course', 'created_by')
        }),
        ('Settings', {
            'fields': ('max_members', 'is_active', 'is_public')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StudyGroupMember)
class StudyGroupMemberAdmin(admin.ModelAdmin):
    list_display = ('study_group', 'user', 'role', 'is_active', 'joined_at')
    list_filter = ('role', 'is_active', 'joined_at')
    search_fields = ('study_group__name', 'user__username')
    list_editable = ('role', 'is_active')
    readonly_fields = ('joined_at', 'updated_at')

    fieldsets = (
        ('Membership', {
            'fields': ('study_group', 'user', 'role', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('joined_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ==================== STAFF PAYROLL ====================
@admin.register(StaffPayroll)
class StaffPayrollAdmin(admin.ModelAdmin):
    list_display = (
        'payroll_reference', 'staff', 'month', 'year',
        'base_salary', 'gross_salary', 'net_salary',
        'payment_status', 'payment_method', 'payment_date'
    )
    list_filter = ('payment_status', 'payment_method', 'month', 'year')
    search_fields = ('payroll_reference', 'staff__username', 'staff__first_name', 'staff__last_name')
    readonly_fields = (
        'payroll_reference', 'gross_salary', 'net_salary',
        'created_at', 'updated_at', 'approved_at'
    )
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Reference', {
            'fields': ('payroll_reference', 'staff', 'month', 'year')
        }),
        ('Salary', {
            'fields': ('base_salary', 'allowances', 'bonuses', 'gross_salary')
        }),
        ('Deductions', {
            'fields': ('tax_deduction', 'other_deductions', 'net_salary')
        }),
        ('Payment', {
            'fields': ('payment_status', 'payment_method', 'payment_date', 'bank_name', 'account_number')
        }),
        ('Attachments', {
            'fields': (
                'attachment_1', 'attachment_1_name',
                'attachment_2', 'attachment_2_name',
                'attachment_3', 'attachment_3_name',
                'attachment_4', 'attachment_4_name',
                'attachment_5', 'attachment_5_name',
            ),
            'classes': ('collapse',)
        }),
        ('Administration', {
            'fields': ('notes', 'created_by', 'approved_by', 'approved_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of paid payrolls"""
        if obj and obj.payment_status == 'paid':
            return False
        return super().has_delete_permission(request, obj)


# Site customization
admin.site.site_header = "LMS Administration"
admin.site.site_title = "LMS Admin Portal"
admin.site.index_title = "Welcome to LMS Administration"