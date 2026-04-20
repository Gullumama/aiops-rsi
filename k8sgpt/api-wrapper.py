"""
K8sGPT API Wrapper - Integration with AIOps Agent
Provides a Python interface to interact with K8sGPT
"""

import requests
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class K8sGPTClient:
    """Client for interacting with K8sGPT API"""
    
    def __init__(self, base_url: str = "http://k8sgpt.aiops:8080", timeout: int = 30):
        """
        Initialize K8sGPT client
        
        Args:
            base_url: Base URL of K8sGPT API
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
    
    def analyze(self, filters: list = None) -> Dict[str, Any]:
        """
        Analyze Kubernetes cluster
        
        Args:
            filters: List of resource types to analyze
            
        Returns:
            Analysis results
        """
        try:
            params = {}
            if filters:
                params['filters'] = ','.join(filters)
            
            response = self.session.get(
                f"{self.base_url}/analyze",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            logger.info(f"✓ K8sGPT analysis successful")
            return response.json()
        
        except requests.Timeout:
            logger.error(f"✗ K8sGPT request timeout")
            return {"error": "timeout"}
        
        except requests.RequestException as e:
            logger.error(f"✗ K8sGPT request error: {e}")
            return {"error": str(e)}
    
    def analyze_pod(self, pod_name: str, namespace: str) -> Dict[str, Any]:
        """
        Analyze specific pod
        
        Args:
            pod_name: Pod name
            namespace: Pod namespace
            
        Returns:
            Analysis results
        """
        try:
            response = self.session.get(
                f"{self.base_url}/analyze",
                params={
                    'filters': 'Pod',
                    'pod': pod_name,
                    'namespace': namespace
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            
            logger.info(f"✓ Pod analysis successful: {namespace}/{pod_name}")
            return response.json()
        
        except Exception as e:
            logger.error(f"✗ Pod analysis error: {e}")
            return {"error": str(e)}
    
    def analyze_deployment(self, deployment_name: str, namespace: str) -> Dict[str, Any]:
        """
        Analyze specific deployment
        
        Args:
            deployment_name: Deployment name
            namespace: Deployment namespace
            
        Returns:
            Analysis results
        """
        try:
            response = self.session.get(
                f"{self.base_url}/analyze",
                params={
                    'filters': 'Deployment',
                    'deployment': deployment_name,
                    'namespace': namespace
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            
            logger.info(f"✓ Deployment analysis successful: {namespace}/{deployment_name}")
            return response.json()
        
        except Exception as e:
            logger.error(f"✗ Deployment analysis error: {e}")
            return {"error": str(e)}
    
    def get_health(self) -> bool:
        """
        Check K8sGPT health
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=self.timeout
            )
            return response.status_code == 200
        
        except:
            return False
    
    def get_cache_status(self) -> Dict[str, Any]:
        """
        Get cache status
        
        Returns:
            Cache status information
        """
        try:
            response = self.session.get(
                f"{self.base_url}/cache/status",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        
        except Exception as e:
            logger.error(f"✗ Cache status error: {e}")
            return {}
    
    def clear_cache(self) -> bool:
        """
        Clear cache
        
        Returns:
            True if successful
        """
        try:
            response = self.session.post(
                f"{self.base_url}/cache/clear",
                timeout=self.timeout
            )
            response.raise_for_status()
            logger.info("✓ Cache cleared")
            return True
        
        except Exception as e:
            logger.error(f"✗ Cache clear error: {e}")
            return False
    
    def get_version(self) -> Dict[str, Any]:
        """
        Get K8sGPT version info
        
        Returns:
            Version information
        """
        try:
            response = self.session.get(
                f"{self.base_url}/version",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        
        except Exception as e:
            logger.error(f"✗ Version check error: {e}")
            return {}
    
    def close(self):
        """Close the session"""
        self.session.close()


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create client
    client = K8sGPTClient()
    
    # Check health
    if client.get_health():
        print("✓ K8sGPT is healthy")
    else:
        print("✗ K8sGPT is not responding")
    
    # Get version
    version = client.get_version()
    print(f"K8sGPT Version: {version}")
    
    # Analyze cluster
    result = client.analyze(filters=['Pod', 'Deployment'])
    print(f"Analysis result: {json.dumps(result, indent=2)}")
    
    client.close()