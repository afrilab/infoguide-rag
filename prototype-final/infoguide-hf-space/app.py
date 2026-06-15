#!/usr/bin/env python3
"""
Entry point for Hugging Face Spaces deployment.
This module imports and runs the FastAPI app from app/server.py
"""

import sys
import os
from pathlib import Path

# Add app directory to path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from server import app

# Configure CORS for production/demo deployment
# HF Spaces uses a specific domain pattern
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 7860))  # HF Spaces default port
    host = "0.0.0.0"
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
