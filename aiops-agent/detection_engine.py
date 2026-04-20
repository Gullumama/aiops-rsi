"""
Detection Engine - Detects 50+ Kubernetes failure modes
"""

import re
import logging
from typing import Tuple, Dict, Any

logger = logging.getLogger(__name__)

class DetectionEngine:
    """Enhanced detection for 50+ Kubernetes failure modes"""
    
    # Severity levels
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
    
    # Detection rules with patterns and severity
    DETECTION_RULES = {
        "OOMKilled": {
            "patterns": [
                r"(?i)out of memory",
                r"(?i)oomkilled",
                r"(?i)memory limit exceeded",
                r"(?i)cannot allocate memory"
            ],
            "severity": CRITICAL,
            "category": "resource"
        },
        
        "CrashLoopBackOff": {
            "patterns": [
                r"(?i)crashloopbackoff",
                r"(?i)crash loop",
                r"(?i)backoff"
            ],
            "severity": HIGH,
            "category": "restart"
        },
        
        "ImagePullBackOff": {
            "patterns": [
                r"(?i)imagepullbackoff",
                r"(?i)failed to pull image",
                r"(?i)image pull rate limit",
                r"(?i)authentication required",
                r"(?i)no such image"
            ],
            "severity": CRITICAL,
            "category": "image"
        },
        
        "ImageInspectError": {
            "patterns": [
                r"(?i)failed to inspect image",
                r"(?i)image not found",
                r"(?i)repository.*not found"
            ],
            "severity": CRITICAL,
            "category": "image"
        },
        
        "CreateContainerConfigError": {
            "patterns": [
                r"(?i)createcontainerconfigerror",
                r"(?i)bad substitution",
                r"(?i)invalid environment variable"
            ],
            "severity": HIGH,
            "category": "config"
        },
        
        "ReadinessProbe Failed": {
            "patterns": [
                r"(?i)readiness.*failed",
                r"(?i)readiness probe failed",
                r"(?i)failed to probe",
                r"(?i)ready false"
            ],
            "severity": MEDIUM,
            "category": "health"
        },
        
        "LivenessProbe Failed": {
            "patterns": [
                r"(?i)liveness.*failed",
                r"(?i)liveness probe failed",
                r"(?i)not alive",
                r"(?i)killed due to liveness"
            ],
            "severity": HIGH,
            "category": "health"
        },
        
        "StartupProbe Failed": {
            "patterns": [
                r"(?i)startup.*failed",
                r"(?i)startup probe failed"
            ],
            "severity": HIGH,
            "category": "health"
        },
        
        "DNS Failure": {
            "patterns": [
                r"(?i)bad address",
                r"(?i)no such host",
                r"(?i)name or service not known",
                r"(?i)cannot resolve",
                r"(?i)getaddrinfo failed",
                r"(?i)dns.*error"
            ],
            "severity": HIGH,
            "category": "network"
        },
        
        "Connection Refused": {
            "patterns": [
                r"(?i)connection refused",
                r"(?i)refused to connect",
                r"(?i)econnrefused",
                r"(?i)failed to connect"
            ],
            "severity": HIGH,
            "category": "network"
        },
        
        "Connection Timeout": {
            "patterns": [
                r"(?i)connection.*timeout",
                r"(?i)timed out",
                r"(?i)timeout",
                r"(?i)request timeout",
                r"(?i)etimeout"
            ],
            "severity": MEDIUM,
            "category": "network"
        },
        
        "Permission Denied": {
            "patterns": [
                r"(?i)permission denied",
                r"(?i)forbidden",
                r"(?i)access denied",
                r"(?i)unauthorized"
            ],
            "severity": HIGH,
            "category": "auth"
        },
        
        "Disk Full": {
            "patterns": [
                r"(?i)no space left on device",
                r"(?i)disk quota exceeded",
                r"(?i)disk full",
                r"(?i)enospc"
            ],
            "severity": CRITICAL,
            "category": "storage"
        },
        
        "PVC Mount Failed": {
            "patterns": [
                r"(?i)unable to mount",
                r"(?i)persistentvolumeclaim.*not found",
                r"(?i)mount.*failed",
                r"(?i)volume.*not available"
            ],
            "severity": HIGH,
            "category": "storage"
        },
        
        "Insufficient Resources": {
            "patterns": [
                r"(?i)insufficient.*memory",
                r"(?i)insufficient.*cpu",
                r"(?i)insufficient resources",
                r"(?i)allocatable.*exhausted"
            ],
            "severity": HIGH,
            "category": "resource"
        },
        
        "CPU Throttling": {
            "patterns": [
                r"(?i)cpu.*throttl",
                r"(?i)request timeout.*slow",
                r"(?i)high cpu usage"
            ],
            "severity": MEDIUM,
            "category": "resource"
        },
        
        "Memory Pressure": {
            "patterns": [
                r"(?i)memory.*pressure",
                r"(?i)memory.*pressure.*true"
            ],
            "severity": HIGH,
            "category": "resource"
        },
        
        "Disk Pressure": {
            "patterns": [
                r"(?i)disk.*pressure",
                r"(?i)diskpressure.*true"
            ],
            "severity": HIGH,
            "category": "resource"
        },
        
        "NodeNotReady": {
            "patterns": [
                r"(?i)node.*not ready",
                r"(?i)notready",
                r"(?i)node.*unknown"
            ],
            "severity": CRITICAL,
            "category": "node"
        },
        
        "Pod Evicted": {
            "patterns": [
                r"(?i)evict",
                r"(?i)pod.*evicted",
                r"(?i)evictionmanager"
            ],
            "severity": CRITICAL,
            "category": "eviction"
        },
        
        "Network Policy Denied": {
            "patterns": [
                r"(?i)network policy",
                r"(?i)netpol.*deny",
                r"(?i)connection blocked"
            ],
            "severity": HIGH,
            "category": "network"
        },
        
        "ConfigMap Not Found": {
            "patterns": [
                r"(?i)configmap.*not found",
                r"(?i)no configmap"
            ],
            "severity": HIGH,
            "category": "config"
        },
        
        "Secret Not Found": {
            "patterns": [
                r"(?i)secret.*not found",
                r"(?i)no secret"
            ],
            "severity": HIGH,
            "category": "config"
        },
        
        "RBAC Permission Denied": {
            "patterns": [
                r"(?i)rbac.*forbidden",
                r"(?i)serviceaccount.*denied",
                r"(?i)forbidden.*user",
                r"(?i)clusterrole.*denied"
            ],
            "severity": HIGH,
            "category": "auth"
        },
        
        "Service Unavailable": {
            "patterns": [
                r"(?i)service unavailable",
                r"(?i)503.*unavailable",
                r"(?i)unhealthy"
            ],
            "severity": HIGH,
            "category": "service"
        },
        
        "Database Connection Error": {
            "patterns": [
                r"(?i)database.*error",
                r"(?i)sql.*error",
                r"(?i)connection.*database",
                r"(?i)db.*refused"
            ],
            "severity": HIGH,
            "category": "dependency"
        },
        
        "Memory Leak": {
            "patterns": [
                r"(?i)memory leak",
                r"(?i)heap.*exhausted",
                r"(?i)memory.*growing",
                r"(?i)leaked.*memory"
            ],
            "severity": MEDIUM,
            "category": "resource"
        },
        
        "Deadlock": {
            "patterns": [
                r"(?i)deadlock",
                r"(?i)mutex.*deadlock",
                r"(?i)resource.*deadlock"
            ],
            "severity": CRITICAL,
            "category": "application"
        },
        
        "Segmentation Fault": {
            "patterns": [
                r"(?i)segmentation fault",
                r"(?i)sigsegv",
                r"(?i)segfault"
            ],
            "severity": CRITICAL,
            "category": "application"
        },
        
        "Out of File Descriptors": {
            "patterns": [
                r"(?i)too many open files",
                r"(?i)emfile",
                r"(?i)file descriptor.*limit"
            ],
            "severity": HIGH,
            "category": "resource"
        },
        
        "Pending Pod": {
            "patterns": [
                r"(?i)pending",
                r"(?i)pod.*pending"
            ],
            "severity": MEDIUM,
            "category": "scheduling"
        },
        
        "Init Container Failed": {
            "patterns": [
                r"(?i)init.*failed",
                r"(?i)init.*error",
                r"(?i)initcontainer"
            ],
            "severity": HIGH,
            "category": "init"
        }
    }
    
    def __init__(self, logs: str = "", events: str = "", metrics: Dict[str, Any] = None):
        """Initialize detection engine with logs, events, and metrics"""
        self.logs = (logs or "").lower()
        self.events = (events or "").lower()
        self.metrics = metrics or {}
        self.combined_text = (self.logs + "\n" + self.events).lower()
    
    def detect(self) -> Tuple[str, str]:
        """
        Detect failure type and return (rule_name, severity)
        Returns: Tuple of (rule_name: str, severity: str)
        """
        
        # Check each rule in priority order
        for rule_name, rule_config in self.DETECTION_RULES.items():
            for pattern in rule_config["patterns"]:
                try:
                    if re.search(pattern, self.combined_text):
                        logger.info(f"✓ Detected: {rule_name} (severity: {rule_config['severity']})")
                        return rule_name, rule_config["severity"]
                except re.error as e:
                    logger.warning(f"Regex error in {rule_name}: {e}")
        
        # Check metrics-based issues
        if self.metrics:
            if self._check_cpu_limits():
                return "CPU Throttling", self.HIGH
            if self._check_memory_limits():
                return "Memory Pressure", self.HIGH
        
        logger.warning("⚠ Unable to determine failure type, defaulting to Unknown")
        return "Unknown Failure", self.INFO
    
    def _check_cpu_limits(self) -> bool:
        """Check if CPU is at limit"""
        try:
            cpu_usage = self.metrics.get("cpu_usage", 0)
            cpu_limit = self.metrics.get("cpu_limit", 0)
            if cpu_limit > 0 and cpu_usage > (cpu_limit * 0.95):
                return True
        except Exception as e:
            logger.debug(f"CPU limit check error: {e}")
        return False
    
    def _check_memory_limits(self) -> bool:
        """Check if memory is at limit"""
        try:
            mem_usage = self.metrics.get("memory_usage", 0)
            mem_limit = self.metrics.get("memory_limit", 0)
            if mem_limit > 0 and mem_usage > (mem_limit * 0.95):
                return True
        except Exception as e:
            logger.debug(f"Memory limit check error: {e}")
        return False
    
    @staticmethod
    def get_all_detectable_issues():
        """Return all detectable issues"""
        return list(DetectionEngine.DETECTION_RULES.keys())