from django.db import models


class Supplier(models.Model):
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    tax_id = models.CharField(max_length=100, blank=True, null=True)
    payment_terms = models.CharField(max_length=100, blank=True, null=True)
    outstanding_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    ]

    po_number = models.CharField(max_length=100, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='purchase_orders')
    ordered_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='orders_placed')
    order_date = models.DateField()
    expected_delivery_date = models.DateField(blank=True, null=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PO-{self.po_number} ({self.supplier.name})"


class SupplierPerformanceReports(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='performance_reports')
    report_date = models.DateField()
    total_orders = models.IntegerField()
    total_amount_purchased = models.DecimalField(max_digits=10, decimal_places=2)
    on_time_deliveries = models.IntegerField()
    late_deliveries = models.IntegerField()
    average_delivery_time = models.DecimalField(max_digits=5, decimal_places=2)  
    quality_rating = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Performance Report for {self.supplier.name} on {self.report_date}"


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    purchase_variant_id = models.CharField(max_length=100)
    quantity_ordered = models.IntegerField()
    product_code = models.CharField(max_length=50)
    quantity = models.IntegerField()
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product_code} ({self.quantity} @ {self.unit_cost})"


class SupplierPayment(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='payments')
    payment_number = models.CharField(max_length=100, unique=True)
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=100)
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    paid_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment of {self.amount} to {self.supplier.name} on {self.payment_date}"


class PurchaseReport(models.Model):
    report_date = models.DateField()
    period_type = models.CharField(max_length=50)  # e.g., Monthly, Quarterly
    total_purchases = models.DecimalField(max_digits=10, decimal_places=2)
    total_items_purchased = models.IntegerField()
    total_suppliers = models.IntegerField()
    average_purchase_value = models.DecimalField(max_digits=10, decimal_places=2)
    top_supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='top_purchase_reports')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Purchase Report for {self.top_supplier.name} on {self.report_date}"


class DebitNote(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='debit_notes')
    debit_note_number = models.CharField(max_length=100, unique=True)
    issue_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    created_by = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Debit Note {self.debit_note_number} for {self.supplier.name}"


class StockMovement(models.Model):
    product_variant_id = models.CharField(max_length=100)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='stock_movements', blank=True, null=True)
    movement_type = models.CharField(max_length=50)  # e.g., Incoming, Outgoing
    quantity_change = models.IntegerField()
    previous_quantity = models.IntegerField()
    new_quantity = models.IntegerField()
    reference_id = models.CharField(max_length=100, blank=True, null=True)
    reason = models.TextField(blank=True, null=True)
    moved_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    movement_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Stock Movement ({self.movement_type}) on {self.movement_date}"


class SupplierProduct(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='products_supplied')
    product_name = models.CharField(max_length=255)
    product_code = models.CharField(max_length=50)
    cost_price = models.DecimalField(max_digits=15, decimal_places=2)
    lead_time_days = models.IntegerField()
    last_supplied_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product_name} - {self.supplier.name}"
