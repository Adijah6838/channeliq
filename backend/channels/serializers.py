from rest_framework import serializers
from .models import Channel, ChannelMetric


class ChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = ['id', 'name', 'platform', 'slug', 'description', 'created_at']


class ChannelMetricSerializer(serializers.ModelSerializer):
    engagement_rate = serializers.ReadOnlyField()
    conversion_rate = serializers.ReadOnlyField()

    class Meta:
        model = ChannelMetric
        fields = [
            'id', 'date', 'impressions', 'engagements',
            'clicks', 'conversions', 'revenue',
            'engagement_rate', 'conversion_rate',
        ]