import axios, { AxiosInstance } from 'axios';
import { Incident, IncidentStats, HealthStatus } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080';

class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Error:', error);
        return Promise.reject(error);
      }
    );
  }

  // Health Check
  async getHealth(): Promise<HealthStatus> {
    try {
      const response = await this.client.get<HealthStatus>('/health');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch health:', error);
      throw error;
    }
  }

  // Get all incidents
  async getIncidents(limit: number = 100): Promise<Incident[]> {
    try {
      const response = await this.client.get<{ total: number; recent: Incident[] }>(
        `/incidents?limit=${limit}`
      );
      return response.data.recent;
    } catch (error) {
      console.error('Failed to fetch incidents:', error);
      throw error;
    }
  }

  // Get specific incident
  async getIncident(id: string): Promise<Incident> {
    try {
      const response = await this.client.get<Incident>(`/incidents/${id}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch incident:', error);
      throw error;
    }
  }

  // Get incidents by namespace
  async getIncidentsByNamespace(namespace: string): Promise<Incident[]> {
    try {
      const incidents = await this.getIncidents();
      return incidents.filter((incident) => incident.namespace === namespace);
    } catch (error) {
      console.error('Failed to fetch incidents by namespace:', error);
      throw error;
    }
  }

  // Get incidents by severity
  async getIncidentsBySeverity(severity: string): Promise<Incident[]> {
    try {
      const incidents = await this.getIncidents();
      return incidents.filter((incident) => incident.severity === severity);
    } catch (error) {
      console.error('Failed to fetch incidents by severity:', error);
      throw error;
    }
  }

  // Calculate incident statistics
  async getIncidentStats(): Promise<IncidentStats> {
    try {
      const incidents = await this.getIncidents();

      return {
        total: incidents.length,
        critical: incidents.filter((i) => i.severity === 'critical').length,
        high: incidents.filter((i) => i.severity === 'high').length,
        medium: incidents.filter((i) => i.severity === 'medium').length,
        low: incidents.filter((i) => i.severity === 'low').length,
        resolved: incidents.filter((i) => i.status === 'resolved').length,
        analyzing: incidents.filter((i) => i.status === 'analyzing').length,
      };
    } catch (error) {
      console.error('Failed to calculate stats:', error);
      throw error;
    }
  }

  // Get metrics
  async getMetrics(): Promise<string> {
    try {
      const response = await this.client.get('/metrics');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
      throw error;
    }
  }

  // Clear cache
  async clearCache(): Promise<any> {
    try {
      const response = await this.client.post('/clear-cache');
      return response.data;
    } catch (error) {
      console.error('Failed to clear cache:', error);
      throw error;
    }
  }

  // Get memory database
  async getMemoryDB(): Promise<any> {
    try {
      const response = await this.client.get('/memory');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch memory DB:', error);
      throw error;
    }
  }

  // Get unique namespaces
  async getNamespaces(): Promise<string[]> {
    try {
      const incidents = await this.getIncidents();
      const namespaces = Array.from(new Set(incidents.map((i) => i.namespace)));
      return namespaces.sort();
    } catch (error) {
      console.error('Failed to fetch namespaces:', error);
      throw error;
    }
  }

  // Get namespace statistics
  async getNamespaceStats(): Promise<any[]> {
    try {
      const incidents = await this.getIncidents();

      const namespaceMap = new Map<
        string,
        { incidents: Incident[]; pod_names: Set<string> }
      >();

      incidents.forEach((incident) => {
        if (!namespaceMap.has(incident.namespace)) {
          namespaceMap.set(incident.namespace, {
            incidents: [],
            pod_names: new Set(),
          });
        }

        const ns = namespaceMap.get(incident.namespace)!;
        ns.incidents.push(incident);
        ns.pod_names.add(incident.pod);
      });

      return Array.from(namespaceMap.entries()).map(([namespace, data]) => ({
        namespace,
        pod_count: data.pod_names.size,
        incident_count: data.incidents.length,
        severity: data.incidents[0]?.severity || 'info',
        last_incident: data.incidents[0]?.timestamp || 'N/A',
      }));
    } catch (error) {
      console.error('Failed to fetch namespace stats:', error);
      throw error;
    }
  }
}

export default new APIClient();