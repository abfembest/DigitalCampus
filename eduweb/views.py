from email.mime import application
from urllib import request
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives, send_mail
from django.conf import settings

import payment

import payment
from .forms import ContactForm, CourseApplicationForm
from eduweb.models import ContactMessage, CourseApplication, CourseIntake, Vendor
from eduweb.models import Faculty, Course, Program, Department, BlogPost, BlogCategory
from django.http import JsonResponse, HttpResponse, Http404
from django.utils import timezone
from .decorators import check_for_auth, smart_redirect_applicant
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
from .forms import SignUpForm, LoginForm
from .models import UserProfile
import random
from django.db import transaction, IntegrityError
import json
from datetime import datetime
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_protect
from .models import (
    ContactMessage, CourseApplication, Vendor, 
    UserProfile, Course, CourseIntake, Faculty,
    ApplicationDocument, ApplicationPayment,
    Program, Department
)
from django.db.models import Prefetch
from django.db.models import Q
from django.shortcuts import get_object_or_404
from .decorators import applicant_required
from .emailservices import *



def basefile(request):
    return render(request, 'base.html')



def get_application_secure(application_id, user):
    """
    Securely retrieve application with triple validation.
    
    Security Layers:
    1. Application ID match
    2. Email match (constant user attribute)
    3. User authentication (handled by @login_required)
    
    Args:
        application_id (str): The application identifier (e.g., APP-C344D4731E41)
        user (User): The authenticated user object
        
    Returns:
        CourseApplication object or None if validation fails
        
    Example:
        application = get_application_secure(application_id, request.user)
        if not application:
            messages.error(request, 'Access denied')
            return redirect('eduweb:application_status')
    """
    try:
        # Triple validation security check
        application = CourseApplication.objects.get(
            application_id=application_id,  # Layer 1: ID match
            email=user.email,                # Layer 2: Email match (constant)
            user=user                         # Layer 3: User FK match (constant)
        )
        return application
    except CourseApplication.DoesNotExist:
        # Log unauthorized access attempt (optional)
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            f"Unauthorized access attempt - User: {user.email}, "
            f"Application ID: {application_id}"
        )
        return None
    except Exception as e:
        # Log unexpected errors
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in get_application_secure: {str(e)}")
        return None
    
def application_status_context(request):
    """Add application status to all template contexts"""
    has_pending_application = False
    if request.user.is_authenticated:
        has_pending_application = CourseApplication.objects.filter(
            user=request.user,
            status__in=['draft', 'pending_payment', 'payment_complete', 'documents_uploaded', 'under_review']
        ).exists()
    return {'has_pending_application': has_pending_application}

# After successful login, check admission status
def redirect_after_login(user):
    """Determine redirect URL based on user status"""
    
    # Check if user is admin/staff
    if user.is_staff or user.is_superuser:
        return redirect('management:dashboard')
    
    # Check if user has accepted admission
    accepted_application = CourseApplication.objects.filter(
        user=user,
        status='approved',
        admission_accepted=True,
        admission_number__isnull=False,
        department_approved=True
    ).first()
    
    if accepted_application:
        # Student has completed admission - go to student dashboard
        return redirect('student:dashboard')
    
    # Check if user has pending applications
    has_application = CourseApplication.objects.filter(
        user=user
    ).exists()
    
    if has_application:
        # User has application - go to application status
        return redirect('eduweb:application_status')
    
    # Default redirect
    return redirect('eduweb:index')

def generate_captcha():
    """Generate a simple math captcha"""
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)
    operations = ['+', '-', '*']
    operation = random.choice(operations)
    
    if operation == '+':
        answer = num1 + num2
    elif operation == '-':
        answer = num1 - num2
    else:  # multiplication
        answer = num1 * num2
    
    question = f"{num1} {operation} {num2}"
    return question, answer


def verify_email(request, token):
    """Verify user email with token"""
    try:
        profile = UserProfile.objects.get(verification_token=token)
        user = profile.user
        
        if not user.is_active:
            user.is_active = True
            user.save()
            profile.email_verified = True
            profile.save()
            
            messages.success(request, 'Your email has been verified! You can now log in.')
            # Send welcome email after successful verification
            send_verification_success_email(user)
        else:
            messages.info(request, 'Your email is already verified.')
        
        return redirect('eduweb:auth_page')
        
    except UserProfile.DoesNotExist:
        messages.error(request, 'Invalid verification link.')
        return redirect('eduweb:auth_page')

