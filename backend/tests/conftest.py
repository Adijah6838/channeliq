import pytest
from datetime import date, timedelta
from rest_framework.test import APIClient
from channels.models import Channel, ChannelMetric


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def sample_channels(db):
    channels = [
        Channel.objects.create(name='Test YouTube', platform='youtube', slug='test-yt'),
        Channel.objects.create(name='Test Twitter', platform='twitter', slug='test-tw'),
    ]
    return channels


@pytest.fixture
def sample_metrics(db, sample_channels):
    today = date.today()
    for i, ch in enumerate(sample_channels):
        for days_ago in range(10):
            ChannelMetric.objects.create(
                channel=ch,
                date=today - timedelta(days=days_ago),
                impressions=1000 * (i + 1),
                engagements=100 * (i + 1),
                clicks=50 * (i + 1),
                conversions=10 * (i + 1),
                revenue=100 * (i + 1),
            )
    return sample_channels
