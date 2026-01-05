
"""Command executor for running bash commands."""


# async def _execute_single(self, action: Action) -> str:
# 当前写法: 如果新增一个 Action，必须修改这个 _execute_single 方法。
# 优化写法: 可以用一个字典映射 handler_map = {BashAction: self._handle_bash, ...} 来消除这一长串 if-else。

# cmd = f"echo '{escaped_content}' > {temp_file} && mv {temp_file} {action.file_path}"
# 风险 (Security):
# action.content.replace("'", "'\\''"): 这里试图转义单引号。
# 致命漏洞: 如果 content 里包含 '; rm -rf /; echo '，这简单的 replace 够用吗？
# （答案是不够的，这是经典的 Shell Injection 漏洞点）。


# cmd = f"sed -i 's/{old_escaped}/{new_escaped}/{flag}' {action.file_path}"
# 原理: 调用 Linux 的流编辑器 sed。
# 局限性: sed 使用正则表达式。如果 old_string 里包含了特殊的正则符号（比如 . 或 *），
# 而作者只转义了 /，那么匹配可能会失败或者产生意想不到的结果。



import asyncio
import logging
from typing import Tuple
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class CommandExecutor(ABC):
    """Abstract base class for command execution."""
    
    @abstractmethod
    async def execute(self, cmd: str, timeout: int = 300) -> Tuple[str, int]:
        """Execute a command. 
        
        Args:
            cmd: Command to execute
            timeout:  Timeout in seconds
            
        Returns:
            Tuple of (output, exit_code)
        """
        pass


class LocalExecutor(CommandExecutor):
    """Execute commands locally using subprocess."""
    
    def __init__(self, workspace_dir: str = "."):
        """Initialize executor. 
        
        Args:
            workspace_dir: Working directory for commands
        """
        self.workspace_dir = workspace_dir
    
    async def execute(self, cmd: str, timeout: int = 300) -> Tuple[str, int]:
        """Execute command locally.
        
        Args:
            cmd: Command to execute
            timeout: Timeout in seconds
            
        Returns:
            Tuple of (combined stdout/stderr, exit_code)
        """
        logger.debug(f"Executing: {cmd}")
        
        try:
            # 创建子进程
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio. subprocess.PIPE,
                cwd=self.workspace_dir
            )
            
            # 等待完成（带超时）
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            # 合并输出
            output = stdout.decode('utf-8', errors='replace')
            if stderr:
                error_output = stderr.decode('utf-8', errors='replace')
                if error_output. strip():
                    output += f"\n[STDERR]\n{error_output}"
            
            exit_code = process.returncode
            
            logger.debug(f"Command completed with exit code {exit_code}")
            
            return output, exit_code
            
        except asyncio.TimeoutError:
            logger.error(f"Command timed out after {timeout}s:  {cmd}")
            # 尝试杀死进程
            try:
                process.kill()
                await process.wait()
            except: 
                pass
            return f"❌ Command timed out after {timeout} seconds", 124
            
        except Exception as e: 
            logger.error(f"Command execution failed: {e}")
            return f"❌ Execution error: {str(e)}", 1
