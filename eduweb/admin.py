from django.contrib import admin
from .models import ContactMessage, CourseApplication, CourseApplicationFile, UserProfile

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
    readonly_fields = ('file',)


@admin.register(CourseApplication)
class CourseApplicationAdmin(admin.ModelAdmin):
    list_display = ('application_id', 'get_full_name', 'email', 'program', 'degree_level', 'submission_date', 'is_reviewed')
    list_filter = ('program', 'degree_level', 'study_mode', 'intake', 'is_reviewed', 'submitted')
    search_fields = ('application_id', 'first_name', 'last_name', 'email')
    readonly_fields = ('application_id', 'created_at', 'submission_date', 'user')
    date_hierarchy = 'submission_date'
    inlines = [CourseApplicationFileInline]
    
    fieldsets = (
        ('Application Info', {
            'fields': ('application_id', 'user', 'submitted', 'is_reviewed', 'created_at', 'submission_date')
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'date_of_birth', 'country', 'gender', 'address')
        }),
        ('Academic Background', {
            'fields': ('academic_history', 'english_proficiency', 'english_score', 'additional_qualifications')
        }),
        ('Course Selection', {
            'fields': ('program', 'degree_level', 'study_mode', 'intake', 'scholarship')
        }),
        ('Documents', {
            'fields': ('documents_uploaded',),
            'description': 'Uploaded documents are shown below as inline files'
        }),
        ('Additional', {
            'fields': ('referral_source',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user')


@admin.register(CourseApplicationFile)
class CourseApplicationFileAdmin(admin.ModelAdmin):
    list_display = ('application', 'file_type', 'original_filename', 'get_file_size', 'uploaded_at')
    list_filter = ('file_type', 'uploaded_at')
    search_fields = ('application__application_id', 'application__first_name', 'application__last_name', 'original_filename')
    readonly_fields = ('application', 'file', 'file_type', 'original_filename', 'file_size', 'uploaded_at', 'get_file_size')
    
    fieldsets = (
        ('Application Info', {
            'fields': ('application',)
        }),
        ('File Information', {
            'fields': ('file', 'file_type', 'original_filename', 'file_size', 'get_file_size', 'uploaded_at')
        }),
    )
    
    def get_file_size(self, obj):
        """Display human-readable file size"""
        return obj.get_file_size_display()
    get_file_size.short_description = 'File Size'