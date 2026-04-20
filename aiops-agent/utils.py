"""
Utility functions for AIOps Agent
"""

import logging
import yaml
import os
import traceback
from typing import Dict, Any
from datetime import datetime, timezone

# ================= LOGGING SETUP =================
def setup_logging(level=logging.INFO):
    """Configure logging for the application"""
    
    log_format = '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
    
    # Create logs directory if it doesn't exist
    os.makedirs('/tmp/aiops', exist_ok=True)
    
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('/tmp/aiops/aiops-agent.log')
        ]
    )
    
    # Suppress verbose logs from libraries
    logging.getLogger('kubernetes').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# ================= CONFIG LOADING =================
def load_config() -> Dict[str, Any]:
    """Load configuration from environment or config file"""
    
    config = {
        # Ollama configuration
        "ollama_url": os.getenv("OLLAMA_URL", "http://ollama.default:11434"),
        "ollama_model": os.getenv("OLLAMA_MODEL", "llama3:8b-instruct-q4_0"),
        
        # Loki configuration
        "loki_url": os.getenv("LOKI_URL", "http://loki.monitoring:3100"),
        
        # Prometheus configuration
        "prometheus_url": os.getenv("PROMETHEUS_URL", "http://prometheus.monitoring:9090"),
        
        # Remediation settings
        "enable_auto_remediation": os.getenv("ENABLE_AUTO_REMEDIATION", "true").lower() == "true",
        "require_approval": os.getenv("REQUIRE_APPROVAL", "false").lower() == "true",
        
        # Monitoring settings
        "enable_metrics": os.getenv("ENABLE_METRICS", "true").lower() == "true",
        
        # Incident storage
        "store_file": os.getenv("STORE_FILE", "/tmp/aiops/incidents.json"),
        "max_stored_incidents": int(os.getenv("MAX_INCIDENTS", "1000")),
        "max_memory_db": int(os.getenv("MAX_MEMORY_DB", "500")),
        
        # Logging
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        
        # Notification settings
        "slack_webhook": os.getenv("SLACK_WEBHOOK", ""),
        "email_alerts": os.getenv("EMAIL_ALERTS", ""),
        
        # Cluster info
        "cluster_name": os.getenv("CLUSTER_NAME", "default-cluster"),
    }
    
    # Try to load from config file if exists
    config_file = os.getenv("CONFIG_FILE", "/etc/aiops/config.yaml")
    if os.path.exists(config_file):
        try:
            with open(config_file) as f:
                file_config = yaml.safe_load(f) or {}
                config.update(file_config)
                logger.info(f"✓ Loaded config from {config_file}")
        except Exception as e:
            logger.warning(f"⚠ Failed to load config file: {e}")
    
    logger.info("=" * 50)
    logger.info("Configuration loaded:")
    logger.info("=" * 50)
    for key, value in config.items():
        # Don't log sensitive values
        if "password" not in key.lower() and "token" not in key.lower() and "key" not in key.lower() and "webhook" not in key.lower():
            logger.info(f"  {key}: {value}")
    
    return config

# ================= NOTIFICATION HELPERS =================
def send_slack_notification(webhook_url: str, message: str, severity: str = "info") -> bool:
    """Send notification to Slack"""
    
    if not webhook_url:
        return False
    
    import requests
    
    color_map = {
        "critical": "#FF0000",
        "high": "#FFA500",
        "medium": "#FFFF00",
        "low": "#00FF00",
        "info": "#0000FF"
    }
    
    payload = {
        "attachments": [
            {
                "color": color_map.get(severity, "#0000FF"),
                "title": f"🚨 AIOps Alert - {severity.upper()}",
                "text": message,
                "footer": "AIOps Agent",
                "ts": int(__import__('time').time())
            }
        ]
    }
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Failed to send Slack notification: {e}")
        return False

