"""
K8sGPT Integration Module
Integrates K8sGPT analysis results with AIOps Agent
"""

import logging
from typing import Dict, Any, Optional
from k8sgpt_client import K8sGPTClient

logger = logging.getLogger(__name__)

class K8sGPTIntegration:
    """Integrate K8sGPT analysis with AIOps Agent"""
    
    def __init__(self, k8sgpt_url: str = "http://k8sgpt.aiops:8080"):
        """Initialize K8sGPT integration"""
        self.client = K8sGPTClient(base_url=k8sgpt_url)
    
    def enrich_incident(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich incident with K8sGPT analysis
        
        Args:
            incident: Incident data from AIOps Agent
            
        Returns:
            Enhanced incident data
        """
        try:
            pod_name = incident.get("pod")
            namespace = incident.get("namespace")
            
            # Get K8sGPT analysis
            analysis = self.client.analyze_pod(pod_name, namespace)
            
            if analysis and "error" not in analysis:
                incident["k8sgpt_analysis"] = analysis
                incident["k8sgpt_status"] = "success"
                logger.info(f"✓ K8sGPT enrichment successful for {namespace}/{pod_name}")
            else:
                logger.warning(f"⚠️  K8sGPT analysis failed or empty")
                incident["k8sgpt_status"] = "failed"
        
        except Exception as e:
            logger.error(f"✗ K8sGPT enrichment error: {e}")
            incident["k8sgpt_status"] = "error"
            incident["k8sgpt_error"] = str(e)
        
        return incident
    
    def analyze_resource(self, resource_type: str, name: str, namespace: str) -> Dict[str, Any]:
        """
        Analyze a specific Kubernetes resource
        
        Args:
            resource_type: Type of resource (Pod, Deployment, etc.)
            name: Resource name
            namespace: Resource namespace
            
        Returns:
            Analysis results
        """
        try:
            # Map resource type to K8sGPT filter
            filter_map = {
                "pod": "Pod",
                "deployment": "Deployment",
                "statefulset": "StatefulSet",
                "daemonset": "DaemonSet",
                "job": "Job",
                "cronjob": "CronJob",
                "service": "Service",
                "ingress": "Ingress",
                "node": "Node",
                "pvc": "PersistentVolumeClaim",
                "pv": "PersistentVolume",
            }
            
            filter_name = filter_map.get(resource_type.lower(), resource_type)
            
            # Get analysis
            analysis = self.client.analyze(filters=[filter_name])
            
            logger.info(f"✓ Analyzed {resource_type}: {namespace}/{name}")
            return analysis
        
        except Exception as e:
            logger.error(f"✗ Resource analysis error: {e}")
            return {"error": str(e)}
    
    def get_cluster_health(self) -> Dict[str, Any]:
        """
        Get overall cluster health analysis
        
        Returns:
            Cluster health information
        """
        try:
            # Analyze all resources
            analysis = self.client.analyze()
            
            # Extract health metrics
            health = {
                "status": "healthy" if self.client.get_health() else "unhealthy",
                "timestamp": __import__('datetime').datetime.now().isoformat(),
                "analysis": analysis
            }
            
            logger.info("✓ Cluster health check complete")
            return health
        
        except Exception as e:
            logger.error(f"✗ Cluster health check error: {e}")
            return {"status": "error", "error": str(e)}
    
    def close(self):
        """Close the client"""
        self.client.close()


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    integration = K8sGPTIntegration()
    
    # Get cluster health
    health = integration.get_cluster_health()
    print(f"Cluster Health: {health['status']}")
    
    # Analyze a pod
    analysis = integration.analyze_resource("pod", "example-pod", "default")
    print(f"Pod Analysis: {analysis}")
    
    integration.close()