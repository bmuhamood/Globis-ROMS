from django.db import models
from apps.clients.models import Client
from apps.placements.models import Placement
from django.contrib.auth.models import User

class Income(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='incomes')
    placement = models.OneToOneField(Placement, on_delete=models.CASCADE, null=True, blank=True, related_name='income')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    description = models.TextField(blank=True)
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Income - {self.amount} from {self.client.company_name}"
    
    class Meta:
        ordering = ['-date']

class Expense(models.Model):
    EXPENSE_CATEGORIES = [
        ('salary', 'Salary'),
        ('office_rent', 'Office Rent'),
        ('utilities', 'Utilities'),
        ('travel', 'Travel'),
        ('marketing', 'Marketing'),
        ('other', 'Other'),
    ]
    
    category = models.CharField(max_length=20, choices=EXPENSE_CATEGORIES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    description = models.TextField()
    paid_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    receipt = models.FileField(upload_to='expense_receipts/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.category} - {self.amount}"
    
    class Meta:
        ordering = ['-date']