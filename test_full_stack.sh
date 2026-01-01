#!/bin/bash
# Full Stack Integration Test Script

set -e  # Exit on error

echo "🚀 Starting Full Stack Integration Test..."
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
        exit 1
    fi
}

# Function to wait for service
wait_for_service() {
    local url=$1
    local max_attempts=30
    local attempt=1

    echo -e "${YELLOW}⏳ Waiting for $url...${NC}"

    while [ $attempt -le $max_attempts ]; do
        if curl -s --head $url >/dev/null; then
            echo -e "${GREEN}✅ $url is ready${NC}"
            return 0
        fi
        echo -e "${YELLOW}  Attempt $attempt/$max_attempts...${NC}"
        sleep 2
        attempt=$((attempt + 1))
    done

    echo -e "${RED}❌ $url failed to start${NC}"
    return 1
}

echo ""
echo "📋 Test Plan:"
echo "1. Check backend API"
echo "2. Check frontend server"
echo "3. Test API proxy"
echo "4. Test core functionality"
echo "5. Verify integration"
echo ""

# Step 1: Check backend API
echo "🔍 Step 1: Checking Backend API..."
if curl -s http://localhost:8000/api/health >/dev/null; then
    backend_status=$(curl -s http://localhost:8000/api/health | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])")
    print_status 0 "Backend API is running ($backend_status)"
else
    print_status 1 "Backend API is not accessible"
fi

# Step 2: Check frontend server
echo ""
echo "🔍 Step 2: Checking Frontend Server..."
if curl -s http://localhost:5174 >/dev/null; then
    print_status 0 "Frontend server is running"
else
    print_status 1 "Frontend server is not accessible"
fi

# Step 3: Test API proxy
echo ""
echo "🔍 Step 3: Testing API Proxy..."
if curl -s http://localhost:5174/api/health >/dev/null; then
    proxy_status=$(curl -s http://localhost:5174/api/health | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])")
    print_status 0 "API proxy is working ($proxy_status)"
else
    print_status 1 "API proxy is not working"
fi

# Step 4: Test core functionality
echo ""
echo "🔍 Step 4: Testing Core Functionality..."

# Test search API
echo "  Testing Search API..."
search_result=$(curl -s "http://localhost:5174/api/search/?query=test" | python3 -c "import sys, json; data=json.load(sys.stdin); print('success' if data.get('success') else 'failed')")
if [ "$search_result" = "success" ]; then
    echo -e "    ${GREEN}✅ Search API: Working${NC}"
else
    echo -e "    ${RED}❌ Search API: Failed${NC}"
fi

# Test analytics API
echo "  Testing Analytics API..."
analytics_result=$(curl -s "http://localhost:5174/api/analytics/summary" | python3 -c "import sys, json; data=json.load(sys.stdin); print('success' if data.get('success') else 'failed')")
if [ "$analytics_result" = "success" ]; then
    echo -e "    ${GREEN}✅ Analytics API: Working${NC}"
else
    echo -e "    ${RED}❌ Analytics API: Failed${NC}"
fi

# Step 5: Verify integration
echo ""
echo "🔍 Step 5: Verifying Integration..."

# Check if both services are running
backend_pid=$(ps aux | grep "uvicorn src.backend.main" | grep -v grep | awk '{print $2}')
frontend_pid=$(ps aux | grep "vite" | grep -v grep | awk '{print $2}')

if [ -n "$backend_pid" ] && [ -n "$frontend_pid" ]; then
    echo -e "${GREEN}✅ Both services are running:${NC}"
    echo -e "  Backend PID: $backend_pid"
    echo -e "  Frontend PID: $frontend_pid"
else
    echo -e "${RED}❌ Services not running properly${NC}"
    if [ -z "$backend_pid" ]; then
        echo -e "  Backend is not running"
    fi
    if [ -z "$frontend_pid" ]; then
        echo -e "  Frontend is not running"
    fi
fi

# Test complete workflow
echo ""
echo "🔍 Testing Complete Workflow..."
echo "  Making sample API calls..."

# Test 1: Health check
echo "  Test 1: Health Check..."
health_response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5174/api/health)
if [ "$health_response" = "200" ]; then
    echo -e "    ${GREEN}✅ Health check: 200 OK${NC}"
else
    echo -e "    ${RED}❌ Health check: $health_response${NC}"
fi

# Test 2: Root endpoint
echo "  Test 2: Root Endpoint..."
root_response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5174/)
if [ "$root_response" = "200" ]; then
    echo -e "    ${GREEN}✅ Root endpoint: 200 OK${NC}"
else
    echo -e "    ${RED}❌ Root endpoint: $root_response${NC}"
fi

# Test 3: API documentation
echo "  Test 3: API Documentation..."
docs_response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs)
if [ "$docs_response" = "200" ]; then
    echo -e "    ${GREEN}✅ API docs: 200 OK${NC}"
else
    echo -e "    ${RED}❌ API docs: $docs_response${NC}"
fi

echo ""
echo "📊 Test Summary:"
echo "================"

# Count successful tests
success_count=0
total_tests=8

# Check each test
[ "$backend_status" = "healthy" ] && success_count=$((success_count + 1))
curl -s http://localhost:5174 >/dev/null && success_count=$((success_count + 1))
[ "$proxy_status" = "healthy" ] && success_count=$((success_count + 1))
[ "$search_result" = "success" ] && success_count=$((success_count + 1))
[ "$analytics_result" = "success" ] && success_count=$((success_count + 1))
[ -n "$backend_pid" ] && [ -n "$frontend_pid" ] && success_count=$((success_count + 1))
[ "$health_response" = "200" ] && success_count=$((success_count + 1))
[ "$root_response" = "200" ] && success_count=$((success_count + 1))

# Calculate percentage
percentage=$((success_count * 100 / total_tests))

echo -e "Total Tests: $total_tests"
echo -e "Passed: ${GREEN}$success_count${NC}"
echo -e "Failed: ${RED}$((total_tests - success_count))${NC}"
echo -e "Success Rate: ${YELLOW}$percentage%${NC}"

echo ""
if [ $success_count -eq $total_tests ]; then
    echo -e "${GREEN}🎉 All tests passed! Full stack integration is working correctly.${NC}"
    echo ""
    echo "🌐 Access URLs:"
    echo "  Frontend: http://localhost:5174"
    echo "  Backend API: http://localhost:8000"
    echo "  API Docs: http://localhost:8000/docs"
    echo ""
    echo "🚀 System is ready for production use!"
else
    echo -e "${YELLOW}⚠️  Some tests failed. Please check the logs above.${NC}"
    exit 1
fi