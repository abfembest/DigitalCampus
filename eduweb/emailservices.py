from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse



#######################################################
# SENDING ACOUNT VERIFICATION EMAIL TO A USER AT SIGNUP
#######################################################
def send_verification_email(request, user):
    """Send email verification link to user"""
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


