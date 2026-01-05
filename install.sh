#!/bin/bash

echo "🚀 Installing Coding Agent CLI..."

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 创建符号链接到 /usr/local/bin
chmod +x coding_agent
sudo ln -sf "$(pwd)/coding_agent" /usr/local/bin/coding-agent

echo "✅ Installation complete!"
echo ""
echo "Usage:"
echo "  coding-agent run 'your task here'"
echo "  coding-agent chat"
echo "  coding-agent history"
echo ""
echo "For more help:   coding-agent --help"
