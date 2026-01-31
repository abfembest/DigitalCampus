from django import forms
from django.core.validators import FileExtensionValidator
from eduweb.models import (
    LMSCourse, Lesson, LessonSection, Quiz, QuizQuestion,
    QuizAnswer, Assignment, Announcement
)


# ==================== COURSE FORMS ====================
class CourseForm(forms.ModelForm):
    """Form for creating and editing courses"""
    
    class Meta:
        model = LMSCourse
        fields = [
            'title', 'code', 'category', 'short_description', 
            'description', 'difficulty_level', 'duration_hours',
            'language', 'thumbnail', 'promo_video_url',
            'is_free', 'price', 'discount_price', 'max_students',
            'enrollment_start_date', 'enrollment_end_date',
            'has_certificate', 'is_published', 'is_featured'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Course Title'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., CS101'
            }),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'short_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Brief description (max 500 characters)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Detailed course description'
            }),
            'difficulty_level': forms.Select(attrs={'class': 'form-control'}),
            'duration_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.5'
            }),
            'language': forms.TextInput(attrs={
                'class': 'form-control',
                'value': 'English'
            }),
            'promo_video_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'YouTube or Vimeo URL'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'discount_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'max_students': forms.NumberInput(attrs={
                'class': 'form-control'
            }),
            'enrollment_start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'enrollment_end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'is_free': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_certificate': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CourseObjectivesForm(forms.ModelForm):
    """Form for managing course learning objectives"""
    objectives = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 6,
            'placeholder': 'Enter one objective per line'
        }),
        help_text='Enter each learning objective on a new line'
    )
    prerequisites = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Enter one prerequisite per line'
        }),
        help_text='Enter each prerequisite on a new line'
    )
    
    class Meta:
        model = LMSCourse
        fields = []


# ==================== SECTION FORMS ====================
class SectionForm(forms.ModelForm):
    """Form for creating course sections"""
    
    class Meta:
        model = LessonSection
        fields = ['title', 'description', 'display_order']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Section Title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Section description (optional)'
            }),
            'display_order': forms.NumberInput(attrs={
                'class': 'form-control',
                'value': 0
            }),
        }


# ==================== LESSON FORMS ====================
class LessonForm(forms.ModelForm):
    """Form for creating and editing lessons"""
    
    class Meta:
        model = Lesson
        fields = [
            'section', 'title', 'lesson_type', 'description',
            'content', 'video_url', 'video_duration_minutes',
            'file', 'is_preview', 'display_order'
        ]
        widgets = {
            'section': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Lesson Title'
            }),
            'lesson_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Lesson description'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Lesson content (for text lessons)'
            }),
            'video_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'YouTube, Vimeo, or storage URL'
            }),
            'video_duration_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'value': 0
            }),
            'display_order': forms.NumberInput(attrs={
                'class': 'form-control',
                'value': 0
            }),
            'is_preview': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        course = kwargs.pop('course', None)
        super().__init__(*args, **kwargs)
        if course:
            self.fields['section'].queryset = LessonSection.objects.filter(
                course=course
            )


# ==================== QUIZ FORMS ====================
class QuizForm(forms.ModelForm):
    """Form for creating and editing quizzes"""
    
    class Meta:
        model = Quiz
        fields = [
            'title', 'description', 'instructions',
            'time_limit_minutes', 'passing_score', 'max_attempts',
            'shuffle_questions', 'show_correct_answers', 'display_order'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Quiz Title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Quiz description'
            }),
            'instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Instructions for students'
            }),
            'time_limit_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Leave blank for no limit'
            }),
            'passing_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'value': 70,
                'step': '0.01'
            }),
            'max_attempts': forms.NumberInput(attrs={
                'class': 'form-control',
                'value': 3
            }),
            'display_order': forms.NumberInput(attrs={
                'class': 'form-control',
                'value': 0
            }),
            'shuffle_questions': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'show_correct_answers': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class QuizQuestionForm(forms.ModelForm):
    """Form for creating quiz questions"""
    
    class Meta:
        model = QuizQuestion
        fields = [
            'question_type', 'question_text', 'explanation',
            'points', 'display_order'
        ]
        widgets = {
            'question_type': forms.Select(attrs={'class': 'form-control'}),
            'question_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter your question'
            }),
            'explanation': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Explanation (shown after answer)'
            }),
            'points': forms.NumberInput(attrs={
                'class': 'form-control',
                'value': 1,
                'step': '0.01'
            }),
            'display_order': forms.NumberInput(attrs={
                'class': 'form-control',
                'value': 0
            }),
        }


class QuizAnswerForm(forms.ModelForm):
    """Form for creating quiz answer choices"""
    
    class Meta:
        model = QuizAnswer
        fields = ['answer_text', 'is_correct', 'display_order']
        widgets = {
            'answer_text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Answer choice'
            }),
            'is_correct': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'display_order': forms.NumberInput(attrs={
                'class': 'form-control',
                'value': 0
            }),
        }


# ==================== ASSIGNMENT FORMS ====================
class AssignmentForm(forms.ModelForm):
    """Form for creating and editing assignments"""
    
    class Meta:
        model = Assignment
        fields = [
            'title', 'description', 'instructions',
            'max_score', 'passing_score', 'attachment',
            'due_date', 'allow_late_submission',
            'late_penalty_percent', 'display_order'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Assignment Title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Assignment description'
            }),
            'instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Detailed instructions for students'
            }),
            'max_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'value': 100,
                'step': '0.01'
            }),
            'passing_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'value': 50,
                'step': '0.01'
            }),
            'due_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'late_penalty_percent': forms.NumberInput(attrs={
                'class': 'form-control',
                'value': 0
            }),
            'display_order': forms.NumberInput(attrs={
                'class': 'form-control',
                'value': 0
            }),
            'allow_late_submission': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


# ==================== ANNOUNCEMENT FORMS ====================
class AnnouncementForm(forms.ModelForm):
    """Form for creating course announcements"""
    
    class Meta:
        model = Announcement
        fields = [
            'title', 'content', 'priority',
            'publish_date', 'expiry_date'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Announcement Title'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Announcement content'
            }),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'publish_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'expiry_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
        }