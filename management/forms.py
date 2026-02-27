from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from eduweb.models import (
    Faculty,
    Department,
    Program,
    Course,
    BlogPost,
    BlogCategory,
    BroadcastMessage,
    LMSCourse,
    CourseApplication,
    Enrollment,
    UserProfile,
    SystemConfiguration,
    CourseCategory,
)
import json


# ==============================================================================
# FACULTY FORM
# ==============================================================================

class FacultyForm(forms.ModelForm):
    special_features_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
            'rows': 6,
            'placeholder': 'Enter one feature per line in format:\nicon|title|description\n\nExample:\nrocket|Business Incubator|Launch your startup with mentorship'
        }),
        label='Special Features',
        help_text='Format: icon|title|description (one per line)'
    )

    class Meta:
        model = Faculty
        fields = [
            'name', 'code', 'icon', 'color_primary', 'color_secondary',
            'tagline', 'description', 'mission', 'vision',
            'student_count', 'placement_rate', 'partner_count', 'international_faculty',
            'accreditation', 'hero_image', 'about_image',
            'meta_description', 'meta_keywords',
            'is_active', 'display_order'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., Faculty of Business'
            }),
            'code': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., BUS'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., briefcase (Lucide icon name)'
            }),
            'color_primary': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all bg-white'
            }, choices=[
                ('orange', 'Orange'), ('blue', 'Blue'), ('teal', 'Teal'),
                ('green', 'Green'), ('purple', 'Purple'), ('red', 'Red'),
                ('pink', 'Pink'), ('indigo', 'Indigo'), ('cyan', 'Cyan')
            ]),
            'color_secondary': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all bg-white'
            }, choices=[
                ('amber', 'Amber'), ('cyan', 'Cyan'), ('emerald', 'Emerald'),
                ('lime', 'Lime'), ('violet', 'Violet'), ('rose', 'Rose'),
                ('fuchsia', 'Fuchsia'), ('sky', 'Sky'), ('yellow', 'Yellow')
            ]),
            'tagline': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., Lead. Innovate. Transform.'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'rows': 4,
                'placeholder': 'Main description of the faculty...'
            }),
            'mission': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'rows': 3,
                'placeholder': 'Faculty mission statement...'
            }),
            'vision': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'rows': 3,
                'placeholder': 'Faculty vision statement...'
            }),
            'student_count': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., 4000'
            }),
            'placement_rate': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., 95 (percentage)', 'min': 0, 'max': 100
            }),
            'partner_count': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., 500'
            }),
            'international_faculty': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., 85 (percentage)', 'min': 0, 'max': 100
            }),
            'accreditation': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'rows': 3,
                'placeholder': 'e.g., AACSB Accreditation - Top 5% worldwide'
            }),
            'hero_image': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'accept': 'image/*'
            }),
            'about_image': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'accept': 'image/*'
            }),
            'meta_description': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'SEO description (160 characters max)', 'maxlength': 160
            }),
            'meta_keywords': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'keyword1, keyword2, keyword3'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-primary-600 border-gray-300 rounded focus:ring-primary-500'
            }),
            'display_order': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., 1 (lower numbers appear first)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.special_features:
            lines = []
            if isinstance(self.instance.special_features, list):
                for feature in self.instance.special_features:
                    if isinstance(feature, dict):
                        icon = feature.get('icon', '')
                        title = feature.get('title', '')
                        description = feature.get('description', '')
                        lines.append(f"{icon}|{title}|{description}")
                self.fields['special_features_text'].initial = '\n'.join(lines)

    def clean_special_features_text(self):
        text = self.cleaned_data.get('special_features_text', '').strip()
        if not text:
            return []
        features = []
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            parts = line.split('|')
            if len(parts) == 3:
                features.append({
                    'icon': parts[0].strip(),
                    'title': parts[1].strip(),
                    'description': parts[2].strip()
                })
        return features

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.special_features = self.cleaned_data.get('special_features_text', [])
        if commit:
            instance.save()
        return instance


