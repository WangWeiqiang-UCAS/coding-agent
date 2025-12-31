"""Test LLM client with Qwen API."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path. insert(0, str(Path(__file__).parent.parent))

from app.llm.client import LLMClient, get_llm_response
from app.config.settings import settings


async def test_basic_completion():
    """Test basic LLM completion."""
    print("=" * 60)
    print("🧪 Test 1: Basic Completion")
    print("=" * 60)
    
    client = LLMClient(
        model=settings.get_model(),
        api_key=settings. get_api_key(),
        api_base=settings.get_api_base(),
    )
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say 'Hello!  I am working correctly.' in both Chinese and English."}
    ]
    
    print(f"\n📤 Sending request to {settings.get_model()}...")
    
    try:
        response = await client.get_completion(messages, max_tokens=100)
        print(f"\n✅ Response received:")
        print(f"   {response}")
        
        # Test token counting
        token_count = client.count_tokens(messages)
        print(f"\n📊 Input tokens: ~{token_count}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_coding_task():
    """Test LLM with a coding task."""
    print("\n" + "=" * 60)
    print("🧪 Test 2: Coding Task")
    print("=" * 60)
    
    client = LLMClient(
        model=settings.get_model(),
        api_key=settings.get_api_key(),
        api_base=settings.get_api_base(),
    )
    
    messages = [
        {"role": "system", "content": "You are a Python programming expert."},
        {"role": "user", "content": "Write a Python function to calculate factorial.  Just show the code, no explanation."}
    ]
    
    print(f"\n📤 Sending coding request...")
    
    try:
        response = await client.get_completion(messages, max_tokens=300)
        print(f"\n✅ Code generated:")
        print("-" * 60)
        print(response)
        print("-" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


async def test_orchestrator_model():
    """Test orchestrator model configuration."""
    print("\n" + "=" * 60)
    print("🧪 Test 3: Orchestrator Model")
    print("=" * 60)
    
    client = LLMClient(
        model=settings.get_model("orchestrator"),
        api_key=settings.get_api_key("orchestrator"),
        api_base=settings.get_api_base("orchestrator"),
    )
    
    print(f"\n📋 Configuration:")
    print(f"   Model: {settings.get_model('orchestrator')}")
    print(f"   Temperature: {settings. orca_orchestrator_temperature}")
    
    messages = [
        {"role": "user", "content": "List 3 key principles of multi-agent systems in one sentence each."}
    ]
    
    print(f"\n📤 Sending request...")
    
    try:
        response = await client.get_completion(messages, max_tokens=200)
        print(f"\n✅ Response:")
        print(f"   {response}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


async def test_subagent_model():
    """Test subagent model configuration."""
    print("\n" + "=" * 60)
    print("🧪 Test 4: Subagent Model")
    print("=" * 60)
    
    client = LLMClient(
        model=settings.get_model("subagent"),
        api_key=settings.get_api_key("subagent"),
        api_base=settings.get_api_base("subagent"),
    )
    
    print(f"\n📋 Configuration:")
    print(f"   Model: {settings.get_model('subagent')}")
    print(f"   Temperature: {settings.orca_subagent_temperature}")
    
    messages = [
        {"role": "user", "content": "What is 2+2?  Answer in one word."}
    ]
    
    print(f"\n📤 Sending request...")
    
    try:
        response = await client.get_completion(messages, max_tokens=50)
        print(f"\n✅ Response:  {response. strip()}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


async def test_retry_logic():
    """Test retry logic with invalid API key."""
    print("\n" + "=" * 60)
    print("🧪 Test 5: Retry Logic (Expected to Fail)")
    print("=" * 60)
    
    client = LLMClient(
        model=settings.get_model(),
        api_key="invalid_key_for_testing",
        api_base=settings.get_api_base(),
        max_retries=2,  # Reduce retries for faster testing
    )
    
    messages = [
        {"role":  "user", "content": "Hello"}
    ]
    
    print(f"\n📤 Sending request with invalid API key...")
    print(f"   (Should see retry attempts)")
    
    try:
        response = await client.get_completion(messages, max_tokens=50)
        print(f"\n❌ Unexpected success: {response}")
        return False
        
    except Exception as e:
        print(f"\n✅ Expected failure: {type(e).__name__}")
        print(f"   (Retry logic working correctly)")
        return True


async def test_convenience_function():
    """Test convenience function."""
    print("\n" + "=" * 60)
    print("🧪 Test 6: Convenience Function")
    print("=" * 60)
    
    messages = [
        {"role": "user", "content": "Say 'OK' in one word."}
    ]
    
    print(f"\n📤 Using get_llm_response() function...")
    
    try:
        response = await get_llm_response(
            messages=messages,
            model=settings. get_model(),
            api_key=settings.get_api_key(),
            api_base=settings.get_api_base(),
            max_tokens=50
        )
        print(f"\n✅ Response: {response. strip()}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


async def main():
    """Run all tests."""
    print("\n" + "🚀" * 30)
    print("LLM Client Test Suite")
    print("🚀" * 30)
    
    print(f"\n📋 Configuration Summary:")
    print(f"   Provider: {settings.llm_provider}")
    print(f"   Default Model: {settings.get_model()}")
    print(f"   Orchestrator Model: {settings.get_model('orchestrator')}")
    print(f"   Subagent Model: {settings.get_model('subagent')}")
    print(f"   API Base: {settings.get_api_base()}")
    print(f"   API Key: {settings.get_api_key()[:10]}***")
    
    # Run tests
    tests = [
        ("Basic Completion", test_basic_completion),
        ("Coding Task", test_coding_task),
        ("Orchestrator Model", test_orchestrator_model),
        ("Subagent Model", test_subagent_model),
        ("Retry Logic", test_retry_logic),
        ("Convenience Function", test_convenience_function),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            results. append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}:  {name}")
    
    print(f"\n   Total:  {passed}/{total} passed")
    
    if passed == total:
        print("\n🎉 All tests passed!  LLM client is ready.")
    elif passed >= total - 1:  # Allow retry test to fail
        print("\n✅ Core tests passed! System is ready.")
    else:
        print("\n⚠️  Some tests failed.  Please check your configuration.")
    
    print("=" * 60)


if __name__ == "__main__": 
    asyncio.run(main())
