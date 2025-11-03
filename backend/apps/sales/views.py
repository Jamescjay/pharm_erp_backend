import os
import requests
import json
from datetime import datetime, timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Sale, SaleItem, Receipt, SaleReturn, ReturnItem
from .serializers import (
    SaleSerializer, SaleItemSerializer, ReceiptSerializer,
    SaleReturnSerializer, ReturnItemSerializer, SaleCreateSerializer
)
from backend.apps.customers.models import Customer
from backend.apps.products.models import ProductVariant
from backend.apps.inventory.models import Stock


class PesapalPaymentService:
    """Service class for Pesapal payment integration"""
    
    def __init__(self):
        self.base_url = os.getenv('PESAPAL_BASE_URL', 'https://cybqa.pesapal.com/pesapalv3')
        self.consumer_key = os.getenv('PESAPAL_CONSUMER_KEY')
        self.consumer_secret = os.getenv('PESAPAL_CONSUMER_SECRET')
        self.ipn_id = os.getenv('PESAPAL_IPN_ID')
        self.callback_url = os.getenv('PESAPAL_CALLBACK_URL', 'http://localhost:8000/api/sales/payment-callback/')
        self.token = None
        self.token_expiry = None
    
    def get_access_token(self):
        """Get or refresh Pesapal access token"""
        if self.token and self.token_expiry and timezone.now() < self.token_expiry:
            return self.token
        
        url = f"{self.base_url}/api/Auth/RequestToken"
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        payload = {
            'consumer_key': self.consumer_key,
            'consumer_secret': self.consumer_secret
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            self.token = data.get('token')
            self.token_expiry = timezone.now() + timedelta(seconds=data.get('expiryDate', 3600))
            return self.token
        except Exception as e:
            raise Exception(f"Failed to get Pesapal token: {str(e)}")
    
    def submit_order_request(self, sale_data):
        """Submit order to Pesapal for payment"""
        token = self.get_access_token()
        
        url = f"{self.base_url}/api/Transactions/SubmitOrderRequest"
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        
        payload = {
            'id': sale_data['merchant_reference'],
            'currency': 'KES',
            'amount': float(sale_data['amount']),
            'description': sale_data['description'],
            'callback_url': self.callback_url,
            'notification_id': self.ipn_id,
            'billing_address': {
                'email_address': sale_data.get('email', ''),
                'phone_number': sale_data.get('phone', ''),
                'country_code': 'KE',
                'first_name': sale_data.get('first_name', ''),
                'last_name': sale_data.get('last_name', ''),
            }
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"Failed to submit order to Pesapal: {str(e)}")
    
    def get_transaction_status(self, order_tracking_id):
        """Get transaction status from Pesapal"""
        token = self.get_access_token()
        
        url = f"{self.base_url}/api/Transactions/GetTransactionStatus"
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        params = {'orderTrackingId': order_tracking_id}
        
        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"Failed to get transaction status: {str(e)}")


