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
from django.core.mail import EmailMultiAlternatives
from django.conf import settings


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
    
    return render(request, 'management/applications.html', context)


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def application_detail(request, pk):
    """View detailed information about a specific application"""
    
    application = get_object_or_404(
        CourseApplication.objects.prefetch_related('files'),
        pk=pk
    )
    
    # Mark as under review when admin opens it (only if status is 'submitted')
    if application.status == 'submitted':
        application.status = 'under_review'
        application.save()
    
    # Get pending count for sidebar
    pending_count = CourseApplication.objects.filter(status='submitted').count()
    
    context = {
        'application': application,
        'pending_count': pending_count,
    }
    
    return render(request, 'management/application_detail.html', context)


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def mark_reviewed(request, pk):
    """Mark an application as reviewed (completed review)"""
    
    if request.method == 'POST':
        application = get_object_or_404(CourseApplication, pk=pk)
        
        # Update status to reviewed
        application.status = 'reviewed'
        application.is_reviewed = True  # For backwards compatibility
        application.reviewed_by = request.user
        application.reviewed_at = timezone.now()
        application.save()
        
        messages.success(
            request, 
            f'Application {application.application_id} has been marked as reviewed and is now awaiting decision.'
        )
        
        return redirect('management:application_detail', pk=pk)
    
    return redirect('management:applications_list')


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def make_decision(request, pk):
    """Make admission decision on an application"""
    
    if request.method == 'POST':
        application = get_object_or_404(CourseApplication, pk=pk)
        decision = request.POST.get('decision')
        decision_notes = request.POST.get('decision_notes', '')
        
        if decision not in ['accepted', 'rejected', 'waitlisted']:
            messages.error(request, 'Invalid decision type.')
            return redirect('management:application_detail', pk=pk)
        
        # Update application
        application.decision = decision
        application.decision_notes = decision_notes
        application.status = 'decision_made'
        application.decision_date = timezone.now()
        application.save()
        
        # Send decision email
        send_decision_email(application)
        
        messages.success(
            request, 
            f'Decision "{decision.capitalize()}" has been recorded and email sent to applicant.'
        )
        
        return redirect('management:application_detail', pk=pk)
    
    return redirect('management:applications_list')


