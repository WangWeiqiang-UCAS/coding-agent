"""Test Qwen API connection."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path. insert(0, str(Path(__file__).parent.parent))

from app.llm.client import LLMClient
from app.config.settings import settings


async def test_qwen_connection():
    """Test connection to Qwen API."""
    print("=" * 60)
    print("Testing Qwen API Connection")
    print("=" * 60)
    
    # Display configuration
    print(f"\n📋 Configuration:")
    print(f"   Provider: {settings.llm_provider}")
    print(f"   Model: {settings.litellm_model}")
    print(f"   API Base: {settings.get_api_base()}")
    print(f"   API Key: {settings.get_api_key()[:10]}..." if settings.get_api_key() else "   API Key: NOT SET")
    
    # Create client
    print(f"\n🔧 Creating LLM client...")
    client = LLMClient()
    
    # Test simple completion
    print(f"\n🚀 Sending test request...")
    messages = [
        {"role": "system", "content": "You are a helpful coding assistant."},
        {"role":  "user", "content": "Say 'Hello!  I am working correctly.' in Chinese and English."}
    ]
    
    try:
        response = await client. get_completion(messages, max_tokens=100)
        print(f"\n✅ Response received:")
        print(f"   {response}")
        
        # Test token counting
        token_count = client.count_tokens(messages)
        print(f"\n📊 Token count: {token_count}")
        
        print(f"\n✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


async def test_orchestrator_model():
    """Test orchestrator model configuration."""
    print("\n" + "=" * 60)
    print("Testing Orchestrator Model")
    print("=" * 60)
    
    client = LLMClient(
        model=settings.get_model("orchestrator"),
        api_key=settings.get_api_key("orchestrator"),
        api_base=settings.get_api_base("orchestrator"),
    )
    
    print(f"\n📋 Orchestrator Config:")
    print(f"   Model: {settings.get_model('orchestrator')}")
    
    messages = [
        {"role": "user", "content": "List 3 advantages of multi-agent systems.  Be concise."}
    ]
    
    try:
        response = await client. get_completion(messages, max_tokens=200)
        print(f"\n✅ Response:  {response[: 100]}...")
        return True
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


async def test_subagent_model():
    """Test subagent model configuration."""
    print("\n" + "=" * 60)
    print("Testing Subagent Model")
    print("=" * 60)
    
    client = LLMClient(
        model=settings.get_model("subagent"),
        api_key=settings.get_api_key("subagent"),
        api_base=settings.get_api_base("subagent"),
    )
    
    print(f"\n📋 Subagent Config:")
    print(f"   Model: {settings.get_model('subagent')}")
    
    messages = [
        {"role": "user", "content": "What is 2+2?  Answer in one word."}
    ]
    
    try:
        response = await client.get_completion(messages, max_tokens=50)
        print(f"\n✅ Response: {response}")
        return True
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


async def main():
    """Run all tests."""
    results = []
    
    # Test basic connection
    results.append(await test_qwen_connection())
    
    # Test orchestrator model
    results.append(await test_orchestrator_model())
    
    # Test subagent model
    results.append(await test_subagent_model())
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Total tests:  {len(results)}")
    print(f"Passed: {sum(results)}")
    print(f"Failed: {len(results) - sum(results)}")
    
    if all(results):
        print("\n🎉 All tests passed!  System is ready.")
    else:
        print("\n⚠️  Some tests failed.  Please check your configuration.")


if __name__ == "__main__":
    asyncio.run(main())