def auth_page(request):
    """Combined authentication page for login and signup"""

    # Check authenticated user with proper status
    if request.user.is_authenticated:
        # Check account status
        if not request.user.is_active:
            logout(request)
            messages.warning(
                request, 
                'Your account is inactive. Please verify your email.'
            )
            # Don't redirect, show the auth page
        elif not request.user.profile.email_verified:
            logout(request)
            messages.warning(
                request,
                'Please verify your email to continue. '
                'Check your inbox for the verification link.'
            )
            # Don't redirect, show the auth page
        else:
            # User is authenticated and verified
            messages.info(request, 'You are already logged in.')
            role = request.user.profile.role
            
            if role == 'admin' or request.user.is_superuser:
                return redirect('management:dashboard')
            elif role == 'instructor':
                return redirect('instructor:dashboard')
            elif role == 'student':
                return redirect('eduweb:apply')
            elif role == 'finance':
                return redirect('finance:dashboard')
            else:
                return redirect('eduweb:apply')
    
    # Generate captcha
    if request.method == 'GET':
        captcha_question, captcha_answer = generate_captcha()
        request.session['captcha_answer'] = captcha_answer
    else:
        captcha_answer = request.session.get('captcha_answer')
        if captcha_answer is None:
            captcha_question, captcha_answer = generate_captcha()
            request.session['captcha_answer'] = captcha_answer
            return JsonResponse({
                'success': False,
                'errors': {
                    'captcha': ['Session expired. Please try again.']
                },
                'captcha_question': captcha_question
            }, status=400)
        else:
            captcha_question = None
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'signup':
            session_captcha = request.session.get('captcha_answer')
            
            signup_form = SignUpForm(
                request.POST, 
                captcha_answer=session_captcha
            )
            
            if signup_form.is_valid():
                if 'captcha_answer' in request.session:
                    del request.session['captcha_answer']
                    
                user = signup_form.save(commit=False)
                user.is_active = False
                user.save()
                
                send_verification_email(request, user)
                
                return JsonResponse({
                    'success': True,
                    'message': (
                        'Account created! Check your email '
                        'to verify your account before logging in.'
                    ),
                    'email': user.email
                })
            else:
                errors = {}
                for field, error_list in signup_form.errors.items():
                    errors[field] = [str(e) for e in error_list]
                
                new_question, new_answer = generate_captcha()
                request.session['captcha_answer'] = new_answer
                
                return JsonResponse({
                    'success': False,
                    'errors': errors,
                    'captcha_question': new_question
                }, status=400)
        
        elif action == 'login':
            username_or_email = request.POST.get('username', '').strip()
            password = request.POST.get('password', '')
            captcha = request.POST.get('captcha', '').strip()
            
            # Validate inputs
            if not username_or_email or not password:
                new_question, new_answer = generate_captcha()
                request.session['captcha_answer'] = new_answer
                return JsonResponse({
                    'success': False,
                    'errors': {
                        'username': ['Username/email and password required.']
                    },
                    'captcha_question': new_question
                }, status=400)
            
            # Verify captcha
            session_answer = request.session.get('captcha_answer')
            
            try:
                captcha_int = int(captcha) if captcha else None
                session_answer_int = (
                    int(session_answer) 
                    if session_answer is not None 
                    else None
                )
                
                if (session_answer_int is None or 
                    captcha_int != session_answer_int):
                    new_question, new_answer = generate_captcha()
                    request.session['captcha_answer'] = new_answer
                    return JsonResponse({
                        'success': False,
                        'errors': {
                            'captcha': ['Incorrect answer. Try again.']
                        },
                        'captcha_question': new_question
                    }, status=400)
            except (ValueError, TypeError):
                new_question, new_answer = generate_captcha()
                request.session['captcha_answer'] = new_answer
                return JsonResponse({
                    'success': False,
                    'errors': {
                        'captcha': ['Invalid answer. Enter a number.']
                    },
                    'captcha_question': new_question
                }, status=400)
            
            # Check if input is email
            if '@' in username_or_email:
                try:
                    user_obj = User.objects.get(
                        email=username_or_email
                    )
                    username_or_email = user_obj.username
                except User.DoesNotExist:
                    pass
            
            user = authenticate(
                request, 
                username=username_or_email, 
                password=password
            )
            
            if user is not None:
                # Check if account is active
                if not user.is_active:
                    new_question, new_answer = generate_captcha()
                    request.session['captcha_answer'] = new_answer
                    return JsonResponse({
                        'success': False,
                        'errors': {
                            'username': [
                                'Account inactive. '
                                'Please verify your email first.'
                            ]
                        },
                        'captcha_question': new_question
                    }, status=400)
                
                # Check if email is verified
                if not user.profile.email_verified:
                    new_question, new_answer = generate_captcha()
                    request.session['captcha_answer'] = new_answer
                    return JsonResponse({
                        'success': False,
                        'errors': {
                            'username': [
                                'Email not verified. '
                                'Check your inbox for verification link.'
                            ]
                        },
                        'captcha_question': new_question
                    }, status=400)
                
                # Login successful
                login(request, user)
                
                if 'captcha_answer' in request.session:
                    del request.session['captcha_answer']
                
                role = user.profile.role
                redirect_url = 'eduweb:apply'
                
                if role == 'admin' or user.is_superuser:
                    redirect_url = 'management:dashboard'
                elif role == 'instructor':
                    redirect_url = 'instructor:dashboard'
                elif role == 'student':
                    redirect_url = 'eduweb:apply'
                elif role == 'finance':
                    redirect_url = 'finance:dashboard'
                
                return JsonResponse({
                    'success': True,
                    'message': 'Login successful!',
                    'redirect_url': reverse(redirect_url)
                })
            else:
                new_question, new_answer = generate_captcha()
                request.session['captcha_answer'] = new_answer
                return JsonResponse({
                    'success': False,
                    'errors': {
                        'username': [
                            'Invalid username/email or password.'
                        ]
                    },
                    'captcha_question': new_question
                }, status=400)
    
    # GET request - render the auth page
    signup_form = SignUpForm()
    login_form = LoginForm()
    
    context = {
        'signup_form': signup_form,
        'login_form': login_form,
        'captcha_question': captcha_question,
    }
    
    return render(request, 'auth/auth.html', context)

