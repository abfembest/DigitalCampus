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
    captcha = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-950 focus:ring-2 focus:ring-purple-200 transition-all',
            'placeholder': 'Enter the result',
            'autocomplete': 'off'
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
        
        # Update password field widgets
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
        
        # Update labels
        self.fields['username'].label = 'Username'
        self.fields['first_name'].label = 'First Name'
        self.fields['last_name'].label = 'Last Name'
        self.fields['email'].label = 'Email Address'
        self.fields['password1'].label = 'Password'
        self.fields['password2'].label = 'Confirm Password'
        self.fields['captcha'].label = 'Security Check'
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('This email address is already registered.')
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValidationError('Username can only contain letters, numbers, and underscores.')
        if len(username) < 3:
            raise ValidationError('Username must be at least 3 characters long.')
        return username
    
    def clean_captcha(self):
        captcha = self.cleaned_data.get('captcha')
        if self.captcha_answer and str(captcha) != str(self.captcha_answer):
            raise ValidationError('Incorrect answer. Please try again.')
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
    captcha = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-950 focus:ring-2 focus:ring-purple-200 transition-all',
            'placeholder': 'Enter the result',
            'autocomplete': 'off'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.captcha_answer = kwargs.pop('captcha_answer', None)
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Username or Email'
        self.fields['password'].label = 'Password'
        self.fields['captcha'].label = 'Security Check'
    
    def clean_captcha(self):
        captcha = self.cleaned_data.get('captcha')
        if self.captcha_answer and str(captcha) != str(self.captcha_answer):
            raise ValidationError('Incorrect answer. Please try again.')
        return captcha

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full p-4 border border-gray-300 rounded-lg focus:border-miu-secondary focus:ring-2 focus:ring-blue-100 transition',
                'placeholder': 'John Smith',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full p-4 border border-gray-300 rounded-lg focus:border-miu-secondary focus:ring-2 focus:ring-blue-100 transition',
                'placeholder': 'john@example.com',
                'required': True
            }),
            'subject': forms.Select(attrs={
                'class': 'w-full p-4 border border-gray-300 rounded-lg focus:border-miu-secondary focus:ring-2 focus:ring-blue-100 transition bg-white'
            }),
            'message': forms.Textarea(attrs={
                'class': 'w-full p-4 border border-gray-300 rounded-lg focus:border-miu-secondary focus:ring-2 focus:ring-blue-100 transition',
                'placeholder': "I'm interested in learning more about...",
                'rows': 4,
                'required': True
            }),
        }
        labels = {
            'name': 'Your Name',
            'email': 'Your Email',
            'subject': 'Subject',
            'message': 'Your Message'
        }
    
    def clean_message(self):
        message = self.cleaned_data.get('message')
        if len(message) < 10:
            raise forms.ValidationError('Message must be at least 10 characters long.')
        return message

