import os
import jwt
from datetime import datetime, timedelta
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import User, Role, UserPermission, UserSession
from .serializers import (
    UserSerializer, RoleSerializer, UserPermissionSerializer,
    UserSessionSerializer, UserCreateSerializer, PasswordChangeSerializer
)
from backend.apps.administration.models import AuditLog



class JWTAuthentication:
    """JWT Token Management"""
    
    @staticmethod
    def generate_tokens(user):
        """Generate access and refresh tokens"""
        secret_key = os.getenv('SECRET_KEY')
        
        # Access token (1 hour)
        access_payload = {
            'user_id': user.id,
            'email': user.email,
            'role': user.role.name if user.role else None,
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow(),
            'type': 'access'
        }
        access_token = jwt.encode(access_payload, secret_key, algorithm='HS256')
        
        # Refresh token (7 days)
        refresh_payload = {
            'user_id': user.id,
            'email': user.email,
            'exp': datetime.utcnow() + timedelta(days=7),
            'iat': datetime.utcnow(),
            'type': 'refresh'
        }
        refresh_token = jwt.encode(refresh_payload, secret_key, algorithm='HS256')
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': 3600  # 1 hour in seconds
        }
    
    @staticmethod
    def verify_token(token):
        """Verify and decode JWT token"""
        try:
            secret_key = os.getenv('SECRET_KEY')
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return {'error': 'Token has expired'}
        except jwt.InvalidTokenError:
            return {'error': 'Invalid token'}
    
    @staticmethod
    def get_user_from_token(request):
        """Extract user from request token"""
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        payload = JWTAuthentication.verify_token(token)
        
        if 'error' in payload:
            return None
        
        try:
            user = User.objects.get(id=payload['user_id'], is_active=True)
            return user
        except User.DoesNotExist:
            return None


