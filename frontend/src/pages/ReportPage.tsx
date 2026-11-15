import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { api } from '../api';
import type { Channel, AggregateReport } from '../api';
import ChannelSelector from '../components/ChannelSelector';
import StatCard from '../components/StatCard';

function defaultStart() { const d = new Date(); d.setDate(d.getDate() - 30); return d.toISOString().slice(0, 10); }
function defaultEnd() { return new Date().toISOString().slice(0, 10); }

export default function ReportPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [channels, setChannels] = useState<Channel[]>([]);
  const [report, setReport] = useState<AggregateReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const selectedIds = (searchParams.get('channels') || '').split(',').filter(Boolean).map(Number);
  const startDate = searchParams.get('start_date') || defaultStart();
  const endDate = searchParams.get('end_date') || defaultEnd();
  const granularity = searchParams.get('granularity') || 'daily';

  useEffect(() => { api.get<{ results: Channel[] }>('/channels/').then(r => setChannels(r.data.results)); }, []);

  useEffect(() => {
    if (selectedIds.length === 0) { setReport(null); return; }
    setLoading(true); setError('');
    api.get<AggregateReport>('/reports/aggregate/', { params: { channels: selectedIds.join(','), start_date: startDate, end_date: endDate, granularity } })
      .then(r => setReport(r.data))
      .catch(e => setError(e.response?.data?.error || 'Failed to load report'))
      .finally(() => setLoading(false));
  }, [searchParams]);

  const updateParam = (key: string, value: string) => {
    const next = new URLSearchParams(searchParams);
    if (value) next.set(key, value); else next.delete(key);
    setSearchParams(next);
  };

  const exportCsv = () => {
    if (!report) return;
    const headers = ['period','impressions','engagements','clicks','conversions','revenue'];
    const rows = report.timeseries.map(p => [p.period, p.impressions, p.engagements, p.clicks, p.conversions, p.revenue]);
    const csv = [headers, ...rows].map(r => r.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `channeliq-${startDate}-to-${endDate}.csv`; a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b px-6 py-4 flex justify-between items-center shadow-sm">
        <h1 className="text-xl font-bold text-blue-600">ChannelIQ</h1>
        <button onClick={exportCsv} disabled={!report} className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-500 disabled:opacity-50 text-sm font-medium">Export CSV</button>
      </nav>
      <main className="max-w-7xl mx-auto p-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <aside className="lg:col-span-1 space-y-4">
            <ChannelSelector channels={channels} selectedIds={selectedIds} onChange={ids => updateParam('channels', ids.join(','))} />
            <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Date Range</h3>
              <div className="space-y-3">
                <div><label className="block text-xs text-gray-500 mb-1">Start</label><input type="date" value={startDate} onChange={e => updateParam('start_date', e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm" /></div>
                <div><label className="block text-xs text-gray-500 mb-1">End</label><input type="date" value={endDate} onChange={e => updateParam('end_date', e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm" /></div>
                <div><label className="block text-xs text-gray-500 mb-1">Granularity</label><select value={granularity} onChange={e => updateParam('granularity', e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"><option value="daily">Daily</option><option value="weekly">Weekly</option><option value="monthly">Monthly</option></select></div>
              </div>
            </div>
          </aside>
          <div className="lg:col-span-3 space-y-6">
            {error && <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded-lg text-sm">{error}</div>}
            {!report && !loading && selectedIds.length === 0 && <div className="bg-white p-12 rounded-xl text-center border border-dashed border-gray-300"><p className="text-gray-500">Select one or more channels to generate a report.</p></div>}
            {loading && <div className="text-center py-12 text-gray-500">Loading report...</div>}
            {report && !loading && (
              <>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <StatCard label="Impressions" value={report.totals.impressions.toLocaleString()} />
                  <StatCard label="Engagements" value={report.totals.engagements.toLocaleString()} />
                  <StatCard label="Clicks" value={report.totals.clicks.toLocaleString()} />
                  <StatCard label="Revenue" value={`$${report.totals.revenue.toLocaleString()}`} />
                </div>
                {report.cached && <p className="text-xs text-green-600">Served from Redis cache</p>}
                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                  <h2 className="text-lg font-bold mb-4">Performance Over Time</h2>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={report.timeseries}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
                      <XAxis dataKey="period" tick={{ fontSize: 12 }} /><YAxis tick={{ fontSize: 12 }} /><Tooltip /><Legend />
                      <Line type="monotone" dataKey="impressions" stroke="#3b82f6" strokeWidth={2} dot={false} />
                      <Line type="monotone" dataKey="engagements" stroke="#10b981" strokeWidth={2} dot={false} />
                      <Line type="monotone" dataKey="clicks" stroke="#f59e0b" strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                  <h2 className="text-lg font-bold mb-4">Channel Comparison</h2>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={report.channels}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
                      <XAxis dataKey="channel_name" tick={{ fontSize: 12 }} /><YAxis tick={{ fontSize: 12 }} /><Tooltip /><Legend />
                      <Bar dataKey="impressions" fill="#3b82f6" />
                      <Bar dataKey="engagements" fill="#10b981" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
