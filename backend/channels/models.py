from django.db import models


class Channel(models.Model):
    """A content channel (e.g., YouTube, Twitter, Newsletter)."""
    PLATFORM_CHOICES = [
        ('youtube', 'YouTube'),
        ('twitter', 'Twitter / X'),
        ('instagram', 'Instagram'),
        ('tiktok', 'TikTok'),
        ('newsletter', 'Newsletter'),
        ('blog', 'Blog'),
        ('podcast', 'Podcast'),
    ]

    name = models.CharField(max_length=200)
    platform = models.CharField(max_length=50, choices=PLATFORM_CHOICES)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['platform']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_platform_display()})"


class ChannelMetric(models.Model):
    """Daily performance metrics for a channel."""
    channel = models.ForeignKey(
        Channel,
        on_delete=models.CASCADE,
        related_name='metrics',
    )
    date = models.DateField()
    impressions = models.BigIntegerField(default=0)
    engagements = models.BigIntegerField(default=0)
    clicks = models.BigIntegerField(default=0)
    conversions = models.BigIntegerField(default=0)
    revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ['-date']
        unique_together = [['channel', 'date']]
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['channel', 'date']),
        ]

    def __str__(self):
        return f"{self.channel.name} on {self.date}"

    @property
    def engagement_rate(self):
        if self.impressions == 0:
            return 0
        return round((self.engagements / self.impressions) * 100, 2)

    @property
    def conversion_rate(self):
        if self.clicks == 0:
            return 0
        return round((self.conversions / self.clicks) * 100, 2)
