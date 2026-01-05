"""Main CLI application using Click."""

import asyncio
import click
from rich. console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.markdown import Markdown
import time

from app.cli.agent_runner import AgentRunner
from app. cli.history_manager import HistoryManager
from app.config.settings import settings

console = Console()


@click.  group()
@click.version_option(version="1.0.0")
def cli():
    """🤖 Coding Agent - Your AI-powered coding assistant."""
    pass


@cli.command()
@click.argument('instruction', nargs=-1, required=True)
@click.option('--max-turns', default=20, help='Maximum turns for agent execution')
@click. option('--workspace', default='.', help='Working directory')
@click.option('--verbose', is_flag=True, help='Show detailed logs')
def run(instruction, max_turns, workspace, verbose):
    """Run a coding task. 
    
    Example:
        coding-agent run "Create a Python function to calculate factorial"
        coding-agent run "Fix bugs in app.py" --workspace ./my-project
    """
    instruction_text = " ".join(instruction)
    
    console.print(Panel. fit(
        f"[bold cyan]🤖 Coding Agent[/bold cyan]\n"
        f"[yellow]Task:[/yellow] {instruction_text}\n"
        f"[dim]Workspace:[/dim] {workspace}",
        border_style="cyan"
    ))
    
    # 运行 Agent
    runner = AgentRunner(workspace=workspace, verbose=verbose)
    result = asyncio.run(runner.run_task(instruction_text, max_turns))
    
    # 显示结果
    console.print()
    if result["completed"]: 
        console.print(f"[bold green]✅ Task Completed![/bold green]")
        console.print(f"[green]{result['finish_message']}[/green]")
    else:
        console.print(f"[bold red]❌ Task Failed[/bold red]")
        console.print(f"[red]{result['finish_message']}[/red]")
    
    console.  print(f"\n[dim]⏱️  Time: {result['elapsed_time']:.1f}s  |  🔄 Turns: {result['turns_executed']}[/dim]")
    
    # 保存历史
    history_mgr = HistoryManager()
    history_mgr.save(instruction_text, result)
    console.print(f"[dim]💾 Saved to history (ID: {result['task_id']})[/dim]")


@cli.command()
@click.option('--limit', default=10, help='Number of recent tasks to show')
def history(limit):
    """Show task execution history. 
    
    Example:
        coding-agent history
        coding-agent history --limit 20
    """
    history_mgr = HistoryManager()
    tasks = history_mgr.list(limit=limit)
    
    if not tasks:
        console.print("[yellow]No task history found.[/yellow]")
        return
    
    table = Table(title="📜 Task History", show_header=True, header_style="bold magenta")
    table.add_column("ID", style="cyan", width=12)
    table.add_column("Task", style="white", width=40)
    table.add_column("Status", width=10)
    table.add_column("Time", style="dim", width=10)
    table.add_column("Date", style="dim", width=20)
    
    for task in tasks:
        status_color = "green" if task['completed'] else "red"
        status_icon = "✅" if task['completed'] else "❌"
        
        table.add_row(
            task['task_id'][:  12],
            task['instruction'][:40] + "..." if len(task['instruction']) > 40 else task['instruction'],
            f"[{status_color}]{status_icon}[/{status_color}]",
            f"{task. get('elapsed_time', 0):.1f}s",
            task['timestamp']
        )
    
    console.print(table)


@cli.command()
@click.argument('task_id')
def status(task_id):
    """Show detailed status of a specific task.
    
    Example:
        coding-agent status task_abc12345
    """
    history_mgr = HistoryManager()
    task = history_mgr.get(task_id)
    
    if not task:
        console. print(f"[red]❌ Task {task_id} not found[/red]")
        return
    
    # 显示详细信息
    console.print(Panel.fit(
        f"[bold cyan]Task Details[/bold cyan]\n\n"
        f"[yellow]ID:[/yellow] {task['task_id']}\n"
        f"[yellow]Instruction:[/yellow] {task['instruction']}\n"
        f"[yellow]Status:[/yellow] {'✅ Completed' if task['completed'] else '❌ Failed'}\n"
        f"[yellow]Turns:[/yellow] {task['turns_executed']}\n"
        f"[yellow]Time:[/yellow] {task. get('elapsed_time', 0):.1f}s\n"
        f"[yellow]Date:[/yellow] {task['timestamp']}\n\n"
        f"[yellow]Result:[/yellow]\n{task['finish_message']}",
        border_style="cyan"
    ))


