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
             # Placeholder
            ('toefl', 'TOEFL'),
            ('ielts', 'IELTS'),
            ('other', 'Other'),
            ('native', 'Native Speaker'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'mr-2 h-5 w-5'}),
        error_messages={
            'required': 'Please select your English proficiency type'
        }
    )
    
    # File uploads
    transcripts_file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-purple-500',
            'accept': '.pdf,.doc,.docx,.jpg,.png'
        }),
        error_messages={
            'invalid': 'Please upload a valid file (PDF, DOC, DOCX, JPG, or PNG)'
        }
    )
    english_proficiency_file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-purple-500',
            'accept': '.pdf,.doc,.docx,.jpg,.png'
        }),
        error_messages={
            'invalid': 'Please upload a valid file (PDF, DOC, DOCX, JPG, or PNG)'
        }
    )
    personal_statement_file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-purple-500',
            'accept': '.pdf,.doc,.docx'
        }),
        error_messages={
            'invalid': 'Please upload a valid document (PDF, DOC, or DOCX)'
        }
    )
    cv_file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-purple-500',
            'accept': '.pdf,.doc,.docx'
        }),
        error_messages={
            'invalid': 'Please upload a valid document (PDF, DOC, or DOCX)'
        }
    )
    
    # Declarations
    declaration = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'mr-3 h-5 w-5'}),
        error_messages={
            'required': 'You must accept the declaration to submit your application'
        }
    )
    privacy = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'mr-3 h-5 w-5'}),
        error_messages={
            'required': 'You must accept the privacy policy to continue'
        }
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
            }),
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
            }),
            'degree_level': forms.RadioSelect(attrs={'class': 'mr-3 h-5 w-5'}),
            'study_mode': forms.RadioSelect(attrs={'class': 'mr-3 h-5 w-5'}),
            'intake': forms.RadioSelect(attrs={'class': 'mr-3 h-5 w-5'}),
            'scholarship': forms.CheckboxInput(attrs={'class': 'mr-3 h-5 w-5'}),
            'referral_source': forms.Select(attrs={
                'class': 'w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all bg-white'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add placeholder options to Select fields
        self.fields['country'].choices = [('', '-- Select Your Country --')] + list(self.fields['country'].choices)[1:]
        self.fields['gender'].choices = [('', '-- Select Gender --')] + list(self.fields['gender'].choices)[1:]
        self.fields['program'].choices = [('', '-- Select a Program --')] + list(self.fields['program'].choices)[1:]
        self.fields['referral_source'].choices = [('', '-- Select an Option --')] + list(self.fields['referral_source'].choices)[1:]
        
        # Add custom error messages for all required fields
        self.fields['first_name'].error_messages = {
            'required': 'Please enter your first name'
        }
        self.fields['last_name'].error_messages = {
            'required': 'Please enter your last name'
        }
        self.fields['email'].error_messages = {
            'required': 'Please enter your email address',
            'invalid': 'Please enter a valid email address'
        }
        self.fields['phone'].error_messages = {
            'required': 'Please enter your phone number'
        }
        self.fields['date_of_birth'].error_messages = {
            'required': 'Please enter your date of birth',
            'invalid': 'Please enter a valid date'
        }
        self.fields['country'].error_messages = {
            'required': 'Please select your country',
            'invalid_choice': 'Please select a valid country from the list'
        }
        self.fields['gender'].error_messages = {
            'required': 'Please select your gender',
            'invalid_choice': 'Please select a valid option'
        }
        self.fields['address'].error_messages = {
            'required': 'Please enter your address'
        }
        self.fields['program'].error_messages = {
            'required': 'Please select a program',
            'invalid_choice': 'Please select a valid program from the list'
        }
        self.fields['degree_level'].error_messages = {
            'required': 'Please select your desired degree level'
        }
        self.fields['study_mode'].error_messages = {
            'required': 'Please select your preferred study mode'
        }
        self.fields['intake'].error_messages = {
            'required': 'Please select your intake semester'
        }
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate English proficiency type
        english_type = cleaned_data.get('english_proficiency_type')
        if not english_type or english_type == '':
            self.add_error('english_proficiency_type', 'Please select your English proficiency type')
        
        # Validate that placeholders weren't selected for select fields
        if cleaned_data.get('country') == '':
            self.add_error('country', 'Please select your country')
        if cleaned_data.get('gender') == '':
            self.add_error('gender', 'Please select your gender')
        if cleaned_data.get('program') == '':
            self.add_error('program', 'Please select a program')
        
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
            instance.english_score = self.data.get('toefl_score', '')
        elif english_type == 'ielts':
            instance.english_score = self.data.get('ielts_score', '')
        elif english_type == 'other':
            instance.english_score = self.data.get('other_test', '')
        else:
            instance.english_score = 'Native Speaker'
        
        # Mark as submitted
        instance.submitted = True
        instance.submission_date = timezone.now()
        
        if commit:
            instance.save()
        
        return instance