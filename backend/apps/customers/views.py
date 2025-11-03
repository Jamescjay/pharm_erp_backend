from decimal import Decimal
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Customer, CustomerType, CreditNote, CustomerStatement
from .serializers import (
    CustomerSerializer, CustomerTypeSerializer,
    CreditNoteSerializer, CustomerStatementSerializer,
    CustomerCreateSerializer
)


class CustomerTypeViewSet(viewsets.ModelViewSet):
    """Customer type management"""
    queryset = CustomerType.objects.all()
    serializer_class = CustomerTypeSerializer
    permission_classes = [IsAuthenticated]


class CustomerViewSet(viewsets.ModelViewSet):
    """
    Complete Customer Management
    - Registration
    - Profile management
    - Purchase history
    - Loyalty points
    """
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Customer.objects.all()
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Search by name, email, or phone
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(first_name__icontains=search) |
                models.Q(last_name__icontains=search) |
                models.Q(email__icontains=search) |
                models.Q(phone__icontains=search) |
                models.Q(company_name__icontains=search)
            )
        
        # Filter by customer type
        customer_type = self.request.query_params.get('customer_type')
        if customer_type:
            queryset = queryset.filter(customer_type_id=customer_type)
        
        return queryset.order_by('-created_at')
    
    def create(self, request):
        """Register new customer"""
        serializer = CustomerCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Check if customer with phone already exists
        phone = request.data.get('phone')
        if Customer.objects.filter(phone=phone).exists():
            return Response({
                'error': 'Customer with this phone number already exists'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate customer code
        customer_code = self._generate_customer_code()
        
        customer = serializer.save(customer_code=customer_code)
        
        # Send welcome email if email provided
        if customer.email:
            self._send_welcome_email(customer)
        
        return Response(CustomerSerializer(customer).data, status=status.HTTP_201_CREATED)
    
    def _generate_customer_code(self):
        """Generate unique customer code"""
        last_customer = Customer.objects.order_by('-id').first()
        if last_customer and last_customer.customer_code:
            try:
                last_num = int(last_customer.customer_code.split('-')[1])
                new_num = last_num + 1
            except:
                new_num = 1
        else:
            new_num = 1
        
        return f"CUST-{new_num:05d}"
    
    def _send_welcome_email(self, customer):
        """Send welcome email to new customer"""
        subject = 'Welcome to Our Pharmacy!'
        message = f"""
        Dear {customer.first_name or customer.company_name},
        
        Welcome to our pharmacy! Your customer account has been created successfully.
        
        Customer Code: {customer.customer_code}
        
        Benefits of being a registered customer:
        - Earn loyalty points on every purchase
        - Get exclusive discounts
        - Track your purchase history
        - Receive email receipts
        
        Thank you for choosing us!
        
        Best regards,
        Pharmacy Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [customer.email],
            fail_silently=True,
        )
    
    @action(detail=True, methods=['get'])
    def purchase_history(self, request, pk=None):
        """Get customer purchase history"""
        customer = self.get_object()
        
        # Get all sales for this customer
        from sales.models import Sale
        from sales.serializers import SaleSerializer
        
        sales = Sale.objects.filter(
            customer=customer,
            sale_status='completed'
        ).order_by('-created_at')
        
        # Apply date filters if provided
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date and end_date:
            sales = sales.filter(created_at__date__range=[start_date, end_date])
        
        page = self.paginate_queryset(sales)
        if page is not None:
            serializer = SaleSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = SaleSerializer(sales, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Get customer analytics"""
        customer = self.get_object()
        from sales.models import Sale
        
        sales = Sale.objects.filter(customer=customer, sale_status='completed')
        
        analytics = {
            'total_purchases': sales.count(),
            'total_spent': customer.total_spent,
            'average_order_value': sales.aggregate(avg=Avg('total_amount'))['avg'] or 0,
            'loyalty_points': customer.loyalty_points,
            'outstanding_balance': customer.outstanding_balance,
            'last_purchase_date': customer.last_purchase_date,
            'customer_since': customer.created_at,
            'purchase_frequency': self._calculate_purchase_frequency(customer),
        }
        
        return Response(analytics)
    
    def _calculate_purchase_frequency(self, customer):
        """Calculate average days between purchases"""
        from sales.models import Sale
        
        sales = Sale.objects.filter(
            customer=customer,
            sale_status='completed'
        ).order_by('created_at')
        
        if sales.count() < 2:
            return None
        
        dates = list(sales.values_list('created_at', flat=True))
        total_days = (dates[-1] - dates[0]).days
        
        if total_days == 0:
            return 0
        
        return total_days / (len(dates) - 1)
    
    @action(detail=True, methods=['post'])
    def update_loyalty_points(self, request, pk=None):
        """Manually update customer loyalty points"""
        customer = self.get_object()
        
        points = request.data.get('points', 0)
        action_type = request.data.get('action', 'add')  # add or deduct
        reason = request.data.get('reason', '')
        
        if action_type == 'add':
            customer.loyalty_points += int(points)
        elif action_type == 'deduct':
            customer.loyalty_points = max(0, customer.loyalty_points - int(points))
        
        customer.save()
        
        # Send email notification
        if customer.email:
            self._send_loyalty_update_email(customer, points, action_type, reason)
        
        return Response({
            'success': True,
            'message': f'Loyalty points {action_type}ed successfully',
            'current_points': customer.loyalty_points
        })
    
    def _send_loyalty_update_email(self, customer, points, action_type, reason):
        """Send loyalty points update email"""
        subject = 'Loyalty Points Update'
        action_text = 'added to' if action_type == 'add' else 'deducted from'
        
        message = f"""
        Dear {customer.first_name},
        
        Your loyalty points have been updated.
        
        Points {action_text}: {points}
        Reason: {reason}
        
        Current Balance: {customer.loyalty_points} points
        
        Thank you for your continued patronage!
        
        Best regards,
        Pharmacy Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [customer.email],
            fail_silently=True,
        )
    
    @action(detail=True, methods=['post'])
    def send_statement(self, request, pk=None):
        """Send account statement to customer"""
        customer = self.get_object()
        
        if not customer.email:
            return Response({
                'error': 'Customer has no email address'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate statement
        statement = self._generate_customer_statement(customer)
        
        # Send email
        subject = f'Account Statement - {timezone.now().strftime("%B %Y")}'
        message = f"""
        Dear {customer.first_name or customer.company_name},
        
        Please find your account statement below:
        
        Statement Period: {statement['period']}
        Opening Balance: KES {statement['opening_balance']}
        Total Purchases: KES {statement['total_purchases']}
        Total Payments: KES {statement['total_payments']}
        Closing Balance: KES {statement['closing_balance']}
        
        Loyalty Points: {customer.loyalty_points}
        
        Thank you for your business!
        
        Best regards,
        Pharmacy Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [customer.email],
            fail_silently=True,
        )
        
        # Save statement record
        CustomerStatement.objects.create(
            customer=customer,
            statement_date=timezone.now().date(),
            opening_balance=statement['opening_balance'],
            total_sales=statement['total_purchases'],
            total_payments=statement['total_payments'],
            closing_balance=statement['closing_balance']
        )
        
        return Response({
            'success': True,
            'message': 'Statement sent successfully'
        })
    
    def _generate_customer_statement(self, customer):
        """Generate customer statement data"""
        from sales.models import Sale
        
        # Get current month data
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        sales = Sale.objects.filter(
            customer=customer,
            sale_status='completed',
            created_at__gte=start_of_month
        )
        
        total_purchases = sales.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        # For simplicity, assuming payments reduce outstanding balance
        total_payments = Decimal('0.00')  # Would come from payment records
        
        return {
            'period': f"{start_of_month.strftime('%B %Y')}",
            'opening_balance': customer.outstanding_balance,
            'total_purchases': total_purchases,
            'total_payments': total_payments,
            'closing_balance': customer.outstanding_balance + total_purchases - total_payments
        }


class CreditNoteViewSet(viewsets.ModelViewSet):
    """Credit note management"""
    queryset = CreditNote.objects.all()
    serializer_class = CreditNoteSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = CreditNote.objects.all()
        
        # Filter by customer
        customer_id = self.request.query_params.get('customer_id')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        
        # Filter by status
        credit_status = self.request.query_params.get('status')
        if credit_status:
            queryset = queryset.filter(status=credit_status)
        
        return queryset.order_by('-created_at')
    
    def create(self, request):
        """Create credit note"""
        serializer = CreditNoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Generate credit note number
        credit_note_number = self._generate_credit_note_number()
        
        credit_note = serializer.save(
            credit_note_number=credit_note_number,
            created_by=request.user,
            status='pending'
        )
        
        # Send email to customer
        if credit_note.customer.email:
            self._send_credit_note_email(credit_note)
        
        return Response(CreditNoteSerializer(credit_note).data, status=status.HTTP_201_CREATED)
    
    def _generate_credit_note_number(self):
        """Generate unique credit note number"""
        from django.utils import timezone
        date_str = timezone.now().strftime('%Y%m%d')
        
        last_note = CreditNote.objects.filter(
            credit_note_number__startswith=f'CN-{date_str}'
        ).order_by('-credit_note_number').first()
        
        if last_note:
            last_num = int(last_note.credit_note_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        
        return f'CN-{date_str}-{new_num:03d}'
    
    def _send_credit_note_email(self, credit_note):
        """Send credit note email to customer"""
        subject = f'Credit Note - {credit_note.credit_note_number}'
        message = f"""
        Dear {credit_note.customer.first_name},
        
        A credit note has been issued for your account.
        
        Credit Note Number: {credit_note.credit_note_number}
        Amount: KES {credit_note.amount}
        Date: {credit_note.issue_date}
        Reason: {credit_note.reason}
        
        This credit will be applied to your account balance.
        
        Best regards,
        Pharmacy Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [credit_note.customer.email],
            fail_silently=True,
        )
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve credit note"""
        credit_note = self.get_object()
        
        if credit_note.status != 'pending':
            return Response({
                'error': 'Credit note already processed'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        credit_note.status = 'approved'
        credit_note.save()
        
        # Update customer balance
        customer = credit_note.customer
        customer.outstanding_balance -= credit_note.amount
        customer.save()
        
        # Send email notification
        if customer.email:
            subject = f'Credit Note Approved - {credit_note.credit_note_number}'
            message = f"""
            Dear {customer.first_name},
            
            Your credit note has been approved and applied to your account.
            
            Credit Note: {credit_note.credit_note_number}
            Amount: KES {credit_note.amount}
            New Balance: KES {customer.outstanding_balance}
            
            Best regards,
            Pharmacy Team
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [customer.email],
                fail_silently=True,
            )
        
        return Response({
            'success': True,
            'message': 'Credit note approved successfully'
        })


class CustomerStatementViewSet(viewsets.ReadOnlyModelViewSet):
    """Customer statement viewing"""
    queryset = CustomerStatement.objects.all()
    serializer_class = CustomerStatementSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = CustomerStatement.objects.all()
        
        # Filter by customer
        customer_id = self.request.query_params.get('customer_id')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        
        return queryset.order_by('-statement_date')