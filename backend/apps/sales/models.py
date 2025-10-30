from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Sale(models.Model):
    
    STATUS_CHOICES = [
        ('completed', 'Completed'),
        ('pending', 'Pending'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('mpesa', 'M-Pesa'),
        ('card', 'Card'),
        ('insurance', 'Insurance'),
        ('credit', 'Credit'),
    ]
    
    sale_number = models.CharField(max_length=100, unique=True, db_index=True)
    customer = models.ForeignKey('customers.Customer', on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')
    customer_type = models.CharField(max_length=50, default='walk-in')
    cashier = models.ForeignKey('users.User', on_delete=models.PROTECT, related_name='processed_sales')
    total_items = models.IntegerField(default=0)
    subtotal_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    change_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES)
    payment_reference = models.CharField(max_length=255, blank=True)
    sale_status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='completed', db_index=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'sales'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.sale_number}"


class SaleItem(models.Model):
    
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product_variant = models.ForeignKey('products.ProductVariant', on_delete=models.PROTECT, related_name='sale_items')
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'sale_items'
        ordering = ['id']
    
    def __str__(self):
        return f"{self.sale.sale_number} - Item {self.id}"


class Receipt(models.Model):
    
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='receipts')
    receipt_number = models.CharField(max_length=100, unique=True, db_index=True)
    amount_received = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    payment_reference = models.CharField(max_length=255, blank=True)
    payment_date = models.DateField()
    received_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='receipts_processed')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'receipts'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.receipt_number}"


class SaleReturn(models.Model):
    
    STATUS_CHOICES = [
        ('completed', 'Completed'),
        ('pending', 'Pending'),
        ('cancelled', 'Cancelled'),
    ]
    
    original_sale = models.ForeignKey(Sale, on_delete=models.PROTECT, related_name='returns')
    return_number = models.CharField(max_length=100, unique=True, db_index=True)
    cashier = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_returns')
    total_refund_amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    return_status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='completed', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'sale_returns'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.return_number}"


class ReturnItem(models.Model):
    
    return_record = models.ForeignKey(SaleReturn, on_delete=models.CASCADE, related_name='items')
    sale_item = models.ForeignKey(SaleItem, on_delete=models.PROTECT, related_name='return_items')
    quantity_returned = models.IntegerField(validators=[MinValueValidator(1)])
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'return_items'
        ordering = ['id']
    
    def __str__(self):
        return f"{self.return_record.return_number} - Item {self.id}"