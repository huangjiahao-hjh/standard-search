#!/usr/bin/env python3
"""
构建脚本：使用 PyInstaller 将应用打包为独立可执行文件。

用法:
    python3 build_app.py          # macOS 打包
    python3 build_app.py --win    # Windows 交叉打包（需额外配置）

打包后的文件在 dist/ 目录下。
"""

import os
import sys
import subprocess
import shutil
import platform

APP_NAME = "标准信息检索平台"
ENTRY_POINT = "launcher.py"
DATA_FILES = ["app.py", "scraper.py"]


def check_pyinstaller():
    """确保 PyInstaller 已安装。"""
    try:
        import PyInstaller  # noqa
    except ImportError:
        print("正在安装 PyInstaller...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "pyinstaller"]
        )


def build():
    check_pyinstaller()

    system = platform.system()
    is_mac = system == "Darwin"
    is_win = system == "Windows"

    # 确认数据文件存在
    base_dir = os.path.dirname(os.path.abspath(__file__))
    for f in DATA_FILES:
        fpath = os.path.join(base_dir, f)
        if not os.path.exists(fpath):
            print(f"错误：找不到 {fpath}")
            sys.exit(1)

    # 构建命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--noconfirm",
        "--clean",
    ]

    # 平台特定选项
    if is_mac:
        cmd += [
            "--windowed",          # 无终端窗口（双击启动）
            "--onedir",            # 目录模式（启动更快）
        ]
    elif is_win:
        cmd += [
            "--windowed",          # Windows 无控制台窗口
            "--onedir",
        ]

    # 添加数据文件
    for f in DATA_FILES:
        cmd += ["--add-data", f"{f}{';' if is_win else ':'}."]

    # 添加隐式导入（Streamlit 的懒加载模块）
    hidden_imports = [
        "streamlit",
        "pandas",
        "requests",
        "bs4",
        "lxml",
        "html5lib",
        "streamlit.runtime.scriptrunner.magic_funcs",
        "streamlit.web.cli",
        "streamlit.connections",
        "streamlit.hello",
    ]
    for mod in hidden_imports:
        cmd += ["--hidden-import", mod]

    # 收集 Streamlit 所有数据
    cmd += ["--collect-all", "streamlit"]
    cmd += ["--collect-all", "pandas"]

    # 入口文件
    cmd.append(os.path.join(base_dir, ENTRY_POINT))

    print(f"\n{'='*50}")
    print(f"  构建 {APP_NAME}")
    print(f"  平台: {system}")
    print(f"  输出: {os.path.join(base_dir, 'dist', APP_NAME)}")
    print(f"{'='*50}\n")

    subprocess.check_call(cmd, cwd=base_dir)

    print(f"\n✅ 构建完成!")
    print(f"   路径: {os.path.join(base_dir, 'dist', APP_NAME)}")
    if is_mac:
        app_bundle = os.path.join(base_dir, "dist", f"{APP_NAME}.app")
        if os.path.exists(app_bundle):
            print(f"   macOS App: {app_bundle}")
    print()
    print("将整个文件夹发送给其他人即可直接运行（无需安装 Python）。")


if __name__ == "__main__":
    build()