def user_logout(request):
    """Logout user"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('eduweb:auth_page')


@login_required
def resend_verification(request):
    """Resend verification email"""
    if request.method == 'POST':
        user = request.user
        if not user.profile.email_verified:
            user.profile.generate_verification_token()
            send_verification_email(request, user)
            return JsonResponse({
                'success': True,
                'message': 'Verification email has been resent. Please check your inbox.'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Your email is already verified.'
            })
    return JsonResponse({'success': False, 'message': 'Invalid request.'}, status=400)

@check_for_auth
def index(request):
    from .models import Program, Faculty
    featured_programs = Program.objects.filter(
        is_active=True, is_featured=True
    ).select_related('department__faculty').order_by('display_order', 'name')[:6]
    faculties = Faculty.objects.filter(is_active=True).order_by('display_order', 'name')[:6]
    return render(request, 'index.html', {
        'featured_programs': featured_programs,
        'faculties': faculties,
    })

@check_for_auth
def about(request):
    from .models import Faculty
    faculties = Faculty.objects.filter(is_active=True).prefetch_related('departments').order_by('display_order', 'name')
    return render(request, 'about.html', {'faculties': faculties})

def all_programs(request):
    from .models import Faculty, Department, Program
    from django.db.models import Prefetch
    faculties = Faculty.objects.filter(is_active=True).prefetch_related(
        Prefetch(
            'departments',
            queryset=Department.objects.filter(is_active=True).prefetch_related(
                Prefetch(
                    'programs',
                    queryset=Program.objects.filter(is_active=True).order_by('display_order', 'name')
                )
            ).order_by('display_order', 'name')
        )
    ).order_by('display_order', 'name')
    return render(request, 'all_programs.html', {'faculties': faculties})


@login_required
@smart_redirect_applicant
def apply(request):
    # Check if email is verified
    if request.user.profile.email_verified is False:
        messages.warning(request, 'Please verify your email before applying.')
        return redirect('eduweb:auth_page')

    # Check if user already has a pending application
    existing_application = CourseApplication.objects.filter(
        user=request.user,
        status__in=['draft', 'pending_payment', 'payment_complete', 'documents_uploaded', 'under_review']
    ).first()

    if existing_application:
        messages.info(request, 'You already have an application in progress.')
        return redirect('eduweb:application_status')

    # -------------------------------
    # FETCH COURSES (UPDATED)
    # -------------------------------
    from .models import Program, Faculty, CourseIntake

    programs = Program.objects.filter(
        is_active=True
    ).select_related('department__faculty')
    faculties = Faculty.objects.filter(is_active=True)

    # Group programs by faculty
    courses_by_faculty = {}
    for program in programs:
        faculty_name = program.department.faculty.name
        if faculty_name not in courses_by_faculty:
            courses_by_faculty[faculty_name] = []

        # Get active intakes for this program
        intakes = CourseIntake.objects.filter(
            program=program,
            is_active=True,
            application_deadline__gte=timezone.now().date()
        ).values('id', 'intake_period', 'year', 'start_date')

        courses_by_faculty[faculty_name].append({
            "id": program.id,
            "name": program.name,
            "code": program.code,
            "degree_level": program.degree_level,
            "available_study_modes": program.available_study_modes,
            "application_fee": str(program.application_fee),
            "tuition_fee": str(program.tuition_fee),
            "intakes": list(intakes)
        })

    courses_json = json.dumps(courses_by_faculty, cls=DjangoJSONEncoder)

    # -------------------------------
    # POST LOGIC (UNCHANGED)
    # -------------------------------
    if request.method == 'POST':
        form = CourseApplicationForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                # Collect academic history
                academic_history = []
                entry_count = 1
                while True:
                    education_level = request.POST.get(f'education_level_{entry_count}')
                    if not education_level:
                        break

                    academic_history.append({
                        'education_level': education_level,
                        'institution': request.POST.get(f'institution_{entry_count}', ''),
                        'field_of_study': request.POST.get(f'field_of_study_{entry_count}', ''),
                        'graduation_year': request.POST.get(f'graduation_year_{entry_count}', ''),
                        'gpa': request.POST.get(f'gpa_{entry_count}', ''),
                    })
                    entry_count += 1

                application = form.save(commit=False, user=request.user)
                application.academic_history = academic_history
                application.save()

                documents = {}
                from .models import ApplicationDocument

                file_field_mapping = {
                    'transcript_file': 'transcript',
                    'certificate_file': 'certificate',
                    'english_test_file': 'english_test',
                    'id_document_file': 'id_document',
                    'cv_file': 'cv',
                    'recommendation_file': 'recommendation'
                }

                for form_field, file_type in file_field_mapping.items():
                    if form_field in request.FILES:
                        file_obj = request.FILES[form_field]
                        ApplicationDocument.objects.create(
                            application=application,
                            file=file_obj,
                            file_type=file_type,
                            original_filename=file_obj.name,
                            file_size=file_obj.size
                        )

                from threading import Thread

                def send_emails_async():
                    send_application_confirmation_email(application)
                    send_application_admin_notification(application)

                Thread(target=send_emails_async, daemon=True).start()

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'application_id': application.application_id,
                        'redirect_url': reverse('eduweb:application_status')
                    })

                messages.success(
                    request,
                    f'Application submitted successfully! Your ID: {application.application_id}'
                )
                return redirect('eduweb:application_status')

            except Exception as e:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse(
                        {'success': False, 'error': str(e)},
                        status=500
                    )
                messages.error(request, str(e))

        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse(
                    {'success': False, 'errors': form.errors},
                    status=400
                )
            messages.error(request, 'Please correct the errors in the form.')

    # -------------------------------
    # GET LOGIC (UNCHANGED)
    # -------------------------------
    if request.user.is_authenticated:
        form = CourseApplicationForm(initial={'email': request.user.email})
    else:
        form = CourseApplicationForm()

    return render(request, 'form.html', {
        'form': form,
        'courses': programs,
        'courses_json': courses_json,
    })

@check_for_auth
def detail(request):
    return render(request, 'detail.html')

@check_for_auth
def admission_course(request):
    return render(request, 'course.html')

@check_for_auth
def admission_requirement(request):
    return render(request, 'admission_requirement.html')

@check_for_auth
def blank_page(request):
    return render(request, 'blank_page.html')

@check_for_auth
def contact_submit(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact_message = form.save()
            
            # Send emails
            admin_email_sent = send_admin_email(contact_message)
            user_email_sent = send_user_confirmation_email(contact_message)
            
            # Show appropriate message
            if admin_email_sent and user_email_sent:
                messages.success(request, 'Thank you for contacting us! We will get back to you soon. A confirmation email has been sent to your inbox.')
            elif admin_email_sent or user_email_sent:
                messages.success(request, 'Thank you for contacting us! We will get back to you soon.')
            else:
                messages.success(request, 'Thank you for contacting us! We have received your message and will get back to you soon.')
            
            return redirect('index')
        else:
            messages.error(request, 'Please correct the errors below.')
            return render(request, 'index.html', {'form': form})
    else:
        return redirect('index')

# Additional Pages
@check_for_auth
def research(request):
    """Research page view"""
    return render(request, 'research.html')

@check_for_auth
def campus_life(request):
    """Campus Life page view"""
    return render(request, 'campus_life.html')


from django.core.paginator import Paginator
from eduweb.models import BlogPost, BlogCategory

@check_for_auth
def blog(request):
    """Blog listing page with filtering and pagination"""
    # Get all published posts
    posts = BlogPost.objects.filter(status='published').select_related('category', 'author')
    
    # Get category filter
    category_slug = request.GET.get('category', '')
    if category_slug:
        posts = posts.filter(category__slug=category_slug)
    
    # Get search query
    search_query = request.GET.get('search', '')
    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query) | 
            Q(excerpt__icontains=search_query) |
            Q(content__icontains=search_query)
        )
    
    # Order by publish date
    posts = posts.order_by('-publish_date')
    
    # Get featured post (most recent featured post)
    featured_post = BlogPost.objects.filter(
        status='published', 
        is_featured=True
    ).order_by('-publish_date').first()
    
    # Pagination (9 posts per page)
    paginator = Paginator(posts, 9)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get all active categories for filter
    categories = BlogCategory.objects.filter(is_active=True).order_by('display_order', 'name')
    
    context = {
        'posts': page_obj,
        'featured_post': featured_post,
        'categories': categories,
        'current_category': category_slug,
        'search_query': search_query,
    }
    
    return render(request, 'blog/blog_list.html', context)


@check_for_auth
def blog_detail(request, slug):
    """Individual blog post detail page"""
    post = get_object_or_404(
        BlogPost.objects.select_related('category', 'author'),
        slug=slug,
        status='published'
    )
    
    # Increment view count
    post.increment_views()
    
    # Get related posts
    related_posts = post.get_related_posts(limit=3)
    
    # Get all categories for sidebar
    categories = BlogCategory.objects.filter(is_active=True).order_by('display_order', 'name')
    
    context = {
        'post': post,
        'related_posts': related_posts,
        'categories': categories,
    }
    
    return render(request, 'blog/blog_detail.html', context)


@check_for_auth
def blog_category(request, slug):
    """Blog posts filtered by category"""
    category = get_object_or_404(BlogCategory, slug=slug, is_active=True)
    
    posts = BlogPost.objects.filter(
        status='published',
        category=category
    ).select_related('author').order_by('-publish_date')
    
    # Pagination
    paginator = Paginator(posts, 9)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get all categories for filter
    categories = BlogCategory.objects.filter(is_active=True).order_by('display_order', 'name')
    
    context = {
        'posts': page_obj,
        'categories': categories,
        'current_category': category,
    }
    
    return render(request, 'blog/blog_category.html', context)

@smart_redirect_applicant
@login_required(login_url='eduweb:auth_page')
def application_status(request):
    """
    Display application status page with progress tracking.
    Shows the most recent application for the logged-in user.
    """
    try:
        # Get user's most recent application
        application = CourseApplication.objects.filter(
            email=request.user.email
        ).order_by('-created_at').first()
        
    except CourseApplication.DoesNotExist:
        application = None
    
    context = {
        'application': application,
    }
    
    return render(request, 'applications/application_status.html', context)


@login_required(login_url='eduweb:auth_page')
def admission_letter(request, application_id):
    """
    Display admission letter for approved applications.
    Accessible by both applicants and admin staff.
    """
    application = get_object_or_404(
        CourseApplication, 
        application_id=application_id
    )
    
    # Check permissions
    user = request.user
    is_owner = (
        application.user == user or 
        application.email == user.email
    )
    is_admin = user.is_staff or user.is_superuser
    
    # Only owner or admin can view
    if not (is_owner or is_admin):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden(
            "You don't have permission to view this letter."
        )
    
    # Only show letter for approved applications
    if application.status != 'approved':
        from django.contrib import messages
        from django.shortcuts import redirect
        
        messages.warning(
            request, 
            'Admission letter is only available for approved applications.'
        )
        
        if is_admin:
            return redirect(
                'management:application_detail', 
                application.application_id
            )
        else:
            return redirect('eduweb:application_status')
    
    context = {
        'application': application,
    }
    
    return render(
        request, 
        'applications/admission_letter.html', 
        context
    )
@login_required
def payments(request):
    """payments page"""
    return render(request, 'payments.html')



####### PAYMENT GATEWAY ###########

from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
import stripe
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


@require_GET
@login_required
def get_payment_summary(request, application_id):
    """
    Returns payment summary for an application.
    ALWAYS returns JSON.
    """

    try:
        application_id = application_id.strip()

        application = CourseApplication.objects.select_related(
            "program", "program__department__faculty"
        ).get(application_id__iexact=application_id)

        if application.user != request.user and not request.user.is_staff:
            return JsonResponse(
                {"success": False, "error": "Permission denied"},
                status=403
            )

        summary = {
            "application_id": application.application_id,
            "full_name": application.get_full_name(),
            "email": application.email,
            "course_name": application.program.name,
            "faculty": application.program.department.faculty.name,
            "amount": float(application.program.application_fee),
            "currency": "GBP",
            "description": "Application Processing Fee",
            "stripe_public_key": settings.STRIPE_PUBLIC_KEY,
        }

        return JsonResponse({"success": True, "data": summary})

    except CourseApplication.DoesNotExist:
        return JsonResponse(
            {"success": False, "error": "Application not found"},
            status=404
        )

    except Exception as e:
        logger.exception("get_payment_summary failed")
        return JsonResponse(
            {"success": False, "error": "Unable to load payment summary"},
            status=500
        )


@require_POST
@login_required
def create_payment_intent(request):

    try:
        payload = request.body.decode("utf-8")
        if not payload:
            return JsonResponse({"success": False, "error": "Empty request body"}, status=400)

        data = json.loads(payload)

        application_id = data.get("application_id")
        if not application_id:
            return JsonResponse({"success": False, "error": "Missing application_id"}, status=400)

        application_id = application_id.strip()

        application = get_object_or_404(
            CourseApplication,
            application_id__iexact=application_id,
            user=request.user
        )
        
        if application.is_paid:
            return JsonResponse({"success": False, "error": "Application already paid"}, status=400)

        amount_decimal = application.program.application_fee
        amount_pence = int(amount_decimal * Decimal("100"))

        with transaction.atomic():

            existing_payment = ApplicationPayment.objects.filter(
                application=application,
                status="pending"
            ).select_for_update().first()

            if existing_payment:
                intent = stripe.PaymentIntent.retrieve(existing_payment.gateway_payment_id)

                return JsonResponse({
                    "success": True,
                    "clientSecret": intent.client_secret
                })

            intent = stripe.PaymentIntent.create(
                amount=amount_pence,
                currency="gbp",
                metadata={
                    "application_id": application.application_id,
                    "user_id": request.user.id,
                },
                automatic_payment_methods={"enabled": True},
            )

            ApplicationPayment.objects.create(
                application=application,
                gateway_payment_id=intent.id,
                amount=amount_decimal,
                currency="GBP",
                status="pending",
            )

        return JsonResponse({
            "success": True,
            "clientSecret": intent.client_secret
        })

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    except stripe.error.StripeError as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)

    except Exception as e:
        logger.exception("create_payment_intent crash")
        return JsonResponse({"success": False, "error": "Unable to create payment"}, status=500)




@require_POST
@login_required
def confirm_payment(request):
    """
    Confirms a payment after Stripe confirmation.
    ALWAYS returns JSON.
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    payment_intent_id = data.get("payment_intent_id")
    if not payment_intent_id:
        return JsonResponse({"success": False, "error": "Missing payment_intent_id"}, status=400)

    try:
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
    except stripe.error.StripeError as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)

    if intent.status != "succeeded":
        return JsonResponse({"success": False, "error": "Payment not successful"}, status=400)

    # Check if payment record already exists
    payment = ApplicationPayment.objects.filter(gateway_payment_id=intent.id).first()
    if payment:
        # Ensure paid_at is always set even if webhook created the record first
        if not payment.paid_at:
            payment.paid_at = timezone.now()
            payment.save(update_fields=['paid_at'])
        # Ensure application status is synced
        application_id = intent.metadata.get("application_id")
        if application_id:
            try:
                app = CourseApplication.objects.get(application_id=application_id, user=request.user)
                if app.status in ['draft', 'pending_payment']:
                    app.status = 'payment_complete'
                    app.payment_status = 'success'
                    app.save(update_fields=['status', 'payment_status'])
            except CourseApplication.DoesNotExist:
                pass
        redirect_url = reverse("eduweb:application_status")
        return JsonResponse({"success": True, "payment_id": payment.id, "redirect_url": redirect_url})

    # No payment record yet – create it from the intent metadata
    application_id = intent.metadata.get("application_id")
    if not application_id:
        return JsonResponse({"success": False, "error": "Application ID missing in payment intent"}, status=400)

    try:
        application = CourseApplication.objects.get(application_id=application_id, user=request.user)
    except CourseApplication.DoesNotExist:
        return JsonResponse({"success": False, "error": "Application not found or access denied"}, status=404)

    # Create payment record AND update CourseApplication atomically
    with transaction.atomic():
        payment, created = ApplicationPayment.objects.select_for_update().get_or_create(
            gateway_payment_id=intent.id,
            defaults={
                "application": application,
                "amount": Decimal(intent.amount) / Decimal(100),
                "currency": intent.currency.upper(),
                "status": "success",
                "paid_at": timezone.now(),
            }
        )

        # If webhook already created it, ensure status is correct
        if not created and payment.status != "success":
            payment.status = "success"
            payment.paid_at = timezone.now()
            payment.save(update_fields=["status", "paid_at"])

        # ✅ Update CourseApplication — this is the missing piece
        application.status = "payment_complete"
        application.payment_status = "success"
        application.save(update_fields=["status", "payment_status"])

    redirect_url = reverse("eduweb:application_status")
    return JsonResponse({"success": True, "payment_id": payment.id, "redirect_url": redirect_url})



