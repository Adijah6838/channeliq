from django.urls import path
from .views import ChannelListView, ChannelDetailView, AggregateReportView

urlpatterns = [
    path('channels/', ChannelListView.as_view(), name='channel-list'),
    path('channels/<int:pk>/', ChannelDetailView.as_view(), name='channel-detail'),
    path('reports/aggregate/', AggregateReportView.as_view(), name='report-aggregate'),
]
