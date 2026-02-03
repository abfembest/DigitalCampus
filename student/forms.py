from django import forms
from django.contrib.auth.models import User
from eduweb.models import (
    AssignmentSubmission, UserProfile, Message
)


class AssignmentSubmissionForm(forms.ModelForm):
    """Form for submitting assignments with validation"""
    
    class Meta:
        model = AssignmentSubmission
        fields = ['submission_text', 'attachment']
        widgets = {
            'submission_text': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'rows': 8,
                'placeholder': 'Enter your submission text here...',
                'required': True,
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'accept': '.pdf,.doc,.docx,.txt,.zip'
            }),
        }
    
    def clean_submission_text(self):
        """Validate submission text"""
        text = self.cleaned_data.get('submission_text', '')
        if not text or text.strip() == '':
            raise forms.ValidationError(
                'Submission text is required and cannot be empty.'
            )
        if len(text.strip()) < 10:
            raise forms.ValidationError(
                'Submission text must be at least 10 characters long.'
            )
        return text.strip()
    
    def clean_attachment(self):
        """Validate file attachment"""
        attachment = self.cleaned_data.get('attachment')
        if attachment:
            # Check file size (10MB max)
            if attachment.size > 10 * 1024 * 1024:
                raise forms.ValidationError(
                    'File size cannot exceed 10MB.'
                )
            
            # Check file extension
            allowed_extensions = ['pdf', 'doc', 'docx', 'txt', 'zip']
            ext = attachment.name.split('.')[-1].lower()
            if ext not in allowed_extensions:
                raise forms.ValidationError(
                    f'File type not allowed. Accepted: {", ".join(allowed_extensions)}'
                )
        
        return attachment


class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile"""
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
            'placeholder': 'Last Name'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
            'placeholder': 'Email Address'
        })
    )
    
    class Meta:
        model = UserProfile
        fields = ['bio', 'phone', 'city', 'country', 'avatar']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'rows': 4,
                'placeholder': 'Tell us about yourself...'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'placeholder': 'Phone Number'
            }),
            'city': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'placeholder': 'City'
            }),
            'country': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'placeholder': 'Country'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'accept': 'image/*'
            }),
        }


class MessageComposeForm(forms.ModelForm):
    """Form for composing messages"""
    recipient = forms.ModelChoiceField(
        queryset=User.objects.filter(
            profile__role__in=['instructor', 'admin']
        ),
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent'
        })
    )
    
    class Meta:
        model = Message
        fields = ['recipient', 'subject', 'body']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'placeholder': 'Message Subject'
            }),
            'body': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'rows': 6,
                'placeholder': 'Type your message here...'
            }),
        }


class SettingsForm(forms.ModelForm):
    """Form for account settings"""
    class Meta:
        model = UserProfile
        fields = ['email_notifications', 'marketing_emails']
        widgets = {
            'email_notifications': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-primary-600 focus:ring-2 focus:ring-primary-500'
            }),
            'marketing_emails': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-primary-600 focus:ring-2 focus:ring-primary-500'
            }),
        }