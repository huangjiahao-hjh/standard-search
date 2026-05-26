#!/usr/bin/env python3
"""
标准信息检索平台 - 桌面启动器
双击运行 / 打包为独立可执行文件
"""

import os
import sys
import threading
import time
import webbrowser


def get_base_dir():
    """获取程序所在目录（支持 PyInstaller 打包后的路径）。"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def find_app_path(base_dir):
    """查找 app.py 文件路径。"""
    candidates = [
        os.path.join(base_dir, "app.py"),
        os.path.join(base_dir, "_internal", "app.py"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    for root, _dirs, files in os.walk(base_dir):
        if "app.py" in files:
            return os.path.join(root, "app.py")
    return None


def open_browser(url, delay=3):
    """延迟打开浏览器。"""
    time.sleep(delay)
    webbrowser.open(url)


def main():
    base_dir = get_base_dir()
    app_path = find_app_path(base_dir)

    if not app_path:
        input(
            "错误：找不到 app.py 文件。\n"
            "请确保 launcher.py 和 app.py 在同一个目录。\n\n按 Enter 退出..."
        )
        sys.exit(1)

    port = 8501
    url = f"http://localhost:{port}"

    print("=" * 52)
    print("      全国标准信息检索平台")
    print("=" * 52)
    print()
    print(f"  正在启动服务...")
    print(f"  启动后浏览器将自动打开")
    print(f"  地址：{url}")
    print()
    print("  关闭窗口或按 Ctrl+C 即可停止")
    print("-" * 52)

    # 延迟打开浏览器
    threading.Thread(target=open_browser, args=(url,), daemon=True).start()

    # 直接使用 Streamlit CLI，避免 PyInstaller 环境下 subprocess 重启动问题
    from streamlit.web import cli as st_cli

    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--server.port",
        str(port),
        "--server.headless",
        "true",
        "--server.enableXsrfProtection",
        "false",
        "--browser.gatherUsageStats",
        "false",
        "--server.fileWatcherType",
        "none",
    ]
    try:
        st_cli.main()
    except SystemExit:
        pass


if __name__ == "__main__":
    main()
