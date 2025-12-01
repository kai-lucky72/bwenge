#!/bin/bash

# Bwenge OS - Stop Local Development Services

echo "🛑 Stopping Bwenge OS Local Development..."
echo ""

# Read PIDs if file exists
if [ -f .dev-pids ]; then
    pids=$(cat .dev-pids)
    echo "📋 Stopping services..."
    
    for pid in $pids; do
        if kill -0 $pid 2>/dev/null; then
            echo "   Stopping PID $pid..."
            kill $pid 2>/dev/null || true
        fi
    done
    
    rm .dev-pids
    echo "✅ Services stopped"
else
    echo "⚠️  No PID file found, stopping by port..."
    
    # Kill processes on known ports
    ports=(8000 8001 8002 8003 8004 8005 8006 8007)
    for port in "${ports[@]}"; do
        pid=$(lsof -ti:$port 2>/dev/null)
        if [ ! -z "$pid" ]; then
            echo "   Stopping service on port $port (PID: $pid)..."
            kill $pid 2>/dev/null || true
        fi
    done
fi

# Stop Docker services
echo ""
echo "🐳 Stopping Docker services..."
docker-compose -f docker-compose.dev.yml down

echo ""
echo "✅ All services stopped!"
echo ""