def send_decision_email(application):
    """Send admission decision email to applicant"""
    try:
        decision = application.decision
        
        if decision == 'accepted':
            subject = f'Congratulations! Admission Offer - {application.application_id}'
            decision_text = 'Congratulations! We are pleased to offer you admission to'
            color = '#10b981'  # green
            icon = '🎉'
        elif decision == 'waitlisted':
            subject = f'Application Update - Waitlisted - {application.application_id}'
            decision_text = 'Your application has been placed on our waitlist for'
            color = '#f59e0b'  # orange
            icon = '⏳'
        else:  # rejected
            subject = f'Application Decision - {application.application_id}'
            decision_text = 'Thank you for your interest in'
            color = '#ef4444'  # red
            icon = '📧'
        
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
                            <p style="font-size: 16px;"><strong>{decision_text} {application.get_program_display_name()}</strong></p>
                            <p><strong>Application ID:</strong> {application.application_id}</p>
                            <p><strong>Decision Date:</strong> {application.decision_date.strftime('%B %d, %Y')}</p>
                        </div>
        """
        
        if decision == 'accepted':
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
        elif decision == 'waitlisted':
            html_content += f"""
                        <p>We received a large number of qualified applications this year. Your application was impressive, and you have been placed on our waitlist.</p>
                        <p>We will notify you if a space becomes available. No further action is required at this time.</p>
            """
        else:
            html_content += f"""
                        <p>After careful review of your application, we regret to inform you that we are unable to offer you admission at this time.</p>
                        <p>We encourage you to apply again in the future. We wish you the best in your academic pursuits.</p>
            """
        
        if application.decision_notes:
            html_content += f"""
                        <div style="background-color: #f9f9f9; padding: 15px; margin-top: 20px; border-radius: 5px;">
                            <p style="margin: 0;"><strong>Additional Notes:</strong></p>
                            <p style="margin: 10px 0 0 0;">{application.decision_notes}</p>
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
    pending_count = CourseApplication.objects.filter(is_reviewed=False).count()
    
    context = {
        'faculties': faculties,
        'pending_count': pending_count,
    }
    
    return render(request, 'management/faculties_list.html', context)


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
    
    pending_count = CourseApplication.objects.filter(is_reviewed=False).count()
    
    context = {
        'form': form,
        'pending_count': pending_count,
        'action': 'Create',
    }
    
    return render(request, 'management/faculty_form.html', context)


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
    
    pending_count = CourseApplication.objects.filter(is_reviewed=False).count()
    
    context = {
        'form': form,
        'faculty': faculty,
        'pending_count': pending_count,
        'action': 'Edit',
    }
    
    return render(request, 'management/faculty_form.html', context)


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


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def courses_list(request):
    """List all courses"""
    courses = Course.objects.select_related('faculty').all().order_by('faculty', 'display_order', 'name')
    pending_count = CourseApplication.objects.filter(is_reviewed=False).count()
    
    context = {
        'courses': courses,
        'pending_count': pending_count,
    }
    
    return render(request, 'management/courses_list.html', context)


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def course_create(request):
    """Create a new course"""
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save()
            messages.success(request, f'Course "{course.name}" created successfully!')
            return redirect('management:courses_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CourseForm()
    
    pending_count = CourseApplication.objects.filter(is_reviewed=False).count()
    
    context = {
        'form': form,
        'pending_count': pending_count,
        'action': 'Create',
    }
    
    return render(request, 'management/course_form.html', context)


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
            return redirect('management:courses_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CourseForm(instance=course)
    
    pending_count = CourseApplication.objects.filter(is_reviewed=False).count()
    
    context = {
        'form': form,
        'course': course,
        'pending_count': pending_count,
        'action': 'Edit',
    }
    
    return render(request, 'management/course_form.html', context)


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def course_delete(request, pk):
    """Delete a course"""
    course = get_object_or_404(Course, pk=pk)
    
    if request.method == 'POST':
        course_name = course.name
        course.delete()
        messages.success(request, f'Course "{course_name}" deleted successfully!')
        return redirect('management:courses_list')
    
    return redirect('management:courses_list')

from eduweb.models import BlogPost, BlogCategory
from management.forms import BlogPostForm, BlogCategoryForm

# Add these views to management/views.py


@login_required(login_url='eduweb:auth_page')
@user_passes_test(is_admin)
def blog_posts_list(request):
    """List all blog posts"""
    posts = BlogPost.objects.select_related('category', 'author').all().order_by('-publish_date')
    pending_count = CourseApplication.objects.filter(is_reviewed=False).count()
    
    # Filter by status if provided
    status_filter = request.GET.get('status', '')
    if status_filter:
        posts = posts.filter(status=status_filter)
    
    context = {
        'posts': posts,
        'pending_count': pending_count,
    }
    
    return render(request, 'management/blog_posts_list.html', context)


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
    
    pending_count = CourseApplication.objects.filter(is_reviewed=False).count()
    
    context = {
        'form': form,
        'pending_count': pending_count,
        'action': 'Create',
    }
    
    return render(request, 'management/blog_post_form.html', context)


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
    
    pending_count = CourseApplication.objects.filter(is_reviewed=False).count()
    
    context = {
        'form': form,
        'post': post,
        'pending_count': pending_count,
        'action': 'Edit',
    }
    
    return render(request, 'management/blog_post_form.html', context)


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
    pending_count = CourseApplication.objects.filter(is_reviewed=False).count()
    
    context = {
        'categories': categories,
        'pending_count': pending_count,
    }
    
    return render(request, 'management/blog_categories_list.html', context)


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
    
    pending_count = CourseApplication.objects.filter(is_reviewed=False).count()
    
    context = {
        'form': form,
        'pending_count': pending_count,
        'action': 'Create',
    }
    
    return render(request, 'management/blog_category_form.html', context)


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
    
    pending_count = CourseApplication.objects.filter(is_reviewed=False).count()
    
    context = {
        'form': form,
        'category': category,
        'pending_count': pending_count,
        'action': 'Edit',
    }
    
    return render(request, 'management/blog_category_form.html', context)


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