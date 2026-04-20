# AIOps Agent v2.0.0

AI-powered Kubernetes Root Cause Analysis and Remediation System

## Features

✅ **50+ Failure Detection** - Detects OOMKilled, CrashLoopBackOff, DNS failures, network issues, and more  
✅ **AI-Powered RCA** - Uses Ollama + LLM for intelligent root cause analysis  
✅ **Auto-Remediation** - Safely restarts pods, scales resources, and fixes issues  
✅ **Prometheus Metrics** - Full observability of incidents and remediations  
✅ **Loki Integration** - Centralized log aggregation  
✅ **Memory Learning** - Caches solutions for similar issues  

## Quick Start

### Prerequisites
- Kubernetes cluster (local or remote)
- Docker (for building images)
- kubectl configured

### Local Development with Docker Compose

```bash
docker-compose up -d