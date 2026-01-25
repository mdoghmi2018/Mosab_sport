#!/bin/bash
# Golden Routine: Bring-up, verify, prove invariants
# Usage: ./scripts/golden_routine.sh

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "🚀 Mosab Sport - Golden Routine Verification"
echo "============================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Start stack
echo "📦 Step 1: Starting Docker stack..."
docker-compose up -d --build

echo ""
echo "⏳ Waiting for services to be healthy (30s)..."
sleep 30

# Step 2: Check service status
echo ""
echo "🔍 Step 2: Checking service status..."
docker-compose ps

# Check if services are running
if ! docker-compose ps | grep -q "mosab_api.*Up"; then
    echo -e "${RED}❌ API service is not running${NC}"
    exit 1
fi

if ! docker-compose ps | grep -q "mosab_worker.*Up"; then
    echo -e "${RED}❌ Worker service is not running${NC}"
    exit 1
fi

if ! docker-compose ps | grep -q "mosab_db.*Up"; then
    echo -e "${RED}❌ Database service is not running${NC}"
    exit 1
fi

if ! docker-compose ps | grep -q "mosab_redis.*Up"; then
    echo -e "${RED}❌ Redis service is not running${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All services are running${NC}"

# Step 3: Check logs for errors
echo ""
echo "📋 Step 3: Checking service logs for errors..."

echo "Checking API logs..."
API_ERRORS=$(docker-compose logs api 2>&1 | grep -i "error\|exception\|traceback" | head -5 || true)
if [ -n "$API_ERRORS" ]; then
    echo -e "${YELLOW}⚠️  API warnings/errors found:${NC}"
    echo "$API_ERRORS"
else
    echo -e "${GREEN}✅ API logs clean${NC}"
fi

echo "Checking Worker logs..."
WORKER_ERRORS=$(docker-compose logs worker 2>&1 | grep -i "error\|exception\|traceback" | head -5 || true)
if [ -n "$WORKER_ERRORS" ]; then
    echo -e "${YELLOW}⚠️  Worker warnings/errors found:${NC}"
    echo "$WORKER_ERRORS"
else
    echo -e "${GREEN}✅ Worker logs clean${NC}"
fi

# Step 4: Apply migrations
echo ""
echo "🗄️  Step 4: Applying database migrations..."
if docker-compose exec -T api alembic upgrade head; then
    echo -e "${GREEN}✅ Migrations applied successfully${NC}"
else
    echo -e "${RED}❌ Migration failed${NC}"
    exit 1
fi

# Step 5: Verify API health
echo ""
echo "🏥 Step 5: Verifying API health endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health || echo "FAILED")
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo -e "${GREEN}✅ Health check passed${NC}"
    echo "$HEALTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_RESPONSE"
else
    echo -e "${RED}❌ Health check failed${NC}"
    echo "$HEALTH_RESPONSE"
    exit 1
fi

# Step 6: Verify API docs
echo ""
echo "📚 Step 6: Verifying API documentation..."
if curl -s http://localhost:8000/docs > /dev/null; then
    echo -e "${GREEN}✅ API docs accessible at http://localhost:8000/docs${NC}"
else
    echo -e "${YELLOW}⚠️  API docs not accessible (may be disabled in production)${NC}"
fi

# Step 7: Verify frontend port
echo ""
echo "🌐 Step 7: Verifying frontend port..."
FRONTEND_PORT=$(docker-compose ps | grep mosab_frontend | grep -oP '0.0.0.0:\K[0-9]+' | head -1 || echo "")
if [ -n "$FRONTEND_PORT" ]; then
    echo -e "${GREEN}✅ Frontend accessible on port $FRONTEND_PORT${NC}"
    echo "   Note: Vite default is 5173, but compose maps to 3000"
else
    echo -e "${YELLOW}⚠️  Frontend port not detected${NC}"
fi

# Step 8: Verify Celery beat (for TTL expiry)
echo ""
echo "⏰ Step 8: Checking Celery beat for TTL expiry..."
if docker-compose ps | grep -q "celery.*beat"; then
    echo -e "${GREEN}✅ Celery beat is running${NC}"
else
    echo -e "${YELLOW}⚠️  Celery beat not detected - TTL expiry may not work${NC}"
    echo "   Add celery-beat service to docker-compose.yml"
fi

# Step 9: Verify shared volumes
echo ""
echo "💾 Step 9: Verifying shared volumes..."
if docker-compose exec -T api test -d /app/uploads/reports; then
    echo -e "${GREEN}✅ Report directory exists in API container${NC}"
else
    echo -e "${YELLOW}⚠️  Report directory missing - creating...${NC}"
    docker-compose exec -T api mkdir -p /app/uploads/reports
fi

if docker-compose exec -T worker test -d /app/uploads/reports; then
    echo -e "${GREEN}✅ Report directory exists in Worker container${NC}"
else
    echo -e "${YELLOW}⚠️  Report directory missing in worker - creating...${NC}"
    docker-compose exec -T worker mkdir -p /app/uploads/reports
fi

echo ""
echo -e "${GREEN}✅ Golden Routine Complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Run: ./scripts/seed_demo_data.py"
echo "  2. Run: ./scripts/e2e_smoke_test.py"
echo ""

