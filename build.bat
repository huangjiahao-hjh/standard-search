@echo off
chcp 65001 >nul
title 标准信息检索平台 - Windows 打包工具
color 0B
cls

echo ==============================================
echo      标准信息检索平台 - Windows 打包工具
echo ==============================================
echo.
echo 此工具将把应用打包成独立的 .exe 可执行文件
echo 打包后无需安装 Python，可直接发给别人运行
echo.
echo 按任意键开始打包...
pause >nul
cls

echo ==============================================
echo 步骤 1/4：检查 Python
echo ==============================================
echo.

:: 检查 Python 3.8+
python --version >nul 2>nul
if %errorlevel% neq 0 (
    echo ⚠️ 未检测到 Python
    echo 正在从官网下载 Python 3.12...
    echo.
    curl -o "%TEMP%\python-3.12.0-amd64.exe" https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe
    if %errorlevel% equ 0 (
        echo 正在安装 Python（请勿关闭窗口）...
        "%TEMP%\python-3.12.0-amd64.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
        echo 安装完成，请重启打包工具
    ) else (
        echo ❌ 下载失败，请手动安装 Python 3.8+
        echo    下载地址：https://www.python.org/downloads/
    )
    echo.
    pause
    exit /b 1
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i
    echo ✅ Python %PYTHON_VER%
)

echo.
echo ==============================================
echo 步骤 2/4：安装构建工具
echo ==============================================
echo.

echo 正在安装 PyInstaller 和运行依赖...
python -m pip install --upgrade pip -q
python -m pip install pyinstaller -q
python -m pip install requests beautifulsoup4 streamlit pandas -q
echo ✅ 依赖安装完成

echo.
echo ==============================================
echo 步骤 3/4：执行打包
echo ==============================================
echo.
echo 正在打包应用（约 1-3 分钟）...
echo.

:: 清理旧构建
if exist "dist\标准信息检索平台" rmdir /s /q "dist\标准信息检索平台"
if exist "build" rmdir /s /q "build"
if exist "标准信息检索平台.spec" del "标准信息检索平台.spec"

:: PyInstaller 打包
python -m PyInstaller ^
    --name "标准信息检索平台" ^
    --noconfirm ^
    --clean ^
    --windowed ^
    --onedir ^
    --add-data "app.py;." ^
    --add-data "scraper.py;." ^
    --hidden-import streamlit ^
    --hidden-import pandas ^
    --hidden-import requests ^
    --hidden-import bs4 ^
    --hidden-import lxml ^
    --hidden-import html5lib ^
    --hidden-import streamlit.web.cli ^
    --hidden-import streamlit.runtime.scriptrunner.magic_funcs ^
    --collect-all streamlit ^
    --collect-all pandas ^
    launcher.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ 打包失败！请截图错误信息反馈。
    pause
    exit /b 1
)

echo.
echo ==============================================
echo 步骤 4/4：完成！
echo ==============================================
echo.
echo ✅ 打包成功！
echo.
echo 输出路径：%CD%\dist\标准信息检索平台\
echo.
echo 将 "dist\标准信息检索平台" 整个文件夹发送给任意人，
echo 双击 "标准信息检索平台.exe" 即可运行，无需安装 Python！
echo.
explorer "%CD%\dist\标准信息检索平台"
echo.
pause
