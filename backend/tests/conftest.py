"""
pytest configuration for backend tests

This conftest.py handles Python path setup for all tests in this directory,
eliminating the need for sys.path manipulation in individual test files.
"""
import sys
import os

# Add workspace root to Python path for backend.* imports
# Tests run from workspace root with: pytest -q backend/tests
workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)
