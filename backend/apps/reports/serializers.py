
from rest_framework import serializers
from .models import (
    DailySalesSummary, CustomerAnalytics, SalesReport,
    CustomerReport, InventoryReport, ProfitabilityReport
)

class DailySalesSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = DailySalesSummary
        fields = '__all__'
        read_only_fields = ['created_at']


class CustomerAnalyticsSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomerAnalytics
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def get_customer_name(self, obj):
        if obj.customer.company_name:
            return obj.customer.company_name
        return f"{obj.customer.first_name} {obj.customer.last_name}"


class SalesReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesReport
        fields = '__all__'
        read_only_fields = ['created_at']


class CustomerReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerReport
        fields = '__all__'
        read_only_fields = ['created_at']


class InventoryReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryReport
        fields = '__all__'
        read_only_fields = ['created_at']


class ProfitabilityReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfitabilityReport
        fields = '__all__'
        read_only_fields = ['created_at']