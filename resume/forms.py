from django import forms
from .models import Resume


class ResumeForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = [
            'full_name',
            'email',
            'phone',
            'address',
            'education',
            'skills',
            'projects',
            'certifications',
            'internships',
            'career_objective',
        ]
from django import forms
from .models import Job


class JobForm(forms.ModelForm):

    class Meta:
        model = Job

        fields = [
            'job_title',
            'required_skills',
            'qualification',
            'experience',
            'location',
            'employment_type',
            'job_description',
        ]

        widgets = {
            'job_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter job title'
            }),

            'required_skills': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter required skills',
                'rows': 3
            }),

            'qualification': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter required qualification'
            }),

            'experience': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Example: Fresher'
            }),

            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter job location'
            }),

            'employment_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Example: Full-time'
            }),

            'job_description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter job description',
                'rows': 5
            }),
        }