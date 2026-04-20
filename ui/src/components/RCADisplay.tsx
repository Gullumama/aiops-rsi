import React, { useState } from 'react';
import { Incident } from '../types';
import ReactMarkdown from 'react-markdown';
import { Zap, Brain, AlertCircle } from 'lucide-react';

interface Props {
  incident: Incident;
}

const RCADisplay: React.FC<Props> = ({ incident }) => {
  const [showK8sGPT, setShowK8sGPT] = useState(false);

  const isAnalyzing = incident.status === 'analyzing';
  const isFallback = incident.status === 'fallback';

  return (
    <div className="space-y-4">
      {/* AI-RCA Section */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <Brain size={18} className="text-blue-400" />
          <h3 className="font-semibold text-sm text-slate-300">
            🤖 AI Root Cause Analysis
          </h3>
          {isAnalyzing && (
            <span className="ml-auto text-xs text-yellow-400 flex items-center gap-1">
              <span className="animate-pulse">⏳</span> Analyzing...
            </span>
          )}
          {isFallback && (
            <span className="ml-auto text-xs text-orange-400 flex items-center gap-1">
              <AlertCircle size={14} /> Fallback Mode
            </span>
          )}
        </div>

        <div className="bg-slate-900 rounded p-4 text-sm text-slate-300">
          <ReactMarkdown
            components={{
              h2: ({ node, ...props }) => (
                <h2 className="font-bold text-blue-300 mt-3 mb-2" {...props} />
              ),
              h3: ({ node, ...props }) => (
                <h3 className="font-semibold text-blue-300 mt-2 mb-1" {...props} />
              ),
              p: ({ node, ...props }) => (
                <p className="mb-2" {...props} />
              ),
              ul: ({ node, ...props }) => (
                <ul className="list-disc list-inside mb-2" {...props} />
              ),
              li: ({ node, ...props }) => (
                <li className="mb-1" {...props} />
              ),
              code: ({ node, inline, ...props }) => (
                <code
                  className={
                    inline
                      ? 'bg-slate-800 px-2 py-1 rounded text-xs'
                      : 'block bg-slate-800 p-2 rounded my-2 overflow-x-auto'
                  }
                  {...props}
                />
              ),
            }}
          >
            {incident.ai_rca}
          </ReactMarkdown>
        </div>
      </div>

      {/* K8sGPT Analysis (if available) */}
      {incident.k8sgpt_analysis && (
        <div>
          <button
            onClick={() => setShowK8sGPT(!showK8sGPT)}
            className="flex items-center gap-2 text-sm font-semibold text-green-400 hover:text-green-300"
          >
            <Zap size={18} />
            K8sGPT Analysis
            <span className="ml-auto text-xs text-slate-400">
              {showK8sGPT ? '▼' : '▶'}
            </span>
          </button>

          {showK8sGPT && (
            <div className="mt-2 bg-green-900/20 border border-green-700 rounded p-4">
              <div className="space-y-3">
                {incident.k8sgpt_analysis.findings && (
                  <div>
                    <h4 className="font-semibold text-green-300 text-sm mb-2">
                      Findings:
                    </h4>
                    <ul className="space-y-1">
                      {incident.k8sgpt_analysis.findings.map((finding, i) => (
                        <li key={i} className="text-sm text-green-200">
                          • {finding}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {incident.k8sgpt_analysis.recommendations && (
                  <div>
                    <h4 className="font-semibold text-green-300 text-sm mb-2">
                      Recommendations:
                    </h4>
                    <ul className="space-y-1">
                      {incident.k8sgpt_analysis.recommendations.map(
                        (rec, i) => (
                          <li key={i} className="text-sm text-green-200">
                            • {rec}
                          </li>
                        )
                      )}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Source Indicator */}
      <div className="text-xs text-slate-500 flex items-center gap-2">
        <span>Source:</span>
        <span className={`px-2 py-1 rounded ${
          isFallback
            ? 'bg-orange-900/30 text-orange-300'
            : 'bg-blue-900/30 text-blue-300'
        }`}>
          {isFallback ? 'Fallback Rules' : 'Ollama AI'}
        </span>
      </div>
    </div>
  );
};

export default RCADisplay;