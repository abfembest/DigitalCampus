from django.contrib import admin
from django.utils import timezone
from .models import (
    ContactMessage, CourseApplication, ApplicationDocument,
    UserProfile, ApplicationPayment, Vendor, BlogCategory, 
    BlogPost, Faculty, Course, CourseIntake
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'email_verified', 'created_at')
    list_filter = ('email_verified', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('verification_token', 'created_at', 'updated_at')
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Verification', {
            'fields': ('email_verified', 'verification_token')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at', 'is_read', 'responded')
    list_filter = ('subject', 'is_read', 'responded', 'created_at')
    search_fields = ('name', 'email', 'message')
    readonly_fields = ('created_at',)
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
            'fields': ('is_read', 'responded', 'created_at')
        }),
    )


# ==================== FACULTY & COURSES ====================
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
        'name', 'code', 'faculty', 'degree_level', 'duration_years', 
        'application_fee', 'tuition_fee', 'is_active', 'is_featured', 'display_order'
    )
    list_filter = ('faculty', 'degree_level', 'is_active', 'is_featured', 'created_at')
    search_fields = ('name', 'code', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active', 'is_featured', 'display_order')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'code', 'faculty', 'is_active', 'is_featured', 'display_order')
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


# ==================== APPLICATIONS ====================
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
        'get_payment_status',
        'submitted_at', 
        'created_at'
    )
    list_filter = (
        'status',
        'course__faculty',
        'course',
        'intake__intake_period',
        'study_mode',
        'scholarship_requested',
        'financial_aid_requested',
        'created_at',
        'submitted_at'
    )
    search_fields = (
        'application_id', 'first_name', 'last_name', 
        'email', 'phone', 'course__name'
    )
    readonly_fields = (
        'application_id', 
        'created_at', 
        'submitted_at',
        'updated_at',
        'user',
        'reviewed_at',
        'get_payment_status'
    )
    date_hierarchy = 'created_at'
    inlines = [ApplicationDocumentInline, ApplicationPaymentInline]
    list_editable = ('status',)
    
    fieldsets = (
        ('Application Info', {
            'fields': (
                'application_id', 
                'user', 
                'created_at', 
                'submitted_at',
                'updated_at'
            )
        }),
        ('Application Status', {
            'fields': (
                'status',
                'get_payment_status'
            )
        }),
        ('Review Information', {
            'fields': (
                'reviewed_by',
                'reviewed_at',
                'review_notes'
            ),
            'classes': ('collapse',),
        }),
        ('Personal Information', {
            'fields': (
                'first_name', 
                'last_name', 
                'email', 
                'phone', 
                'date_of_birth', 
                'country', 
                'gender', 
                'address'
            )
        }),
        ('Academic Background', {
            'fields': (
                'academic_history', 
                'english_proficiency_test', 
                'english_proficiency_score', 
                'additional_qualifications'
            )
        }),
        ('Course Selection', {
            'fields': (
                'course',
                'intake',
                'study_mode'
            )
        }),
        ('Financial Aid', {
            'fields': ('scholarship_requested', 'financial_aid_requested'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('referral_source', 'personal_statement'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related(
            'user', 'reviewed_by', 'course', 'course__faculty', 'intake'
        )
    
    def get_payment_status(self, obj):
        """Display payment status"""
        return obj.payment_status
    get_payment_status.short_description = 'Payment Status'
    
    actions = [
        'mark_as_under_review', 'mark_as_reviewed', 
        'mark_as_submitted', 'mark_as_withdrawn'
    ]
    
    def mark_as_under_review(self, request, queryset):
        """Bulk action to mark applications as under review"""
        updated = queryset.update(status='under_review')
        self.message_user(request, f'{updated} application(s) marked as under review.')
    mark_as_under_review.short_description = "Mark selected as Under Review"
    
    def mark_as_reviewed(self, request, queryset):
        """Bulk action to mark applications as reviewed"""
        updated = queryset.update(
            status='reviewed',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} application(s) marked as reviewed.')
    mark_as_reviewed.short_description = "Mark selected as Reviewed"
    
    def mark_as_submitted(self, request, queryset):
        """Bulk action to mark applications as submitted"""
        updated = queryset.filter(status='draft').update(
            status='submitted',
            submitted_at=timezone.now()
        )
        self.message_user(request, f'{updated} application(s) marked as submitted.')
    mark_as_submitted.short_description = "Mark selected as Submitted"
    
    def mark_as_withdrawn(self, request, queryset):
        """Bulk action to mark applications as withdrawn"""
        updated = queryset.update(status='withdrawn')
        self.message_user(request, f'{updated} application(s) marked as withdrawn.')
    mark_as_withdrawn.short_description = "Mark selected as Withdrawn"


@admin.register(ApplicationDocument)
class ApplicationDocumentAdmin(admin.ModelAdmin):
    list_display = (
        'application', 
        'file_type', 
        'original_filename', 
        'get_file_size', 
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
        'uploaded_at', 
        'get_file_size'
    )
    
    fieldsets = (
        ('Application Info', {
            'fields': ('application',)
        }),
        ('File Information', {
            'fields': (
                'file', 
                'file_type', 
                'original_filename', 
                'file_size', 
                'get_file_size', 
                'uploaded_at'
            )
        }),
    )
    
    def get_file_size(self, obj):
        """Display human-readable file size"""
        return obj.get_file_size_display()
    get_file_size.short_description = 'File Size'
    
    def has_add_permission(self, request):
        """Disable adding files directly from admin"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing files from admin"""
        return False


# ==================== PAYMENT ====================
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
    
    fieldsets = (
        ('Application', {
            'fields': ('application',)
        }),
        ('Payment Details', {
            'fields': (
                'payment_reference', 'amount', 'currency', 
                'status', 'payment_method'
            )
        }),
        ('Gateway Information', {
            'fields': ('gateway_payment_id', 'card_last4', 'card_brand'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'paid_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('payment_metadata', 'failure_reason'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Payments should be created programmatically"""
        return False
    
    actions = ['mark_as_success', 'mark_as_failed']
    
    def mark_as_success(self, request, queryset):
        """Mark payments as successful"""
        updated = queryset.filter(status='processing').update(
            status='success',
            paid_at=timezone.now()
        )
        self.message_user(request, f'{updated} payment(s) marked as successful.')
    mark_as_success.short_description = "Mark selected as Successful"
    
    def mark_as_failed(self, request, queryset):
        """Mark payments as failed"""
        updated = queryset.filter(status='processing').update(status='failed')
        self.message_user(request, f'{updated} payment(s) marked as failed.')
    mark_as_failed.short_description = "Mark selected as Failed"


# ==================== VENDOR ====================
@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'country', 'is_active', 'created_at')
    list_filter = ('is_active', 'country', 'created_at')
    search_fields = ('name', 'email', 'stripe_account_id')
    list_editable = ('is_active',)
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'email', 'country')
        }),
        ('Integration', {
            'fields': ('stripe_account_id',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'created_at')
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
        """Display number of published posts"""
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
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('author', 'category')
    
    actions = ['publish_posts', 'unpublish_posts', 'feature_posts']
    
    def publish_posts(self, request, queryset):
        """Publish selected posts"""
        updated = queryset.update(status='published', publish_date=timezone.now())
        self.message_user(request, f'{updated} post(s) published.')
    publish_posts.short_description = "Publish selected posts"
    
    def unpublish_posts(self, request, queryset):
        """Unpublish selected posts"""
        updated = queryset.update(status='draft')
        self.message_user(request, f'{updated} post(s) unpublished.')
    unpublish_posts.short_description = "Unpublish selected posts"
    
    def feature_posts(self, request, queryset):
        """Feature selected posts"""
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} post(s) featured.')
    feature_posts.short_description = "Feature selected posts"


# Site customization
admin.site.site_header = "MIU Administration"
admin.site.site_title = "MIU Admin Portal"
admin.site.index_title = "Welcome to MIU Administration"