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
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)