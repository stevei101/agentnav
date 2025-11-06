#!/usr/bin/env python3
"""
Test Gemma Rollback - Local Verification
Quick test to verify backend works without Gemma service
"""
import os
import sys

# Clear GEMMA_SERVICE_URL if set
os.environ.pop('GEMMA_SERVICE_URL', None)

def test_imports():
    """Test that critical imports work without Gemma"""
    print("🧪 Test 1: Import agents without Gemma...")
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        from agents.visualizer_agent import VisualizerAgent
        from agents.summarizer_agent import SummarizerAgent
        from agents.linker_agent import LinkerAgent
        from services.gemini_client import reason_with_gemini
        print("   ✅ All imports successful")
        return True
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False

def test_gemma_client_missing():
    """Test that gemma_client import fails gracefully"""
    print("🧪 Test 2: Verify gemma_client is missing...")
    try:
        from services.gemma_client import get_gemma_client
        print("   ⚠️  gemma_client still exists (unexpected)")
        return False
    except ImportError:
        print("   ✅ gemma_client correctly removed")
        return True
    except Exception as e:
        print(f"   ⚠️  Unexpected error: {e}")
        return False

def test_main_endpoint():
    """Test that main.py endpoint handles missing Gemma gracefully"""
    print("🧪 Test 3: Check main.py endpoint fallback...")
    try:
        with open('main.py', 'r') as f:
            content = f.read()
            if 'gemma_client' in content and ('ImportError' in content or 'RuntimeError' in content):
                print("   ✅ main.py has fallback logic for missing Gemma")
                return True
            elif 'gemma_client' not in content:
                print("   ✅ main.py no longer references gemma_client")
                return True
            else:
                print("   ⚠️  main.py references gemma_client without fallback")
                return False
    except Exception as e:
        print(f"   ⚠️  Could not check main.py: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Gemma Rollback Local Verification")
    print("=" * 60)
    
    results = []
    results.append(test_imports())
    results.append(test_gemma_client_missing())
    results.append(test_main_endpoint())
    
    print("\n" + "=" * 60)
    if all(results):
        print("✅ All tests passed! Rollback verified.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please review.")
        sys.exit(1)

