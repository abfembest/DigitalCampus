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
    path('applications/<str:application_id>/', views.application_detail, name='application_detail'),
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

    # ==================== LMS COURSES ====================
    path('lms-courses/', views.lms_courses_list, name='lms_courses_list'),
    path('lms-courses/create/', views.lms_course_create, name='lms_course_create'),
    path('lms-courses/<int:pk>/', views.lms_course_detail, name='lms_course_detail'),
    path('lms-courses/<int:pk>/edit/', views.lms_course_edit, name='lms_course_edit'),
    path('lms-courses/<int:pk>/delete/', views.lms_course_delete, name='lms_course_delete'),

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

    # ==================== DEPARTMENTS ====================
    path('departments/', views.departments_list, name='departments_list'),
    path('departments/create/', views.department_create, name='department_create'),
    path('departments/<int:pk>/edit/', views.department_edit, name='department_edit'),
    path('departments/<int:pk>/delete/', views.department_delete, name='department_delete'),

    # ==================== PROGRAMS ====================
    path('programs/', views.programs_list, name='programs_list'),
    path('programs/create/', views.program_create, name='program_create'),
    path('programs/<int:pk>/', views.program_detail, name='program_detail'),
    path('programs/<int:pk>/edit/', views.program_edit, name='program_edit'),
    path('programs/<int:pk>/delete/', views.program_delete, name='program_delete'),

    # ==================== ACADEMIC SESSIONS ====================
    path('academic-sessions/', views.academic_sessions_list, name='academic_sessions_list'),
    path('academic-sessions/create/', views.academic_session_create, name='academic_session_create'),
    path('academic-sessions/<int:pk>/edit/', views.academic_session_edit, name='academic_session_edit'),
    path('academic-sessions/<int:pk>/set-current/', views.academic_session_set_current, name='academic_session_set_current'),
    path('academic-sessions/<int:pk>/delete/', views.academic_session_delete, name='academic_session_delete'),

    # ==================== COURSE INTAKES ====================
    path('intakes/', views.intakes_list, name='intakes_list'),
    path('intakes/create/', views.intake_create, name='intake_create'),
    path('intakes/<int:pk>/edit/', views.intake_edit, name='intake_edit'),
    path('intakes/<int:pk>/delete/', views.intake_delete, name='intake_delete'),

    # ==================== COURSE CATEGORIES (add missing list page) ====================
    path('categories/', views.course_categories_list, name='course_categories_list'),

    # ==================== SUPPORT TICKETS ====================
    path('tickets/', views.tickets_list, name='tickets_list'),
    path('tickets/<int:pk>/', views.ticket_detail, name='ticket_detail'),
    path('tickets/<int:pk>/reply/', views.ticket_reply, name='ticket_reply'),
    path('tickets/<int:pk>/change-status/', views.ticket_change_status, name='ticket_change_status'),
    path('tickets/<int:pk>/assign/', views.ticket_assign, name='ticket_assign'),

    # ==================== CONTACT MESSAGES ====================
    path('contact-messages/', views.contact_messages_list, name='contact_messages_list'),
    path('contact-messages/<int:pk>/', views.contact_message_detail, name='contact_message_detail'),
    path('contact-messages/<int:pk>/mark-read/', views.contact_message_mark_read, name='contact_message_mark_read'),
    path('contact-messages/<int:pk>/respond/', views.contact_message_respond, name='contact_message_respond'),

    # ==================== ANNOUNCEMENTS ====================
    path('announcements/', views.announcements_list, name='announcements_list'),
    path('announcements/create/', views.announcement_create, name='announcement_create'),
    path('announcements/<int:pk>/edit/', views.announcement_edit, name='announcement_edit'),
    path('announcements/<int:pk>/delete/', views.announcement_delete, name='announcement_delete'),

    # ==================== ENROLLMENTS ====================
    path('enrollments/', views.enrollments_list, name='enrollments_list'),
    path('enrollments/create/', views.enrollment_create, name='enrollment_create'),
    path('enrollments/<int:pk>/edit/', views.enrollment_edit, name='enrollment_edit'),
    path('enrollments/<int:pk>/delete/', views.enrollment_delete, name='enrollment_delete'),

    # ==================== STAFF PAYROLL ====================
    path('payroll/', views.staff_payroll_list, name='staff_payroll_list'),
    path('payroll/create/', views.staff_payroll_create, name='staff_payroll_create'),
    path('payroll/<int:pk>/edit/', views.staff_payroll_edit, name='staff_payroll_edit'),
    path('payroll/<int:pk>/delete/', views.staff_payroll_delete, name='staff_payroll_delete'),

    # ==================== REVIEWS ====================
    path('reviews/', views.reviews_list, name='reviews_list'),
    path('reviews/create/', views.review_create, name='review_create'),
    path('reviews/<int:pk>/edit/', views.review_edit, name='review_edit'),
    path('reviews/<int:pk>/delete/', views.review_delete, name='review_delete'),

    # ==================== CERTIFICATES ====================
    path('certificates/', views.certificates_list, name='certificates_list'),
    path('certificates/create/', views.certificate_create, name='certificate_create'),
    path('certificates/<str:certificate_id>/edit/', views.certificate_edit, name='certificate_edit'),
    path('certificates/<str:certificate_id>/delete/', views.certificate_delete, name='certificate_delete'),

    # ==================== BADGES ====================
    path('badges/', views.badges_list, name='badges_list'),
    path('badges/create/', views.badge_create, name='badge_create'),
    path('badges/<int:pk>/edit/', views.badge_edit, name='badge_edit'),
    path('badges/<int:pk>/delete/', views.badge_delete, name='badge_delete'),

    # ==================== STUDENT BADGES ====================
    path('student-badges/', views.student_badges_list, name='student_badges_list'),
    path('student-badges/assign/', views.student_badge_assign, name='student_badge_assign'),
    path('student-badges/<int:pk>/delete/', views.student_badge_delete, name='student_badge_delete'),

    # ==================== PAYMENT GATEWAYS ====================
    path('payment-gateways/', views.payment_gateways_list, name='payment_gateways_list'),
    path('payment-gateways/create/', views.payment_gateway_create, name='payment_gateway_create'),
    path('payment-gateways/<int:pk>/edit/', views.payment_gateway_edit, name='payment_gateway_edit'),
    path('payment-gateways/<int:pk>/delete/', views.payment_gateway_delete, name='payment_gateway_delete'),

    # ==================== TRANSACTIONS ====================
    path('transactions/', views.transactions_list, name='transactions_list'),
    path('transactions/<int:pk>/', views.transaction_detail, name='transaction_detail'),

    # ==================== REQUIRED PAYMENTS ====================
    path('required-payments/', views.required_payments_list, name='required_payments_list'),
    path('required-payments/create/', views.required_payment_create, name='required_payment_create'),
    path('required-payments/<int:pk>/edit/', views.required_payment_edit, name='required_payment_edit'),
    path('required-payments/<int:pk>/delete/', views.required_payment_delete, name='required_payment_delete'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)