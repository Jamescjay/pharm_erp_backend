from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils import timezone



class AuditModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        related_name="%(class)s_created", on_delete=models.SET_NULL
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        related_name="%(class)s_updated", on_delete=models.SET_NULL
    )

    class Meta:
        abstract = True


class ChartOfAccount(models.Model):
    ACCOUNT_TYPES = [
        ("ASSET", "Asset"),
        ("LIABILITY", "Liability"),
        ("EQUITY", "Equity"),
        ("REVENUE", "Revenue"),
        ("EXPENSE", "Expense"),
    ]

    account_code = models.CharField(max_length=50, unique=True)
    account_name = models.CharField(max_length=255)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    parent_account = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children"
    )
    is_active = models.BooleanField(default=True)
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chart_of_accounts"
        ordering = ["account_code"]
        indexes = [
            models.Index(fields=["account_code"]),
            models.Index(fields=["account_type"])
        ]

    def __str__(self):
        return f"{self.account_code} - {self.account_name}"


class JournalEntry(models.Model):
    reference_number = models.CharField(max_length=50, unique=True)
    date = models.DateField(default=timezone.now)
    description = models.TextField(blank=True)
    posted = models.BooleanField(default=False)
    posted_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = "journal_entries"
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"JE {self.reference_number} - {self.date}"


class JournalEntryLine(models.Model):
    journal_entry = models.ForeignKey("JournalEntry", related_name="lines", on_delete=models.CASCADE)
    account = models.ForeignKey("ChartOfAccount", on_delete=models.PROTECT, related_name="journal_lines")
    debit = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"))
    credit = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"))
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "journal_entry_lines"


class GeneralLedger(models.Model):
    account = models.ForeignKey("ChartOfAccount", on_delete=models.PROTECT, related_name="ledger_entries")
    transaction_date = models.DateField()
    reference_type = models.CharField(max_length=100)
    reference_id = models.PositiveIntegerField()
    debit_amount = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"))
    credit_amount = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"))
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "general_ledger"
        indexes = [
            models.Index(fields=["transaction_date"]),
            models.Index(fields=["account", "transaction_date"]),
        ]
        ordering = ["-transaction_date", "-id"]

    def __str__(self):
        return f"{self.transaction_date} | {self.account.account_code}"


class Expense(AuditModel):
    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("APPROVED", "Approved"),
        ("PAID", "Paid"),
        ("CANCELLED", "Cancelled"),
    ]

    expense_number = models.CharField(max_length=50, unique=True)
    company = models.ForeignKey("company.Company", on_delete=models.CASCADE, related_name="expenses")
    category = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    expense_date = models.DateField()
    paid_to = models.CharField(max_length=255)
    payment_method = models.CharField(max_length=50, blank=True)
    reference_number = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="DRAFT")
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        related_name="approved_expenses", on_delete=models.SET_NULL
    )

    class Meta:
        db_table = "expenses"
        ordering = ["-expense_date"]

    def __str__(self):
        return f"{self.expense_number} - {self.category}"


class SupplierPayment(AuditModel):
    supplier = models.ForeignKey("suppliers.Supplier", on_delete=models.CASCADE, related_name="payments")
    payment_number = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=50)
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    paid_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        related_name="supplier_payments", on_delete=models.SET_NULL
    )

    class Meta:
        db_table = "supplier_payments"
        ordering = ["-payment_date"]

    def __str__(self):
        return f"{self.payment_number} - {self.supplier.name}"


class PaymentAllocation(models.Model):
    payment = models.ForeignKey("SupplierPayment", on_delete=models.CASCADE, related_name="allocations")
    purchase_order = models.ForeignKey("PurchaseOrder", on_delete=models.CASCADE, related_name="payment_allocations")
    amount_allocated = models.DecimalField(max_digits=20, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payment_allocations"


class AccountsReceivable(models.Model):
    customer = models.ForeignKey("customers.Customer", on_delete=models.CASCADE, related_name="receivables")
    invoice_number = models.CharField(max_length=50)
    invoice_date = models.DateField()
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"))
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"))
    status = models.CharField(max_length=20, default="UNPAID")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "accounts_receivable"
        ordering = ["-invoice_date"]
        indexes = [
            models.Index(fields=["invoice_number"]),
            models.Index(fields=["customer"])
        ]

    def __str__(self):
        return f"AR {self.invoice_number} - {self.customer.name}"


class CustomerReceipt(AuditModel):
    customer = models.ForeignKey("customers.Customer", on_delete=models.CASCADE, related_name="receipts")
    receipt_number = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=50)
    reference_number = models.CharField(max_length=100, blank=True)
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        related_name="received_receipts", on_delete=models.SET_NULL
    )

    class Meta:
        db_table = "customer_receipts"
        ordering = ["-payment_date"]

    def __str__(self):
        return f"{self.receipt_number} - {self.customer.name}"


class ReceiptAllocation(models.Model):
    receipt = models.ForeignKey("CustomerReceipt", on_delete=models.CASCADE, related_name="allocations")
    invoice = models.ForeignKey("AccountsReceivable", on_delete=models.CASCADE, related_name="receipt_allocations")
    amount_allocated = models.DecimalField(max_digits=20, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "receipt_allocations"


class AccountsPayable(models.Model):
    supplier = models.ForeignKey("suppliers.Supplier", on_delete=models.CASCADE, related_name="payables")
    invoice_number = models.CharField(max_length=50)
    invoice_date = models.DateField()
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"))
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"))
    status = models.CharField(max_length=20, default="UNPAID")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "accounts_payable"
        ordering = ["-invoice_date"]

    def __str__(self):
        return f"AP {self.invoice_number} - {self.supplier.name}"


class FinancialReport(models.Model):
    PERIOD_CHOICES = [
        ("DAILY", "Daily"),
        ("MONTHLY", "Monthly"),
        ("QUARTERLY", "Quarterly"),
        ("YEARLY", "Yearly"),
    ]

    report_date = models.DateField()
    period_type = models.CharField(max_length=20, choices=PERIOD_CHOICES)
    total_revenue = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"))
    total_expenses = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"))
    gross_profit = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"))
    net_profit = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"))
    profit_margin = models.DecimalField(max_digits=7, decimal_places=4, default=Decimal("0.0000"))
    accounts_receivable_total = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"))
    accounts_payable_total = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"))
    cash_flow = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "financial_reports"
        ordering = ["-report_date"]

    def __str__(self):
        return f"{self.period_type} Report {self.report_date}"


class TaxRate(models.Model):
    name = models.CharField(max_length=100)
    rate = models.DecimalField(max_digits=5, decimal_places=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "tax_rates"

    def __str__(self):
        return f"{self.name} - {self.rate}%"


class TaxInvoice(models.Model):
    invoice_number = models.CharField(max_length=100, unique=True)
    customer = models.ForeignKey("customers.Customer", on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=20, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=20, decimal_places=2)
    issue_date = models.DateField(default=timezone.now)
    kra_invoice_number = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tax_invoices"

    def __str__(self):
        return f"TaxInvoice {self.invoice_number}"


class TaxReport(models.Model):
    report_date = models.DateField()
    total_sales_tax = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"))
    total_purchase_tax = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tax_reports"

    def __str__(self):
        return f"Tax Report {self.report_date}"


