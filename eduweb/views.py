from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from .forms import ContactForm
from .models import ContactMessage

def index(request):
    return render(request, 'index.html')

def about(request):
    return render(request, 'about.html')

def apply(request):
    return render(request, 'form.html')

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