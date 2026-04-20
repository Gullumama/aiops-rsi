"""
Metrics Collector - Collect Kubernetes metrics for pods and nodes
"""

import logging
from kubernetes import client
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MetricsCollector:
    """Collect Kubernetes metrics for pods and nodes"""
    
    @staticmethod
    def get_pod_metrics(custom_api: client.CustomObjectsApi, pod) -> Dict[str, Any]:
        """Get resource metrics for a pod"""
        try:
            metric = custom_api.get_namespaced_custom_object(
                group="metrics.k8s.io",
                version="v1beta1",
                namespace=pod.metadata.namespace,
                plural="pods",
                name=pod.metadata.name
            )
            
            metrics = {
                "timestamp": metric.get("timestamp"),
                "containers": []
            }
            
            for container in metric.get("containers", []):
                cpu_str = container.get("usage", {}).get("cpu", "0")
                memory_str = container.get("usage", {}).get("memory", "0")
                
                metrics["containers"].append({
                    "name": container.get("name"),
                    "cpu": MetricsCollector._parse_resource(cpu_str, "cpu"),
                    "memory": MetricsCollector._parse_resource(memory_str, "memory")
                })
            
            logger.debug(f"✓ Fetched metrics for pod {pod.metadata.name}")
            return metrics
        
        except Exception as e:
            logger.debug(f"Could not fetch metrics: {e}")
            return {}
    
    @staticmethod
    def get_node_metrics(custom_api: client.CustomObjectsApi, node_name: str) -> Dict[str, Any]:
        """Get resource metrics for a node"""
        try:
            metric = custom_api.get_cluster_custom_object(
                group="metrics.k8s.io",
                version="v1beta1",
                plural="nodes",
                name=node_name
            )
            
            cpu_str = metric.get("usage", {}).get("cpu", "0")
            memory_str = metric.get("usage", {}).get("memory", "0")
            
            return {
                "timestamp": metric.get("timestamp"),
                "cpu": MetricsCollector._parse_resource(cpu_str, "cpu"),
                "memory": MetricsCollector._parse_resource(memory_str, "memory")
            }
        
        except Exception as e:
            logger.debug(f"Could not fetch node metrics: {e}")
            return {}
    
    @staticmethod
    def _parse_resource(value: str, resource_type: str) -> float:
        """Parse resource value (CPU in millicores, Memory in bytes)"""
        if not value:
            return 0.0
        
        value = value.strip()
        
        if resource_type == "cpu":
            # CPU can be: "100m" (millicores), "1" (cores), "1.5"
            if value.endswith("m"):
                return float(value[:-1])
            else:
                return float(value) * 1000
        
        elif resource_type == "memory":
            # Memory can be: "128Mi", "1Gi", "512M", etc.
            multipliers = {
                "Ki": 1024,
                "Mi": 1024 ** 2,
                "Gi": 1024 ** 3,
                "Ti": 1024 ** 4,
                "K": 1000,
                "M": 1000 ** 2,
                "G": 1000 ** 3,
                "T": 1000 ** 4
            }
            
            for suffix, multiplier in multipliers.items():
                if value.endswith(suffix):
                    return float(value[:-len(suffix)]) * multiplier
            
            try:
                return float(value)
            except:
                return 0.0
        
        return 0.0
    
    @staticmethod
    def get_pod_resource_limits(pod) -> Dict[str, Any]:
        """Extract resource limits from pod spec"""
        limits = {
            "containers": []
        }
        
        try:
            if pod.spec.containers:
                for container in pod.spec.containers:
                    container_limits = {}
                    
                    if container.resources and container.resources.limits:
                        if container.resources.limits.get("cpu"):
                            container_limits["cpu_limit"] = MetricsCollector._parse_resource(
                                container.resources.limits["cpu"], "cpu"
                            )
                        if container.resources.limits.get("memory"):
                            container_limits["memory_limit"] = MetricsCollector._parse_resource(
                                container.resources.limits["memory"], "memory"
                            )
                    
                    if container.resources and container.resources.requests:
                        if container.resources.requests.get("cpu"):
                            container_limits["cpu_request"] = MetricsCollector._parse_resource(
                                container.resources.requests["cpu"], "cpu"
                            )
                        if container.resources.requests.get("memory"):
                            container_limits["memory_request"] = MetricsCollector._parse_resource(
                                container.resources.requests["memory"], "memory"
                            )
                    
                    limits["containers"].append({
                        "name": container.name,
                        **container_limits
                    })
        
        except Exception as e:
            logger.debug(f"Error extracting resource limits: {e}")
        
        return limits
    
    @staticmethod
    def compare_usage_to_limits(pod_metrics: Dict, pod_limits: Dict) -> Dict[str, Any]:
        """Compare actual usage to limits"""
        comparison = {
            "containers": []
        }
        
        try:
            for i, container_metric in enumerate(pod_metrics.get("containers", [])):
                if i < len(pod_limits.get("containers", [])):
                    container_limit = pod_limits["containers"][i]
                    
                    result = {"name": container_metric["name"]}
                    
                    # CPU comparison
                    if "cpu_limit" in container_limit:
                        cpu_percent = (
                            container_metric["cpu"] / container_limit["cpu_limit"] * 100
                        ) if container_limit["cpu_limit"] > 0 else 0
                        result["cpu_percent"] = cpu_percent
                        result["cpu_warning"] = cpu_percent > 80
                    
                    # Memory comparison
                    if "memory_limit" in container_limit:
                        memory_percent = (
                            container_metric["memory"] / container_limit["memory_limit"] * 100
                        ) if container_limit["memory_limit"] > 0 else 0
                        result["memory_percent"] = memory_percent
                        result["memory_warning"] = memory_percent > 80
                    
                    comparison["containers"].append(result)
        
        except Exception as e:
            logger.debug(f"Error comparing usage to limits: {e}")
        
        return comparison