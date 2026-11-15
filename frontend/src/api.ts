import axios from 'axios';

export const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: { 'Content-Type': 'application/json' },
});

export interface Channel {
  id: number;
  name: string;
  platform: string;
  slug: string;
  description: string;
}

export interface TimeseriesPoint {
  period: string;
  impressions: number;
  engagements: number;
  clicks: number;
  conversions: number;
  revenue: number;
}

export interface ChannelSummary {
  channel_id: number;
  channel_name: string;
  platform: string;
  impressions: number;
  engagements: number;
  clicks: number;
  conversions: number;
  revenue: number;
  engagement_rate: number;
}

export interface AggregateReport {
  channels: ChannelSummary[];
  timeseries: TimeseriesPoint[];
  totals: { impressions: number; engagements: number; clicks: number; conversions: number; revenue: number; };
  period: { start: string; end: string; granularity: string };
  cached: boolean;
}
