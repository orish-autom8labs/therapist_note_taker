#!/bin/bash
# Setup and run Soniox official example

set -e

echo "=== Soniox Official Example Setup ==="

# Check if we're in the right directory
if [ ! -f "soniox_realtime.py" ]; then
    echo "Error: Must run from soniox_test directory"
    exit 1
fi

# Check for API key
if [ -z "$SONIOX_API_KEY" ]; then
    echo "Error: SONIOX_API_KEY environment variable not set"
    echo ""
    echo "Set it with:"
    echo "  export SONIOX_API_KEY=your_api_key_here"
    echo ""
    echo "Or get it from: https://soniox.com/console"
    exit 1
fi

echo "✓ API key found"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

echo ""
echo "=== Running Soniox Real-time Example ==="
echo ""

# Check if audio file exists
if [ -f "assets/coffee_shop.mp3" ]; then
    echo "Using test audio file: assets/coffee_shop.mp3"
    python soniox_realtime.py --audio_path assets/coffee_shop.mp3
else
    echo "Error: Audio file not found at assets/coffee_shop.mp3"
    echo "Please provide an audio file:"
    echo "  python soniox_realtime.py --audio_path /path/to/your/audio.mp3"
    exit 1
fi




