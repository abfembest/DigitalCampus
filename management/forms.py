from django import forms
from eduweb.models import Faculty, Course, BlogPost, BlogCategory
import json

class FacultyForm(forms.ModelForm):
    # Special Features as textarea (we'll convert to JSON)
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
                'placeholder': 'e.g., 95 (percentage)',
                'min': 0,
                'max': 100
            }),
            'partner_count': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., 500'
            }),
            'international_faculty': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., 85 (percentage)',
                'min': 0,
                'max': 100
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
                'placeholder': 'SEO description (160 characters max)',
                'maxlength': 160
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
        # Pre-populate special_features_text if editing
        if self.instance.pk and self.instance.special_features:
            lines = []
            # Check if special_features is a list (correct format)
            if isinstance(self.instance.special_features, list):
                for feature in self.instance.special_features:
                    # Check if each feature is a dict
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


class CourseForm(forms.ModelForm):
    # Text fields for JSON data
    available_study_modes_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
            'rows': 2,
            'placeholder': 'Enter one mode per line:\nFull Time\nPart Time\nOnline'
        }),
        label='Available Study Modes',
        help_text='One mode per line'
    )
    
    learning_outcomes_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
            'rows': 4,
            'placeholder': 'Enter one outcome per line:\nMaster programming fundamentals\nUnderstand data structures\nBuild web applications'
        }),
        label='Learning Outcomes',
        help_text='One outcome per line'
    )
    
    career_paths_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
            'rows': 4,
            'placeholder': 'Enter one career per line:\nSoftware Developer\nData Scientist\nSystems Architect'
        }),
        label='Career Paths',
        help_text='One career path per line'
    )
    
    core_courses_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
            'rows': 6,
            'placeholder': 'Format: title|description (one per line)\n\nExample:\nIntroduction to Programming|Learn Python and Java fundamentals\nData Structures|Master arrays, lists, trees, and graphs'
        }),
        label='Core Courses',
        help_text='Format: title|description (one per line)'
    )
    
    specialization_tracks_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
            'rows': 6,
            'placeholder': 'Format: title|description (one per line)\n\nExample:\nArtificial Intelligence|Deep learning and neural networks\nWeb Development|Full-stack web applications'
        }),
        label='Specialization Tracks',
        help_text='Format: title|description (one per line)'
    )
    
    entry_requirements_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
            'rows': 4,
            'placeholder': 'Enter one requirement per line:\nHigh school diploma or equivalent\nMinimum GPA of 3.0\nEnglish proficiency test scores'
        }),
        label='Entry Requirements',
        help_text='One requirement per line'
    )
    
    class Meta:
        model = Course
        fields = [
            'name', 'code', 'faculty', 'icon', 'color_primary', 'color_secondary',
            'tagline', 'overview', 'description',
            'degree_level',  # Changed from degree_levels
            'duration_years', 'credits_required',
            'application_fee', 'tuition_fee',  # Added fee fields
            'avg_starting_salary', 'job_placement_rate',
            'hero_image', 'meta_description', 'meta_keywords',
            'is_active', 'is_featured', 'display_order'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., Computer Science'
            }),
            'code': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., CS-101'
            }),
            'faculty': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all bg-white'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., code-2 (Lucide icon name)'
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
            'tagline': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., Build the future with code'
            }),
            'overview': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'rows': 3,
                'placeholder': 'Brief program overview...'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'rows': 4,
                'placeholder': 'Detailed program description...'
            }),
            'degree_level': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all bg-white'
            }),
            'duration_years': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., 4',
                'step': '0.5'
            }),
            'credits_required': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., 120'
            }),
            'application_fee': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., 50.00',
                'step': '0.01'
            }),
            'tuition_fee': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., 15000.00',
                'step': '0.01'
            }),
            'avg_starting_salary': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., $125k'
            }),
            'job_placement_rate': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., 95 (percentage)',
                'min': 0,
                'max': 100
            }),
            'hero_image': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'accept': 'image/*'
            }),
            'meta_description': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'SEO description (160 characters max)',
                'maxlength': 160
            }),
            'meta_keywords': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'keyword1, keyword2, keyword3'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-primary-600 border-gray-300 rounded focus:ring-primary-500'
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-primary-600 border-gray-300 rounded focus:ring-primary-500'
            }),
            'display_order': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'e.g., 1 (lower numbers appear first)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Pre-populate text fields if editing
        if self.instance.pk:
            # Safely handle available_study_modes
            if self.instance.available_study_modes and isinstance(self.instance.available_study_modes, list):
                self.fields['available_study_modes_text'].initial = '\n'.join(self.instance.available_study_modes)
            
            # Safely handle learning_outcomes
            if self.instance.learning_outcomes and isinstance(self.instance.learning_outcomes, list):
                self.fields['learning_outcomes_text'].initial = '\n'.join(self.instance.learning_outcomes)
            
            # Safely handle career_paths
            if self.instance.career_paths and isinstance(self.instance.career_paths, list):
                self.fields['career_paths_text'].initial = '\n'.join(self.instance.career_paths)
            
            # Safely handle core_courses
            if self.instance.core_courses and isinstance(self.instance.core_courses, list):
                lines = []
                for c in self.instance.core_courses:
                    if isinstance(c, dict) and 'title' in c and 'description' in c:
                        lines.append(f"{c['title']}|{c['description']}")
                if lines:
                    self.fields['core_courses_text'].initial = '\n'.join(lines)
            
            # Safely handle specialization_tracks
            if self.instance.specialization_tracks and isinstance(self.instance.specialization_tracks, list):
                lines = []
                for t in self.instance.specialization_tracks:
                    if isinstance(t, dict) and 'title' in t and 'description' in t:
                        lines.append(f"{t['title']}|{t['description']}")
                if lines:
                    self.fields['specialization_tracks_text'].initial = '\n'.join(lines)
            
            # Safely handle entry_requirements
            if self.instance.entry_requirements and isinstance(self.instance.entry_requirements, list):
                self.fields['entry_requirements_text'].initial = '\n'.join(self.instance.entry_requirements)
    
    def _process_simple_list(self, text):
        """Convert textarea to simple list"""
        if not text:
            return []
        return [line.strip() for line in text.split('\n') if line.strip()]
    
    def _process_title_description_list(self, text):
        """Convert textarea to list of title|description objects"""
        if not text:
            return []
        
        items = []
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            parts = line.split('|')
            if len(parts) == 2:
                items.append({
                    'title': parts[0].strip(),
                    'description': parts[1].strip()
                })
        
        return items
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Convert text fields to JSON
        instance.available_study_modes = self._process_simple_list(
            self.cleaned_data.get('available_study_modes_text', '')
        )
        instance.learning_outcomes = self._process_simple_list(
            self.cleaned_data.get('learning_outcomes_text', '')
        )
        instance.career_paths = self._process_simple_list(
            self.cleaned_data.get('career_paths_text', '')
        )
        instance.core_courses = self._process_title_description_list(
            self.cleaned_data.get('core_courses_text', '')
        )
        instance.specialization_tracks = self._process_title_description_list(
            self.cleaned_data.get('specialization_tracks_text', '')
        )
        instance.entry_requirements = self._process_simple_list(
            self.cleaned_data.get('entry_requirements_text', '')
        )
        
        if commit:
            instance.save()
        
        return instance

class BlogCategoryForm(forms.ModelForm):
    """Form for creating/editing blog categories"""
    
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
    """Form for creating/editing blog posts"""
    
    # Tags as textarea (convert to JSON list)
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
                'placeholder': 'e.g., 5 (minutes)',
                'min': 1
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
                'placeholder': 'SEO meta description (max 160 characters)',
                'maxlength': 160
            }),
            'meta_keywords': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all',
                'placeholder': 'keyword1, keyword2, keyword3'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Pre-populate tags_text if editing
        if self.instance.pk and self.instance.tags:
            if isinstance(self.instance.tags, list):
                self.fields['tags_text'].initial = ', '.join(self.instance.tags)
        
        # Set current user as default author if creating new post
        if not self.instance.pk:
            # This will be set in the view
            pass
    
    def clean_tags_text(self):
        """Convert comma-separated tags to list"""
        text = self.cleaned_data.get('tags_text', '').strip()
        if not text:
            return []
        
        # Split by comma and clean each tag
        tags = [tag.strip().lower() for tag in text.split(',') if tag.strip()]
        return tags
    
    def clean_excerpt(self):
        """Ensure excerpt is not too long"""
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