# ==============================================================================
# COURSE FORM  — updated to match refactored Course model
# Course is now a subject/unit under a Program.
# Program-level fields (fees, degree_level, duration, etc.) are no longer here.
# ==============================================================================

class CourseForm(forms.ModelForm):
    """
    Form for creating / editing a Course (academic subject unit).
    Aligns with the refactored Course model:
      - Belongs to a Program (not directly to Faculty/Department)
      - Has course_type, credit_units, year_of_study, semester
      - Has academic_session and lecturer
      - learning_outcomes stored as JSON (textarea helper provided)
    """

    # ── JSON textarea helpers ──────────────────────────────────────────────────
    learning_outcomes_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
            'rows': 4,
            'placeholder': (
                'Enter one outcome per line:\n'
                'Understand core programming concepts\n'
                'Apply data structures in real problems\n'
                'Build and deploy web applications'
            )
        }),
        label='Learning Outcomes',
        help_text='One outcome per line — stored as a list'
    )

    class Meta:
        model = Course
        fields = [
            'program', 'name', 'code', 'course_type', 'credit_units',
            'year_of_study', 'semester', 'academic_session', 'lecturer',
            'description', 'learning_outcomes', 'icon', 'color_primary',
            'color_secondary', 'is_active', 'display_order',
        ]
        widgets = {
            # ── Hierarchy ──────────────────────────────────────────────────
            'program': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all bg-white',
            }),

            # ── Identity ──────────────────────────────────────────────────
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., Introduction to Programming'
            }),
            'code': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., CS101'
            }),

            # ── Academic Structure ─────────────────────────────────────────
            'course_type': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all bg-white'
            }),
            'credit_units': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., 3',
                'min': 1,
                'max': 12
            }),
            'year_of_study': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., 1',
                'min': 1,
                'max': 7
            }),
            'semester': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all bg-white'
            }),

            # ── Session & Instructor ───────────────────────────────────────
            'academic_session': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all bg-white'
            }),
            'lecturer': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all bg-white'
            }),

            # ── Content ────────────────────────────────────────────────────
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'rows': 4,
                'placeholder': 'What does this course cover?'
            }),

            # ── Display ────────────────────────────────────────────────────
            'icon': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., book-open (Lucide icon name)'
            }),
            'color_primary': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all bg-white'
            }, choices=[
                ('blue', 'Blue'), ('teal', 'Teal'), ('green', 'Green'),
                ('orange', 'Orange'), ('purple', 'Purple'), ('red', 'Red'),
                ('pink', 'Pink'), ('indigo', 'Indigo'), ('cyan', 'Cyan')
            ]),
            'color_secondary': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all bg-white'
            }, choices=[
                ('cyan', 'Cyan'), ('emerald', 'Emerald'), ('lime', 'Lime'),
                ('amber', 'Amber'), ('violet', 'Violet'), ('rose', 'Rose'),
                ('fuchsia', 'Fuchsia'), ('sky', 'Sky'), ('yellow', 'Yellow')
            ]),

            # ── Status ─────────────────────────────────────────────────────
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-primary-600 border-gray-300 rounded focus:ring-primary-500'
            }),
            'display_order': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., 1 (lower numbers appear first)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Restrict lecturer dropdown to staff/superusers for cleaner UX
        self.fields['lecturer'].queryset = User.objects.filter(
            is_staff=True
        ).order_by('last_name', 'first_name')
        self.fields['lecturer'].empty_label = '— Assign Lecturer —'
        self.fields['academic_session'].empty_label = '— Select Session —'
        self.fields['program'].empty_label = '— Select Program —'

        # Pre-populate learning_outcomes_text when editing
        if self.instance.pk:
            outcomes = self.instance.learning_outcomes
            if outcomes and isinstance(outcomes, list):
                self.fields['learning_outcomes_text'].initial = '\n'.join(outcomes)

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Convert textarea to JSON list
        raw = self.cleaned_data.get('learning_outcomes_text', '')
        instance.learning_outcomes = [
            line.strip() for line in raw.split('\n') if line.strip()
        ]
        if commit:
            instance.save()
        return instance