class SaleViewSet(viewsets.ModelViewSet):
    """
    Complete Sales Management ViewSet
    Handles sales creation, payment processing, and completion
    """
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Sale.objects.all()
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date and end_date:
            queryset = queryset.filter(created_at__date__range=[start_date, end_date])
        
        # Filter by customer
        customer_id = self.request.query_params.get('customer_id')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        
        # Filter by status
        sale_status = self.request.query_params.get('status')
        if sale_status:
            queryset = queryset.filter(sale_status=sale_status)
        
        return queryset.order_by('-created_at')
    
    @transaction.atomic
    def create(self, request):
        """Create new sale"""
        serializer = SaleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Validate stock availability
        items = request.data.get('items', [])
        for item in items:
            try:
                stock = Stock.objects.get(product_variant_id=item['product_variant_id'])
                if stock.quantity < item['quantity']:
                    return Response({
                        'error': f"Insufficient stock for product variant {item['product_variant_id']}"
                    }, status=status.HTTP_400_BAD_REQUEST)
            except Stock.DoesNotExist:
                return Response({
                    'error': f"Product variant {item['product_variant_id']} not found in stock"
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create sale
        sale = serializer.save(cashier=request.user, sale_status='pending')
        
        # Create sale items
        total_amount = Decimal('0.00')
        for item in items:
            variant = ProductVariant.objects.get(id=item['product_variant_id'])
            quantity = item['quantity']
            unit_price = variant.selling_price
            discount = item.get('discount_amount', Decimal('0.00'))
            total_price = (unit_price * quantity) - discount
            
            SaleItem.objects.create(
                sale=sale,
                product_variant=variant,
                quantity=quantity,
                unit_price=unit_price,
                discount_amount=discount,
                total_price=total_price,
                cost_price=variant.purchase_price
            )
            total_amount += total_price
        
        # Update sale totals
        sale.total_items = len(items)
        sale.subtotal_amount = total_amount
        sale.total_amount = total_amount
        sale.save()
        
        return Response(SaleSerializer(sale).data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def process_payment(self, request, pk=None):
        """Process payment for a sale using Pesapal"""
        sale = self.get_object()
        
        if sale.sale_status == 'completed':
            return Response({
                'error': 'Sale already completed'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        payment_method = request.data.get('payment_method')
        
        if payment_method == 'cash':
            return self._process_cash_payment(sale, request.data)
        elif payment_method in ['mpesa', 'card']:
            return self._process_pesapal_payment(sale, request.data)
        else:
            return Response({
                'error': 'Invalid payment method'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def _process_cash_payment(self, sale, data):
        """Process cash payment"""
        amount_paid = Decimal(str(data.get('amount_paid', 0)))
        
        if amount_paid < sale.total_amount:
            return Response({
                'error': 'Insufficient amount paid'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            sale.amount_paid = amount_paid
            sale.change_amount = amount_paid - sale.total_amount
            sale.payment_method = 'cash'
            sale.sale_status = 'completed'
            sale.save()
            
            # Update stock
            self._update_stock(sale)
            
            # Update customer loyalty points if registered
            if sale.customer:
                self._update_loyalty_points(sale.customer, sale.total_amount)
            
            # Create receipt
            receipt = Receipt.objects.create(
                sale=sale,
                amount_received=amount_paid,
                payment_method='cash',
                payment_date=timezone.now().date(),
                received_by=self.request.user
            )
            
            # Send email receipt if customer is registered
            if sale.customer and sale.customer.email:
                self._send_receipt_email(sale, receipt)
        
        return Response({
            'success': True,
            'message': 'Payment processed successfully',
            'sale': SaleSerializer(sale).data,
            'receipt': ReceiptSerializer(receipt).data
        })
    
    def _process_pesapal_payment(self, sale, data):
        """Process Pesapal payment (MPesa/Card)"""
        try:
            pesapal = PesapalPaymentService()
            
            # Prepare payment data
            payment_data = {
                'merchant_reference': sale.sale_number,
                'amount': str(sale.total_amount),
                'description': f'Payment for {sale.sale_number}',
                'email': data.get('email', sale.customer.email if sale.customer else ''),
                'phone': data.get('phone', sale.customer.phone if sale.customer else ''),
                'first_name': data.get('first_name', sale.customer.first_name if sale.customer else ''),
                'last_name': data.get('last_name', sale.customer.last_name if sale.customer else ''),
            }
            
            # Submit order to Pesapal
            response = pesapal.submit_order_request(payment_data)
            
            # Store order tracking ID
            sale.payment_reference = response.get('order_tracking_id')
            sale.payment_method = data.get('payment_method')
            sale.save()
            
            return Response({
                'success': True,
                'message': 'Payment initiated',
                'redirect_url': response.get('redirect_url'),
                'order_tracking_id': response.get('order_tracking_id')
            })
        
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def payment_callback(self, request):
        """Handle Pesapal payment callback"""
        order_tracking_id = request.query_params.get('OrderTrackingId')
        merchant_reference = request.query_params.get('OrderMerchantReference')
        
        try:
            sale = Sale.objects.get(sale_number=merchant_reference)
            pesapal = PesapalPaymentService()
            
            # Get transaction status
            transaction_status = pesapal.get_transaction_status(order_tracking_id)
            
            if transaction_status.get('payment_status_description') == 'Completed':
                with transaction.atomic():
                    sale.sale_status = 'completed'
                    sale.amount_paid = Decimal(str(transaction_status.get('amount')))
                    sale.payment_reference = transaction_status.get('confirmation_code')
                    sale.save()
                    
                    # Update stock
                    self._update_stock(sale)
                    
                    # Update loyalty points
                    if sale.customer:
                        self._update_loyalty_points(sale.customer, sale.total_amount)
                    
                    # Create receipt
                    receipt = Receipt.objects.create(
                        sale=sale,
                        amount_received=sale.amount_paid,
                        payment_method=sale.payment_method,
                        payment_reference=sale.payment_reference,
                        payment_date=timezone.now().date(),
                        received_by=sale.cashier
                    )
                    
                    # Send email receipt
                    if sale.customer and sale.customer.email:
                        self._send_receipt_email(sale, receipt)
                
                return Response({
                    'success': True,
                    'message': 'Payment completed successfully'
                })
            else:
                sale.sale_status = 'cancelled'
                sale.notes = transaction_status.get('description', 'Payment failed')
                sale.save()
                
                return Response({
                    'success': False,
                    'message': 'Payment failed',
                    'reason': transaction_status.get('description')
                })
        
        except Sale.DoesNotExist:
            return Response({
                'error': 'Sale not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def _update_stock(self, sale):
        """Update stock levels after sale"""
        for item in sale.items.all():
            stock = Stock.objects.get(product_variant=item.product_variant)
            stock.quantity -= item.quantity
            stock.save()
            
            # Create stock movement record
            from inventory.models import StockMovement
            StockMovement.objects.create(
                product_variant=item.product_variant,
                movement_type='sale',
                quantity_change=-item.quantity,
                previous_quantity=stock.quantity + item.quantity,
                new_quantity=stock.quantity,
                reference_id=sale.id,
                reference_type='sale',
                moved_by=sale.cashier
            )
    
    def _update_loyalty_points(self, customer, amount):
        """Update customer loyalty points"""
        # 1 point per 100 KES spent
        points = int(amount / 100)
        customer.loyalty_points += points
        customer.total_spent += amount
        customer.last_purchase_date = timezone.now()
        customer.save()
    
    def _send_receipt_email(self, sale, receipt):
        """Send receipt email to customer"""
        subject = f'Receipt for {sale.sale_number}'
        message = f"""
        Dear {sale.customer.first_name},
        
        Thank you for your purchase!
        
        Receipt Number: {receipt.receipt_number}
        Sale Number: {sale.sale_number}
        Date: {sale.created_at.strftime('%Y-%m-%d %H:%M')}
        Total Amount: KES {sale.total_amount}
        Payment Method: {sale.get_payment_method_display()}
        
        Items:
        """
        
        for item in sale.items.all():
            message += f"\n- {item.product_variant.product.name} x{item.quantity} = KES {item.total_price}"
        
        message += f"\n\nLoyalty Points Earned: {int(sale.total_amount / 100)}"
        message += f"\nTotal Loyalty Points: {sale.customer.loyalty_points}"
        message += "\n\nThank you for shopping with us!"
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [sale.customer.email],
            fail_silently=True,
        )
    
    @action(detail=True, methods=['post'])
    def process_return(self, request, pk=None):
        """Process sale return/refund"""
        sale = self.get_object()
        
        if sale.sale_status != 'completed':
            return Response({
                'error': 'Can only return completed sales'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        items_to_return = request.data.get('items', [])
        reason = request.data.get('reason', '')
        
        with transaction.atomic():
            total_refund = Decimal('0.00')
            
            # Create return record
            sale_return = SaleReturn.objects.create(
                original_sale=sale,
                cashier=request.user,
                reason=reason,
                total_refund_amount=Decimal('0.00')
            )
            
            # Process return items
            for item_data in items_to_return:
                sale_item = SaleItem.objects.get(id=item_data['sale_item_id'])
                quantity_returned = item_data['quantity_returned']
                
                if quantity_returned > sale_item.quantity:
                    return Response({
                        'error': 'Cannot return more than purchased'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                refund_amount = (sale_item.unit_price * quantity_returned)
                
                ReturnItem.objects.create(
                    return_record=sale_return,
                    sale_item=sale_item,
                    quantity_returned=quantity_returned,
                    refund_amount=refund_amount
                )
                
                total_refund += refund_amount
                
                # Return stock
                stock = Stock.objects.get(product_variant=sale_item.product_variant)
                stock.quantity += quantity_returned
                stock.save()
            
            # Update return total
            sale_return.total_refund_amount = total_refund
            sale_return.save()
            
            # Deduct loyalty points if customer
            if sale.customer:
                points_to_deduct = int(total_refund / 100)
                sale.customer.loyalty_points = max(0, sale.customer.loyalty_points - points_to_deduct)
                sale.customer.total_spent -= total_refund
                sale.customer.save()
        
        return Response({
            'success': True,
            'message': 'Return processed successfully',
            'return': SaleReturnSerializer(sale_return).data
        })
    
    @action(detail=False, methods=['get'])
    def daily_summary(self, request):
        """Get daily sales summary"""
        today = timezone.now().date()
        sales = Sale.objects.filter(created_at__date=today, sale_status='completed')
        
        summary = {
            'date': today,
            'total_sales': sales.aggregate(total=models.Sum('total_amount'))['total'] or 0,
            'total_transactions': sales.count(),
            'cash_sales': sales.filter(payment_method='cash').aggregate(total=models.Sum('total_amount'))['total'] or 0,
            'mpesa_sales': sales.filter(payment_method='mpesa').aggregate(total=models.Sum('total_amount'))['total'] or 0,
            'card_sales': sales.filter(payment_method='card').aggregate(total=models.Sum('total_amount'))['total'] or 0,
        }
        
        return Response(summary)


class ReceiptViewSet(viewsets.ReadOnlyModelViewSet):
    """Receipt management"""
    queryset = Receipt.objects.all()
    serializer_class = ReceiptSerializer
    permission_classes = [IsAuthenticated]


class SaleReturnViewSet(viewsets.ReadOnlyModelViewSet):
    """Sale returns management"""
    queryset = SaleReturn.objects.all()
    serializer_class = SaleReturnSerializer
    permission_classes = [IsAuthenticated]