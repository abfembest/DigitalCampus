from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'eduweb'

urlpatterns = [
    path('auth/', views.auth_page, name='auth_page'),
    path('verify-email/<uuid:token>/', views.verify_email, name='verify_email'),
    path('logout/', views.user_logout, name='logout'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    
    path('', views.index, name='index'),
    path('about-us/', views.about, name='about'),
    path('admission/apply/', views.apply, name='apply'),
    path('admission/course/', views.admission_course, name='admission_course'),
    path('admission/requirements/', views.admission_requirement, name='admission_requirement'),
    path('admission/detail/', views.detail, name='detail'),
    path('contact/submit/', views.contact_submit, name='contact_submit'),
    path('application_status/', views.application_status, name='application_status'),
    path('payments/', views.payments, name='payments'),

    path('admission-letter/<int:application_id>/', views.admission_letter, name='admission_letter'),

    # Faculty Pages
    path('faculties/science/', views.faculty_science, name='faculty_science'),
    path('faculties/engineering/', views.faculty_engineering, name='faculty_engineering'),
    path('faculties/business/', views.faculty_business, name='faculty_business'),
    path('faculties/arts/', views.faculty_arts, name='faculty_arts'),
    path('faculties/health-sciences/', views.faculty_health, name='faculty_health'),

    # Program Pages
    path('programs/business-administration/', views.program_business_admin, name='program_business_admin'),
    path('programs/computer-science/', views.program_computer_science, name='program_computer_science'),
    path('programs/data-science/', views.program_data_science, name='program_data_science'),
    path('programs/health-sciences/', views.program_health_sciences, name='program_health_sciences'),
    path('programs/engineering/', views.program_engineering, name='program_engineering'),

    # Additional Pages
    path('research/', views.research, name='research'),
    path('campus-life/', views.campus_life, name='campus_life'),
    path('blog/', views.blog, name='blog'),



    ############### PAYMENT GATEWAY ################

    path("pay/", views.payment_page),
    path("create-intent/", views.create_payment_intent),
    path("confirm/", views.confirm_payment),
    path("success/<int:payment_id>/", views.payment_success),
    path("stripe/webhook/", views.stripe_webhook),
    path("refund/<int:payment_id>/", views.refund_payment),

]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

