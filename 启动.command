#!/bin/bash
# =============================================
#  标准信息检索平台 - macOS 启动器
#  双击此文件即可运行
# =============================================

cd "$(dirname "$0")" || exit 1
clear

echo "=============================================="
echo "     全国标准信息检索平台"
echo "=============================================="
echo ""

# 检查 Python 3
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "❌ 未检测到 Python，请先安装 Python 3.8+"
    echo "   下载地址：https://www.python.org/downloads/"
    echo ""
    read -n 1 -s -r -p "按任意键退出..."
    exit 1
fi

# 检查/安装 uv（快速包管理器）
if ! command -v uv &>/dev/null; then
    echo "📦 正在安装 uv (Python 包管理器)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

echo "📦 正在检查依赖..."
uv run --with streamlit --with pandas --with requests --with beautifulsoup4 \
    streamlit run app.py --server.port 8501 --server.headless true \
    --browser.gatherUsageStats false

echo ""
read -n 1 -s -r -p "按任意键退出..."
