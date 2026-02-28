from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.urls import reverse
from datetime import timedelta
import json
from django.core.mail import send_mass_mail
import threading

# Model imports
from eduweb.models import (
    CourseApplication, 
    User, 
    Faculty, 
    Course, 
    BlogPost, 
    BlogCategory,
    BroadcastMessage,
    LMSCourse,
    CourseCategory,
    AuditLog
)

# Form imports
from management.forms import (
    FacultyForm, 
    CourseForm, 
    BlogPostForm, 
    BlogCategoryForm,
    BroadcastMessageForm,
    LMSCourseForm
)


def is_admin(user):
    """Check if user is staff/admin"""
    return user.is_staff or user.is_superuser

@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def dashboard(request):
    """Admin dashboard with statistics and recent applications"""
    
    # Get statistics
    total_applications = CourseApplication.objects.count()
    pending_applications = CourseApplication.objects.filter(status__in=['payment_complete', 'under_review', 'documents_uploaded']).count()
    approved_applications = CourseApplication.objects.filter(status='approved').count()
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
    
    program_distribution = CourseApplication.objects.values(
        'program__name', 'program__department__faculty__name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:10]

    program_labels = [
        f"{item['program__name']} ({item['program__department__faculty__name'] or 'N/A'})"
        for item in program_distribution
    ]
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
    
    return render(request, 'management/dashboard.html', context)


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
    if status_filter:
        applications = applications.filter(status=status_filter)
    
    # Apply program filter
    if program_filter:
        applications = applications.filter(program__id=program_filter)
    
    # Pagination
    paginator = Paginator(applications, 15)  # 15 applications per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get pending count for sidebar
    pending_count = CourseApplication.objects.filter(status__in=['payment_complete', 'documents_uploaded', 'under_review']).count()
    
    from eduweb.models import Program

    context = {
        'applications': page_obj,
        'programs': [
            (str(p.id), f"{p.name} ({p.department.faculty.name})")
            for p in Program.objects.filter(is_active=True).select_related('department__faculty')
        ],
        'pending_count': pending_count,
    }
    
    return render(request, 'management/applications.html', context)


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def application_detail(request, application_id):
    """View detailed information about a specific application"""
    
    application = get_object_or_404(
        CourseApplication.objects.prefetch_related('documents'),  # ✅ Correct related name
        application_id=application_id
    )
    
    # Mark as under review when admin opens it (only if status is 'documents_uploaded')
    if application.status == 'documents_uploaded':
        application.status = 'under_review'
        application.save(update_fields=['status'])
    
    # Get pending count for sidebar
    pending_count = CourseApplication.objects.filter(status__in=['payment_complete', 'documents_uploaded']).count()
    
    context = {
        'application': application,
        'pending_count': pending_count,
    }
    
    return render(request, 'management/application_detail.html', context)


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def mark_reviewed(request, pk):
    """Log reviewer + timestamp, then redirect to make decision."""
    if request.method != 'POST':
        return redirect('management:applications_list')

    application = get_object_or_404(CourseApplication, pk=pk)

    # Only act on applications that are under review
    if application.status != 'under_review':
        messages.warning(request, 'Application is not in under_review status.')
        return redirect('management:application_detail', application_id=application.application_id)

    # Record who reviewed it and when (status stays under_review until decision)
    application.reviewer = request.user
    application.reviewed_at = timezone.now()
    application.save(update_fields=['reviewer', 'reviewed_at'])

    messages.success(
        request,
        f'Review recorded for {application.application_id}. Now make your decision.'
    )
    return redirect('management:application_detail', application_id=application.application_id)

@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def make_decision(request, pk):
    """Make admission decision on an application"""
    
    if request.method == 'POST':
        application = get_object_or_404(CourseApplication, pk=pk)
        decision = request.POST.get('decision')
        decision_notes = request.POST.get('decision_notes', '')
        
        VALID_DECISIONS = ['approved', 'rejected']
        if decision not in VALID_DECISIONS:
            messages.error(request, 'Invalid decision. Choose Approved or Rejected.')
            return redirect('management:application_detail', application_id=application.application_id)
        
        # Update application status
        if decision == 'approved':
            application.status = 'approved'
        elif decision == 'rejected':
            application.status = 'rejected'

        application.review_notes = decision_notes
        application.reviewer = request.user
        application.reviewed_at = timezone.now()
        application.save()

        # Auto-issue admission number for accepted students
        if decision == 'approved':
            application.issue_admission_number()
        
        # Send decision email
        send_decision_email(application)
        
        messages.success(
            request, 
            f'Decision "{decision.capitalize()}" has been recorded and email sent to applicant.'
        )
        
        return redirect('management:application_detail', application_id=application.application_id)
    
    return redirect('management:applications_list')


def send_application_submission_email(application):
    """Send confirmation email when application is submitted"""
    try:
        subject = (
            f'Application Received - {application.application_id}'
        )
        
        program_name = (
            f"{application.course.name} "
            f"({application.course.get_degree_level_display()})"
        )
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; 
                         line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; 
                            padding: 20px; background-color: #f4f4f4;">
                    <div style="background: linear-gradient(135deg, 
                                #0F2A44 0%, #1D4ED8 100%); 
                                padding: 30px; text-align: center;">
                        <h1 style="color: white; margin: 0;">
                            ✅ Application Submitted
                        </h1>
                    </div>
                    
                    <div style="background-color: white; 
                                padding: 30px; margin-top: 20px;">
                        <p style="font-size: 16px;">
                            Dear <strong>
                                {application.first_name} 
                                {application.last_name}
                            </strong>,
                        </p>
                        
                        <div style="background-color: #10b98115; 
                                    padding: 20px; border-radius: 8px; 
                                    margin: 25px 0; 
                                    border-left: 4px solid #10b981;">
                            <h3 style="color: #10b981; margin-top: 0;">
                                Application Successfully Submitted!
                            </h3>
                            <p style="font-size: 16px;">
                                Your application for <strong>
                                    {program_name}
                                </strong> has been received.
                            </p>
                            <p>
                                <strong>Application ID:</strong> 
                                {application.application_id}
                            </p>
                            <p>
                                <strong>Submission Date:</strong> 
                                {timezone.now().strftime('%B %d, %Y')}
                            </p>
                        </div>
                        
                        <h4>What Happens Next?</h4>
                        <ol>
                            <li>
                                Our admissions team will review 
                                your application
                            </li>
                            <li>
                                You will receive an email with 
                                the decision within 5-7 business days
                            </li>
                            <li>
                                You can track your application status 
                                in your account
                            </li>
                        </ol>
                        
                        <p style="margin-top: 30px;">
                            Best regards,<br>
                            <strong style="color: #0F2A44;">
                                The MIU Admissions Team
                            </strong>
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=f"Application Submitted - {application.application_id}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[application.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        return True
        
    except Exception as e:
        print(f"Error sending submission email: {str(e)}")
        return False

def send_decision_email(application):
    """Send admission decision email to applicant"""
    try:
        decision = application.status
        
        if decision == 'approved':
            subject = f'Congratulations! Admission Offer - {application.application_id}'
            decision_text = 'Congratulations! We are pleased to offer you admission to'
            color = '#10b981'  # green
            icon = '🎉'
        else:
            subject = f'Application Decision - {application.application_id}'
            decision_text = 'Thank you for your interest in'
            color = '#ef4444'  # red
            icon = '📧'
        
        # Get program name from the related Course model
        program_name = f"{application.course.name} ({application.course.get_degree_level_display()})"
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f4f4f4;">
                    <div style="background: linear-gradient(135deg, #0F2A44 0%, #1D4ED8 100%); padding: 30px; text-align: center;">
                        <h1 style="color: white; margin: 0;">{icon} Application Decision</h1>
                    </div>
                    <div style="background-color: white; padding: 30px; margin-top: 20px;">
                        <p style="font-size: 16px;">Dear <strong>{application.first_name} {application.last_name}</strong>,</p>
                        <div style="background-color: {color}15; padding: 20px; border-radius: 8px; margin: 25px 0; border-left: 4px solid {color};">
                            <h3 style="color: {color}; margin-top: 0;">Admission Decision</h3>
                            <p style="font-size: 16px;"><strong>{decision_text} {program_name}</strong></p>
                            <p><strong>Application ID:</strong> {application.application_id}</p>
                            <p><strong>Decision Date:</strong> {application.reviewed_at.strftime('%B %d, %Y') if application.reviewed_at else timezone.now().strftime('%B %d, %Y')}</p>
                        </div>
        """
        
        if decision == 'approved':
            html_content += f"""
                        <p>We are excited to welcome you to Modern International University!</p>
                        <h4>Next Steps:</h4>
                        <ol>
                            <li>Review your admission offer letter (attached)</li>
                            <li>Complete enrollment within 2 weeks</li>
                            <li>Submit your acceptance confirmation</li>
                            <li>Pay the enrollment deposit</li>
                        </ol>
                        <p>If you have any questions, please contact our admissions office.</p>
            """
        else:
            html_content += f"""
                        <p>After careful review of your application, we regret to inform you that we are unable to offer you admission at this time.</p>
                        <p>We encourage you to apply again in the future. We wish you the best in your academic pursuits.</p>
            """
        
        if application.review_notes:
            html_content += f"""
                        <div style="background-color: #f9f9f9; padding: 15px; margin-top: 20px; border-radius: 5px;">
                            <p style="margin: 0;"><strong>Additional Notes:</strong></p>
                            <p style="margin: 10px 0 0 0;">{application.review_notes}</p>
                        </div>
            """
        
        html_content += f"""
                        <p style="margin-top: 30px;">Best regards,<br><strong style="color: #0F2A44;">The MIU Admissions Team</strong></p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=f"Application Decision for {application.application_id}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[application.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        return True
    except Exception as e:
        print(f"Error sending decision email: {str(e)}")
        return False
    

# Add these imports at the top
from eduweb.models import Faculty, Course
from management.forms import FacultyForm, CourseForm
from django.urls import reverse

# Add these new views AFTER your existing views

@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def faculties_list(request):
    """List all faculties"""
    faculties = Faculty.objects.all().order_by('display_order', 'name')
    pending_count = CourseApplication.objects.filter(status__in=['payment_complete', 'documents_uploaded', 'under_review']).count()
    
    context = {
        'faculties': faculties,
        'pending_count': pending_count,
    }
    
    return render(request, 'management/faculty/faculties_list.html', context)


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def faculty_create(request):
    """Create a new faculty"""
    if request.method == 'POST':
        form = FacultyForm(request.POST, request.FILES)
        if form.is_valid():
            faculty = form.save()
            messages.success(request, f'Faculty "{faculty.name}" created successfully!')
            return redirect('management:faculties_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = FacultyForm()
    
    pending_count = CourseApplication.objects.filter(status__in=['payment_complete', 'documents_uploaded', 'under_review']).count()
    
    context = {
        'form': form,
        'pending_count': pending_count,
        'action': 'Create',
    }
    
    return render(request, 'management/faculty/faculty_form.html', context)


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def faculty_edit(request, pk):
    """Edit an existing faculty"""
    faculty = get_object_or_404(Faculty, pk=pk)
    
    if request.method == 'POST':
        form = FacultyForm(request.POST, request.FILES, instance=faculty)
        if form.is_valid():
            faculty = form.save()
            messages.success(request, f'Faculty "{faculty.name}" updated successfully!')
            return redirect('management:faculties_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = FacultyForm(instance=faculty)
    
    pending_count = CourseApplication.objects.filter(status__in=['payment_complete', 'documents_uploaded', 'under_review']).count()
    
    context = {
        'form': form,
        'faculty': faculty,
        'pending_count': pending_count,
        'action': 'Edit',
    }
    
    return render(request, 'management/faculty/faculty_form.html', context)


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def faculty_delete(request, pk):
    """Delete a faculty"""
    faculty = get_object_or_404(Faculty, pk=pk)
    
    if request.method == 'POST':
        faculty_name = faculty.name
        faculty.delete()
        messages.success(request, f'Faculty "{faculty_name}" deleted successfully!')
        return redirect('management:faculties_list')
    
    return redirect('management:faculties_list')


def courses(request):
    """
    Unified courses management page with tabs for programs and categories
    """
    from django.db.models import Count
    
    # Get all programs with related data
    programs = Program.objects.select_related(
        'department',
        'department__faculty'
    ).order_by('display_order', 'name')
    
    # Get all categories with course counts
    categories = CourseCategory.objects.annotate(
        course_count=Count('lms_courses')
    ).order_by('display_order', 'name')
    
    context = {
        'courses': programs,  # Keep variable name as 'courses' for template compatibility
        'categories': categories,
    }
    
    return render(request, 'management/course/courses.html', context)


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def course_create(request):
    """Create a new course"""
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save()
            messages.success(request, f'Course "{course.name}" created successfully!')
            return redirect('management:courses')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CourseForm()
    
    pending_count = CourseApplication.objects.filter(status__in=['payment_complete', 'documents_uploaded', 'under_review']).count()
    
    context = {
        'form': form,
        'pending_count': pending_count,
        'action': 'Create',
    }
    
    return render(request, 'management/course/course_form.html', context)

@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def course_detail(request, pk):
    """
    Display detailed information about a specific course/program
    """
    course = get_object_or_404(
        Course.objects.select_related('faculty'),
        pk=pk
    )
    
    # Get statistics
    application_count = CourseApplication.objects.filter(
        course=course
    ).count()
    
    active_applications = CourseApplication.objects.filter(
        course=course,
        status__in=['payment_complete', 'documents_uploaded', 'under_review']
    ).count()
    
    accepted_applications = CourseApplication.objects.filter(
        course=course,
        status='accepted'
    ).count()
    
    # Get recent applications for this course
    recent_applications = CourseApplication.objects.filter(
        course=course
    ).select_related('user').order_by('-created_at')[:10]
    
    pending_count = CourseApplication.objects.filter(
        status__in=['payment_complete', 'documents_uploaded', 'under_review']
    ).count()
    
    context = {
        'course': course,
        'application_count': application_count,
        'active_applications': active_applications,
        'accepted_applications': accepted_applications,
        'recent_applications': recent_applications,
        'pending_count': pending_count,
    }
    
    return render(
        request, 
        'management/course/detail.html', 
        context
    )

@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def course_edit(request, pk):
    """Edit an existing course"""
    course = get_object_or_404(Course, pk=pk)
    
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            course = form.save()
            messages.success(request, f'Course "{course.name}" updated successfully!')
            return redirect('management:courses')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CourseForm(instance=course)
    
    pending_count = CourseApplication.objects.filter(status__in=['payment_complete', 'documents_uploaded', 'under_review']).count()
    
    context = {
        'form': form,
        'course': course,
        'pending_count': pending_count,
        'action': 'Edit',
    }
    
    return render(request, 'management/course/course_form.html', context)


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def course_delete(request, pk):
    """Delete a course"""
    course = get_object_or_404(Course, pk=pk)
    
    if request.method == 'POST':
        course_name = course.name
        course.delete()
        messages.success(request, f'Course "{course_name}" deleted successfully!')
        return redirect('management:courses')
    
    return redirect('management:courses')

from eduweb.models import BlogPost, BlogCategory
from management.forms import BlogPostForm, BlogCategoryForm

# Add these views to management/views.py


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def blog_posts_list(request):
    """List all blog posts"""
    posts = BlogPost.objects.select_related('category', 'author').all().order_by('-publish_date')
    pending_count = CourseApplication.objects.filter(status__in=['payment_complete', 'documents_uploaded', 'under_review']).count()
    
    # Filter by status if provided
    status_filter = request.GET.get('status', '')
    if status_filter:
        posts = posts.filter(status=status_filter)
    
    context = {
        'posts': posts,
        'pending_count': pending_count,
    }
    
    return render(request, 'management/blog/blog_posts_list.html', context)


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def blog_post_create(request):
    """Create a new blog post"""
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, f'Blog post "{post.title}" created successfully!')
            return redirect('management:blog_posts_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BlogPostForm()
    
    pending_count = CourseApplication.objects.filter(status__in=['payment_complete', 'documents_uploaded', 'under_review']).count()
    
    context = {
        'form': form,
        'pending_count': pending_count,
        'action': 'Create',
    }
    
    return render(request, 'management/blog/blog_post_form.html', context)


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def blog_post_edit(request, pk):
    """Edit an existing blog post"""
    post = get_object_or_404(BlogPost, pk=pk)
    
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save()
            messages.success(request, f'Blog post "{post.title}" updated successfully!')
            return redirect('management:blog_posts_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BlogPostForm(instance=post)
    
    pending_count = CourseApplication.objects.filter(status__in=['payment_complete', 'documents_uploaded', 'under_review']).count()
    
    context = {
        'form': form,
        'post': post,
        'pending_count': pending_count,
        'action': 'Edit',
    }
    
    return render(request, 'management/blog/blog_post_form.html', context)


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def blog_post_delete(request, pk):
    """Delete a blog post"""
    post = get_object_or_404(BlogPost, pk=pk)
    
    if request.method == 'POST':
        post_title = post.title
        post.delete()
        messages.success(request, f'Blog post "{post_title}" deleted successfully!')
        return redirect('management:blog_posts_list')
    
    return redirect('management:blog_posts_list')


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def blog_categories_list(request):
    """List all blog categories"""
    categories = BlogCategory.objects.all().order_by('display_order', 'name')
    pending_count = CourseApplication.objects.filter(status__in=['payment_complete', 'documents_uploaded', 'under_review']).count()
    
    context = {
        'categories': categories,
        'pending_count': pending_count,
    }
    
    return render(request, 'management/blog/blog_categories_list.html', context)


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def blog_category_create(request):
    """Create a new blog category"""
    if request.method == 'POST':
        form = BlogCategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" created successfully!')
            return redirect('management:blog_categories_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BlogCategoryForm()
    
    pending_count = CourseApplication.objects.filter(status__in=['payment_complete', 'documents_uploaded', 'under_review']).count()
    
    context = {
        'form': form,
        'pending_count': pending_count,
        'action': 'Create',
    }
    
    return render(request, 'management/blog/blog_category_form.html', context)


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def blog_category_edit(request, pk):
    """Edit an existing blog category"""
    category = get_object_or_404(BlogCategory, pk=pk)
    
    if request.method == 'POST':
        form = BlogCategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" updated successfully!')
            return redirect('management:blog_categories_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BlogCategoryForm(instance=category)
    
    pending_count = CourseApplication.objects.filter(status__in=['payment_complete', 'documents_uploaded', 'under_review']).count()
    
    context = {
        'form': form,
        'category': category,
        'pending_count': pending_count,
        'action': 'Edit',
    }
    
    return render(request, 'management/blog/blog_category_form.html', context)


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def blog_category_delete(request, pk):
    """Delete a blog category"""
    category = get_object_or_404(BlogCategory, pk=pk)
    
    if request.method == 'POST':
        category_name = category.name
        category.delete()
        messages.success(request, f'Category "{category_name}" deleted successfully!')
        return redirect('management:blog_categories_list')
    
    return redirect('management:blog_categories_list')

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from .forms import (
    UserSearchForm, UserCreateForm, UserEditForm, 
    UserProfileForm, QuickRoleChangeForm
)
from eduweb.models import UserProfile


def is_admin(user):
    """Check if user is admin or staff"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@login_required
@user_passes_test(is_admin)
def users_list(request):
    """List all users with search and filter functionality"""
    # Get search and filter parameters
    search_form = UserSearchForm(request.GET or None)
    users = User.objects.select_related('profile').all()
    
    # Apply filters
    if search_form.is_valid():
        search = search_form.cleaned_data.get('search')
        role = search_form.cleaned_data.get('role')
        is_active = search_form.cleaned_data.get('is_active')
        
        if search:
            users = users.filter(
                Q(username__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search)
            )
        
        if role:
            users = users.filter(profile__role=role)
        
        if is_active:
            users = users.filter(is_active=(is_active == 'true'))
    
    # Calculate statistics
    stats = {
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'staff_users': User.objects.filter(is_staff=True).count(),
        'students': UserProfile.objects.filter(role='student').count(),
        'instructors': UserProfile.objects.filter(role='instructor').count(),
    }
    
    # Order QuerySet before pagination to avoid inconsistent results
    users = users.order_by('-date_joined')
    
    # Pagination
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    users_page = paginator.get_page(page_number)
    
    return render(request, 'management/users/list.html', {
        'users': users_page,
        'search_form': search_form,
        'stats': stats
    })


@login_required
@user_passes_test(is_admin)
def user_detail(request, pk):
    """View user details"""
    user = get_object_or_404(User.objects.select_related('profile'), pk=pk)
    
    # Calculate user statistics based on role
    stats = {}
    if user.profile.role == 'student':
        stats = {
            'enrollments': 0,  # Add actual enrollment count
            'completed_courses': 0,  # Add actual completed courses count
        }
    elif user.profile.role == 'instructor':
        stats = {
            'courses_taught': 0,  # Add actual courses count
            'total_students': 0,  # Add actual students count
        }
    
    return render(request, 'management/users/detail.html', {
        'user': user,
        'stats': stats
    })


@login_required
@user_passes_test(is_admin)
def user_create(request):
    """Create a new user"""
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # Create user
                user = form.save()
                
                # Update profile with role
                user.profile.role = form.cleaned_data['role']
                user.profile.save()
                
                messages.success(
                    request, 
                    f'User {user.username} created successfully!'
                )
                return redirect('management:user_detail', pk=user.pk)
    else:
        form = UserCreateForm()
    
    return render(request, 'management/users/create.html', {
        'form': form
    })


@login_required
@user_passes_test(is_admin)
def user_edit(request, pk):
    """Edit user information"""
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        user_form = UserEditForm(request.POST, instance=user)
        profile_form = UserProfileForm(
            request.POST, 
            request.FILES, 
            instance=user.profile
        )
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, f'User {user.username} updated successfully!')
            return redirect('management:user_detail', pk=user.pk)
    else:
        user_form = UserEditForm(instance=user)
        profile_form = UserProfileForm(instance=user.profile)
    
    return render(request, 'management/users/edit.html', {
        'user': user,
        'user_form': user_form,
        'profile_form': profile_form
    })


@login_required
@user_passes_test(is_admin)
@require_POST
def user_toggle_active(request, pk):
    """Toggle user active status"""
    user = get_object_or_404(User, pk=pk)
    
    # Prevent self-deactivation
    if user.id == request.user.id:
        messages.error(request, 'You cannot deactivate your own account!')
        return redirect('management:user_detail', pk=pk)
    
    user.is_active = not user.is_active
    user.save()
    
    status = 'activated' if user.is_active else 'deactivated'
    messages.success(request, f'User {user.username} has been {status}.')
    
    # Return JSON for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'is_active': user.is_active
        })
    
    return redirect('management:user_detail', pk=pk)


@login_required
@user_passes_test(is_admin)
@require_POST
def user_change_role(request, pk):
    """Change user role (AJAX endpoint)"""
    user = get_object_or_404(User, pk=pk)
    form = QuickRoleChangeForm(request.POST)
    
    if form.is_valid():
        user.profile.role = form.cleaned_data['role']
        user.profile.save()
        
        messages.success(
            request, 
            f"Role changed to {user.profile.get_role_display()}"
        )
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'role': user.profile.role,
                'role_display': user.profile.get_role_display()
            })
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
    
    return redirect('management:user_detail', pk=pk)


@login_required
@user_passes_test(is_admin)
@require_POST
def bulk_user_action(request):
    """Handle bulk actions on users"""
    action = request.POST.get('action')
    user_ids = request.POST.get('user_ids', '').split(',')
    
    if not action or not user_ids:
        messages.error(request, 'Invalid bulk action request.')
        return redirect('management:users_list')
    
    # Filter out current user to prevent self-modification
    user_ids = [int(uid) for uid in user_ids if uid and int(uid) != request.user.id]
    
    if not user_ids:
        messages.warning(request, 'No valid users selected.')
        return redirect('management:users_list')
    
    users = User.objects.filter(id__in=user_ids)
    count = users.count()
    
    if action == 'activate':
        users.update(is_active=True)
        messages.success(request, f'{count} user(s) activated successfully.')
    
    elif action == 'deactivate':
        users.update(is_active=False)
        messages.success(request, f'{count} user(s) deactivated successfully.')
    
    else:
        messages.error(request, 'Invalid action specified.')
    
    return redirect('management:users_list')


@login_required
@user_passes_test(is_admin)
def user_quick_info(request, pk):
    """Get quick user info for preview (AJAX endpoint)"""
    user = get_object_or_404(User.objects.select_related('profile'), pk=pk)
    
    data = {
        'id': user.id,
        'username': user.username,
        'full_name': user.get_full_name() or user.username,
        'email': user.email,
        'role': user.profile.get_role_display(),
        'is_active': user.is_active,
        'is_staff': user.is_staff,
        'date_joined': user.date_joined.strftime('%B %d, %Y'),
        'last_login': user.last_login.strftime('%B %d, %Y') if user.last_login else 'Never',
        'avatar_url': user.profile.avatar.url if user.profile.avatar else None,
    }
    
    return JsonResponse(data)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta
import json
import csv

# Import models
from eduweb.models import (
    SystemConfiguration, 
    CourseCategory, 
    AuditLog
)

# Import forms
from management.forms import (
    SystemConfigurationForm,
    BrandingConfigForm,
    EmailConfigForm,
    NotificationConfigForm,
    CourseCategoryForm,
    AuditLogFilterForm
)


def is_admin(user):
    """Check if user is staff/admin"""
    return user.is_staff or user.is_superuser


# ==================== SYSTEM CONFIGURATION VIEWS ====================
@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def system_config_list(request):
    """List all system configurations"""
    configs = SystemConfiguration.objects.all().order_by('key')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        configs = configs.filter(
            Q(key__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(configs, 20)
    page = request.GET.get('page', 1)
    configs_page = paginator.get_page(page)
    
    context = {
        'configs': configs_page,
        'search_query': search_query,
        'total_configs': configs.count()
    }
    return render(request, 'management/system_config/list.html', context)


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def system_config_create(request):
    """Create new system configuration"""
    if request.method == 'POST':
        form = SystemConfigurationForm(request.POST)
        if form.is_valid():
            config = form.save(commit=False)
            config.updated_by = request.user
            config.save()
            
            # Create audit log
            AuditLog.objects.create(
                user=request.user,
                action='create',
                model_name='SystemConfiguration',
                object_id=config.id,
                description=f'Created configuration: {config.key}'
            )
            
            messages.success(request, f'Configuration "{config.key}" created successfully.')
            return redirect('management:system_config_list')
    else:
        form = SystemConfigurationForm()
    
    return render(request, 'management/system_config/create.html', {'form': form})


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def system_config_edit(request, pk):
    """Edit system configuration"""
    config = get_object_or_404(SystemConfiguration, pk=pk)
    
    if request.method == 'POST':
        form = SystemConfigurationForm(request.POST, instance=config)
        if form.is_valid():
            config = form.save(commit=False)
            config.updated_by = request.user
            config.save()
            
            # Create audit log
            AuditLog.objects.create(
                user=request.user,
                action='update',
                model_name='SystemConfiguration',
                object_id=config.id,
                description=f'Updated configuration: {config.key}'
            )
            
            messages.success(request, f'Configuration "{config.key}" updated successfully.')
            return redirect('management:system_config_list')
    else:
        form = SystemConfigurationForm(instance=config)
    
    return render(request, 'management/system_config/edit.html', {
        'form': form,
        'config': config
    })


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def system_config_delete(request, pk):
    """Delete system configuration"""
    config = get_object_or_404(SystemConfiguration, pk=pk)
    
    if request.method == 'POST':
        config_key = config.key
        
        # Create audit log before deletion
        AuditLog.objects.create(
            user=request.user,
            action='delete',
            model_name='SystemConfiguration',
            object_id=config.id,
            description=f'Deleted configuration: {config_key}'
        )
        
        config.delete()
        messages.success(request, f'Configuration "{config_key}" deleted successfully.')
        return redirect('management:system_config_list')
    
    return render(request, 'management/system_config/delete.html', {'config': config})


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def branding_config(request):
    """Manage branding configuration"""
    if request.method == 'POST':
        form = BrandingConfigForm(request.POST, request.FILES)
        if form.is_valid():
            # Save each configuration
            for key, value in form.cleaned_data.items():
                if value:
                    config, created = SystemConfiguration.objects.get_or_create(
                        key=f'branding_{key}',
                        defaults={
                            'setting_type': 'text',
                            'is_public': True,
                            'updated_by': request.user
                        }
                    )
                    config.value = str(value)
                    config.updated_by = request.user
                    config.save()
            
            # Create audit log
            AuditLog.objects.create(
                user=request.user,
                action='update',
                model_name='SystemConfiguration',
                description='Updated branding configuration'
            )
            
            messages.success(request, 'Branding settings updated successfully.')
            return redirect('management:branding_config')
    else:
        # Load existing values
        initial_data = {}
        for key in ['site_name', 'site_tagline', 'primary_color']:
            try:
                config = SystemConfiguration.objects.get(key=f'branding_{key}')
                initial_data[key] = config.value
            except SystemConfiguration.DoesNotExist:
                pass
        
        form = BrandingConfigForm(initial=initial_data)
    
    return render(request, 'management/system_config/branding.html', {'form': form})


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def email_config(request):
    """Manage email configuration"""
    if request.method == 'POST':
        form = EmailConfigForm(request.POST)
        if form.is_valid():
            # Save email configuration
            for key, value in form.cleaned_data.items():
                config, created = SystemConfiguration.objects.get_or_create(
                    key=f'email_{key}',
                    defaults={
                        'setting_type': 'text',
                        'is_public': False,
                        'updated_by': request.user
                    }
                )
                config.value = str(value)
                config.updated_by = request.user
                config.save()
            
            # Create audit log
            AuditLog.objects.create(
                user=request.user,
                action='update',
                model_name='SystemConfiguration',
                description='Updated email configuration'
            )
            
            messages.success(request, 'Email settings updated successfully.')
            return redirect('management:email_config')
    else:
        # Load existing values
        initial_data = {}
        for key in ['smtp_host', 'smtp_port', 'smtp_username', 'from_email', 'from_name']:
            try:
                config = SystemConfiguration.objects.get(key=f'email_{key}')
                initial_data[key] = config.value
            except SystemConfiguration.DoesNotExist:
                pass
        
        form = EmailConfigForm(initial=initial_data)
    
    return render(request, 'management/system_config/email.html', {'form': form})


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def notification_config(request):
    """Manage notification settings"""
    if request.method == 'POST':
        form = NotificationConfigForm(request.POST)
        if form.is_valid():
            # Save notification configuration
            for key, value in form.cleaned_data.items():
                config, created = SystemConfiguration.objects.get_or_create(
                    key=f'notification_{key}',
                    defaults={
                        'setting_type': 'boolean' if isinstance(value, bool) else 'text',
                        'is_public': False,
                        'updated_by': request.user
                    }
                )
                config.value = str(value)
                config.updated_by = request.user
                config.save()
            
            # Create audit log
            AuditLog.objects.create(
                user=request.user,
                action='update',
                model_name='SystemConfiguration',
                description='Updated notification configuration'
            )
            
            messages.success(request, 'Notification settings updated successfully.')
            return redirect('management:notification_config')
    else:
        # Load existing values
        initial_data = {}
        form = NotificationConfigForm(initial=initial_data)
    
    return render(request, 'management/system_config/notifications.html', {'form': form})


# @login_required(login_url='eduweb:auth_page')
# @user_passes_test(is_admin)
# def course_categories_list(request):
#     """List all course categories"""
#     # Add course counts to categories
#     categories = CourseCategory.objects.annotate(
#         course_count=Count('lms_courses')
#     ).order_by('display_order', 'name')
    
#     # Search functionality
#     search_query = request.GET.get('search', '')
#     if search_query:
#         categories = categories.filter(
#             Q(name__icontains=search_query) | 
#             Q(description__icontains=search_query)
#         )
    
#     # Status filter
#     status = request.GET.get('status', '')
#     if status == 'active':
#         categories = categories.filter(is_active=True)
#     elif status == 'inactive':
#         categories = categories.filter(is_active=False)
    
#     # Pagination
#     paginator = Paginator(categories, 15)
#     page = request.GET.get('page', 1)
#     categories_page = paginator.get_page(page)
    
#     context = {
#         'categories': categories_page,
#         'search_query': search_query,
#         'status': status,
#         'total_categories': categories.count()
#     }
#     return render(request, 'management/course/list.html', context)


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def course_category_create(request):
    """Create new course category"""
    if request.method == 'POST':
        form = CourseCategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            
            # Create audit log
            AuditLog.objects.create(
                user=request.user,
                action='create',
                model_name='CourseCategory',
                object_id=category.id,
                description=f'Created course category: {category.name}'
            )
            
            messages.success(request, f'Category "{category.name}" created successfully.')
            return redirect('management:course_categories_list')
    else:
        form = CourseCategoryForm()
    
    return render(request, 'management/course/create.html', {'form': form})


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def course_category_edit(request, pk):
    """Edit course category"""
    category = get_object_or_404(CourseCategory, pk=pk)
    
    if request.method == 'POST':
        form = CourseCategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save()
            
            # Create audit log
            AuditLog.objects.create(
                user=request.user,
                action='update',
                model_name='CourseCategory',
                object_id=category.id,
                description=f'Updated course category: {category.name}'
            )
            
            messages.success(request, f'Category "{category.name}" updated successfully.')
            return redirect('management:course_categories_list')
    else:
        form = CourseCategoryForm(instance=category)
    
    return render(request, 'management/course/edit.html', {
        'form': form,
        'category': category
    })


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def course_category_delete(request, pk):
    """Delete course category"""
    category = get_object_or_404(CourseCategory, pk=pk)
    
    # Check if category has courses
    course_count = category.lmscourse_set.count()
    
    if request.method == 'POST':
        category_name = category.name
        
        # Create audit log before deletion
        AuditLog.objects.create(
            user=request.user,
            action='delete',
            model_name='CourseCategory',
            object_id=category.id,
            description=f'Deleted course category: {category_name}'
        )
        
        category.delete()
        messages.success(request, f'Category "{category_name}" deleted successfully.')
        return redirect('management:course_categories_list')
    
    return render(request, 'management/course/delete.html', {
        'category': category,
        'course_count': course_count
    })


# ==================== LMS COURSE VIEWS ====================
@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def lms_courses_list(request):
    """List all LMS courses with filtering"""
    courses = LMSCourse.objects.select_related('category', 'instructor').order_by('-created_at')
    
    # Filtering
    category_id = request.GET.get('category')
    if category_id:
        courses = courses.filter(category_id=category_id)
    
    difficulty = request.GET.get('difficulty')
    if difficulty:
        courses = courses.filter(difficulty_level=difficulty)
    
    published_filter = request.GET.get('published')
    if published_filter == 'published':
        courses = courses.filter(is_published=True)
    elif published_filter == 'draft':
        courses = courses.filter(is_published=False)
    
    categories = CourseCategory.objects.filter(is_active=True).order_by('name')
    stats = {
        'total': LMSCourse.objects.count(),
        'published': LMSCourse.objects.filter(is_published=True).count(),
        'draft': LMSCourse.objects.filter(is_published=False).count(),
        'featured': LMSCourse.objects.filter(is_featured=True).count(),
    }
    
    context = {
        'courses': courses,
        'categories': categories,
        'stats': stats,
    }
    return render(request, 'management/lms_course/list.html', context)


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def lms_course_create(request):
    """Create new LMS course"""
    if request.method == 'POST':
        form = LMSCourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save()
            
            # Create audit log
            AuditLog.objects.create(
                user=request.user,
                action='create',
                model_name='LMSCourse',
                object_id=course.id,
                description=f'Created LMS course: {course.title}'
            )
            
            messages.success(request, f'LMS course "{course.title}" created successfully.')
            return redirect('management:lms_courses_list')
    else:
        form = LMSCourseForm()
    
    context = {'form': form}
    return render(request, 'management/lms_course/create.html', context)


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def lms_course_edit(request, pk):
    """Edit LMS course"""
    course = get_object_or_404(LMSCourse, pk=pk)
    
    if request.method == 'POST':
        form = LMSCourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            course = form.save()
            
            # Create audit log
            AuditLog.objects.create(
                user=request.user,
                action='update',
                model_name='LMSCourse',
                object_id=course.id,
                description=f'Updated LMS course: {course.title}'
            )
            
            messages.success(request, f'LMS course "{course.title}" updated successfully.')
            return redirect('management:lms_courses_list')
    else:
        form = LMSCourseForm(instance=course)
    
    context = {
        'form': form,
        'course': course,
    }
    return render(request, 'management/lms_course/edit.html', context)


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def lms_course_detail(request, pk):
    """View LMS course details"""
    course = get_object_or_404(LMSCourse, pk=pk)
    enrollments = course.enrollments.count()
    
    context = {
        'course': course,
        'enrollments': enrollments,
    }
    return render(request, 'management/lms_course/detail.html', context)


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def lms_course_delete(request, pk):
    """Delete LMS course"""
    course = get_object_or_404(LMSCourse, pk=pk)
    enrollment_count = course.enrollments.count()
    
    if request.method == 'POST':
        course_title = course.title
        
        # Create audit log before deletion
        AuditLog.objects.create(
            user=request.user,
            action='delete',
            model_name='LMSCourse',
            object_id=course.id,
            description=f'Deleted LMS course: {course_title}'
        )
        
        course.delete()
        messages.success(request, f'LMS course "{course_title}" deleted successfully.')
        return redirect('management:lms_courses_list')
    
    context = {
        'course': course,
        'enrollment_count': enrollment_count,
    }
    return render(request, 'management/lms_course/delete.html', context)


# ==================== AUDIT LOG VIEWS ====================
@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def audit_logs_list(request):
    """List all audit logs with filtering"""
    logs = AuditLog.objects.select_related('user').order_by('-timestamp')
    
    # Apply filters
    form = AuditLogFilterForm(request.GET)
    if form.is_valid():
        if form.cleaned_data.get('user'):
            logs = logs.filter(user=form.cleaned_data['user'])
        if form.cleaned_data.get('action'):
            logs = logs.filter(action=form.cleaned_data['action'])
        if form.cleaned_data.get('date_from'):
            logs = logs.filter(timestamp__date__gte=form.cleaned_data['date_from'])
        if form.cleaned_data.get('date_to'):
            logs = logs.filter(timestamp__date__lte=form.cleaned_data['date_to'])
        if form.cleaned_data.get('search'):
            logs = logs.filter(
                Q(description__icontains=form.cleaned_data['search']) |
                Q(model_name__icontains=form.cleaned_data['search'])
            )
    
    # Pagination
    paginator = Paginator(logs, 50)
    page = request.GET.get('page', 1)
    logs_page = paginator.get_page(page)
    
    # Statistics
    stats = {
        'total_logs': logs.count(),
        'today_logs': AuditLog.objects.filter(timestamp__date=timezone.now().date()).count(),
        'week_logs': AuditLog.objects.filter(
            timestamp__gte=timezone.now() - timedelta(days=7)
        ).count(),
        'action_breakdown': AuditLog.objects.values('action').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
    }
    
    context = {
        'logs': logs_page,
        'form': form,
        'stats': stats,
        'total_logs': logs.count()
    }
    return render(request, 'management/audit_logs/list.html', context)


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def audit_log_detail(request, pk):
    """View detailed audit log entry"""
    log = get_object_or_404(AuditLog, pk=pk)
    
    # Get related logs (same object)
    related_logs = []
    if log.model_name and log.object_id:
        related_logs = AuditLog.objects.filter(
            model_name=log.model_name,
            object_id=log.object_id
        ).exclude(pk=log.pk).order_by('-timestamp')[:10]
    
    context = {
        'log': log,
        'related_logs': related_logs
    }
    return render(request, 'management/audit_logs/detail.html', context)


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def audit_logs_export(request):
    """Export audit logs to CSV"""
    logs = AuditLog.objects.select_related('user').order_by('-timestamp')
    
    # Apply same filters as list view
    form = AuditLogFilterForm(request.GET)
    if form.is_valid():
        if form.cleaned_data.get('user'):
            logs = logs.filter(user=form.cleaned_data['user'])
        if form.cleaned_data.get('action'):
            logs = logs.filter(action=form.cleaned_data['action'])
        if form.cleaned_data.get('date_from'):
            logs = logs.filter(timestamp__date__gte=form.cleaned_data['date_from'])
        if form.cleaned_data.get('date_to'):
            logs = logs.filter(timestamp__date__lte=form.cleaned_data['date_to'])
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="audit_logs.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Timestamp', 'User', 'Action', 'Model', 'Object ID', 'Description', 'IP Address'])
    
    for log in logs:
        writer.writerow([
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            log.user.username if log.user else 'System',
            log.action,
            log.model_name or '',
            log.object_id or '',
            log.description,
            log.ip_address or ''
        ])
    
    return response


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def security_dashboard(request):
    """Security overview dashboard"""
    # Recent security events
    security_logs = AuditLog.objects.filter(
        action__in=['login', 'logout', 'password_reset', 'permission_change']
    ).select_related('user').order_by('-timestamp')[:20]
    
    # Failed login attempts (would need additional tracking)
    failed_logins = []
    
    # Active sessions count
    active_users = User.objects.filter(
        is_active=True,
        last_login__gte=timezone.now() - timedelta(hours=24)
    ).count()
    
    # Permission changes in last 30 days
    recent_permission_changes = AuditLog.objects.filter(
        action='permission_change',
        timestamp__gte=timezone.now() - timedelta(days=30)
    ).count()
    
    context = {
        'security_logs': security_logs,
        'failed_logins': failed_logins,
        'active_users': active_users,
        'recent_permission_changes': recent_permission_changes
    }
    return render(request, 'management/security/dashboard.html', context)

# ==================== BROADCAST CENTER ====================
@login_required
@user_passes_test(
    lambda u: u.is_staff or u.is_superuser or u.profile.role == 'admin'
)
def broadcast_center(request):
    """List all broadcasts with status counts"""
    broadcasts = BroadcastMessage.objects.select_related('created_by').all()
    
    # Calculate status counts
    sent_count = broadcasts.filter(status='sent').count()
    draft_count = broadcasts.filter(status='draft').count()
    failed_count = broadcasts.filter(status='failed').count()
    
    context = {
        'broadcasts': broadcasts,
        'sent_count': sent_count,
        'draft_count': draft_count,
        'failed_count': failed_count,
        'page_title': 'Broadcast Center',
    }
    return render(
        request, 
        'management/broadcast/list.html', 
        context
    )


@login_required
@user_passes_test(
    lambda u: u.is_staff or u.is_superuser or u.profile.role == 'admin'
)
def broadcast_create(request):
    """Create new broadcast"""
    if request.method == 'POST':
        form = BroadcastMessageForm(request.POST)
        if form.is_valid():
            broadcast = form.save(commit=False)
            broadcast.created_by = request.user
            
            # Collect filter values
            filter_values = {}
            filter_type = form.cleaned_data['filter_type']
            
            if filter_type == 'faculty':
                filter_values['faculties'] = list(
                    form.cleaned_data['faculties']
                    .values_list('id', flat=True)
                )
            elif filter_type == 'course':
                filter_values['courses'] = list(
                    form.cleaned_data['courses']
                    .values_list('id', flat=True)
                )
            elif filter_type == 'lms_course':
                filter_values['lms_courses'] = list(
                    form.cleaned_data['lms_courses']
                    .values_list('id', flat=True)
                )
            elif filter_type == 'role':
                filter_values['roles'] = form.cleaned_data['roles']
            elif filter_type == 'application_status':
                filter_values['application_statuses'] = (
                    form.cleaned_data['application_statuses']
                )
            elif filter_type == 'enrollment_status':
                filter_values['enrollment_statuses'] = (
                    form.cleaned_data['enrollment_statuses']
                )
            
            broadcast.filter_values = filter_values
            
            # Get recipient emails
            emails = get_recipient_emails(filter_type, filter_values)
            broadcast.recipient_emails = emails
            broadcast.recipient_count = len(emails)
            
            broadcast.save()
            
            messages.success(
                request, 
                f'Broadcast created! {len(emails)} recipients identified.'
            )
            return redirect('management:broadcast_center')
    else:
        form = BroadcastMessageForm()
    
    context = {
        'form': form,
        'page_title': 'Create Broadcast',
    }
    return render(
        request, 
        'management/broadcast/form.html', 
        context
    )

@login_required
@user_passes_test(
    lambda u: u.is_staff or u.is_superuser or u.profile.role == 'admin'
)
def broadcast_edit(request, slug):
    """Edit draft broadcast"""
    broadcast = get_object_or_404(BroadcastMessage, slug=slug)
    
    # Only allow editing drafts
    if broadcast.status != 'draft':
        messages.error(
            request, 
            'Only draft broadcasts can be edited.'
        )
        return redirect('management:broadcast_center')
    
    if request.method == 'POST':
        form = BroadcastMessageForm(request.POST, instance=broadcast)
        if form.is_valid():
            broadcast = form.save(commit=False)
            
            # Update filter values
            filter_values = {}
            filter_type = form.cleaned_data['filter_type']
            
            if filter_type == 'faculty':
                filter_values['faculties'] = list(
                    form.cleaned_data['faculties']
                    .values_list('id', flat=True)
                )
            elif filter_type == 'course':
                filter_values['courses'] = list(
                    form.cleaned_data['courses']
                    .values_list('id', flat=True)
                )
            elif filter_type == 'lms_course':
                filter_values['lms_courses'] = list(
                    form.cleaned_data['lms_courses']
                    .values_list('id', flat=True)
                )
            elif filter_type == 'role':
                filter_values['roles'] = form.cleaned_data['roles']
            elif filter_type == 'application_status':
                filter_values['application_statuses'] = (
                    form.cleaned_data['application_statuses']
                )
            elif filter_type == 'enrollment_status':
                filter_values['enrollment_statuses'] = (
                    form.cleaned_data['enrollment_statuses']
                )
            
            broadcast.filter_values = filter_values
            
            # Recalculate recipient emails
            emails = get_recipient_emails(filter_type, filter_values)
            broadcast.recipient_emails = emails
            broadcast.recipient_count = len(emails)
            
            broadcast.save()
            
            messages.success(
                request, 
                f'Broadcast updated! {len(emails)} recipients identified.'
            )
            return redirect('management:broadcast_center')
    else:
        # Pre-populate form with existing data
        initial_data = {
            'subject': broadcast.subject,
            'message': broadcast.message,
            'filter_type': broadcast.filter_type,
        }
        
        # Pre-populate filter selections
        filter_type = broadcast.filter_type
        filter_values = broadcast.filter_values
        
        if filter_type == 'faculty' and 'faculties' in filter_values:
            initial_data['faculties'] = Faculty.objects.filter(
                id__in=filter_values['faculties']
            )
        elif filter_type == 'course' and 'courses' in filter_values:
            initial_data['courses'] = Course.objects.filter(
                id__in=filter_values['courses']
            )
        elif filter_type == 'lms_course' and 'lms_courses' in filter_values:
            initial_data['lms_courses'] = LMSCourse.objects.filter(
                id__in=filter_values['lms_courses']
            )
        elif filter_type == 'role' and 'roles' in filter_values:
            initial_data['roles'] = filter_values['roles']
        elif (filter_type == 'application_status' and 
              'application_statuses' in filter_values):
            initial_data['application_statuses'] = (
                filter_values['application_statuses']
            )
        elif (filter_type == 'enrollment_status' and 
              'enrollment_statuses' in filter_values):
            initial_data['enrollment_statuses'] = (
                filter_values['enrollment_statuses']
            )
        
        form = BroadcastMessageForm(instance=broadcast, initial=initial_data)
    
    context = {
        'form': form,
        'broadcast': broadcast,
        'is_edit': True,
        'page_title': f'Edit Broadcast: {broadcast.subject}',
    }
    return render(
        request, 
        'management/broadcast/form.html', 
        context
    )

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser or u.profile.role == 'admin')
def broadcast_send(request, slug):
    """Send broadcast email - POST only"""
    broadcast = get_object_or_404(BroadcastMessage, slug=slug)
    
    if broadcast.status == 'sent':
        messages.warning(request, 'This broadcast has already been sent.')
        return redirect('management:broadcast_center')
    
    if request.method == 'POST':
        import threading
        
        def send_emails_background():
            """Background thread to send emails"""
            try:
                # Send emails in smaller batches for better performance
                batch_size = 50
                email_list = broadcast.recipient_emails
                
                for i in range(0, len(email_list), batch_size):
                    batch = email_list[i:i + batch_size]
                    email_messages = [
                        (
                            broadcast.subject,
                            broadcast.message,
                            settings.DEFAULT_FROM_EMAIL,
                            [email],
                        )
                        for email in batch
                    ]
                    send_mass_mail(email_messages, fail_silently=False)
                
                # Update status after all sent
                broadcast.status = 'sent'
                broadcast.sent_at = timezone.now()
                broadcast.save()
                
            except Exception as e:
                broadcast.status = 'failed'
                broadcast.error_message = str(e)
                broadcast.save()
        
        # Start background thread
        thread = threading.Thread(target=send_emails_background)
        thread.daemon = True
        thread.start()
        
        # Immediate response to user
        messages.success(
            request, 
            f'Sending broadcast to {broadcast.recipient_count} recipients...'
        )
    
    return redirect('management:broadcast_center')

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser or u.profile.role == 'admin')
def broadcast_delete(request, slug):
    """Delete broadcast - POST only"""
    broadcast = get_object_or_404(BroadcastMessage, slug=slug)
    
    if request.method == 'POST':
        broadcast.delete()
        messages.success(request, 'Broadcast deleted successfully.')
    
    return redirect('management:broadcast_center')


# ==================== HELPER FUNCTIONS ====================
def get_recipient_emails(filter_type, filter_values):
    """Get recipient emails based on filter"""
    emails = set()
    
    if filter_type == 'all_users':
        # All active users
        emails = set(
            User.objects.filter(is_active=True)
            .values_list('email', flat=True)
        )
    
    elif filter_type == 'faculty':
        # Users who applied to courses in selected faculties
        faculty_ids = filter_values.get('faculties', [])
        emails = set(
            CourseApplication.objects.filter(
                program__department__faculty_id__in=faculty_ids
            ).values_list('email', flat=True)
        )
    
    elif filter_type == 'course':
        # Users who applied to selected programs
        program_ids = filter_values.get('courses', [])
        emails = set(
            CourseApplication.objects.filter(
                program_id__in=program_ids
            ).values_list('email', flat=True)
        )
    
    elif filter_type == 'lms_course':
        # Users enrolled in selected LMS courses
        lms_course_ids = filter_values.get('lms_courses', [])
        user_emails = User.objects.filter(
            enrollments__course_id__in=lms_course_ids
        ).values_list('email', flat=True)
        emails = set(user_emails)
    
    elif filter_type == 'role':
        # Users with selected roles
        roles = filter_values.get('roles', [])
        user_emails = User.objects.filter(
            profile__role__in=roles
        ).values_list('email', flat=True)
        emails = set(user_emails)
    
    elif filter_type == 'application_status':
        # Users with specific application statuses
        statuses = filter_values.get('application_statuses', [])
        emails = set(
            CourseApplication.objects.filter(
                status__in=statuses
            ).values_list('email', flat=True)
        )
    
    elif filter_type == 'enrollment_status':
        # Users with specific enrollment statuses
        statuses = filter_values.get('enrollment_statuses', [])
        user_emails = User.objects.filter(
            enrollments__status__in=statuses
        ).values_list('email', flat=True)
        emails = set(user_emails)
    
    # Remove empty emails
    emails = {e for e in emails if e}
    
    return list(emails)


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def approve_department(request, pk):
    """Department head approves admission"""
    
    if request.method == 'POST':
        application = get_object_or_404(CourseApplication, pk=pk)
        
        if not application.admission_accepted:
            messages.error(
                request, 
                'Student must accept admission first.'
            )
            return redirect('management:application_detail', application_id=application.application_id)
        
        application.department_approved = True
        application.department_approved_at = timezone.now()
        application.department_approved_by = request.user
        application.save()
        
        # Send notification to student
        send_department_approval_email(application)
        
        messages.success(
            request,
            f'Department approval granted for {application.admission_number}'
        )
        
        return redirect('management:application_detail', application_id=application.application_id)
    
    return redirect('management:applications_list')


def send_department_approval_email(application):
    """Send email when department approves admission"""
    try:
        subject = f'Portal Access Granted - {application.admission_number}'
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; 
                         line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; 
                            padding: 20px; background-color: #f4f4f4;">
                    <div style="background: linear-gradient(135deg, 
                                #0F2A44 0%, #1D4ED8 100%); 
                                padding: 30px; text-align: center;">
                        <h1 style="color: white; margin: 0;">
                            🎉 Welcome to MIU Student Portal!
                        </h1>
                    </div>
                    
                    <div style="background-color: white; 
                                padding: 30px; margin-top: 20px;">
                        <p style="font-size: 16px;">
                            Dear <strong>
                                {application.first_name} 
                                {application.last_name}
                            </strong>,
                        </p>
                        
                        <div style="background-color: #10b98115; 
                                    padding: 20px; border-radius: 8px; 
                                    margin: 25px 0; 
                                    border-left: 4px solid #10b981;">
                            <h3 style="color: #10b981; margin-top: 0;">
                                Department Approval Complete!
                            </h3>
                            <p>
                                Your admission has been approved by 
                                the department.
                            </p>
                            <p>
                                <strong>Admission Number:</strong> 
                                {application.admission_number}
                            </p>
                        </div>
                        
                        <h4>You can now access:</h4>
                        <ul>
                            <li>Student Dashboard</li>
                            <li>Course Materials</li>
                            <li>Academic Resources</li>
                            <li>Student Services</li>
                        </ul>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{settings.SITE_URL}/login/" 
                               style="background-color: #1D4ED8; 
                                      color: white; padding: 12px 30px; 
                                      text-decoration: none; 
                                      border-radius: 5px; 
                                      display: inline-block;">
                                Access Student Portal
                            </a>
                        </div>
                        
                        <p style="margin-top: 30px;">
                            Welcome to MIU!<br>
                            <strong style="color: #0F2A44;">
                                The MIU Team
                            </strong>
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=f"Portal Access Granted - {application.admission_number}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[application.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        return True
        
    except Exception as e:
        print(f"Error sending approval email: {str(e)}")
        return False

# ============================================================
# ADD THESE IMPORTS TO THE TOP OF views.py (if not already present)
# ============================================================
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings

# ── Import your models ──────────────────────────────────────────────────────
from eduweb.models import (
    Department, Program, AcademicSession, CourseIntake,
    CourseCategory, SupportTicket, TicketReply,
    ContactMessage, Announcement, Faculty
)


# ── Helper: restrict to admin/staff ─────────────────────────────────────────
def is_admin(user):
    return user.is_staff or user.is_superuser or (
        hasattr(user, 'profile') and user.profile.role == 'admin'
    )


# ===========================================================================
# DEPARTMENTS
# ===========================================================================

@login_required
@user_passes_test(is_admin)
def departments_list(request):
    qs = Department.objects.select_related('faculty').prefetch_related('programs')

    search = request.GET.get('search', '').strip()
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(code__icontains=search))

    faculty_id = request.GET.get('faculty', '')
    if faculty_id:
        qs = qs.filter(faculty_id=faculty_id)

    status = request.GET.get('status', '')
    if status == 'active':
        qs = qs.filter(is_active=True)
    elif status == 'inactive':
        qs = qs.filter(is_active=False)
    
    # Order before pagination
    qs = qs.order_by('name')

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'departments': page_obj,
        'faculties': Faculty.objects.all(),
        'total_departments': Department.objects.count(),
        'active_departments': Department.objects.filter(is_active=True).count(),
        'total_faculties': Faculty.objects.count(),
        'total_programs': Program.objects.count(),
    }
    return render(request, 'management/departments_list.html', context)


@login_required
@user_passes_test(is_admin)
def department_create(request):
    from .forms import DepartmentForm
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Department created successfully.')
            return redirect('management:departments_list')
    else:
        form = DepartmentForm()
    return render(request, 'management/department_form.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def department_edit(request, pk):
    from .forms import DepartmentForm
    dept = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=dept)
        if form.is_valid():
            form.save()
            messages.success(request, 'Department updated.')
            return redirect('management:departments_list')
    else:
        form = DepartmentForm(instance=dept)
    return render(request, 'management/department_form.html', {'form': form, 'department': dept})


@login_required
@user_passes_test(is_admin)
def department_delete(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        dept_name = dept.name
        dept.delete()
        messages.success(request, f'Department "{dept_name}" deleted successfully.')
        return redirect('management:departments_list')
    
    return render(request, 'management/department_delete.html', {'department': dept})


# ===========================================================================
# PROGRAMS
# ===========================================================================

@login_required
@user_passes_test(is_admin)
def programs_list(request):
    qs = Program.objects.select_related('department__faculty').order_by('name')

    search = request.GET.get('search', '').strip()
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(code__icontains=search))

    faculty_id = request.GET.get('faculty', '')
    if faculty_id:
        qs = qs.filter(department__faculty_id=faculty_id)

    degree_level = request.GET.get('degree_level', '')
    if degree_level:
        qs = qs.filter(degree_level=degree_level)

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'programs': page_obj,
        'faculties': Faculty.objects.all(),
        'stats': [
            {'label': 'Total Programs', 'value': Program.objects.count(), 'color': 'text-primary-600'},
            {'label': 'Active', 'value': Program.objects.filter(is_active=True).count(), 'color': 'text-green-600'},
            {'label': 'Featured', 'value': Program.objects.filter(is_featured=True).count(), 'color': 'text-yellow-600'},
            {'label': 'Departments', 'value': Department.objects.count(), 'color': 'text-blue-600'},
        ],
    }
    return render(request, 'management/programs_list.html', context)


@login_required
@user_passes_test(is_admin)
def program_create(request):
    from .forms import ProgramForm
    if request.method == 'POST':
        form = ProgramForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Program created.')
            return redirect('management:programs_list')
    else:
        form = ProgramForm()
    return render(request, 'management/program_form.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def program_edit(request, pk):
    from .forms import ProgramForm
    program = get_object_or_404(Program, pk=pk)
    if request.method == 'POST':
        form = ProgramForm(request.POST, request.FILES, instance=program)
        if form.is_valid():
            form.save()
            messages.success(request, 'Program updated.')
            return redirect('management:programs_list')
    else:
        form = ProgramForm(instance=program)
    return render(request, 'management/program_form.html', {'form': form, 'program': program})


@login_required
@user_passes_test(is_admin)
def program_detail(request, pk):
    program = get_object_or_404(Program.objects.select_related('department__faculty'), pk=pk)
    intakes = program.intakes.all()
    applications = program.applications.all()[:10]
    context = {'program': program, 'intakes': intakes, 'applications': applications}
    return render(request, 'management/program_detail.html', context)


@login_required
@user_passes_test(is_admin)
def program_delete(request, pk):
    program = get_object_or_404(Program, pk=pk)
    if request.method == 'POST':
        program_name = program.name
        program.delete()
        messages.success(request, f'Program "{program_name}" deleted successfully.')
        return redirect('management:programs_list')
    
    return render(request, 'management/program_delete.html', {'program': program})


# ===========================================================================
# ACADEMIC SESSIONS
# ===========================================================================

@login_required
@user_passes_test(is_admin)
def academic_sessions_list(request):
    sessions = AcademicSession.objects.all()
    current_session = AcademicSession.get_current()
    return render(request, 'management/academic_sessions_list.html', {
        'sessions': sessions,
        'current_session': current_session,
    })


@login_required
@user_passes_test(is_admin)
def academic_session_create(request):
    from .forms import AcademicSessionForm
    if request.method == 'POST':
        form = AcademicSessionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Academic session created.')
            return redirect('management:academic_sessions_list')
    else:
        form = AcademicSessionForm()
    return render(request, 'management/academic_session_form.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def academic_session_edit(request, pk):
    from .forms import AcademicSessionForm
    session = get_object_or_404(AcademicSession, pk=pk)
    if request.method == 'POST':
        form = AcademicSessionForm(request.POST, instance=session)
        if form.is_valid():
            form.save()
            messages.success(request, 'Session updated.')
            return redirect('management:academic_sessions_list')
    else:
        form = AcademicSessionForm(instance=session)
    return render(request, 'management/academic_session_form.html', {'form': form, 'session': session})


@login_required
@user_passes_test(is_admin)
def academic_session_set_current(request, pk):
    if request.method == 'POST':
        session = get_object_or_404(AcademicSession, pk=pk)
        # Unset all others
        AcademicSession.objects.exclude(pk=pk).update(is_current=False)
        session.is_current = True
        session.status = 'active'
        session.save()
        messages.success(request, f'{session.name} is now the current session.')
    return redirect('management:academic_sessions_list')


@login_required
@user_passes_test(is_admin)
def academic_session_delete(request, pk):
    session = get_object_or_404(AcademicSession, pk=pk)
    
    if session.is_current:
        messages.error(request, 'Cannot delete the current active session. Please set another session as current first.')
        return redirect('management:academic_sessions_list')
    
    if request.method == 'POST':
        session_name = session.name
        session.delete()
        messages.success(request, f'Session "{session_name}" deleted successfully.')
        return redirect('management:academic_sessions_list')
    
    return render(request, 'management/academic_session_delete.html', {'session': session})


# ===========================================================================
# COURSE INTAKES
# ===========================================================================

@login_required
@user_passes_test(is_admin)
def intakes_list(request):
    qs = CourseIntake.objects.select_related('program__department__faculty').prefetch_related('applications')

    program_id = request.GET.get('program', '')
    if program_id:
        qs = qs.filter(program_id=program_id)

    year = request.GET.get('year', '')
    if year:
        qs = qs.filter(year=year)

    period = request.GET.get('period', '')
    if period:
        qs = qs.filter(intake_period=period)

    status = request.GET.get('status', '')
    if status == 'active':
        qs = qs.filter(is_active=True)
    elif status == 'inactive':
        qs = qs.filter(is_active=False)
    
    # Order before pagination
    qs = qs.order_by('-year', 'intake_period')

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    years = CourseIntake.objects.values_list('year', flat=True).distinct().order_by('-year')

    context = {
        'intakes': page_obj,
        'programs': Program.objects.filter(is_active=True).order_by('name'),
        'years': years,
        'today': timezone.now().date(),
    }
    return render(request, 'management/intakes_list.html', context)


@login_required
@user_passes_test(is_admin)
def intake_create(request):
    from .forms import CourseIntakeForm
    if request.method == 'POST':
        form = CourseIntakeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Intake created.')
            return redirect('management:intakes_list')
    else:
        form = CourseIntakeForm()
    return render(request, 'management/intake_form.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def intake_edit(request, pk):
    from .forms import CourseIntakeForm
    intake = get_object_or_404(CourseIntake, pk=pk)
    if request.method == 'POST':
        form = CourseIntakeForm(request.POST, instance=intake)
        if form.is_valid():
            form.save()
            messages.success(request, 'Intake updated.')
            return redirect('management:intakes_list')
    else:
        form = CourseIntakeForm(instance=intake)
    return render(request, 'management/intake_form.html', {'form': form, 'intake': intake})


@login_required
@user_passes_test(is_admin)
def intake_delete(request, pk):
    intake = get_object_or_404(CourseIntake, pk=pk)
    if request.method == 'POST':
        intake_name = f"{intake.program.name} ({intake.academic_session.name})"
        intake.delete()
        messages.success(request, f'Intake for {intake_name} deleted successfully.')
        return redirect('management:intakes_list')
    
    return render(request, 'management/intake_delete.html', {'intake': intake})


# ===========================================================================
# COURSE CATEGORIES LIST (the missing page)
# ===========================================================================

@login_required
@user_passes_test(is_admin)
def course_categories_list(request):
    categories = CourseCategory.objects.prefetch_related(
        'lms_courses', 'subcategories'
    ).select_related('parent').order_by('display_order', 'name')
    return render(request, 'management/course_categories_list.html', {'categories': categories})


# ===========================================================================
# SUPPORT TICKETS
# ===========================================================================

@login_required
@user_passes_test(is_admin)
def tickets_list(request):
    from eduweb.models import SupportTicket
    qs = SupportTicket.objects.select_related('user', 'assigned_to').order_by('-created_at')

    search = request.GET.get('search', '').strip()
    if search:
        qs = qs.filter(
            Q(ticket_id__icontains=search) |
            Q(subject__icontains=search) |
            Q(user__username__icontains=search) |
            Q(user__email__icontains=search)
        )

    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)

    priority = request.GET.get('priority', '')
    if priority:
        qs = qs.filter(priority=priority)

    stats = {
        'total': SupportTicket.objects.count(),
        'open': SupportTicket.objects.filter(status='open').count(),
        'in_progress': SupportTicket.objects.filter(status='in_progress').count(),
        'resolved': SupportTicket.objects.filter(status='resolved').count(),
        'urgent': SupportTicket.objects.filter(priority='urgent', status__in=['open', 'in_progress']).count(),
    }

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'management/tickets_list.html', {'tickets': page_obj, 'stats': stats})


@login_required
@user_passes_test(is_admin)
def ticket_detail(request, pk):
    from eduweb.models import SupportTicket, TicketReply
    from django.contrib.auth.models import User
    ticket = get_object_or_404(SupportTicket.objects.select_related('user', 'assigned_to'), pk=pk)
    replies = ticket.replies.select_related('author').order_by('created_at')
    staff_users = User.objects.filter(
        Q(is_staff=True) | Q(profile__role__in=['admin', 'support'])
    ).distinct()
    return render(request, 'management/ticket_detail.html', {
        'ticket': ticket,
        'replies': replies,
        'staff_users': staff_users,
    })


@login_required
@user_passes_test(is_admin)
def ticket_reply(request, pk):
    from eduweb.models import SupportTicket, TicketReply
    ticket = get_object_or_404(SupportTicket, pk=pk)
    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        is_internal = request.POST.get('is_internal_note') == 'on'
        if message:
            TicketReply.objects.create(
                ticket=ticket,
                author=request.user,
                message=message,
                is_internal_note=is_internal,
            )
            # Auto-set to in_progress if open
            if ticket.status == 'open':
                ticket.status = 'in_progress'
                ticket.save(update_fields=['status'])
            messages.success(request, 'Reply posted.')
    return redirect('management:ticket_detail', pk=pk)


@login_required
@user_passes_test(is_admin)
def ticket_change_status(request, pk):
    if request.method == 'POST':
        from eduweb.models import SupportTicket
        ticket = get_object_or_404(SupportTicket, pk=pk)
        new_status = request.POST.get('status')
        if new_status in dict(SupportTicket.STATUS_CHOICES):
            ticket.status = new_status
            ticket.save(update_fields=['status', 'resolved_at', 'updated_at'])
            messages.success(request, f'Status changed to {ticket.get_status_display()}.')
    return redirect('management:ticket_detail', pk=pk)


@login_required
@user_passes_test(is_admin)
def ticket_assign(request, pk):
    if request.method == 'POST':
        from eduweb.models import SupportTicket
        from django.contrib.auth.models import User
        ticket = get_object_or_404(SupportTicket, pk=pk)
        assigned_to_id = request.POST.get('assigned_to')
        if assigned_to_id:
            ticket.assigned_to = get_object_or_404(User, pk=assigned_to_id)
        else:
            ticket.assigned_to = None
        ticket.save(update_fields=['assigned_to'])
        messages.success(request, 'Ticket assigned.')
    return redirect('management:ticket_detail', pk=pk)


# ===========================================================================
# CONTACT MESSAGES
# ===========================================================================

@login_required
@user_passes_test(is_admin)
def contact_messages_list(request):
    from eduweb.models import ContactMessage
    qs = ContactMessage.objects.select_related('user', 'responded_by').order_by('-created_at')

    search = request.GET.get('search', '').strip()
    if search:
        qs = qs.filter(
            Q(name__icontains=search) |
            Q(email__icontains=search) |
            Q(message__icontains=search)
        )

    subject = request.GET.get('subject', '')
    if subject:
        qs = qs.filter(subject=subject)

    read_status = request.GET.get('read_status', '')
    if read_status == 'unread':
        qs = qs.filter(is_read=False)
    elif read_status == 'read':
        qs = qs.filter(is_read=True)

    responded = request.GET.get('responded', '')
    if responded == 'yes':
        qs = qs.filter(responded=True)
    elif responded == 'no':
        qs = qs.filter(responded=False)

    unread_count = ContactMessage.objects.filter(is_read=False).count()
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'management/contact_messages_list.html', {
        'messages_list': page_obj,
        'unread_count': unread_count,
    })


@login_required
@user_passes_test(is_admin)
def contact_message_detail(request, pk):
    from eduweb.models import ContactMessage
    msg = get_object_or_404(ContactMessage, pk=pk)
    # Auto-mark as read on open
    if not msg.is_read:
        msg.is_read = True
        msg.save(update_fields=['is_read'])
    return render(request, 'management/contact_message_detail.html', {'contact_message': msg})


@login_required
@user_passes_test(is_admin)
def contact_message_mark_read(request, pk):
    if request.method == 'POST':
        from eduweb.models import ContactMessage
        msg = get_object_or_404(ContactMessage, pk=pk)
        msg.is_read = True
        msg.save(update_fields=['is_read'])
        messages.success(request, 'Marked as read.')
    return redirect('management:contact_message_detail', pk=pk)


@login_required
@user_passes_test(is_admin)
def contact_message_respond(request, pk):
    if request.method == 'POST':
        from eduweb.models import ContactMessage
        msg = get_object_or_404(ContactMessage, pk=pk)
        response_text = request.POST.get('response', '').strip()
        if response_text:
            try:
                send_mail(
                    subject=f'Re: {msg.get_subject_display()} — MIU',
                    message=response_text,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[msg.email],
                    fail_silently=False,
                )
            except Exception:
                pass  # Log in production
            msg.responded = True
            msg.responded_at = timezone.now()
            msg.responded_by = request.user
            msg.is_read = True
            msg.save(update_fields=['responded', 'responded_at', 'responded_by', 'is_read'])
            messages.success(request, f'Response sent to {msg.email}.')
        else:
            messages.error(request, 'Response cannot be empty.')
    return redirect('management:contact_message_detail', pk=pk)


# ===========================================================================
# ANNOUNCEMENTS
# ===========================================================================

@login_required
@user_passes_test(is_admin)
def announcements_list(request):
    qs = Announcement.objects.select_related('course', 'category', 'created_by').order_by('-priority', '-publish_date')

    search = request.GET.get('search', '').strip()
    if search:
        qs = qs.filter(Q(title__icontains=search) | Q(content__icontains=search))

    ann_type = request.GET.get('type', '')
    if ann_type:
        qs = qs.filter(announcement_type=ann_type)

    priority = request.GET.get('priority', '')
    if priority:
        qs = qs.filter(priority=priority)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'management/announcements_list.html', {'announcements': page_obj})


@login_required
@user_passes_test(is_admin)
def announcement_create(request):
    from .forms import AnnouncementForm
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            ann = form.save(commit=False)
            ann.created_by = request.user
            ann.save()
            messages.success(request, 'Announcement created.')
            return redirect('management:announcements_list')
    else:
        form = AnnouncementForm()
    return render(request, 'management/announcement_form.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def announcement_edit(request, pk):
    from .forms import AnnouncementForm
    announcement = get_object_or_404(Announcement, pk=pk)
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, instance=announcement)
        if form.is_valid():
            form.save()
            messages.success(request, 'Announcement updated.')
            return redirect('management:announcements_list')
    else:
        form = AnnouncementForm(instance=announcement)
    return render(request, 'management/announcement_form.html', {
        'form': form,
        'announcement': announcement,
    })


@login_required
@user_passes_test(is_admin)
def announcement_delete(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    if request.method == 'POST':
        announcement.delete()
        messages.success(request, 'Announcement deleted.')
    return redirect('management:announcements_list')


# ===========================================================================
# ENROLLMENTS MANAGEMENT
# ===========================================================================

@login_required
@user_passes_test(is_admin)
def enrollments_list(request):
    """List all student enrollments"""
    from eduweb.models import Enrollment
    from .forms import EnrollmentForm
    
    qs = Enrollment.objects.select_related(
        'student', 'course'
    ).order_by('-enrolled_at')
    
    search = request.GET.get('search', '').strip()
    if search:
        qs = qs.filter(
            Q(student__user__username__icontains=search) |
            Q(course__name__icontains=search)
        )
    
    status = request.GET.get('status', '')
    if status and hasattr(Enrollment, 'STATUS_CHOICES'):
        qs = qs.filter(status=status)
    
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    return render(request, 'management/enrollments_list.html', {
        'enrollments': page_obj
    })


@login_required
@user_passes_test(is_admin)
def enrollment_create(request):
    """Create new enrollment"""
    from .forms import EnrollmentForm
    
    if request.method == 'POST':
        form = EnrollmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Enrollment created.')
            return redirect('management:enrollments_list')
    else:
        form = EnrollmentForm()
    
    return render(request, 'management/enrollment_form.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def enrollment_edit(request, pk):
    """Edit enrollment"""
    from eduweb.models import Enrollment
    from .forms import EnrollmentForm
    
    enrollment = get_object_or_404(Enrollment, pk=pk)
    if request.method == 'POST':
        form = EnrollmentForm(request.POST, instance=enrollment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Enrollment updated.')
            return redirect('management:enrollments_list')
    else:
        form = EnrollmentForm(instance=enrollment)
    
    return render(request, 'management/enrollment_form.html', {
        'form': form,
        'enrollment': enrollment
    })


@login_required
@user_passes_test(is_admin)
def enrollment_delete(request, pk):
    """Delete enrollment"""
    from eduweb.models import Enrollment
    
    enrollment = get_object_or_404(Enrollment, pk=pk)
    if request.method == 'POST':
        enrollment.delete()
        messages.success(request, 'Enrollment deleted.')
    return redirect('management:enrollments_list')


# ===========================================================================
# STAFF PAYROLL MANAGEMENT
# ===========================================================================

@login_required
@user_passes_test(is_admin)
def staff_payroll_list(request):
    """List all payroll records"""
    from eduweb.models import StaffPayroll
    
    qs = StaffPayroll.objects.select_related('staff').order_by('-payment_date')
    
    search = request.GET.get('search', '').strip()
    if search:
        qs = qs.filter(
            Q(staff__username__icontains=search) |
            Q(pay_period__icontains=search)
        )
    
    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)
    
    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    return render(request, 'management/payroll_list.html', {
        'payroll_records': page_obj
    })


@login_required
@user_passes_test(is_admin)
def staff_payroll_create(request):
    """Create payroll record"""
    from .forms import StaffPayrollForm
    
    if request.method == 'POST':
        form = StaffPayrollForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Payroll created.')
            return redirect('management:staff_payroll_list')
    else:
        form = StaffPayrollForm()
    
    return render(request, 'management/payroll_form.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def staff_payroll_edit(request, pk):
    """Edit payroll record"""
    from eduweb.models import StaffPayroll
    from .forms import StaffPayrollForm
    
    payroll = get_object_or_404(StaffPayroll, pk=pk)
    if request.method == 'POST':
        form = StaffPayrollForm(request.POST, instance=payroll)
        if form.is_valid():
            form.save()
            messages.success(request, 'Payroll updated.')
            return redirect('management:staff_payroll_list')
    else:
        form = StaffPayrollForm(instance=payroll)
    
    return render(request, 'management/payroll_form.html', {
        'form': form,
        'payroll': payroll
    })


@login_required
@user_passes_test(is_admin)
def staff_payroll_delete(request, pk):
    """Delete payroll record"""
    from eduweb.models import StaffPayroll
    
    payroll = get_object_or_404(StaffPayroll, pk=pk)
    if request.method == 'POST':
        payroll.delete()
        messages.success(request, 'Payroll deleted.')
    return redirect('management:staff_payroll_list')


# ===========================================================================
# REVIEWS MANAGEMENT
# ===========================================================================

@login_required
@user_passes_test(is_admin)
def reviews_list(request):
    """List all course reviews"""
    from eduweb.models import Review
    
    qs = Review.objects.select_related(
        'student', 'course'
    ).order_by('-created_at')
    
    search = request.GET.get('search', '').strip()
    if search:
        qs = qs.filter(
            Q(course__title__icontains=search) |
            Q(review_text__icontains=search)
        )
    
    rating = request.GET.get('rating', '')
    if rating:
        try:
            qs = qs.filter(rating=int(rating))
        except ValueError:
            pass
    
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    return render(request, 'management/reviews_list.html', {
        'reviews': page_obj
    })


@login_required
@user_passes_test(is_admin)
def review_create(request):
    """Create review"""
    from .forms import ReviewForm
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Review created.')
            return redirect('management:reviews_list')
    else:
        form = ReviewForm()
    
    return render(request, 'management/review_form.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def review_edit(request, pk):
    """Edit review"""
    from eduweb.models import Review
    from .forms import ReviewForm
    
    review = get_object_or_404(Review, pk=pk)
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, 'Review updated.')
            return redirect('management:reviews_list')
    else:
        form = ReviewForm(instance=review)
    
    return render(request, 'management/review_form.html', {
        'form': form,
        'review': review
    })


@login_required
@user_passes_test(is_admin)
def review_delete(request, pk):
    """Delete review"""
    from eduweb.models import Review
    
    review = get_object_or_404(Review, pk=pk)
    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Review deleted.')
    return redirect('management:reviews_list')


# ===========================================================================
# CERTIFICATES MANAGEMENT
# ===========================================================================

@login_required
@user_passes_test(is_admin)
def certificates_list(request):
    """List all certificates"""
    from eduweb.models import Certificate
    
    qs = Certificate.objects.select_related(
        'student', 'course'
    ).order_by('-issued_date')
    
    search = request.GET.get('search', '').strip()
    if search:
        qs = qs.filter(
            Q(student__user__username__icontains=search) |
            Q(course__title__icontains=search)
        )
    
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    return render(request, 'management/certificates_list.html', {
        'certificates': page_obj
    })


@login_required
@user_passes_test(is_admin)
def certificate_create(request):
    """Create certificate"""
    from .forms import CertificateForm
    
    if request.method == 'POST':
        form = CertificateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Certificate created.')
            return redirect('management:certificates_list')
    else:
        form = CertificateForm()
    
    return render(request, 'management/certificate_form.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def certificate_edit(request, pk):
    """Edit certificate"""
    from eduweb.models import Certificate
    from .forms import CertificateForm
    
    certificate = get_object_or_404(Certificate, pk=pk)
    if request.method == 'POST':
        form = CertificateForm(request.POST, instance=certificate)
        if form.is_valid():
            form.save()
            messages.success(request, 'Certificate updated.')
            return redirect('management:certificates_list')
    else:
        form = CertificateForm(instance=certificate)
    
    return render(request, 'management/certificate_form.html', {
        'form': form,
        'certificate': certificate
    })


@login_required
@user_passes_test(is_admin)
def certificate_delete(request, pk):
    """Delete certificate"""
    from eduweb.models import Certificate
    
    certificate = get_object_or_404(Certificate, pk=pk)
    if request.method == 'POST':
        certificate.delete()
        messages.success(request, 'Certificate deleted.')
    return redirect('management:certificates_list')


# ===========================================================================
# BADGES MANAGEMENT
# ===========================================================================

@login_required
@user_passes_test(is_admin)
def badges_list(request):
    """List all badges"""
    from eduweb.models import Badge
    
    qs = Badge.objects.order_by('name')
    
    search = request.GET.get('search', '').strip()
    if search:
        qs = qs.filter(name__icontains=search)
    
    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    return render(request, 'management/badges_list.html', {
        'badges': page_obj
    })


@login_required
@user_passes_test(is_admin)
def badge_create(request):
    """Create badge"""
    from .forms import BadgeForm
    
    if request.method == 'POST':
        form = BadgeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Badge created.')
            return redirect('management:badges_list')
    else:
        form = BadgeForm()
    
    return render(request, 'management/badge_form.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def badge_edit(request, pk):
    """Edit badge"""
    from eduweb.models import Badge
    from .forms import BadgeForm
    
    badge = get_object_or_404(Badge, pk=pk)
    if request.method == 'POST':
        form = BadgeForm(request.POST, instance=badge)
        if form.is_valid():
            form.save()
            messages.success(request, 'Badge updated.')
            return redirect('management:badges_list')
    else:
        form = BadgeForm(instance=badge)
    
    return render(request, 'management/badge_form.html', {
        'form': form,
        'badge': badge
    })


@login_required
@user_passes_test(is_admin)
def badge_delete(request, pk):
    """Delete badge"""
    from eduweb.models import Badge
    
    badge = get_object_or_404(Badge, pk=pk)
    if request.method == 'POST':
        badge.delete()
        messages.success(request, 'Badge deleted.')
    return redirect('management:badges_list')


# ===========================================================================
# STUDENT BADGES (ASSIGNMENT)
# ===========================================================================

@login_required
@user_passes_test(is_admin)
def student_badges_list(request):
    """List badge assignments"""
    from eduweb.models import StudentBadge
    
    qs = StudentBadge.objects.select_related(
        'student', 'badge', 'awarded_by'
    ).order_by('-awarded_at')
    
    search = request.GET.get('search', '').strip()
    if search:
        qs = qs.filter(
            Q(student__username__icontains=search) |
            Q(badge__name__icontains=search)
        )
    
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    return render(request, 'management/student_badges_list.html', {
        'student_badges': page_obj
    })


@login_required
@user_passes_test(is_admin)
def student_badge_assign(request):
    """Assign badge to student"""
    from .forms import StudentBadgeForm
    
    if request.method == 'POST':
        form = StudentBadgeForm(request.POST)
        if form.is_valid():
            badge = form.save(commit=False)
            badge.awarded_by = request.user
            badge.save()
            messages.success(request, 'Badge assigned.')
            return redirect('management:student_badges_list')
    else:
        form = StudentBadgeForm()
    
    return render(request, 'management/student_badge_form.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def student_badge_delete(request, pk):
    """Revoke badge from student"""
    from eduweb.models import StudentBadge
    
    student_badge = get_object_or_404(StudentBadge, pk=pk)
    if request.method == 'POST':
        student_badge.delete()
        messages.success(request, 'Badge revoked.')
    return redirect('management:student_badges_list')


# ===========================================================================
# PAYMENT GATEWAYS MANAGEMENT
# ===========================================================================

@login_required
@user_passes_test(is_admin)
def payment_gateways_list(request):
    """List payment gateways"""
    from eduweb.models import PaymentGateway
    
    gateways = PaymentGateway.objects.order_by('name')
    
    return render(request, 'management/payment_gateways_list.html', {
        'gateways': gateways
    })


@login_required
@user_passes_test(is_admin)
def payment_gateway_create(request):
    """Create payment gateway"""
    from .forms import PaymentGatewayForm
    
    if request.method == 'POST':
        form = PaymentGatewayForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Gateway added.')
            return redirect('management:payment_gateways_list')
    else:
        form = PaymentGatewayForm()
    
    return render(request, 'management/payment_gateway_form.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def payment_gateway_edit(request, pk):
    """Edit payment gateway"""
    from eduweb.models import PaymentGateway
    from .forms import PaymentGatewayForm
    
    gateway = get_object_or_404(PaymentGateway, pk=pk)
    if request.method == 'POST':
        form = PaymentGatewayForm(request.POST, instance=gateway)
        if form.is_valid():
            form.save()
            messages.success(request, 'Gateway updated.')
            return redirect('management:payment_gateways_list')
    else:
        form = PaymentGatewayForm(instance=gateway)
    
    return render(request, 'management/payment_gateway_form.html', {
        'form': form,
        'gateway': gateway
    })


@login_required
@user_passes_test(is_admin)
def payment_gateway_delete(request, pk):
    """Delete payment gateway"""
    from eduweb.models import PaymentGateway
    
    gateway = get_object_or_404(PaymentGateway, pk=pk)
    if request.method == 'POST':
        gateway.delete()
        messages.success(request, 'Gateway deleted.')
    return redirect('management:payment_gateways_list')


# ===========================================================================
# TRANSACTIONS MANAGEMENT
# ===========================================================================

@login_required
@user_passes_test(is_admin)
def transactions_list(request):
    """List all transactions"""
    from eduweb.models import Transaction
    
    qs = Transaction.objects.select_related(
        'user', 'gateway'
    ).order_by('-created_at')
    
    search = request.GET.get('search', '').strip()
    if search:
        qs = qs.filter(
            Q(user__username__icontains=search) |
            Q(transaction_id__icontains=search)
        )
    
    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)
    
    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    return render(request, 'management/transactions_list.html', {
        'transactions': page_obj
    })


@login_required
@user_passes_test(is_admin)
def transaction_detail(request, pk):
    """View transaction details"""
    from eduweb.models import Transaction
    
    transaction = get_object_or_404(
        Transaction.objects.select_related('user', 'gateway'),
        pk=pk
    )
    
    return render(request, 'management/transaction_detail.html', {
        'transaction': transaction
    })


# ===========================================================================
# REQUIRED PAYMENTS MANAGEMENT
# ===========================================================================

@login_required
@user_passes_test(is_admin)
def required_payments_list(request):
    """List required payments"""
    from eduweb.models import AllRequiredPayments
    
    qs = AllRequiredPayments.objects.select_related(
        'program', 'course', 'academic_session'
    ).order_by('-due_date')
    
    search = request.GET.get('search', '').strip()
    if search:
        qs = qs.filter(
            Q(purpose__icontains=search) |
            Q(program__name__icontains=search)
        )
    
    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)
    
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    return render(request, 'management/required_payments_list.html', {
        'payments': page_obj
    })


@login_required
@user_passes_test(is_admin)
def required_payment_create(request):
    """Create required payment"""
    from .forms import AllRequiredPaymentsForm
    
    if request.method == 'POST':
        form = AllRequiredPaymentsForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Payment created.')
            return redirect('management:required_payments_list')
    else:
        form = AllRequiredPaymentsForm()
    
    return render(request, 'management/required_payment_form.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def required_payment_edit(request, pk):
    """Edit required payment"""
    from eduweb.models import AllRequiredPayments
    from .forms import AllRequiredPaymentsForm
    
    payment = get_object_or_404(AllRequiredPayments, pk=pk)
    if request.method == 'POST':
        form = AllRequiredPaymentsForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Payment updated.')
            return redirect('management:required_payments_list')
    else:
        form = AllRequiredPaymentsForm(instance=payment)
    
    return render(request, 'management/required_payment_form.html', {
        'form': form,
        'payment': payment
    })


@login_required
@user_passes_test(is_admin)
def required_payment_delete(request, pk):
    """Delete required payment"""
    from eduweb.models import AllRequiredPayments
    
    payment = get_object_or_404(AllRequiredPayments, pk=pk)
    if request.method == 'POST':
        payment.delete()
        messages.success(request, 'Payment deleted.')
    return redirect('management:required_payments_list')