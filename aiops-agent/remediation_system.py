"""
Remediation System - Safe remediation actions for Kubernetes failures
"""

import logging
from kubernetes import client
from typing import Dict, Any

logger = logging.getLogger(__name__)

class RemediationSystem:
    """Safe remediation actions for Kubernetes failures"""
    
    def __init__(self, v1: client.CoreV1Api, config: Dict[str, Any]):
        self.v1 = v1
        self.config = config
        self.apps_api = client.AppsV1Api()
        self.batch_api = client.BatchV1Api()
    
    def execute(self, pod, rule: str, logs: str) -> Dict[str, Any]:
        """Execute remediation action for the given rule"""
        
        pod_name = pod.metadata.name
        namespace = pod.metadata.namespace
        
        try:
            # Route to appropriate handler
            handler_name = f"_handle_{rule.lower().replace(' ', '_').replace('-', '_')}"
            
            if hasattr(self, handler_name):
                handler = getattr(self, handler_name)
                result = handler(pod, logs)
                logger.info(f"✓ Remediation action executed: {result.get('action')}")
                return result
            else:
                return {
                    "status": "pending",
                    "action": "manual_review",
                    "message": f"No automatic remediation for {rule}. Requires manual review."
                }
        
        except Exception as e:
            logger.error(f"Remediation failed: {e}")
            return {
                "status": "failed",
                "action": "error",
                "message": str(e)
            }
    
    # ================= RESTART HANDLERS =================
    
    def _handle_crashloopbackoff(self, pod, logs: str):
        """Handle CrashLoopBackOff"""
        pod_name = pod.metadata.name
        namespace = pod.metadata.namespace
        
        owner_ref = self._get_owner_reference(pod)
        
        if owner_ref:
            workload_type = owner_ref.get("kind", "").lower()
            workload_name = owner_ref.get("name")
            
            if workload_type == "deployment":
                return self._restart_deployment(workload_name, namespace)
            elif workload_type == "statefulset":
                return self._restart_statefulset(workload_name, namespace)
            elif workload_type == "daemonset":
                return self._restart_daemonset(workload_name, namespace)
        
        return self._restart_pod(pod_name, namespace)
    
    def _handle_imagepullbackoff(self, pod, logs: str):
        """Handle ImagePullBackOff"""
        return {
            "status": "pending",
            "action": "image_pull_failed",
            "message": "Image pull failed. Verify image exists and credentials are valid."
        }
    
    def _handle_imageinspecterror(self, pod, logs: str):
        """Handle ImageInspectError"""
        return {
            "status": "pending",
            "action": "image_error",
            "message": "Image inspection failed. Verify image URI is correct."
        }
    
    # ================= RESOURCE HANDLERS =================
    
    def _handle_oomkilled(self, pod, logs: str):
        """Handle OOMKilled"""
        return {
            "status": "pending",
            "action": "increase_memory",
            "message": "Pod OOM killed. Memory limits should be increased."
        }
    
    def _handle_cpu_throttling(self, pod, logs: str):
        """Handle CPU throttling"""
        return {
            "status": "pending",
            "action": "increase_cpu",
            "message": "Pod CPU is being throttled. Increase CPU limits."
        }
    
    def _handle_insufficient_resources(self, pod, logs: str):
        """Handle insufficient resources"""
        return {
            "status": "pending",
            "action": "cluster_scaling",
            "message": "Cluster has insufficient resources."
        }
    
    # ================= HEALTH CHECK HANDLERS =================
    
    def _handle_readinessprobe_failed(self, pod, logs: str):
        """Handle readiness probe failure"""
        return {
            "status": "pending",
            "action": "health_check_failed",
            "message": "Pod failed readiness probe."
        }
    
    def _handle_livenessprobe_failed(self, pod, logs: str):
        """Handle liveness probe failure"""
        return {
            "status": "pending",
            "action": "liveness_restart",
            "message": "Pod will be restarted due to liveness probe failure."
        }
    
    def _handle_startupprobe_failed(self, pod, logs: str):
        """Handle startup probe failure"""
        return {
            "status": "pending",
            "action": "startup_failed",
            "message": "Pod failed to startup."
        }
    
    # ================= NETWORK HANDLERS =================
    
    def _handle_dns_failure(self, pod, logs: str):
        """Handle DNS failures"""
        return {
            "status": "pending",
            "action": "dns_resolution",
            "message": "Pod cannot resolve DNS names."
        }
    
    def _handle_connection_refused(self, pod, logs: str):
        """Handle connection refused"""
        return {
            "status": "pending",
            "action": "connection_error",
            "message": "Connection was refused."
        }
    
    def _handle_connection_timeout(self, pod, logs: str):
        """Handle connection timeout"""
        return {
            "status": "pending",
            "action": "timeout",
            "message": "Connection timed out."
        }
    
    # ================= STORAGE HANDLERS =================
    
    def _handle_disk_full(self, pod, logs: str):
        """Handle disk full"""
        return {
            "status": "pending",
            "action": "disk_space",
            "message": "Disk is full. Pod cannot write data."
        }
    
    def _handle_pvc_mount_failed(self, pod, logs: str):
        """Handle PVC mount failure"""
        return {
            "status": "pending",
            "action": "pvc_mount",
            "message": "PVC could not be mounted."
        }
    
    # ================= CONFIG HANDLERS =================
    
    def _handle_createcontainerconfigerror(self, pod, logs: str):
        """Handle container config error"""
        return {
            "status": "pending",
            "action": "config_error",
            "message": "Container configuration is invalid."
        }
    
    def _handle_configmap_not_found(self, pod, logs: str):
        """Handle missing ConfigMap"""
        return {
            "status": "pending",
            "action": "missing_config",
            "message": "ConfigMap referenced by pod not found."
        }
    
    def _handle_secret_not_found(self, pod, logs: str):
        """Handle missing Secret"""
        return {
            "status": "pending",
            "action": "missing_secret",
            "message": "Secret referenced by pod not found."
        }
    
    # ================= PERMISSION HANDLERS =================
    
    def _handle_permission_denied(self, pod, logs: str):
        """Handle permission error"""
        return {
            "status": "pending",
            "action": "permission_error",
            "message": "Permission denied."
        }
    
    def _handle_rbac_permission_denied(self, pod, logs: str):
        """Handle RBAC permission error"""
        return {
            "status": "pending",
            "action": "rbac_denied",
            "message": "RBAC permission denied."
        }
    
    # ================= EVICTION HANDLERS =================
    
    def _handle_pod_evicted(self, pod, logs: str):
        """Handle pod eviction"""
        return {
            "status": "pending",
            "action": "pod_evicted",
            "message": "Pod was evicted from node."
        }
    
    # ================= HELPER METHODS =================
    
    def _get_owner_reference(self, pod):
        """Get parent workload reference from pod"""
        if pod.metadata.owner_references:
            for ref in pod.metadata.owner_references:
                return {
                    "kind": ref.kind,
                    "name": ref.name,
                    "uid": ref.uid
                }
        return None
    
    def _restart_pod(self, pod_name: str, namespace: str):
        """Restart pod by deleting it"""
        try:
            self.v1.delete_namespaced_pod(
                pod_name,
                namespace,
                grace_period_seconds=30
            )
            return {
                "status": "success",
                "action": "pod_restart",
                "message": f"Pod {pod_name} restarted."
            }
        except Exception as e:
            return {
                "status": "failed",
                "action": "pod_restart",
                "message": f"Failed to restart pod: {str(e)}"
            }
    
    def _restart_deployment(self, deployment_name: str, namespace: str):
        """Restart deployment"""
        try:
            self.apps_api.patch_namespaced_deployment(
                deployment_name,
                namespace,
                {
                    "spec": {
                        "template": {
                            "metadata": {
                                "annotations": {
                                    "kubectl.kubernetes.io/restartedAt": __import__('datetime').datetime.now(
                                        __import__('datetime').timezone.utc
                                    ).isoformat()
                                }
                            }
                        }
                    }
                }
            )
            return {
                "status": "success",
                "action": "deployment_restart",
                "message": f"Deployment {deployment_name} rolling restart initiated."
            }
        except Exception as e:
            return {
                "status": "failed",
                "action": "deployment_restart",
                "message": f"Failed: {str(e)}"
            }
    
    def _restart_statefulset(self, statefulset_name: str, namespace: str):
        """Restart StatefulSet"""
        try:
            self.apps_api.patch_namespaced_stateful_set(
                statefulset_name,
                namespace,
                {
                    "spec": {
                        "template": {
                            "metadata": {
                                "annotations": {
                                    "kubectl.kubernetes.io/restartedAt": __import__('datetime').datetime.now(
                                        __import__('datetime').timezone.utc
                                    ).isoformat()
                                }
                            }
                        }
                    }
                }
            )
            return {
                "status": "success",
                "action": "statefulset_restart",
                "message": f"StatefulSet {statefulset_name} rolling restart initiated."
            }
        except Exception as e:
            return {
                "status": "failed",
                "action": "statefulset_restart",
                "message": f"Failed: {str(e)}"
            }
    
    def _restart_daemonset(self, daemonset_name: str, namespace: str):
        """Restart DaemonSet"""
        try:
            self.apps_api.patch_namespaced_daemon_set(
                daemonset_name,
                namespace,
                {
                    "spec": {
                        "template": {
                            "metadata": {
                                "annotations": {
                                    "kubectl.kubernetes.io/restartedAt": __import__('datetime').datetime.now(
                                        __import__('datetime').timezone.utc
                                    ).isoformat()
                                }
                            }
                        }
                    }
                }
            )
            return {
                "status": "success",
                "action": "daemonset_restart",
                "message": f"DaemonSet {daemonset_name} rolling restart initiated."
            }
        except Exception as e:
            return {
                "status": "failed",
                "action": "daemonset_restart",
                "message": f"Failed: {str(e)}"
            }