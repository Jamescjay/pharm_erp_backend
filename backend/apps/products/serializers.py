from rest_framework import serializers
from .models import Product, ProductVariant, Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'parent_id', 'created_at']

class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = [
            'id', 'product', 'strength', 'pack_size', 'barcode',
            'purchase_price', 'selling_price', 'wholesale_price',
            'min_stock_level', 'max_stock_level', 'is_active', 'created_at'
        ]

class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'sku', 'name', 'generic_name', 'description',
            'category', 'category_id', 'manufacturer', 'unit_of_measure',
            'prescription_required', 'is_active', 'created_at',
            'updated_at', 'variants'
        ]
