from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives, send_mail
from django.conf import settings
from .forms import ContactForm, CourseApplicationForm
from .models import ContactMessage, CourseApplication, CourseApplicationFile,Application,Payment,Vendor
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from .decorators import check_for_auth
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


def application_status_context(request):
    """Add application status to all template contexts"""
    has_pending_application = False
    if request.user.is_authenticated:
        has_pending_application = CourseApplication.objects.filter(
            user=request.user,
            submitted=True
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

    # Redirect if user is already logged in
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in.')
        # Redirect based on user type
        if request.user.is_staff:
            return redirect('management:dashboard')
        else:
            return redirect('eduweb:apply')
    
    # Generate captcha only on GET request (initial page load)
    if request.method == 'GET':
        captcha_question, captcha_answer = generate_captcha()
        request.session['captcha_answer'] = captcha_answer
    else:
        # On POST, retrieve the existing captcha from session
        captcha_answer = request.session.get('captcha_answer')
        if captcha_answer is None:
            # Session expired, generate new captcha and return error
            captcha_question, captcha_answer = generate_captcha()
            request.session['captcha_answer'] = captcha_answer
            return JsonResponse({
                'success': False,
                'errors': {'captcha': ['Session expired. Please try again.']},
                'captcha_question': captcha_question
            }, status=400)
        else:
            captcha_question = None
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'signup':
            # Get captcha from session
            session_captcha = request.session.get('captcha_answer')
            
            signup_form = SignUpForm(
                request.POST, 
                captcha_answer=session_captcha
            )
            
            if signup_form.is_valid():
                # Clear the captcha from session after successful validation
                if 'captcha_answer' in request.session:
                    del request.session['captcha_answer']
                    
                user = signup_form.save(commit=False)
                user.is_active = False  # Deactivate until email verification
                user.save()
                
                # Send verification email
                send_verification_email(request, user)
                
                return JsonResponse({
                    'success': True,
                    'message': 'Account created successfully! Please check your email to verify your account.',
                    'email': user.email
                })
            else:
                errors = {}
                for field, error_list in signup_form.errors.items():
                    errors[field] = [str(e) for e in error_list]
                
                # Generate new captcha on error
                new_question, new_answer = generate_captcha()
                request.session['captcha_answer'] = new_answer
                
                return JsonResponse({
                    'success': False,
                    'errors': errors,
                    'captcha_question': new_question
                }, status=400)
        
        elif action == 'login':
            # Try to authenticate with username or email
            username_or_email = request.POST.get('username')
            password = request.POST.get('password')
            captcha = request.POST.get('captcha')
            
            # Verify captcha
            session_answer = request.session.get('captcha_answer')
            
            try:
                # TYPE CAST BOTH TO INT FOR COMPARISON
                captcha_int = int(captcha) if captcha else None
                session_answer_int = int(session_answer) if session_answer is not None else None
                
                if session_answer_int is None or captcha_int != session_answer_int:
                    new_question, new_answer = generate_captcha()
                    request.session['captcha_answer'] = new_answer
                    return JsonResponse({
                        'success': False,
                        'errors': {'captcha': ['Incorrect answer. Please try again.']},
                        'captcha_question': new_question
                    }, status=400)
            except (ValueError, TypeError):
                new_question, new_answer = generate_captcha()
                request.session['captcha_answer'] = new_answer
                return JsonResponse({
                    'success': False,
                    'errors': {'captcha': ['Invalid answer. Please enter a number.']},
                    'captcha_question': new_question
                }, status=400)
            
            # Check if input is email
            user = None
            if '@' in username_or_email:
                try:
                    user_obj = User.objects.get(email=username_or_email)
                    username_or_email = user_obj.username
                except User.DoesNotExist:
                    pass
            
            user = authenticate(request, username=username_or_email, password=password)
            
            if user is not None:
                if not user.is_active:
                    # Generate new captcha for retry
                    new_question, new_answer = generate_captcha()
                    request.session['captcha_answer'] = new_answer
                    return JsonResponse({
                        'success': False,
                        'errors': {'__all__': ['Please verify your email before logging in. Check your inbox for the verification link.']},
                        'captcha_question': new_question
                    }, status=400)
                
                # Clear captcha on successful login
                if 'captcha_answer' in request.session:
                    del request.session['captcha_answer']
                    
                login(request, user)
                
                # Check if user is admin/staff and redirect accordingly
                if user.is_staff or user.is_superuser:
                    redirect_url = reverse('management:dashboard')
                else:
                    redirect_url = reverse('eduweb:apply')
                
                return JsonResponse({
                    'success': True,
                    'message': 'Login successful! Redirecting...',
                    'redirect_url': redirect_url
                })
            else:
                new_question, new_answer = generate_captcha()
                request.session['captcha_answer'] = new_answer
                return JsonResponse({
                    'success': False,
                    'errors': {'__all__': ['Invalid username/email or password.']},
                    'captcha_question': new_question
                }, status=400)
    
    # GET request - show forms
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
        
        return redirect('auth_page')
        
    except UserProfile.DoesNotExist:
        messages.error(request, 'Invalid verification link.')
        return redirect('auth_page')


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
def apply(request):
    print(request.user)
    # Check if email is verified
    if not request.user.profile.email_verified:
        messages.warning(request, 'Please verify your email before applying.')
        return redirect('auth_page')
    
    # Check if user already has a pending application
    existing_application = CourseApplication.objects.filter(
        user=request.user,
        decision='pending'
    ).first()
    
    if existing_application:
        messages.info(request, 'You already have an application in progress.')
        return redirect('eduweb:application_status')
    
    if request.method == 'POST':
        form = CourseApplicationForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                print("=== APPLICATION SUBMISSION STARTED ===")
                print(f"User: {request.user.username}")
                print(f"Files received: {list(request.FILES.keys())}")
                
                # Collect academic history from all entries
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
                
                # Save application first (without files)
                application = form.save(commit=False, user=request.user)
                application.academic_history = academic_history
                application.save()
                
                print(f"Application saved: {application.application_id}")
                
                # Handle file uploads with detailed tracking
                documents = {}
                file_field_mapping = {
                    'transcripts_file': ('transcripts', 'Transcripts'),
                    'english_proficiency_file': ('english_proficiency', 'English Proficiency Certificate'),
                    'personal_statement_file': ('personal_statement', 'Personal Statement'),
                    'cv_file': ('cv', 'CV/Resume')
                }
                
                for form_field, (file_type, doc_name) in file_field_mapping.items():
                    if form_field in request.FILES:
                        try:
                            file_obj = request.FILES[form_field]
                            print(f"Processing {form_field}: {file_obj.name} ({file_obj.size} bytes)")
                            
                            # Create CourseApplicationFile entry with file type
                            app_file = CourseApplicationFile.objects.create(
                                application=application,
                                file=file_obj,
                                file_type=file_type,
                                original_filename=file_obj.name,
                                file_size=file_obj.size
                            )
                            
                            # Store metadata in documents_uploaded JSON
                            documents[doc_name] = {
                                'file_id': app_file.id,
                                'file_name': file_obj.name,
                                'file_type': file_type,
                                'file_size': app_file.get_file_size_display(),
                                'file_path': app_file.file.name,
                                'uploaded_at': timezone.now().isoformat()
                            }
                            
                            print(f"✅ Successfully saved {doc_name}: ID {app_file.id}")
                            
                        except Exception as file_error:
                            print(f"❌ Error uploading {form_field}: {str(file_error)}")
                            import traceback
                            traceback.print_exc()
                            # Continue with other files even if one fails
                            continue
                    else:
                        print(f"⚠️ No file uploaded for {form_field}")
                
                # Update documents_uploaded field if any documents were uploaded
                if documents:
                    application.documents_uploaded = documents
                    application.save()
                    print(f"Documents metadata saved: {list(documents.keys())}")
                else:
                    print("⚠️ No documents were uploaded")
                
                print("=== APPLICATION SUBMISSION COMPLETED ===")

                # Send emails asynchronously (non-blocking)
                from threading import Thread

                def send_emails_async():
                    try:
                        send_application_confirmation_email(application)
                        send_application_admin_notification(application)
                    except Exception as email_error:
                        print(f"Email error (non-critical): {str(email_error)}")

                # Start email sending in background thread
                email_thread = Thread(target=send_emails_async)
                email_thread.daemon = True
                email_thread.start()
                
                # Return JSON for AJAX
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'application_id': application.application_id,
                        'message': 'Application submitted successfully!',
                        'files_uploaded': len(documents),
                        'redirect_url': reverse('application_status')
                    })
                else:
                    messages.success(request, f'Application submitted successfully! Your ID: {application.application_id}')
                    return redirect('application_status')
                    
            except Exception as e:
                print(f"=== ERROR IN APPLICATION SUBMISSION ===")
                print(f"Error type: {type(e).__name__}")
                print(f"Error message: {str(e)}")
                import traceback
                traceback.print_exc()
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': f'{type(e).__name__}: {str(e)}'
                    }, status=500)
                else:
                    messages.error(request, f'Error: {str(e)}')
        else:
            print("=== FORM VALIDATION ERRORS ===")
            for field, errors in form.errors.items():
                print(f"{field}: {errors}")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                errors = {}
                for field, error_list in form.errors.items():
                    errors[field] = [str(e) for e in error_list]
                
                return JsonResponse({
                    'success': False,
                    'errors': errors,
                    'error': 'Please correct the errors in the form.'
                }, status=400)
            else:
                messages.error(request, 'Please correct the errors in the form.')
    if request.user.is_authenticated:
        form = CourseApplicationForm(initial={
            'email': request.user.email
        })

    else:
        form = CourseApplicationForm()
    
    return render(request, 'form.html', {'form': form})

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
                            <p><strong>Program:</strong> {application.get_program_display_name()}</p>
                            <p><strong>Degree Level:</strong> {application.get_degree_level_display_name()}</p>
                            <p><strong>Submission Date:</strong> {application.submission_date.strftime('%B %d, %Y')}</p>
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
                <p><strong>Program:</strong> {application.get_program_display_name()}</p>
                <p><strong>Degree Level:</strong> {application.get_degree_level_display_name()}</p>
                <p><strong>Submitted:</strong> {application.submission_date.strftime('%Y-%m-%d %H:%M:%S')}</p>
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
def research(request):
    """Research page view"""
    return render(request, 'research.html')


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
def application_status(request):
    """Display user's application status"""
    # Get the most recent application for this user
    application = CourseApplication.objects.filter(
        user=request.user
    ).order_by('-created_at').first()
    
    context = {
        'application': application
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
    if application.decision != 'accepted':
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
                    stripe_payment_intent=intent.id,
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
        stripe_payment_intent=intent.id
    ).first()

    if not payment:
        return JsonResponse({"error": "Payment not recorded yet"}, status=400)

    return JsonResponse({"status": "success", "payment_id": payment.id})


