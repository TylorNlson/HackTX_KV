#!/bin/bash

# F1 Race Decision System - Quick Start Script

echo "🏁 F1 Race Decision System - Starting..."
echo "=========================================="

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✓ Python 3 found"

# Check if dependencies are installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

echo "✓ Dependencies ready"

# Start the API server in background
echo "🚀 Starting API server on port 5000..."
python3 src/api/app.py &
API_PID=$!

# Wait for API to be ready
echo "⏳ Waiting for API to start..."
sleep 3

# Check if API is running
if kill -0 $API_PID 2>/dev/null; then
    echo "✓ API server running (PID: $API_PID)"
else
    echo "❌ Failed to start API server"
    exit 1
fi

# Start simple HTTP server for frontend
echo "🌐 Starting web dashboard on port 8000..."
python3 -m http.server 8000 &
WEB_PID=$!

sleep 2

if kill -0 $WEB_PID 2>/dev/null; then
    echo "✓ Web dashboard running (PID: $WEB_PID)"
else
    echo "❌ Failed to start web server"
    kill $API_PID 2>/dev/null
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ System ready!"
echo "=========================================="
echo ""
echo "📊 Web Dashboard: http://localhost:8000"
echo "🔌 API Endpoint:  http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $API_PID 2>/dev/null
    kill $WEB_PID 2>/dev/null
    echo "✓ Stopped"
    exit 0
}

# Trap Ctrl+C
trap cleanup INT

# Wait for user to stop
wait
