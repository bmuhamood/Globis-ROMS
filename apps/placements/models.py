from django.db import models
from apps.candidates.models import Candidate
from apps.clients.models import Client

class Placement(models.Model):
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
    ]
    
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='placements')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='placements')
    placement_fee = models.DecimalField(max_digits=10, decimal_places=2)
    date_placed = models.DateField()
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='pending')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.candidate.full_name} -> {self.client.company_name}"
    
    class Meta:
        ordering = ['-date_placed']