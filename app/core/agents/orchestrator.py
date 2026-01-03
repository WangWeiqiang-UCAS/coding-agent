
"""Orchestrator Agent - coordinates tasks and subagents."""

import logging
import time
import uuid
from typing import Optional, Dict, Any

from app.llm.client import LLMClient
from app.core.storage.redis_store import RedisContextStore
from app.core.storage.task_store import TaskStore
from app.core.actions.parsing. parser import SimpleActionParser
from app.core.actions.parsing.handler import ActionHandler
from app.core.execution.command_executor import CommandExecutor
from app.core.actions.entities.actions import FinishAction
from app.config. settings import settings

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    """Orchestrator agent that coordinates multi-agent task execution."""
    
    def __init__(
        self,
        task_id: str,
        executor: CommandExecutor,
        context_store: RedisContextStore,
        task_store: TaskStore,
    ):
        """Initialize orchestrator. 
        
        Args:
            task_id: ID of the task to execute
            executor: Command executor
            context_store: Redis context store
            task_store: Redis task store
        """
        self.task_id = task_id
        self.agent_id = f"orca-{uuid.uuid4().hex[:8]}"
        self.executor = executor
        self.context_store = context_store
        self.task_store = task_store
        
        # Initialize components
        self.llm_client = LLMClient(
            model=settings.get_model("orchestrator"),
            api_key=settings.get_api_key("orchestrator"),
            api_base=settings.get_api_base("orchestrator"),
            temperature=settings. orca_orchestrator_temperature,
        )
        
        self.action_parser = SimpleActionParser()
        self.action_handler = ActionHandler(
            executor=executor,
            context_store=context_store,
            task_store=task_store,
        )
        
        # System message
        self.system_message = self._load_system_message()
        
        # Conversation history
        self.messages = []
        
        # State
        self.done = False
        self.finish_message = None
        self.start_time = None
    
    def _load_system_message(self) -> str:
        """Load orchestrator system message."""
        return """You are an expert coding orchestrator agent. Your role is to coordinate complex coding tasks by breaking them down and using available tools.

## Available Actions

You can use these XML-tagged actions: 

### File Operations
- <read>file_path:  path/to/file</read> - Read file content
- <write>file_path: path\ncontent:  file content here</write> - Write file
- <edit>file_path: path\nold_string: old\nnew_string: new</edit> - Edit file

### Execution
- <bash>cmd: command to run</bash> - Execute bash command
- <finish>completion message</finish> - Complete the task

### Search
- <grep>pattern: search_pattern\npath: directory</grep> - Search in files
- <glob>pattern: **. py\npath: directory</glob> - Find files

## Instructions

1. **Analyze the task** - Understand what needs to be done
2. **Explore the environment** - Use bash/grep/read to understand the codebase
3. **Plan your approach** - Break down the task into steps
4. **Execute systematically** - Implement changes step by step
5. **Verify your work** - Test that your changes work
6. **Finish** - Use <finish> when complete

## Important Notes

- Always verify file paths exist before reading/writing
- Test your changes after making them
- If stuck, explore the codebase structure
- Use <finish> when the task is complete or you need help

Begin your work now! """
    
    async def run(self, instruction: str, max_turns: int = 50) -> Dict[str, Any]:
        """Run the orchestrator until completion.
        
        Args:
            instruction: Task instruction
            max_turns: Maximum turns allowed
            
        Returns:
            Execution result dictionary
        """
        self.start_time = time.time()
        turns_executed = 0
        
        logger.info(f"[{self.agent_id}] Starting task: {instruction[: 50]}...")
        
        # Initialize conversation
        self.messages = [
            {"role": "system", "content":  self.system_message},
            {"role": "user", "content": f"Task: {instruction}\n\nStart working on this task now."}
        ]
        
        while not self.done and turns_executed < max_turns:
            turns_executed += 1
            elapsed = time.time() - self.start_time
            
            logger.info(f"[{self.agent_id}] Turn {turns_executed}/{max_turns} (elapsed: {elapsed:.1f}s)")
            
            try:
                # Get LLM response
                llm_output = await self.llm_client.get_completion(
                    messages=self. messages,
                    max_tokens=4096
                )
                
                logger.debug(f"[{self.agent_id}] LLM output: {llm_output[: 200]}...")
                
                # Add to history
                self.messages.append({"role": "assistant", "content": llm_output})
                
                # Parse actions
                actions, parse_errors = self.action_parser.parse(llm_output)
                
                if parse_errors:
                    logger.warning(f"[{self.agent_id}] Parse errors: {parse_errors}")
                
                # Execute actions
                if actions:
                    results = await self.action_handler.execute(actions)
                    
                    # Check for finish action
                    for action in actions:
                        if isinstance(action, FinishAction):
                            self.done = True
                            self.finish_message = action.message
                            logger.info(f"[{self.agent_id}] Task finished: {action.message}")
                            break
                    
                    # Add results to conversation
                    result_text = "\n\n".join(results)
                    if parse_errors:
                        result_text += f"\n\n⚠️ Parse errors:\n" + "\n".join(parse_errors)
                    
                    self.messages.append({
                        "role": "user",
                        "content": f"Action results:\n{result_text}\n\nContinue working or use <finish> when done."
                    })
                else:
                    # No actions parsed
                    self.messages.append({
                        "role": "user",
                        "content": "⚠️ No valid actions detected. Please use the XML format (e.g., <bash>cmd: ls</bash>) or <finish> if done."
                    })
                
            except Exception as e:
                logger.error(f"[{self.agent_id}] Error in turn {turns_executed}:  {e}")
                self.messages.append({
                    "role": "user",
                    "content": f"❌ Error occurred: {str(e)}\n\nPlease continue or use <finish> to report the issue."
                })
        
        # Handle max turns reached
        if not self.done:
            logger. warning(f"[{self.agent_id}] Max turns reached without finishing")
            self.finish_message = f"Task incomplete:  reached maximum turns ({max_turns})"
        
        elapsed_total = time.time() - self.start_time
        
        return {
            "completed": self.done,
            "finish_message": self.finish_message,
            "turns_executed": turns_executed,
            "elapsed_time": elapsed_total,
            "max_turns_reached": turns_executed >= max_turns
        }
