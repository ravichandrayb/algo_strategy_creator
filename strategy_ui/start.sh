#!/bin/bash

# Start backend in background
echo "🚀 Starting Flask backend..."
cd backend
source venv/bin/activate
python app.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start frontend
echo "🚀 Starting React frontend..."
cd ../frontend
npm start &
FRONTEND_PID=$!

echo ""
echo "✅ Strategy Manager is running!"
echo "   Backend: http://localhost:5000"
echo "   Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both services"

# Trap Ctrl+C and kill both processes
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT

# Wait for processes
wait
