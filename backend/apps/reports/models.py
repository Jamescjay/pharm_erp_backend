from django.db import models
from decimal import Decimal


class DailySalesSummary(models.Model):
    
    summary_date = models.DateField(unique=True, db_index=True)
    total_sales = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_transactions = models.IntegerField(default=0)
    total_customers = models.IntegerField(default=0)
    cash_sales = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    mpesa_sales = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    card_sales = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_profit = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'daily_sales_summary'
        ordering = ['-summary_date']
    
    def __str__(self):
        return f"Daily Sales - {self.summary_date}"


class InventoryValuation(models.Model):
    
    valuation_date = models.DateField(unique=True, db_index=True)
    total_quantity = models.IntegerField(default=0)
    total_cost_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_retail_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'inventory_valuations'
        ordering = ['-valuation_date']
    
    def __str__(self):
        return f"Inventory Valuation - {self.valuation_date}"


class CustomerAnalytics(models.Model):
    
    customer = models.OneToOneField('customers.Customer', on_delete=models.CASCADE, related_name='analytics')
    total_orders = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    last_order_date = models.DateTimeField(null=True, blank=True)
    favorite_category = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'customer_analytics'
    
    def __str__(self):
        return f"Analytics - {self.customer}"


class ProfitabilityReport(models.Model):
    
    PERIOD_TYPE_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    report_date = models.DateField(db_index=True)
    period_type = models.CharField(max_length=50, choices=PERIOD_TYPE_CHOICES)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    gross_profit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    operating_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    net_profit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    profit_margin = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'profitability_reports'
        ordering = ['-report_date']
        unique_together = ['report_date', 'period_type']
    
    def __str__(self):
        return f"Profitability - {self.period_type} - {self.report_date}"


class PurchaseReport(models.Model):
    
    PERIOD_TYPE_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    report_date = models.DateField(db_index=True)
    period_type = models.CharField(max_length=50, choices=PERIOD_TYPE_CHOICES)
    total_purchases = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_items_purchased = models.IntegerField(default=0)
    total_suppliers = models.IntegerField(default=0)
    average_purchase_value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    top_supplier = models.ForeignKey('suppliers.Supplier', on_delete=models.SET_NULL, null=True, blank=True, related_name='top_supplier_reports')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'purchase_reports'
        ordering = ['-report_date']
        unique_together = ['report_date', 'period_type']
    
    def __str__(self):
        return f"Purchase Report - {self.period_type} - {self.report_date}"


class SalesReport(models.Model):
    
    PERIOD_TYPE_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    report_date = models.DateField(db_index=True)
    period_type = models.CharField(max_length=50, choices=PERIOD_TYPE_CHOICES)
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_transactions = models.IntegerField(default=0)
    total_items_sold = models.IntegerField(default=0)
    average_transaction_value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    top_product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True, blank=True, related_name='top_product_reports')
    top_customer = models.ForeignKey('customers.Customer', on_delete=models.SET_NULL, null=True, blank=True, related_name='top_customer_reports')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'sales_reports'
        ordering = ['-report_date']
        unique_together = ['report_date', 'period_type']
    
    def __str__(self):
        return f"Sales Report - {self.period_type} - {self.report_date}"


class InventoryReport(models.Model):
    
    report_date = models.DateField(unique=True, db_index=True)
    total_products = models.IntegerField(default=0)
    total_stock_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    low_stock_items = models.IntegerField(default=0)
    expiring_soon_items = models.IntegerField(default=0)
    out_of_stock_items = models.IntegerField(default=0)
    fast_moving_products = models.JSONField(null=True, blank=True)
    slow_moving_products = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'inventory_reports'
        ordering = ['-report_date']
    
    def __str__(self):
        return f"Inventory Report - {self.report_date}"


class FinancialReport(models.Model):
    
    PERIOD_TYPE_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    report_date = models.DateField(db_index=True)
    period_type = models.CharField(max_length=50, choices=PERIOD_TYPE_CHOICES)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    gross_profit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    net_profit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    profit_margin = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    accounts_receivable_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    accounts_payable_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    cash_flow = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'financial_reports'
        ordering = ['-report_date']
        unique_together = ['report_date', 'period_type']
    
    def __str__(self):
        return f"Financial Report - {self.period_type} - {self.report_date}"


class SupplierPerformanceReport(models.Model):
    
    report_date = models.DateField(db_index=True)
    supplier = models.ForeignKey('suppliers.Supplier', on_delete=models.CASCADE, related_name='performance_reports')
    total_orders = models.IntegerField(default=0)
    total_amount_purchased = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    on_time_deliveries = models.IntegerField(default=0)
    late_deliveries = models.IntegerField(default=0)
    average_delivery_time = models.IntegerField(default=0)
    quality_rating = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'supplier_performance_reports'
        ordering = ['-report_date']
    
    def __str__(self):
        return f"Supplier Performance - {self.supplier.name} - {self.report_date}"


class CustomerReport(models.Model):
    
    PERIOD_TYPE_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    report_date = models.DateField(db_index=True)
    period_type = models.CharField(max_length=50, choices=PERIOD_TYPE_CHOICES)
    total_customers = models.IntegerField(default=0)
    new_customers = models.IntegerField(default=0)
    returning_customers = models.IntegerField(default=0)
    total_loyalty_points_issued = models.IntegerField(default=0)
    average_customer_value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    top_customers = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'customer_reports'
        ordering = ['-report_date']
        unique_together = ['report_date', 'period_type']
    
    def __str__(self):
        return f"Customer Report - {self.period_type} - {self.report_date}"


class ExpiryReport(models.Model):
    
    report_date = models.DateField(unique=True, db_index=True)
    expired_items = models.IntegerField(default=0)
    expired_items_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    expiring_this_month = models.IntegerField(default=0)
    expiring_this_month_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    expiring_next_month = models.IntegerField(default=0)
    expiring_next_month_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    expired_items_list = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'expiry_reports'
        ordering = ['-report_date']
    
    def __str__(self):
        return f"Expiry Report - {self.report_date}"