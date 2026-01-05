"""Orchestrator Agent with Long-Term Memory."""

import logging
import time
import uuid
from typing import Optional, Dict, Any, List

from app.llm.client import LLMClient
from app.core.storage.redis_store import RedisContextStore
from app.core.storage.task_store import TaskStore
from app.core.actions.parsing.parser import SimpleActionParser
from app.core.actions.parsing.handler import ActionHandler
from app.core.execution.command_executor import CommandExecutor
from app.core.actions.entities.actions import FinishAction, RecallAction
from app.core.agents.memory_manager import MemoryManager
from app.config.settings import settings
import redis.asyncio as redis

logger = logging.getLogger(__name__)

TASK_EXAMPLES = """
## Common Task Examples

### Example 1: Find all Python files in a directory
<glob>
pattern: *.py
path: app/core/
</glob>

### Example 2: Search for a pattern
<grep>
pattern: async def
path: app/
include:  "*.py"
</grep>

### Example 3: Write a multiline file
<write>
file_path: /tmp/summary.txt
content: |
  Project Analysis Summary
  
  Total files:  25
  Total lines: 3500
  
  Main components:
  - Parser:  handles action parsing
  - Handler: executes actions
  - Orchestrator: manages workflow
</write>

### Example 4: Read and analyze
<read>
file_path:  app/core/agents/orchestrator.py
</read>

After reading, provide analysis in your response.  

### Example 5: Complete task
<finish>
Analysis complete.  Found 15 Python files across 3 directories. 
Summary saved to /tmp/report.txt
</finish>

## Remember:  
- One parameter per line
- Use pipe | for multiline content
- Always use <finish> when done
"""

