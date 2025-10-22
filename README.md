# PharmERP System

## 👥 Team Responsibilities

### James - Sales, Reports & Customers Module

**Your Focus Areas:**
- Customer management and profiles
- Sales transactions and point-of-sale system
- Returns and refunds processing
- Prescription management
- All reporting and analytics dashboards
- Customer loyalty programs
- **MPesa Daraja API integration for payments**
- **Card payments with CVV processing**

**What You'll Build:**
- Customer registration and profile management
- POS interface for sales transactions with multiple payment options
- Sales receipts and invoices
- Return and refund management system
- Prescription tracking and validation
- Sales analytics dashboards
- Customer behavior reports
- Loyalty points system
- **MPesa payment processing**
- **Card payment integration**

**Key Integrations:**
- MPesa Daraja API for mobile payments
- Card payment gateway
- Email notifications to customers
- KRA tax calculations

---

### Nelly - Suppliers, Inventory & Products Module

**Your Focus Areas:**
- Product catalog management
- Supplier relationship management
- Inventory tracking and stock management
- Purchase order processing
- Goods receiving and quality control
- Expiry date tracking and management
- Product categorization and pricing
- **Email communication with suppliers**

**What You'll Build:**
- Complete product information management
- Supplier database with performance tracking
- Real-time inventory levels and alerts
- Purchase order creation and tracking
- Stock movement and adjustment system
- Batch and expiry date management
- Low stock notifications and alerts
- **Automated email to suppliers for orders**
- **Supplier communication system**

**Key Integrations:**
- Email system for supplier communications
- Inventory alerts to admin/pharmacist
- Product expiry notifications

---

### Anthony - Users & Administration Module

**Your Focus Areas:**
- User management and authentication for:
  - **Admin/Pharmacist/Manager** (Full access)
  - **Cashier/Accountant** (Limited access)
- Role-based access control system
- System settings and configuration
- Audit logs and security monitoring
- Notifications system
- User sessions and activity tracking
- **Email system for internal communications**

**What You'll Build:**
- User registration and profile management for two roles
- Permission and role management system
- System configuration panel
- Activity logging and audit trails
- Notification center
- Security protocols and access control
- **Email communication system between staff**
- **Role-specific dashboards**

---

### Hillary - Finance & Company Module

**Your Focus Areas:**
- Single company setup and management
- Financial accounting system
- Expense management and tracking
- Accounts payable and receivable
- General ledger and chart of accounts
- Payment processing and reconciliation
- Financial reporting and statements
- **KRA Kenya Revenue Authority tax integration**
- **Tax compliance and reporting**

**What You'll Build:**
- Company profile and settings management
- Chart of accounts setup
- Expense tracking and approval workflow
- Payment processing system
- Financial statements generation
- **KRA tax calculations and compliance**
- **Tax reporting and filing preparation**
- **Payment reconciliation with MPesa and cards**

**Key Integrations:**
- KRA tax rates and calculations
- MPesa transaction reconciliation
- Card payment reconciliation
- Tax-compliant invoicing

---

## 🔐 User Roles & Permissions

### Admin/Pharmacist/Manager (Full Access)
- **Full system access and control**
- **Manage suppliers and place orders**
- Approve purchase orders and payments
- Manage inventory and stock levels
- View all financial reports
- Manage user accounts
- System configuration
- **Can perform all actions in the system**

### Cashier/Accountant (Limited Access)
- **Process sales transactions**
- **View stock levels only (cannot order supplies)**
- Manage customer information
- Process returns and refunds
- View basic sales reports
- **Cannot access supplier management**
- **Cannot create purchase orders**
- **Cannot modify product catalog**
- **View-only access to inventory data**

---

## 🔗 Integration Requirements

### Payment Processing (James & Hillary)
- **MPesa Daraja API** integration for mobile payments
- **Card payment** processing with CVV security
- Payment reconciliation between sales and finance
- Receipt generation with KRA-compliant tax calculations

### Tax Compliance (Hillary & James)
- **KRA tax rates** integration
- Tax calculations on all sales
- Tax-compliant invoice generation
- Sales reports for tax filing

### Communication System (All)
- **Email notifications to customers** (order confirmations, receipts)
- **Email to suppliers** (purchase orders, payments)
- **Internal email** between admin and cashier
- Automated alerts and notifications

### Inventory Workflow (Nelly & Anthony)
- **Only Admin** can order supplies and manage suppliers
- **Cashier/Accountant** can only view stock levels
- Low stock alerts sent to Admin only
- Purchase order approval workflow

---

## 🔄 How We Work Together

### Critical Integration Points:

**James & Hillary - Payments & Taxes**
- Sales transactions with MPesa/card payments
- Real-time tax calculations using KRA rates
- Payment reconciliation and reporting

**James & Anthony - User Experience**
- Cashier-friendly POS interface with limited permissions
- Admin dashboard with full system control
- Secure authentication for payment processing

**Nelly & Anthony - Inventory Management**
- **Admin-only** access to supplier management and ordering
- **Cashier view-only** access to stock levels
- Stock alerts sent only to Admin

**Nelly & Hillary - Financial Tracking**
- Purchase order costing (Admin only)
- Supplier payment processing (Admin only)
- Inventory valuation for accounting

### Restricted Workflows:
1. **Supply Ordering**: Only Admin can access → Suppliers (Nelly) → Email to suppliers
2. **Stock Viewing**: Cashier can view but not modify → Inventory (Nelly)
3. **Financial Approvals**: Only Admin can approve payments → Finance (Hillary)

---

## 🚀 Key Features by Role

### For Cashier/Accountant (Limited Access):
- Quick sales processing with MPesa/card options
- Customer lookup and management
- Prescription validation
- Receipt printing with KRA compliance
- **View stock levels only**
- **Cannot order supplies**
- Basic sales reporting

### For Admin/Pharmacist/Manager (Full Access):
- **Full system oversight and control**
- **Supplier management and ordering**
- **Purchase order creation and approval**
- Financial reporting and approvals
- Inventory management and adjustments
- Staff management and permissions
- System configuration

---

## 📞 Support & Collaboration

- Daily sync-ups for payment and tax integration issues
- Weekly meetings for cross-module testing
- Shared channel for payment gateway issues
- Document all API integrations (MPesa, KRA, Email)

*Remember: We're building a complete pharmacy system with strict role separation - Admin handles ordering, Cashier handles sales!*