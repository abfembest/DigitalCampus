from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Courses
    path(
        'courses/', 
        views.my_courses, 
        name='my_courses'
    ),
    path(
        'courses/catalog/', 
        views.course_catalog, 
        name='course_catalog'
    ),
    path(
        'courses/<slug:course_slug>/',
        views.course_detail,
        name='course_detail'
    ),
    path(
        'courses/<slug:course_slug>/enroll/',
        views.enroll_course,
        name='enroll_course'
    ),
    
    # Lessons - Slug-based
    path(
        'courses/<slug:course_slug>/lessons/<slug:lesson_slug>/',
        views.lesson_view,
        name='lesson_view'
    ),
    path(
        'courses/<slug:course_slug>/lessons/<slug:lesson_slug>/complete/',
        views.mark_lesson_complete,
        name='mark_lesson_complete'
    ),
    
    # Assignments
    path('assignments/', views.assignments, name='assignments'),
    path(
        'courses/<slug:course_slug>/assignments/<slug:assignment_slug>/',
        views.assignment_detail,
        name='assignment_detail'
    ),
    path(
        'courses/<slug:course_slug>/assignments/<slug:assignment_slug>/submit/',
        views.submit_assignment,
        name='submit_assignment'
    ),
    
    # Quizzes
    path('quizzes/', views.quiz_list, name='quiz_list'),
    path(
        'courses/<slug:course_slug>/lessons/<slug:lesson_slug>/quizzes/<slug:quiz_slug>/',
        views.quiz_detail,
        name='quiz_detail'
    ),
    path(
        'courses/<slug:course_slug>/lessons/<slug:lesson_slug>/quizzes/<slug:quiz_slug>/take/',
        views.quiz_take,
        name='quiz_take'
    ),
    path(
        'quizzes/attempt/<int:attempt_id>/submit/',
        views.quiz_submit,
        name='quiz_submit'
    ),
    path(
        'quizzes/attempt/<int:attempt_id>/result/',
        views.quiz_result,
        name='quiz_result'
    ),
    
    # Community
    path(
        'community/', 
        views.community, 
        name='community'
    ),
    path(
        'community/thread/<int:thread_id>/', 
        views.thread_detail, 
        name='thread_detail'
    ),
    path(
        'community/create/', 
        views.create_thread, 
        name='create_thread'
    ),
    
    # Study Groups
    path(
        'study-groups/', 
        views.study_groups, 
        name='study_groups'
    ),
    path(
        'study-groups/<int:group_id>/', 
        views.study_group_detail, 
        name='study_group_detail'
    ),
    path(
        'study-groups/<int:group_id>/join/', 
        views.join_study_group, 
        name='join_study_group'
    ),
    
    # Achievements
    path(
        'achievements/', 
        views.achievements, 
        name='achievements'
    ),
    
    # Grades & Progress
    path(
        'grades/', 
        views.grades, 
        name='grades'
    ),
    path(
        'progress/', 
        views.progress, 
        name='progress'
    ),
    
    # Certificates
    path(
        'certificates/', 
        views.certificates, 
        name='certificates'
    ),
    
    # Profile & Settings
    path(
        'profile/', 
        views.profile, 
        name='profile'
    ),
    path(
        'settings/', 
        views.settings, 
        name='settings'
    ),
    path(
        'help-support/', 
        views.help_support, 
        name='help_support'
    ),

    # Outstanding fees table
    path(
        'payments/',
        views.my_payments,
        name='my_payments',
    ),
]