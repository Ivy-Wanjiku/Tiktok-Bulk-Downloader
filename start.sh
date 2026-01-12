#!/bin/bash
# TikTok Bulk Downloader - Start Script

echo "🚀 Starting TikTok Bulk Downloader..."

# Kill any existing processes on ports 3000 and 8080
echo "🧹 Checking for existing processes..."
lsof -ti:3000 | xargs -r kill -9 2>/dev/null
lsof -ti:8080 | xargs -r kill -9 2>/dev/null
sleep 1

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run: python3 -m venv venv"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -q -r backend/requirements.txt
fi

# Create downloads directory
mkdir -p downloads

# Start backend in background
echo "🔧 Starting FastAPI backend on port 3000..."
cd backend
python api.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Start frontend
echo "🌐 Starting frontend on port 8080..."
cd frontend
python3 -m http.server 8080 &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ TikTok Bulk Downloader is running!"
echo ""
echo "   📡 Backend API: http://localhost:3000"
echo "   📖 API Docs: http://localhost:3000/docs"
echo "   🌐 Frontend: http://localhost:8080"
echo "   📁 Downloads: $(pwd)/downloads/"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Trap Ctrl+C to kill both processes
trap "echo ''; echo '🛑 Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT

# Wait for processes
wait
