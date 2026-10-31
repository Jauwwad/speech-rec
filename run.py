#!/usr/bin/env python3
"""
Single-command launcher for the Classroom Lecture Speech-to-Text System.
Usage: python run.py
"""
import subprocess, sys, os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("=" * 55)
print("  🎓 Classroom Lecture Speech-to-Text System")
print("=" * 55)
print()

# Check dependencies
try:
    import flask, whisper, librosa, jiwer
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Please run:  pip install -r requirements.txt\n")
    sys.exit(1)

from app import app

print("  Server starting on http://localhost:5000")
print("  Press Ctrl+C to stop.\n")
app.run(host="0.0.0.0", port=5000, debug=False)

