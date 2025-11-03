from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DailySalesSummaryViewSet, SalesReportViewSet,
    CustomerReportViewSet, CustomerAnalyticsViewSet,
    ProfitabilityReportViewSet,
    sales_daily_report, sales_monthly_report,
    top_customers_report, top_products_report,
    payment_methods_summary, customer_analytics_summary,
    inventory_status_report, sales_vs_target_report
)

router = DefaultRouter()
router.register(r'daily-sales-summary', DailySalesSummaryViewSet, basename='daily-sales')
router.register(r'sales-reports', SalesReportViewSet, basename='sales-report')
router.register(r'customer-reports', CustomerReportViewSet, basename='customer-report')
router.register(r'customer-analytics', CustomerAnalyticsViewSet, basename='customer-analytics')
router.register(r'profitability', ProfitabilityReportViewSet, basename='profitability')

urlpatterns = [
    path('', include(router.urls)),
    path('sales/daily/', sales_daily_report, name='sales-daily'),
    path('sales/monthly/', sales_monthly_report, name='sales-monthly'),
    path('customers/top/', top_customers_report, name='top-customers'),
    path('products/top/', top_products_report, name='top-products'),
    path('payments/summary/', payment_methods_summary, name='payment-summary'),
    path('customers/analytics/', customer_analytics_summary, name='customer-analytics-summary'),
    path('inventory/status/', inventory_status_report, name='inventory-status'),
    path('sales/vs-target/', sales_vs_target_report, name='sales-vs-target'),
]