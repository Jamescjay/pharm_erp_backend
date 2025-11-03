from datetime import datetime, timedelta
from decimal import Decimal

from django.db.models import Sum, Count, Avg, F, Q
from django.utils import timezone

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import (
    DailySalesSummary, CustomerAnalytics, SalesReport,
    CustomerReport, InventoryReport, ProfitabilityReport
)
from .serializers import (
    DailySalesSummarySerializer, CustomerAnalyticsSerializer,
    SalesReportSerializer, CustomerReportSerializer,
    InventoryReportSerializer, ProfitabilityReportSerializer
)

from backend.apps.sales.models import Sale, SaleItem
from backend.apps.customers.models import Customer
from backend.apps.products.models import Product, ProductVariant
from backend.apps.inventory.models import Stock


class DailySalesSummaryViewSet(viewsets.ReadOnlyModelViewSet):
    """Daily sales summary reports"""
    queryset = DailySalesSummary.objects.all()
    serializer_class = DailySalesSummarySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = DailySalesSummary.objects.all()
        
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date and end_date:
            queryset = queryset.filter(summary_date__range=[start_date, end_date])
        
        return queryset.order_by('-summary_date')


class SalesReportViewSet(viewsets.ReadOnlyModelViewSet):
    """Comprehensive sales reports"""
    queryset = SalesReport.objects.all()
    serializer_class = SalesReportSerializer
    permission_classes = [IsAuthenticated]


class CustomerReportViewSet(viewsets.ReadOnlyModelViewSet):
    """Customer analytics reports"""
    queryset = CustomerReport.objects.all()
    serializer_class = CustomerReportSerializer
    permission_classes = [IsAuthenticated]


class CustomerAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """Individual customer analytics"""
    queryset = CustomerAnalytics.objects.all()
    serializer_class = CustomerAnalyticsSerializer
    permission_classes = [IsAuthenticated]


