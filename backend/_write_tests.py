import os

# Ensure tests directory
os.makedirs('tests', exist_ok=True)
open('tests/__init__.py', 'w').close()

# ============================================
# pytest.ini
# ============================================
pytest_ini = """[pytest]
DJANGO_SETTINGS_MODULE = config.settings
python_files = tests.py test_*.py *_tests.py
addopts = -v --tb=short
"""
with open('pytest.ini', 'w', encoding='utf-8') as f:
    f.write(pytest_ini)

# ============================================
# conftest.py — fixtures
# ============================================
conftest = """import pytest
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
"""
with open('tests/conftest.py', 'w', encoding='utf-8') as f:
    f.write(conftest)

# ============================================
# tests/test_aggregation.py
# ============================================
test_file = '''import pytest
from datetime import date, timedelta
from channels.models import Channel, ChannelMetric


@pytest.mark.django_db
def test_channel_list_endpoint(api_client, sample_channels):
    """Verify channels endpoint returns paginated list."""
    response = api_client.get('/api/channels/')
    assert response.status_code == 200
    data = response.json()
    assert data['count'] == 2
    assert len(data['results']) == 2


@pytest.mark.django_db
def test_aggregation_requires_params(api_client):
    """Verify aggregation requires channels, start_date, end_date."""
    response = api_client.get('/api/reports/aggregate/')
    assert response.status_code == 400
    assert 'required' in response.json()['error'].lower()


@pytest.mark.django_db
def test_aggregation_invalid_channel_ids(api_client):
    """Verify aggregation rejects non-numeric channel IDs."""
    response = api_client.get('/api/reports/aggregate/', {
        'channels': 'abc,def',
        'start_date': '2026-01-01',
        'end_date': '2026-01-31',
    })
    assert response.status_code == 400


@pytest.mark.django_db
def test_aggregation_invalid_granularity(api_client, sample_channels):
    """Verify aggregation rejects invalid granularity."""
    response = api_client.get('/api/reports/aggregate/', {
        'channels': str(sample_channels[0].id),
        'start_date': '2026-01-01',
        'end_date': '2026-01-31',
        'granularity': 'hourly',
    })
    assert response.status_code == 400


@pytest.mark.django_db
def test_aggregation_correctness(api_client, sample_channels, sample_metrics):
    """Verify aggregation math is correct (totals match per-channel sums)."""
    ch_ids = ','.join(str(ch.id) for ch in sample_channels)
    today = date.today()
    response = api_client.get('/api/reports/aggregate/', {
        'channels': ch_ids,
        'start_date': (today - timedelta(days=15)).isoformat(),
        'end_date': today.isoformat(),
        'granularity': 'daily',
    })
    assert response.status_code == 200
    data = response.json()

    # Expected: 2 channels x 10 days x 1000 impressions (ch1) + 2000 (ch2) = 30000
    # Per-channel expected: ch1 = 10 days * 1000 = 10000, ch2 = 10 days * 2000 = 20000
    ch1 = next(c for c in data['channels'] if c['channel_id'] == sample_channels[0].id)
    ch2 = next(c for c in data['channels'] if c['channel_id'] == sample_channels[1].id)

    assert ch1['impressions'] == 10000
    assert ch2['impressions'] == 20000
    assert data['totals']['impressions'] == 30000
    assert data['totals']['engagements'] == 3000
    assert data['totals']['clicks'] == 1500


@pytest.mark.django_db
def test_aggregation_no_n_plus_one(api_client, sample_channels, sample_metrics, django_assert_num_queries):
    """Verify aggregation uses a fixed number of queries regardless of channel count."""
    ch_ids = ','.join(str(ch.id) for ch in sample_channels)
    today = date.today()

    # With 2 channels, should be exactly 3 queries:
    # 1) timeseries aggregate, 2) per-channel aggregate, 3) grand totals
    with django_assert_num_queries(3):
        response = api_client.get('/api/reports/aggregate/', {
            'channels': ch_ids,
            'start_date': (today - timedelta(days=15)).isoformat(),
            'end_date': today.isoformat(),
        })
        assert response.status_code == 200


@pytest.mark.django_db
def test_aggregation_date_range_filter(api_client, sample_channels, sample_metrics):
    """Verify date range properly filters data."""
    today = date.today()
    # Ask for only last 3 days
    response = api_client.get('/api/reports/aggregate/', {
        'channels': str(sample_channels[0].id),
        'start_date': (today - timedelta(days=2)).isoformat(),
        'end_date': today.isoformat(),
    })
    data = response.json()
    # Should have 3 timeseries points (today, today-1, today-2)
    assert len(data['timeseries']) == 3
    # Each day has 1000 impressions
    assert data['totals']['impressions'] == 3000


@pytest.mark.django_db
def test_aggregation_granularity_weekly(api_client, sample_channels, sample_metrics):
    """Verify weekly granularity groups data correctly."""
    today = date.today()
    response = api_client.get('/api/reports/aggregate/', {
        'channels': str(sample_channels[0].id),
        'start_date': (today - timedelta(days=15)).isoformat(),
        'end_date': today.isoformat(),
        'granularity': 'weekly',
    })
    data = response.json()
    # Weekly should have fewer points than daily
    assert len(data['timeseries']) < 10
'''
with open('tests/test_aggregation.py', 'w', encoding='utf-8') as f:
    f.write(test_file)

print('✅ Created 3 test files:')
print('   - tests/__init__.py')
print('   - tests/conftest.py')
print('   - tests/test_aggregation.py')
print('   - pytest.ini')