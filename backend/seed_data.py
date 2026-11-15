import random
from datetime import date, timedelta
from channels.models import Channel, ChannelMetric

print("Seeding channels...")
platforms = [
    ('YouTube Channel', 'youtube', 'youtube-channel'),
    ('Twitter Account', 'twitter', 'twitter-account'),
    ('Instagram Profile', 'instagram', 'instagram-profile'),
    ('TikTok Channel', 'tiktok', 'tiktok-channel'),
    ('Weekly Newsletter', 'newsletter', 'weekly-newsletter'),
]

channels = []
for name, platform, slug in platforms:
    ch, created = Channel.objects.get_or_create(
        slug=slug,
        defaults={'name': name, 'platform': platform, 'description': f'Sample {platform} channel'},
    )
    channels.append(ch)
    print(f"  {'Created' if created else 'Exists'}: {ch.name}")

print(f"\nSeeding 90 days of metrics for {len(channels)} channels...")
today = date.today()
count = 0
for channel in channels:
    for days_ago in range(90):
        d = today - timedelta(days=days_ago)
        impressions = random.randint(1000, 50000)
        engagements = random.randint(50, max(51, int(impressions * 0.15)))
        clicks = random.randint(20, max(21, int(impressions * 0.08)))
        conversions = random.randint(0, max(1, int(clicks * 0.2)))
        revenue = round(conversions * random.uniform(5, 50), 2)

        _, created = ChannelMetric.objects.get_or_create(
            channel=channel,
            date=d,
            defaults={
                'impressions': impressions,
                'engagements': engagements,
                'clicks': clicks,
                'conversions': conversions,
                'revenue': revenue,
            },
        )
        if created:
            count += 1

print(f"\n[OK] Created {count} metrics")
print(f"Total channels: {Channel.objects.count()}")
print(f"Total metrics: {ChannelMetric.objects.count()}")