"""Vercel Serverless Function entry point."""
import sys
from pathlib import Path

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.main import app  # noqa: E402, F401

# Vercel expects the FastAPI app to be exported as `app`
