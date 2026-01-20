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
    path('courses/', views.courses_list, name='courses_list'),
    path('courses/create/', views.course_create, name='course_create'),
    path('courses/<int:pk>/edit/', views.course_edit, name='course_edit'),
    path('courses/<int:pk>/delete/', views.course_delete, name='course_delete'),

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
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)