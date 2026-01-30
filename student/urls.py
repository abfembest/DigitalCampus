from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Courses
    path('courses/', views.my_courses, name='my_courses'),
    path('courses/catalog/', views.course_catalog, name='course_catalog'),
    path('courses/<int:course_id>/', views.course_detail, name='course_detail'),
    path('courses/<int:course_id>/enroll/', views.enroll_course, name='enroll_course'),
    
    # Lessons
    path('lessons/<int:lesson_id>/', views.lesson_view, name='lesson_view'),
    path('lessons/<int:lesson_id>/complete/', views.mark_lesson_complete, name='mark_lesson_complete'),
    
    # Assignments
    path('assignments/', views.assignments, name='assignments'),
    path('assignments/<int:assignment_id>/', views.assignment_detail, name='assignment_detail'),
    path('assignments/<int:assignment_id>/submit/', views.submit_assignment, name='submit_assignment'),
    
    # Quizzes
    path('quizzes/<int:quiz_id>/', views.quiz_detail, name='quiz_detail'),
    path('quizzes/<int:quiz_id>/attempt/', views.quiz_attempt, name='quiz_attempt'),
    path('quizzes/<int:quiz_id>/submit/', views.submit_quiz, name='submit_quiz'),
    
    # Grades & Progress
    path('grades/', views.grades, name='grades'),
    path('progress/', views.progress, name='progress'),
    
    # Certificates
    path('certificates/', views.certificates, name='certificates'),
    path('certificates/<int:certificate_id>/download/', views.download_certificate, name='download_certificate'),
    
    # Messages
    path('messages/', views.messages, name='messages'),
    path('messages/<int:message_id>/', views.message_detail, name='message_detail'),
    path('messages/compose/', views.compose_message, name='compose_message'),
    
    # Profile & Settings
    path('profile/', views.profile, name='profile'),
    path('settings/', views.settings, name='settings'),
]