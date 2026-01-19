# Coding Agent

一个基于大语言模型的智能编码助手，支持长期记忆、多轮对话和复杂任务执行。

## 特性

- **长期记忆系统** - 使用 Redis 存储对话历史，突破上下文窗口限制
- **Action 驱动** - 通过结构化 XML Action 与环境交互
- **多 LLM 支持** - 支持通义千问、OpenAI、Azure OpenAI 等多种模型
- **CLI ** - 提供命令行工具的使用方式
- **实时反馈** - verbose 模式下显示 Agent 执行的每一步操作
- **任务模板** - 内置常用任务模板（文档生成、测试、重构等）

## 三种使用方式

### 方式一：Docker 一键启动（最简单）

```bash
# 下载启动脚本并运行
curl -fsSL https://raw.githubusercontent.com/WangWeiqiang-UCAS/coding-agent/main/quick-start.sh | bash

# 使用
docker-compose exec agent coding-agent run "你的任务" --verbose
```
### 方式二：使用 Docker 镜像
```bash
# 1. 拉取镜像
docker pull wangweiqiang/coding-agent:latest

# 2. 启动 Redis
docker run -d --name coding-agent-redis -p 6379:6379 redis:7-alpine

# 3. 启动 Agent
docker run -d \
  --name coding-agent \
  --link coding-agent-redis:redis \
  -p 8000:8000 \
  -e DASHSCOPE_API_KEY=your_api_key_here \
  -e REDIS_URL=redis://redis:6379 \
  wangweiqiang/coding-agent:latest

# 4. 使用
docker exec -it coding-agent coding-agent run "你的任务" --verbose
```

### 方式三：从源码安装（开发者）
```bash
git clone https://github.com/WangWeiqiang-UCAS/coding-agent.git
cd coding-agent
pip install -e . 
# 配置 .env 后使用
coding-agent run "你的任务" --verbose
```
本地安装
```bash
# 1. 安装依赖
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. 启动 Redis
docker run -d -p 6379:6379 redis:7-alpine

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 API Key

# 4. 安装 CLI
pip install -e .

# 5. 使用
coding-agent run "创建一个 Python 函数计算斐波那契数列" --verbose
```
使用示例
基础任务执行
```bash
# 简单任务
coding-agent run "列出当前目录的所有 Python 文件"

# 详细模式
coding-agent run "分析 app/core/agents/orchestrator.py 的代码结构" --verbose

# 指定最大轮次
coding-agent run "重构 test. py 中的函数" --max-turns 15 --verbose
```

使用任务模板
```bash
# 查看所有模板
coding-agent templates

# 生成文档
coding-agent template doc --file app/main.py --verbose

# 生成测试
coding-agent template test --file utils. py --verbose

# 代码重构
coding-agent template refactor --file legacy. py --verbose
```
项目初始化
```bash
# 创建 FastAPI 项目
coding-agent init my-api --type fastapi --verbose

# 创建 CLI 工具
coding-agent init my-tool --type cli --verbose

# 创建 Python 库
coding-agent init my-lib --type library --verbose

```
查看历史和记忆
```bash
# 查看执行历史
coding-agent history --limit 20

# 查看特定任务详情
coding-agent status cli_abc12345

# 查看任务的长期记忆
coding-agent memory cli_abc12345
```
交互式对话模式
```bash
coding-agent chat
```
复杂任务示例
数据处理任务
```bash
coding-agent run "完成一个完整的数据处理任务：
1. 创建 CSV 文件 /tmp/data.csv
2. 编写 Python 脚本处理数据
3. 计算统计信息
4. 生成可视化报告
5. 保存结果" --max-turns 20 --verbose
```
代码分析任务
```bash
coding-agent run "执行以下操作：
1. 使用 glob 查找所有 Python 文件
2. 使用 grep 搜索包含 'class.*Agent' 的文件
3. 分析主要的 Agent 类
4. 生成架构文档" --max-turns 15 --verbose
```
可用的 Action
Agent 通过 XML 格式的 Action 与环境交互：
```bash
<!-- 读取文件 -->
<read>
file_path:  app/main.py
</read>

<!-- 写入文件 -->
<write>
file_path:  test.py
content: |
  def hello():
      print("Hello, World!")
</write>

<!-- 编辑文件 -->
<edit>
file_path: config.py
old_string: DEBUG = False
new_string: DEBUG = True
</edit>
```
执行命令
```bash
<!-- 运行 Bash 命令 -->
<bash>
cmd: python3 test.py
</bash>
```
搜索操作
```bash
<!-- 搜索文件内容 -->
<grep>
pattern: "def.*login"
path: src/
include:  "*.py"
</grep>

<!-- 查找文件 -->
<glob>
pattern: "**/*.py"
path: app/
</glob>
```
记忆操作
```bash
<!-- 标记任务完成 -->
<finish>
任务已完成！所有文件已创建并验证通过。
</finish>
```
API 使用
启动 API 服务
```bash
# 使用 Docker
docker-compose up -d

# 或本地启动
uvicorn app.api. main:app --host 0.0.0.0 --port 8000
```
API 端点
```bash
# 创建任务
curl -X POST http://localhost:8000/api/v1/tasks/ \
  -H "Content-Type: application/json" \
  -d '{
    "instruction": "创建一个 Python 函数计算质数",
    "max_turns": 20
  }'

# 查询任务状态
curl http://localhost:8000/api/v1/tasks/{task_id}

# 列出所有任务
curl http://localhost:8000/api/v1/tasks/

# 查询上下文
curl http://localhost:8000/api/v1/contexts/
```

