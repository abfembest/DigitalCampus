from django.contrib import admin
from .models import ContactMessage, CourseApplication

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

@admin.register(CourseApplication)
class CourseApplicationAdmin(admin.ModelAdmin):
    list_display = ('application_id', 'get_full_name', 'email', 'program', 'degree_level', 'submission_date', 'is_reviewed')
    list_filter = ('program', 'degree_level', 'study_mode', 'intake', 'is_reviewed', 'submitted')
    search_fields = ('application_id', 'first_name', 'last_name', 'email')
    readonly_fields = ('application_id', 'created_at', 'submission_date')
    date_hierarchy = 'submission_date'
    
    fieldsets = (
        ('Application Info', {
            'fields': ('application_id', 'submitted', 'is_reviewed', 'created_at', 'submission_date')
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
        ('Additional', {
            'fields': ('referral_source', 'documents_uploaded')
        }),
    )