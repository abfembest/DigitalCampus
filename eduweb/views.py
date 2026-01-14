from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from .forms import ContactForm, CourseApplicationForm
from .models import ContactMessage, CourseApplication, CourseApplicationFile,Application,Payment
from django.http import JsonResponse
from django.utils import timezone

from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
from .forms import SignUpForm, LoginForm
from .models import UserProfile
import random

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
        return redirect('apply')
    
    # Generate captcha only on GET request (initial page load)
    # This prevents the captcha from changing when the form is submitted
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
            # Reconstruct question for display (we'll generate a new one on error)
            captcha_question = None  # Will be generated on error if needed
    
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
                return JsonResponse({
                    'success': True,
                    'message': 'Login successful! Redirecting...',
                    'redirect_url': reverse('apply')
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


def index(request):
    return render(request, 'index.html')


def about(request):
    return render(request, 'about.html')


@login_required
def apply(request):
    # Check if email is verified
    if not request.user.profile.email_verified:
        messages.warning(request, 'Please verify your email before applying.')
        return redirect('auth_page')
    
    # Check if user already has a pending application
    existing_application = CourseApplication.objects.filter(
        user=request.user,
        submitted=True
    ).first()
    
    if existing_application:
        messages.info(request, 'You already have an application in progress.')
        return redirect('application_status')
    
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


def detail(request):
    return render(request, 'detail.html')


def admission_course(request):
    return render(request, 'course.html')


def admission_requirement(request):
    return render(request, 'admission_requirement.html')


def blank_page(request):
    return render(request, 'blank_page.html')


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


# Faculty Pages
def faculty_science(request):
    """Faculty of Science page"""
    return render(request, 'faculties/science.html')


def faculty_engineering(request):
    """Faculty of Engineering page"""
    return render(request, 'faculties/engineering.html')


def faculty_business(request):
    """Faculty of Business page"""
    return render(request, 'faculties/business.html')


def faculty_arts(request):
    """Faculty of Arts page"""
    return render(request, 'faculties/arts.html')


def faculty_health(request):
    """Faculty of Health Sciences page"""
    return render(request, 'faculties/health.html')


# Program Pages
def program_business_admin(request):
    """Business Administration program page"""
    return render(request, 'programs/business_administration.html')


def program_computer_science(request):
    """Computer Science program page"""
    return render(request, 'programs/computer_science.html')


def program_data_science(request):
    """Data Science program page"""
    return render(request, 'programs/data_science.html')


def program_health_sciences(request):
    """Health Sciences program page"""
    return render(request, 'programs/health_sciences.html')


def program_engineering(request):
    """Engineering program page"""
    return render(request, 'programs/engineering.html')


# Additional Pages
def research(request):
    """Research page view"""
    return render(request, 'research.html')


def campus_life(request):
    """Campus Life page view"""
    return render(request, 'campus_life.html')


def blog(request):
    """Blog page view"""
    return render(request, 'blog.html')


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


def payments(request):
    """payments page"""
    return render(request, 'payments.html')



####### PAYMENT GATEWAY ###########

from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
import json
import stripe
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

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

@require_POST
@csrf_exempt
def create_payment_intent(request):
    """Create Stripe Payment Intent"""
    try:
        data = json.loads(request.body)
        application_id = data.get('application_id')
        
        application = get_object_or_404(Application, id=application_id)
        amount = int(application.amount * 100)  # Convert to cents
        
        # Create Payment Intent
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency='usd',
            metadata={
                'application_id': str(application.id),
                'user_email': application.email,
            },
            description=f'Application fee for {application.full_name}',
        )
        
        # Create payment record
        payment = Payment.objects.create(
            application=application,
            amount=application.amount,
            stripe_payment_intent_id=intent.id,
            status='created'
        )
        
        return JsonResponse({
            'success': True,
            'clientSecret': intent.client_secret,
            'payment_id': str(payment.id)
        })
    except Exception as e:
        logger.error(f"Error creating payment intent: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_POST
@csrf_exempt
def confirm_payment(request):
    """Confirm payment and update application status"""
    try:
        data = json.loads(request.body)
        payment_intent_id = data.get('payment_intent_id')
        
        # Retrieve payment intent from Stripe
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        if intent.status == 'succeeded':
            # Update payment record
            payment = Payment.objects.get(stripe_payment_intent_id=payment_intent_id)
            payment.status = 'completed'
            payment.card_last4 = intent.charges.data[0].payment_method_details.card.last4
            payment.card_brand = intent.charges.data[0].payment_method_details.card.brand
            payment.processed_at = timezone.now()
            payment.save()
            
            # Update application status
            application = payment.application
            application.status = 'payment_completed'
            application.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Payment completed successfully',
                'application_id': str(application.id)
            })
        else:
            return JsonResponse({
                'success': False,
                'error': f'Payment not successful. Status: {intent.status}'
            }, status=400)
            
    except Exception as e:
        logger.error(f"Error confirming payment: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_POST
@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhooks for payment events"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError as e:
        return JsonResponse({'error': 'Invalid signature'}, status=400)
    
    # Handle the event
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        # Update your database here
        logger.info(f"Payment succeeded for {payment_intent['id']}")
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        logger.error(f"Payment failed for {payment_intent['id']}")
    
    return JsonResponse({'success': True})


