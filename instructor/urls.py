from django.urls import path
from . import views

app_name = 'instructor'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Course Management
    path('courses/', views.course_list, name='course_list'),
    path('courses/create/', views.course_create, name='course_create'),
    path('courses/<slug:slug>/edit/', views.course_edit, name='course_edit'),
    path('courses/<slug:slug>/objectives/', views.course_objectives, name='course_objectives'),
    path('courses/<slug:slug>/delete/', views.course_delete, name='course_delete'),
    
    # Section Management
    path('courses/<slug:course_slug>/sections/create/', views.section_create, name='section_create'),
    path('courses/<slug:course_slug>/sections/<int:section_id>/edit/', views.section_edit, name='section_edit'),
    path('courses/<slug:course_slug>/sections/<int:section_id>/delete/', views.section_delete, name='section_delete'),
    
    # Lesson Management
    path('courses/<slug:course_slug>/lessons/', views.lesson_list, name='lesson_list'),
    path('courses/<slug:course_slug>/lessons/create/', views.lesson_create, name='lesson_create'),
    path('courses/<slug:course_slug>/lessons/<int:lesson_id>/edit/', views.lesson_edit, name='lesson_edit'),
    path('courses/<slug:course_slug>/lessons/<int:lesson_id>/delete/', views.lesson_delete, name='lesson_delete'),
    
    # Quiz Management
    path('courses/<slug:course_slug>/lessons/<int:lesson_id>/quizzes/', views.quiz_list, name='quiz_list'),
    path('courses/<slug:course_slug>/lessons/<int:lesson_id>/quizzes/create/', views.quiz_create, name='quiz_create'),
    path('courses/<slug:course_slug>/lessons/<int:lesson_id>/quizzes/<int:quiz_id>/edit/', views.quiz_edit, name='quiz_edit'),
    path('courses/<slug:course_slug>/lessons/<int:lesson_id>/quizzes/<int:quiz_id>/questions/', views.quiz_questions, name='quiz_questions'),
    
    # Question Management
    path('courses/<slug:course_slug>/lessons/<int:lesson_id>/quizzes/<int:quiz_id>/questions/create/', views.question_create, name='question_create'),
    path('courses/<slug:course_slug>/lessons/<int:lesson_id>/quizzes/<int:quiz_id>/questions/<int:question_id>/answers/', views.question_answers, name='question_answers'),
    
    # Assignment Management
    path('courses/<slug:course_slug>/lessons/<int:lesson_id>/assignments/', views.assignment_list, name='assignment_list'),
    path('courses/<slug:course_slug>/lessons/<int:lesson_id>/assignments/create/', views.assignment_create, name='assignment_create'),
    path('courses/<slug:course_slug>/lessons/<int:lesson_id>/assignments/<int:assignment_id>/edit/', views.assignment_edit, name='assignment_edit'),
    path('courses/<slug:course_slug>/assignments/<int:assignment_id>/submissions/', views.assignment_submissions, name='assignment_submissions'),
    path('courses/<slug:course_slug>/submissions/<int:submission_id>/grade/', views.grade_submission, name='grade_submission'),
    
    # Student Management
    path('courses/<slug:course_slug>/students/', views.students_list, name='students_list'),
    path('courses/<slug:course_slug>/students/<int:student_id>/progress/', views.student_progress, name='student_progress'),
    
    # Announcements
    path('courses/<slug:course_slug>/announcements/create/', views.announcement_create, name='announcement_create'),
]