# ==============================================================================
# BLOG FORMS
# ==============================================================================

class BlogCategoryForm(forms.ModelForm):
    class Meta:
        model = BlogCategory
        fields = ['name', 'description', 'icon', 'color', 'display_order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., Student Life'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'rows': 3,
                'placeholder': 'Brief description of this category...'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., users (Lucide icon name)'
            }),
            'color': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all bg-white'
            }, choices=[
                ('blue', 'Blue'), ('green', 'Green'), ('purple', 'Purple'),
                ('orange', 'Orange'), ('red', 'Red'), ('teal', 'Teal'),
                ('pink', 'Pink'), ('indigo', 'Indigo'), ('rose', 'Rose')
            ]),
            'display_order': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., 1 (lower numbers appear first)'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-primary-600 border-gray-300 rounded focus:ring-primary-500'
            }),
        }


class BlogPostForm(forms.ModelForm):
    tags_text = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
            'placeholder': 'research, innovation, technology (comma-separated)'
        }),
        label='Tags',
        help_text='Enter tags separated by commas'
    )

    class Meta:
        model = BlogPost
        fields = [
            'title', 'subtitle', 'excerpt', 'content', 'category',
            'author_name', 'author_title', 'featured_image', 'featured_image_alt',
            'read_time', 'status', 'is_featured', 'publish_date',
            'meta_description', 'meta_keywords'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., MIU Researchers Develop Breakthrough AI Technology'
            }),
            'subtitle': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'Optional subtitle for additional context'
            }),
            'excerpt': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'rows': 3,
                'placeholder': 'Write a compelling summary (max 500 characters)...',
                'maxlength': 500
            }),
            'content': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'rows': 15,
                'placeholder': 'Write your full blog post content here. You can use HTML for formatting...'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all bg-white'
            }),
            'author_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., Dr. Sarah Johnson'
            }),
            'author_title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., Communications Director'
            }),
            'featured_image': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'accept': 'image/*'
            }),
            'featured_image_alt': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'Describe the image for accessibility'
            }),
            'read_time': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., 5 (minutes)', 'min': 1
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all bg-white'
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-primary-600 border-gray-300 rounded focus:ring-primary-500'
            }),
            'publish_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all'
            }),
            'meta_description': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'SEO meta description (max 160 characters)', 'maxlength': 160
            }),
            'meta_keywords': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'keyword1, keyword2, keyword3'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.tags:
            if isinstance(self.instance.tags, list):
                self.fields['tags_text'].initial = ', '.join(self.instance.tags)

    def clean_tags_text(self):
        text = self.cleaned_data.get('tags_text', '').strip()
        if not text:
            return []
        return [tag.strip().lower() for tag in text.split(',') if tag.strip()]

    def clean_excerpt(self):
        excerpt = self.cleaned_data.get('excerpt', '')
        if len(excerpt) > 500:
            raise forms.ValidationError('Excerpt must be 500 characters or less.')
        return excerpt

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.tags = self.cleaned_data.get('tags_text', [])
        if commit:
            instance.save()
        return instance


# ==============================================================================
# USER FORMS
# ==============================================================================

class UserSearchForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
            'placeholder': 'Search by name, username, or email...',
            'id': 'searchInput'
        })
    )
    role = forms.ChoiceField(
        required=False,
        choices=[('', 'All Roles')] + UserProfile.ROLE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white',
            'id': 'roleFilter'
        })
    )
    is_active = forms.ChoiceField(
        required=False,
        choices=[('', 'All Status'), ('true', 'Active'), ('false', 'Inactive')],
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white',
            'id': 'statusFilter'
        })
    )


class UserCreateForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
            'placeholder': 'user@example.com'
        })
    )
    first_name = forms.CharField(
        max_length=150, required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
            'placeholder': 'John'
        })
    )
    last_name = forms.CharField(
        max_length=150, required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
            'placeholder': 'Doe'
        })
    )
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white'
        })
    )
    is_staff = forms.BooleanField(
        required=False, initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-5 h-5 text-primary-600 border-gray-300 rounded focus:ring-2 focus:ring-primary-500'
        }),
        help_text='Designates whether the user can log into this admin site.'
    )
    is_active = forms.BooleanField(
        required=False, initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-5 h-5 text-primary-600 border-gray-300 rounded focus:ring-2 focus:ring-primary-500'
        }),
        help_text='Designates whether this user should be treated as active.'
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email',
                  'password1', 'password2', 'is_staff', 'is_active')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'placeholder': 'username'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
            'placeholder': 'Enter password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
            'placeholder': 'Confirm password'
        })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('This email is already registered.')
        return email.lower()


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'readonly': True
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'placeholder': 'First name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'placeholder': 'Last name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'placeholder': 'user@example.com'
            }),
            'is_staff': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-primary-600 border-gray-300 rounded focus:ring-2 focus:ring-primary-500'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-primary-600 border-gray-300 rounded focus:ring-2 focus:ring-primary-500'
            })
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError('This email is already in use.')
        return email.lower()


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('role', 'bio', 'avatar', 'phone', 'date_of_birth',
                  'address', 'city', 'country', 'website', 'linkedin',
                  'twitter', 'email_notifications', 'marketing_emails')
        widgets = {
            'role': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'rows': 4, 'placeholder': 'Tell us about yourself...'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'accept': 'image/*'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'placeholder': '+1234567890'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'type': 'date'
            }),
            'address': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'rows': 2, 'placeholder': 'Street address'
            }),
            'city': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'placeholder': 'City'
            }),
            'country': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'placeholder': 'Country'
            }),
            'website': forms.URLInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'placeholder': 'https://yourwebsite.com'
            }),
            'linkedin': forms.URLInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'placeholder': 'https://linkedin.com/in/username'
            }),
            'twitter': forms.URLInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'placeholder': 'https://twitter.com/username'
            }),
            'email_notifications': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-primary-600 border-gray-300 rounded focus:ring-2 focus:ring-primary-500'
            }),
            'marketing_emails': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-primary-600 border-gray-300 rounded focus:ring-2 focus:ring-primary-500'
            })
        }


class QuickRoleChangeForm(forms.Form):
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white'
        })
    )


# ==============================================================================
# SYSTEM CONFIGURATION FORMS
# ==============================================================================

class SystemConfigurationForm(forms.ModelForm):
    class Meta:
        model = SystemConfiguration
        fields = ('key', 'value', 'setting_type', 'description', 'is_public')
        widgets = {
            'key': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'placeholder': 'e.g., site_name'
            }),
            'value': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'rows': 4, 'placeholder': 'Configuration value'
            }),
            'setting_type': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'rows': 2, 'placeholder': 'Describe what this setting controls'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-primary-600 border-gray-300 rounded focus:ring-2 focus:ring-primary-500'
            })
        }


class BrandingConfigForm(forms.Form):
    site_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
            'placeholder': 'Your University Name'
        })
    )
    site_tagline = forms.CharField(
        max_length=200, required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
            'placeholder': 'Your inspiring tagline'
        })
    )
    logo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
            'accept': 'image/*'
        })
    )
    favicon = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
            'accept': 'image/*'
        })
    )
    primary_color = forms.CharField(
        max_length=7,
        widget=forms.TextInput(attrs={
            'type': 'color',
            'class': 'h-12 w-24 rounded-lg border border-gray-300'
        })
    )


