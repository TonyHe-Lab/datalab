#!/bin/bash
# Start script for FastAPI backend

# Activate virtual environment
source venv/bin/activate

# Set environment variables
# Use script directory for PYTHONPATH (portable, no hardcoded paths)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$SCRIPT_DIR:${PYTHONPATH:-}"

# Start FastAPI application
echo "Starting Medical Work Order Analysis API..."
echo "API will be available at: http://localhost:8000"
echo "Interactive docs: http://localhost:8000/docs"
echo ""

python -m src.backend.main