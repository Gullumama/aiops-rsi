# K8sGPT Custom Build

Custom K8sGPT image built from source for the AIOps platform.

## What is K8sGPT?

K8sGPT is an AI-driven Kubernetes troubleshooting tool that uses LLMs to analyze Kubernetes clusters and provide actionable insights.

## Building from Source

### Prerequisites
- Docker
- Go 1.21+ (for local development)
- kubectl

### Build Methods

#### Method 1: Using Makefile

```bash
cd k8sgpt

# Build image
make build

# Build with custom registry
make build REGISTRY=myregistry TAG=v1.0.0

# Test image
make test

# Deploy to Kubernetes
make deploy