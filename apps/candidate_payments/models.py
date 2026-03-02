from django.db import models
from apps.candidates.models import Candidate
from django.contrib.auth.models import User
import uuid

class CandidatePayment(models.Model):
    PAYMENT_TYPES = [
        ('registration', 'Registration'),
        ('medical', 'Medical'),
        ('visa', 'Visa'),
        ('ticket', 'Ticket'),
        ('balance', 'Balance Payment'),
        ('loan_disbursement', 'Loan Disbursement'),
    ]
    
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('mobile_money', 'Mobile Money'),
        ('cheque', 'Cheque'),
        ('loan', 'Loan'),
    ]
    
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='payments')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    receipt_number = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    receipt_file = models.FileField(upload_to='payment_receipts/', null=True, blank=True)
    receipt_uploaded_at = models.DateTimeField(null=True, blank=True)
    
    # Balance tracking
    previous_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    new_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        # Calculate balances
        if not self.pk:  # New payment
            total_paid_before = self.candidate.payments.aggregate(total=models.Sum('amount'))['total'] or 0
            self.previous_balance = self.candidate.initial_amount - total_paid_before
            self.new_balance = self.previous_balance - self.amount
        
        super().save(*args, **kwargs)
        # Update candidate balance
        self.candidate.update_balance()
    
    def __str__(self):
        return f"{self.candidate.full_name} - {self.payment_type} - {self.amount}"
    
    class Meta:
        ordering = ['-date']

class PaymentHistory(models.Model):
    """Track payment history for candidates on loan/installment"""
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='payment_history')
    payment = models.ForeignKey(CandidatePayment, on_delete=models.CASCADE, related_name='history', null=True, blank=True)  # Made nullable
    due_date = models.DateField()
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
    ], default='pending')
    paid_date = models.DateField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['due_date']
    
    def __str__(self):
        return f"{self.candidate.full_name} - Due: {self.due_date} - {self.amount_due}"