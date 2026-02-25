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
    LMSCourse
)

# Form imports
from management.forms import (
    FacultyForm, 
    CourseForm, 
    BlogPostForm, 
    BlogCategoryForm,
    BroadcastMessageForm
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
    
    program_distribution = CourseApplication.objects.values('program__name', 'course__faculty__name').annotate(
        count=Count('id')
    ).order_by('-count')[:10]  # Top 10 courses

    program_labels = [f"{item['course__name']} ({item['course__faculty__name']})" 
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
        applications = applications.filter(course__id=program_filter)
    
    # Pagination
    paginator = Paginator(applications, 15)  # 15 applications per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get pending count for sidebar
    pending_count = CourseApplication.objects.filter(status__in=['payment_complete', 'documents_uploaded', 'under_review']).count()
    
    from eduweb.models import Course

    context = {
        'applications': page_obj,
        'programs': [
            (str(c.id), f"{c.name} ({c.faculty.name})")
            for c in Course.objects.filter(is_active=True).select_related('faculty')
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
    
    # Mark as under review when admin opens it (only if status is 'submitted')
    if application.status == 'documents_uploaded':
        CourseApplication.objects.filter(pk=pk).update(status='under_review')
        application.status = 'under_review'
    
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
    
    # Get all courses with related data
    courses = Course.objects.select_related('faculty').order_by('display_order', 'name')
    
    # Get all categories with course counts
    categories = CourseCategory.objects.annotate(
        course_count=Count('lms_courses')
    ).order_by('display_order', 'name')
    
    context = {
        'courses': courses,
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
        if course_count > 0:
            messages.error(
                request, 
                f'Cannot delete category "{category.name}" because it has {course_count} course(s). '
                'Please reassign or delete those courses first.'
            )
            return redirect('management:course_categories_list')
        
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
                course__faculty_id__in=faculty_ids
            ).values_list('email', flat=True)
        )
    
    elif filter_type == 'course':
        # Users who applied to selected courses
        course_ids = filter_values.get('courses', [])
        emails = set(
            CourseApplication.objects.filter(
                course_id__in=course_ids
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