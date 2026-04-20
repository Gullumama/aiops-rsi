#!/bin/bash

echo "🚀 Starting Ollama server..."

ollama serve &

echo "⏳ Waiting for Ollama API to be ready..."

until curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
  echo "  Waiting for Ollama..."
  sleep 2
done

echo "✓ Ollama is ready!"

# Pull model if not present
MODEL_NAME="llama3:8b-instruct-q4_0"

if ! ollama list | grep -q "$MODEL_NAME"; then
  echo "📥 Pulling $MODEL_NAME model (this may take a few minutes)..."
  ollama pull "$MODEL_NAME"
  echo "✓ Model pulled successfully"
else
  echo "✓ $MODEL_NAME model already present"
fi

echo "🚀 Ollama fully ready!"

# Keep container alive
wait