"""LLM client with retry logic and multi-provider support."""

import asyncio
import logging
from typing import List, Dict, Optional
import litellm
from litellm import acompletion, token_counter
from litellm.exceptions import (
    InternalServerError,
    RateLimitError,
    APIError,
)

logger = logging.getLogger(__name__)

# Configure LiteLLM
litellm. drop_params = True  # 自动处理不支持的参数
litellm.suppress_debug_info = True  # 减少调试输出


class LLMClient:
    """Unified LLM client supporting multiple providers."""
    
    def __init__(
        self,
        model: str,
        api_key: str,
        api_base: Optional[str] = None,
        temperature: float = 0.1,
        max_retries: int = 5,
    ):
        """Initialize LLM client.
        
        Args:
            model: Model name (e.g., "qwen/qwen-max")
            api_key: API key for the provider
            api_base: Optional API base URL
            temperature: Sampling temperature
            max_retries:  Maximum retry attempts
        """
        self. model = model
        self.api_key = api_key
        self.api_base = api_base
        self.temperature = temperature
        self.max_retries = max_retries
        
        logger.info(
            f"LLMClient initialized:  model={self.model}, "
            f"api_base={self.api_base}"
        )
    
    async def get_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """Get completion from LLM with retry logic.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens in response
            temperature: Override default temperature
            **kwargs: Additional parameters
            
        Returns:
            LLM response text
            
        Raises:
            Exception: After all retries exhausted
        """
        temp = temperature if temperature is not None else self.temperature
        
        for attempt in range(self.max_retries):
            try:
                # Prepare request parameters
                request_params = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temp,
                    "max_tokens": max_tokens,
                    "custom_llm_provider": "dashscope",  # 显式指定供应商
                    "api_key": self.api_key,
                }
                
                # Add api_base if provided
                if self.api_base:
                    request_params["api_base"] = self.api_base
                
                # Make API call
                logger.debug(f"Calling LLM API (attempt {attempt + 1}/{self.max_retries})")
                response = await acompletion(**request_params)
                
                # Extract content
                content = response.choices[0].message.content
                
                logger.debug(f"LLM response received: {len(content)} chars")
                
                return content
                
            except (RateLimitError, InternalServerError, APIError) as e:
                wait_time = min(2 ** attempt, 60)  # Exponential backoff, max 60s
                logger.warning(
                    f"LLM API error (attempt {attempt + 1}/{self.max_retries}): {e}. "
                    f"Retrying in {wait_time}s..."
                )
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Max retries reached.  Last error: {e}")
                    raise
                    
            except Exception as e:
                logger.error(f"Unexpected error in LLM call: {e}")
                raise
    
    def count_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Count tokens in messages. 
        
        Args:
            messages: List of message dicts
            
        Returns:
            Total token count
        """
        try:
            return token_counter(model=self.model, messages=messages)
        except Exception as e: 
            logger.warning(f"Token counting failed: {e}. Using char estimation.")
            # Fallback:  estimate 1 token ≈ 4 characters
            total_chars = sum(len(m. get("content", "")) for m in messages)
            return total_chars // 4


# Convenience functions

async def get_llm_response(
    messages: List[Dict[str, str]],
    model: str,
    api_key: str,
    api_base: Optional[str] = None,
    temperature:  float = 0.1,
    max_tokens: int = 4096,
    **kwargs
) -> str:
    """Get LLM response with automatic retry. 
    
    This is a convenience function that creates a temporary client. 
    For better performance, create a LLMClient instance and reuse it.
    """
    client = LLMClient(
        model=model,
        api_key=api_key,
        api_base=api_base,
        temperature=temperature,
    )
    return await client.get_completion(messages, max_tokens, **kwargs)


def count_tokens(messages: List[Dict[str, str]], model: str) -> int:
    """Count tokens in messages."""
    try:
        return token_counter(model=model, messages=messages)
    except Exception: 
        # Fallback
        total_chars = sum(len(m.get("content", "")) for m in messages)
        return total_chars // 4