from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('aboutus/', views.about, name='about'),
    path('admission/apply/', views.apply, name='apply'),
    path('admission/apply/success/', views.application_success, name='application_success'),
    path('admission/course/', views.admission_course, name='admission_course'),
    path('adrequirements/', views.admission_requirement, name='admission_requirement'),
    path('admission/detail/', views.detail, name='detail'),
    path('contact/submit/', views.contact_submit, name='contact_submit'),
    path('admission/apply/submit/', views.application_submit, name='application_submit'),
    path('blank_page/', views.blank_page, name='blank_page'),

    
]