class OrchestratorAgent:
    """Orchestrator agent with long-term memory system."""
    
    MAX_ACTIVE_TURNS = 8
    MAX_CONTEXT_TOKENS = 25000
    TRUNCATE_ENV_RESPONSE = 2000
    SUMMARIZE_THRESHOLD = 10
    
    def __init__(
        self,
        task_id: str,
        executor: CommandExecutor,
        context_store: RedisContextStore,
        task_store: TaskStore,
        redis_client: redis.Redis,
        console=None,
    ):
        self.task_id = task_id
        self.agent_id = f"orca-{uuid.uuid4().hex[:8]}"
        self.executor = executor
        self.context_store = context_store
        self.task_store = task_store
        self.console = console
        
        self.llm_client = LLMClient(
            model=settings.get_model("orchestrator"),
            api_key=settings.get_api_key("orchestrator"),
            api_base=settings.get_api_base("orchestrator"),
            temperature=settings.orca_orchestrator_temperature,
        )
        
        self.memory_manager = MemoryManager(
            redis_client=redis_client,
            task_id=task_id,
            llm_client=self.llm_client
        )
        
        self.action_parser = SimpleActionParser()
        
        # FIX: Removed 'console=console' as ActionHandler does not accept it
        self.action_handler = ActionHandler(
            executor=executor,
            context_store=context_store,
            task_store=task_store
        )
        
        self.system_message = self._load_system_message()
        self.messages = []
        self.active_summaries = []
        self.done = False
        self.finish_message = None
        self.start_time = None
        self.current_turn = 0
    
    def _load_system_message(self) -> str:
        """Load orchestrator system message with file filtering guidance."""
        base_message = """You are an expert coding assistant with long-term memory capabilities. 

## Available Actions

### File Operations
- <read>file_path: path/to/file</read>
- <write>file_path: path\ncontent:  content</write>
- <edit>file_path: path\nold_string: old\nnew_string: new</edit>

### Execution
- <bash>cmd: command</bash>
- <finish>completion message</finish>

### Search (use quotes for patterns with *)
- <grep>pattern: "search_pattern"\npath: directory</grep>
- <glob>pattern: "**/*.py"\npath: directory</glob>

### Memory Management (NEW!)
- <recall>turn_range: "5-10"</recall> - Recall specific turns
- <recall>query: "login function"</recall> - Search memory

## Memory System

You have **long-term memory**:
- All conversation history is preserved
- When context is full, old turns are summarized but still accessible
- Use <recall> to retrieve past information:  
  * Recall specific turns:  `<recall>turn_range: "5-10"</recall>`
  * Search for topics: `<recall>query: "database schema"</recall>`

## Guidelines

1. For complex tasks spanning many steps, use memory:  
   - Early turns:  Explore and gather info
   - Later turns: Recall findings and implement
2. If you forget something from earlier, use <recall>
3. Work incrementally - you have unlimited turns
4. Use <finish> only when truly complete

## Critical Rules

1. After EVERY action, check if task is complete
2. If file created successfully, use <finish> immediately:  
   <finish>File /path/to/file created successfully</finish>
3. Do NOT retry the same action multiple times
4. Maximum 3 attempts per subtask

Begin working!  """
        return base_message + "\n\n" + TASK_EXAMPLES

    async def run(self, instruction: str, max_turns: int = 50) -> Dict[str, Any]:
        """Run the orchestrator until completion."""
        self.start_time = time.time()
        self.current_turn = 0
        
        logger.info(f"[{self.agent_id}] Starting task:  {instruction[:50]}...")
        
        if self.console:
            self.console.print(f"\n[dim]Starting task execution (max {max_turns} turns)...[/dim]\n")
        
        self.messages = [
            {"role": "system", "content": self.system_message},
            {"role": "user", "content": f"Task: {instruction}\n\nStart working on this task now."}
        ]
        
        while not self.done and self.current_turn < max_turns:  
            self.current_turn += 1
            elapsed = time.time() - self.start_time
            
            logger.info(f"[{self.agent_id}] Turn {self.current_turn}/{max_turns} (elapsed: {elapsed:.1f}s)")
            
            if self.console:
                self.console.print(f"[cyan]--- Turn {self.current_turn}/{max_turns} (elapsed: {elapsed:.1f}s) ---[/cyan]")
            
            try:
                await self._manage_memory()
                
                if self.console:
                    self.console.print("[dim]Calling LLM...[/dim]")
                
                llm_output = await self.llm_client.get_completion(
                    messages=self.messages,
                    max_tokens=4096
                )
                
                logger.debug(f"[{self.agent_id}] LLM output: {llm_output[:200]}...")
                
                if self.console:
                    thinking_text = self._extract_thinking(llm_output)
                    if thinking_text:
                        self.console.print(f"[blue]Agent:  {thinking_text}[/blue]")
                
                actions, parse_errors = self.action_parser.parse(llm_output)
                
                if parse_errors:
                    logger.warning(f"[{self.agent_id}] Parse errors: {parse_errors}")
                    if self.console:
                        for error in parse_errors[:2]: 
                            self.console.print(f"[yellow]Parse warning: {error}[/yellow]")
                
                if self.console and actions:
                    action_names = [type(a).__name__.replace("Action", "") for a in actions]
                    self.console.print(f"[green]Executing actions: {', '.join(action_names)}[/green]")
                
                recall_results = []
                other_actions = []
                
                for action in actions:
                    if isinstance(action, RecallAction):
                        result = await self._handle_recall(action)
                        recall_results.append(result)
                    else:
                        other_actions.append(action)
                
                action_results = []
                if other_actions:
                    action_results = await self.action_handler.execute(other_actions)
                
                for action in other_actions:
                    if isinstance(action, FinishAction):
                        self.done = True
                        self.finish_message = action.message
                        logger.info(f"[{self.agent_id}] Task finished: {action.message}")
                        if self.console:
                            self.console.print(f"[bold green]Task completed:  {action.message}[/bold green]\n")
                        break
                
                action_names = [type(a).__name__ for a in actions]
                
                all_results = recall_results + action_results
                result_text = self._format_results(all_results, parse_errors)
                
                await self.memory_manager.save_turn(
                    turn_num=self.current_turn,
                    user_message=self.messages[-1]["content"] if len(self.messages) > 1 else "",
                    assistant_message=llm_output,
                    actions_executed=action_names,
                    metadata={"elapsed":  elapsed}
                )
                
                self.messages.append({"role":  "assistant", "content": llm_output})
                
                if not self.done:
                    user_msg = {
                        "role": "user",
                        "content": f"{result_text}\n\n[Turn {self.current_turn}] Continue or <finish> when done."
                    }
                    self.messages.append(user_msg)
                
            except Exception as e:
                logger.error(f"[{self.agent_id}] Error in turn {self.current_turn}: {e}", exc_info=True)
                if self.console:
                    self.console.print(f"[red]Error:  {str(e)}[/red]")
                error_msg = {
                    "role": "user",
                    "content": f"Error:  {str(e)}\n\nContinue or <finish> to report issue."
                }
                self.messages.append(error_msg)
        
        if not self.done:
            logger.warning(f"[{self.agent_id}] Max turns reached")
            self.finish_message = f"Task incomplete:  reached maximum turns ({max_turns})"
            if self.console:
                self.console.print(f"[yellow]Task incomplete: reached maximum turns[/yellow]\n")
        
        elapsed_total = time.time() - self.start_time
        mem_stats = await self.memory_manager.get_memory_stats()
        
        return {
            "completed": self.done,
            "finish_message": self.finish_message,
            "turns_executed": self.current_turn,
            "elapsed_time": elapsed_total,
            "max_turns_reached": self.current_turn >= max_turns,
            "memory_stats": mem_stats
        }

    def _extract_thinking(self, llm_output: str) -> str:
        """Extract thinking text before first action tag."""
        if '<' not in llm_output:
            return llm_output.strip()[:200]
        
        first_tag_pos = llm_output.index('<')
        thinking = llm_output[:first_tag_pos].strip()
        
        if len(thinking) > 200:
            thinking = thinking[:200] + "..."
        
        return thinking

    async def _manage_memory(self):
        """Manage active context window."""
        active_messages = [m for m in self.messages if m.get("role") != "system"]
        
        if len(active_messages) <= self.MAX_ACTIVE_TURNS * 2:
            return
        
        logger.info(f"[{self.agent_id}] Managing memory:  {len(active_messages)} messages")
        
        if self.console:
            self.console.print("[dim]Summarizing old conversation turns...[/dim]")
        
        system_msg = self.messages[0]
        initial_task = self.messages[1]
        turns_to_keep = self.MAX_ACTIVE_TURNS * 2
        recent_messages = self.messages[-turns_to_keep:]
        
        middle_start = 2
        middle_end = len(self.messages) - turns_to_keep
        
        if middle_end > middle_start:
            start_turn = max(1, self.current_turn - len(self.messages) + middle_start)
            end_turn = self.current_turn - turns_to_keep // 2
            
            summary_text = await self.memory_manager.summarize_turns(start_turn, end_turn)
            await self.memory_manager.save_summary(f"{start_turn}-{end_turn}", summary_text)
            
            summary_msg = {
                "role": "user",
                "content": f"{summary_text}\n\n[Use <recall> to see details]"
            }
            
            self.messages = [system_msg, initial_task, summary_msg] + recent_messages
            
            logger.info(f"[{self.agent_id}] Summarized turns {start_turn}-{end_turn}")

    async def _handle_recall(self, action: RecallAction) -> str:
        """Handle recall action."""
        logger.info(f"[{self.agent_id}] Recall:  range={action.turn_range}, query={action.query}")
        
        if self.console:
            if action.turn_range:
                self.console.print(f"[dim]Recalling turns {action.turn_range}...[/dim]")
            elif action.query:
                self.console.print(f"[dim]Searching memory for: {action.query}[/dim]")
        
        if action.turn_range:
            try:
                start, end = map(int, action.turn_range.split("-"))
                turns = await self.memory_manager.get_turns_range(start, end)
                
                if not turns:
                    return f"No turns found in range {action.turn_range}"
                
                return self._format_recalled_turns(
                    turns, 
                    header=f"Recalled turns {action.turn_range}:",
                    truncate_len=300
                )
                
            except ValueError:  
                return f"Invalid turn range format: {action.turn_range} (use '5-10')"
        
        elif action.query:
            results = await self.memory_manager.search_memory(action.query, limit=action.limit)
            
            if not results:
                return f"No results found for query: {action.query}"
            
            return self._format_recalled_turns(
                results, 
                header=f"Search results for '{action.query}':",
                truncate_len=200
            )
        
        else:
            return "Recall requires either 'turn_range' or 'query'"

    def _format_recalled_turns(self, turns: List[Dict], header: str, truncate_len: int) -> str:
        """Helper to format a list of recalled turns."""
        lines = [header]
        for turn in turns:
            lines.append(f"\n**Turn {turn['turn_num']}:**")
            lines.append(f"Actions: {', '.join(turn['actions'])}")
            snippet = turn['assistant'][:truncate_len]
            if len(turn['assistant']) > truncate_len:
                snippet += "..."
            lines.append(f"Result: {snippet}")
        return "\n".join(lines)

    def _format_results(self, results: List[str], parse_errors: List[str]) -> str:
        """Format execution results with truncation."""
        formatted:  List[str] = []

        for result in results:
            if len(result) > self.TRUNCATE_ENV_RESPONSE: 
                truncated = result[:self.TRUNCATE_ENV_RESPONSE]
                formatted.append(f"{truncated}\n\n[...  Output truncated ...]")
            else:
                formatted.append(result)

        result_text = "\n\n".join(formatted)

        if parse_errors:
            error_summary = "\n".join(parse_errors[:3])
            if len(parse_errors) > 3:
                error_summary += f"\n...  and {len(parse_errors) - 3} more"
            result_text += f"\n\nParse errors:\n{error_summary}"

        return result_text