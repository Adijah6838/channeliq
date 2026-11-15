from django.db import models
from django.contrib.auth.models import User
import uuid


class SavedReport(models.Model):
    """A shareable report configuration (channels + date range + filters)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    channel_ids = models.JSONField(default=list)
    start_date = models.DateField()
    end_date = models.DateField()
    filters = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='saved_reports',
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name