def send_email_alert(email_addresses: str, subject: str, message: str) -> bool:
    """Send email alert"""
    
    if not email_addresses:
        return False
    
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    try:
        smtp_host = os.getenv("SMTP_HOST", "localhost")
        smtp_port = int(os.getenv("SMTP_PORT", "25"))
        
        server = smtplib.SMTP(smtp_host, smtp_port)
        
        msg = MIMEMultipart()
        msg["From"] = os.getenv("SMTP_FROM", "aiops@localhost")
        msg["To"] = email_addresses
        msg["Subject"] = subject
        
        msg.attach(MIMEText(message, "html"))
        
        server.send_message(msg)
        server.quit()
        
        logger.info(f"✓ Email sent to {email_addresses}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False

# ================= KUBERNETES HELPERS =================
def get_cluster_info() -> Dict[str, Any]:
    """Get cluster information"""
    from kubernetes import client, config
    
    try:
        try:
            config.load_incluster_config()
            logger.info("✓ Using in-cluster config")
        except:
            config.load_kube_config()
            logger.info("✓ Using kubeconfig")
        
        v1 = client.CoreV1Api()
        
        nodes = v1.list_node()
        namespaces = v1.list_namespace()
        
        info = {
            "node_count": len(nodes.items),
            "namespace_count": len(namespaces.items),
        }
        
        logger.info(f"✓ Cluster info: {info['node_count']} nodes, {info['namespace_count']} namespaces")
        return info
    
    except Exception as e:
        logger.error(f"Failed to get cluster info: {e}")
        return {}

# ================= TIME HELPERS =================
def get_time_ago(timestamp_str: str) -> str:
    """Convert timestamp to relative time string"""
    
    try:
        if isinstance(timestamp_str, str):
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            timestamp = timestamp_str
        
        now = datetime.now(timezone.utc)
        diff = now - timestamp
        
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return f"{int(seconds)}s ago"
        elif seconds < 3600:
            return f"{int(seconds / 60)}m ago"
        elif seconds < 86400:
            return f"{int(seconds / 3600)}h ago"
        else:
            return f"{int(seconds / 86400)}d ago"
    except Exception as e:
        logger.debug(f"Time conversion error: {e}")
        return "unknown"

# ================= VALIDATION HELPERS =================
def validate_pod_safety(pod) -> bool:
    """Check if pod is safe to remediate"""
    
    unsafe_namespaces = ["kube-system", "kube-public", "kube-node-lease", "kube-apiserver"]
    
    if pod.metadata.namespace in unsafe_namespaces:
        logger.warning(f"⚠ Pod {pod.metadata.name} is in system namespace, skipping remediation")
        return False
    
    # Check if pod has critical annotation
    if pod.metadata.annotations:
        if pod.metadata.annotations.get("aiops.io/no-remediate") == "true":
            logger.info(f"ℹ Pod {pod.metadata.name} has no-remediate annotation")
            return False
    
    return True

# ================= PARSING HELPERS =================
def extract_container_from_logs(logs: str) -> str:
    """Try to extract container name from logs"""
    import re
    
    patterns = [
        r"container\s*=\s*([a-zA-Z0-9\-]+)",
        r"container\s*:\s*([a-zA-Z0-9\-]+)",
        r"\[([a-zA-Z0-9\-]+)\]\s*"
    ]
    """
Utility functions for AIOps Agent
"""

import logging
import yaml
import os
import traceback
from typing import Dict, Any
from datetime import datetime, timezone

# ================= LOGGING SETUP =================
def setup_logging(level=logging.INFO):
    """Configure logging for the application"""
    
    log_format = '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
    
    # Create logs directory if it doesn't exist
    os.makedirs('/tmp/aiops', exist_ok=True)
    
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('/tmp/aiops/aiops-agent.log')
        ]
    )
    
    # Suppress verbose logs from libraries
    logging.getLogger('kubernetes').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# ================= CONFIG LOADING =================
def load_config() -> Dict[str, Any]:
    """Load configuration from environment or config file"""
    
    config = {
        # Ollama configuration
        "ollama_url": os.getenv("OLLAMA_URL", "http://ollama.default:11434"),
        "ollama_model": os.getenv("OLLAMA_MODEL", "llama3:8b-instruct-q4_0"),
        
        # Loki configuration
        "loki_url": os.getenv("LOKI_URL", "http://loki.monitoring:3100"),
        
        # Prometheus configuration
        "prometheus_url": os.getenv("PROMETHEUS_URL", "http://prometheus.monitoring:9090"),
        
        # Remediation settings
        "enable_auto_remediation": os.getenv("ENABLE_AUTO_REMEDIATION", "true").lower() == "true",
        "require_approval": os.getenv("REQUIRE_APPROVAL", "false").lower() == "true",
        
        # Monitoring settings
        "enable_metrics": os.getenv("ENABLE_METRICS", "true").lower() == "true",
        
        # Incident storage
        "store_file": os.getenv("STORE_FILE", "/tmp/aiops/incidents.json"),
        "max_stored_incidents": int(os.getenv("MAX_INCIDENTS", "1000")),
        "max_memory_db": int(os.getenv("MAX_MEMORY_DB", "500")),
        
        # Logging
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        
        # Notification settings
        "slack_webhook": os.getenv("SLACK_WEBHOOK", ""),
        "email_alerts": os.getenv("EMAIL_ALERTS", ""),
        
        # Cluster info
        "cluster_name": os.getenv("CLUSTER_NAME", "default-cluster"),
    }
    
    # Try to load from config file if exists
    config_file = os.getenv("CONFIG_FILE", "/etc/aiops/config.yaml")
    if os.path.exists(config_file):
        try:
            with open(config_file) as f:
                file_config = yaml.safe_load(f) or {}
                config.update(file_config)
                logger.info(f"✓ Loaded config from {config_file}")
        except Exception as e:
            logger.warning(f"⚠ Failed to load config file: {e}")
    
    logger.info("=" * 50)
    logger.info("Configuration loaded:")
    logger.info("=" * 50)
    for key, value in config.items():
        # Don't log sensitive values
        if "password" not in key.lower() and "token" not in key.lower() and "key" not in key.lower() and "webhook" not in key.lower():
            logger.info(f"  {key}: {value}")
    
    return config

