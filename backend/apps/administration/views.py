from django.db.models import Q, Count
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import SystemSetting, AuditLog, Notification, EmailMessage
from .serializers import (
    SystemSettingSerializer, AuditLogSerializer,
    NotificationSerializer, EmailMessageSerializer
)

# Import JWT authentication from users app
import sys
sys.path.append('..')
from backend.apps.users.views import JWTAuthentication, IsAdmin



class SystemSettingViewSet(viewsets.ModelViewSet):
    """System settings management - Admin only"""
    queryset = SystemSetting.objects.all()
    serializer_class = SystemSettingSerializer
    permission_classes = [IsAdmin]
    
    def get_queryset(self):
        queryset = SystemSetting.objects.all()
        
        # Search by key
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(setting_key__icontains=search)
        
        # Filter by type
        setting_type = self.request.query_params.get('type')
        if setting_type:
            queryset = queryset.filter(setting_type=setting_type)
        
        return queryset.order_by('setting_key')
    
    def create(self, request):
        """Create system setting"""
        user = JWTAuthentication.get_user_from_token(request)
        
        serializer = SystemSettingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        setting = serializer.save(updated_by=user)
        
        # Log audit
        AuditLog.objects.create(
            user=user,
            action='create',
            table_name='system_settings',
            record_id=setting.id,
            new_values=serializer.data,
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, pk=None):
        """Update system setting"""
        user = JWTAuthentication.get_user_from_token(request)
        setting = self.get_object()
        
        old_value = setting.setting_value
        
        serializer = SystemSettingSerializer(setting, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=user)
        
        # Log audit
        AuditLog.objects.create(
            user=user,
            action='update',
            table_name='system_settings',
            record_id=setting.id,
            old_values={'setting_value': old_value},
            new_values={'setting_value': setting.setting_value},
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def get_by_key(self, request):
        """Get setting by key"""
        key = request.query_params.get('key')
        
        if not key:
            return Response({
                'error': 'Setting key is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            setting = SystemSetting.objects.get(setting_key=key)
            return Response(SystemSettingSerializer(setting).data)
        except SystemSetting.DoesNotExist:
            return Response({
                'error': 'Setting not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """Bulk update settings"""
        user = JWTAuthentication.get_user_from_token(request)
        settings_data = request.data.get('settings', [])
        
        updated = []
        for setting_data in settings_data:
            try:
                setting = SystemSetting.objects.get(setting_key=setting_data['key'])
                old_value = setting.setting_value
                setting.setting_value = setting_data['value']
                setting.updated_by = user
                setting.save()
                
                # Log audit
                AuditLog.objects.create(
                    user=user,
                    action='bulk_update',
                    table_name='system_settings',
                    record_id=setting.id,
                    old_values={'setting_value': old_value},
                    new_values={'setting_value': setting.setting_value},
                    ip_address=request.META.get('REMOTE_ADDR', ''),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                updated.append(setting.setting_key)
            except SystemSetting.DoesNotExist:
                continue
        
        return Response({
            'success': True,
            'message': f'{len(updated)} settings updated',
            'updated_keys': updated
        })


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Audit logs viewing - Admin only"""
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdmin]
    
    def get_queryset(self):
        queryset = AuditLog.objects.all()
        
        # Filter by user
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by table
        table_name = self.request.query_params.get('table')
        if table_name:
            queryset = queryset.filter(table_name=table_name)
        
        # Filter by action
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date and end_date:
            queryset = queryset.filter(created_at__date__range=[start_date, end_date])
        
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get audit log statistics"""
        total_logs = AuditLog.objects.count()
        
        # Actions breakdown
        actions = AuditLog.objects.values('action').annotate(count=Count('id'))
        
        # Tables breakdown
        tables = AuditLog.objects.values('table_name').annotate(count=Count('id')).order_by('-count')[:10]
        
        # Most active users
        users = AuditLog.objects.filter(user__isnull=False).values(
            'user__first_name', 'user__last_name', 'user__email'
        ).annotate(count=Count('id')).order_by('-count')[:10]
        
        return Response({
            'total_logs': total_logs,
            'actions': list(actions),
            'top_tables': list(tables),
            'most_active_users': list(users)
        })
    
    @action(detail=False, methods=['get'])
    def recent_activity(self, request):
        """Get recent system activity"""
        limit = int(request.query_params.get('limit', 50))
        
        logs = AuditLog.objects.select_related('user').order_by('-created_at')[:limit]
        
        activity = [{
            'id': log.id,
            'user': f"{log.user.first_name} {log.user.last_name}" if log.user else 'System',
            'action': log.action,
            'table': log.table_name,
            'record_id': log.record_id,
            'timestamp': log.created_at,
            'ip_address': log.ip_address
        } for log in logs]
        
        return Response(activity)


class NotificationViewSet(viewsets.ModelViewSet):
    """User notifications management"""
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = JWTAuthentication.get_user_from_token(self.request)
        
        # Users can only see their own notifications
        queryset = Notification.objects.filter(user=user)
        
        # Filter by read status
        is_read = self.request.query_params.get('is_read')
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read.lower() == 'true')
        
        # Filter by type
        notification_type = self.request.query_params.get('type')
        if notification_type:
            queryset = queryset.filter(type=notification_type)
        
        return queryset.order_by('-created_at')
    
    def create(self, request):
        """Create notification - Admin only"""
        if not self._is_admin(request):
            return Response({
                'error': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = NotificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notification = serializer.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        
        return Response({
            'success': True,
            'message': 'Notification marked as read'
        })
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        user = JWTAuthentication.get_user_from_token(request)
        
        Notification.objects.filter(user=user, is_read=False).update(is_read=True)
        
        return Response({
            'success': True,
            'message': 'All notifications marked as read'
        })
    
    @action(detail=False, methods=['post'])
    def broadcast(self, request):
        """Broadcast notification to all users - Admin only"""
        if not self._is_admin(request):
            return Response({
                'error': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)
        
        title = request.data.get('title')
        message = request.data.get('message')
        notification_type = request.data.get('type', 'info')
        
        if not title or not message:
            return Response({
                'error': 'Title and message are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get all active users
        from users.models import User
        users = User.objects.filter(is_active=True)
        
        # Create notifications
        notifications = []
        for user in users:
            notification = Notification.objects.create(
                user=user,
                title=title,
                message=message,
                type=notification_type
            )
            notifications.append(notification)
        
        return Response({
            'success': True,
            'message': f'Notification sent to {len(notifications)} users'
        })
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get unread notifications count"""
        user = JWTAuthentication.get_user_from_token(request)
        
        count = Notification.objects.filter(user=user, is_read=False).count()
        
        return Response({
            'unread_count': count
        })
    
    def _is_admin(self, request):
        """Check if user is admin"""
        user = JWTAuthentication.get_user_from_token(request)
        return user and user.role and user.role.name in ['Admin', 'Manager', 'Pharmacist']


class EmailMessageViewSet(viewsets.ModelViewSet):
    """Email message tracking"""
    queryset = EmailMessage.objects.all()
    serializer_class = EmailMessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """Only admins can create emails"""
        if self.action == 'create':
            return [IsAdmin()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        user = JWTAuthentication.get_user_from_token(self.request)
        
        # Users can only see emails they sent
        queryset = EmailMessage.objects.filter(sender=user)
        
        # Admins can see all emails
        if user.role and user.role.name in ['Admin', 'Manager']:
            queryset = EmailMessage.objects.all()
        
        # Filter by status
        email_status = self.request.query_params.get('status')
        if email_status:
            queryset = queryset.filter(status=email_status)
        
        # Filter by type
        email_type = self.request.query_params.get('type')
        if email_type:
            queryset = queryset.filter(email_type=email_type)
        
        return queryset.order_by('-sent_at')
    
    def create(self, request):
        """Send email"""
        sender = JWTAuthentication.get_user_from_token(request)
        
        recipient_email = request.data.get('recipient_email')
        subject = request.data.get('subject')
        body = request.data.get('body')
        email_type = request.data.get('email_type', 'general')
        
        if not all([recipient_email, subject, body]):
            return Response({
                'error': 'Recipient, subject, and body are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Send email
        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
                fail_silently=False,
            )
            
            # Save email record
            email_message = EmailMessage.objects.create(
                sender=sender,
                recipient_email=recipient_email,
                subject=subject,
                body=body,
                email_type=email_type,
                status='sent'
            )
            
            return Response({
                'success': True,
                'message': 'Email sent successfully',
                'email': EmailMessageSerializer(email_message).data
            })
        
        except Exception as e:
            # Save failed email
            email_message = EmailMessage.objects.create(
                sender=sender,
                recipient_email=recipient_email,
                subject=subject,
                body=body,
                email_type=email_type,
                status='failed'
            )
            
            return Response({
                'error': f'Failed to send email: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def send_bulk(self, request):
        """Send bulk emails - Admin only"""
        sender = JWTAuthentication.get_user_from_token(request)
        
        recipients = request.data.get('recipients', [])
        subject = request.data.get('subject')
        body = request.data.get('body')
        email_type = request.data.get('email_type', 'bulk')
        
        if not all([recipients, subject, body]):
            return Response({
                'error': 'Recipients, subject, and body are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        sent_count = 0
        failed_count = 0
        
        for recipient in recipients:
            try:
                send_mail(
                    subject=subject,
                    message=body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient],
                    fail_silently=False,
                )
                
                EmailMessage.objects.create(
                    sender=sender,
                    recipient_email=recipient,
                    subject=subject,
                    body=body,
                    email_type=email_type,
                    status='sent'
                )
                
                sent_count += 1
            
            except Exception as e:
                EmailMessage.objects.create(
                    sender=sender,
                    recipient_email=recipient,
                    subject=subject,
                    body=body,
                    email_type=email_type,
                    status='failed'
                )
                
                failed_count += 1
        
        return Response({
            'success': True,
            'message': f'Sent {sent_count} emails, {failed_count} failed',
            'sent': sent_count,
            'failed': failed_count
        })


@api_view(['GET'])
@permission_classes([IsAdmin])
def system_dashboard(request):
    """Get system dashboard statistics"""
    from users.models import User
    from sales.models import Sale
    from customers.models import Customer
    from products.models import Product
    
    # User statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    
    # Today's activity
    today = timezone.now().date()
    today_sales = Sale.objects.filter(created_at__date=today, sale_status='completed').count()
    today_revenue = Sale.objects.filter(created_at__date=today, sale_status='completed').aggregate(
        total=models.Sum('total_amount')
    )['total'] or 0
    
    # System health
    total_customers = Customer.objects.count()
    total_products = Product.objects.filter(is_active=True).count()
    
    # Recent audit logs
    recent_logs = AuditLog.objects.order_by('-created_at')[:10]
    
    # Unread notifications
    unread_notifications = Notification.objects.filter(is_read=False).count()
    
    return Response({
        'users': {
            'total': total_users,
            'active': active_users
        },
        'today': {
            'sales': today_sales,
            'revenue': today_revenue
        },
        'system': {
            'customers': total_customers,
            'products': total_products,
            'unread_notifications': unread_notifications
        },
        'recent_activity': [{
            'user': f"{log.user.first_name} {log.user.last_name}" if log.user else 'System',
            'action': log.action,
            'table': log.table_name,
            'timestamp': log.created_at
        } for log in recent_logs]
    })