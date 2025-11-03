from rest_framework import serializers
from .models import Sale, SaleItem, Receipt, SaleReturn, ReturnItem

class SaleItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product_variant.product.name', read_only=True)
    product_sku = serializers.CharField(source='product_variant.product.sku', read_only=True)
    
    class Meta:
        model = SaleItem
        fields = '__all__'
        read_only_fields = ['created_at']


class SaleSerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True, read_only=True)
    cashier_name = serializers.SerializerMethodField()
    customer_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Sale
        fields = '__all__'
        read_only_fields = ['sale_number', 'created_at']
    
    def get_cashier_name(self, obj):
        return f"{obj.cashier.first_name} {obj.cashier.last_name}"
    
    def get_customer_name(self, obj):
        if obj.customer:
            if obj.customer.company_name:
                return obj.customer.company_name
            return f"{obj.customer.first_name} {obj.customer.last_name}"
        return "Walk-in Customer"


class SaleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating sales"""
    
    class Meta:
        model = Sale
        fields = [
            'customer', 'customer_type', 'subtotal_amount',
            'discount_amount', 'discount_percentage', 'notes'
        ]


class ReceiptSerializer(serializers.ModelSerializer):
    sale_number = serializers.CharField(source='sale.sale_number', read_only=True)
    
    class Meta:
        model = Receipt
        fields = '__all__'
        read_only_fields = ['receipt_number', 'created_at']


class ReturnItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='sale_item.product_variant.product.name', read_only=True)
    
    class Meta:
        model = ReturnItem
        fields = '__all__'


class SaleReturnSerializer(serializers.ModelSerializer):
    items = ReturnItemSerializer(many=True, read_only=True)
    original_sale_number = serializers.CharField(source='original_sale.sale_number', read_only=True)
    
    class Meta:
        model = SaleReturn
        fields = '__all__'
        read_only_fields = ['return_number', 'created_at']


