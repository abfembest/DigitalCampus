from django import forms
from .models import ContactMessage, CourseApplication
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re

class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-950 focus:ring-2 focus:ring-purple-200 transition-all',
            'placeholder': 'your.email@example.com',
            'autocomplete': 'email'
        })
    )
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-950 focus:ring-2 focus:ring-purple-200 transition-all',
            'placeholder': 'John',
            'autocomplete': 'given-name'
        })
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-950 focus:ring-2 focus:ring-purple-200 transition-all',
            'placeholder': 'Smith',
            'autocomplete': 'family-name'
        })
    )
    captcha = forms.IntegerField(
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-950 focus:ring-2 focus:ring-purple-200 transition-all',
            'placeholder': 'Enter the result',
            'autocomplete': 'off',
            'type': 'number'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-950 focus:ring-2 focus:ring-purple-200 transition-all',
                'placeholder': 'Choose a username',
                'autocomplete': 'username'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.captcha_answer = kwargs.pop('captcha_answer', None)
        super().__init__(*args, **kwargs)
        
        self.fields['password1'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-950 focus:ring-2 focus:ring-purple-200 transition-all',
            'placeholder': 'Create a strong password',
            'autocomplete': 'new-password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-950 focus:ring-2 focus:ring-purple-200 transition-all',
            'placeholder': 'Confirm your password',
            'autocomplete': 'new-password'
        })
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('This email address is already registered.')
        return email
    
    def clean_captcha(self):
        captcha = self.cleaned_data.get('captcha')
        if self.captcha_answer is None:
            raise ValidationError('Captcha session expired. Please refresh the page.')
        
        try:
            captcha_int = int(captcha) if captcha is not None else None
            answer_int = int(self.captcha_answer) if self.captcha_answer is not None else None
            
            if captcha_int != answer_int:
                raise ValidationError('Incorrect answer. Please try again.')
        except (ValueError, TypeError):
            raise ValidationError('Invalid captcha answer format.')
        
        return captcha


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-950 focus:ring-2 focus:ring-purple-200 transition-all',
            'placeholder': 'Enter your username or email',
            'autocomplete': 'username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-950 focus:ring-2 focus:ring-purple-200 transition-all',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password'
        })
    )
    captcha = forms.IntegerField(
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-950 focus:ring-2 focus:ring-purple-200 transition-all',
            'placeholder': 'Enter the result',
            'autocomplete': 'off',
            'type': 'number'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.captcha_answer = kwargs.pop('captcha_answer', None)
        super().__init__(*args, **kwargs)
    
    def clean_captcha(self):
        captcha = self.cleaned_data.get('captcha')
        if self.captcha_answer is None:
            raise ValidationError('Captcha session expired. Please refresh the page.')
        
        try:
            captcha_int = int(captcha) if captcha is not None else None
            answer_int = int(self.captcha_answer) if self.captcha_answer is not None else None
            
            if captcha_int != answer_int:
                raise ValidationError('Incorrect answer. Please try again.')
        except (ValueError, TypeError):
            raise ValidationError('Invalid captcha answer format.')
        
        return captcha


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full p-4 border border-gray-300 rounded-lg focus:border-primary-950 focus:ring-2 focus:ring-purple-200 transition',
                'placeholder': 'John Smith',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full p-4 border border-gray-300 rounded-lg focus:border-primary-950 focus:ring-2 focus:ring-purple-200 transition',
                'placeholder': 'john@example.com',
                'required': True
            }),
            'subject': forms.Select(attrs={
                'class': 'w-full p-4 border border-gray-300 rounded-lg focus:border-primary-950 focus:ring-2 focus:ring-purple-200 transition bg-white'
            }),
            'message': forms.Textarea(attrs={
                'class': 'w-full p-4 border border-gray-300 rounded-lg focus:border-primary-950 focus:ring-2 focus:ring-purple-200 transition',
                'placeholder': "I'm interested in learning more about...",
                'rows': 4,
                'required': True
            }),
        }


