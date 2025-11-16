#!/bin/bash

echo "🚀 Setting up Strategy Manager UI..."
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

echo "✅ Python and Node.js found"
echo ""

# Setup Backend
echo "📦 Setting up Flask backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

echo "✅ Backend setup complete"
echo ""

# Setup Frontend
echo "📦 Setting up React frontend..."
cd ../frontend

# Install Node dependencies
npm install

echo "✅ Frontend setup complete"
echo ""
echo "🎉 Setup complete!"
echo ""
echo "To start the application:"
echo "1. Start the backend:"
echo "   cd backend && source venv/bin/activate && python app.py"
echo ""
echo "2. In a new terminal, start the frontend:"
echo "   cd frontend && npm start"
echo ""
echo "The UI will be available at http://localhost:3000"
