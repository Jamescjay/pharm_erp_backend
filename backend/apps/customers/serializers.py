
from rest_framework import serializers
from .models import Customer, CustomerType, CreditNote, CustomerStatement

class CustomerTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerType
        fields = '__all__'


class CustomerSerializer(serializers.ModelSerializer):
    customer_type_name = serializers.CharField(source='customer_type.name', read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Customer
        fields = '__all__'
        read_only_fields = ['customer_code', 'loyalty_points', 'total_spent',
                           'outstanding_balance', 'last_purchase_date', 'created_at', 'updated_at']
    
    def get_full_name(self, obj):
        if obj.company_name:
            return obj.company_name
        return f"{obj.first_name} {obj.last_name}".strip()


class CustomerCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating customers"""
    
    class Meta:
        model = Customer
        fields = [
            'customer_type', 'first_name', 'last_name', 'company_name',
            'email', 'phone', 'address', 'id_number', 'date_of_birth'
        ]


class CreditNoteSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CreditNote
        fields = '__all__'
        read_only_fields = ['credit_note_number', 'created_by', 'created_at']
    
    def get_customer_name(self, obj):
        if obj.customer.company_name:
            return obj.customer.company_name
        return f"{obj.customer.first_name} {obj.customer.last_name}"


class CustomerStatementSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomerStatement
        fields = '__all__'
        read_only_fields = ['created_at']
    
    def get_customer_name(self, obj):
        if obj.customer.company_name:
            return obj.customer.company_name
        return f"{obj.customer.first_name} {obj.customer.last_name}"