class CourseApplicationForm(forms.ModelForm):    
    # English proficiency
    english_proficiency_type = forms.ChoiceField(
        required=True,
        choices=[
            ('toefl', 'TOEFL'),
            ('ielts', 'IELTS'),
            ('other', 'Other'),
            ('native', 'Native Speaker'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'mr-2 h-5 w-5'})
    )
    toefl_score = forms.CharField(
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'w-20 px-2 py-1 border border-gray-300 rounded',
            'placeholder': 'Score'
        })
    )
    ielts_score = forms.CharField(
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'w-20 px-2 py-1 border border-gray-300 rounded',
            'placeholder': 'Score'
        })
    )
    other_test = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-32 px-2 py-1 border border-gray-300 rounded',
            'placeholder': 'Test name'
        })
    )
    
    # File uploads
    transcripts_file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-purple-500',
            'accept': '.pdf,.doc,.docx,.jpg,.png'
        })
    )
    english_proficiency_file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-purple-500',
            'accept': '.pdf,.doc,.docx,.jpg,.png'
        })
    )
    personal_statement_file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-purple-500',
            'accept': '.pdf,.doc,.docx'
        })
    )
    cv_file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-purple-500',
            'accept': '.pdf,.doc,.docx'
        })
    )
    
    # Declarations
    declaration = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'mr-3 h-5 w-5'})
    )
    privacy = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'mr-3 h-5 w-5'})
    )
    
    class Meta:
        model = CourseApplication
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'date_of_birth',
            'country', 'gender', 'address', 'additional_qualifications',
            'program', 'degree_level', 'study_mode', 'intake', 'scholarship',
            'referral_source'
        ]
        
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all',
                'placeholder': 'John'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all',
                'placeholder': 'Smith'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all',
                'placeholder': 'john@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all',
                'placeholder': '+1 (555) 123-4567'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all'
            }),
            'country': forms.Select(attrs={
                'class': 'w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all bg-white'
            }, choices=[('', '-- Select Country --')] + CourseApplication.COUNTRY_CHOICES),
            'gender': forms.Select(attrs={
                'class': 'w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all bg-white'
            }),
            'address': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all',
                'placeholder': 'Enter your full address'
            }),
            'additional_qualifications': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all',
                'placeholder': 'List any certifications, awards, or relevant coursework'
            }),
            'program': forms.Select(attrs={
                'class': 'w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all bg-white'
            }, choices=[('', '-- Select a Program --')] + CourseApplication.PROGRAM_CHOICES),
            'degree_level': forms.RadioSelect(attrs={'class': 'mr-3 h-5 w-5'}),
            'study_mode': forms.RadioSelect(attrs={'class': 'mr-3 h-5 w-5'}),
            'intake': forms.RadioSelect(attrs={'class': 'mr-3 h-5 w-5'}),
            'scholarship': forms.CheckboxInput(attrs={'class': 'mr-3 h-5 w-5'}),
            'referral_source': forms.Select(attrs={
                'class': 'w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all bg-white'
            }, choices=[('', '-- How did you hear about us? --')] + CourseApplication.REFERRAL_CHOICES),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate English proficiency
        english_type = cleaned_data.get('english_proficiency_type')
        if english_type == 'toefl' and not cleaned_data.get('toefl_score'):
            raise forms.ValidationError('Please provide your TOEFL score.')
        elif english_type == 'ielts' and not cleaned_data.get('ielts_score'):
            raise forms.ValidationError('Please provide your IELTS score.')
        elif english_type == 'other' and not cleaned_data.get('other_test'):
            raise forms.ValidationError('Please specify your English proficiency test.')
        
        return cleaned_data
    
    def save(self, commit=True, user=None):
        instance = super().save(commit=False)
        
        # Link to user if provided
        if user:
            instance.user = user
        
        # Process English proficiency
        english_type = self.cleaned_data.get('english_proficiency_type')
        instance.english_proficiency = english_type
        
        if english_type == 'toefl':
            instance.english_score = self.cleaned_data.get('toefl_score', '')
        elif english_type == 'ielts':
            instance.english_score = self.cleaned_data.get('ielts_score', '')
        elif english_type == 'other':
            instance.english_score = self.cleaned_data.get('other_test', '')
        else:
            instance.english_score = 'Native Speaker'
        
        # Mark as submitted
        instance.submitted = True
        instance.submission_date = timezone.now()
        
        if commit:
            instance.save()
        
        return instance