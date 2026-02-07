from email.mime import application
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives, send_mail
from django.conf import settings
from .forms import ContactForm, CourseApplicationForm
from eduweb.models import ContactMessage, CourseApplication, CourseIntake, Vendor
from eduweb.models import Faculty, Course, BlogPost, BlogCategory
from django.http import JsonResponse, HttpResponse
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
    ApplicationDocument, ApplicationPayment
)
from django.db.models import Q
from django.shortcuts import get_object_or_404
from .decorators import applicant_required

def application_status_context(request):
    """Add application status to all template contexts"""
    has_pending_application = False
    if request.user.is_authenticated:
        has_pending_application = CourseApplication.objects.filter(
            user=request.user,
            status__in=['draft', 'pending_payment', 'submitted', 'under_review', 'reviewed']
        ).exists()
    return {'has_pending_application': has_pending_application}

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



def send_verification_email(request, user):
    """Send email verification link to user"""
    try:
        profile = user.profile
        token = profile.verification_token
        current_site = get_current_site(request)
        verification_url = request.build_absolute_uri(
            reverse('verify_email', kwargs={'token': str(token)})
        )
        
        subject = 'Verify Your MIU Account'
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f4f4f4;">
                    <div style="background: linear-gradient(135deg, #840384 0%, #a855f7 100%); padding: 30px; text-align: center;">
                        <h1 style="color: white; margin: 0;">Welcome to MIU!</h1>
                    </div>
                    <div style="background-color: white; padding: 30px; margin-top: 20px;">
                        <p style="font-size: 16px;">Dear <strong>{user.get_full_name() or user.username}</strong>,</p>
                        <p>Thank you for creating an account with Modern International University. Please verify your email address to complete your registration.</p>
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{verification_url}" style="display: inline-block; padding: 15px 40px; background: linear-gradient(135deg, #840384 0%, #a855f7 100%); color: white; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px;">
                                Verify Email Address
                            </a>
                        </div>
                        <p style="font-size: 14px; color: #666;">Or copy and paste this link into your browser:</p>
                        <p style="font-size: 14px; color: #1D4ED8; word-break: break-all;">{verification_url}</p>
                        <p style="font-size: 14px; color: #666; margin-top: 30px;">This link will expire in 24 hours.</p>
                        <p>Best regards,<br><strong style="color: #840384;">The MIU Team</strong></p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        text_content = f"""
Welcome to Modern International University!

Dear {user.get_full_name() or user.username},

Thank you for creating an account. Please verify your email address by clicking the link below:

{verification_url}

This link will expire in 24 hours.

Best regards,
The MIU Team
        """
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        return True
    except Exception as e:
        print(f"Error sending verification email: {str(e)}")
        return False


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
        else:
            messages.info(request, 'Your email is already verified.')
        
        return redirect('eduweb:auth_page')
        
    except UserProfile.DoesNotExist:
        messages.error(request, 'Invalid verification link.')
        return redirect('eduweb:auth_page')


def user_logout(request):
    """Logout user"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('eduweb:index')


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
    return render(request, 'index.html')

@check_for_auth
def about(request):
    return render(request, 'about.html')


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
        status__in=['draft', 'pending_payment', 'submitted', 'under_review']
    ).first()

    if existing_application:
        messages.info(request, 'You already have an application in progress.')
        return redirect('eduweb:application_status')

    # -------------------------------
    # FETCH COURSES (UPDATED)
    # -------------------------------
    from .models import Course, Faculty, CourseIntake

    courses = Course.objects.filter(is_active=True).select_related('faculty')
    faculties = Faculty.objects.filter(is_active=True)

    # Group courses by faculty
    courses_by_faculty = {}
    for course in courses:
        faculty_name = course.faculty.name
        if faculty_name not in courses_by_faculty:
            courses_by_faculty[faculty_name] = []
        
        # Get active intakes for this course
        intakes = CourseIntake.objects.filter(
            course=course,
            is_active=True,
            application_deadline__gte=timezone.now().date()
        ).values('id', 'intake_period', 'year', 'start_date')
        
        courses_by_faculty[faculty_name].append({
            "id": course.id,
            "name": course.name,
            "code": course.code,
            "degree_level": course.degree_level,
            "available_study_modes": course.available_study_modes,
            "application_fee": str(course.application_fee),
            "tuition_fee": str(course.tuition_fee),
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
                        'redirect_url': reverse('application_status')
                    })

                messages.success(
                    request,
                    f'Application submitted successfully! Your ID: {application.application_id}'
                )
                return redirect('application_status')

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
        'courses': courses,
        'courses_json': courses_json,
    })




def send_application_confirmation_email(application):
    """Send confirmation email to applicant"""
    try:
        subject = f'Application Received - {application.application_id}'
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f4f4f4;">
                    <div style="background: linear-gradient(135deg, #0F2A44 0%, #1D4ED8 100%); padding: 30px; text-align: center;">
                        <h1 style="color: white; margin: 0;">Application Received!</h1>
                    </div>
                    <div style="background-color: white; padding: 30px; margin-top: 20px;">
                        <p style="font-size: 16px;">Dear <strong>{application.first_name} {application.last_name}</strong>,</p>
                        <p>Thank you for applying to Modern International University. We have received your application.</p>
                        <div style="background-color: #E6F0FF; padding: 20px; border-radius: 8px; margin: 25px 0;">
                            <h3 style="color: #0F2A44; margin-top: 0;">Application Details</h3>
                            <p><strong>Application ID:</strong> {application.application_id}</p>
                            <p><strong>Program:</strong> {application.course.name}</p>
                            <p><strong>Degree Level:</strong> {application.course.get_degree_level_display()}</p>
                            <p><strong>Faculty:</strong> {application.course.faculty.name}</p>
                            <p><strong>Submission Date:</strong> {application.submitted_at.strftime('%B %d, %Y') if application.submitted_at else 'Pending'}</p>
                        </div>
                        <p>Our admissions team will review your application and contact you within 5-7 business days.</p>
                        <p>Best regards,<br><strong style="color: #0F2A44;">The MIU Admissions Team</strong></p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=f"Application ID: {application.application_id}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[application.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        return True
    except Exception as e:
        print(f"Error sending confirmation email: {str(e)}")
        return False


def send_application_admin_notification(application):
    """Send notification email to admin"""
    try:
        subject = f'New Application - {application.application_id}'
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>New Course Application Received</h2>
                <p><strong>Application ID:</strong> {application.application_id}</p>
                <p><strong>Name:</strong> {application.get_full_name()}</p>
                <p><strong>Email:</strong> {application.email}</p>
                <p><strong>Course:</strong> {application.course.name} ({application.course.code})</p>
                <p><strong>Degree Level:</strong> {application.course.get_degree_level_display()}</p>
                <p><strong>Faculty:</strong> {application.course.faculty.name}</p>
                <p><strong>Intake:</strong> {application.intake.get_intake_period_display()} {application.intake.year}</p>
                <p><strong>Study Mode:</strong> {application.get_study_mode_display()}</p>
                <p><strong>Submitted:</strong> {application.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if application.submitted_at else 'Draft'}</p>
            </body>
        </html>
        """
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=f"New application from {application.get_full_name()}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.CONTACT_EMAIL],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        return True
    except Exception as e:
        print(f"Error sending admin notification: {str(e)}")
        return False


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


def send_admin_email(contact_message):
    """Send notification email to admin"""
    try:
        subject = f'New Contact Form Submission - {contact_message.get_subject_display()}'
        
        text_content = f"""
New contact form submission from MIU website:

Name: {contact_message.name}
Email: {contact_message.email}
Subject: {contact_message.get_subject_display()}

Message:
{contact_message.message}

Submitted at: {contact_message.created_at.strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f4f4f4;">
                    <div style="background-color: #0F2A44; padding: 20px; text-align: center;">
                        <h1 style="color: white; margin: 0;">New Contact Form Submission</h1>
                    </div>
                    <div style="background-color: white; padding: 30px; margin-top: 20px;">
                        <h2 style="color: #0F2A44; border-bottom: 2px solid #1D4ED8; padding-bottom: 10px;">
                            Contact Details
                        </h2>
                        <table style="width: 100%; margin-top: 20px;">
                            <tr>
                                <td style="padding: 10px; font-weight: bold; width: 30%;">Name:</td>
                                <td style="padding: 10px;">{contact_message.name}</td>
                            </tr>
                            <tr style="background-color: #f9f9f9;">
                                <td style="padding: 10px; font-weight: bold;">Email:</td>
                                <td style="padding: 10px;">{contact_message.email}</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; font-weight: bold;">Subject:</td>
                                <td style="padding: 10px;">{contact_message.get_subject_display()}</td>
                            </tr>
                            <tr style="background-color: #f9f9f9;">
                                <td style="padding: 10px; font-weight: bold;">Submitted:</td>
                                <td style="padding: 10px;">{contact_message.created_at.strftime('%Y-%m-%d %H:%M:%S')}</td>
                            </tr>
                        </table>
                        <h3 style="color: #0F2A44; margin-top: 30px; border-bottom: 2px solid #1D4ED8; padding-bottom: 10px;">
                            Message
                        </h3>
                        <div style="background-color: #f9f9f9; padding: 20px; margin-top: 15px; border-left: 4px solid #1D4ED8;">
                            {contact_message.message}
                        </div>
                        <div style="margin-top: 30px; padding: 15px; background-color: #E6F0FF; border-radius: 5px;">
                            <p style="margin: 0; color: #0F2A44;">
                                <strong>Reply to:</strong> <a href="mailto:{contact_message.email}" style="color: #1D4ED8;">{contact_message.email}</a>
                            </p>
                        </div>
                    </div>
                </div>
            </body>
        </html>
        """
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.CONTACT_EMAIL],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        
        print(f"✅ Admin email sent successfully to {settings.CONTACT_EMAIL}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending admin email: {str(e)}")
        return False


