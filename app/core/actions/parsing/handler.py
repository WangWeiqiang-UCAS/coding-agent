"""Action handler with improved write and verification."""

import logging
import asyncio
from typing import List, Optional, Dict, Callable, Awaitable
import uuid
import tempfile
import os

from app.core.actions.entities.actions import (
    Action, BashAction, ReadAction, WriteAction, EditAction,
    GrepAction, GlobAction, FinishAction,
    TaskCreateAction, LaunchSubagentAction, ReportAction, RecallAction
)
from app.core.execution.command_executor import CommandExecutor

logger = logging.getLogger(__name__)


class ActionHandler:
    """Execute parsed actions using dispatch pattern."""
    
    def __init__(
        self,
        executor: CommandExecutor,
        context_store=None,
        task_store=None,
    ):
        self.executor = executor
        self.context_store = context_store
        self.task_store = task_store
        
        self._action_handlers: Dict[type, Callable[[Action], Awaitable[str]]] = {
            BashAction: self._handle_bash,
            ReadAction: self._handle_read,
            WriteAction: self._handle_write,
            EditAction: self._handle_edit,
            GrepAction: self._handle_grep,
            GlobAction: self._handle_glob,
            FinishAction: self._handle_finish,
            TaskCreateAction: self._handle_task_create,
            LaunchSubagentAction: self._handle_launch_subagent,
            ReportAction: self._handle_report,
        }
    
    async def execute(self, actions: List[Action]) -> List[str]:
        """Execute a list of actions."""
        results = []
        
        for action in actions:
            try:
                result = await self._execute_single(action)
                results.append(result)
            except Exception as e:
                error_msg = f"Error executing {type(action).__name__}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                results.append(f"❌ {error_msg}")
        
        return results
    
    async def _execute_single(self, action: Action) -> str:
        """Execute a single action using dispatch pattern."""
        handler = self._action_handlers.get(type(action))
        
        if handler:
            return await handler(action)
        else:
            logger.warning(f"Unknown action type: {type(action).__name__}")
            return f"⚠️ Unknown action type: {type(action).__name__}"
    
    def register_handler(self, action_type: type, handler: Callable) -> None:
        """Register a custom action handler."""
        self._action_handlers[action_type] = handler
        logger.info(f"Registered handler for {action_type.__name__}")
    
    async def _handle_bash(self, action: BashAction) -> str:
        """Execute bash command."""
        logger.info(f"Executing bash: {action.cmd[:100]}")
        
        output, exit_code = await self.executor.execute(
            action.cmd,
            timeout=action.timeout_secs
        )
        
        if exit_code == 0:
            return f"✅ Command executed successfully:\n{output}"
        else:
            return f"❌ Command failed (exit code {exit_code}):\n{output}"
    
    async def _handle_read(self, action: ReadAction) -> str:
        """Read file content."""
        logger.info(f"Reading file: {action.file_path}")
        
        cmd = f"cat {action.file_path}"
        
        if action.offset or action.limit:
            start = action.offset or 1
            end = start + action.limit - 1 if action.limit else "$"
            cmd = f"sed -n '{start},{end}p' {action.file_path}"
        
        output, exit_code = await self.executor.execute(cmd)
        
        if exit_code == 0:
            line_count = len(output.splitlines())
            return f"📄 File: {action.file_path} ({line_count} lines)\n```\n{output}\n```"
        else:
            return f"❌ Failed to read file: {output}"
    
    async def _handle_write(self, action: WriteAction) -> str:
        """Write content to file with robust method."""
        logger.info(f"Writing file: {action.file_path}")
        logger.debug(f"Content length: {len(action.content)} chars")
        logger.debug(f"Content preview: {action.content[:100]}")
        
        # 🔥 检查内容是否为空
        if not action.content or action.content.strip() == "":
            logger.warning("WriteAction received EMPTY content!")
            return f"❌ Write failed: content is empty"
        
        try:
            # Method 1: Direct Python write
            parent_dir = os.path.dirname(action.file_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            
            with open(action.file_path, 'w', encoding='utf-8') as f:
                f.write(action.content)
            
            # 🔥 严格验证
            if not os.path.exists(action.file_path):
                raise Exception(f"File does not exist after write: {action.file_path}")
            
            file_size = os.path.getsize(action.file_path)
            
            if file_size == 0:
                raise Exception(f"File is empty after write: {action.file_path}")
            
            # 验证内容
            with open(action.file_path, 'r', encoding='utf-8') as f:
                written_content = f.read()
            
            if written_content != action.content:
                logger.warning(f"Content mismatch! Expected {len(action.content)} bytes, got {len(written_content)} bytes")
            
            line_count = len(action.content.splitlines())
            return f"✅ File written: {action.file_path} ({file_size} bytes, {line_count} lines)"
            
        except Exception as e:
            logger.error(f"Python write failed: {e}")
            
            # Fallback: Bash method
            logger.info("Trying fallback bash method...")
            
            try:
                # Create temp file
                with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as tmp:
                    tmp.write(action.content)
                    temp_path = tmp.name
                
                # Move to target
                cmd = f"mkdir -p $(dirname {action.file_path}) && mv {temp_path} {action.file_path}"
                output, exit_code = await self.executor.execute(cmd)
                
                if exit_code == 0:
                    # Verify
                    verify_cmd = f"test -f {action.file_path} && wc -c {action.file_path}"
                    verify_output, verify_code = await self.executor.execute(verify_cmd)
                    
                    if verify_code == 0:
                        return f"✅ File written (via bash): {action.file_path}\n{verify_output}"
                    else:
                        return f"⚠️ File written but verification failed: {action.file_path}"
                else:
                    return f"❌ Failed to write file: {output}"
            except Exception as e2:
                logger.error(f"Bash fallback also failed: {e2}")
                return f"❌ All write methods failed: {str(e)} | {str(e2)}"
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
    
    async def _handle_edit(self, action: EditAction) -> str:
        """Edit file by string replacement."""
        logger.info(f"Editing file: {action.file_path}")
        
        old_escaped = action.old_string.replace("/", "\\/").replace("&", "\\&")
        new_escaped = action.new_string.replace("/", "\\/").replace("&", "\\&")
        flag = "g" if action.replace_all else ""
        
        cmd = f"sed -i 's/{old_escaped}/{new_escaped}/{flag}' {action.file_path}"
        
        output, exit_code = await self.executor.execute(cmd)
        
        if exit_code == 0:
            return f"✅ File edited: {action.file_path}"
        else:
            return f"❌ Failed to edit file: {output}"
    
    async def _handle_grep(self, action: GrepAction) -> str:
        """Search for pattern in files."""
        logger.info(f"Searching for pattern: {action.pattern}")
        
        cmd = f"grep -rn '{action.pattern}' {action.path}"
        
        if action.include:
            cmd += f" --include='{action.include}'"
        
        output, exit_code = await self.executor.execute(cmd)
        
        if exit_code == 0:
            match_count = len(output.splitlines())
            if match_count > 50:
                lines = output.splitlines()[:50]
                output = "\n".join(lines) + f"\n... ({match_count - 50} more matches)"
            return f"🔍 Found {match_count} matches:\n{output}"
        elif exit_code == 1:
            return f"🔍 No matches found for pattern: {action.pattern}"
        else:
            return f"❌ Search failed: {output}"
    
    async def _handle_glob(self, action: GlobAction) -> str:
        """Find files matching pattern."""
        logger.info(f"Finding files: {action.pattern}")
        
        cmd = f"find {action.path} -name '{action.pattern}'"
        
        output, exit_code = await self.executor.execute(cmd)
        
        if exit_code == 0:
            file_count = len(output.splitlines())
            if file_count > 100:
                lines = output.splitlines()[:100]
                output = "\n".join(lines) + f"\n... ({file_count - 100} more files)"
            return f"📁 Found {file_count} files:\n{output}"
        else:
            return f"❌ Find failed: {output}"
    
    async def _handle_finish(self, action: FinishAction) -> str:
        """Mark task as complete."""
        logger.info(f"Task finished: {action.message}")
        return f"✅ FINISHED: {action.message}"
    
    async def _handle_task_create(self, action: TaskCreateAction) -> str:
        """Create a task for subagent."""
        logger.info(f"Creating task: {action.title}")
        
        if not self.task_store:
            return "⚠️ Task store not available"
        
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        
        await self.task_store.create_task(
            task_id=task_id,
            agent_type=action.agent_type,
            title=action.title,
            description=action.description,
            max_turns=action.max_turns,
            context_refs=action.context_refs,
            context_bootstrap=action.context_bootstrap,
        )
        
        return f"✅ Task created: {task_id} - {action.title}"
    
    async def _handle_launch_subagent(self, action: LaunchSubagentAction) -> str:
        """Launch a subagent (placeholder)."""
        logger.info(f"Launching subagent for task: {action.task_id}")
        return f"⚠️ Subagent launching not yet implemented (task: {action.task_id})"
    
    async def _handle_report(self, action: ReportAction) -> str:
        """Handle subagent report."""
        logger.info(f"Received report with {len(action.contexts)} contexts")
        return f"✅ Report received: {len(action.contexts)} contexts"