@csrf_exempt
def stripe_webhook(request):

    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        print("Webhook verification failed:", str(e))
        return HttpResponse(status=400)

    if event["type"] == "payment_intent.succeeded":
        intent = event["data"]["object"]

        application_id = intent.metadata.get("application_id")
        if not application_id:
            return HttpResponse(status=200)

        try:
            application = CourseApplication.objects.get(
                application_id=application_id
            )
        except CourseApplication.DoesNotExist:
            return HttpResponse(status=200)
        with transaction.atomic():
            print('immediate atomic hook')
            payment, created = ApplicationPayment.objects.select_for_update().get_or_create(
                gateway_payment_id=intent.id,
                defaults={
                    "application": application,
                    "amount": Decimal(intent.amount) / Decimal(100),
                    "currency": intent.currency.upper(),
                    "status": "success",
                    "paid_at": timezone.now(),
                },
            )

            if not created and payment.status == "success":
                return HttpResponse(status=200)

            payment.status = "success"
            payment.paid_at = timezone.now()
            payment.save()

            # Sync CourseApplication status when webhook fires
            application.status = "payment_complete"
            application.payment_status = "success"
            application.save(update_fields=["status", "payment_status"])
    return HttpResponse(status=200)

# eduweb/views.py — add this view
@login_required
def get_student_fee_summary(request, fee_pk):
    from eduweb.models import AllRequiredPayments
    from django.conf import settings
    try:
        fee = AllRequiredPayments.objects.select_related('faculty', 'department').get(pk=fee_pk, is_active=True)
    except AllRequiredPayments.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Fee not found'}, status=404)

    return JsonResponse({
        'success': True,
        'data': {
            'full_name': request.user.get_full_name() or request.user.username,
            'purpose': fee.purpose,
            'amount': float(fee.amount),
            'currency': 'NGN',
            'stripe_public_key': settings.STRIPE_PUBLISHABLE_KEY,
        }
    })

