from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views


router = DefaultRouter()
router.register(r'settings', views.SystemSettingViewSet, basename='system-settings')
router.register(r'audit-logs', views.AuditLogViewSet, basename='audit-logs')
router.register(r'notifications', views.NotificationViewSet, basename='notifications')
router.register(r'emails', views.EmailMessageViewSet, basename='emails')

urlpatterns = [
    path('dashboard/', views.system_dashboard, name='system-dashboard'),
    path('', include(router.urls)),
]