"""
Root-level pytest configuration
Sets up Python path for all tests
"""
import sys
import os

# Ensure the repo root is in the path for backend imports
repo_root = os.path.dirname(os.path.abspath(__file__))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

# Ensure backend directory is in the path
backend_dir = os.path.join(repo_root, 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
