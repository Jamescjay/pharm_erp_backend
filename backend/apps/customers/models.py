from django.db import models
from decimal import Decimal


class CustomerType(models.Model):
    
    name = models.CharField(max_length=100)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    credit_limit = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'customer_types'
    
    def __str__(self):
        return self.name


class Customer(models.Model):
    
    customer_type = models.ForeignKey(CustomerType, on_delete=models.SET_NULL, null=True, blank=True, related_name='customers')
    customer_code = models.CharField(max_length=100, unique=True, null=True, blank=True, db_index=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    company_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20)
    address = models.TextField(blank=True)
    id_number = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    loyalty_points = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    outstanding_balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    last_purchase_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'customers'
        ordering = ['-created_at']
    
    def __str__(self):
        if self.company_name:
            return self.company_name
        return f"{self.first_name} {self.last_name}".strip() or f"Customer {self.id}"


class CreditNote(models.Model):
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('settled', 'Settled'),
    ]
    
    credit_note_number = models.CharField(max_length=100, unique=True, db_index=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='credit_notes')
    sale = models.ForeignKey('sales.Sale', on_delete=models.SET_NULL, null=True, blank=True, related_name='credit_notes')
    issue_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending', db_index=True)
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_credit_notes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'credit_notes'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.credit_note_number}"


class CustomerStatement(models.Model):
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='statements')
    statement_date = models.DateField()
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_payments = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    closing_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'customer_statements'
        ordering = ['-statement_date']
    
    def __str__(self):
        return f"Statement - {self.customer} - {self.statement_date}"