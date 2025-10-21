import pytest
from django.core.exceptions import ValidationError
from apps.products.models import Product, ProductVariant

class TestProductModel:
    def test_product_creation(self, product):
        assert product.name == 'Test Product'
        assert product.sku == 'TEST001'
        assert str(product) == 'Test Product (TEST001)'

    def test_product_sku_uniqueness(self):
        Product.objects.create(name='Product 1', sku='UNIQUE001')
        with pytest.raises(ValidationError):
            Product.objects.create(name='Product 2', sku='UNIQUE001')