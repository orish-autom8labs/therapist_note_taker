#!/bin/bash

# Script to run the official Soniox Live Demo example

set -e

EXAMPLE_DIR="/Users/orish/code/soniox_examples/speech_to_text/apps/soniox-live-demo"
SERVER_DIR="$EXAMPLE_DIR/server"
REACT_DIR="$EXAMPLE_DIR/react"

echo "🚀 Setting up Soniox Live Demo Example"
echo "======================================"
echo ""

# Check if SONIOX_API_KEY is set
if [ -z "$SONIOX_API_KEY" ]; then
    echo "⚠️  SONIOX_API_KEY not set!"
    echo "Please set it:"
    echo "  export SONIOX_API_KEY='your_api_key_here'"
    echo ""
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 1: Setup Server
echo "📦 Step 1: Setting up server..."
cd "$SERVER_DIR"

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Installing server dependencies..."
pip install -q -r requirements.txt

# Create .env if it doesn't exist and SONIOX_API_KEY is set
if [ ! -f ".env" ] && [ -n "$SONIOX_API_KEY" ]; then
    echo "SONIOX_API_KEY=$SONIOX_API_KEY" > .env
    echo "✅ Created .env file with API key"
fi

# Step 2: Setup React Frontend
echo ""
echo "📦 Step 2: Setting up React frontend..."
cd "$REACT_DIR"

if [ ! -d "node_modules" ]; then
    echo "Installing React dependencies..."
    npm install
else
    echo "✅ React dependencies already installed"
fi

# Step 3: Start services
echo ""
echo "🎯 Step 3: Starting services..."
echo ""
echo "⚠️  You'll need TWO terminals:"
echo "   1. Server will start in this terminal"
echo "   2. React will need another terminal"
echo ""
echo "Starting server in 3 seconds..."
sleep 3

# Start server in background
cd "$SERVER_DIR"
source .venv/bin/activate
echo "Starting server on http://localhost:8000"
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
SERVER_PID=$!

echo "✅ Server started (PID: $SERVER_PID)"
echo ""
echo "Now open a NEW terminal and run:"
echo "  cd $REACT_DIR"
echo "  npm run dev"
echo ""
echo "Then open your browser to the URL shown (usually http://localhost:5173)"
echo ""
echo "Press Ctrl+C to stop the server"

# Wait for Ctrl+C
trap "kill $SERVER_PID 2>/dev/null; exit" INT TERM
wait $SERVER_PID

