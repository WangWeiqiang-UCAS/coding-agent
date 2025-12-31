"""Application configuration with multi-provider LLM support."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional, Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # --- LLM Provider ---
    # 增加别名，兼容 .env 中的 LM_PROVIDER 或 LLM_PROVIDER
    llm_provider: Literal["openai", "qwen", "azure", "anthropic"] = "qwen"
    
    # --- Qwen / Dashscope Configuration ---
    dashscope_api_key: Optional[str] = None
    qwen_api_base: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    
    # --- OpenAI Configuration ---
    openai_api_key: Optional[str] = None
    openai_api_base: str = "https://api.openai.com/v1"
    
    # --- General LLM Configuration ---
    litellm_model: str = "qwen/qwen-max"
    
    # --- Orchestrator Configuration ---
    orca_orchestrator_model: str = "qwen/qwen-max"
    orca_orchestrator_temperature: float = 0.1
    
    # --- Subagent Configuration ---
    orca_subagent_model: str = "qwen/qwen-plus"
    orca_subagent_temperature: float = 0.1
    
    # --- Redis Configuration ---
    redis_url: str = "redis://localhost:6379"
    redis_max_connections: int = 50
    
    # --- Application Configuration ---
    log_level: str = "INFO"
    max_turns: int = 50
    max_subagent_turns: int = 20
    workspace_dir: Path = Path("./workspace")
    
    # --- API Configuration ---
    api_title: str = "Multi-Agent Coding Assistant"
    api_version: str = "1.0.0"
    api_prefix: str = "/api/v1"
    
    # --- Execution Configuration ---
    command_timeout: int = 300
    max_env_response_chars: int = 12000

    # --- Pydantic 2.x 核心配置 ---
    # 使用 SettingsConfigDict 代替 class Config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # 不区分环境变量大小写
        extra="ignore",        # 关键！忽略 .env 中多余的变量，防止报错
    )
    
    def get_api_key(self, for_component: str = "default") -> str:
        """Get API key based on provider."""
        if self.llm_provider == "qwen":
            return self.dashscope_api_key or ""
        elif self.llm_provider == "openai":
            return self.openai_api_key or ""
        return ""
    
    def get_api_base(self, for_component: str = "default") -> Optional[str]:
        """Get API base URL based on provider."""
        if self.llm_provider == "qwen":
            return self.qwen_api_base
        elif self.llm_provider == "openai":
            return self.openai_api_base
        return None
    
    def get_model(self, for_component: str = "default") -> str:
        """Get model name based on component."""
        if for_component == "orchestrator":
            return self.orca_orchestrator_model
        elif for_component == "subagent":
            return self.orca_subagent_model
        return self.litellm_model


# 全局单例
try:
    settings = Settings()
except Exception as e:
    print(f"❌ 配置文件初始化失败: {e}")
    raise