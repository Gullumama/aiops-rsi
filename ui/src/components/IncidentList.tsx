import React, { useState } from 'react';
import { Incident } from '../types';
import { ChevronDown, ChevronUp } from 'lucide-react';
import IncidentDetail from './IncidentDetail';

interface Props {
  incidents: Incident[];
}

const IncidentList: React.FC<Props> = ({ incidents }) => {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-900 text-red-200';
      case 'high':
        return 'bg-orange-900 text-orange-200';
      case 'medium':
        return 'bg-yellow-900 text-yellow-200';
      case 'low':
        return 'bg-blue-900 text-blue-200';
      default:
        return 'bg-slate-700 text-slate-200';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'resolved':
        return 'text-green-400';
      case 'analyzing':
        return 'text-yellow-400';
      case 'fallback':
        return 'text-orange-400';
      case 'error':
        return 'text-red-400';
      default:
        return 'text-slate-400';
    }
  };

  return (
    <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden">
      <div className="p-6 border-b border-slate-700">
        <h2 className="text-xl font-bold flex items-center gap-2">
          📋 Incidents
          <span className="ml-auto text-sm text-slate-400">
            Total: {incidents.length}
          </span>
        </h2>
      </div>

      <div className="divide-y divide-slate-700">
        {incidents.length === 0 ? (
          <div className="p-8 text-center text-slate-400">
            No incidents found
          </div>
        ) : (
          incidents.map((incident) => (
            <div key={incident.id} className="hover:bg-slate-700/50 transition-colors">
              <button
                onClick={() =>
                  setExpandedId(expandedId === incident.id ? null : incident.id)
                }
                className="w-full p-4 text-left flex items-center gap-4"
              >
                {/* Expand Button */}
                <div className="flex-shrink-0">
                  {expandedId === incident.id ? (
                    <ChevronUp size={20} />
                  ) : (
                    <ChevronDown size={20} />
                  )}
                </div>

                {/* Severity Badge */}
                <div className={`px-3 py-1 rounded text-xs font-semibold ${getSeverityColor(incident.severity)}`}>
                  {incident.severity.toUpperCase()}
                </div>

                {/* Pod and Namespace */}
                <div className="flex-grow min-w-0">
                  <div className="font-semibold truncate">{incident.pod}</div>
                  <div className="text-sm text-slate-400">
                    {incident.namespace} • {incident.rule}
                  </div>
                </div>

                {/* Status and Time */}
                <div className="flex-shrink-0 text-right">
                  <div className={`text-xs font-semibold ${getStatusColor(incident.status)}`}>
                    {incident.status.toUpperCase()}
                  </div>
                  <div className="text-xs text-slate-400 mt-1">
                    {new Date(incident.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </button>

              {/* Expanded Detail */}
              {expandedId === incident.id && (
                <div className="px-4 pb-4 border-t border-slate-700 bg-slate-900/50">
                  <IncidentDetail incident={incident} />
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default IncidentList;