class EmailConfigForm(forms.Form):
    smtp_host = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
            'placeholder': 'smtp.example.com'
        })
    )
    smtp_port = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
            'placeholder': '587'
        })
    )
    smtp_username = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
            'placeholder': 'your-email@example.com'
        })
    )
    smtp_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
            'placeholder': '••••••••'
        })
    )
    from_email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
            'placeholder': 'noreply@example.com'
        })
    )
    from_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
            'placeholder': 'University Name'
        })
    )


class NotificationConfigForm(forms.Form):
    enable_email_notifications = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-5 h-5 text-primary-600 border-gray-300 rounded focus:ring-2 focus:ring-primary-500'
        })
    )
    enable_sms_notifications = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-5 h-5 text-primary-600 border-gray-300 rounded focus:ring-2 focus:ring-primary-500'
        })
    )
    enable_push_notifications = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-5 h-5 text-primary-600 border-gray-300 rounded focus:ring-2 focus:ring-primary-500'
        })
    )
    notification_from_email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
            'placeholder': 'notifications@example.com'
        })
    )


# ==============================================================================
# COURSE CATEGORY FORM
# ==============================================================================

class CourseCategoryForm(forms.ModelForm):
    class Meta:
        model = CourseCategory
        fields = ('name', 'slug', 'description', 'icon', 'color', 'is_active', 'display_order')
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'placeholder': 'e.g., Programming'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'placeholder': 'programming (auto-generated)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'rows': 3, 'placeholder': 'Brief description of this category'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'placeholder': 'code (Font Awesome icon name without fa-)'
            }),
            'color': forms.TextInput(attrs={
                'type': 'color',
                'class': 'h-12 w-24 rounded-lg border border-gray-300'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-primary-600 border-gray-300 rounded focus:ring-2 focus:ring-primary-500'
            }),
            'display_order': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'placeholder': '0'
            })
        }


# ==============================================================================
# AUDIT LOG FILTER FORM
# ==============================================================================

class AuditLogFilterForm(forms.Form):
    ACTION_CHOICES = [
        ('', 'All Actions'),
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('password_reset', 'Password Reset'),
        ('permission_change', 'Permission Change'),
    ]

    user = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        empty_label='All Users',
        widget=forms.Select(attrs={
            'class': 'px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white'
        })
    )
    action = forms.ChoiceField(
        choices=ACTION_CHOICES, required=False,
        widget=forms.Select(attrs={
            'class': 'px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white'
        })
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500'
        })
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
            'placeholder': 'Search description...'
        })
    )


# ==============================================================================
# BROADCAST FORM
# NOTE: The Course filter here refers to academic Course (admission),
#       not the old Course which had program-level fields.
# ==============================================================================

class BroadcastMessageForm(forms.ModelForm):

    faculties = forms.ModelMultipleChoiceField(
        queryset=Faculty.objects.filter(is_active=True),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Select Faculties"
    )

    # Filters by Program now (since Course is a unit — Program is the admission-level entity)
    programs = forms.ModelMultipleChoiceField(
        queryset=Program.objects.filter(is_active=True),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Select Programs (Admission)"
    )

    # Keep academic Course filter — now scoped to subject units
    courses = forms.ModelMultipleChoiceField(
        queryset=Course.objects.filter(is_active=True),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Select Courses (Academic Units)"
    )

    lms_courses = forms.ModelMultipleChoiceField(
        queryset=LMSCourse.objects.filter(is_published=True),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Select LMS Courses"
    )

    roles = forms.MultipleChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Select User Roles"
    )

    application_statuses = forms.MultipleChoiceField(
        choices=CourseApplication.STATUS_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Select Application Statuses"
    )

    enrollment_statuses = forms.MultipleChoiceField(
        choices=Enrollment.STATUS_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Select Enrollment Statuses"
    )

    class Meta:
        model = BroadcastMessage
        fields = ['subject', 'message', 'filter_type']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg',
                'placeholder': 'Email Subject'
            }),
            'message': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border rounded-lg',
                'rows': 8,
                'placeholder': 'Email Message Content'
            }),
            'filter_type': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg',
                'id': 'id_filter_type'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        filter_type = cleaned_data.get('filter_type')

        validation_map = {
            'faculty':            ('faculties',            'Please select at least one faculty.'),
            'program':            ('programs',             'Please select at least one program.'),
            'course':             ('courses',              'Please select at least one course.'),
            'lms_course':         ('lms_courses',          'Please select at least one LMS course.'),
            'role':               ('roles',                'Please select at least one role.'),
            'application_status': ('application_statuses', 'Please select at least one application status.'),
            'enrollment_status':  ('enrollment_statuses',  'Please select at least one enrollment status.'),
        }

        if filter_type in validation_map:
            field, message = validation_map[filter_type]
            if not cleaned_data.get(field):
                raise forms.ValidationError(message)

        return cleaned_data

