from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'roles', views.RoleViewSet, basename='roles')
router.register(r'users', views.UserViewSet, basename='users')
router.register(r'permissions', views.UserPermissionViewSet, basename='permissions')
router.register(r'sessions', views.UserSessionViewSet, basename='sessions')

urlpatterns = [
    path('auth/login/', views.login, name='login'),
    path('auth/logout/', views.logout, name='logout'),
    path('auth/password-reset/', views.request_password_reset, name='request-password-reset'),
    path('auth/password-change/', views.change_password, name='password-change'),
    path('', include(router.urls)),
]