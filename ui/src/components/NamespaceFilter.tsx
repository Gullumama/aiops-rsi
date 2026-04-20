import React, { useState, useEffect } from 'react';
import apiClient from '../services/api';
import { Search, Filter } from 'lucide-react';

interface Props {
  selectedNamespace: string | null;
  onNamespaceChange: (namespace: string | null) => void;
}

const NamespaceFilter: React.FC<Props> = ({
  selectedNamespace,
  onNamespaceChange,
}) => {
  const [namespaces, setNamespaces] = useState<string[]>([]);
  const [namespaceStats, setNamespaceStats] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchNamespaces();
  }, []);

  const fetchNamespaces = async () => {
    try {
      setLoading(true);
      const [namespaces, stats] = await Promise.all([
        apiClient.getNamespaces(),
        apiClient.getNamespaceStats(),
      ]);

      setNamespaces(namespaces);
      setNamespaceStats(stats);
    } catch (error) {
      console.error('Failed to fetch namespaces:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredNamespaces = namespaces.filter((ns) =>
    ns.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getStatForNamespace = (namespace: string) => {
    return namespaceStats.find((s) => s.namespace === namespace);
  };

  return (
    <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
      <div className="flex items-center gap-2 mb-4">
        <Filter size={20} className="text-blue-400" />
        <h2 className="font-bold">Namespaces</h2>
      </div>

      {/* Search */}
      <div className="relative mb-4">
        <Search size={16} className="absolute left-3 top-3 text-slate-400" />
        <input
          type="text"
          placeholder="Search namespaces..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-10 pr-3 py-2 bg-slate-700 text-white rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Namespace List */}
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {/* All Namespaces Option */}
        <button
          onClick={() => onNamespaceChange(null)}
          className={`w-full text-left px-3 py-2 rounded transition-colors ${
            selectedNamespace === null
              ? 'bg-blue-600 text-white'
              : 'hover:bg-slate-700'
          }`}
        >
          <div className="font-semibold text-sm">All Namespaces</div>
          <div className="text-xs text-slate-400 mt-1">
            Total: {namespaceStats.reduce((sum, s) => sum + s.incident_count, 0)}
          </div>
        </button>

        {/* Individual Namespaces */}
        {loading ? (
          <div className="text-center text-slate-400 py-4">Loading...</div>
        ) : filteredNamespaces.length === 0 ? (
          <div className="text-center text-slate-400 py-4 text-sm">
            No namespaces found
          </div>
        ) : (
          filteredNamespaces.map((namespace) => {
            const stat = getStatForNamespace(namespace);
            return (
              <button
                key={namespace}
                onClick={() => onNamespaceChange(namespace)}
                className={`w-full text-left px-3 py-3 rounded transition-colors border ${
                  selectedNamespace === namespace
                    ? 'bg-blue-600 border-blue-500'
                    : 'border-slate-600 hover:bg-slate-700'
                }`}
              >
                <div className="font-semibold text-sm">{namespace}</div>
                {stat && (
                  <div className="text-xs text-slate-400 mt-1 space-y-1">
                    <div>Pods: {stat.pod_count}</div>
                    <div className="flex items-center gap-2">
                      <span>Incidents: {stat.incident_count}</span>
                      <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                        stat.severity === 'critical'
                          ? 'bg-red-900 text-red-200'
                          : stat.severity === 'high'
                          ? 'bg-orange-900 text-orange-200'
                          : 'bg-slate-600 text-slate-200'
                      }`}>
                        {stat.severity}
                      </span>
                    </div>
                  </div>
                )}
              </button>
            );
          })
        )}
      </div>
    </div>
  );
};

export default NamespaceFilter;