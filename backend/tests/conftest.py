"""
pytest configuration for backend tests
Sets up Python path and test fixtures
"""
import sys
import os

# Add the parent directory (repository root) to Python path
# This allows imports like `from backend.main import app`
repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

# Add backend directory to path as well
backend_dir = os.path.join(repo_root, 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
