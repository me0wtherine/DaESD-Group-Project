from django.db import models
from accounts.models import Accounts

class Notification(models.Model):
    customer = models.ForeignKey(Accounts, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.customer.name}: {self.message[:50]}"

