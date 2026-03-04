from django.db import models
from apps.clients.models import Client
from apps.agents.models import Agent
from django.utils import timezone
from decimal import Decimal

class Candidate(models.Model):
    NATIONALITIES = [
        ('UG', 'Ugandan'),
        ('KE', 'Kenyan'),
        ('TZ', 'Tanzanian'),
        ('RW', 'Rwandan'),
        ('BI', 'Burundian'),
        ('SS', 'South Sudanese'),
        ('NG', 'Nigerian'),
        ('GH', 'Ghanaian'),
        ('ZA', 'South African'),
        ('CM', 'Cameroonian'),
        ('CI', 'Ivorian'),
        ('SN', 'Senegalese'),
        ('ET', 'Ethiopian'),
        ('ER', 'Eritrean'),
        ('SO', 'Somali'),
        ('CD', 'Congolese (DRC)'),
        ('CG', 'Congolese (Brazzaville)'),
        ('EG', 'Egyptian'),
        ('MA', 'Moroccan'),
        ('TN', 'Tunisian'),
        ('DZ', 'Algerian'),
        ('LY', 'Libyan'),
        ('SD', 'Sudanese'),
        ('Other', 'Other'),
    ]
    
    BLOOD_GROUPS = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('O+', 'O+'), ('O-', 'O-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
    ]
    
    PAYMENT_PLANS = [
        ('cash', 'Full Cash Payment'),
        ('loan', 'Loan'),
        ('installment', 'Installment Plan'),
    ]
    
    full_name = models.CharField(max_length=200)
    passport_no = models.CharField(max_length=50, unique=True)
    passport_expiry = models.DateField()
    nationality = models.CharField(max_length=50, choices=NATIONALITIES, default='UG', help_text="Candidate's nationality")
    position = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=20)
    mother_name = models.CharField(max_length=100, blank=True)
    father_name = models.CharField(max_length=100, blank=True)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUPS, blank=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, related_name='candidates')
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, related_name='candidates')
    
    # Payment tracking
    initial_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, 
                                         help_text="Total amount to be paid")
    remaining_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                           help_text="Remaining balance to be paid")
    payment_plan = models.CharField(max_length=20, choices=PAYMENT_PLANS, default='cash')
    loan_provider = models.CharField(max_length=100, blank=True, help_text="If on loan, name of provider")
    loan_reference = models.CharField(max_length=100, blank=True, help_text="Loan reference number")
    fully_paid = models.BooleanField(default=False)
    fully_paid_date = models.DateField(null=True, blank=True)
    
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.full_name} - {self.passport_no}"
    
    def update_balance(self):
        """Update remaining balance based on payments"""
        from apps.candidate_payments.models import CandidatePayment
        total_paid = self.payments.aggregate(total=models.Sum('amount'))['total'] or 0
        self.remaining_balance = self.initial_amount - total_paid
        
        if self.remaining_balance <= 0:
            self.fully_paid = True
            self.fully_paid_date = timezone.now().date()
            self.remaining_balance = 0
        else:
            self.fully_paid = False
            self.fully_paid_date = None
        
        self.save()
        return self.remaining_balance
    
    def get_payment_progress(self):
        """Get payment progress percentage"""
        if self.initial_amount == 0:
            return 0
        total_paid = self.initial_amount - self.remaining_balance
        progress = (total_paid / self.initial_amount) * 100
        return int(progress)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['passport_no']),
            models.Index(fields=['created_at']),
            models.Index(fields=['fully_paid']),
            models.Index(fields=['payment_plan']),
        ]