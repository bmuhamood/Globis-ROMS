from django.db import models
from apps.candidates.models import Candidate

class VisaProcess(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]
    
    candidate = models.OneToOneField(Candidate, on_delete=models.CASCADE, related_name='visa_process')
    interview_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    medical_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    interpol_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    visa_applied = models.BooleanField(default=False)
    visa_stamped = models.BooleanField(default=False)
    ticket_issued = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    
    def progress_percentage(self):
        total = 6
        completed = 0
        if self.interview_status == 'completed': completed += 1
        if self.medical_status == 'completed': completed += 1
        if self.interpol_status == 'completed': completed += 1
        if self.visa_applied: completed += 1
        if self.visa_stamped: completed += 1
        if self.ticket_issued: completed += 1
        return int((completed / total) * 100)
    
    def __str__(self):
        return f"Visa Process - {self.candidate.full_name}"