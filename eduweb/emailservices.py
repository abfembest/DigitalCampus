from django.conf import settings
from django.core.mail import EmailMultiAlternatives, send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse


#######################################################
# EMAIL VERIFICATION - SENT AT SIGNUP
#######################################################
def send_verification_email(request, user):
    """
    Send email verification link to new user at signup.
    
    Trigger: Called in auth_page() view after user creation
    Purpose: Verify user's email address before account activation
    Recipients: New user
    
    Args:
        request: HTTP request object (for building absolute URL)
        user: User object with unverified email
        
    Returns:
        bool: True if email sent successfully, False otherwise
        
    Security: 
        - Token expires in 24 hours
        - One-time use verification token
    """
    try:
        profile = user.profile
        token = profile.verification_token
        current_site = get_current_site(request)
        verification_url = request.build_absolute_uri(
            reverse('eduweb:verify_email', kwargs={'token': str(token)})
        )
        
        subject = 'Verify Your MIU Account'
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; 
                         line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; 
                            padding: 20px; background-color: #f4f4f4;">
                    <div style="background: linear-gradient(135deg, 
                                #840384 0%, #a855f7 100%); 
                                padding: 30px; text-align: center;">
                        <h1 style="color: white; margin: 0;">
                            Welcome to MIU!
                        </h1>
                    </div>
                    <div style="background-color: white; 
                                padding: 30px; margin-top: 20px;">
                        <p style="font-size: 16px;">
                            Dear <strong>
                                {user.get_full_name() or user.username}
                            </strong>,
                        </p>
                        <p>
                            Thank you for creating an account with 
                            Modern International University. Please verify 
                            your email address to complete your registration.
                        </p>
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{verification_url}" 
                               style="display: inline-block; 
                                      padding: 15px 40px; 
                                      background: linear-gradient(135deg, 
                                      #840384 0%, #a855f7 100%); 
                                      color: white; 
                                      text-decoration: none; 
                                      border-radius: 8px; 
                                      font-weight: bold; 
                                      font-size: 16px;">
                                Verify Email Address
                            </a>
                        </div>
                        <p style="font-size: 14px; color: #666;">
                            Or copy and paste this link into your browser:
                        </p>
                        <p style="font-size: 14px; color: #1D4ED8; 
                                  word-break: break-all;">
                            {verification_url}
                        </p>
                        <p style="font-size: 14px; color: #666; 
                                  margin-top: 30px;">
                            This link will expire in 24 hours.
                        </p>
                        <p>
                            Best regards,<br>
                            <strong style="color: #840384;">
                                The MIU Team
                            </strong>
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        text_content = f"""
Welcome to Modern International University!

Dear {user.get_full_name() or user.username},

Thank you for creating an account. Please verify your email address by 
clicking the link below:

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


#######################################################
# VERIFICATION SUCCESS - SENT AFTER EMAIL VERIFICATION
#######################################################
def send_verification_success_email(user):
    """
    Send welcome email after successful email verification.
    
    Trigger: Called in verify_email() view after verification success
    Purpose: Confirm successful verification and guide next steps
    Recipients: Newly verified user
    
    Args:
        user: User object with verified email
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject = 'Email Verified - Welcome to MIU!'
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; 
                         line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; 
                            padding: 20px; background-color: #f4f4f4;">
                    <div style="background: linear-gradient(135deg, 
                                #10b981 0%, #059669 100%); 
                                padding: 30px; text-align: center;">
                        <h1 style="color: white; margin: 0;">
                            ✓ Email Verified!
                        </h1>
                    </div>
                    <div style="background-color: white; 
                                padding: 30px; margin-top: 20px;">
                        <p style="font-size: 16px;">
                            Dear <strong>
                                {user.get_full_name() or user.username}
                            </strong>,
                        </p>
                        <p>
                            Congratulations! Your email has been successfully 
                            verified. Your account is now active.
                        </p>
                        
                        <div style="background-color: #d1fae515; 
                                    padding: 20px; border-radius: 8px; 
                                    margin: 25px 0; 
                                    border-left: 4px solid #10b981;">
                            <h3 style="color: #10b981; margin-top: 0;">
                                Next Steps
                            </h3>
                            <ol style="margin: 10px 0; padding-left: 20px;">
                                <li>Log in to your account</li>
                                <li>Complete your application</li>
                                <li>Upload required documents</li>
                                <li>Track your application status</li>
                            </ol>
                        </div>
                        
                        <p>
                            If you have any questions, please contact us at 
                            <a href="mailto:{settings.CONTACT_EMAIL}">
                                {settings.CONTACT_EMAIL}
                            </a>
                        </p>
                        
                        <p>
                            Best regards,<br>
                            <strong style="color: #840384;">
                                The MIU Team
                            </strong>
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        text_content = f"""
Email Verified - Welcome to MIU!

Dear {user.get_full_name() or user.username},

Congratulations! Your email has been successfully verified. 
Your account is now active.

Next Steps:
1. Log in to your account
2. Complete your application
3. Upload required documents
4. Track your application status

If you have any questions, please contact us at {settings.CONTACT_EMAIL}

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
        print(f"Error sending verification success email: {str(e)}")
        return False


#######################################################
# APPLICATION SUBMISSION - SENT TO APPLICANT
#######################################################
def send_application_confirmation_email(application):
    """
    Send confirmation email when application is submitted.
    
    Trigger: Called in submit_application() view
    Purpose: Confirm receipt of application
    Recipients: Applicant
    
    Args:
        application: CourseApplication object
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject = f'Application Received - {application.application_id}'
        
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
                            Application Received!
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
                        <p>
                            Thank you for applying to Modern International 
                            University. We have received your application.
                        </p>
                        <div style="background-color: #E6F0FF; 
                                    padding: 20px; border-radius: 8px; 
                                    margin: 25px 0;">
                            <h3 style="color: #0F2A44; margin-top: 0;">
                                Application Details
                            </h3>
                            <p>
                                <strong>Application ID:</strong> 
                                {application.application_id}
                            </p>
                            <p>
                                <strong>Program:</strong> 
                                {application.course.name}
                            </p>
                            <p>
                                <strong>Degree Level:</strong> 
                                {application.course.get_degree_level_display()}
                            </p>
                            <p>
                                <strong>Faculty:</strong> 
                                {application.course.faculty.name}
                            </p>
                            <p>
                                <strong>Submission Date:</strong> 
                                {application.submitted_at.strftime('%B %d, %Y') 
                                 if application.submitted_at else 'Pending'}
                            </p>
                        </div>
                        <p>
                            Our admissions team will review your application 
                            and contact you within 5-7 business days.
                        </p>
                        <p>
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


#######################################################
# APPLICATION SUBMISSION - SENT TO ADMIN
#######################################################
def send_application_admin_notification(application):
    """
    Send notification to admin when new application submitted.
    
    Trigger: Called in submit_application() view
    Purpose: Alert admin team of new application requiring review
    Recipients: Admin team (settings.CONTACT_EMAIL)
    
    Args:
        application: CourseApplication object
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject = f'New Application - {application.application_id}'
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>New Course Application Received</h2>
                <p>
                    <strong>Application ID:</strong> 
                    {application.application_id}
                </p>
                <p>
                    <strong>Name:</strong> 
                    {application.get_full_name()}
                </p>
                <p>
                    <strong>Email:</strong> 
                    {application.email}
                </p>
                <p>
                    <strong>Course:</strong> 
                    {application.course.name} ({application.course.code})
                </p>
                <p>
                    <strong>Degree Level:</strong> 
                    {application.course.get_degree_level_display()}
                </p>
                <p>
                    <strong>Faculty:</strong> 
                    {application.course.faculty.name}
                </p>
                <p>
                    <strong>Intake:</strong> 
                    {application.intake.get_intake_period_display()} 
                    {application.intake.year}
                </p>
                <p>
                    <strong>Study Mode:</strong> 
                    {application.get_study_mode_display()}
                </p>
                <p>
                    <strong>Submitted:</strong> 
                    {application.submitted_at.strftime('%Y-%m-%d %H:%M:%S') 
                     if application.submitted_at else 'Draft'}
                </p>
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


#######################################################
# DOCUMENT UPLOAD SUCCESS - SENT TO APPLICANT
#######################################################
def send_document_upload_confirmation(application, documents):
    """
    Send confirmation email when documents uploaded successfully.
    
    Trigger: Called after upload(s) in upload_application_file() view
    Purpose: Confirm receipt of uploaded document(s)
    Recipients: Applicant
    
    Args:
        application: CourseApplication object
        documents: Single ApplicationDocument or list of ApplicationDocument objects
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Ensure documents is a list
        if not isinstance(documents, list):
            documents = [documents]
        
        # Count documents
        doc_count = len(documents)
        
        # Build subject
        if doc_count == 1:
            subject = (
                f'Document Uploaded - {application.application_id}'
            )
        else:
            subject = (
                f'{doc_count} Documents Uploaded - '
                f'{application.application_id}'
            )
        
        # Build document list HTML
        docs_html = ""
        for idx, doc in enumerate(documents, 1):
            docs_html += f"""
            <div style="background-color: #f9fafb; 
                        padding: 15px; 
                        border-radius: 6px; 
                        margin-bottom: 10px;">
                <p style="margin: 5px 0;">
                    <strong>Document {idx}:</strong>
                </p>
                <p style="margin: 5px 0; padding-left: 15px;">
                    <strong>Type:</strong> 
                    {doc.get_file_type_display()}
                </p>
                <p style="margin: 5px 0; padding-left: 15px;">
                    <strong>File:</strong> 
                    {doc.original_filename}
                </p>
                <p style="margin: 5px 0; padding-left: 15px;">
                    <strong>Size:</strong> 
                    {doc.get_file_size_display()}
                </p>
                <p style="margin: 5px 0; padding-left: 15px;">
                    <strong>Uploaded:</strong> 
                    {doc.uploaded_at.strftime('%B %d, %Y at %I:%M %p')}
                </p>
            </div>
            """
        
        # Build document list text
        docs_text = ""
        for idx, doc in enumerate(documents, 1):
            docs_text += f"""
Document {idx}:
  Type: {doc.get_file_type_display()}
  File: {doc.original_filename}
  Size: {doc.get_file_size_display()}
  Uploaded: {doc.uploaded_at.strftime('%B %d, %Y at %I:%M %p')}

"""
        
        # Build HTML email
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; 
                         line-height: 1.6; 
                         color: #333;">
                <div style="max-width: 600px; 
                            margin: 0 auto; 
                            padding: 20px; 
                            background-color: #f4f4f4;">
                    <div style="background: linear-gradient(135deg, 
                                #10b981 0%, #059669 100%); 
                                padding: 30px; 
                                text-align: center;">
                        <h1 style="color: white; margin: 0;">
                            📄 {'Documents' if doc_count > 1 else 'Document'} Uploaded
                        </h1>
                    </div>
                    <div style="background-color: white; 
                                padding: 30px; 
                                margin-top: 20px;">
                        <p style="font-size: 16px;">
                            Dear <strong>
                                {application.first_name} 
                                {application.last_name}
                            </strong>,
                        </p>
                        <p>
                            Your {'documents have' if doc_count > 1 else 'document has'} 
                            been successfully uploaded to your application.
                        </p>
                        
                        <div style="background-color: #E6F0FF; 
                                    padding: 20px; 
                                    border-radius: 8px; 
                                    margin: 25px 0;">
                            <h3 style="color: #0F2A44; margin-top: 0;">
                                Upload Summary
                            </h3>
                            <p>
                                <strong>Application ID:</strong> 
                                {application.application_id}
                            </p>
                            <p>
                                <strong>Total Documents:</strong> 
                                {doc_count}
                            </p>
                        </div>
                        
                        <h3 style="color: #0F2A44;">
                            {'Documents' if doc_count > 1 else 'Document'} Uploaded
                        </h3>
                        {docs_html}
                        
                        <p>
                            You can continue uploading additional documents 
                            or submit your application when ready.
                        </p>
                        
                        <p>
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
        
        # Build text email
        text_content = f"""
{'Documents' if doc_count > 1 else 'Document'} Uploaded Successfully

Dear {application.first_name} {application.last_name},

Your {'documents have' if doc_count > 1 else 'document has'} been 
successfully uploaded to your application.

Upload Summary:
- Application ID: {application.application_id}
- Total Documents: {doc_count}

{'Documents' if doc_count > 1 else 'Document'} Uploaded:
{docs_text}

You can continue uploading additional documents or submit your 
application when ready.

Best regards,
The MIU Admissions Team
        """
        
        # Send email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[application.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        return True
        
    except Exception as e:
        print(
            f"Error sending document confirmation email: {str(e)}"
        )
        return False


#######################################################
# DOCUMENT UPLOAD - SENT TO ADMIN
#######################################################
def send_document_upload_admin_notification(application, documents):
    """
    Notify admin when applicant uploads document(s).
    
    Trigger: Called after upload(s) in upload_application_file() view
    Purpose: Alert admin of new documents requiring verification
    Recipients: Admin team (settings.CONTACT_EMAIL)
    
    Args:
        application: CourseApplication object
        documents: Single ApplicationDocument or list of ApplicationDocument objects
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Ensure documents is a list
        if not isinstance(documents, list):
            documents = [documents]
        
        # Count documents
        doc_count = len(documents)
        
        # Build subject
        if doc_count == 1:
            subject = (
                f'New Document Uploaded - '
                f'{application.application_id}'
            )
        else:
            subject = (
                f'{doc_count} New Documents Uploaded - '
                f'{application.application_id}'
            )
        
        # Build document table rows
        docs_html = ""
        for idx, doc in enumerate(documents, 1):
            docs_html += f"""
            <tr>
                <td style="padding: 10px; 
                           border: 1px solid #ddd;">
                    {idx}
                </td>
                <td style="padding: 10px; 
                           border: 1px solid #ddd;">
                    {doc.get_file_type_display()}
                </td>
                <td style="padding: 10px; 
                           border: 1px solid #ddd;">
                    {doc.original_filename}
                </td>
                <td style="padding: 10px; 
                           border: 1px solid #ddd;">
                    {doc.get_file_size_display()}
                </td>
                <td style="padding: 10px; 
                           border: 1px solid #ddd;">
                    {doc.uploaded_at.strftime('%Y-%m-%d %H:%M:%S')}
                </td>
            </tr>
            """
        
        # Build HTML email
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>
                    {'New Documents Uploaded' if doc_count > 1 else 'New Document Uploaded'}
                </h2>
                <p>
                    An applicant has uploaded 
                    {doc_count} 
                    {'documents' if doc_count > 1 else 'document'}.
                </p>
                
                <h3>Applicant Information</h3>
                <table style="border-collapse: collapse; 
                              width: 100%; 
                              max-width: 600px;">
                    <tr>
                        <td style="padding: 8px; 
                                   font-weight: bold; 
                                   width: 150px;">
                            Name:
                        </td>
                        <td style="padding: 8px;">
                            {application.get_full_name()}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; font-weight: bold;">
                            Email:
                        </td>
                        <td style="padding: 8px;">
                            {application.email}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; font-weight: bold;">
                            Application ID:
                        </td>
                        <td style="padding: 8px;">
                            {application.application_id}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; font-weight: bold;">
                            Course:
                        </td>
                        <td style="padding: 8px;">
                            {application.course.name}
                        </td>
                    </tr>
                </table>
                
                <h3>
                    {'Documents' if doc_count > 1 else 'Document'} Uploaded
                </h3>
                <table style="border-collapse: collapse; 
                              width: 100%; 
                              max-width: 800px;">
                    <thead>
                        <tr style="background-color: #f2f2f2;">
                            <th style="padding: 10px; 
                                       border: 1px solid #ddd; 
                                       text-align: left;">
                                #
                            </th>
                            <th style="padding: 10px; 
                                       border: 1px solid #ddd; 
                                       text-align: left;">
                                Type
                            </th>
                            <th style="padding: 10px; 
                                       border: 1px solid #ddd; 
                                       text-align: left;">
                                Filename
                            </th>
                            <th style="padding: 10px; 
                                       border: 1px solid #ddd; 
                                       text-align: left;">
                                Size
                            </th>
                            <th style="padding: 10px; 
                                       border: 1px solid #ddd; 
                                       text-align: left;">
                                Uploaded
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                        {docs_html}
                    </tbody>
                </table>
                
                <p style="margin-top: 20px;">
                    Please review the 
                    {'documents' if doc_count > 1 else 'document'} 
                    in the admin panel.
                </p>
            </body>
        </html>
        """
        
        # Build text email
        text_body = (
            f"{'New documents' if doc_count > 1 else 'New document'} "
            f"uploaded by {application.get_full_name()} "
            f"for application {application.application_id}"
        )
        
        # Send email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.CONTACT_EMAIL],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        return True
        
    except Exception as e:
        print(
            f"Error sending document admin notification: {str(e)}"
        )
        return False

#######################################################
# CONTACT FORM - SENT TO ADMIN
#######################################################
def send_admin_email(contact_message):
    """
    Send contact form submission to admin.
    
    Trigger: Called in contact_submit() view
    Purpose: Forward user inquiry to admin team
    Recipients: Admin team (settings.CONTACT_EMAIL)
    
    Args:
        contact_message: ContactMessage object
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject = (
            f'New Contact Form Submission - '
            f'{contact_message.get_subject_display()}'
        )
        
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
            <body style="font-family: Arial, sans-serif; 
                         line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; 
                            padding: 20px; background-color: #f4f4f4;">
                    <div style="background: linear-gradient(135deg, 
                                #0F2A44 0%, #1D4ED8 100%); 
                                padding: 30px; text-align: center;">
                        <h1 style="color: white; margin: 0;">
                            New Contact Form Submission
                        </h1>
                    </div>
                    <div style="background-color: white; 
                                padding: 30px; margin-top: 20px;">
                        <h3 style="color: #0F2A44;">
                            Contact Information
                        </h3>
                        <p>
                            <strong>Name:</strong> 
                            {contact_message.name}
                        </p>
                        <p>
                            <strong>Email:</strong> 
                            {contact_message.email}
                        </p>
                        <p>
                            <strong>Subject:</strong> 
                            {contact_message.get_subject_display()}
                        </p>
                        
                        <h3 style="color: #0F2A44; margin-top: 30px;">
                            Message
                        </h3>
                        <div style="background-color: #f9fafb; 
                                    padding: 15px; border-radius: 5px; 
                                    border-left: 3px solid #1D4ED8;">
                            <p style="margin: 0; white-space: pre-wrap;">
                                {contact_message.message}
                            </p>
                        </div>
                        
                        <p style="margin-top: 30px; 
                                  font-size: 14px; color: #666;">
                            Submitted at: 
                            {contact_message.created_at.strftime('%B %d, %Y at %I:%M %p')}
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
            to=[settings.CONTACT_EMAIL],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        
        print(
            f"✅ Admin notification sent successfully to "
            f"{settings.CONTACT_EMAIL}"
        )
        return True
        
    except Exception as e:
        print(f"❌ Error sending admin email: {str(e)}")
        return False


#######################################################
# CONTACT FORM - SENT TO USER
#######################################################
def send_user_confirmation_email(contact_message):
    """
    Send confirmation email to user who submitted contact form.
    
    Trigger: Called in contact_submit() view
    Purpose: Acknowledge receipt of contact form submission
    Recipients: Contact form submitter
    
    Args:
        contact_message: ContactMessage object
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject = (
            'Thank you for contacting MIU - '
            'We received your message'
        )
        
        text_content = f"""
Dear {contact_message.name},

Thank you for contacting Modern International University (MIU). 
We have received your message and will respond within 1-2 business days.

Your Message Details:
Subject: {contact_message.get_subject_display()}
Message: {contact_message.message}

If you have any urgent questions, please call us at +1 (555) 123-4567.

Best regards,
The MIU Admissions Team
        """
        
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
                            Thank You for Contacting Us!
                        </h1>
                    </div>
                    <div style="background-color: white; 
                                padding: 30px; margin-top: 20px;">
                        <p style="font-size: 16px; margin-bottom: 20px;">
                            Dear <strong>{contact_message.name}</strong>,
                        </p>
                        <p style="font-size: 16px; margin-bottom: 20px;">
                            Thank you for reaching out to Modern International 
                            University. We have received your message and our 
                            team will review it carefully.
                        </p>
                        <div style="background-color: #E6F0FF; 
                                    padding: 20px; border-radius: 8px; 
                                    margin: 25px 0;">
                            <h3 style="color: #0F2A44; margin-top: 0;">
                                Your Message Summary
                            </h3>
                            <p>
                                <strong>Subject:</strong> 
                                {contact_message.get_subject_display()}
                            </p>
                        </div>
                        <p style="font-size: 16px;">
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
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[contact_message.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        
        print(
            f"✅ Confirmation email sent successfully to "
            f"{contact_message.email}"
        )
        return True
        
    except Exception as e:
        print(f"❌ Error sending user confirmation email: {str(e)}")
        return False


#######################################################
# PAYMENT CONFIRMATION
#######################################################
def send_payment_emails(payment):
    """
    Send payment confirmation to user and vendor.
    
    Trigger: Called after successful payment processing
    Purpose: Confirm payment receipt
    Recipients: User and vendor
    
    Args:
        payment: ApplicationPayment object
        
    Returns:
        None (sends two separate emails)
        
    Note: Currently sends plain text emails
    """
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


#######################################################
# ADMISSION ACCEPTANCE
#######################################################
def send_admission_acceptance_email(application):
    """
    Send confirmation when student accepts admission offer.
    
    Trigger: Called in accept_admission() view
    Purpose: Confirm admission acceptance and provide next steps
    Recipients: Student who accepted admission
    
    Args:
        application: CourseApplication object with admission_accepted=True
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject = (
            f'Admission Accepted - {application.admission_number}'
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
                            🎓 Welcome to MIU!
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
                                Admission Acceptance Confirmed!
                            </h3>
                            <p>
                                <strong>Admission Number:</strong> 
                                {application.admission_number}
                            </p>
                            <p>
                                <strong>Program:</strong> 
                                {application.course.name}
                            </p>
                        </div>
                        
                        <h4>Next Steps:</h4>
                        <ol>
                            <li>Department approval is in progress</li>
                            <li>
                                You will receive portal access 
                                once approved
                            </li>
                            <li>
                                Keep this admission number for 
                                all correspondence
                            </li>
                        </ol>
                        
                        <p style="margin-top: 30px;">
                            Welcome aboard!<br>
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
            body=f"Admission Accepted - {application.admission_number}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[application.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        return True
        
    except Exception as e:
        print(f"Error sending acceptance email: {str(e)}")
        return False