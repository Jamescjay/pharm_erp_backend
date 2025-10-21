import pytest
from django.contrib.auth import get_user_model
from model_bakery import baker

User = get_user_model()

@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()

@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client

@pytest.fixture
def user():
    return baker.make(User, email='test@pharmerp.com', role='admin')

@pytest.fixture
def product():
    from apps.products.models import Product
    return baker.make(Product, name='Test Product', sku='TEST001')

@pytest.fixture
def customer():
    from apps.customers.models import Customer
    return baker.make(Customer, first_name='John', last_name='Doe')