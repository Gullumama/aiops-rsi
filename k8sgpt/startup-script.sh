#!/bin/bash

set -e

echo "════════════════════════════════════════════════════════════"
echo "K8sGPT Initialization Script"
echo "════════════════════════════════════════════════════════════"

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to be ready..."
OLLAMA_URL=${OLLAMA_URL:-"http://ollama.aiops:11434"}
MAX_RETRIES=30
RETRY_COUNT=0

until curl -s "${OLLAMA_URL}/api/tags" > /dev/null 2>&1; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "✗ Ollama failed to respond after $MAX_RETRIES retries"
        exit 1
    fi
    echo "  Retry $RETRY_COUNT/$MAX_RETRIES..."
    sleep 2
done

echo "✓ Ollama is ready"

# Check if model is available
MODEL_NAME=${OLLAMA_MODEL:-"llama3:8b-instruct-q4_0"}
echo "⏳ Checking if model '$MODEL_NAME' is available..."

if curl -s "${OLLAMA_URL}/api/tags" | grep -q "$MODEL_NAME"; then
    echo "✓ Model '$MODEL_NAME' is available"
else
    echo "⚠️  Model '$MODEL_NAME' not found, K8sGPT will pull it on first use"
fi

# Start K8sGPT
echo "🚀 Starting K8sGPT..."
k8sgpt serve \
    --backend=ollama \
    --model="${MODEL_NAME}" \
    --port=8080 \
    --log-level=info

# Keep container alive
wait