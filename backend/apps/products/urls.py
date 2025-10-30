from django.urls import path
from .views import (
    ProductListCreateView,
    ProductRetrieveUpdateDestroyView,
    ProductSearchView,  
    AddProductVariantView,
    CategoryListCreateView,
    CategoryRetrieveUpdateDestroyView,
)

urlpatterns = [
    path('categories/', CategoryListCreateView.as_view(), name='category-list-create'),
    path('categories/<int:pk>/', CategoryRetrieveUpdateDestroyView.as_view(), name='category-detail'),
    path('products/', ProductListCreateView.as_view(), name='product-list-create'),
    path('products/<int:pk>/', ProductRetrieveUpdateDestroyView.as_view(), name='product-detail'),
    path('products/search/', ProductSearchView.as_view(), name='product-search'),   
    path('products/<int:pk>/variants/', AddProductVariantView.as_view(), name='add-product-variant'),

]