#!/bin/bash
# Vantage Run Script for Linux/Mac
# This script starts all required services for Vantage

set -e

echo "🔍 Starting LocalLens..."
echo "======================================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.8+${NC}"
    exit 1
fi

# Check if Node is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js not found. Please install Node.js 16+${NC}"
    exit 1
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Ollama not running. Starting Ollama...${NC}"
    ollama serve &
    sleep 3
fi

# Check if OpenSearch is running
if ! curl -s http://localhost:9200 > /dev/null 2>&1; then
    echo -e "${RED}❌ OpenSearch not running on localhost:9200${NC}"
    echo -e "${YELLOW}Please start OpenSearch manually in a separate terminal${NC}"
    echo ""
    echo "To start OpenSearch:"
    echo "  cd /path/to/opensearch"
    echo "  ./bin/opensearch"
    echo ""
    read -p "Press Enter when OpenSearch is running..."
    read -p "Press Enter when OpenSearch is running..."
fi

# Check if Redis is running
if ! (echo > /dev/tcp/localhost/6379) >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Redis not running on localhost:6379${NC}"
    echo -e "${YELLOW}Session memory will be in-memory only (non-persistent)${NC}"
    echo ""
fi

# Create logs directory
mkdir -p logs

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Stopping LocalLens...${NC}"
    kill $(jobs -p) 2>/dev/null
    exit
}

trap cleanup INT TERM

echo ""
echo -e "${GREEN}✅ Prerequisites check passed!${NC}"
echo ""

# Start backend
echo -e "${GREEN}🚀 Starting backend API...${NC}"
python3 -m backend.api > logs/backend.log 2>&1 &
BACKEND_PID=$!
sleep 3

# Check if backend started successfully
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${RED}❌ Backend failed to start. Check logs/backend.log${NC}"
    kill $BACKEND_PID
    exit 1
fi

echo -e "${GREEN}✅ Backend running on http://localhost:8000${NC}"

# Start frontend
echo -e "${GREEN}🚀 Starting frontend...${NC}"
cd frontend
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
sleep 3

echo ""
echo -e "${GREEN}✅ LocalLens is ready!${NC}"
echo "======================================"
echo ""
echo -e "${GREEN}📱 Frontend:${NC} http://localhost:5173"
echo -e "${GREEN}🔌 Backend:${NC}  http://localhost:8000"
echo -e "${GREEN}🔍 OpenSearch:${NC} http://localhost:9200"
echo ""
echo -e "${YELLOW}📝 Logs:${NC}"
echo "  Backend:  logs/backend.log"
echo "  Frontend: logs/frontend.log"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Wait for user interrupt
wait
