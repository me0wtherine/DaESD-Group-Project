from django.db import models
from accounts.models import Accounts, Producers


class Notification(models.Model):
    customer = models.ForeignKey(
        Accounts,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications"
    )

    producer = models.ForeignKey(
        Producers,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications"
    )

    title = models.CharField(max_length=200, default="")
    message = models.TextField(default="")
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title