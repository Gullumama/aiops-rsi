import React, { useState, useEffect } from 'react';
import {
  AlertCircle,
  CheckCircle,
  Clock,
  TrendingUp,
  Eye,
  RefreshCw,
} from 'lucide-react';
import apiClient from '../services/api';
import { Incident, IncidentStats } from '../types';
import IncidentList from './IncidentList';
import NamespaceFilter from './NamespaceFilter';
import MetricsChart from './MetricsChart';
import toast from 'react-hot-toast';

const Dashboard: React.FC = () => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [stats, setStats] = useState<IncidentStats | null>(null);
  const [selectedNamespace, setSelectedNamespace] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [incidents, stats] = await Promise.all([
        apiClient.getIncidents(),
        apiClient.getIncidentStats(),
      ]);

      setIncidents(incidents);
      setStats(stats);
    } catch (error) {
      console.error('Failed to fetch data:', error);
      toast.error('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await fetchData();
      toast.success('Data refreshed');
    } catch (error) {
      toast.error('Failed to refresh data');
    } finally {
      setRefreshing(false);
    }
  };

  const filteredIncidents = selectedNamespace
    ? incidents.filter((i) => i.namespace === selectedNamespace)
    : incidents;

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      {/* Header */}
      <div className="border-b border-slate-700 bg-slate-800">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold">AIOps Dashboard</h1>
              <p className="text-slate-400 mt-1">
                AI-powered Kubernetes RCA and Remediation
              </p>
            </div>
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors disabled:opacity-50"
            >
              <RefreshCw size={20} className={refreshing ? 'animate-spin' : ''} />
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <StatCard
              icon={<AlertCircle className="text-red-500" />}
              label="Critical"
              value={stats.critical}
              color="red"
            />
            <StatCard
              icon={<AlertCircle className="text-orange-500" />}
              label="High"
              value={stats.high}
              color="orange"
            />
            <StatCard
              icon={<Clock className="text-yellow-500" />}
              label="Medium"
              value={stats.medium}
              color="yellow"
            />
            <StatCard
              icon={<CheckCircle className="text-green-500" />}
              label="Resolved"
              value={stats.resolved}
              color="green"
            />
          </div>
        </div>
      )}

      {/* Filters and Content */}
      <div className="max-w-7xl mx-auto px-6 pb-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar */}
          <div className="lg:col-span-1">
            <NamespaceFilter
              selectedNamespace={selectedNamespace}
              onNamespaceChange={setSelectedNamespace}
            />
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            {loading ? (
              <div className="flex items-center justify-center h-96">
                <div className="animate-spin">
                  <RefreshCw size={40} />
                </div>
              </div>
            ) : (
              <>
                <MetricsChart incidents={filteredIncidents} />
                <div className="mt-8">
                  <IncidentList incidents={filteredIncidents} />
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: number;
  color: string;
}

const StatCard: React.FC<StatCardProps> = ({ icon, label, value, color }) => {
  return (
    <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 hover:border-slate-600 transition-colors">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-slate-400 text-sm">{label}</p>
          <p className="text-3xl font-bold mt-2">{value}</p>
        </div>
        <div className="p-3 bg-slate-700 rounded-lg">{icon}</div>
      </div>
    </div>
  );
};

export default Dashboard;