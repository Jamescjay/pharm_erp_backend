from django.db import models
from django.utils import timezone

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)
    permissions = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "roles"
        verbose_name = "Role"
        verbose_name_plural = "Roles"

    def __str__(self):
        return self.name

class User(models.Model):
    employee_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    role = models.ForeignKey('Role', on_delete=models.SET_NULL, null=True, related_name="users")
    password_hash = models.CharField(max_length=255)
    profile_image_url = models.URLField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.role})"

    @property
    def is_authenticated(self):
        return True

class UserPermission(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name="user_permissions")
    module = models.CharField(max_length=100)
    can_view = models.BooleanField(default=False)
    can_create = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "user_permissions"
        unique_together = ['user', 'module']
        ordering = ["user", "module"]

    def __str__(self):
        return f"{self.user.email} - {self.module}"

class UserSession(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name="user_sessions")
    session_token = models.CharField(max_length=255, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "user_sessions"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Session for {self.user.email} - {self.created_at}"