#Payment Success Page (Receipt)

def payment_success(request, payment_id):
    payment = get_object_or_404(Application_pay, id=payment_id, status="PAID")

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
                payment_intent=payment.stripe_payment_intent
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
        application = get_object_or_404(Application, id=application_id)
        
        # In production, verify user has permission to view this application
        
        summary = {
            'application_id': str(application.id),
            'full_name': application.full_name,
            'email': application.email,
            'amount': float(application.amount),
            'description': 'Application Processing Fee',
            'stripe_public_key': settings.STRIPE_PUBLISHABLE_KEY,
        }
        
        return JsonResponse({'success': True, 'data': summary})
    except Exception as e:
        logger.error(f"Error getting payment summary: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Unable to load payment details'}, status=500)




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
        data = request.POST

        # -------------------------------------------------
        # 1. GET OR CREATE APPLICATION (NO DUPLICATES)
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
        # 2. PERSONAL INFORMATION
        # -------------------------------------------------
        application.first_name = data.get("first_name", "").strip()
        application.last_name = data.get("last_name", "").strip()
        application.email = data.get("email", "").strip()
        application.phone = data.get("phone", "").strip()
        application.gender = data.get("gender", "")
        application.country = data.get("country", "")
        application.address = data.get("address", "").strip()

        # Date of birth (safe parsing, never overwrite with None)
        dob = data.get("date_of_birth")
        print(dob)
        if dob:
            try:
                application.date_of_birth = datetime.strptime(
                    dob, "%Y-%m-%d"
                ).date()
            except ValueError:
                pass  # ignore invalid format during draft save
       
        # -------------------------------------------------
        # 3. ACADEMIC / ENGLISH DETAILS
        # -------------------------------------------------
        # -------------------------------
        # ENGLISH PROFICIENCY (FIXED)
        # -------------------------------
        proficiency_type = data.get("english_proficiency_type", "")

        score = ""
        if proficiency_type == "toefl":
            score = data.get("toefl_score", "")
        elif proficiency_type == "ielts":
            score = data.get("ielts_score", "")
        elif proficiency_type == "other":
            score = data.get("other_test", "")
        elif proficiency_type == "native":
            score = "native"

        application.english_proficiency = proficiency_type
        application.english_score = score


        # Academic history (JSON string expected)
        academic_history = data.get("academic_history")
        print(academic_history)
        if academic_history:
            try:
                application.academic_history = json.loads(academic_history)
            except json.JSONDecodeError:
                pass

        # -------------------------------------------------
        # 4. COURSE SELECTION
        # -------------------------------------------------
        application.program = data.get("program", "")
        application.degree_level = data.get("degree_level", "")
        application.study_mode = data.get("study_mode", "")
        application.intake = data.get("intake", "")
        application.scholarship = data.get("scholarship") in ("true", "on", "1")

        # -------------------------------------------------
        # 5. META / DRAFT FLAGS
        # -------------------------------------------------
        application.submitted = False  # draft save only

        # -------------------------------------------------
        # 6. SAVE (MODEL HANDLES application_id GENERATION)
        # -------------------------------------------------
        application.save()

        # -------------------------------------------------
        # 7. RESPONSE
        # -------------------------------------------------
        return JsonResponse({
            "success": True,
            "application_id": application.application_id,
            "payment_status": application.decision if application.decision else "pending",
        })

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
        "program": app.get_program_display_name(),
        "amount": 150.00,  # configurable later
        "payment_status": app.files.filter(
            payment_status="success"
        ).exists() and "success" or "pending"
    })

@login_required
@require_POST
def upload_application_file(request, application_id):
    application = CourseApplication.objects.get(
        application_id=application_id,
        user=request.user
    )

    # 🔒 HARD PAYMENT ENFORCEMENT
    if not application.files.filter(payment_status="success").exists():
        return JsonResponse({
            "success": False,
            "error": "Payment required before uploading documents"
        }, status=403)

    file = request.FILES.get("file")
    file_type = request.POST.get("file_type")

<<<<<<< HEAD
    CourseApplicationFile.objects.create(
        application=application,
        file=file,
        file_type=file_type,
        submitted=True
    )

    return JsonResponse({"success": True})

def finalize_application(application):
    application.submitted = True
    application.submission_date = timezone.now()
    application.status = "submitted"
    application.save()
=======

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
>>>>>>> ef6e711df83ba864c3342774272e1a30ecceb6b3
