from django.db import models
from django.utils import timezone
from .user import User

class EmailMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_emails")
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_emails")
    subject = models.CharField(max_length=255)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    sent_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "email_messages"
        ordering = ["-sent_at"]

    def __str__(self):
        return f"{self.subject} from {self.sender.email} to {self.recipient.email}"
