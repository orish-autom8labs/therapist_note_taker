#!/usr/bin/env python3
"""
Simple script to run the server.
"""
import uvicorn
import sys
import os

# Change to server directory so imports work correctly
server_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(server_dir)
sys.path.insert(0, server_dir)

from src.config import config
from src.services.transcription_service import TranscriptionService

if __name__ == "__main__":
    transcription_service = TranscriptionService()
    
    print(f"Starting server on port {config.server.port}")
    print(f"Transcription provider: {transcription_service.get_provider_info()['name']}")
    
    # Import app directly to ensure all routes are loaded
    # For development, we'll disable reload to avoid import issues
    use_reload = False  # Disable reload to ensure WebSocket routes load correctly
    
    try:
        # Import app directly to ensure WebSocket routes are registered
        from main import app
        
        print(f"Server starting on http://0.0.0.0:{config.server.port}")
        print(f"WebSocket endpoint: ws://localhost:{config.server.port}/ws")
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=config.server.port,
            reload=use_reload,
            log_level="info"
        )
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

