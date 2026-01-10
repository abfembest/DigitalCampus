from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from .forms import ContactForm, CourseApplicationForm
from .models import ContactMessage, CourseApplication, CourseApplicationFile
from django.http import JsonResponse
from django.utils import timezone

def index(request):
    return render(request, 'index.html')

def about(request):
    return render(request, 'about.html')

def apply(request):
    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        form = CourseApplicationForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                application = form.save()
                
                # Handle multiple additional files
                additional_files = request.FILES.getlist('additional_files')
                for f in additional_files:
                    CourseApplicationFile.objects.create(application=application, file=f)
                
                # Send emails
                send_application_confirmation_email(application)
                send_application_admin_notification(application)
                
                # Always return JSON for AJAX
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
        else:
            # Format errors for JSON response
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = [str(e) for e in error_list]
            
            return JsonResponse({
                'success': False,
                'errors': errors,
                'error': 'Please correct the errors in the form.'
            }, status=400)
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
            send_admin_email(contact_message)
            send_user_confirmation_email(contact_message)
            messages.success(request, 'Thank you for contacting us! We will get back to you soon.')
            return redirect('index')
        else:
            messages.error(request, 'Please correct the errors below.')
            return render(request, 'index.html', {'form': form})
    else:
        return redirect('index')

def send_admin_email(contact_message):
    """Send notification email to admin"""
    try:
        subject = f'New Contact - {contact_message.get_subject_display()}'
        html_content = f"""
        <html><body style="font-family: Arial, sans-serif;">
            <h2>New Contact Form Submission</h2>
            <p><strong>Name:</strong> {contact_message.name}</p>
            <p><strong>Email:</strong> {contact_message.email}</p>
            <p><strong>Subject:</strong> {contact_message.get_subject_display()}</p>
            <p><strong>Message:</strong><br>{contact_message.message}</p>
        </body></html>
        """
        email = EmailMultiAlternatives(subject=subject, body="New message", 
                                      from_email=settings.DEFAULT_FROM_EMAIL, 
                                      to=[settings.CONTACT_EMAIL])
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        return True
    except Exception as e:
        print(f"Error sending admin email: {str(e)}")
        return False

def send_user_confirmation_email(contact_message):
    """Send confirmation email to user"""
    try:
        subject = 'Thank you for contacting MIU'
        html_content = f"""
        <html><body style="font-family: Arial, sans-serif;">
            <h2>Thank You!</h2>
            <p>Dear <strong>{contact_message.name}</strong>,</p>
            <p>Thank you for contacting Modern International University. We will respond within 1-2 business days.</p>
            <p>Best regards,<br><strong>The MIU Team</strong></p>
        </body></html>
        """
        email = EmailMultiAlternatives(subject=subject, body="Thank you", 
                                      from_email=settings.DEFAULT_FROM_EMAIL, 
                                      to=[contact_message.email])
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        return True
    except Exception as e:
        print(f"Error sending confirmation email: {str(e)}")
        return False

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
            send_admin_email(contact_message)
            send_user_confirmation_email(contact_message)
            
            messages.success(request, 'Thank you for contacting us! We will get back to you soon.')
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
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f4f4f4;">
                    <div style="background-color: #0F2A44; padding: 20px; text-align: center;">
                        <h1 style="color: white; margin: 0;">New Contact Form Submission</h1>
                    </div>
                    <div style="background-color: white; padding: 30px; margin-top: 20px;">
                        <h2 style="color: #0F2A44;">Contact Details</h2>
                        <p><strong>Name:</strong> {contact_message.name}</p>
                        <p><strong>Email:</strong> {contact_message.email}</p>
                        <p><strong>Subject:</strong> {contact_message.get_subject_display()}</p>
                        <h3 style="color: #0F2A44;">Message</h3>
                        <div style="background-color: #f9f9f9; padding: 20px; border-left: 4px solid #1D4ED8;">
                            {contact_message.message}
                        </div>
                    </div>
                </div>
            </body>
        </html>
        """
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=f"New message from {contact_message.name}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.CONTACT_EMAIL],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        return True
    except Exception as e:
        print(f"Error sending admin email: {str(e)}")
        return False

def send_user_confirmation_email(contact_message):
    """Send confirmation email to user"""
    try:
        subject = 'Thank you for contacting MIU'
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f4f4f4;">
                    <div style="background: linear-gradient(135deg, #0F2A44 0%, #1D4ED8 100%); padding: 30px; text-align: center;">
                        <h1 style="color: white; margin: 0;">Thank You!</h1>
                    </div>
                    <div style="background-color: white; padding: 30px; margin-top: 20px;">
                        <p>Dear <strong>{contact_message.name}</strong>,</p>
                        <p>Thank you for contacting Modern International University. We have received your message and will respond within 1-2 business days.</p>
                        <p>Best regards,<br><strong style="color: #0F2A44;">The MIU Team</strong></p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        email = EmailMultiAlternatives(
            subject=subject,
            body="Thank you for contacting us.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[contact_message.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        return True
    except Exception as e:
        print(f"Error sending confirmation email: {str(e)}")
        return False

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

# Additional Pages Views
def research(request):
    """Research page view"""
    return render(request, 'research.html')

def campus_life(request):
    """Campus Life page view"""
    return render(request, 'campus_life.html')

def blog(request):
    """Blog page view"""
    return render(request, 'blog.html')