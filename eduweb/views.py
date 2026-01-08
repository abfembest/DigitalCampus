from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from .forms import ContactForm, CourseApplicationForm
from .models import ContactMessage, CourseApplication, CourseApplicationFile
from django.views.decorators.http import require_POST
from django.http import JsonResponse
import json
from django.utils import timezone

def index(request):
    return render(request, 'index.html')

def about(request):
    return render(request, 'about.html')

# REPLACE the apply function

def apply(request):
    if request.method == 'POST':
        # Include request.FILES
        form = CourseApplicationForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                # 1. Save the main application data and individual files
                application = form.save(commit=False)
                
                # Manually assign the single files from the form to the model
                if request.FILES.get('transcripts_file'):
                    application.transcripts_file = request.FILES['transcripts_file']
                if request.FILES.get('english_proficiency_file'):
                    application.english_proficiency_file = request.FILES['english_proficiency_file']
                if request.FILES.get('personal_statement_file'):
                    application.personal_statement_file = request.FILES['personal_statement_file']
                if request.FILES.get('cv_file'):
                    application.cv_file = request.FILES['cv_file']
                
                application.save()
                
                # 2. Handle the MULTIPLE additional files
                additional_files = request.FILES.getlist('additional_files')
                docs_meta = {
                    'transcripts': application.transcripts_file.name if application.transcripts_file else None,
                    'english': application.english_proficiency_file.name if application.english_proficiency_file else None,
                    'statement': application.personal_statement_file.name if application.personal_statement_file else None,
                    'cv': application.cv_file.name if application.cv_file else None,
                    'additional': []
                }

                for f in additional_files:
                    # Create a record for each file in the extra model
                    CourseApplicationFile.objects.create(application=application, file=f)
                    docs_meta['additional'].append(f.name)
                
                # Update the metadata JSON
                application.documents_uploaded = docs_meta
                application.save()
                
                # 3. Success logic
                send_application_confirmation_email(application)
                send_application_admin_notification(application)
                
                request.session['application_success'] = {
                    'application_id': application.application_id,
                    'name': application.get_full_name(),
                }
                return redirect('application_success')
                
            except Exception as e:
                messages.error(request, f'Error submitting application: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CourseApplicationForm()
    
    return render(request, 'form.html', {'form': form})

def application_success(request):
    """Display application success page"""
    success_data = request.session.get('application_success')
    
    if not success_data:
        return redirect('apply')
    
    # Clear session data after retrieving
    del request.session['application_success']
    
    return render(request, 'application_success.html', success_data)

@require_POST
def application_submit(request):
    """Handle course application form submission via AJAX"""
    try:
        data = json.loads(request.body)
        
        # Parse academic history
        academic_history = []
        education_levels = data.get('educationLevel', [])
        if not isinstance(education_levels, list):
            education_levels = [education_levels] if education_levels else []
        
        institutions = data.get('institution', [])
        if not isinstance(institutions, list):
            institutions = [institutions] if institutions else []
            
        for i in range(len(education_levels)):
            if education_levels[i]:
                academic_history.append({
                    'education_level': education_levels[i],
                    'institution': institutions[i] if i < len(institutions) else '',
                    'field_of_study': data.get('fieldOfStudy', [])[i] if isinstance(data.get('fieldOfStudy', []), list) and i < len(data.get('fieldOfStudy', [])) else '',
                    'graduation_year': data.get('graduationYear', [])[i] if isinstance(data.get('graduationYear', []), list) and i < len(data.get('graduationYear', [])) else '',
                    'gpa': data.get('gpa', [])[i] if isinstance(data.get('gpa', []), list) and i < len(data.get('gpa', [])) else '',
                })
        
        # Get English proficiency data
        english_proficiency = data.get('englishProficiency', '')
        english_score = ''
        if english_proficiency == 'toefl':
            english_score = data.get('toeflScore', '')
        elif english_proficiency == 'ielts':
            english_score = data.get('ieltsScore', '')
        elif english_proficiency == 'other':
            english_score = data.get('otherTest', '')
        
        # Create application
        application = CourseApplication.objects.create(
            first_name=data.get('firstName', ''),
            last_name=data.get('lastName', ''),
            email=data.get('email', ''),
            phone=data.get('phone', ''),
            date_of_birth=data.get('dob', ''),
            country=data.get('country', ''),
            gender=data.get('gender', ''),
            address=data.get('address', ''),
            academic_history=academic_history,
            english_proficiency=english_proficiency,
            english_score=english_score,
            additional_qualifications=data.get('additionalQualifications', ''),
            program=data.get('program', ''),
            degree_level=data.get('degreeLevel', ''),
            study_mode=data.get('studyMode', ''),
            intake=data.get('intake', ''),
            scholarship=data.get('scholarship', False),
            referral_source=data.get('referralSource', ''),
            documents_uploaded=data.get('uploadedFiles', {}),
            submitted=True,
            submission_date=timezone.now()
        )
        
        # Send confirmation emails
        send_application_confirmation_email(application)
        send_application_admin_notification(application)
        
        return JsonResponse({
            'success': True,
            'application_id': application.application_id,
            'message': 'Application submitted successfully!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    
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

def contact_submit(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Save the contact message
            contact_message = form.save()
            
            # Send email to admin
            admin_email_sent = send_admin_email(contact_message)
            
            # Send confirmation email to user
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
        
        # Plain text version
        text_content = f"""
New contact form submission from MIU website:

Name: {contact_message.name}
Email: {contact_message.email}
Subject: {contact_message.get_subject_display()}

Message:
{contact_message.message}

Submitted at: {contact_message.created_at.strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        # HTML version
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
                    <div style="text-align: center; margin-top: 20px; color: #666; font-size: 12px;">
                        <p>This email was sent from the MIU Contact Form</p>
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
        import traceback
        traceback.print_exc()
        return False

def send_user_confirmation_email(contact_message):
    """Send confirmation email to user"""
    try:
        subject = 'Thank you for contacting MIU - We received your message'
        
        # Plain text version
        text_content = f"""
Dear {contact_message.name},

Thank you for contacting Modern International University (MIU). We have received your message and will respond within 1-2 business days.

Your Message Details:
Subject: {contact_message.get_subject_display()}
Message: {contact_message.message}

If you have any urgent questions, please call us at +1 (555) 123-4567.

Best regards,
The MIU Admissions Team

Modern International University
123 University Avenue
Knowledge City, KC 10101
Website: www.miu.edu
        """
        
        # HTML version
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f4f4f4;">
                    <div style="background: linear-gradient(135deg, #0F2A44 0%, #1D4ED8 100%); padding: 30px; text-align: center;">
                        <div style="width: 60px; height: 60px; background-color: white; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 15px;">
                            <span style="color: #0F2A44; font-weight: bold; font-size: 24px;">MIU</span>
                        </div>
                        <h1 style="color: white; margin: 0;">Thank You for Contacting Us!</h1>
                    </div>
                    <div style="background-color: white; padding: 30px; margin-top: 20px;">
                        <p style="font-size: 16px; margin-bottom: 20px;">Dear <strong>{contact_message.name}</strong>,</p>
                        <p style="font-size: 16px; margin-bottom: 20px;">
                            Thank you for reaching out to Modern International University. We have received your message 
                            and our team will review it carefully.
                        </p>
                        <div style="background-color: #E6F0FF; padding: 20px; border-radius: 8px; margin: 25px 0;">
                            <h3 style="color: #0F2A44; margin-top: 0; margin-bottom: 15px;">Your Message Summary</h3>
                            <table style="width: 100%;">
                                <tr>
                                    <td style="padding: 8px 0; font-weight: bold; color: #0F2A44;">Subject:</td>
                                    <td style="padding: 8px 0;">{contact_message.get_subject_display()}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px 0; font-weight: bold; color: #0F2A44; vertical-align: top;">Message:</td>
                                    <td style="padding: 8px 0;">{contact_message.message[:150]}{'...' if len(contact_message.message) > 150 else ''}</td>
                                </tr>
                            </table>
                        </div>
                        <div style="background-color: #F0F7FF; padding: 20px; border-left: 4px solid #1D4ED8; margin: 25px 0;">
                            <p style="margin: 0; color: #0F2A44;">
                                <strong>Expected Response Time:</strong> 1-2 business days<br>
                                <strong>Urgent Inquiries:</strong> +1 (555) 123-4567
                            </p>
                        </div>
                        <p style="font-size: 16px; margin-bottom: 10px;">
                            We look forward to assisting you on your educational journey!
                        </p>
                        <p style="font-size: 16px; margin-bottom: 0;">
                            Best regards,<br>
                            <strong style="color: #0F2A44;">The MIU Admissions Team</strong>
                        </p>
                    </div>
                    <div style="background-color: white; padding: 20px; margin-top: 20px; text-align: center; border-top: 3px solid #1D4ED8;">
                        <p style="margin: 0 0 10px 0; color: #0F2A44; font-weight: bold;">Modern International University</p>
                        <p style="margin: 0; color: #666; font-size: 14px;">
                            123 University Avenue, Knowledge City, KC 10101<br>
                            info@miu.edu | +1 (555) 123-4567 | www.miu.edu
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
        import traceback
        traceback.print_exc()
        return False