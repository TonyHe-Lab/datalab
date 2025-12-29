#!/usr/bin/env python3
"""
Simple test to verify FastAPI installation and basic functionality.
"""

import sys
import asyncio
from fastapi import FastAPI
import uvicorn

# Create a simple app for testing
app = FastAPI()


@app.get("/")
async def root():
    return {"message": "FastAPI is working!"}


@app.get("/test")
async def test():
    return {"status": "ok", "test": "successful"}


if __name__ == "__main__":
    print("Testing FastAPI installation...")

    # Test imports
    try:
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        import uvicorn

        print("✓ All imports successful")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        sys.exit(1)

    # Test creating app
    try:
        test_app = FastAPI()
        print("✓ FastAPI app creation successful")
    except Exception as e:
        print(f"✗ App creation error: {e}")
        sys.exit(1)

    print("\nFastAPI installation test passed!")
    print("You can now run the main application with:")
    print("  cd /home/tonyhe/TonyHe-Gitlab/datalab")
    print("  source venv/bin/activate")
    print("  python -m src.backend.main")
