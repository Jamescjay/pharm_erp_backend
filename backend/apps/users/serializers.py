from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import User, Role, UserPermission, UserSession


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'
        read_only_fields = ['created_at']


class UserPermissionSerializer(serializers.ModelSerializer):
    module_name = serializers.CharField(source='module', read_only=True)
    
    class Meta:
        model = UserPermission
        fields = '__all__'
        read_only_fields = ['created_at']


class UserSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', read_only=True)
    permissions = UserPermissionSerializer(source='user_permissions', many=True, read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'employee_id', 'first_name', 'last_name', 'full_name',
            'email', 'phone', 'role', 'role_name', 'profile_image_url',
            'is_active', 'last_login', 'permissions', 'created_at', 'updated_at'
        ]
        read_only_fields = ['employee_id', 'last_login', 'created_at', 'updated_at']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating users"""
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    
    class Meta:
        model = User
        fields = [
            'employee_id', 'first_name', 'last_name', 'email',
            'phone', 'role', 'password', 'profile_image_url'
        ]

    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data['password_hash'] = make_password(password)
        return User.objects.create(**validated_data)


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=8)


class UserSessionSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = UserSession
        fields = '__all__'
        read_only_fields = ['created_at']
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
