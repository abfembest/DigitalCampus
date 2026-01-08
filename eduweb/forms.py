from django import forms
from .models import ContactMessage, CourseApplication
from django.utils import timezone
import json

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
    # Additional fields not in model but needed for form
    education_level = forms.MultipleChoiceField(
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'hidden'})
    )
    institution = forms.CharField(required=False, widget=forms.HiddenInput())
    field_of_study = forms.CharField(required=False, widget=forms.HiddenInput())
    graduation_year = forms.CharField(required=False, widget=forms.HiddenInput())
    gpa = forms.CharField(required=False, widget=forms.HiddenInput())
    
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
        widget=forms.RadioSelect(attrs={'class': 'mr-2'})
    )
    toefl_score = forms.CharField(required=False, max_length=20)
    ielts_score = forms.CharField(required=False, max_length=20)
    other_test = forms.CharField(required=False, max_length=100)
    
    # File upload fields
    transcripts_file = forms.FileField(required=False)
    english_proficiency_file = forms.FileField(required=False)
    personal_statement_file = forms.FileField(required=False)
    cv_file = forms.FileField(required=False)
    additional_files = forms.FileField(
        required=False, 
        widget=MultipleFileInput(attrs={
            'multiple': True,
            'class': 'w-full p-3 border border-gray-300 rounded-lg focus:border-miu-secondary focus:ring-2 focus:ring-blue-100 transition'
        })
    )
    
    # Declaration checkboxes
    declaration = forms.BooleanField(required=True)
    privacy = forms.BooleanField(required=True)
    
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
                'class': 'w-full p-3 border border-gray-300 rounded-lg focus:border-miu-secondary focus:ring-2 focus:ring-blue-100 transition',
                'placeholder': 'John'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full p-3 border border-gray-300 rounded-lg focus:border-miu-secondary focus:ring-2 focus:ring-blue-100 transition',
                'placeholder': 'Smith'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full p-3 border border-gray-300 rounded-lg focus:border-miu-secondary focus:ring-2 focus:ring-blue-100 transition',
                'placeholder': 'john@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full p-3 border border-gray-300 rounded-lg focus:border-miu-secondary focus:ring-2 focus:ring-blue-100 transition',
                'placeholder': '+1 (555) 123-4567'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full p-3 border border-gray-300 rounded-lg focus:border-miu-secondary focus:ring-2 focus:ring-blue-100 transition'
            }),
            'country': forms.Select(attrs={
                'class': 'w-full p-3 border border-gray-300 rounded-lg focus:border-miu-secondary focus:ring-2 focus:ring-blue-100 transition bg-white'
            }),
            'gender': forms.Select(attrs={
                'class': 'w-full p-3 border border-gray-300 rounded-lg focus:border-miu-secondary focus:ring-2 focus:ring-blue-100 transition bg-white'
            }),
            'address': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full p-3 border border-gray-300 rounded-lg focus:border-miu-secondary focus:ring-2 focus:ring-blue-100 transition',
                'placeholder': 'Enter your full address'
            }),
            'additional_qualifications': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full p-3 border border-gray-300 rounded-lg focus:border-miu-secondary focus:ring-2 focus:ring-blue-100 transition',
                'placeholder': 'List any additional qualifications, certifications, or relevant coursework'
            }),
            'program': forms.Select(attrs={
                'class': 'w-full p-3 border border-gray-300 rounded-lg focus:border-miu-secondary focus:ring-2 focus:ring-blue-100 transition bg-white'
            }),
            'degree_level': forms.RadioSelect(attrs={'class': 'mr-3'}),
            'study_mode': forms.RadioSelect(attrs={'class': 'mr-3'}),
            'intake': forms.RadioSelect(attrs={'class': 'mr-3'}),
            'scholarship': forms.CheckboxInput(attrs={'class': 'mr-3 h-5 w-5'}),
            'referral_source': forms.Select(attrs={
                'class': 'w-full p-3 border border-gray-300 rounded-lg focus:border-miu-secondary focus:ring-2 focus:ring-blue-100 transition bg-white'
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
        institutions = self.data.getlist('institution[]')
        
        if not education_levels or not any(education_levels):
            raise forms.ValidationError('Please provide at least one academic history entry.')
        
        # Validate English proficiency
        english_type = cleaned_data.get('english_proficiency_type')
        if english_type == 'toefl' and not cleaned_data.get('toefl_score'):
            raise forms.ValidationError('Please provide your TOEFL score.')
        elif english_type == 'ielts' and not cleaned_data.get('ielts_score'):
            raise forms.ValidationError('Please provide your IELTS score.')
        elif english_type == 'other' and not cleaned_data.get('other_test'):
            raise forms.ValidationError('Please specify your English proficiency test.')
        
        return super().clean()
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Process academic history (exact names from your file)
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