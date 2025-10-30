from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import Product,Category, ProductVariant
from .serializers import ProductSerializer, ProductVariantSerializer, CategorySerializer
from .permisions import IsAdminOrReadOnly
from rest_framework.views import APIView
from django.db.models import Q

# Only Admins can create, update, delete Categories and Products
# POST /api/categories and GET /api/categories
class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all().order_by('-created_at')
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAdminOrReadOnly]

# GET /api/categories/<int:pk>, PUT /api/categories/<int:pk>, DELETE /api/categories/<int:pk>
class CategoryRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAdminOrReadOnly]

# POST /api/products and GET /api/products
class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.all().order_by('-created_at')
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAdminOrReadOnly]


# GET /api/products/<int:pk>, PUT /api/products/<int:pk>, DELETE /api/products/<int:pk>
class ProductRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAdminOrReadOnly]


#  GET /api/products/search/?q=<query>
class ProductSearchView(APIView):
    def get(self, request):
        query = request.query_params.get('q', '')
        products =  Product.objects.filter(
            Q(name__icontains=query) | Q(generic_name__icontains=query)| Q(description__icontains=query)          
        )

        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
# POST /api/products/{id}/variants/
class AddProductVariantView(generics.CreateAPIView):
    serializer_class = ProductVariantSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAdminOrReadOnly]
    def post(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            variant = serializer.save(product=product)
            return Response(ProductSerializer(variant).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    