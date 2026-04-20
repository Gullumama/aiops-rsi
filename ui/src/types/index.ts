// Type definitions for AIOps Dashboard

export interface Incident {
  id: string;
  pod: string;
  namespace: string;
  timestamp: string;
  rule: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  metrics: Record<string, any>;
  logs: string;
  events: string;
  correlation: {
    type: string;
    message: string;
    affected_pods: number;
  } | null;
  remediation: {
    status: string;
    action: string;
    message: string;
  };
  ai_rca: string;
  status: 'analyzing' | 'resolved' | 'fallback' | 'error';
  k8sgpt_analysis?: {
    summary: string;
    findings: string[];
    recommendations: string[];
  };
}

export interface IncidentStats {
  total: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  resolved: number;
  analyzing: number;
}

export interface NamespaceStats {
  namespace: string;
  pod_count: number;
  incident_count: number;
  severity: string;
  last_incident: string;
}

export interface TimelineEvent {
  timestamp: string;
  type: 'incident' | 'remediation' | 'analysis';
  pod: string;
  namespace: string;
  message: string;
  severity: string;
}

export interface APIResponse<T> {
  success: boolean;
  data: T;
  error?: string;
  timestamp: string;
}

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  incidents_count: number;
  memory_db_size: number;
  timestamp: string;
}

export interface AnalysisResult {
  root_cause: string;
  recommended_fix: string;
  prevention_steps: string;
  source: 'ollama' | 'k8sgpt' | 'fallback';
}