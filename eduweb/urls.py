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
    path('faculty/<slug:slug>/', views.faculty_detail, name='faculty_detail'),
    path('program/<slug:slug>/', views.course_detail, name='course_detail'),

    # Additional Pages
    path('research/', views.research, name='research'),
    path('campus-life/', views.campus_life, name='campus_life'),
    path('blog/', views.blog, name='blog'),



    ############### PAYMENT GATEWAY ################

    path('api/payment/summary/<uuid:application_id>/', views.get_payment_summary, name='payment-summary'),
    path('api/payment/create-intent/', views.create_payment_intent, name='create-payment-intent'),
    path('api/payment/confirm/', views.confirm_payment, name='confirm-payment'),
    path('api/webhooks/stripe/', views.stripe_webhook, name='stripe-webhook'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

