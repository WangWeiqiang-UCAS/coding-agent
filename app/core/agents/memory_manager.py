"""Long-term memory management for agents."""

import logging
import json
from typing import List, Dict, Optional
import time
import redis.asyncio as redis

from app.llm.client import LLMClient

logger = logging.getLogger(__name__)


class MemoryManager:
    """Manages long-term memory storage and retrieval for agents."""
    
    def __init__(
        self,
        redis_client: redis.Redis,
        task_id: str,
        llm_client: Optional[LLMClient] = None
    ):
        """Initialize memory manager.
        
        Args:
            redis_client: Redis connection
            task_id: Task identifier
            llm_client: LLM client for summarization (optional)
        """
        self.redis = redis_client
        self.task_id = task_id
        self.llm_client = llm_client
        
        # Redis keys
        self.turn_key_prefix = f"memory:{task_id}:turn:"
        self.summary_key = f"memory:{task_id}:summary"
        self.metadata_key = f"memory:{task_id}:metadata"
    
    async def save_turn(
        self,
        turn_num: int,
        user_message: str,
        assistant_message: str,
        actions_executed: List[str],
        metadata: Optional[Dict] = None
    ):
        """Save a conversation turn to long-term memory.
        
        Args:
            turn_num: Turn number
            user_message: User message content
            assistant_message: Assistant response
            actions_executed: List of action names executed
            metadata: Optional metadata (e.g., tokens used, time elapsed)
        """
        turn_data = {
            "turn_num": turn_num,
            "timestamp": time.time(),
            "user": user_message,
            "assistant": assistant_message,
            "actions": actions_executed,
            "metadata":metadata or {}
        }
        
        key = f"{self.turn_key_prefix}{turn_num}"
        
        # Store as JSON
        await self.redis.set(key, json.dumps(turn_data))
        
        # Set expiration (30 days)
        await self.redis.expire(key, 2592000)
        
        # Update metadata
        await self._update_metadata(turn_num)
        
        logger.debug(f"Saved turn {turn_num} to long-term memory")
    
    async def get_turn(self, turn_num: int) -> Optional[Dict]:
        """Retrieve a specific turn from memory.
        
        Args:
            turn_num: Turn number to retrieve
            
        Returns:
            Turn data or None if not found
        """
        key = f"{self.turn_key_prefix}{turn_num}"
        data = await self.redis.get(key)
        
        if data:
            return json.loads(data)
        return None
    
    async def get_turns_range(self, start: int, end: int) -> List[Dict]:
        """Get a range of turns.
        
        Args:
            start: Start turn number (inclusive)
            end: End turn number (inclusive)
            
        Returns:
            List of turn data
        """
        turns = []
        
        for turn_num in range(start, end + 1):
            turn = await self.get_turn(turn_num)
            if turn:
                turns.append(turn)
        
        return turns
    
    async def get_all_turns(self) -> List[Dict]:
        """Get all stored turns.
        
        Returns:
            List of all turn data
        """
        metadata = await self._get_metadata()
        max_turn = metadata.get("max_turn", 0)
        
        if max_turn == 0:
            return []
        
        return await self.get_turns_range(1, max_turn)
    
    async def summarize_turns(self, start: int, end: int) -> str:
        """Generate a summary of a range of turns.
        
        Args:
            start: Start turn number
            end: End turn number
            
        Returns:
            Summary text
        """
        turns = await self.get_turns_range(start, end)
        
        if not turns:
            return f"No turns found in range {start}-{end}"
        
        # If no LLM client, return simple summary
        if not self.llm_client:
            return self._simple_summary(turns, start, end)
        
        # Use LLM to generate intelligent summary
        return await self._llm_summary(turns, start, end)
    
    def _simple_summary(self, turns: List[Dict], start: int, end: int) -> str:
        """Generate simple summary without LLM.
        
        Args:
            turns: List of turn data
            start: Start turn
            end: End turn
            
        Returns:
            Simple text summary
        """
        lines = [f"[Summary of turns {start}-{end}]"]
        
        for turn in turns:
            actions = ", ".join(turn["actions"]) if turn["actions"] else "thinking"
            lines.append(f"Turn {turn['turn_num']}: {actions}")
        
        return "\n".join(lines)
    
    async def _llm_summary(self, turns: List[Dict], start: int, end: int) -> str:
        """Generate intelligent summary using LLM.
        
        Args:
            turns: List of turn data
            start: Start turn
            end: End turn
            
        Returns:
            LLM-generated summary
        """
        # Build context for summarization
        context_parts = []
        
        for turn in turns:
            context_parts.append(f"Turn {turn['turn_num']}:")
            context_parts.append(f"Actions: {', '.join(turn['actions'])}")
            
            # Include truncated messages
            assistant_preview = turn['assistant'][:300]
            context_parts.append(f"Result: {assistant_preview}...")
            context_parts.append("")
        
        context = "\n".join(context_parts)
        
        # Summarization prompt
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that summarizes conversation history concisely."
            },
            {
                "role": "user",
                "content": f"""Summarize the following agent conversation turns ({start}-{end}).
Focus on: 
1. What actions were taken
2. Key findings or results
3. Any important files/data discovered

Keep it under 200 words. 

{context}

Summary:"""
            }
        ]
        
        try:
            summary = await self.llm_client.get_completion(messages, max_tokens=500)
            return f"[Summary of turns {start}-{end}]\n{summary}"
        except Exception as e:
            logger.error(f"LLM summarization failed: {e}")
            return self._simple_summary(turns, start, end)
    
    async def save_summary(self, turn_range: str, summary: str):
        """Save a generated summary.
        
        Args:
            turn_range: Range identifier (e.g., "1-10")
            summary: Summary text
        """
        summaries = await self._get_summaries()
        summaries[turn_range] = {
            "summary": summary,
            "timestamp": time.time()
        }
        
        await self.redis.set(self.summary_key, json.dumps(summaries))
        await self.redis.expire(self.summary_key, 2592000)
    
    async def get_summary(self, turn_range: str) -> Optional[str]:
        """Get a saved summary.
        
        Args:
            turn_range: Range identifier
            
        Returns:
            Summary text or None
        """
        summaries = await self._get_summaries()
        summary_data = summaries.get(turn_range)
        
        if summary_data:
            return summary_data["summary"]
        return None
    
    async def search_memory(self, query: str, limit: int = 5) -> List[Dict]:
        """Search memory for relevant turns (simple keyword search).
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of relevant turns
        """
        all_turns = await self.get_all_turns()
        results = []
        query_lower = query.lower()
        
        for turn in all_turns:
            # Search in user message, assistant message, and actions
            content = (
                turn["user"].lower() + " " +
                turn["assistant"].lower() + " " +
                " ".join(turn["actions"]).lower()
            )
            
            if query_lower in content:
                results.append(turn)
            
            if len(results) >= limit:
                break
        
        return results
    
    async def _update_metadata(self, turn_num: int):
        """Update task metadata.
        
        Args:
            turn_num: Current turn number
        """
        metadata = await self._get_metadata()
        metadata["max_turn"] = max(metadata.get("max_turn", 0), turn_num)
        metadata["last_updated"] = time.time()
        
        await self.redis.set(self.metadata_key, json.dumps(metadata))
        await self.redis.expire(self.metadata_key, 2592000)
    
    async def _get_metadata(self) -> Dict:
        """Get task metadata.
        
        Returns:
            Metadata dictionary
        """
        data = await self.redis.get(self.metadata_key)
        
        if data:
            return json.loads(data)
        return {}
    
    async def _get_summaries(self) -> Dict:
        """Get all summaries.
        
        Returns:
            Dictionary of summaries
        """
        data = await self.redis.get(self.summary_key)
        
        if data:
            return json.loads(data)
        return {}
    
    async def get_memory_stats(self) -> Dict:
        """Get memory statistics.
        
        Returns:
            Statistics dictionary
        """
        metadata = await self._get_metadata()
        summaries = await self._get_summaries()
        
        return {
            "total_turns":metadata.get("max_turn", 0),
            "summaries_count": len(summaries),
            "last_updated":metadata.get("last_updated", 0)
        }