配置说明
编辑 .env 文件配置：
```bash
# LLM 提供商（qwen/openai/azure/anthropic）
LLM_PROVIDER=qwen

# 通义千问配置
DASHSCOPE_API_KEY=your_dashscope_api_key
QWEN_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1

# OpenAI 配置（可选）
OPENAI_API_KEY=your_openai_api_key
OPENAI_API_BASE=https://api.openai.com/v1

# 模型配置
ORCA_ORCHESTRATOR_MODEL=qwen/qwen-max
ORCA_SUBAGENT_MODEL=qwen/qwen-plus

# Redis 配置
REDIS_URL=redis://localhost:6379

# 执行配置
MAX_TURNS=50
COMMAND_TIMEOUT=300
LOG_LEVEL=INFO
```
项目架构
```bash
coding-agent/
├── app/
│   ├── api/              # FastAPI 接口
│   │   ├── main.py
│   │   ├── routes/
│   │   └── schemas/
│   ├── cli/              # 命令行工具
│   │   ├── main.py
│   │   ├── agent_runner.py
│   │   └── history_manager.py
│   ├── config/           # 配置管理
│   │   └── settings.py
│   ├── core/             # 核心逻辑
│   │   ├── actions/      # Action 定义和解析
│   │   ├── agents/       # Agent 实现
│   │   ├── execution/    # 命令执行
│   │   └── storage/      # 数据存储
│   └── llm/              # LLM 客户端
│       └── client.py
├── tests/                # 测试文件
├── docker-compose.yml    # Docker 编排
├── Dockerfile            # Docker 镜像
├── requirements.txt      # Python 依赖
├── setup.py              # 安装配置
└── README.md             # 本文件
```

## 核心组件
### OrchestratorAgent
主编排器，负责系统的整体调度：

任务处理：接收用户任务
决策生成：调用 LLM 生成 Action
执行管理：执行 Action 并管理状态
记忆管理：管理长期记忆，自动总结和召回历史

### MemoryManager
长期记忆管理器，提供上下文支持：

存储：对话历史存储
总结：智能总结生成
检索：记忆搜索和召回
优化：上下文窗口管理
### ActionHandler
Action 执行器，负责具体操作：

文件操作：文件读写、编辑
系统交互：Bash 命令执行
检索：文件搜索
记忆交互：记忆操作

### LLMClient
统一 LLM 接口，确保稳定性：

兼容性：多提供商支持
稳定性：自动重试机制、指数退避
健壮性：完善的错误处理

## 开发指南
### 添加新的 Action
#### 在 app/core/actions/entities/actions.py 中定义新的 Action 类。

#### 在 ACTION_TYPE_MAP 中注册该 Action。

#### 在 app/core/actions/parsing/handler.py 中实现对应的 _handle_xxx 方法。

### 添加新的 LLM 提供商
#### 在 app/config/settings.py 添加相关配置。
#### 提示：LiteLLM 已自动支持大部分主流模型，通常只需配置 API Key。

运行测试
```bash
# 单元测试
pytest tests/

# LLM 连接测试
python tests/test_qwen_connection.py

# Action 解析测试
python tests/test_parser_direct.py
```
常见问题
```bash
Redis 连接失败
# 检查 Redis 是否运行
docker ps | grep redis

# 启动 Redis
docker run -d -p 6379:6379 redis:7-alpine

API Key 无效
检查 .env 文件中的 API Key 是否正确：
# 测试通义千问连接
python tests/test_qwen_connection.py
```
任务执行超时
增加最大轮次或命令超时时间：
方法 A：命令行参数
```bash
coding-agent run "复杂任务" --max-turns 50
```
方法 B：修改 .env 配置
```bash
MAX_TURNS=100
COMMAND_TIMEOUT=600
```

贡献指南
欢迎提交 Issue 和 Pull Request！
Fork 本仓库
创建特性分支
```bash 
git checkout -b feature/amazing-feature
```
提交更改 
```bash
git commit -m 'Add amazing feature'
```
推送到分支 
```bash
git push origin feature/amazing-feature
```

联系方式
GitHub: @WangWeiqiang-UCAS
