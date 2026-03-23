#!/bin/bash
# start.sh — DiaWise deployment startup script for Railway
# Step 1: verify / build the Pinecone index (fast-path skip if already populated)
# Step 2: hand off to gunicorn via exec (replaces this shell, ensuring clean signal handling)

set -e  # exit immediately on any error

echo "==> [$(date -u '+%Y-%m-%dT%H:%M:%SZ')] DiaWise startup"
echo "==> Step 1/2: Building/verifying Pinecone index..."

python build_index.py

echo "==> Step 2/2: Index ready. Launching gunicorn..."
exec gunicorn \
  --worker-class gthread \
  --threads 4 \
  --timeout 120 \
  --bind "0.0.0.0:${PORT:-10000}" \
  app:app
