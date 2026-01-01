#!/bin/bash
# Start Production Server Script

set -e  # Exit on error

echo "🚀 Starting Medical Work Order Analysis API in production mode..."
echo "================================================================"

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ Virtual environment not found. Please run deploy_production.sh first."
    exit 1
fi

# Set environment variables for production
export PYTHONPATH=/home/tonyhe/TonyHe-Gitlab/datalab:$PYTHONPATH
export DEBUG=False

echo ""
echo "📊 Application Information:"
echo "   API URL: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo "   Health: http://localhost:8000/api/health"
echo ""
echo "📈 Starting server..."
echo "   Host: 0.0.0.0"
echo "   Port: 8000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the FastAPI application with uvicorn for production
uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 --reload