###################### APPLICATION SUBMISSION ##############################################

@login_required
@require_POST
@csrf_protect
def save_application_draft(request):
    """
    Safely save or update a CourseApplication as a draft.
    Compatible with FormData submissions.
    """

    try:
        # -------------------------------------------------
        # 0. CHECK FOR OPEN APPLICATION
        # -------------------------------------------------
        if request.user.is_authenticated:
            open_application = CourseApplication.objects.filter(
                user=request.user,
                in_processing=True
            ).exists()

            if open_application:
                # Redirect to status page with message
                messages.info(request, "You have an open application")
                return redirect("eduweb:application_status")

        data = request.POST

        # -------------------------------------------------
        # 1. GET OR CREATE APPLICATION
        # -------------------------------------------------
        application_id = data.get("application_id")
        application = None

        if application_id:
            application = CourseApplication.objects.filter(
                application_id=application_id
            ).first()

        if not application:
            application = CourseApplication(
                user=request.user if request.user.is_authenticated else None
            )

        # -------------------------------------------------
        # 2. COURSE & INTAKE
        # -------------------------------------------------
        program_id = data.get("program")
        if program_id:
            try:
                from .models import Program
                application.program = Program.objects.get(id=program_id)
            except Program.DoesNotExist:
                pass

        intake_id = data.get("intake")
        if intake_id:
            try:
                application.intake = CourseIntake.objects.get(id=intake_id)
            except CourseIntake.DoesNotExist:
                pass

        application.study_mode = data.get("study_mode", "")

        # -------------------------------------------------
        # 3. PERSONAL INFORMATION
        # -------------------------------------------------
        application.first_name = data.get("first_name", "").strip()
        application.last_name = data.get("last_name", "").strip()
        application.email = data.get("email", "").strip()
        application.phone = data.get("phone", "").strip()
        application.gender = data.get("gender", "")
        application.nationality = data.get("nationality", "")
        application.country = data.get("country", "")

        dob = data.get("date_of_birth")
        if dob:
            try:
                application.date_of_birth = datetime.strptime(dob, "%Y-%m-%d").date()
            except ValueError:
                pass

        # -------------------------------------------------
        # 4. ADDRESS
        # -------------------------------------------------
        application.address_line1 = data.get("address_line1", "").strip()
        application.address_line2 = data.get("address_line2", "").strip()
        application.city = data.get("city", "").strip()
        application.state = data.get("state", "").strip()
        application.postal_code = data.get("postal_code", "").strip()
        application.country = data.get("country", "")

        # -------------------------------------------------
        # 5. ACADEMIC BACKGROUND
        # -------------------------------------------------
        application.highest_qualification = data.get("highest_qualification", "")
        application.institution_name = data.get("institution_name", "")
        application.graduation_year = data.get("graduation_year", "")
        application.gpa_or_grade = data.get("gpa_or_grade", "")

        # -------------------------------------------------
        # 6. LANGUAGE PROFICIENCY
        # -------------------------------------------------
        application.language_skill = data.get("language_skill", "")
        application.language_score = data.get("language_score", "")

        # -------------------------------------------------
        # 7. FULL ACADEMIC HISTORY
        # -------------------------------------------------
        academic_history = data.get("academic_history")
        if academic_history:
            try:
                application.academic_history = json.loads(academic_history)
            except json.JSONDecodeError:
                pass

        # -------------------------------------------------
        # 8. ADDITIONAL INFORMATION
        # -------------------------------------------------
        application.work_experience_years = data.get("work_experience_years") or 0
        application.personal_statement = data.get("personal_statement", "")
        application.how_did_you_hear = data.get("how_did_you_hear", "")

        # -------------------------------------------------
        # 9. PRIVACY & CONSENT
        # -------------------------------------------------
        application.accept_privacy_policy = data.get("accept_privacy_policy") in ("true", "on", "1")
        application.accept_terms_conditions = data.get("accept_terms_conditions") in ("true", "on", "1")
        application.marketing_consent = data.get("marketing_consent") in ("true", "on", "1")
        application.scholarship = data.get("scholarship") in ("true", "on", "1")

        # -------------------------------------------------
        # 10. EMERGENCY CONTACT
        # -------------------------------------------------
        application.emergency_contact_name = data.get("emergency_contact_name", "")
        application.emergency_contact_phone = data.get("emergency_contact_phone", "")
        application.emergency_contact_relationship = data.get("emergency_contact_relationship", "")

        # -------------------------------------------------
        # 11. DRAFT STATUS
        # -------------------------------------------------
        application.status = "draft"

        # -------------------------------------------------
        # 12. SAVE
        # -------------------------------------------------
        application.save()

        return redirect("eduweb:application_status")

    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=400)

