from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'management'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Applications Management
    path('applications/', views.applications_list, name='applications_list'),
    path('applications/<int:pk>/', views.application_detail, name='application_detail'),
    path('applications/<int:pk>/mark-reviewed/', views.mark_reviewed, name='mark_reviewed'),
    path('applications/<int:pk>/make-decision/', views.make_decision, name='make_decision'),
    
    # Faculties Management
    path('faculties/', views.faculties_list, name='faculties_list'),
    path('faculties/create/', views.faculty_create, name='faculty_create'),
    path('faculties/<int:pk>/edit/', views.faculty_edit, name='faculty_edit'),
    path('faculties/<int:pk>/delete/', views.faculty_delete, name='faculty_delete'),
    
    # Courses Management
    path('courses/', views.courses, name='courses'),
    path('courses/create/', views.course_create, name='course_create'),
    path('courses/<int:pk>/', views.course_detail, name='course_detail'),
    path('courses/<int:pk>/edit/', views.course_edit, name='course_edit'),
    path('courses/<int:pk>/delete/', views.course_delete, name='course_delete'),

    # ==================== COURSE CATEGORIES ====================
    path('categories/create/', views.course_category_create, name='course_category_create'),
    path('categories/<int:pk>/edit/', views.course_category_edit, name='course_category_edit'),
    path('categories/<int:pk>/delete/', views.course_category_delete, name='course_category_delete'),

    # Blog Management
    path('blog/posts/', views.blog_posts_list, name='blog_posts_list'),
    path('blog/posts/create/', views.blog_post_create, name='blog_post_create'),
    path('blog/posts/<int:pk>/edit/', views.blog_post_edit, name='blog_post_edit'),
    path('blog/posts/<int:pk>/delete/', views.blog_post_delete, name='blog_post_delete'),
    
    # Blog Categories
    path('blog/categories/', views.blog_categories_list, name='blog_categories_list'),
    path('blog/categories/create/', views.blog_category_create, name='blog_category_create'),
    path('blog/categories/<int:pk>/edit/', views.blog_category_edit, name='blog_category_edit'),
    path('blog/categories/<int:pk>/delete/', views.blog_category_delete, name='blog_category_delete'),

    path('users/', views.users_list, name='users_list'),
    
    # User CRUD operations
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:pk>/', views.user_detail, name='user_detail'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    
    # User actions
    path('users/<int:pk>/toggle-active/', views.user_toggle_active, name='user_toggle_active'),
    path('users/<int:pk>/change-role/', views.user_change_role, name='user_change_role'),
    
    # Bulk actions
    path('users/bulk-action/', views.bulk_user_action, name='bulk_user_action'),
    
    # AJAX endpoints
    path('users/<int:pk>/quick-info/', views.user_quick_info, name='user_quick_info'),

    # ==================== SYSTEM CONFIGURATION ====================
    path('config/', views.system_config_list, name='system_config_list'),
    path('config/create/', views.system_config_create, name='system_config_create'),
    path('config/<int:pk>/edit/', views.system_config_edit, name='system_config_edit'),
    path('config/<int:pk>/delete/', views.system_config_delete, name='system_config_delete'),
    
    # Specific configuration pages
    path('config/branding/', views.branding_config, name='branding_config'),
    path('config/email/', views.email_config, name='email_config'),
    path('config/notifications/', views.notification_config, name='notification_config'),
    
    # ==================== AUDIT LOGS & SECURITY ====================
    path('audit-logs/', views.audit_logs_list, name='audit_logs_list'),
    path('audit-logs/<int:pk>/', views.audit_log_detail, name='audit_log_detail'),
    path('audit-logs/export/', views.audit_logs_export, name='audit_logs_export'),
    path('security/', views.security_dashboard, name='security_dashboard'),

    # ==================== BROADCAST CENTER ====================
    path('broadcast/', views.broadcast_center, name='broadcast_center'),
    path('broadcast/create/', views.broadcast_create, name='broadcast_create'),
    path('broadcast/<slug:slug>/edit/', views.broadcast_edit, name='broadcast_edit'),
    path('broadcast/<slug:slug>/send/', views.broadcast_send, name='broadcast_send'),
    path('broadcast/<slug:slug>/delete/', views.broadcast_delete, name='broadcast_delete'),

    path(
        'applications/<int:pk>/approve-department/', 
        views.approve_department, 
        name='approve_department'
    ),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)