class IsAdmin(IsAuthenticated):
    """Permission class for Admin/Manager only"""
    
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        
        user = JWTAuthentication.get_user_from_token(request)
        if not user:
            return False
        
        # Admin, Manager, and Pharmacist have full access
        return user.role and user.role.name in ['Admin', 'Manager', 'Pharmacist']


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """User login endpoint"""
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response({
            'error': 'Email and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email, is_active=True)
    except User.DoesNotExist:
        return Response({
            'error': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    # Verify password
    if not check_password(password, user.password_hash):
        return Response({
            'error': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    # Generate tokens
    tokens = JWTAuthentication.generate_tokens(user)
    
    # Update last login
    user.last_login = timezone.now()
    user.save()
    
    # Create user session
    UserSession.objects.create(
        user=user,
        session_token=tokens['access_token'],
        ip_address=request.META.get('REMOTE_ADDR', ''),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        expires_at=timezone.now() + timedelta(hours=1)
    )
    
    # Log audit
    AuditLog.objects.create(
        user=user,
        action='login',
        table_name='users',
        record_id=user.id,
        ip_address=request.META.get('REMOTE_ADDR', ''),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    return Response({
        'success': True,
        'message': 'Login successful',
        'tokens': tokens,
        'user': {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role.name if user.role else None,
            'employee_id': user.employee_id,
            'permissions': list(user.user_permissions.values('module', 'can_view', 'can_create', 'can_edit', 'can_delete'))
        }
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    """Refresh access token using refresh token"""
    refresh_token = request.data.get('refresh_token')
    
    if not refresh_token:
        return Response({
            'error': 'Refresh token is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    payload = JWTAuthentication.verify_token(refresh_token)
    
    if 'error' in payload:
        return Response({
            'error': payload['error']
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    if payload.get('type') != 'refresh':
        return Response({
            'error': 'Invalid token type'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        user = User.objects.get(id=payload['user_id'], is_active=True)
    except User.DoesNotExist:
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Generate new tokens
    tokens = JWTAuthentication.generate_tokens(user)
    
    return Response({
        'success': True,
        'tokens': tokens
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """User logout endpoint"""
    user = JWTAuthentication.get_user_from_token(request)
    
    if not user:
        return Response({
            'error': 'Invalid token'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    # Get token from header
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None
    
    # Delete user session
    if token:
        UserSession.objects.filter(user=user, session_token=token).delete()
    
    # Log audit
    AuditLog.objects.create(
        user=user,
        action='logout',
        table_name='users',
        record_id=user.id,
        ip_address=request.META.get('REMOTE_ADDR', ''),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    return Response({
        'success': True,
        'message': 'Logout successful'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Change user password"""
    user = JWTAuthentication.get_user_from_token(request)
    
    if not user:
        return Response({
            'error': 'Invalid token'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')
    
    if not old_password or not new_password:
        return Response({
            'error': 'Old password and new password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Verify old password
    if not check_password(old_password, user.password_hash):
        return Response({
            'error': 'Invalid old password'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Update password
    user.password_hash = make_password(new_password)
    user.save()
    
    # Log audit
    AuditLog.objects.create(
        user=user,
        action='change_password',
        table_name='users',
        record_id=user.id,
        ip_address=request.META.get('REMOTE_ADDR', ''),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    return Response({
        'success': True,
        'message': 'Password changed successfully'
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset(request):
    """Request password reset"""
    email = request.data.get('email')
    
    if not email:
        return Response({
            'error': 'Email is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email, is_active=True)
    except User.DoesNotExist:
        # Don't reveal if user exists
        return Response({
            'success': True,
            'message': 'If the email exists, a reset link has been sent'
        })
    
    # Generate reset token (valid for 1 hour)
    secret_key = os.getenv('SECRET_KEY')
    reset_payload = {
        'user_id': user.id,
        'email': user.email,
        'exp': datetime.utcnow() + timedelta(hours=1),
        'type': 'password_reset'
    }
    reset_token = jwt.encode(reset_payload, secret_key, algorithm='HS256')
    
    # Send email
    reset_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={reset_token}"
    
    send_mail(
        subject='Password Reset Request',
        message=f"""
        Hello {user.first_name},
        
        You requested a password reset for your PharmERP account.
        
        Click the link below to reset your password:
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request this, please ignore this email.
        
        Best regards,
        PharmERP Team
        """,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )
    
    return Response({
        'success': True,
        'message': 'If the email exists, a reset link has been sent'
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    """Reset password using token"""
    token = request.data.get('token')
    new_password = request.data.get('new_password')
    
    if not token or not new_password:
        return Response({
            'error': 'Token and new password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    payload = JWTAuthentication.verify_token(token)
    
    if 'error' in payload:
        return Response({
            'error': 'Invalid or expired token'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    if payload.get('type') != 'password_reset':
        return Response({
            'error': 'Invalid token type'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        user = User.objects.get(id=payload['user_id'], is_active=True)
    except User.DoesNotExist:
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Update password
    user.password_hash = make_password(new_password)
    user.save()
    
    # Log audit
    AuditLog.objects.create(
        user=user,
        action='reset_password',
        table_name='users',
        record_id=user.id,
        ip_address=request.META.get('REMOTE_ADDR', ''),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    return Response({
        'success': True,
        'message': 'Password reset successfully'
    })


class RoleViewSet(viewsets.ModelViewSet):
    """Role management - Admin only"""
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAdmin]
    
    def create(self, request):
        """Create new role"""
        user = JWTAuthentication.get_user_from_token(request)
        
        serializer = RoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = serializer.save()
        
        # Log audit
        AuditLog.objects.create(
            user=user,
            action='create',
            table_name='roles',
            record_id=role.id,
            new_values=serializer.data,
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserViewSet(viewsets.ModelViewSet):
    """User management"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """Admin-only for create, update, delete"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        user = JWTAuthentication.get_user_from_token(self.request)
        queryset = User.objects.all()
        
        # Cashiers can only see their own profile
        if user and user.role and user.role.name in ['Cashier', 'Accountant']:
            queryset = queryset.filter(id=user.id)
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search) |
                Q(employee_id__icontains=search)
            )
        
        # Filter by role
        role_id = self.request.query_params.get('role')
        if role_id:
            queryset = queryset.filter(role_id=role_id)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.order_by('-created_at')
    
    def create(self, request):
        """Create new user - Admin only"""
        admin_user = JWTAuthentication.get_user_from_token(request)
        
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Hash password
        password = request.data.get('password')
        
        # Generate employee ID if not provided
        employee_id = request.data.get('employee_id')
        if not employee_id:
            last_user = User.objects.order_by('-id').first()
            employee_id = f"EMP-{(last_user.id + 1):05d}" if last_user else "EMP-00001"
        
        user = serializer.save(
            password_hash=make_password(password),
            employee_id=employee_id
        )
        
        # Log audit
        AuditLog.objects.create(
            user=admin_user,
            action='create',
            table_name='users',
            record_id=user.id,
            new_values={'email': user.email, 'role': user.role.name if user.role else None},
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Send welcome email
        send_mail(
            subject='Welcome to PharmERP',
            message=f"""
            Hello {user.first_name},
            
            Your account has been created successfully.
            
            Employee ID: {user.employee_id}
            Email: {user.email}
            Role: {user.role.name if user.role else 'Not assigned'}
            
            Please change your password after first login.
            
            Best regards,
            PharmERP Team
            """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )
        
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate/deactivate user - Admin only"""
        admin_user = JWTAuthentication.get_user_from_token(request)
        user = self.get_object()
        
        is_active = request.data.get('is_active', True)
        old_status = user.is_active
        user.is_active = is_active
        user.save()
        
        # Log audit
        AuditLog.objects.create(
            user=admin_user,
            action='update_status',
            table_name='users',
            record_id=user.id,
            old_values={'is_active': old_status},
            new_values={'is_active': is_active},
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({
            'success': True,
            'message': f"User {'activated' if is_active else 'deactivated'} successfully"
        })
    
    @action(detail=False, methods=['get'])
    def profile(self, request):
        """Get current user profile"""
        user = JWTAuthentication.get_user_from_token(request)
        
        if not user:
            return Response({
                'error': 'Invalid token'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response(UserSerializer(user).data)
    
    @action(detail=True, methods=['get'])
    def activity_logs(self, request, pk=None):
        """Get user activity logs"""
        user = self.get_object()
        logs = AuditLog.objects.filter(user=user).order_by('-created_at')[:50]
        
        return Response([{
            'action': log.action,
            'table_name': log.table_name,
            'record_id': log.record_id,
            'created_at': log.created_at,
            'ip_address': log.ip_address
        } for log in logs])


class UserPermissionViewSet(viewsets.ModelViewSet):
    """User permissions management - Admin only"""
    queryset = UserPermission.objects.all()
    serializer_class = UserPermissionSerializer
    permission_classes = [IsAdmin]
    
    def get_queryset(self):
        queryset = UserPermission.objects.all()
        
        # Filter by user
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def update_user_permissions(self, request):
        """Bulk update user permissions"""
        admin_user = JWTAuthentication.get_user_from_token(request)
        user_id = request.data.get('user_id')
        permissions = request.data.get('permissions', [])
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Delete existing permissions
        UserPermission.objects.filter(user=user).delete()
        
        # Create new permissions
        for perm in permissions:
            UserPermission.objects.create(
                user=user,
                module=perm['module'],
                can_view=perm.get('can_view', False),
                can_create=perm.get('can_create', False),
                can_edit=perm.get('can_edit', False),
                can_delete=perm.get('can_delete', False)
            )
        
        # Log audit
        AuditLog.objects.create(
            user=admin_user,
            action='update_permissions',
            table_name='user_permissions',
            record_id=user.id,
            new_values={'permissions': permissions},
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({
            'success': True,
            'message': 'Permissions updated successfully'
        })


class UserSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """View active user sessions"""
    queryset = UserSession.objects.all()
    serializer_class = UserSessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = JWTAuthentication.get_user_from_token(self.request)
        
        # Users can only see their own sessions
        queryset = UserSession.objects.filter(user=user)
        
        # Admins can see all sessions
        if user.role and user.role.name in ['Admin', 'Manager']:
            user_id = self.request.query_params.get('user_id')
            if user_id:
                queryset = UserSession.objects.filter(user_id=user_id)
            else:
                queryset = UserSession.objects.all()
        
        return queryset.order_by('-created_at')