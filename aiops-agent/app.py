"""
AIOps Agent - Main Application
AI-powered Kubernetes Root Cause Analysis and Remediation System
"""

import os
import threading
import requests
import json
import time
import logging
import traceback
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException
from kubernetes import client, config, watch
from prometheus_client import Counter, Histogram, generate_latest

from detection_engine import DetectionEngine
from remediation_system import RemediationSystem
from metrics_collector import MetricsCollector
from utils import logger, load_config, setup_logging

# ================= SETUP =================
setup_logging()
CONFIG = load_config()
STORE_FILE = CONFIG.get("store_file", "/tmp/aiops/incidents.json")

app = FastAPI(
    title="AIOps Agent",
    version="2.0.0",
    description="AI-powered Kubernetes RCA and Remediation"
)

# ================= STATE =================
incidents = []
incident_cache = set()
memory_db = []

# ================= PROMETHEUS METRICS =================
incident_counter = Counter(
    'aiops_incidents_total',
    'Total incidents detected',
    ['rule', 'namespace', 'status']
)
remediation_counter = Counter(
    'aiops_remediations_total',
    'Total remediations attempted',
    ['action', 'status']
)
ai_rca_latency = Histogram(
    'aiops_rca_latency_seconds',
    'AI RCA latency',
    buckets=(5, 10, 30, 60, 120, 300)
)

# ================= STORAGE =================
def load_incidents():
    """Load incidents from persistent storage"""
    global incidents, memory_db
    try:
        os.makedirs(os.path.dirname(STORE_FILE), exist_ok=True)
        with open(STORE_FILE) as f:
            data = json.load(f)
            incidents = data.get("incidents", [])
            memory_db = data.get("memory", [])
            logger.info(f"✓ Loaded {len(incidents)} incidents from storage")
    except FileNotFoundError:
        incidents, memory_db = [], []
        logger.info("ℹ No stored incidents found - starting fresh")
    except Exception as e:
        logger.error(f"✗ Error loading incidents: {e}")
        incidents, memory_db = [], []

def save_incidents():
    """Save incidents to persistent storage"""
    try:
        os.makedirs(os.path.dirname(STORE_FILE), exist_ok=True)
        with open(STORE_FILE, "w") as f:
            json.dump(
                {
                    "incidents": incidents[-CONFIG.get("max_stored_incidents", 1000):],
                    "memory": memory_db[-CONFIG.get("max_memory_db", 500):]
                },
                f,
                indent=2
            )
    except Exception as e:
        logger.error(f"✗ Error saving incidents: {e}")

# ================= LOG COLLECTION =================
def get_logs_from_pod(v1, pod, tail_lines=100) -> str:
    """Fetch logs from pod"""
    try:
        logs = v1.read_namespaced_pod_log(
            name=pod.metadata.name,
            namespace=pod.metadata.namespace,
            tail_lines=tail_lines,
            timestamps=True
        )
        return logs[:2000] if logs else "No logs available"
    except Exception as e:
        logger.debug(f"Could not fetch logs from pod: {e}")
        return "No logs available"

