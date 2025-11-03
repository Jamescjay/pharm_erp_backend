from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SaleViewSet, ReceiptViewSet, SaleReturnViewSet

router = DefaultRouter()
router.register(r'sales', SaleViewSet, basename='sale')
router.register(r'receipts', ReceiptViewSet, basename='receipt')
router.register(r'returns', SaleReturnViewSet, basename='sale-return')

urlpatterns = [
    path('', include(router.urls)),
]