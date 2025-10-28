from django.db import models
from django.utils import timezone

class SystemSetting(models.Model):
    setting_key = models.CharField(max_length=255, unique=True)
    setting_value = models.TextField()
    setting_type = models.CharField(max_length=50) 
    description = models.TextField(null=True, blank=True)
    updated_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name="updated_settings")
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "system_settings"
        ordering = ["setting_key"]

    def __str__(self):
        return f"{self.setting_key}: {self.setting_value}"

class AuditLog(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs")
    action = models.CharField(max_length=255)
    table_name = models.CharField(max_length=100)
    record_id = models.IntegerField()
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "audit_logs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email if self.user else 'System'} - {self.action} on {self.table_name}.{self.record_id}"

class Notification(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=255)
    message = models.TextField()
    type = models.CharField(max_length=50)
    is_read = models.BooleanField(default=False)
    action_url = models.CharField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notification to {self.user.email}: {self.title}"

class EmailMessage(models.Model):
    sender = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name="sent_emails")
    recipient_email = models.EmailField()
    subject = models.CharField(max_length=255)
    body = models.TextField()
    sent_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, default='sent')
    email_type = models.CharField(max_length=50) 

    class Meta:
        db_table = "email_messages"
        ordering = ["-sent_at"]

    def __str__(self):
        return f"{self.subject} to {self.recipient_email}"