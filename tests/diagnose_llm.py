
"""Diagnostic script for LLM connection issues."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.settings import settings


def diagnose():
    """Run diagnostic checks."""
    print("=" * 60)
    print("🔍 LLM Connection Diagnostics")
    print("=" * 60)
    
    issues = []
    
    # Check 1: API Key
    print("\n1️⃣ Checking API Key...")
    api_key = settings.get_api_key()
    if not api_key or api_key == "your_dashscope_api_key_here":
        print("   ❌ API Key not set or using default placeholder")
        issues.append("Set DASHSCOPE_API_KEY in . env file")
    else:
        print(f"   ✅ API Key found: {api_key[:10]}***")
    
    # Check 2: Model Configuration
    print("\n2️⃣ Checking Model Configuration...")
    print(f"   Provider: {settings.llm_provider}")
    print(f"   Default Model: {settings.get_model()}")
    print(f"   Orchestrator:  {settings.get_model('orchestrator')}")
    print(f"   Subagent: {settings.get_model('subagent')}")
    
    # Check 3: API Base
    print("\n3️⃣ Checking API Base...")
    api_base = settings.get_api_base()
    print(f"   API Base: {api_base}")
    
    # Check 4: Dependencies
    print("\n4️⃣ Checking Dependencies...")
    try:
        import litellm
        print("   ✅ litellm installed")
    except ImportError: 
        print("   ❌ litellm not installed")
        issues.append("Run:  pip install litellm")
    
    try:
        import openai
        print("   ✅ openai installed")
    except ImportError:
        print("   ❌ openai not installed")
        issues.append("Run: pip install openai")
    
    # Summary
    print("\n" + "=" * 60)
    if issues:
        print("⚠️  Issues Found:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
    else:
        print("✅ All checks passed!")
    print("=" * 60)


if __name__ == "__main__": 
    diagnose()
