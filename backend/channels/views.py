from django.db.models import Sum
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek
from django.core.cache import cache

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

from .models import Channel, ChannelMetric
from .serializers import ChannelSerializer


class ChannelListView(APIView):
    def get(self, request):
        queryset = Channel.objects.all().order_by('name')

        platform = request.query_params.get('platform')
        if platform:
            queryset = queryset.filter(platform=platform)

        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)

        paginator = PageNumberPagination()
        paginator.page_size = int(request.query_params.get('page_size', 20))
        page = paginator.paginate_queryset(queryset, request)
        serializer = ChannelSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class ChannelDetailView(APIView):
    def get(self, request, pk):
        try:
            channel = Channel.objects.get(pk=pk)
        except Channel.DoesNotExist:
            return Response({'error': 'Channel not found'}, status=404)

        metrics = (
            ChannelMetric.objects
            .filter(channel=channel)
            .order_by('-date')[:30]
            .values('date', 'impressions', 'engagements', 'clicks', 'conversions', 'revenue')
        )

        return Response({
            'id': channel.id,
            'name': channel.name,
            'platform': channel.platform,
            'slug': channel.slug,
            'description': channel.description,
            'recent_metrics': list(metrics),
        })


class AggregateReportView(APIView):
    def get(self, request):
        channels_param = request.query_params.get('channels', '').strip()
        start_date = request.query_params.get('start_date', '').strip()
        end_date = request.query_params.get('end_date', '').strip()
        granularity = request.query_params.get('granularity', 'daily').strip()

        if not channels_param or not start_date or not end_date:
            return Response(
                {'error': 'channels, start_date, and end_date are required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            channel_ids = sorted([int(c) for c in channels_param.split(',') if c.strip()])
        except ValueError:
            return Response({'error': 'Invalid channel IDs'}, status=400)

        if not channel_ids:
            return Response({'error': 'At least one channel required'}, status=400)

        if granularity not in ('daily', 'weekly', 'monthly'):
            return Response({'error': 'granularity must be daily, weekly, or monthly'}, status=400)

        cache_key = f'report:agg:channels={channel_ids}:start={start_date}:end={end_date}:gran={granularity}'
        cached = cache.get(cache_key)
        if cached:
            cached['cached'] = True
            return Response(cached)

        qs = ChannelMetric.objects.filter(
            channel_id__in=channel_ids,
            date__gte=start_date,
            date__lte=end_date,
        )

        trunc_func = {
            'daily': TruncDate('date'),
            'weekly': TruncWeek('date'),
            'monthly': TruncMonth('date'),
        }[granularity]

        timeseries = list(
            qs
            .annotate(period=trunc_func)
            .values('period')
            .annotate(
                impressions=Sum('impressions'),
                engagements=Sum('engagements'),
                clicks=Sum('clicks'),
                conversions=Sum('conversions'),
                revenue=Sum('revenue'),
            )
            .order_by('period')
        )

        per_channel = list(
            qs
            .values('channel_id', 'channel__name', 'channel__platform')
            .annotate(
                impressions=Sum('impressions'),
                engagements=Sum('engagements'),
                clicks=Sum('clicks'),
                conversions=Sum('conversions'),
                revenue=Sum('revenue'),
            )
            .order_by('-impressions')
        )

        totals = qs.aggregate(
            impressions=Sum('impressions'),
            engagements=Sum('engagements'),
            clicks=Sum('clicks'),
            conversions=Sum('conversions'),
            revenue=Sum('revenue'),
        )

        def safe_int(v): return int(v or 0)
        def safe_float(v): return float(v or 0)

        result = {
            'channels': [
                {
                    'channel_id': row['channel_id'],
                    'channel_name': row['channel__name'],
                    'platform': row['channel__platform'],
                    'impressions': safe_int(row['impressions']),
                    'engagements': safe_int(row['engagements']),
                    'clicks': safe_int(row['clicks']),
                    'conversions': safe_int(row['conversions']),
                    'revenue': safe_float(row['revenue']),
                    'engagement_rate': round((safe_int(row['engagements']) / safe_int(row['impressions']) * 100) if row['impressions'] else 0, 2),
                }
                for row in per_channel
            ],
            'timeseries': [
                {
                    'period': row['period'].isoformat() if row['period'] else None,
                    'impressions': safe_int(row['impressions']),
                    'engagements': safe_int(row['engagements']),
                    'clicks': safe_int(row['clicks']),
                    'conversions': safe_int(row['conversions']),
                    'revenue': safe_float(row['revenue']),
                }
                for row in timeseries
            ],
            'totals': {
                'impressions': safe_int(totals['impressions']),
                'engagements': safe_int(totals['engagements']),
                'clicks': safe_int(totals['clicks']),
                'conversions': safe_int(totals['conversions']),
                'revenue': safe_float(totals['revenue']),
            },
            'period': {
                'start': start_date,
                'end': end_date,
                'granularity': granularity,
            },
            'cached': False,
        }

        cache.set(cache_key, result, timeout=300)
        return Response(result)