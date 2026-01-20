from django.contrib import admin
from .models import ContactMessage, CourseApplication, CourseApplicationFile, UserProfile, Application, Payment, Vendor, BlogCategory, BlogPost

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


class CourseApplicationFileInline(admin.TabularInline):
    model = CourseApplicationFile
    extra = 0
    readonly_fields = ('file', 'file_type', 'original_filename', 'file_size', 'uploaded_at')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(CourseApplication)
class CourseApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'application_id', 
        'get_full_name', 
        'email', 
        'program', 
        'degree_level', 
        'status',
        'decision',
        'submission_date', 
        'is_reviewed'
    )
    list_filter = (
        'status',
        'decision',
        'program', 
        'degree_level', 
        'study_mode', 
        'intake', 
        'is_reviewed', 
        'submitted',
        'scholarship',
        'created_at',
        'submission_date'
    )
    search_fields = ('application_id', 'first_name', 'last_name', 'email', 'phone')
    readonly_fields = (
        'application_id', 
        'created_at', 
        'submission_date', 
        'user',
        'reviewed_at',
        'decision_date'
    )
    date_hierarchy = 'submission_date'
    inlines = [CourseApplicationFileInline]
    list_editable = ('status', 'decision', 'is_reviewed')
    
    fieldsets = (
        ('Application Info', {
            'fields': (
                'application_id', 
                'user', 
                'submitted', 
                'created_at', 
                'submission_date'
            )
        }),
        ('Application Status', {
            'fields': (
                'status',
                'is_reviewed',
                'reviewed_by',
                'reviewed_at'
            ),
            'classes': ('collapse',),
        }),
        ('Decision', {
            'fields': (
                'decision',
                'decision_date',
                'decision_notes'
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
                'english_proficiency', 
                'english_score', 
                'additional_qualifications'
            )
        }),
        ('Course Selection', {
            'fields': (
                'program', 
                'degree_level', 
                'study_mode', 
                'intake', 
                'scholarship'
            )
        }),
        ('Documents', {
            'fields': ('documents_uploaded',),
            'description': 'Uploaded documents are shown below as inline files',
            'classes': ('collapse',),
        }),
        ('Additional', {
            'fields': ('referral_source',),
            'classes': ('collapse',),
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user', 'reviewed_by')
    
    actions = ['mark_as_under_review', 'mark_as_reviewed', 'mark_as_accepted', 'mark_as_rejected']
    
    def mark_as_under_review(self, request, queryset):
        """Bulk action to mark applications as under review"""
        updated = queryset.update(status='under_review')
        self.message_user(request, f'{updated} application(s) marked as under review.')
    mark_as_under_review.short_description = "Mark selected as Under Review"
    
    def mark_as_reviewed(self, request, queryset):
        """Bulk action to mark applications as reviewed"""
        from django.utils import timezone
        updated = queryset.update(
            status='reviewed',
            is_reviewed=True,
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} application(s) marked as reviewed.')
    mark_as_reviewed.short_description = "Mark selected as Reviewed"
    
    def mark_as_accepted(self, request, queryset):
        """Bulk action to mark applications as accepted"""
        from django.utils import timezone
        updated = queryset.update(
            status='decision_made',
            decision='accepted',
            decision_date=timezone.now()
        )
        self.message_user(request, f'{updated} application(s) marked as accepted.')
    mark_as_accepted.short_description = "Mark selected as Accepted"
    
    def mark_as_rejected(self, request, queryset):
        """Bulk action to mark applications as rejected"""
        from django.utils import timezone
        updated = queryset.update(
            status='decision_made',
            decision='rejected',
            decision_date=timezone.now()
        )
        self.message_user(request, f'{updated} application(s) marked as rejected.')
    mark_as_rejected.short_description = "Mark selected as Rejected"


@admin.register(CourseApplicationFile)
class CourseApplicationFileAdmin(admin.ModelAdmin):
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

admin.site.register(Application)
admin.site.register(Payment)
admin.site.register(Vendor)

from .models import Faculty, Course

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
    list_display = ('name', 'code', 'faculty', 'duration_years', 'is_active', 'is_featured', 'display_order')
    list_filter = ('faculty', 'is_active', 'is_featured', 'created_at')
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
            'fields': ('degree_levels', 'study_modes', 'duration_years', 'credits_required', 'intake_periods')
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
            'fields': ('undergraduate_requirements', 'graduate_requirements'),
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

admin.site.register(BlogCategory)
admin.site.register(BlogPost)