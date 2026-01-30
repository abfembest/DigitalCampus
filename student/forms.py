from django import forms
from django.contrib.auth.models import User
from .models import (
    AssignmentSubmission, UserProfile, Message
)


class AssignmentSubmissionForm(forms.ModelForm):
    """Form for submitting assignments"""
    class Meta:
        model = AssignmentSubmission
        fields = ['submission_text', 'attachment']
        widgets = {
            'submission_text': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
                'rows': 8,
                'placeholder': 'Enter your submission text here...'
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'
            }),
        }


class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile"""
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
            'placeholder': 'Last Name'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
            'placeholder': 'Email Address'
        })
    )
    
    class Meta:
        model = UserProfile
        fields = ['bio', 'phone', 'city', 'country', 'avatar']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
                'rows': 4,
                'placeholder': 'Tell us about yourself...'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
                'placeholder': 'Phone Number'
            }),
            'city': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
                'placeholder': 'City'
            }),
            'country': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
                'placeholder': 'Country'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
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
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'
        })
    )
    
    class Meta:
        model = Message
        fields = ['recipient', 'subject', 'body']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
                'placeholder': 'Message Subject'
            }),
            'body': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
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
                'class': 'w-4 h-4 text-primary-600'
            }),
            'marketing_emails': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-primary-600'
            }),
        }