@cli.command()
def chat():
    """Start interactive chat mode. 
    
    Example:
        coding-agent chat
    """
    console.print(Panel.fit(
        "[bold cyan]🤖 Interactive Chat Mode[/bold cyan]\n"
        "[dim]Type 'exit' or 'quit' to leave[/dim]",
        border_style="cyan"
    ))
    
    runner = AgentRunner(workspace='. ', verbose=False)
    
    while True:
        try: 
            console.print()
            instruction = console.input("[bold green]You:[/bold green] ")
            
            if instruction.lower() in ['exit', 'quit', 'q']:
                console. print("[yellow]👋 Goodbye![/yellow]")
                break
            
            if not instruction. strip():
                continue
            
            console.print("[bold cyan]Agent:[/bold cyan] ", end="")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("Thinking.. .", total=None)
                result = asyncio.run(runner.run_task(instruction, max_turns=10))
            
            if result["completed"]: 
                console.print(f"[green]{result['finish_message']}[/green]")
            else:
                console.print(f"[yellow]{result['finish_message']}[/yellow]")
                
        except KeyboardInterrupt: 
            console.print("\n[yellow]👋 Goodbye![/yellow]")
            break
        except Exception as e:
            console.print(f"[red]❌ Error: {e}[/red]")


@cli.command()
def config():
    """Show current configuration.
    
    Example:
        coding-agent config
    """
    table = Table(title="⚙️  Configuration", show_header=True, header_style="bold magenta")
    table.add_column("Setting", style="cyan", width=30)
    table.add_column("Value", style="white", width=50)
    
    table.add_row("LLM Provider", settings.llm_provider)
    table.add_row("Orchestrator Model", settings. orca_orchestrator_model)
    table.add_row("Subagent Model", settings. orca_subagent_model)
    table.add_row("Redis URL", settings.redis_url)
    table.add_row("Workspace", str(settings.workspace_dir))
    table.add_row("Max Turns", str(settings.max_turns))
    table.add_row("Log Level", settings.log_level)
    
    console.print(table)


if __name__ == "__main__":
    cli()

@cli.command()
@click.argument('template_name')
@click.option('--file', required=True, help='Target file')
@click.option('--max-turns', default=20)
def template(template_name, file, max_turns):
    """Use a built-in template. 
    
    Available templates:
        refactor  - Refactor code
        test      - Generate tests
        doc       - Generate documentation
        fix       - Fix bugs
        optimize  - Optimize performance
        security  - Security audit
    
    Example:
        coding-agent template refactor --file app.py
        coding-agent template test --file utils.py
    """
    from app.cli.templates import get_template
    
    try:
        instruction = get_template(template_name, file=file)
        console.print(f"[cyan]Using template:[/cyan] {template_name}")
        console.print(f"[dim]Instruction:  {instruction}[/dim]\n")
        
        # 复用 run 命令逻辑
        from click.testing import CliRunner
        runner_obj = CliRunner()
        result = runner_obj.invoke(run, [instruction, '--max-turns', str(max_turns)])
        
    except ValueError as e:
        console.print(f"[red]❌ {e}[/red]")


