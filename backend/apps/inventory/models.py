from django.db import models


class Stock(models.Model):
    product_variant = models.ForeignKey(
        'products.ProductVariant',
        on_delete=models.CASCADE,
        related_name='stocks'
    )
    quantity = models.IntegerField()
    reserved_quantity = models.IntegerField(default=0)
    last_restocked_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product_variant.product.name} - {self.product_variant.pack_size}"


class StockMovement(models.Model):
    MOVEMENT_TYPES = [
        ('sale', 'Sale'),
        ('purchase', 'Purchase'),
        ('audit', 'Audit'),
        ('adjustment', 'Adjustment'),
    ]
    product_variant = models.ForeignKey(
        'products.ProductVariant',
        on_delete=models.CASCADE,
        related_name='stock_movements'
    )
    movement_type = models.CharField(max_length=50, choices=MOVEMENT_TYPES)
    quantity_change = models.IntegerField()
    previous_quantity = models.IntegerField()
    new_quantity = models.IntegerField()
    reference_id = models.IntegerField(blank=True, null=True)
    reference_type = models.CharField(max_length=50, blank=True, null=True)
    reason = models.TextField(blank=True, null=True)
    moved_by = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True, related_name='stock_movements')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.movement_type} - {self.product_variant.product.name}"


class ExpiryTracking(models.Model):
    product_variant = models.ForeignKey(
        'products.ProductVariant',
        on_delete=models.CASCADE,
        related_name='expiry_tracking'
    )
    batch_number = models.CharField(max_length=100)
    expiry_date = models.DateField()
    quantity = models.IntegerField()
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product_variant.product.name} - Batch {self.batch_number}"


class StockAudit(models.Model):
    audit_number = models.CharField(max_length=100, unique=True)
    audit_date = models.DateField()
    audited_by = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True, related_name='stock_audits')
    status = models.CharField(max_length=50)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Stock Audit {self.audit_number} ({self.status})"


class StockAuditItem(models.Model):
    stock_audit = models.ForeignKey(
        StockAudit,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product_variant = models.ForeignKey(
        'products.ProductVariant',
        on_delete=models.CASCADE,
        related_name='audit_items'
    )
    system_quantity = models.IntegerField()
    physical_quantity = models.IntegerField()
    variance = models.IntegerField()
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.product_variant.product.name} - Variance {self.variance}"


class InventoryValuations(models.Model):
    valuation_date = models.DateField()
    total_quantity = models.IntegerField()
    total_cost_value = models.DecimalField(max_digits=15, decimal_places=2)
    total_retail_value = models.DecimalField(max_digits=15, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Inventory Valuation on {self.valuation_date} - Total Value: {self.total_cost_value}"


class InventoryReports(models.Model):
    report_date = models.DateField()
    total_products = models.IntegerField()
    total_stock_value = models.DecimalField(max_digits=15, decimal_places=2)
    low_stock_items = models.IntegerField()
    expiring_soon_items = models.IntegerField()
    fast_moving_items = models.JSONField()
    slow_moving_items = models.JSONField()
    out_of_stock_items = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Inventory Report on {self.report_date}"