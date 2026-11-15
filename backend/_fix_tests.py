content = '''import pytest
from datetime import date, timedelta
from django.core.cache import cache
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
    cache.clear()
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
    cache.clear()  # ← Force fresh query, no cache hit
    ch_ids = ','.join(str(ch.id) for ch in sample_channels)
    today = date.today()

    # Should be exactly 3 queries:
    # 1) timeseries aggregate, 2) per-channel aggregate, 3) grand totals
    with django_assert_num_queries(3):
        response = api_client.get('/api/reports/aggregate/', {
            'channels': ch_ids,
            'start_date': (today - timedelta(days=15)).isoformat(),
            'end_date': today.isoformat(),
        })
        assert response.status_code == 200


@pytest.mark.django_db
def test_aggregation_uses_cache(api_client, sample_channels, sample_metrics, django_assert_num_queries):
    """Verify second identical request uses cache (0 queries)."""
    cache.clear()
    ch_ids = ','.join(str(ch.id) for ch in sample_channels)
    today = date.today()

    # First call — populates cache (3 queries)
    with django_assert_num_queries(3):
        api_client.get('/api/reports/aggregate/', {
            'channels': ch_ids,
            'start_date': (today - timedelta(days=15)).isoformat(),
            'end_date': today.isoformat(),
        })

    # Second call — should hit cache (0 queries!)
    with django_assert_num_queries(0):
        r = api_client.get('/api/reports/aggregate/', {
            'channels': ch_ids,
            'start_date': (today - timedelta(days=15)).isoformat(),
            'end_date': today.isoformat(),
        })
        assert r.json()['cached'] is True


@pytest.mark.django_db
def test_aggregation_date_range_filter(api_client, sample_channels, sample_metrics):
    """Verify date range properly filters data."""
    cache.clear()
    today = date.today()
    response = api_client.get('/api/reports/aggregate/', {
        'channels': str(sample_channels[0].id),
        'start_date': (today - timedelta(days=2)).isoformat(),
        'end_date': today.isoformat(),
    })
    data = response.json()
    assert len(data['timeseries']) == 3
    assert data['totals']['impressions'] == 3000


@pytest.mark.django_db
def test_aggregation_granularity_weekly(api_client, sample_channels, sample_metrics):
    """Verify weekly granularity groups data correctly."""
    cache.clear()
    today = date.today()
    response = api_client.get('/api/reports/aggregate/', {
        'channels': str(sample_channels[0].id),
        'start_date': (today - timedelta(days=15)).isoformat(),
        'end_date': today.isoformat(),
        'granularity': 'weekly',
    })
    data = response.json()
    assert len(data['timeseries']) < 10
'''
with open('tests/test_aggregation.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('✅ Updated test_aggregation.py')
print('   - Added cache.clear() to all aggregation tests')
print('   - Added new test_aggregation_uses_cache to prove cache works')