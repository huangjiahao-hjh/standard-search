@echo off
chcp 65001 >nul
title 全国标准信息检索平台

echo ==============================================
echo      全国标准信息检索平台
echo ==============================================
echo.

cd /d "%~dp0"

:: 检查 Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ 未检测到 Python，请先安装 Python 3.8+
    echo    下载地址：https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

:: 检查 uv
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo 📦 正在安装 uv (Python 包管理器)...
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    set PATH=%USERPROFILE%\.local\bin;%PATH%
)

echo 📦 正在检查依赖...

:: 启动应用
uv run --with streamlit --with pandas --with requests --with beautifulsoup4 ^
    streamlit run app.py --server.port 8501 --server.headless true ^
    --browser.gatherUsageStats false

echo.
pause
