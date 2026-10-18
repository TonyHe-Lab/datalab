#!/bin/bash
# Production Deployment Script for Medical Work Order Analysis API

set -e  # Exit on error

echo "🚀 Starting production deployment..."
echo "===================================="

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Creating one..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install/upgrade dependencies
echo "📦 Installing/upgrading dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Run all tests to ensure everything works
echo "🧪 Running tests..."
if python -m pytest tests/backend/ tests/integration/test_api_integration.py tests/integration/test_end_to_end.py -v --tb=short; then
    echo "✅ All tests passed!"
else
    echo "❌ Tests failed. Deployment aborted."
    exit 1
fi

# Check database connection
echo "🔍 Checking database connection..."
if pg_isready -h localhost -p 5432; then
    echo "✅ Database is ready"
else
    echo "❌ Database is not accessible. Please ensure PostgreSQL is running."
    exit 1
fi

# Create production environment file if not exists
if [ ! -f ".env.production" ]; then
    echo "📝 Creating production environment file..."
    cat > .env.production << EOF
# Production Environment Configuration
DEBUG=False
HOST=0.0.0.0
PORT=8000

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=datalab
DB_USER=postgres
DB_PASSWORD=password

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]

# Security
SECRET_KEY=$(openssl rand -hex 32)
EOF
    echo "✅ Production environment file created"
fi

# Copy production environment file
echo "📋 Setting up production environment..."
cp .env.production .env

# Start the application
echo "🚀 Starting FastAPI application..."
echo "📊 API will be available at: http://localhost:8000"
echo "📚 Interactive docs: http://localhost:8000/docs"
echo "📈 Health check: http://localhost:8000/api/health"
echo ""
echo "Press Ctrl+C to stop the application"

# Run the application
# Use script directory for PYTHONPATH (portable, no hardcoded paths)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$SCRIPT_DIR:${PYTHONPATH:-}"
python -m src.backend.main