# ================= NOTIFICATION HELPERS =================
def send_slack_notification(webhook_url: str, message: str, severity: str = "info") -> bool:
    """Send notification to Slack"""
    
    if not webhook_url:
        return False
    
    import requests
    
    color_map = {
        "critical": "#FF0000",
        "high": "#FFA500",
        "medium": "#FFFF00",
        "low": "#00FF00",
        "info": "#0000FF"
    }
    
    payload = {
        "attachments": [
            {
                "color": color_map.get(severity, "#0000FF"),
                "title": f"🚨 AIOps Alert - {severity.upper()}",
                "text": message,
                "footer": "AIOps Agent",
                "ts": int(__import__('time').time())
            }
        ]
    }
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Failed to send Slack notification: {e}")
        return False

def send_email_alert(email_addresses: str, subject: str, message: str) -> bool:
    """Send email alert"""
    
    if not email_addresses:
        return False
    
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    try:
        smtp_host = os.getenv("SMTP_HOST", "localhost")
        smtp_port = int(os.getenv("SMTP_PORT", "25"))
        
        server = smtplib.SMTP(smtp_host, smtp_port)
        
        msg = MIMEMultipart()
        msg["From"] = os.getenv("SMTP_FROM", "aiops@localhost")
        msg["To"] = email_addresses
        msg["Subject"] = subject
        
        msg.attach(MIMEText(message, "html"))
        
        server.send_message(msg)
        server.quit()
        
        logger.info(f"✓ Email sent to {email_addresses}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False

# ================= KUBERNETES HELPERS =================
def get_cluster_info() -> Dict[str, Any]:
    """Get cluster information"""
    from kubernetes import client, config
    
    try:
        try:
            config.load_incluster_config()
            logger.info("✓ Using in-cluster config")
        except:
            config.load_kube_config()
            logger.info("✓ Using kubeconfig")
        
        v1 = client.CoreV1Api()
        
        nodes = v1.list_node()
        namespaces = v1.list_namespace()
        
        info = {
            "node_count": len(nodes.items),
            "namespace_count": len(namespaces.items),
        }
        
        logger.info(f"✓ Cluster info: {info['node_count']} nodes, {info['namespace_count']} namespaces")
        return info
    
    except Exception as e:
        logger.error(f"Failed to get cluster info: {e}")
        return {}

# ================= TIME HELPERS =================
def get_time_ago(timestamp_str: str) -> str:
    """Convert timestamp to relative time string"""
    
    try:
        if isinstance(timestamp_str, str):
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            timestamp = timestamp_str
        
        now = datetime.now(timezone.utc)
        diff = now - timestamp
        
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return f"{int(seconds)}s ago"
        elif seconds < 3600:
            return f"{int(seconds / 60)}m ago"
        elif seconds < 86400:
            return f"{int(seconds / 3600)}h ago"
        else:
            return f"{int(seconds / 86400)}d ago"
    except Exception as e:
        logger.debug(f"Time conversion error: {e}")
        return "unknown"

# ================= VALIDATION HELPERS =================
def validate_pod_safety(pod) -> bool:
    """Check if pod is safe to remediate"""
    
    unsafe_namespaces = ["kube-system", "kube-public", "kube-node-lease", "kube-apiserver"]
    
    if pod.metadata.namespace in unsafe_namespaces:
        logger.warning(f"⚠ Pod {pod.metadata.name} is in system namespace, skipping remediation")
        return False
    
    # Check if pod has critical annotation
    if pod.metadata.annotations:
        if pod.metadata.annotations.get("aiops.io/no-remediate") == "true":
            logger.info(f"ℹ Pod {pod.metadata.name} has no-remediate annotation")
            return False
    
    return True

# ================= PARSING HELPERS =================
def extract_container_from_logs(logs: str) -> str:
    """Try to extract container name from logs"""
    import re
    
    patterns = [
        r"container\s*=\s*([a-zA-Z0-9\-]+)",
        r"container\s*:\s*([a-zA-Z0-9\-]+)",
        r"\[([a-zA-Z0-9\-]+)\]\s*"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, logs, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return "unknown"

def parse_error_code(logs: str) -> str:
    """Extract error code from logs"""
    import re
    
    patterns = [
        r"error\s*code\s*:\s*(\d+)",
        r"exit\s*code\s*:\s*(\d+)",
        r"code\s*=\s*(\d+)"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, logs, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return "unknown"

# ================= ERROR HANDLING =================
def format_exception(e: Exception) -> str:
    """Format exception with traceback"""
    return f"{str(e)}\n{traceback.format_exc()}"
    for pattern in patterns:
        match = re.search(pattern, logs, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return "unknown"

def parse_error_code(logs: str) -> str:
    """Extract error code from logs"""
    import re
    
    patterns = [
        r"error\s*code\s*:\s*(\d+)",
        r"exit\s*code\s*:\s*(\d+)",
        r"code\s*=\s*(\d+)"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, logs, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return "unknown"

# ================= ERROR HANDLING =================
def format_exception(e: Exception) -> str:
    """Format exception with traceback"""
    return f"{str(e)}\n{traceback.format_exc()}"