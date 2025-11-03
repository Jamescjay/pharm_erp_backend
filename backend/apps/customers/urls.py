from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CustomerViewSet, CustomerTypeViewSet,
    CreditNoteViewSet, CustomerStatementViewSet
)

router = DefaultRouter()
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'customer-types', CustomerTypeViewSet, basename='customer-type')
router.register(r'credit-notes', CreditNoteViewSet, basename='credit-note')
router.register(r'statements', CustomerStatementViewSet, basename='customer-statement')

urlpatterns = [
    path('', include(router.urls)),
]