def get_logs_from_loki(pod_name: str, namespace: str, loki_url: str) -> str:
    """Fetch logs from Loki"""
    try:
        query = f'{{namespace="{namespace}", pod="{pod_name}"}}'
        response = requests.get(
            f"{loki_url}/loki/api/v1/query_range",
            params={"query": query, "limit": 500, "direction": "backward"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            logs = []
            for stream in data.get("data", {}).get("result", []):
                for val in stream.get("values", []):
                    logs.append(val[1])
            
            return "\n".join(logs[-100:])[-2000:] if logs else "No logs in Loki"
        return "Loki unavailable"
    except requests.Timeout:
        return "Loki timeout"
    except Exception as e:
        logger.debug(f"Loki error: {e}")
        return "Loki error"

# ================= EVENT COLLECTION =================
def get_events(v1, pod) -> str:
    """Fetch events for pod"""
    try:
        events = v1.list_namespaced_event(pod.metadata.namespace)
        pod_events = [
            f"{e.reason}: {e.message} ({e.last_timestamp})"
            for e in events.items 
            if e.involved_object.name == pod.metadata.name and e.involved_object.kind == "Pod"
        ]
        return "\n".join(pod_events[-20:])[:1000] if pod_events else "No events"
    except Exception as e:
        logger.debug(f"Error fetching events: {e}")
        return "No events"

# ================= MEMORY MANAGEMENT =================
def check_memory(rule: str, logs: str) -> Optional[str]:
    """Check if similar issue was seen before"""
    for item in memory_db:
        if item["rule"] == rule:
            if item["pattern"] in logs[:500]:
                return item["rca"]
    return None

def store_memory(rule: str, logs: str, rca: str):
    """Store RCA in memory for future reference"""
    memory_db.append({
        "rule": rule,
        "pattern": logs[:200],
        "rca": rca,
        "timestamp": datetime.utcnow().isoformat()
    })
    if len(memory_db) > CONFIG.get("max_memory_db", 500):
        memory_db.pop(0)

# ================= CORRELATION =================
def correlate_incidents(namespace: str, rule: str) -> Optional[dict]:
    """Check for related incidents"""
    related = [
        i for i in incidents[-100:]
        if i["namespace"] == namespace and i["rule"] == rule
    ]
    
    if len(related) >= 3:
        return {
            "type": "cluster_wide",
            "message": f"⚠️ Cluster-wide issue: {len(related)} pods affected by {rule}",
            "affected_pods": len(related)
        }
    
    return None

# ================= AI RCA ENGINE =================
def ai_rca(pod_name: str, namespace: str, logs: str, events: str, rule: str) -> str:
    """Call Ollama for AI-based RCA"""
    
    start_time = time.time()
    
    prompt = f"""You are a Kubernetes SRE expert. Analyze this pod failure and provide clear, actionable solutions.

Pod Name: {pod_name}
Namespace: {namespace}
Issue Type: {rule}

=== LOGS ===
{logs[:1500]}

=== EVENTS ===
{events[:500]}

Provide ONLY these 3 sections in this exact format:

Root Cause Analysis:
[Explain what went wrong based on the logs and events]

Recommended Fix:
[Provide specific kubectl commands or actions to fix this]

Prevention Steps:
[What should be done to prevent this issue in the future]

Be concise, specific, and actionable."""

    retry_count = 0
    max_retries = 3
    
    while retry_count < max_retries:
        try:
            logger.info(f"[AI-RCA] Calling Ollama for {pod_name} ({retry_count + 1}/{max_retries})")
            
            response = requests.post(
                f"{CONFIG.get('ollama_url')}/api/generate",
                json={
                    "model": CONFIG.get("ollama_model"),
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": 500,
                        "temperature": 0.7,
                        "top_p": 0.9
                    }
                },
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json().get("response", "").strip()
                
                if "Root Cause Analysis:" in result:
                    elapsed = time.time() - start_time
                    ai_rca_latency.observe(elapsed)
                    logger.info(f"[AI-RCA] ✓ Success for {pod_name} ({elapsed:.2f}s)")
                    return result
            
            logger.warning(f"[AI-RCA] ✗ Unexpected response: {response.status_code}")
            
        except requests.Timeout:
            logger.warning(f"[AI-RCA] ⏱️ Timeout for {pod_name}")
        except Exception as e:
            logger.error(f"[AI-RCA] ✗ Error: {e}")
        
        retry_count += 1
        if retry_count < max_retries:
            time.sleep(5)
    
    logger.error(f"[AI-RCA] ✗ Failed after {max_retries} retries")
    raise Exception("AI-RCA failed after retries")

# ================= FALLBACK RCA =================
def deterministic_rca(rule: str, logs: str, events: str) -> str:
    """Fallback RCA when AI fails"""
    
    fallback_rcas = {
        "OOMKilled": """Root Cause Analysis:
The container exceeded its memory limit and was killed by Kubernetes.

Recommended Fix:
1. kubectl describe pod {pod} -n {ns} | grep -A 5 "Limits"
2. kubectl set resources deployment/{deployment} --limits=memory=2Gi
3. Review application for memory leaks

Prevention Steps:
- Set memory requests/limits appropriately
- Use memory profiling tools
- Monitor with: kubectl top pods""",

        "CrashLoopBackOff": """Root Cause Analysis:
Container is crashing repeatedly.

Recommended Fix:
1. kubectl logs {pod} -n {ns} --previous
2. kubectl describe pod {pod} -n {ns}
3. Check deployment configuration

Prevention Steps:
- Validate Dockerfile and entrypoint
- Test locally before deployment
- Use health checks""",

        "ImagePullBackOff": """Root Cause Analysis:
Cannot pull container image.

Recommended Fix:
1. kubectl get events -n {ns}
2. Verify image name and registry
3. Check image pull secrets

Prevention Steps:
- Use image pull secrets for private registries
- Verify image exists before deploying
- Use specific image tags""",

        "DNS Failure": """Root Cause Analysis:
Pod cannot resolve DNS names.

Recommended Fix:
1. kubectl exec {pod} -- nslookup kubernetes.default
2. Check CoreDNS: kubectl get pods -n kube-system -l k8s-app=kube-dns
3. Verify service exists: kubectl get svc

Prevention Steps:
- Ensure CoreDNS is running
- Verify DNS configuration
- Use fully qualified domain names""",
    }
    
    return fallback_rcas.get(rule, f"Unable to determine root cause for {rule}. Check logs manually.")

# ================= ASYNC RCA PROCESSING =================
def process_ai_rca(incident: dict, pod, v1, logs: str, events: str, rule: str):
    """Process AI RCA asynchronously"""
    
    try:
        # Check memory for similar issue
        cached_rca = check_memory(rule, logs)
        if cached_rca:
            incident["ai_rca"] = f"✓ [CACHED] {cached_rca[:500]}"
            incident["status"] = "resolved"
            logger.info(f"Using cached RCA for {pod.metadata.name}")
            return
        
        # Call AI
        rca = ai_rca(
            pod.metadata.name,
            pod.metadata.namespace,
            logs,
            events,
            rule
        )
        
        incident["ai_rca"] = rca
        incident["status"] = "resolved"
        store_memory(rule, logs, rca)
        logger.info(f"AI RCA completed for {pod.metadata.name}")
        
    except Exception as e:
        logger.error(f"✗ AI RCA failed: {e}")
        fallback = deterministic_rca(rule, logs, events)
        incident["ai_rca"] = f"⚠️ [FALLBACK] {fallback}"
        incident["status"] = "fallback"
    
    finally:
        save_incidents()

# ================= INCIDENT DETECTION & PROCESSING =================
def process_pod(pod, v1, v1_metrics=None):
    """Process a failed pod"""
    
    pod_name = pod.metadata.name
    namespace = pod.metadata.namespace
    uid = pod.metadata.uid
    
    # Check if already processed
    key = f"{namespace}-{pod_name}-{uid}"
    if key in incident_cache:
        return
    
    incident_cache.add(key)
    
    try:
        # Collect signals
        logs = get_logs_from_pod(v1, pod)
        if logs == "No logs available":
            logs = get_logs_from_loki(
                pod_name,
                namespace,
                CONFIG.get("loki_url", "http://loki.monitoring:3100")
            )
        
        events = get_events(v1, pod)
        
        # Get metrics if available
        metrics = {}
        if v1_metrics:
            metrics = MetricsCollector.get_pod_metrics(v1_metrics, pod)
        
        # Detect issue
        detection_engine = DetectionEngine(logs, events, metrics)
        rule, severity = detection_engine.detect()
        
        # Check for correlation
        correlation = correlate_incidents(namespace, rule)
        
        # Attempt remediation
        remediation_system = RemediationSystem(v1, CONFIG)
        remediation_result = remediation_system.execute(pod, rule, logs)
        
        # Create incident record
        incident = {
            "id": uid,
            "pod": pod_name,
            "namespace": namespace,
            "timestamp": datetime.utcnow().isoformat(),
            "rule": rule,
            "severity": severity,
            "metrics": metrics,
            "logs": logs[:1000],
            "events": events,
            "correlation": correlation,
            "remediation": remediation_result,
            "ai_rca": "⏳ AI analysis in progress...",
            "status": "analyzing"
        }
        
        incidents.append(incident)
        incident_counter.labels(rule=rule, namespace=namespace, status="detected").inc()
        
        logger.info(f"📍 Incident detected: {rule} in {namespace}/{pod_name} (severity: {severity})")
        
        if remediation_result["status"] == "success":
            remediation_counter.labels(action=remediation_result["action"], status="success").inc()
        
        save_incidents()
        
        # Process AI RCA asynchronously
        threading.Thread(
            target=process_ai_rca,
            args=(incident, pod, v1, logs, events, rule),
            daemon=True
        ).start()
        
    except Exception as e:
        logger.error(f"✗ Error processing pod {pod_name}: {e}\n{traceback.format_exc()}")
        incident_counter.labels(rule="ProcessingError", namespace=namespace, status="error").inc()

# ================= KUBERNETES WATCHER =================
def watch_pods():
    """Watch for pod changes"""
    
    try:
        config.load_incluster_config()
        logger.info("✓ Using in-cluster config")
    except:
        try:
            config.load_kube_config()
            logger.info("✓ Using kubeconfig")
        except Exception as e:
            logger.error(f"✗ Failed to load Kubernetes config: {e}")
            return
    
    v1 = client.CoreV1Api()
    
    try:
        v1_metrics = client.CustomObjectsApi()
    except:
        v1_metrics = None
        logger.warning("⚠ Metrics API not available")
    
    logger.info("🚀 AIOps Agent watching for pod failures...")
    
    w = watch.Watch()
    while True:
        try:
            for event in w.stream(v1.list_pod_for_all_namespaces, timeout_seconds=300):
                pod = event['object']
                
                if pod.status.container_statuses:
                    for container_status in pod.status.container_statuses:
                        # Check restart count
                        if container_status.restart_count > 0:
                            process_pod(pod, v1, v1_metrics)
                        
                        # Check if waiting
                        if container_status.state and container_status.state.waiting:
                            reason = container_status.state.waiting.reason
                            if reason in ["CrashLoopBackOff", "ImagePullBackOff", "CreateContainerConfigError"]:
                                process_pod(pod, v1, v1_metrics)
                        
                        # Check if terminated with error
                        if container_status.state and container_status.state.terminated:
                            if container_status.state.terminated.exit_code != 0:
                                process_pod(pod, v1, v1_metrics)
        
        except Exception as e:
            logger.error(f"✗ Watch error: {e}")
            time.sleep(10)

# ================= API ENDPOINTS =================
@app.get("/health")
def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "incidents_count": len(incidents),
        "memory_db_size": len(memory_db),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()

@app.get("/incidents")
def get_incidents(limit: int = 50):
    """Get recent incidents"""
    return {
        "total": len(incidents),
        "recent": incidents[-limit:] if incidents else []
    }

@app.get("/incidents/{incident_id}")
def get_incident(incident_id: str):
    """Get specific incident"""
    for incident in incidents:
        if incident.get("id") == incident_id:
            return incident
    raise HTTPException(status_code=404, detail="Incident not found")

@app.get("/memory")
def get_memory():
    """Get memory DB"""
    return {
        "size": len(memory_db),
        "entries": memory_db[-20:] if memory_db else []
    }

@app.post("/clear-cache")
def clear_cache():
    """Clear incident cache"""
    global incident_cache
    count = len(incident_cache)
    incident_cache.clear()
    return {"message": f"Cleared {count} cached incidents"}

# ================= STARTUP =================
@app.on_event("startup")
def startup():
    logger.info("=" * 60)
    logger.info("🚀 Starting AIOps Agent v2.0.0")
    logger.info("=" * 60)
    load_incidents()
    threading.Thread(target=watch_pods, daemon=True).start()
    logger.info("✓ AIOps Agent initialized and watching pods")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)