@login_required
def payment_details(request, application_id):
    app = CourseApplication.objects.get(
        application_id=application_id,
        user=request.user
    )

    return JsonResponse({
        "application_id": app.application_id,
        "name": app.get_full_name(),
        "program": app.program.name if app.program else '',
        "faculty": app.program.department.faculty.name if app.program else '',
        "amount": float(app.program.application_fee) if app.program else 0,
        "payment_status": app.payment_status if hasattr(app, 'payment') else 'pending'
    })

@login_required(login_url='eduweb:auth_page')
def upload_application_file(request, application_id):
    """
    Upload document for application via AJAX.
    Validates file type, size, and application status.
    """
    if request.method != 'POST':
        return JsonResponse({
            'success': False, 
            'error': 'Invalid request method'
        })
    
    application = get_application_secure(application_id, request.user)
    
    if not application:
        return JsonResponse({
            'success': False, 
            'error': 'Application not found or access denied'
        })
    
    # Check if documents can be uploaded
    if not application.can_upload_documents():
        return JsonResponse({
            'success': False, 
            'error': 'Document upload not allowed. Please complete payment first.'
        })
    
    file_type = request.POST.get('file_type')
    file = request.FILES.get('file')
    auto_submit = request.POST.get('auto_submit') == 'true'
    
    if not file_type or not file:
        return JsonResponse({
            'success': False, 
            'error': 'Both file type and file are required'
        })
    
    # Validate file size (5MB limit)
    max_size = 5 * 1024 * 1024  # 5MB in bytes
    if file.size > max_size:
        return JsonResponse({
            'success': False, 
            'error': f'File size exceeds 5MB limit. Your file is {file.size / 1024 / 1024:.2f}MB'
        })
    
    # Validate file extension
    allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
    file_ext = file.name.lower()[-4:]
    if not any(file_ext.endswith(ext) for ext in allowed_extensions):
        return JsonResponse({
            'success': False, 
            'error': 'Invalid file type. Only PDF, JPG, and PNG files are allowed.'
        })
    
    # Create document record
    try:
        document = ApplicationDocument.objects.create(
            application=application,
            file_type=file_type,
            file=file,
            original_filename=file.name,
            file_size=file.size
        )
        
        # Update application status if this is first document
        if application.status == 'payment_complete':
            application.status = 'documents_uploaded'
            application.save(update_fields=['status'])

            # Send confirmation email to applicant
            send_document_upload_confirmation(application, document)
            # Send notification email to admin
            send_document_upload_admin_notification(application, document)
        
        # Auto-submit if requested
        if auto_submit:
            application.mark_as_submitted()
        
        return JsonResponse({
            'success': True,
            'message': 'Document uploaded successfully',
            'document_id': document.id,
            'filename': document.original_filename,
            'file_size': document.get_file_size_display()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': f'Upload failed: {str(e)}'
        })

