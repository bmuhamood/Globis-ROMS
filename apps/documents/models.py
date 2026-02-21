from django.db import models
from apps.candidates.models import Candidate

class DocumentStatus(models.Model):
    candidate = models.OneToOneField(Candidate, on_delete=models.CASCADE, related_name='documents')
    medical_report = models.BooleanField(default=False)
    interpol = models.BooleanField(default=False)
    passport_copy = models.BooleanField(default=False)
    passport_photo = models.BooleanField(default=False)
    offer_letter = models.BooleanField(default=False)
    mol_approval = models.BooleanField(default=False, verbose_name="MOL Approval Received and Signed")
    updated_at = models.DateTimeField(auto_now=True)
    
    def missing_documents_count(self):
        count = 0
        if not self.medical_report: count += 1
        if not self.interpol: count += 1
        if not self.passport_copy: count += 1
        if not self.passport_photo: count += 1
        if not self.offer_letter: count += 1
        if not self.mol_approval: count += 1  # Changed from signed_offer_letter
        return count
    
    def __str__(self):
        return f"Documents - {self.candidate.full_name}"