def send_user_confirmation_email(contact_message):
    """Send confirmation email to user"""
    try:
        subject = 'Thank you for contacting MIU - We received your message'
        
        text_content = f"""
Dear {contact_message.name},

Thank you for contacting Modern International University (MIU). We have received your message and will respond within 1-2 business days.

Your Message Details:
Subject: {contact_message.get_subject_display()}
Message: {contact_message.message}

If you have any urgent questions, please call us at +1 (555) 123-4567.

Best regards,
The MIU Admissions Team
        """
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f4f4f4;">
                    <div style="background: linear-gradient(135deg, #0F2A44 0%, #1D4ED8 100%); padding: 30px; text-align: center;">
                        <h1 style="color: white; margin: 0;">Thank You for Contacting Us!</h1>
                    </div>
                    <div style="background-color: white; padding: 30px; margin-top: 20px;">
                        <p style="font-size: 16px; margin-bottom: 20px;">Dear <strong>{contact_message.name}</strong>,</p>
                        <p style="font-size: 16px; margin-bottom: 20px;">
                            Thank you for reaching out to Modern International University. We have received your message 
                            and our team will review it carefully.
                        </p>
                        <div style="background-color: #E6F0FF; padding: 20px; border-radius: 8px; margin: 25px 0;">
                            <h3 style="color: #0F2A44; margin-top: 0;">Your Message Summary</h3>
                            <p><strong>Subject:</strong> {contact_message.get_subject_display()}</p>
                        </div>
                        <p style="font-size: 16px;">
                            Best regards,<br>
                            <strong style="color: #0F2A44;">The MIU Admissions Team</strong>
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[contact_message.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        
        print(f"✅ Confirmation email sent successfully to {contact_message.email}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending user confirmation email: {str(e)}")
        return False


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


@login_required
@smart_redirect_applicant
def application_status(request):
    """Display user's application status"""
    # Get the most recent application for this user
    application = CourseApplication.objects.filter(
        user=request.user
    ).select_related('course', 'intake','course__faculty').prefetch_related('documents').order_by('-created_at').first()
    
    # Check if payment exists
    has_payment = False
    payment = None
    if application:
        try:
            payment = application.payment
            has_payment = True
        except ApplicationPayment.DoesNotExist:
            has_payment = False
    
    context = {
        'application': application,
        'has_payment': has_payment,
        'payment': payment,
    }
    
    return render(request, 'applications/application_status.html', context)


login_required
def admission_letter(request, application_id):
    """Display admission letter for accepted application"""
    # Allow both applicant and admin to view
    application = get_object_or_404(CourseApplication, id=application_id)
    
    # Check permissions: either the application owner or staff
    if not (request.user == application.user or request.user.is_staff):
        messages.error(request, 'You do not have permission to view this admission letter.')
        return redirect('eduweb:index')
    
    # Check if application is accepted
    if application.status != 'accepted':
        messages.warning(request, 'Admission letter is only available for accepted applications.')
        return redirect('eduweb:application_status')
    
    context = {
        'application': application,
    }
    
    return render(request, 'applications/admission_letter.html', context)


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

def payment_page(request):
    return render(request, "applications/pay.html", {
        "stripe_key": settings.STRIPE_PUBLIC_KEY,
        "amount": 25000  # £250.00
    })



@require_POST
def create_payment_intent(request):
    if not request.body:
        return JsonResponse({"error": "Empty request body"}, status=400)

    try:
        data = json.loads(request.body.decode("utf-8"))
        print(data)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    amount = data.get("amount")
    application_id = data.get("application_id")
    vendor_id = data.get("vendor_id")  # pass vendor ID from frontend

    vendor = get_object_or_404(Vendor, id=vendor_id)

    if not amount or not application_id:
        return JsonResponse({"error": "Missing fields"}, status=400)

    intent = stripe.PaymentIntent.create(
        amount=int(amount),
        currency="gbp",
        metadata={
            "application_id": application_id,
            "vendor_id": vendor.id,
            "user_id": request.user.id if request.user.is_authenticated else "",
        },
        automatic_payment_methods={"enabled": True}
    )

    return JsonResponse({"clientSecret": intent.client_secret})





#Stripe Webhook (Atomic, Idempotent, Safe)

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception:
        return HttpResponse(status=400)

    if event["type"] == "payment_intent.succeeded":
        intent = event["data"]["object"]

        try:
            with transaction.atomic():
                payment, created = ApplicationPayment.objects.select_for_update().get_or_create(
                    gateway_payment_id=intent.id,  # ✅ Correct field name
                    defaults={
                        "application_id": intent.metadata.get("application_id"),
                        "amount": intent.amount / 100,
                        "currency": intent.currency.upper(),
                        "status": "PAID",
                        "vendor_id": intent.metadata.get("vendor_id"),
                    },
                )

                if not created and payment.status == "PAID":
                    return HttpResponse(status=200)

                payment.status = "PAID"
                payment.save()

                # send emails after commit
                transaction.on_commit(lambda: send_payment_emails(payment))

        except IntegrityError:
            return HttpResponse(status=200)

    return HttpResponse(status=200)



#Send Emails Helper


def send_payment_emails(payment):
    if payment.user and payment.user.email:
        send_mail(
            "Payment Receipt",
            f"""
    Payment Successful

    Amount: £{payment.amount}
    Application ID: {payment.application_id}
    Transaction: {payment.stripe_payment_intent}
    """,
                settings.DEFAULT_FROM_EMAIL,
                [payment.user.email],
                fail_silently=True,
            )

        send_mail(
            "New Payment Received",
            f"""
    Vendor Payment Alert

    Application ID: {payment.application_id}
    Amount: £{payment.amount}
    """,
            settings.DEFAULT_FROM_EMAIL,
            [payment.vendor.email],
            fail_silently=True,
    )



#Confirm Payment (Frontend POST fallback)

@require_POST
def confirm_payment(request):
    if not request.body:
        return JsonResponse({"error": "Empty body"}, status=400)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    payment_intent_id = data.get("payment_intent")
    if not payment_intent_id:
        return JsonResponse({"error": "Missing payment_intent"}, status=400)

    intent = stripe.PaymentIntent.retrieve(payment_intent_id)

    if intent.status != "succeeded":
        return JsonResponse({"status": "failed"}, status=400)

    payment = ApplicationPayment.objects.filter(
        gateway_payment_id=intent.id  # ✅ Correct
    ).first()

    if not payment:
        return JsonResponse({"error": "Payment not recorded yet"}, status=400)

    return JsonResponse({"status": "success", "payment_id": payment.id})


#Payment Success Page (Receipt)

def payment_success(request, payment_id):
    payment = get_object_or_404(ApplicationPayment, id=payment_id, status="success")

    return render(request, "applications/payment_success.html", {
        "payment": payment
    })


#Atomic Refunds

@require_POST
def refund_payment(request, payment_id):
    payment = get_object_or_404(ApplicationPayment, id=payment_id)

    if payment.status != "PAID":
        return JsonResponse({"error": "Cannot refund non-paid payment"}, status=400)

    try:
        with transaction.atomic():
            # Refund via Stripe
            refund = stripe.Refund.create(
                payment_intent=payment.gateway_payment_id  # ✅ Correct
            )
            # Update DB
            payment.status = "REFUNDED"
            payment.refunded_at = timezone.now()
            payment.save()
    except stripe.error.StripeError as e:
        return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"status": "refunded"})