@login_required(login_url='eduweb:auth_page')
def mark_payment_successful(request, application_id):
    """
    Mark payment as successful (for testing purposes only).
    Remove or restrict in production.
    """

    import uuid

    application = get_application_secure(application_id, request.user)
    
    if not application:
        messages.error(
            request, 
            'Application not found or you do not have permission to access it.'
        )
        return redirect('eduweb:application_status')
    
    try:        
        # Check if already paid
        if (hasattr(application, 'payment') and 
            application.payment.status == 'success'):
            messages.info(
                request, 
                'Payment already completed.'
            )
            return redirect('eduweb:application_status')
        
        # Generate test payment reference
        ref = f"TEST-{uuid.uuid4().hex[:12].upper()}"
        gateway_id = f"pi_test_{uuid.uuid4().hex[:24]}"
        
        # Create or update payment
        payment, created = ApplicationPayment.objects.get_or_create(
            application=application,
            defaults={
                'amount': application.course.application_fee,
                'currency': 'GBP',
                'status': 'success',
                'payment_method': 'stripe',
                'payment_reference': ref,
                'gateway_payment_id': gateway_id,
                'paid_at': timezone.now(),
                'card_last4': '4242',
                'card_brand': 'visa',
                'payment_metadata': {
                    'test': True,
                    'timestamp': timezone.now().isoformat()
                }
            }
        )
        
        if not created:
            payment.status = 'success'
            payment.paid_at = timezone.now()
            payment.payment_reference = ref
            payment.gateway_payment_id = gateway_id
            payment.save()
        
        # Update application status
        application.status = 'payment_complete'
        application.payment_status = 'success'
        application.save(
            update_fields=['status', 'payment_status']
        )
        
        messages.success(
            request,
            f'✅ Payment successful! Reference: {ref}'
        )
        
    except Exception as e:
        logger.error(f"Test payment error: {str(e)}")
        messages.error(
            request, 
            f'Payment failed: {str(e)}'
        )
    
    return redirect('eduweb:application_status')

from django.shortcuts import get_object_or_404
from .models import Faculty, Course, Department, Program
from django.db import models

from django.db.models import Prefetch
def faculty_detail(request, slug):
    """
    Faculty detail page.
    Hierarchy: Faculty → Departments → Programs → Courses
    Template: faculties/faculty_detail.html
    """
    faculty = get_object_or_404(Faculty, slug=slug, is_active=True)

    departments = (
        faculty.departments
        .filter(is_active=True)
        .prefetch_related(
            Prefetch(
                'programs',
                queryset=Program.objects.filter(is_active=True)
                    .prefetch_related(
                        Prefetch(
                            'courses',
                            queryset=Course.objects.filter(is_active=True)
                                .order_by('year_of_study', 'semester', 'display_order'),
                            to_attr='active_courses',
                        )
                    )
                    .order_by('display_order', 'name'),
                to_attr='active_programs',
            )
        )
        .order_by('display_order', 'name')
    )

    context = {
        'faculty':     faculty,
        'departments': departments,
    }

    return render(request, 'faculties/faculty_detail.html', context)

@check_for_auth
def program_detail(request, slug):
    """
    Program detail page.
    Shows program info, all active courses grouped by year/semester,
    and the program's intake sessions.
    Template: programs/program_detail.html
    """

    program = get_object_or_404(
        Program.objects.select_related(
            'department',
            'department__faculty',
        ),
        slug=slug,
        is_active=True,
    )

    # All active courses for this program, ordered by year then semester
    courses = (
        program.courses
        .filter(is_active=True)
        .select_related('lecturer')
        .order_by('year_of_study', 'semester', 'display_order', 'name')
    )

    # Active intake sessions for this program
    active_intakes = (
        program.intakes
        .filter(is_active=True)
        .order_by('-year', 'intake_period')
    )

    context = {
        'program':        program,
        'courses':        courses,
        'active_intakes': active_intakes,
        'department':     program.department,
        'faculty':        program.department.faculty,
    }

    return render(request, 'programs/program_detail.html', context)

