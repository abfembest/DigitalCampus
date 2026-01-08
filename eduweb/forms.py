from django import forms
from .models import ContactMessage

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