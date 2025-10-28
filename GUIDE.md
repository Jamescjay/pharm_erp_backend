markdown
# Pharmacy Management System - APIs & Integrations

## 🔌 External Integrations

### Payment Integrations (James)
**MPesa Daraja API:**
```python
- /oauth/v1/generate (Access Token)
- /mpesa/stkpush/v1/processrequest (STK Push)
- /mpesa/stkpushquery/v1/query (Transaction Status)
- /mpesa/transactionstatus/v1/query (Transaction Details)

Card Payment Gateway:
python
- /api/v1/payments/charge (Process card payment)
- /api/v1/payments/refund (Process refund)
- /api/v1/payments/verify (Verify transaction)

Tax Integration (Hillary)

KRA (Kenya Revenue Authority):

python
- /api/v1/tax/calculate (Calculate VAT and other taxes)
- /api/v1/invoices/submit (Submit electronic invoices)
- /api/v1/reports/generate (Generate tax reports)

Email Service Integration (All)
Email API (SendGrid/Mailgun):
python
- /v3/mail/send (Send emails)
- /v3/templates (Email templates)

📡 JAMES - Sales & Customers APIs
Customer Management
python
POST   /api/customers/                 # Create new customer
GET    /api/customers/                 # List all customers
GET    /api/customers/{id}/            # Get customer details
PUT    /api/customers/{id}/            # Update customer
GET    /api/customers/{id}/prescriptions/ # Get customer prescriptions
POST   /api/customers/{id}/loyalty/    # Update loyalty points
Sales Processing
python
POST   /api/sales/                     # Create new sale
GET    /api/sales/                     # List sales with filters
GET    /api/sales/{id}/                # Get sale details
POST   /api/sales/{id}/process-payment/ # Process payment
POST   /api/sales/{id}/mpesa-payment/  # Process MPesa payment
POST   /api/sales/{id}/card-payment/   # Process card payment
POST   /api/sales/{id}/complete/       # Complete sale
POST   /api/sales/{id}/return/         # Process return
Prescription Management
python
POST   /api/prescriptions/             # Create prescription
GET    /api/prescriptions/             # List prescriptions
GET    /api/prescriptions/{id}/        # Get prescription details
PUT    /api/prescriptions/{id}/status/ # Update prescription status
Reports
python
GET    /api/reports/sales/daily/       # Daily sales report
GET    /api/reports/sales/monthly/     # Monthly sales report
GET    /api/reports/customers/top/     # Top customers report
GET    /api/reports/products/top/      # Top selling products
GET    /api/reports/payments/summary/  # Payment methods summary


📦 NELLY - Inventory & Products APIs
Product Management
python
POST   /api/products/                  # Create new product (Admin only)
GET    /api/products/                  # List all products
GET    /api/products/{id}/             # Get product details
PUT    /api/products/{id}/             # Update product (Admin only)
GET    /api/products/search/           # Search products
POST   /api/products/{id}/variants/    # Add product variant (Admin only)
Inventory Management
python
GET    /api/inventory/stock-levels/    # Get all stock levels
GET    /api/inventory/stock/{id}/      # Get specific stock level
POST   /api/inventory/adjustments/     # Stock adjustment (Admin only)
GET    /api/inventory/low-stock/       # Get low stock items
GET    /api/inventory/expiring-soon/   # Get expiring soon items
POST   /api/inventory/stock-audit/     # Create stock audit (Admin only)
Supplier Management
python
POST   /api/suppliers/                 # Create supplier (Admin only)
GET    /api/suppliers/                 # List all suppliers
GET    /api/suppliers/{id}/            # Get supplier details
PUT    /api/suppliers/{id}/            # Update supplier (Admin only)
POST   /api/suppliers/{id}/email/      # Send email to supplier
Purchase Orders
python
POST   /api/purchase-orders/           # Create PO (Admin only)
GET    /api/purchase-orders/           # List all POs
GET    /api/purchase-orders/{id}/      # Get PO details
PUT    /api/purchase-orders/{id}/status/ # Update PO status (Admin only)
POST   /api/purchase-orders/{id}/email/ # Email PO to supplier
Goods Receiving
python
POST   /api/goods-received/            # Create GRN (Admin only)
GET    /api/goods-received/            # List all GRNs
GET    /api/goods-received/{id}/       # Get GRN details
POST   /api/goods-received/{id}/items/ # Add received items (Admin only)


👤 ANTHONY - Users & Administration APIs
User Management
python
POST   /api/users/                     # Create user (Admin only)
GET    /api/users/                     # List all users
GET    /api/users/{id}/                # Get user details
PUT    /api/users/{id}/                # Update user (Admin only)
PUT    /api/users/{id}/status/         # Activate/deactivate user (Admin only)
Authentication
python
POST   /api/auth/login/                # User login
POST   /api/auth/logout/               # User logout
POST   /api/auth/refresh/              # Refresh token
POST   /api/auth/change-password/      # Change password
POST   /api/auth/reset-password/       # Request password reset
Permissions & Roles
python
GET    /api/permissions/               # Get all permissions
PUT    /api/users/{id}/permissions/    # Update user permissions (Admin only)
GET    /api/roles/                     # Get available roles
System Administration
python
GET    /api/settings/                  # Get system settings
PUT    /api/settings/                  # Update system settings (Admin only)
GET    /api/audit-logs/                # Get audit logs (Admin only)
GET    /api/notifications/             # Get user notifications
PUT    /api/notifications/{id}/read/   # Mark notification as read


💰 HILLARY - Finance & Company APIs
Company Management
python
GET    /api/company/                   # Get company details
PUT    /api/company/                   # Update company details (Admin only)
Financial Accounts
python
GET    /api/accounts/chart-of-accounts/ # Get chart of accounts
POST   /api/accounts/chart-of-accounts/ # Add account (Admin only)
GET    /api/accounts/general-ledger/   # Get general ledger
POST   /api/accounts/journal-entry/    # Create journal entry (Admin only)
Expense Management
python
POST   /api/expenses/                  # Create expense (Admin only)
GET    /api/expenses/                  # List all expenses
GET    /api/expenses/{id}/             # Get expense details
PUT    /api/expenses/{id}/status/      # Update expense status (Admin only)
Payment Processing
python
POST   /api/payments/supplier/         # Pay supplier (Admin only)
GET    /api/payments/supplier/         # List supplier payments
POST   /api/payments/allocate/         # Allocate payment to PO (Admin only)
Tax & Compliance
python
GET    /api/tax/calculate/             # Calculate tax for sale
POST   /api/tax/invoice/               # Generate KRA invoice
GET    /api/tax/reports/               # Generate tax reports
Financial Reports
python
GET    /api/reports/financial/daily/   # Daily financial summary
GET    /api/reports/financial/monthly/ # Monthly financial report
GET    /api/reports/accounts-receivable/ # Accounts receivable report
GET    /api/reports/accounts-payable/  # Accounts payable report
GET    /api/reports/profit-loss/       # Profit & loss statement
GET    /api/reports/cash-flow/         # Cash flow statement


🔄 Cross-Module Integration APIs
Stock Updates (Nelly → James)
python
POST   /api/inventory/update-stock/    # Update stock after sale
GET    /api/inventory/check-stock/{product_variant_id}/ # Check stock before sale
Financial Postings (All → Hillary)
python
POST   /api/finance/post-transaction/  # Post transaction to ledger
GET    /api/finance/account-balance/{account_id}/ # Get account balance
Email Notifications (All)
python
POST   /api/notifications/email/       # Send email notification
POST   /api/notifications/sms/         # Send SMS notification
Dashboard Data (All)
python
GET    /api/dashboard/summary/         # Get dashboard summary
GET    /api/dashboard/alerts/          # Get system alerts


🛡️ API Security & Permissions

Admin/Pharmacist/Manager (Full Access)

All POST, PUT, DELETE endpoints
Financial data access
Supplier management
User management

Cashier/Accountant (Limited Access)

GET /api/products/
GET /api/inventory/stock-levels/
POST /api/sales/
GET /api/customers/
GET /api/reports/sales/daily/
NO supplier or purchase order access
NO user management access
NO financial configuration access