class ProfitabilityReportViewSet(viewsets.ReadOnlyModelViewSet):
    """Profitability analysis reports"""
    queryset = ProfitabilityReport.objects.all()
    serializer_class = ProfitabilityReportSerializer
    permission_classes = [IsAuthenticated]


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sales_daily_report(request):
    """Generate daily sales report"""
    date = request.query_params.get('date', timezone.now().date())
    
    if isinstance(date, str):
        date = datetime.strptime(date, '%Y-%m-%d').date()
    
    sales = Sale.objects.filter(
        created_at__date=date,
        sale_status='completed'
    )
    
    report = {
        'date': date,
        'total_sales': sales.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
        'total_transactions': sales.count(),
        'total_items_sold': SaleItem.objects.filter(sale__in=sales).aggregate(total=Sum('quantity'))['total'] or 0,
        'average_transaction_value': sales.aggregate(avg=Avg('total_amount'))['avg'] or Decimal('0.00'),
        
        # Payment methods breakdown
        'cash_sales': sales.filter(payment_method='cash').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
        'mpesa_sales': sales.filter(payment_method='mpesa').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
        'card_sales': sales.filter(payment_method='card').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
        
        # Customer types
        'walk_in_sales': sales.filter(customer_type='walk-in').count(),
        'registered_customer_sales': sales.filter(customer_type='registered').count(),
        
        # Profit calculation
        'total_cost': SaleItem.objects.filter(sale__in=sales).aggregate(
            total=Sum(F('cost_price') * F('quantity'))
        )['total'] or Decimal('0.00'),
    }
    
    # Calculate profit
    report['total_profit'] = report['total_sales'] - report['total_cost']
    report['profit_margin'] = (report['total_profit'] / report['total_sales'] * 100) if report['total_sales'] > 0 else 0
    
    # Save/update daily summary
    DailySalesSummary.objects.update_or_create(
        summary_date=date,
        defaults={
            'total_sales': report['total_sales'],
            'total_transactions': report['total_transactions'],
            'cash_sales': report['cash_sales'],
            'mpesa_sales': report['mpesa_sales'],
            'card_sales': report['card_sales'],
            'total_cost': report['total_cost'],
            'total_profit': report['total_profit'],
        }
    )
    
    return Response(report)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sales_monthly_report(request):
    """Generate monthly sales report"""
    year = int(request.query_params.get('year', timezone.now().year))
    month = int(request.query_params.get('month', timezone.now().month))
    
    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date()
    else:
        end_date = datetime(year, month + 1, 1).date()
    
    sales = Sale.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lt=end_date,
        sale_status='completed'
    )
    
    report = {
        'period': f"{start_date.strftime('%B %Y')}",
        'start_date': start_date,
        'end_date': end_date,
        'total_sales': sales.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
        'total_transactions': sales.count(),
        'total_items_sold': SaleItem.objects.filter(sale__in=sales).aggregate(total=Sum('quantity'))['total'] or 0,
        'average_transaction_value': sales.aggregate(avg=Avg('total_amount'))['avg'] or Decimal('0.00'),
        
        # Payment methods
        'cash_sales': sales.filter(payment_method='cash').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
        'mpesa_sales': sales.filter(payment_method='mpesa').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
        'card_sales': sales.filter(payment_method='card').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
        
        # Daily breakdown
        'daily_sales': [],
    }
    
    # Generate daily breakdown
    current_date = start_date
    while current_date < end_date:
        daily_sales = sales.filter(created_at__date=current_date)
        report['daily_sales'].append({
            'date': current_date,
            'total': daily_sales.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
            'transactions': daily_sales.count()
        })
        current_date += timedelta(days=1)
    
    return Response(report)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def top_customers_report(request):
    """Get top customers by spending"""
    limit = int(request.query_params.get('limit', 10))
    period = request.query_params.get('period', 'all')  # all, month, year
    
    customers = Customer.objects.filter(is_active=True)
    
    if period == 'month':
        start_date = timezone.now().replace(day=1, hour=0, minute=0, second=0)
        customers = customers.filter(sales__created_at__gte=start_date, sales__sale_status='completed')
    elif period == 'year':
        start_date = timezone.now().replace(month=1, day=1, hour=0, minute=0, second=0)
        customers = customers.filter(sales__created_at__gte=start_date, sales__sale_status='completed')
    
    top_customers = customers.annotate(
        total_spent_period=Sum('sales__total_amount', filter=Q(sales__sale_status='completed')),
        total_purchases=Count('sales', filter=Q(sales__sale_status='completed'))
    ).order_by('-total_spent_period')[:limit]
    
    result = []
    for customer in top_customers:
        result.append({
            'customer_id': customer.id,
            'customer_code': customer.customer_code,
            'name': f"{customer.first_name} {customer.last_name}" if customer.first_name else customer.company_name,
            'email': customer.email,
            'phone': customer.phone,
            'total_spent': customer.total_spent_period or Decimal('0.00'),
            'total_purchases': customer.total_purchases,
            'loyalty_points': customer.loyalty_points,
        })
    
    return Response({
        'period': period,
        'limit': limit,
        'customers': result
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def top_products_report(request):
    """Get top selling products"""
    limit = int(request.query_params.get('limit', 10))
    period = request.query_params.get('period', 'month')  # month, year, all
    
    # Date filtering
    if period == 'month':
        start_date = timezone.now().replace(day=1, hour=0, minute=0, second=0)
    elif period == 'year':
        start_date = timezone.now().replace(month=1, day=1, hour=0, minute=0, second=0)
    else:
        start_date = None
    
    # Get sale items
    sale_items = SaleItem.objects.filter(sale__sale_status='completed')
    if start_date:
        sale_items = sale_items.filter(sale__created_at__gte=start_date)
    
    # Aggregate by product
    top_products = sale_items.values(
        'product_variant__product__id',
        'product_variant__product__name',
        'product_variant__product__sku'
    ).annotate(
        total_quantity_sold=Sum('quantity'),
        total_revenue=Sum('total_price'),
        total_transactions=Count('sale', distinct=True)
    ).order_by('-total_quantity_sold')[:limit]
    
    result = []
    for item in top_products:
        result.append({
            'product_id': item['product_variant__product__id'],
            'product_name': item['product_variant__product__name'],
            'sku': item['product_variant__product__sku'],
            'quantity_sold': item['total_quantity_sold'],
            'revenue': item['total_revenue'],
            'transactions': item['total_transactions'],
        })
    
    return Response({
        'period': period,
        'limit': limit,
        'products': result
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_methods_summary(request):
    """Summary of sales by payment method"""
    period = request.query_params.get('period', 'month')
    
    if period == 'today':
        start_date = timezone.now().replace(hour=0, minute=0, second=0)
    elif period == 'week':
        start_date = timezone.now() - timedelta(days=7)
    elif period == 'month':
        start_date = timezone.now().replace(day=1, hour=0, minute=0, second=0)
    elif period == 'year':
        start_date = timezone.now().replace(month=1, day=1, hour=0, minute=0, second=0)
    else:
        start_date = None
    
    sales = Sale.objects.filter(sale_status='completed')
    if start_date:
        sales = sales.filter(created_at__gte=start_date)
    
    summary = {
        'period': period,
        'total_sales': sales.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
        'payment_methods': []
    }
    
    # Get breakdown by payment method
    payment_methods = ['cash', 'mpesa', 'card', 'insurance', 'credit']
    for method in payment_methods:
        method_sales = sales.filter(payment_method=method)
        total = method_sales.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        count = method_sales.count()
        
        summary['payment_methods'].append({
            'method': method,
            'total_amount': total,
            'transaction_count': count,
            'percentage': (total / summary['total_sales'] * 100) if summary['total_sales'] > 0 else 0
        })
    
    return Response(summary)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def customer_analytics_summary(request):
    """Overall customer analytics"""
    
    total_customers = Customer.objects.filter(is_active=True).count()
    
    # New customers this month
    start_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0)
    new_customers_month = Customer.objects.filter(created_at__gte=start_of_month).count()
    
    # Customers with purchases this month
    active_customers_month = Customer.objects.filter(
        sales__created_at__gte=start_of_month,
        sales__sale_status='completed'
    ).distinct().count()
    
    # Average customer lifetime value
    avg_customer_value = Customer.objects.aggregate(avg=Avg('total_spent'))['avg'] or Decimal('0.00')
    
    # Top loyalty points holders
    top_loyalty = Customer.objects.filter(is_active=True).order_by('-loyalty_points')[:5]
    
    summary = {
        'total_customers': total_customers,
        'new_customers_this_month': new_customers_month,
        'active_customers_this_month': active_customers_month,
        'average_customer_lifetime_value': avg_customer_value,
        'total_loyalty_points_issued': Customer.objects.aggregate(total=Sum('loyalty_points'))['total'] or 0,
        'top_loyalty_customers': [
            {
                'name': f"{c.first_name} {c.last_name}" if c.first_name else c.company_name,
                'points': c.loyalty_points,
                'total_spent': c.total_spent
            }
            for c in top_loyalty
        ]
    }
    
    return Response(summary)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def inventory_status_report(request):
    """Current inventory status"""
    
    # Total products and stock
    total_products = Product.objects.filter(is_active=True).count()
    total_stock_value = Stock.objects.aggregate(
        total=Sum(F('quantity') * F('product_variant__purchase_price'))
    )['total'] or Decimal('0.00')
    
    # Low stock items
    low_stock = Stock.objects.filter(
        quantity__lte=F('product_variant__min_stock_level')
    ).count()
    
    # Out of stock
    out_of_stock = Stock.objects.filter(quantity=0).count()
    
    # Expiring soon (next 30 days)
    from inventory.models import ExpiryTracking
    expiring_soon = ExpiryTracking.objects.filter(
        expiry_date__lte=timezone.now().date() + timedelta(days=30),
        expiry_date__gte=timezone.now().date(),
        status='active'
    ).count()
    
    summary = {
        'total_products': total_products,
        'total_stock_value': total_stock_value,
        'low_stock_items': low_stock,
        'out_of_stock_items': out_of_stock,
        'expiring_soon_items': expiring_soon,
        'stock_turnover_rate': None,  # Would require historical data calculation
    }
    
    return Response(summary)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sales_vs_target_report(request):
    """Sales performance vs target"""
    period = request.query_params.get('period', 'month')
    target_amount = Decimal(request.query_params.get('target', '100000'))
    
    if period == 'month':
        start_date = timezone.now().replace(day=1, hour=0, minute=0, second=0)
    elif period == 'year':
        start_date = timezone.now().replace(month=1, day=1, hour=0, minute=0, second=0)
    else:
        start_date = timezone.now() - timedelta(days=30)
    
    sales = Sale.objects.filter(
        created_at__gte=start_date,
        sale_status='completed'
    )
    
    actual_sales = sales.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    achievement_rate = (actual_sales / target_amount * 100) if target_amount > 0 else 0
    
    report = {
        'period': period,
        'target_amount': target_amount,
        'actual_sales': actual_sales,
        'variance': actual_sales - target_amount,
        'achievement_rate': achievement_rate,
        'status': 'achieved' if actual_sales >= target_amount else 'below_target',
        'days_in_period': (timezone.now() - start_date).days,
        'average_daily_sales': actual_sales / max((timezone.now() - start_date).days, 1)
    }
    
    return Response(report)