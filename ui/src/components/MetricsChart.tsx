import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { Incident } from '../types';

interface Props {
  incidents: Incident[];
}

const MetricsChart: React.FC<Props> = ({ incidents }) => {
  // Group incidents by hour
  const timelineData = React.useMemo(() => {
    const grouped = new Map<string, number>();

    incidents.forEach((incident) => {
      const date = new Date(incident.timestamp);
      const hour = date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
      });

      grouped.set(hour, (grouped.get(hour) || 0) + 1);
    });

    return Array.from(grouped.entries())
      .map(([time, count]) => ({ time, count }))
      .sort((a, b) => a.time.localeCompare(b.time))
      .slice(-10);
  }, [incidents]);

  // Severity distribution
  const severityData = React.useMemo(() => {
    const counts = {
      critical: incidents.filter((i) => i.severity === 'critical').length,
      high: incidents.filter((i) => i.severity === 'high').length,
      medium: incidents.filter((i) => i.severity === 'medium').length,
      low: incidents.filter((i) => i.severity === 'low').length,
    };

    return [
      { name: 'Critical', value: counts.critical, color: '#ef4444' },
      { name: 'High', value: counts.high, color: '#f97316' },
      { name: 'Medium', value: counts.medium, color: '#eab308' },
      { name: 'Low', value: counts.low, color: '#3b82f6' },
    ].filter((d) => d.value > 0);
  }, [incidents]);

  // Status distribution
  const statusData = React.useMemo(() => {
    return [
      {
        name: 'Resolved',
        value: incidents.filter((i) => i.status === 'resolved').length,
      },
      {
        name: 'Analyzing',
        value: incidents.filter((i) => i.status === 'analyzing').length,
      },
      {
        name: 'Fallback',
        value: incidents.filter((i) => i.status === 'fallback').length,
      },
      {
        name: 'Error',
        value: incidents.filter((i) => i.status === 'error').length,
      },
    ].filter((d) => d.value > 0);
  }, [incidents]);

  const COLORS = ['#10b981', '#f59e0b', '#f97316', '#ef4444'];

  return (
    <div className="space-y-6">
      {/* Timeline Chart */}
      {timelineData.length > 0 && (
        <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
          <h3 className="font-bold mb-4">📈 Incident Timeline (Last 10 Hours)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={timelineData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="time" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #475569',
                }}
              />
              <Line
                type="monotone"
                dataKey="count"
                stroke="#3b82f6"
                dot={{ fill: '#3b82f6' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Severity and Status Distribution */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Severity Pie Chart */}
        {severityData.length > 0 && (
          <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
            <h3 className="font-bold mb-4">🔴 Severity Distribution</h3>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={severityData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name} (${value})`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {severityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Status Bar Chart */}
        {statusData.length > 0 && (
          <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
            <h3 className="font-bold mb-4">✅ Status Distribution</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={statusData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="name" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #475569',
                  }}
                />
                <Bar dataKey="value" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
};

export default MetricsChart;