@cli.command()
def templates():
    """List available templates."""
    from app.cli.templates import TEMPLATES
    
    table = Table(title="📝 Available Templates", show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan", width=15)
    table.add_column("Description", style="white", width=60)
    
    for name, description in TEMPLATES.items():
        table.add_row(name, description)
    
    console.print(table)
    console.print("\n[dim]Usage:  coding-agent template <name> --file <path>[/dim]")
@cli.command()
@click.argument('project_name')
@click.option('--type', 'project_type', 
              type=click.Choice(['fastapi', 'flask', 'cli', 'library']),
              default='library',
              help='Project type')
def init(project_name, project_type):
    """Initialize a new project with Agent's help. 
    
    Example:
        coding-agent init my-api --type fastapi
        coding-agent init my-tool --type cli
    """
    instructions = {
        'fastapi': f"""创建一个 FastAPI 项目 {project_name}：
1. 创建项目结构（app/, tests/, requirements.txt）
2. 实现基础 API（health check, CRUD 示例）
3. 添加 Dockerfile 和 docker-compose. yml
4. 创建 README 说明文档""",
        
        'flask': f"""创建一个 Flask 项目 {project_name}：
1. 创建项目结构（app. py, templates/, static/）
2. 实现基础路由和模板
3. 添加配置管理
4. 创建 README""",
        
        'cli':  f"""创建一个 CLI 工具项目 {project_name}：
1. 使用 Click 框架创建命令行工具
2. 实现基础命令（--help, --version）
3. 添加 setup.py 用于安装
4. 创建 README 和使用示例""",
        
        'library': f"""创建一个 Python 库项目 {project_name}：
1. 创建标准项目结构（src/, tests/, docs/）
2. 添加 setup.py 和 pyproject. toml
3. 实现示例模块
4. 创建 README 和文档"""
    }
    
    instruction = instructions[project_type]
    
    console.print(Panel. fit(
        f"[bold cyan]🚀 Initializing {project_type} project[/bold cyan]\n"
        f"[yellow]Name:[/yellow] {project_name}",
        border_style="cyan"
    ))
    
    # 执行
    runner = AgentRunner(workspace='. ', verbose=False)
    result = asyncio.run(runner.run_task(instruction, max_turns=30))
    
    if result["completed"]:
        console.print(f"\n[bold green]✅ Project initialized![/bold green]")
        console.print(f"[green]Location: . /{project_name}[/green]")
        console.print(f"\n[dim]Next steps:[/dim]")
        console.print(f"  cd {project_name}")
        console.print(f"  # Follow instructions in README.md")
    else:
        console.print(f"\n[bold red]❌ Initialization failed[/bold red]")
        console.print(f"[red]{result['finish_message']}[/red]")
@cli.command()
@click.argument('task_id')
def memory(task_id):
    """View long-term memory for a task. 
    
    Example:
        coding-agent memory cli_abc12345
    """
    async def show_memory():
        import redis.asyncio as redis
        from app.core.agents.memory_manager import MemoryManager
        
        r = await redis.from_url(settings.redis_url, decode_responses=True)
        
        try:
            memory_mgr = MemoryManager(r, task_id)
            
            # Get stats
            stats = await memory_mgr.get_memory_stats()
            
            console.print(Panel.fit(
                f"[bold cyan]🧠 Memory for {task_id}[/bold cyan]\n\n"
                f"[yellow]Total Turns:[/yellow] {stats['total_turns']}\n"
                f"[yellow]Summaries:[/yellow] {stats['summaries_count']}\n"
                f"[yellow]Last Updated:[/yellow] {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stats. get('last_updated', 0)))}",
                border_style="cyan"
            ))
            
            # Get all turns
            turns = await memory_mgr.get_all_turns()
            
            if not turns:
                console.print("[yellow]No memory found for this task.[/yellow]")
                return
            
            # Display turns table
            table = Table(title="💾 Conversation Turns", show_header=True, header_style="bold magenta")
            table.add_column("Turn", style="cyan", width=6)
            table.add_column("Actions", style="white", width=30)
            table.add_column("Time", style="dim", width=10)
            
            for turn in turns[: 20]:  # Show first 20
                actions_str = ", ".join(turn['actions'][:3])
                if len(turn['actions']) > 3:
                    actions_str += f" +{len(turn['actions'])-3}"
                
                elapsed = turn. get('metadata', {}).get('elapsed', 0)
                
                table.add_row(
                    str(turn['turn_num']),
                    actions_str,
                    f"{elapsed:.1f}s"
                )
            
            console.print(table)
            
            if len(turns) > 20:
                console.print(f"[dim]... and {len(turns)-20} more turns[/dim]")
        
        finally:
            await r.close()
    
    asyncio.run(show_memory())
