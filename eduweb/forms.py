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
    """
    Updated form - ALL fields use Django forms, radio buttons converted to dropdowns
    """
    
    # Course selection
    course = forms.ModelChoiceField(
        queryset=Course.objects.filter(is_active=True),
        required=True,
        empty_label="-- Select a Program --",
        widget=forms.Select(attrs={
            'class': 'w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all bg-white',
        }),
        error_messages={
            'required': 'Please select a program',
        }
    )
    
    # Intake selection
    intake = forms.ModelChoiceField(
        queryset=CourseIntake.objects.filter(is_active=True),
        required=True,
        empty_label="-- Select an Intake Period --",
        widget=forms.Select(attrs={
            'class': 'w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all bg-white',
        }),
        error_messages={
            'required': 'Please select an intake period',
        }
    )
    
    # Study mode - CHANGED TO SELECT DROPDOWN
    study_mode = forms.ChoiceField(
        required=True,
        choices=[('', '-- Select Study Mode --')] + Course.STUDY_MODE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all bg-white',
        }),
        error_messages={
            'required': 'Please select your preferred study mode'
        }
    )
    
    # English proficiency
    english_proficiency_test = forms.ChoiceField(
        required=False,
        choices=[
            ('', '-- Select Test Type --'),
            ('toefl', 'TOEFL'),
            ('ielts', 'IELTS'),
            ('duolingo', 'Duolingo English Test'),
            ('pte', 'PTE Academic'),
            ('cambridge', 'Cambridge English'),
            ('native', 'Native Speaker'),
            ('other', 'Other'),
        ],
        widget=forms.Select(attrs={
            'class': 'w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all bg-white'
        })
    )
    
    english_proficiency_score = forms.CharField(
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all',
            'placeholder': 'e.g., 100 (TOEFL) or 7.5 (IELTS)'
        })
    )
    
    # Declarations - CHANGED TO SELECT DROPDOWN
    declaration = forms.ChoiceField(
        required=True,
        choices=[
            ('', '-- Please Confirm --'),
            ('yes', 'I certify that all information provided is true and accurate'),
        ],
        widget=forms.Select(attrs={
            'class': 'w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all bg-white',
        }),
        error_messages={
            'required': 'You must accept the declaration to submit your application'
        }
    )
    
    privacy = forms.ChoiceField(
        required=True,
        choices=[
            ('', '-- Please Confirm --'),
            ('yes', 'I have read and agree to the MIU Privacy Policy'),
        ],
        widget=forms.Select(attrs={
            'class': 'w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all bg-white',
        }),
        error_messages={
            'required': 'You must accept the privacy policy to continue'
        }
    )
    
    class Meta:
        model = CourseApplication
        fields = [
            # Personal Information
            'first_name', 'last_name', 'email', 'phone', 'date_of_birth',
            'country', 'gender', 'address',
            # Academic Background
            'additional_qualifications',
            # Course Selection
            'course', 'intake', 'study_mode',
            # Financial Aid
            'scholarship_requested', 'financial_aid_requested',
            # Additional Info
            'referral_source', 'personal_statement'
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
                'placeholder': 'john@example.com',
                'readonly': 'readonly'
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
            'personal_statement': forms.Textarea(attrs={
                'rows': 6,
                'class': 'w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all',
                'placeholder': 'Tell us about yourself, your academic goals, and why you want to study this program...'
            }),
            'scholarship_requested': forms.CheckboxInput(attrs={'class': 'mr-3 h-5 w-5'}),
            'financial_aid_requested': forms.CheckboxInput(attrs={'class': 'mr-3 h-5 w-5'}),
            'referral_source': forms.Select(attrs={
                'class': 'w-full p-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all bg-white'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.course_id = kwargs.pop('course_id', None)
        super().__init__(*args, **kwargs)
        
        # Add placeholder options
        self.fields['country'].choices = [('', '-- Select Your Country --')] + list(self.fields['country'].choices)[1:]
        self.fields['gender'].choices = [('', '-- Select Gender --')] + list(self.fields['gender'].choices)[1:]
        self.fields['referral_source'].choices = [('', '-- How did you hear about us? --')] + list(self.fields['referral_source'].choices)[1:]
        
        # Filter intakes
        if self.course_id:
            self.fields['intake'].queryset = CourseIntake.objects.filter(
                course_id=self.course_id,
                is_active=True,
                application_deadline__gte=timezone.now().date()
            ).order_by('start_date')
        
        if self.instance and self.instance.pk and self.instance.course:
            self.fields['intake'].queryset = CourseIntake.objects.filter(
                course=self.instance.course,
                is_active=True
            ).order_by('start_date')
    
    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            today = timezone.now().date()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 16:
                raise forms.ValidationError('You must be at least 16 years old to apply.')
            if age > 100:
                raise forms.ValidationError('Please enter a valid date of birth.')
        return dob
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            cleaned = re.sub(r'[\s\-\(\)]+', '', phone)
            if not re.match(r'^\+?\d{7,15}$', cleaned):
                raise forms.ValidationError(
                    'Please enter a valid phone number (7-15 digits, optionally starting with +)'
                )
        return phone


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