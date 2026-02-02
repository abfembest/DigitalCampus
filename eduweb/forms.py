from django import forms
from .models import ContactMessage, CourseApplication, Course, CourseIntake, ApplicationDocument
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re
import os


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
    """Form for course application"""
    
    class Meta:
        model = CourseApplication
        fields = [
            # Course & Intake
            'course', 'intake', 'study_mode',
            
            # Personal Information
            'first_name', 'last_name', 'email', 'phone',
            'date_of_birth', 'gender', 'nationality',
            
            # Address (Note: the model uses separate address fields, not single 'address')
            'address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country',
            
            # Academic Background
            'highest_qualification', 'institution_name', 'graduation_year', 'gpa_or_grade',          
            'language_skill','language_score',
            # Additional Information
            'work_experience_years', 'personal_statement', 'how_did_you_hear',

             # Privacy & Consent
             'accept_privacy_policy','accept_terms_conditions','marketing_consent','scholarship',

            
            # Emergency Contact
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship',

        ]
        
        widgets = {
            # Course & Intake
            'course': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all bg-white'
            }),
            'intake': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all bg-white'
            }),
            'study_mode': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all bg-white'
            }),
            
            # Personal Information
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'Enter your first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'Enter your last name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'your.email@example.com', 'readonly':'readonly'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': '+234 XXX XXX XXXX'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all'
            }),
            'gender': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all bg-white'
            }),
            'nationality': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., Nigerian'
            }),
            
            # Address
            'address_line1': forms.Textarea(attrs={
                'class': 'w-full px-4 py-1.5 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'Street address'
            }),

            'address_line2': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'Apartment, suite, etc. (optional)'
            }),
            'city': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'City'
            }),
            'state': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'State/Province'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'Postal/ZIP code'
            }),
            'country': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'Country'
            }),
            
            # Academic Background
            'highest_qualification': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., High School Diploma, Bachelor\'s Degree'
            }),
            'institution_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'Name of institution'
            }),
            'graduation_year': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., 2020',
                'min': 1950,
                'max': 2030
            }),
            'gpa_or_grade': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., 3.5/4.0 or First Class'
            }),
               'language_skill': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all bg-white'
            }),
             'language_score': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., 6.5 or 80',
                'min':0
            }),

            # Additional Information
            'work_experience_years': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': '0',
                'min': 0
            }),
            'personal_statement': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'rows': 6,
                'placeholder': 'Tell us about yourself, your goals, and why you want to join this program...'
            }),
            'how_did_you_hear': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., Social Media, Friend, Website'
            }),
            
            # Emergency Contact
            'emergency_contact_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'Full name'
            }),
            'emergency_contact_phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': '+234 XXX XXX XXXX'
            }),
            'emergency_contact_relationship': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., Parent, Spouse, Sibling'
            }),

                        #privacy and terms
            'accept_terms_conditions': forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 text-primary-600 rounded focus:ring-primary-400 cursor-pointer',
                'required': True,
            }),

            'accept_privacy_policy': forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 text-primary-600 rounded focus:ring-primary-400 cursor-pointer',
                'required': True,
            }),

            'scholarship': forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 text-purple-600 rounded focus:ring-purple-400 cursor-pointer',
            }),

        }
    
    def clean_phone(self):
        """Validate phone number format"""
        phone = self.cleaned_data.get('phone')
        # Add your phone validation logic here
        return phone
    
    def clean_graduation_year(self):
        """Validate graduation year"""
        year = self.cleaned_data.get('graduation_year')
        from datetime import datetime
        current_year = datetime.now().year
        if year > current_year + 5:
            raise forms.ValidationError('Graduation year cannot be more than 5 years in the future.')
        if year < 1950:
            raise forms.ValidationError('Please enter a valid graduation year.')
        return year
    
    def clean_email(self):
        """Validate email format"""
        email = self.cleaned_data.get('email')
        return email.lower()


class AcademicHistoryForm(forms.Form):
    """Dynamic form for academic entries"""
    institution_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500',
            'placeholder': 'University/School Name'
        })
    )
    
    qualification = forms.ChoiceField(
        choices=[
            ('', '-- Select Level --'),
            ('high-school', 'High School'),
            ('bachelor', "Bachelor's Degree"),
            ('master', "Master's Degree"),
            ('phd', 'PhD/Doctorate'),
        ],
        widget=forms.Select(attrs={
            'class': 'w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 bg-white'
        })
    )
    
    field_of_study = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500',
            'placeholder': 'e.g., Computer Science'
        })
    )
    
    graduation_year = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'class': 'w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500',
            'min': '1950',
            'max': '2030',
            'placeholder': '2023'
        })
    )
    
    gpa = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500',
            'placeholder': 'e.g., 3.8 GPA or First Class'
        })
    )

class ApplicationDocumentUploadForm(forms.ModelForm):
    """Form for uploading application documents"""
    
    class Meta:
        model = ApplicationDocument
        fields = ['file', 'file_type']
        widgets = {
            'file_type': forms.Select(attrs={
                'class': 'w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all bg-white',
            }),
            'file': forms.FileInput(attrs={
                'class': 'w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all',
                'accept': '.pdf,.jpg,.jpeg,.png'
            })
        }
    
    auto_submit = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-5 h-5 text-green-600 rounded focus:ring-2 focus:ring-green-500'
        }),
        label='Submit application after upload'
    )
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Validate file size (5MB max)
            if file.size > 5 * 1024 * 1024:
                raise forms.ValidationError('File size must be less than 5MB')
            
            # Validate file type
            allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
            file_ext = os.path.splitext(file.name)[1].lower()
            if file_ext not in allowed_extensions:
                raise forms.ValidationError('Only PDF, JPG, and PNG files are allowed')
        
        return file