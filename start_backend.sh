#!/bin/bash
# Start script for FastAPI backend

# Activate virtual environment
source venv/bin/activate

# Set environment variables
export PYTHONPATH=/home/tonyhe/TonyHe-Gitlab/datalab:$PYTHONPATH

# Start FastAPI application
echo "Starting Medical Work Order Analysis API..."
echo "API will be available at: http://localhost:8000"
echo "Interactive docs: http://localhost:8000/docs"
echo ""

python -m src.backend.main