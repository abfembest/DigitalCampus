from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('admission/apply/', views.apply, name='apply'),
    path('admission/course/', views.admission_course, name='admission_course'),
    path('admission/detail/', views.detail, name='detail'),
    path('contact/submit/', views.contact_submit, name='contact_submit'),
]