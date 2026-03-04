from django.db import models
from apps.clients.models import Client
from apps.placements.models import Placement
from django.contrib.auth.models import User

class Income(models.Model):
        INCOME_TYPES = [
            ('client_payment', '💰 Client Payment'),
            ('capital_injection', '🏦 Capital Injection / Owner Investment'),
            ('loan', '💳 Loan'),
            ('other', '📦 Other Income'),
        ]
        
        PAYMENT_METHODS = [
            ('cash', 'Cash'),
            ('bank_transfer', 'Bank Transfer'),
            ('cheque', 'Cheque'),
            ('mobile_money', 'Mobile Money'),
            ('other', 'Other'),
        ]
        
        client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='incomes', null=True, blank=True,
                                help_text="Required for client payments, leave blank for capital/loans")
        placement = models.OneToOneField(Placement, on_delete=models.CASCADE, null=True, blank=True, related_name='income')
        amount = models.DecimalField(max_digits=10, decimal_places=2)
        date = models.DateField()
        
        # New fields
        income_type = models.CharField(max_length=20, choices=INCOME_TYPES, default='client_payment')
        payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')
        reference = models.CharField(max_length=100, blank=True, help_text="Receipt/Invoice/Reference number")
        source = models.CharField(max_length=100, blank=True, help_text="Source of capital (e.g., Owner, Investor, Bank)")
        
        description = models.TextField(blank=True)
        received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)
        
        # Receipt attachment
        receipt = models.FileField(upload_to='income_receipts/', blank=True, null=True)
        
        def __str__(self):
            if self.income_type == 'client_payment' and self.client:
                return f"Income: {self.amount} from {self.client.company_name}"
            elif self.income_type == 'capital_injection':
                return f"Capital Injection: {self.amount} from {self.source or 'Owner'}"
            elif self.income_type == 'loan':
                return f"Loan: {self.amount} from {self.source or 'Unknown'}"
            else:
                return f"Income: {self.amount} - {self.get_income_type_display()}"
        
        class Meta:
            ordering = ['-date']
            verbose_name = "Income"
            verbose_name_plural = "Income Records"


class CapitalInjection(models.Model):
        """Separate model for tracking capital added to the company"""
        SOURCE_TYPES = [
            ('owner', 'Owner Investment'),
            ('shareholder', 'Shareholder Investment'),
            ('loan', 'Loan'),
            ('other', 'Other'),
        ]
        
        date = models.DateField()
        amount = models.DecimalField(max_digits=10, decimal_places=2)
        source_type = models.CharField(max_length=20, choices=SOURCE_TYPES, default='owner')
        source_name = models.CharField(max_length=100, help_text="Name of investor/lender")
        reference = models.CharField(max_length=100, blank=True, help_text="Agreement/Reference number")
        description = models.TextField(blank=True)
        received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='capital_received')
        receipt = models.FileField(upload_to='capital_receipts/', blank=True, null=True)
        created_at = models.DateTimeField(auto_now_add=True)
        
        def __str__(self):
            return f"{self.get_source_type_display()}: {self.amount} from {self.source_name}"
        
        class Meta:
            ordering = ['-date']
            verbose_name = "Capital Injection"
            verbose_name_plural = "Capital Injections"


class Expense(models.Model):
        EXPENSE_CATEGORIES = [
            ('salary', '💼 Salary'),
            ('office_rent', '🏢 Office Rent'),
            ('utilities', '💡 Utilities'),
            ('travel', '✈️ Travel'),
            ('marketing', '📢 Marketing'),
            ('office_supplies', '📎 Office Supplies'),
            ('equipment', '🖥️ Equipment'),
            ('professional_fees', '⚖️ Professional Fees'),
            ('taxes', '📊 Taxes'),
            ('loan_repayment', '💳 Loan Repayment'),
            ('capital_withdrawal', '🏧 Owner Withdrawal'),
            ('other', '📦 Other'),
        ]
        
        PAYMENT_METHODS = [
            ('cash', 'Cash'),
            ('bank_transfer', 'Bank Transfer'),
            ('cheque', 'Cheque'),
            ('mobile_money', 'Mobile Money'),
            ('credit_card', 'Credit Card'),
            ('other', 'Other'),
        ]
        
        category = models.CharField(max_length=20, choices=EXPENSE_CATEGORIES)
        amount = models.DecimalField(max_digits=10, decimal_places=2)
        date = models.DateField()
        payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')
        description = models.TextField()
        reference = models.CharField(max_length=100, blank=True, help_text="Invoice/Receipt number")
        paid_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
        receipt = models.FileField(upload_to='expense_receipts/', blank=True, null=True)
        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)
        
        def __str__(self):
            return f"{self.get_category_display()}: {self.amount} on {self.date}"
        
        class Meta:
            ordering = ['-date']
            verbose_name = "Expense"
            verbose_name_plural = "Expenses"


class CashPosition(models.Model):
        """Track daily cash position"""
        date = models.DateField(unique=True)
        
        # Calculated fields (could be updated via signal or management command)
        total_income = models.DecimalField(max_digits=12, decimal_places=2, default=0)
        total_capital = models.DecimalField(max_digits=12, decimal_places=2, default=0)
        total_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=0)
        
        opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
        closing_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
        
        last_updated = models.DateTimeField(auto_now=True)
        
        class Meta:
            ordering = ['-date']
            verbose_name = "Cash Position"
            verbose_name_plural = "Cash Positions"
        
        def __str__(self):
            return f"Cash Position: {self.date} - {self.closing_balance}"