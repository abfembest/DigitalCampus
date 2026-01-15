from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.utils import timezone
from eduweb.models import CourseApplication, CourseApplicationFile, User
from datetime import timedelta
import json


def is_admin(user):
    """Check if user is staff/admin"""
    return user.is_staff or user.is_superuser


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def dashboard(request):
    """Admin dashboard with statistics and recent applications"""
    
    # Get statistics
    total_applications = CourseApplication.objects.count()
    pending_applications = CourseApplication.objects.filter(is_reviewed=False).count()
    approved_applications = CourseApplication.objects.filter(is_reviewed=True).count()
    total_students = User.objects.filter(is_staff=False, is_active=True).count()
    
    # Get recent applications (last 10)
    recent_applications = CourseApplication.objects.select_related('user').order_by('-created_at')[:10]
    
    # Prepare chart data for applications over time (last 7 days)
    today = timezone.now().date()
    week_ago = today - timedelta(days=6)
    
    applications_by_day = []
    labels = []
    
    for i in range(7):
        date = week_ago + timedelta(days=i)
        count = CourseApplication.objects.filter(
            created_at__date=date
        ).count()
        applications_by_day.append(count)
        labels.append(date.strftime('%a'))
    
    applications_chart_data = json.dumps({
        'labels': labels,
        'data': applications_by_day
    })
    
    # Program distribution data
    program_distribution = CourseApplication.objects.values('program').annotate(
        count=Count('id')
    ).order_by('-count')
    
    program_labels = [dict(CourseApplication.PROGRAM_CHOICES).get(item['program'], item['program']) 
                     for item in program_distribution]
    program_data = [item['count'] for item in program_distribution]
    
    program_chart_data = json.dumps({
        'labels': program_labels,
        'data': program_data
    })
    
    context = {
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'approved_applications': approved_applications,
        'total_students': total_students,
        'recent_applications': recent_applications,
        'applications_chart_data': applications_chart_data,
        'program_chart_data': program_chart_data,
        'pending_count': pending_applications,
    }
    
    return render(request, 'admin/dashboard.html', context)


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def applications_list(request):
    """List all applications with filtering and pagination"""
    
    applications = CourseApplication.objects.select_related('user').order_by('-created_at')
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    program_filter = request.GET.get('program', '')
    
    # Apply search filter
    if search_query:
        applications = applications.filter(
            Q(application_id__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Apply status filter
    if status_filter == 'pending':
        applications = applications.filter(is_reviewed=False)
    elif status_filter == 'reviewed':
        applications = applications.filter(is_reviewed=True)
    
    # Apply program filter
    if program_filter:
        applications = applications.filter(program=program_filter)
    
    # Pagination
    paginator = Paginator(applications, 15)  # 15 applications per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get pending count for sidebar
    pending_count = CourseApplication.objects.filter(is_reviewed=False).count()
    
    context = {
        'applications': page_obj,
        'programs': CourseApplication.PROGRAM_CHOICES,
        'pending_count': pending_count,
    }
    
    return render(request, 'admin/applications.html', context)


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def application_detail(request, pk):
    """View detailed information about a specific application"""
    
    application = get_object_or_404(
        CourseApplication.objects.prefetch_related('files'),
        pk=pk
    )
    
    # Get pending count for sidebar
    pending_count = CourseApplication.objects.filter(is_reviewed=False).count()
    
    context = {
        'application': application,
        'pending_count': pending_count,
    }
    
    return render(request, 'admin/application_detail.html', context)


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def mark_reviewed(request, pk):
    """Mark an application as reviewed"""
    
    if request.method == 'POST':
        application = get_object_or_404(CourseApplication, pk=pk)
        application.is_reviewed = True
        application.save()
        
        messages.success(
            request, 
            f'Application {application.application_id} has been marked as reviewed.'
        )
        
        return redirect('administrator:application_detail', pk=pk)
    
    return redirect('administrator:applications_list')