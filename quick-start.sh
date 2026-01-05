#!/bin/bash

set -e

echo "================================"
echo "Coding Agent 快速启动"
echo "================================"

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "错误:  请先安装 Docker"
    exit 1
fi

# 检查 docker-compose
if ! command -v docker-compose &> /dev/null; then
    echo "错误: 请先安装 docker-compose"
    exit 1
fi

# 创建工作目录
mkdir -p workspace

# 创建 docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  redis: 
    image: redis:7-alpine
    container_name: coding-agent-redis
    ports: 
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout:  3s
      retries:  5
    restart: unless-stopped

  agent:
    image: wangweiqiang/coding-agent:latest
    container_name:  coding-agent
    ports: 
      - "8000:8000"
    volumes:
      - ./workspace:/app/workspace
    environment:
      - LLM_PROVIDER=${LLM_PROVIDER:-qwen}
      - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
      - REDIS_URL=redis://redis:6379
      - ORCA_ORCHESTRATOR_MODEL=${ORCA_ORCHESTRATOR_MODEL:-qwen/qwen-max}
      - MAX_TURNS=${MAX_TURNS:-50}
    depends_on:
      redis: 
        condition: service_healthy
    restart: unless-stopped

volumes:
  redis_data: 
EOF

# 检查 .env 文件
if [ !  -f ".env" ]; then
    echo ""
    echo "请输入你的通义千问 API Key:"
    read -r API_KEY
    
    cat > .env << EOF
DASHSCOPE_API_KEY=$API_KEY
LLM_PROVIDER=qwen
ORCA_ORCHESTRATOR_MODEL=qwen/qwen-max
MAX_TURNS=50
EOF
    echo "已创建 .env 文件"
fi

# 启动服务
echo ""
echo "正在启动服务..."
docker-compose up -d

echo ""
echo "================================"
echo "启动完成！"
echo "================================"
echo ""
echo "使用方法："
echo "1. CLI 模式："
echo "   docker-compose exec agent coding-agent run \"你的任务\" --verbose"
echo ""
echo "2. 交互模式："
echo "   docker-compose exec agent coding-agent chat"
echo ""
echo "3. API 访问："
echo "   http://localhost:8000/docs"
echo ""
echo "4. 查看日志："
echo "   docker-compose logs -f agent"
echo ""
echo "5. 停止服务："
echo "   docker-compose down"