class CourseApplicationForm(forms.ModelForm):
    # English proficiency fields
    english_proficiency_type = forms.ChoiceField(
        choices=[
            ('', 'Select Test Type'),
            ('toefl', 'TOEFL'),
            ('ielts', 'IELTS'),
            ('other', 'Other'),
            ('native', 'Native Speaker'),
        ],
        required=False,
        widget=forms.RadioSelect(attrs={'class': 'mr-2 h-5 w-5'})
    )
    toefl_score = forms.CharField(required=False, max_length=20, widget=forms.TextInput(attrs={
        'class': 'w-32 px-3 py-2 border border-gray-300 rounded-lg focus:border-purple-500',
        'placeholder': 'Score'
    }))
    ielts_score = forms.CharField(required=False, max_length=20, widget=forms.TextInput(attrs={
        'class': 'w-32 px-3 py-2 border border-gray-300 rounded-lg focus:border-purple-500',
        'placeholder': 'Score'
    }))
    other_test = forms.CharField(required=False, max_length=100, widget=forms.TextInput(attrs={
        'class': 'w-40 px-3 py-2 border border-gray-300 rounded-lg focus:border-purple-500',
        'placeholder': 'Test name'
    }))
    
    # File upload fields
    transcripts_file = forms.FileField(required=False, widget=forms.FileInput(attrs={
        'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-purple-500',
        'accept': '.pdf,.doc,.docx,.jpg,.png'
    }))
    english_proficiency_file = forms.FileField(required=False, widget=forms.FileInput(attrs={
        'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-purple-500',
        'accept': '.pdf,.doc,.docx,.jpg,.png'
    }))
    personal_statement_file = forms.FileField(required=False, widget=forms.FileInput(attrs={
        'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-purple-500',
        'accept': '.pdf,.doc,.docx'
    }))
    cv_file = forms.FileField(required=False, widget=forms.FileInput(attrs={
        'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-purple-500',
        'accept': '.pdf,.doc,.docx'
    }))
    additional_files = forms.FileField(
        required=False, 
        widget=MultipleFileInput(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-purple-500',
            'accept': '.pdf,.doc,.docx,.jpg,.png'
        })
    )
    
    # Declaration checkboxes
    declaration = forms.BooleanField(required=True, widget=forms.CheckboxInput(attrs={
        'class': 'mr-3 h-5 w-5'
    }))
    privacy = forms.BooleanField(required=True, widget=forms.CheckboxInput(attrs={
        'class': 'mr-3 h-5 w-5'
    }))
    
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
                'placeholder': 'John',
                'required': True
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all',
                'placeholder': 'Smith',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all',
                'placeholder': 'john@example.com',
                'required': True
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all',
                'placeholder': '+1 (555) 123-4567',
                'required': True
            }),
            'date_of_birth': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all',
                'required': True
            }),
            'country': forms.Select(attrs={
                'class': 'w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all bg-white',
                'required': True
            }),
            'gender': forms.Select(attrs={
                'class': 'w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all bg-white',
                'required': True
            }),
            'address': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all',
                'placeholder': 'Enter your full address',
                'required': True
            }),
            'additional_qualifications': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all',
                'placeholder': 'List any certifications, awards, or relevant coursework'
            }),
            'program': forms.Select(attrs={
                'class': 'w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all bg-white',
                'required': True
            }),
            'degree_level': forms.RadioSelect(attrs={'class': 'mr-3 h-5 w-5'}),
            'study_mode': forms.RadioSelect(attrs={'class': 'mr-3 h-5 w-5'}),
            'intake': forms.RadioSelect(attrs={'class': 'mr-3 h-5 w-5'}),
            'scholarship': forms.CheckboxInput(attrs={'class': 'mr-3 h-5 w-5'}),
            'referral_source': forms.Select(attrs={
                'class': 'w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all bg-white'
            }),
        }
        
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'email': 'Email Address',
            'phone': 'Phone Number',
            'date_of_birth': 'Date of Birth',
            'country': 'Country of Citizenship',
            'gender': 'Gender',
            'address': 'Current Address',
            'additional_qualifications': 'Additional Qualifications or Certifications',
            'program': 'Program of Interest',
            'degree_level': 'Degree Level',
            'study_mode': 'Study Mode',
            'intake': 'Intake Semester',
            'scholarship': 'Scholarship Consideration',
            'referral_source': 'How did you hear about MIU?',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate academic history
        education_levels = self.data.getlist('educationLevel[]')
        if not education_levels or not any(education_levels):
            raise forms.ValidationError('Please provide at least one academic history entry.')
        
        # Validate English proficiency
        english_type = cleaned_data.get('english_proficiency_type')
        if not english_type:
            raise forms.ValidationError('Please select your English proficiency type.')
        
        if english_type == 'toefl' and not cleaned_data.get('toefl_score'):
            raise forms.ValidationError('Please provide your TOEFL score.')
        elif english_type == 'ielts' and not cleaned_data.get('ielts_score'):
            raise forms.ValidationError('Please provide your IELTS score.')
        elif english_type == 'other' and not cleaned_data.get('other_test'):
            raise forms.ValidationError('Please specify your English proficiency test.')
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Process academic history
        education_levels = self.data.getlist('educationLevel[]')
        institutions = self.data.getlist('institution[]')
        fields_of_study = self.data.getlist('fieldOfStudy[]')
        graduation_years = self.data.getlist('graduationYear[]')
        gpas = self.data.getlist('gpa[]')
        
        academic_history = []
        for i in range(len(education_levels)):
            if education_levels[i]:
                academic_history.append({
                    'education_level': education_levels[i],
                    'institution': institutions[i] if i < len(institutions) else '',
                    'field_of_study': fields_of_study[i] if i < len(fields_of_study) else '',
                    'graduation_year': graduation_years[i] if i < len(graduation_years) else '',
                    'gpa': gpas[i] if i < len(gpas) else '',
                })
        
        instance.academic_history = academic_history
        
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
            instance.english_score = ''
        
        # Mark as submitted
        instance.submitted = True
        instance.submission_date = timezone.now()
        
        if commit:
            instance.save()
        
        return instance