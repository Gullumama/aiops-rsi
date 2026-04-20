import React from 'react';
import { Incident } from '../types';
import ReactMarkdown from 'react-markdown';
import RCADisplay from './RCADisplay';

interface Props {
  incident: Incident;
}

const IncidentDetail: React.FC<Props> = ({ incident }) => {
  return (
    <div className="space-y-6 mt-4">
      {/* Logs Section */}
      <div>
        <h3 className="font-semibold text-sm text-slate-300 mb-2">📝 Logs</h3>
        <div className="bg-slate-900 rounded p-3 text-xs font-mono text-slate-300 max-h-32 overflow-y-auto">
          {incident.logs || 'No logs available'}
        </div>
      </div>

      {/* Events Section */}
      <div>
        <h3 className="font-semibold text-sm text-slate-300 mb-2">⚡ Events</h3>
        <div className="bg-slate-900 rounded p-3 text-xs font-mono text-slate-300 max-h-32 overflow-y-auto">
          {incident.events || 'No events'}
        </div>
      </div>

      {/* Remediation Section */}
      {incident.remediation && (
        <div>
          <h3 className="font-semibold text-sm text-slate-300 mb-2">🔧 Remediation</h3>
          <div className="bg-slate-900 rounded p-3">
            <div className="text-xs">
              <div className="flex gap-2 mb-2">
                <span className="font-semibold text-slate-400">Status:</span>
                <span className={`font-semibold ${
                  incident.remediation.status === 'success'
                    ? 'text-green-400'
                    : 'text-yellow-400'
                }`}>
                  {incident.remediation.status}
                </span>
              </div>
              <div className="flex gap-2 mb-2">
                <span className="font-semibold text-slate-400">Action:</span>
                <span>{incident.remediation.action}</span>
              </div>
              <div className="text-slate-300">{incident.remediation.message}</div>
            </div>
          </div>
        </div>
      )}

      {/* RCA Display */}
      <RCADisplay incident={incident} />

      {/* Correlation */}
      {incident.correlation && (
        <div>
          <h3 className="font-semibold text-sm text-slate-300 mb-2">🔗 Correlation</h3>
          <div className="bg-red-900/20 border border-red-700 rounded p-3">
            <p className="text-sm text-red-200">{incident.correlation.message}</p>
            <p className="text-xs text-red-300 mt-2">
              Affecting {incident.correlation.affected_pods} pods
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default IncidentDetail;