from django import forms
from eduweb.models import (
    Department, Program, AcademicSession, CourseIntake,
    Announcement, LMSCourse, CourseCategory
)


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['faculty', 'name', 'code', 'description', 'display_order', 'is_active']

    def clean_code(self):
        code = self.cleaned_data.get('code', '').strip().upper()
        return code


class ProgramForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = [
            'department', 'name', 'code', 'degree_level',
            'duration_years', 'credits_required', 'max_students',
            'tagline', 'overview', 'description',
            'application_fee', 'tuition_fee', 'avg_starting_salary',
            'job_placement_rate',
            'is_active', 'is_featured', 'display_order',
            'hero_image', 'meta_description', 'meta_keywords',
        ]

    def clean_code(self):
        return self.cleaned_data.get('code', '').strip().upper()


class AcademicSessionForm(forms.ModelForm):
    class Meta:
        model = AcademicSession
        fields = [
            'name', 'status', 'is_current',
            'first_semester_start', 'first_semester_end',
            'second_semester_start', 'second_semester_end',
            'registration_start', 'registration_end',
        ]
        widgets = {
            'first_semester_start': forms.DateInput(attrs={'type': 'date'}),
            'first_semester_end': forms.DateInput(attrs={'type': 'date'}),
            'second_semester_start': forms.DateInput(attrs={'type': 'date'}),
            'second_semester_end': forms.DateInput(attrs={'type': 'date'}),
            'registration_start': forms.DateInput(attrs={'type': 'date'}),
            'registration_end': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned = super().clean()
        sem1_start = cleaned.get('first_semester_start')
        sem1_end = cleaned.get('first_semester_end')
        sem2_start = cleaned.get('second_semester_start')
        sem2_end = cleaned.get('second_semester_end')

        if sem1_start and sem1_end and sem1_start >= sem1_end:
            raise forms.ValidationError('Semester 1 start must be before end date.')
        if sem2_start and sem2_end and sem2_start >= sem2_end:
            raise forms.ValidationError('Semester 2 start must be before end date.')
        if sem1_end and sem2_start and sem2_start <= sem1_end:
            raise forms.ValidationError('Semester 2 must start after Semester 1 ends.')
        return cleaned


class CourseIntakeForm(forms.ModelForm):
    class Meta:
        model = CourseIntake
        fields = ['program', 'intake_period', 'year', 'start_date', 'application_deadline', 'available_slots', 'is_active']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'application_deadline': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('start_date')
        deadline = cleaned.get('application_deadline')
        if start and deadline and deadline >= start:
            raise forms.ValidationError('Application deadline must be before the start date.')
        return cleaned


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = [
            'title', 'content',
            'announcement_type', 'priority',
            'course', 'category',
            'is_active', 'publish_date', 'expiry_date',
        ]
        widgets = {
            'publish_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'expiry_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'content': forms.Textarea(attrs={'rows': 6}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active courses & categories
        self.fields['course'].queryset = LMSCourse.objects.filter(is_published=True).order_by('title')
        self.fields['category'].queryset = CourseCategory.objects.filter(is_active=True).order_by('name')
        self.fields['course'].required = False
        self.fields['category'].required = False
