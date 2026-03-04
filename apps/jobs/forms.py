from django import forms
from .models import Job, JobCategory, JobAttachment
from django.utils import timezone

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = '__all__'
        exclude = ['created_by', 'updated_by', 'views_count', 'applications_count', 'description']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Senior Software Developer'
            }),
            'reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Leave blank to auto-generate'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'job_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'experience_level': forms.Select(attrs={
                'class': 'form-select'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Kampala, Uganda'
            }),
            'salary_range': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., UGX 2,000,000 - 3,500,000'
            }),
            'closing_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'posted_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'summary': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 12,
                'placeholder': 'Write a compelling summary to attract candidates...',
                'maxlength': 500
            }),
            'contact_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'hr@company.com'
            }),
            'contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+256 XXX XXXXXX'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'role': 'switch'
            }),
        }
        labels = {
            'title': 'Job Title',
            'reference': 'Reference Number',
            'category': 'Category',
            'job_type': 'Job Type',
            'experience_level': 'Experience Level',
            'location': 'Location',
            'salary_range': 'Salary Range',
            'closing_date': 'Closing Date',
            'posted_date': 'Posted Date',
            'summary': 'Brief Overview',
            'contact_email': 'Contact Email',
            'contact_phone': 'Contact Phone',
            'is_active': 'Publish Job',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make fields required
        self.fields['closing_date'].required = True
        
        # Set field order - removed description
        self.order_fields([
            'title', 'reference', 'category', 'job_type', 'experience_level',
            'location', 'salary_range', 'closing_date', 'posted_date',
            'contact_email', 'contact_phone', 'summary', 'is_active'
        ])
    
    def clean_closing_date(self):
        closing_date = self.cleaned_data.get('closing_date')
        if closing_date and closing_date < timezone.now().date():
            raise forms.ValidationError("Closing date cannot be in the past")
        return closing_date
    
    def clean_summary(self):
        summary = self.cleaned_data.get('summary')
        if summary and len(summary) > 500:
            raise forms.ValidationError("Summary must not exceed 500 characters")
        return summary

class JobAttachmentForm(forms.ModelForm):
    class Meta:
        model = JobAttachment
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png'
            })
        }