@require_GET
def get_payment_summary(request, application_id):
    """Get payment summary for an application"""
    try:
        # Fix 1: Use correct model name 'CourseApplication'
        # Fix 2: Use application_id field instead of id
        application = get_object_or_404(
            CourseApplication, 
            application_id=application_id
        )
        
        # Fix 3: Verify user has permission to view this application
        if request.user.is_authenticated:
            if not (request.user == application.user or request.user.is_staff):
                return JsonResponse({
                    'success': False, 
                    'error': 'Permission denied'
                }, status=403)
        
        summary = {
            'application_id': application.application_id,  # ✅ Use the actual application_id field
            'full_name': application.get_full_name(),  # ✅ Use the method (with parentheses)
            'email': application.email,
            'course_name': application.course.name,  # ✅ Added course info
            'faculty': application.course.faculty.name,  # ✅ Added faculty info
            'amount': float(application.course.application_fee),  # ✅ Get fee from course
            'currency': 'GBP',  # ✅ Added currency
            'description': 'Application Processing Fee',
            'stripe_public_key': settings.STRIPE_PUBLIC_KEY,  # ✅ Correct setting name
        }
        
        return JsonResponse({'success': True, 'data': summary})
    except CourseApplication.DoesNotExist:
        logger.error(f"Application not found: {application_id}")
        return JsonResponse({
            'success': False, 
            'error': 'Application not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error getting payment summary: {str(e)}")
        return JsonResponse({
            'success': False, 
            'error': 'Unable to load payment details'
        }, status=500)




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
        course_id = data.get("course")
        if course_id:
            try:
                application.course = Course.objects.get(id=course_id)
            except Course.DoesNotExist:
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
        "course": app.course.name,
        "faculty": app.course.faculty.name,
        "amount": float(app.course.application_fee),
        "payment_status": app.payment_status if hasattr(app, 'payment') else 'pending'
    })