@login_required(login_url='eduweb:auth_page')
def submit_application(request, application_id):
    """
    Submit application for review.
    Ensures payment and documents are complete before submission.
    """
    if request.method != 'POST':
        return redirect('eduweb:application_status')
    
    application = get_application_secure(application_id, request.user)
    
    if not application:
        messages.error(
            request, 
            'Application not found or you do not have permission to access it.'
        )
        return redirect('eduweb:application_status')
    
    # Validate payment completed
    if not application.is_paid:
        messages.error(
            request, 
            'Payment must be completed before submission. Please complete payment first.'
        )
        return redirect('eduweb:application_status')
    
    # Validate documents uploaded
    if not application.documents.exists():
        messages.error(
            request, 
            'Please upload required documents before submission.'
        )
        return redirect('eduweb:application_status')
    
    # Check application status allows submission
    if application.status not in ['payment_complete', 'documents_uploaded']:
        messages.warning(
            request, 
            f'Application cannot be submitted from status: {application.get_status_display()}'
        )
        return redirect('eduweb:application_status')
    
    # Submit application
    if application.mark_as_submitted():
        # Send notification email
        try:
            applicant_name = (
                application.get_full_name() 
                if hasattr(application, 'get_full_name') 
                else f"{application.first_name} {application.last_name}"
            )
            
            subject = 'Application Submitted Successfully - MIU'
            html_message = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #840384 0%, #6B21A8 100%); 
                               color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .info-box {{ background: #DBEAFE; padding: 15px; border-left: 4px solid #3B82F6; 
                                margin: 20px 0; border-radius: 5px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>✅ Application Submitted!</h1>
                    </div>
                    <div class="content">
                        <p>Dear {applicant_name},</p>
                        
                        <p>Your application <strong>({application.application_id})</strong> has been 
                        successfully submitted for review.</p>
                        
                        <div class="info-box">
                            <strong>📅 Submitted:</strong> {timezone.now().strftime('%B %d, %Y at %I:%M %p')}<br>
                            <strong>📝 Documents:</strong> {application.documents.count()} file(s) uploaded<br>
                            <strong>⏰ Review Time:</strong> 4-6 weeks
                        </div>
                        
                        <h3>What Happens Next?</h3>
                        <ol>
                            <li>Our admissions committee will review your application</li>
                            <li>You will receive email updates on your application status</li>
                            <li>A final decision will be communicated within 4-6 weeks</li>
                            <li>You can track your status anytime through your dashboard</li>
                        </ol>
                        
                        <p>If you have any questions, contact us at 
                        <a href="mailto:admissions@miu.edu">admissions@miu.edu</a></p>
                        
                        <p>Best regards,<br>
                        <strong>Admissions Team</strong><br>
                        Modern International University</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            email = EmailMultiAlternatives(
                subject,
                f"Your application {application.application_id} has been submitted.",
                settings.DEFAULT_FROM_EMAIL,
                [application.email]
            )
            email.attach_alternative(html_message, "text/html")
            email.send(fail_silently=True)
            
        except Exception as e:
            print(f"Error sending submission email: {e}")
        
        messages.success(
            request, 
            'Application submitted successfully! You will receive a decision within 4-6 weeks. '
            'Check your email for confirmation.'
        )
    else:
        messages.error(
            request, 
            'Unable to submit application. Please ensure all requirements are met.'
        )
    
    return redirect('eduweb:application_status')


@login_required(login_url='eduweb:auth_page')
def accept_admission(request, application_id):
    """
    Student accepts admission offer.
    Secure version with proper validation and email notification.
    """
    if request.method != 'POST':
        return redirect('eduweb:application_status')
    
    application = get_application_secure(application_id, request.user)
    
    if not application:
        messages.error(
            request, 
            'Application not found or you do not have permission to access it.'
        )
        return redirect('eduweb:application_status')
    
    # Validate application status
    if application.status != 'approved':
        messages.error(
            request, 
            'Only approved applications can be accepted.'
        )
        return redirect('eduweb:application_status')
    
    # Check if already accepted
    if application.admission_accepted:
        messages.info(
            request, 
            'You have already accepted this admission offer.'
        )
        return redirect('eduweb:application_status')
    
    # Accept admission
    if application.accept_admission():
        # Issue admission number
        application.issue_admission_number()
        
        # Send confirmation email
        try:
            applicant_name = (
                application.get_full_name() 
                if hasattr(application, 'get_full_name') 
                else f"{application.first_name} {application.last_name}"
            )
            
            subject = 'Admission Acceptance Confirmed - Modern International University'
            html_message = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #840384 0%, #6B21A8 100%); 
                               color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .highlight {{ background: #FEF3C7; padding: 15px; border-left: 4px solid #F59E0B; 
                                 margin: 20px 0; border-radius: 5px; }}
                    .button {{ display: inline-block; padding: 12px 30px; background: #840384; 
                              color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎉 Admission Acceptance Confirmed!</h1>
                    </div>
                    <div class="content">
                        <p>Dear {applicant_name},</p>
                        
                        <p>Congratulations! We have received your acceptance of our admission offer.</p>
                        
                        <div class="highlight">
                            <strong>Your Admission Number:</strong> {application.admission_number}
                        </div>
                        
                        <h3>📋 Next Steps:</h3>
                        <ol>
                            <li>Your application is now pending <strong>department approval</strong></li>
                            <li>You will receive another email once the department head approves your admission</li>
                            <li>After approval, you will gain access to the <strong>Student Portal</strong></li>
                            <li>Keep your admission number safe for future reference</li>
                        </ol>
                        
                        <p><strong>Estimated Time:</strong> Department approval typically takes 2-3 business days.</p>
                        
                        <p>If you have any questions, please contact our admissions team at 
                        <a href="mailto:admissions@miu.edu">admissions@miu.edu</a></p>
                        
                        <p>Best regards,<br>
                        <strong>Admissions Team</strong><br>
                        Modern International University</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            email = EmailMultiAlternatives(
                subject,
                f"Dear {applicant_name}, your admission number is {application.admission_number}",
                settings.DEFAULT_FROM_EMAIL,
                [application.email]
            )
            email.attach_alternative(html_message, "text/html")
            email.send(fail_silently=True)
            
        except Exception as e:
            print(f"Error sending confirmation email: {e}")
        
        messages.success(
            request, 
            f'Admission accepted successfully! Your admission number is {application.admission_number}. '
            'Awaiting department approval to access the student portal.'
        )
    else:
        messages.error(
            request, 
            'Unable to accept admission at this time. Please contact support.'
        )
    
    return redirect('eduweb:application_status')