@login_required
@require_POST
def upload_application_file(request, application_id):
    from eduweb.forms import ApplicationDocumentUploadForm
    """Handle document upload for an application using Django Form"""
    try:
        # Get the application
        application = get_object_or_404(
            CourseApplication, 
            application_id=application_id,
            user=request.user
        )
        
        # Check if payment is completed
        if not application.is_paid:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    "success": False,
                    "error": "Payment must be completed before uploading documents"
                }, status=403)
            messages.error(request, "Payment must be completed before uploading documents")
            return redirect('eduweb:application_status')
        
        # Check if application allows document uploads
        if not application.can_upload_documents():
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    "success": False,
                    "error": "Application is not in a state that allows document uploads"
                }, status=403)
            messages.error(request, "Application is not in a state that allows document uploads")
            return redirect('eduweb:application_status')
        
        # Process the form
        form = ApplicationDocumentUploadForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Create document
            document = form.save(commit=False)
            document.application = application
            document.original_filename = request.FILES['file'].name
            document.file_size = request.FILES['file'].size
            document.save()
            
            # Update status to documents_uploaded after first document
            if application.status in ['payment_complete', 'pending_payment']:
                application.status = 'documents_uploaded'
                application.save(update_fields=['status'])
            
            # Check if user wants to auto-submit
            auto_submit = form.cleaned_data.get('auto_submit', False)
            
            response_data = {
                "success": True,
                "message": "Document uploaded successfully",
                "documents_count": application.documents.count(),
                "can_submit": application.can_submit(),
                "document": {
                    "id": document.id,
                    "file_type": document.get_file_type_display(),
                    "original_filename": document.original_filename,
                    "file_size": document.get_file_size_display(),
                }
            }
            
            # If auto_submit is true and application can be submitted, submit it
            if auto_submit and application.can_submit():
                if application.mark_as_submitted():
                    # Send submission confirmation emails
                    from threading import Thread
                    
                    def send_emails_async():
                        send_application_confirmation_email(application)
                        send_application_admin_notification(application)
                    
                    Thread(target=send_emails_async, daemon=True).start()
                    
                    response_data.update({
                        "submitted": True,
                        "message": "Document uploaded and application submitted successfully!",
                        "redirect_url": reverse('eduweb:application_status')
                    })
            
            # AJAX response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse(response_data)
            
            # Regular form response
            messages.success(request, response_data['message'])
            if response_data.get('submitted'):
                return redirect('eduweb:application_status')
            return redirect('eduweb:application_status')
        
        else:
            # Form has errors
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(f"{field}: {error}")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    "success": False,
                    "error": "; ".join(error_messages),
                    "errors": form.errors
                }, status=400)
            
            for error in error_messages:
                messages.error(request, error)
            return redirect('eduweb:application_status')
        
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                "success": False,
                "error": str(e)
            }, status=500)
        messages.error(request, f"Error uploading document: {str(e)}")
        return redirect('eduweb:application_status')

@applicant_required
def mark_payment_successful(request, application_id):
    """
    TEST: Mark payment as successful
    Remove in production
    """
    import uuid
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        application = get_object_or_404(
            CourseApplication,
            application_id=application_id,
            user=request.user
        )
        
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
        from django.utils import timezone
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
from .models import Faculty, Course

@check_for_auth
def faculty_detail(request, slug):
    """Dynamic faculty detail page"""
    faculty = get_object_or_404(Faculty, slug=slug, is_active=True)
    courses = faculty.courses.filter(is_active=True)
    
    context = {
        'faculty': faculty,
        'courses': courses,
    }
    
    return render(request, 'faculties/faculty_detail.html', context)


@check_for_auth
def course_detail(request, slug):
    """Dynamic course detail page"""
    course = get_object_or_404(Course, slug=slug, is_active=True)
    
    context = {
        'course': course,
    }
    
    return render(request, 'programs/course_detail.html', context)